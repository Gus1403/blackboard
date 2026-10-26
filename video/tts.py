#!/usr/bin/env python3
"""Narrate every cue of script.json with ElevenLabs (with timestamps), then build timeline.json + timeline.js.

audio/<scene>_<cue>.mp3 + .json (alignment). Re-runs skip cues whose model, voice, voice settings, output
format and text did not change, so an interrupted or quota-stopped run resumes where it stopped.
timeline.json: scenes with absolute start/dur, cues with scene-local s/e, subtitle chunks per sentence.
tts.done: sha256 of timeline.json, timeline.js and narration.wav, written last; render refuses any other set.

  python3 tts.py               narrate what is missing, then write timeline.json, timeline.js, narration.wav, tts.done
  python3 tts.py --check       report cached / missing cues without calling the API (exit 0 = all cached)
  python3 tts.py --verify      exit 0 only if the three published files are the set tts.done fingerprints
  python3 tts.py --workers 3   parallel requests (default 3)

Credentials: ELEVENLABS_API_KEY in the environment (only needed when a cue is missing).
Overrides: ELEVENLABS_MODEL, ELEVENLABS_API_BASE. The voice comes from script.json "voice".
Exit codes: 0 ok, 2 usage/script/credential error, 3 quota or auth refused by the API, 4 other API failure.
"""
import argparse, base64, concurrent.futures as cf, hashlib, json, os, re, subprocess, sys, tempfile, threading, time
import urllib.error, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(ROOT, "audio")
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_v4")
VOICE = "XrExE9yKIg1WjnnlVkGX"   # default when script.json has no "voice"
VOICE_SETTINGS = {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 0.97}
OUTPUT_FORMAT = "mp3_44100_192"
API_BASE = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io").rstrip("/")
FPS = 30
GAP = 0.45          # silence between cues
HEAD, TAIL = 0.6, 0.9  # scene padding
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
DONE = os.path.join(ROOT, "tts.done")
PUBLISHED = ("script.json", "timeline.json", "timeline.js", "narration.wav")


class Stop(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def load_script(path):
    try:
        with open(path) as f:
            s = json.load(f)
    except (OSError, ValueError) as e:
        raise Stop(2, f"cannot read {path}: {e}")
    errs = []
    for k in ("title", "chapters", "scenes"):
        if k not in s:
            errs.append(f"missing key {k!r}")
    if errs:
        raise Stop(2, "script.json: " + "; ".join(errs))
    if not isinstance(s["chapters"], list) or not s["chapters"]:
        errs.append("chapters must be a non-empty list")
    seen = set()
    for sc in s["scenes"]:
        sid = sc.get("id")
        if not isinstance(sid, str) or not SAFE_ID.match(sid):
            errs.append(f"bad scene id {sid!r}")
            continue
        if sid in seen:
            errs.append(f"duplicate scene id {sid}")
        seen.add(sid)
        ch = sc.get("chapter")
        if not isinstance(ch, int) or not 0 <= ch < len(s["chapters"]):
            errs.append(f"{sid}: chapter {ch!r} is not an index into chapters")
        cues = sc.get("cues") or []
        if not cues:
            errs.append(f"{sid}: no cues")
        cseen = set()
        for c in cues:
            cid = c.get("id")
            if not isinstance(cid, str) or not SAFE_ID.match(cid):
                errs.append(f"{sid}: bad cue id {cid!r}")
                continue
            if cid in cseen:
                errs.append(f"{sid}: duplicate cue id {cid}")
            cseen.add(cid)
            if ("say" in c) == ("pause" in c):
                errs.append(f"{sid}.{cid}: needs exactly one of say / pause")
            elif "say" in c and not (isinstance(c["say"], str) and c["say"].strip()):
                errs.append(f"{sid}.{cid}: empty say")
            elif "pause" in c and not (isinstance(c["pause"], (int, float)) and c["pause"] > 0):
                errs.append(f"{sid}.{cid}: pause must be > 0 seconds")
    if errs:
        raise Stop(2, "script.json:\n  " + "\n  ".join(errs))
    return s


def cache_key(voice, text, model=MODEL, settings=None, fmt=OUTPUT_FORMAT):
    """Everything that changes the audio: model, voice, voice settings, output format, text."""
    blob = json.dumps({"model": model, "voice": voice, "settings": settings or VOICE_SETTINGS, "format": fmt, "text": text},
                      sort_keys=True, ensure_ascii=False)
    return "v2:" + hashlib.sha256(blob.encode()).hexdigest()


def legacy_key(voice, text):
    # Projects narrated before the cache key covered the settings used sha1(model + voice + text) with exactly
    # these defaults; accept such audio only while the defaults are still in force.
    if MODEL == "eleven_v4" and VOICE_SETTINGS == {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 0.97} \
            and OUTPUT_FORMAT == "mp3_44100_192":
        return hashlib.sha1((MODEL + voice + text).encode()).hexdigest()
    return None


def cached(path, voice, text):
    meta = path + ".json"
    if not (os.path.exists(path) and os.path.exists(meta)):
        return False
    try:
        with open(meta) as f:
            m = json.load(f)
    except ValueError:
        return False
    if not m.get("alignment"):
        return False
    h = m.get("hash")
    if h == cache_key(voice, text):
        return True
    if h is not None and h == legacy_key(voice, text):
        m["hash"] = cache_key(voice, text)        # upgrade in place, audio unchanged
        atomic_write(meta, json.dumps(m).encode())
        return True
    return False


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_done():
    """None when the current script and published timing/audio match one successful run, else why not."""
    try:
        with open(DONE) as f:
            want = json.load(f)
    except (OSError, ValueError):
        return "tts.done is missing: run python3 tts.py (cached cues make no API call)"
    for n in PUBLISHED:
        p = os.path.join(ROOT, n)
        if not os.path.exists(p) or file_sha256(p) != want.get(n):
            return f"{n} is not the file tts.done fingerprints (a tts.py run failed or was interrupted): rerun python3 tts.py"
    return None


def atomic_write(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def api_error(e):
    """(code, message) for an HTTPError; code 3 = quota/auth (do not retry), None = retryable."""
    try:
        body = e.read().decode(errors="replace")
    except Exception:
        body = ""
    status = ""
    try:
        d = json.loads(body).get("detail")
        status = (d.get("status") or d.get("code") or "") if isinstance(d, dict) else ""
    except Exception:
        pass
    msg = f"HTTP {e.code} {status} {body[:400]}".strip()
    if e.code in (401, 402, 403) or "quota" in status or "credit" in status or "quota" in body.lower():
        return 3, msg
    if e.code == 429 or e.code >= 500:
        return None, msg
    return 4, msg


stop_event = threading.Event()


def tts(path, voice, text, key):
    if stop_event.is_set():
        return
    body = json.dumps({"text": text, "model_id": MODEL, "voice_settings": VOICE_SETTINGS}).encode()
    url = f"{API_BASE}/v1/text-to-speech/{voice}/with-timestamps?output_format={OUTPUT_FORMAT}"
    last = ""
    for attempt in range(6):
        if stop_event.is_set():
            return
        try:
            req = urllib.request.Request(url, body, {"xi-api-key": key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                r = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            code, last = api_error(e)
            if code:
                stop_event.set()
                raise Stop(code, f"{os.path.basename(path)}: {last}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:  # network / bad JSON
            last = repr(e)
        if attempt < 5:
            time.sleep(3 * (attempt + 1))
    else:
        stop_event.set()
        raise Stop(4, f"{os.path.basename(path)}: failed after 6 attempts: {last}")
    al = r.get("alignment") or r.get("normalized_alignment")
    if not r.get("audio_base64") or not al:
        stop_event.set()
        raise Stop(4, f"{os.path.basename(path)}: response without audio or alignment")
    # the metadata is the commit marker that makes the cue count as cached: drop the old one before the audio
    # changes, write the new one last, so an interruption in between leaves the cue missing, never mismatched
    if os.path.exists(path + ".json"):
        os.remove(path + ".json")
    atomic_write(path, base64.b64decode(r["audio_base64"]))
    atomic_write(path + ".json", json.dumps({"hash": cache_key(voice, text), "model": MODEL, "voice": voice,
                                             "settings": VOICE_SETTINGS, "text": text, "alignment": al}).encode())
    print("tts", os.path.basename(path), flush=True)


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode())


def chunks(text, al):
    """Split narration into subtitle chunks (sentences, long ones split at commas) with times."""
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    joined = "".join(chars)
    out, i = [], 0
    for m in re.finditer(r"[^.?!:]+[.?!:]?", joined):
        seg = m.group(0)
        if not seg.strip():
            continue
        parts = [seg]
        if len(seg) > 95:
            parts = re.split(r"(?<=,)\s", seg)
        pos = m.start()
        for p in parts:
            a = joined.find(p, pos)
            b = a + len(p) - 1
            pos = b + 1
            a2 = a + (len(p) - len(p.lstrip()))
            if a2 > b:
                continue
            out.append({"text": p.strip(), "s": st[a2], "e": en[b]})
    return out


def jobs_for(script):
    voice = script.get("voice") or VOICE
    return [(os.path.join(AUD, f"{sc['id']}_{cue['id']}.mp3"), voice, cue["say"])
            for sc in script["scenes"] for cue in sc["cues"] if "say" in cue]


def build_timeline(script):
    t, scenes, concat = 0.0, [], []
    for sc in script["scenes"]:
        local, cues, subs = HEAD, {}, []
        for cue in sc["cues"]:
            if "pause" in cue:
                d = cue["pause"]
                cues[cue["id"]] = {"s": local, "e": local + d, "pause": True}
            else:
                p = os.path.join(AUD, f"{sc['id']}_{cue['id']}.mp3")
                d = dur(p)
                cues[cue["id"]] = {"s": local, "e": local + d}
                with open(p + ".json") as f:
                    al = json.load(f)["alignment"]
                for c in chunks(cue["say"], al):
                    subs.append({"text": c["text"], "s": local + c["s"], "e": local + c["e"]})
                concat.append((t + local, p))
            local += d + GAP
        sd = local - GAP + TAIL
        scenes.append({"id": sc["id"], "chapter": sc["chapter"], "start": round(t, 3), "dur": round(sd, 3), "cues": cues, "subs": subs})
        t += sd
    tl = {"title": script["title"], "subtitle": script.get("subtitle", ""), "chapters": script["chapters"],
          "total": round(t, 3), "fps": FPS, "scenes": scenes}
    return tl, concat, t


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report cached/missing cues, no API calls")
    ap.add_argument("--verify", action="store_true", help="check that the published files form one complete run")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    if a.verify:
        why = verify_done()
        if why:
            print("TTS_INCOMPLETE: " + why, file=sys.stderr)
            return 1
        print("TTS_OK: " + ", ".join(PUBLISHED) + " match tts.done")
        return 0
    if a.workers < 1:
        raise Stop(2, "--workers must be >= 1")
    script = load_script(os.path.join(ROOT, "script.json"))
    os.makedirs(AUD, exist_ok=True)
    jobs = jobs_for(script)
    missing = [j for j in jobs if not cached(*j)]
    print(f"cues: {len(jobs)} spoken, {len(jobs) - len(missing)} cached, {len(missing)} to narrate "
          f"(model {MODEL}, voice {jobs[0][1] if jobs else '-'})", flush=True)
    if a.check:
        for p, _, _ in missing:
            print("missing", os.path.basename(p))
        return 0 if not missing else 1
    if missing:
        key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        if not key:
            raise Stop(2, f"ELEVENLABS_API_KEY is not set and {len(missing)} cue(s) need narration")
        with cf.ThreadPoolExecutor(a.workers) as ex:
            futs = [ex.submit(tts, p, v, txt, key) for p, v, txt in missing]
            errs = []
            for fu in cf.as_completed(futs):
                try:
                    fu.result()
                except Stop as e:
                    errs.append(e)
        if errs:
            left = sum(1 for j in jobs if not cached(*j))
            e = min(errs, key=lambda x: x.code)
            raise Stop(e.code, f"{'TTS_QUOTA_OR_AUTH' if e.code == 3 else 'TTS_FAILED'}: {e}\n"
                               f"{len(jobs) - left} of {len(jobs)} cues are cached; rerun tts.py to resume the other {left}.")

    tl, concat, t = build_timeline(script)
    data = json.dumps(tl, indent=1)
    # narration track: place each clip at its absolute time
    inputs, filt = [], []
    if not concat:   # pause-only script: a silent track of the right length
        inputs, filt = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono"], [f"[0:a]atrim=0:{t:.3f}[out]"]
    for k, (at, p) in enumerate(concat):
        inputs += ["-i", p]
        filt.append(f"[{k}:a]aresample=48000,adelay={int(at*1000)}:all=1[a{k}]")
    if concat:
        filt.append("".join(f"[a{k}]" for k in range(len(concat))) + f"amix=inputs={len(concat)}:normalize=0,apad=whole_dur={t:.3f}[out]")
    with open(os.path.join(ROOT, "narr_filter.txt"), "w") as f:
        f.write(";\n".join(filt))
    tmp = os.path.join(ROOT, ".narration.tmp.wav")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex_script", os.path.join(ROOT, "narr_filter.txt"),
                           "-map", "[out]", "-t", f"{t:.3f}", "-c:a", "pcm_s16le", "-f", "wav", tmp])
    # publish only after the WAV is built, then fingerprint the set; a failure before this leaves the previous set
    atomic_write(os.path.join(ROOT, "timeline.json"), data.encode())
    atomic_write(os.path.join(ROOT, "timeline.js"), ("window.TIMELINE=" + data + ";\n").encode())
    os.replace(tmp, os.path.join(ROOT, "narration.wav"))
    atomic_write(DONE, json.dumps({n: file_sha256(os.path.join(ROOT, n)) for n in PUBLISHED}, indent=1).encode())
    print(f"timeline: {len(tl['scenes'])} scenes, {t/60:.1f} min")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Stop as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.code)
