#!/usr/bin/env python3
"""Blackboard bridge: serves the board, streams lesson changes, queues page actions.

Routes
  GET  /                 board page (current lesson of the last rendered workspace)
  GET  /lessons          hub: every lesson in every workspace (rendered before, or found under the scan roots)
  GET  /lessons/NNNN     board page for one lesson (last rendered workspace)
  GET  /w/<slug>/        board page pinned to one workspace: follows that workspace's current lesson
  GET  /w/<slug>/lessons/NNNN, /w/<slug>/assets/<file>, and every /api route accepts ?ws=<slug>
  GET  /api/state        {ws, slug, current, page_version, lessons:[...], workspaces:[{slug,name,path,current,count,last,lessons}]}
  GET  /api/lesson?id=NNNN&from=N&hash=H   {text, offset, reset}  (text = new bytes cut at last blank line)
  GET  /events?id=NNNN   SSE: `change` when the lesson file or state changes
  GET  /assets/<file>    $WS/lessons/assets/<file>
  GET  /anim/<path>      board/anim/<path>
  POST /ask              {kind,...} -> appended to queue.jsonl, wake per host
  GET  /health           ok
State lives in $BLACKBOARD_HOME/state.json (default ~/.cache/blackboard), written by render.sh: {ws, current, agent, layout, cli_surface, opened}
"""
import calendar, hashlib, json, os, re, subprocess, sys, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOARD = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BOARD)
HOME_DIR = os.environ.get("BLACKBOARD_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "blackboard")
os.makedirs(HOME_DIR, exist_ok=True)
STATE = os.path.join(HOME_DIR, "state.json")
QUEUE = os.path.join(HOME_DIR, "queue.jsonl")
TMPL = os.path.join(BOARD, "board.html.tmpl")
PORT = int(os.environ.get("BLACKBOARD_PORT", "7331"))


def state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {}


def scan_roots():
    """Folders to search for lessons/: BLACKBOARD_SCAN (colon-separated), else "scan" in $BLACKBOARD_HOME/config.json,
    else the grandparent of the last rendered workspace (…/school/math1552/learn -> …/school)."""
    env = os.environ.get("BLACKBOARD_SCAN")
    if env:
        return [os.path.expanduser(p) for p in env.split(":") if p]
    try:
        with open(os.path.join(HOME_DIR, "config.json")) as f:
            cfg = json.load(f)
        roots = cfg.get("scan") or []
        if roots:
            return [os.path.expanduser(p) for p in roots]
    except Exception:
        pass
    w = state().get("ws")
    return [os.path.dirname(os.path.dirname(os.path.abspath(w)))] if w else []


_scan = {"t": 0, "v": [], "roots": None}


def slug_of(path):
    """Course slug for a workspace path: the directory above `learn` (math1552/learn -> math1552), else the basename."""
    path = os.path.abspath(path)
    base = os.path.basename(path)
    if base == "learn":
        base = os.path.basename(os.path.dirname(path))
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "ws"


def discovered():
    """Every */learn/lessons (depth <= 4) under the scan roots, cached for 30 s."""
    roots = scan_roots()
    if time.time() - _scan["t"] < 30 and roots == _scan["roots"]:
        return _scan["v"]
    out = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            depth = dp[len(root):].count(os.sep)
            dns[:] = [d for d in dns if not d.startswith(".") and d not in ("node_modules", "venv", ".venv", "dist", "build", "assets")]
            if depth >= 4:
                dns[:] = []
            if os.path.basename(dp) == "lessons" and any(re.match(r"^\d{4}-.+\.md$", f) for f in fns):
                out.append(os.path.dirname(dp))
    _scan.update(t=time.time(), v=out, roots=roots)
    return out


def workspaces():
    """slug -> {path, current, streaming, rev, ...}: registered (rendered) workspaces plus discovered ones."""
    st = state()
    out = {}
    for slug, w in (st.get("workspaces") or {}).items():
        if w.get("path") and os.path.isdir(os.path.join(w["path"], "lessons")):
            out[slug] = dict(w)
    if st.get("ws") and os.path.isdir(st["ws"]):
        out.setdefault(slug_of(st["ws"]), {"path": st["ws"], "current": st.get("current", "")})
    for path in discovered():
        sl = slug_of(path)
        if sl in out and os.path.abspath(out[sl]["path"]) != os.path.abspath(path):
            sl = sl + "-" + hashlib.md5(path.encode()).hexdigest()[:4]
        out.setdefault(sl, {"path": path, "current": ""})
    return out


def ws(slug=None):
    """Workspace path: the slug's, else the last rendered one."""
    if slug:
        w = workspaces().get(slug)
        if w:
            return w["path"]
    return state().get("ws") or os.getcwd()


def current(slug=None):
    st = state()
    if slug:
        w = (st.get("workspaces") or {}).get(slug)
        if w and w.get("current"):
            return w["current"]
        if slug != slug_of(st.get("ws", "")):
            files = lesson_files(ws(slug))
            return files[-1][0] if files else ""
    return st.get("current", "")


def lessons_dir(wsp=None):
    return os.path.join(wsp or ws(), "lessons")


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm


def lesson_files(wsp=None):
    d = lessons_dir(wsp)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        m = re.match(r"^(\d{4})-(.+)\.md$", name)
        if m:
            out.append((m.group(1), m.group(2), os.path.join(d, name)))
    return out


def lesson_path(lid, wsp=None):
    for i, slug, p in lesson_files(wsp):
        if i == lid:
            return p
    return None


def scores(wsp=None):
    p = os.path.join(wsp or ws(), "learning-records", "quiz-log.jsonl")
    out = {}
    try:
        with open(p) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    out.setdefault(str(r.get("lesson")), []).append(int(r.get("score", 0)))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def lessons_meta(wsp=None):
    sc = scores(wsp)
    out = []
    for i, slug, p in lesson_files(wsp):
        try:
            with open(p) as f:
                text = f.read(4000)
        except Exception:
            text = ""
        fm = front_matter(text)
        title = fm.get("title")
        if not title:
            m = re.search(r"^# (.+)$", text, re.M)
            title = m.group(1) if m else slug.replace("-", " ")
        out.append({
            "id": i, "slug": slug, "title": title, "course": fm.get("course", ""),
            "exam": fm.get("exam", ""), "photo": fm.get("photo", ""), "credit": fm.get("credit", ""),
            "date": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(p))),
            "mtime": int(os.path.getmtime(p)),
            "scores": sc.get(i, []),
        })
    return out


def hub():
    """Every workspace with its lessons, for the /lessons hub."""
    out = []
    for slug, w in workspaces().items():
        lessons = lessons_meta(w["path"])
        if not lessons:
            continue
        name = next((l["course"] for l in reversed(lessons) if l.get("course")), "") or slug
        out.append({"slug": slug, "name": name, "path": w["path"], "current": current(slug), "count": len(lessons),
                    "last": max(l["date"] for l in lessons), "lessons": lessons})
    out.sort(key=lambda w: max(l["mtime"] for l in w["lessons"]), reverse=True)
    return out


def cut_at_blank(text):
    """Return the prefix of text that ends at the last blank line (complete blocks only)."""
    idx = text.rfind("\n\n")
    if idx < 0:
        return ""
    # do not cut inside an unterminated ::: container
    head = text[: idx + 2]
    opens = len(re.findall(r"^::: ", head, re.M))
    closes = len(re.findall(r"^:::\s*$", head, re.M))
    if opens > closes:
        # back up to before the last unterminated container
        last_open = [m.start() for m in re.finditer(r"^::: ", head, re.M)][-1]
        prev_blank = head.rfind("\n\n", 0, last_open)
        head = head[: prev_blank + 2] if prev_blank >= 0 else ""
    return head


def read_lesson(lid, frm, h, wsp=None):
    p = lesson_path(lid, wsp)
    if not p:
        return {"reset": True, "text": "", "offset": 0, "missing": True}
    with open(p, "rb") as f:
        data = f.read()
    if frm > 0 and frm <= len(data) and hashlib.md5(data[:frm]).hexdigest() == h:
        new = data[frm:].decode("utf-8", "replace")
        complete = cut_at_blank(new) if state().get("streaming") else new
        end = frm + len(complete.encode("utf-8"))
        return {"reset": False, "text": complete, "offset": end, "hash": hashlib.md5(data[:end]).hexdigest()}
    text = data.decode("utf-8", "replace")
    return {"reset": True, "text": text, "offset": len(data), "hash": hashlib.md5(data).hexdigest()}


def host_command(req):
    """Build the agent command for a queue item."""
    agent = state().get("agent", "claude")
    prefix = "$blackboard" if agent == "codex" else "/blackboard"
    k = req.get("kind")
    q = lambda s: '"' + str(s).replace('"', "'") + '"'
    if k == "explain":
        parts = [prefix, "explain", f"L{req.get('line', 0)}", q(req.get("text", ""))]
        if req.get("depth") == "deep":
            parts.append("deep")
        if req.get("parent"):
            parts.append(f"parent={req['parent']}")
        if req.get("grow"):
            parts.append(f"grow={req['grow']}")
        parts.append(f"lesson={req.get('lesson','')}")
        return " ".join(parts)
    if k == "remove":
        return f"{prefix} remove {req.get('id')} lesson={req.get('lesson','')}"
    if k == "quiz":
        return f"{prefix} quiz {q(req.get('topic',''))} {req.get('mode','recall')} lesson={req.get('lesson','')}"
    if k == "predict":
        return f"{prefix} predict {req.get('block')} {req.get('choice')} lesson={req.get('lesson','')}"
    if k == "mcq":
        return f"{prefix} mcq {req.get('item')} {req.get('choice')} lesson={req.get('lesson','')}"
    if k == "grid":
        return f"{prefix} grid"
    return f"{prefix} {json.dumps(req)}"


PENDING = {}
PENDING_LOCK = threading.Lock()
LISTEN_LOCK = threading.Lock()


def headless(script, req, keep=("id",), timeout=180):
    """Run bin/<script> in a thread; record the result under the page's pending id.

    `keep` names the writer's output fields copied into the pending record, so the
    page can paint the result (a score, the new item ids) without refetching."""
    pid = req.get("pending") or f"p{int(time.time()*1000)}"
    wsp = ws(req.get("ws"))
    lesson = req.get("lesson") or current(req.get("ws"))
    path = lesson_path(lesson, wsp)
    with PENDING_LOCK:
        PENDING[pid] = {"status": "writing", "started": time.time()}
    def run():
        try:
            if not path:
                raise RuntimeError("lesson not found")
            r = subprocess.run([sys.executable, os.path.join(BOARD, "..", "bin", script), path, json.dumps(req)],
                               capture_output=True, text=True, timeout=timeout)
            out = json.loads((r.stdout or "{}").strip().splitlines()[-1]) if r.stdout.strip() else {}
            if r.returncode != 0 or "error" in out:
                raise RuntimeError(out.get("error") or (r.stderr or "writer failed")[:300])
            done = {"status": "done"}
            for k in keep:
                if k in out:
                    done[k] = out[k]
            with PENDING_LOCK:
                PENDING[pid] = done
        except Exception as e:
            with PENDING_LOCK:
                PENDING[pid] = {"status": "error", "error": str(e)[:300]}
        # bump rev so SSE clients refresh even if the file did not change
        bump_rev(req.get("ws"))
    threading.Thread(target=run, daemon=True).start()
    return {"queued": True, "wake": "headless", "pending": pid}


def bump_rev(slug=None):
    try:
        st = state(); now = int(time.time() * 1000); st["rev"] = now
        w = (st.get("workspaces") or {}).get(slug) if slug else None
        if w is not None:
            w["rev"] = now
        with open(STATE, "w") as f:
            json.dump(st, f)
    except Exception:
        pass


def set_fold(req):
    path = lesson_path(req.get("lesson") or current(req.get("ws")), ws(req.get("ws")))
    eid, folded = req.get("id"), bool(req.get("folded"))
    if not path or not eid:
        return {"error": "no lesson/id"}
    s = open(path).read()
    m = re.search(rf"^(::: exp {re.escape(eid)})([^\n]*)$", s, re.M)
    if not m:
        return {"error": "id not found"}
    flags = [f for f in m.group(2).split() if f != "folded"]
    if folded:
        flags.append("folded")
    s = s[:m.start()] + m.group(1) + (" " + " ".join(flags) if flags else "") + s[m.end():]
    open(path, "w").write(s)
    return {"ok": True, "id": eid, "folded": folded}


def remove_exp(req):
    path = lesson_path(req.get("lesson") or current(req.get("ws")), ws(req.get("ws")))
    r = subprocess.run([sys.executable, os.path.join(BOARD, "..", "bin", "exp-remove.py"), path, req.get("id", "")],
                       capture_output=True, text=True)
    return {"ok": r.returncode == 0, "out": (r.stdout or r.stderr).strip()}


def wake(req):
    st = state()
    k = req.get("kind")
    if k == "explain":
        return headless("explain.py", req, keep=("id",))
    if k == "quiz":
        req = dict(req, op="generate")
        return headless("quiz.py", req, keep=("ids", "n"))
    if k == "grade":
        req = dict(req, op="grade")
        return headless("quiz.py", req, keep=("item", "score", "rationale", "missing"), timeout=120)
    if k == "fold":
        return set_fold(req)
    if k == "remove":
        return remove_exp(req)
    if k in ("predict", "mcq"):
        # click logging only; no agent wake
        return {"queued": True, "wake": "none"}
    cmd = host_command(req)
    layout, agent = st.get("layout", "tab"), st.get("agent", "claude")
    if layout == "cmux" and st.get("cli_surface"):
        try:
            subprocess.run(["cmux", "send", "--surface", st["cli_surface"], cmd + "\n"], check=False, timeout=5)
            return {"queued": True, "wake": "cmux", "command": cmd}
        except Exception as e:
            return {"queued": True, "wake": "cmux-failed", "command": cmd, "error": str(e)}
    if agent == "codex":
        return {"queued": True, "fallback": "paste", "command": cmd}
    return {"queued": True, "wake": "waiter", "command": cmd}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") or ctype == "application/json" else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def page(self, mode, lid, slug=""):
        with open(TMPL) as f:
            html = f.read()
        html = html.replace("__MODE__", mode).replace("__LESSON__", lid or "").replace("__WS__", slug or "")
        self.send(200, html, "text/html")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        path = u.path
        st = state()
        # /w/<slug>/... pins a page to one workspace; the same routes without the prefix use the last rendered one
        slug = ""
        m = re.match(r"^/w/([a-z0-9-]+)(/.*)?$", path)
        if m:
            slug, path = m.group(1), (m.group(2) or "/")
            if slug not in workspaces():
                return self.send(404, "no such workspace", "text/plain")
        slug = slug or qs.get("ws", [""])[0]
        wsp = ws(slug)
        if path == "/health":
            return self.send(200, "ok", "text/plain")
        if path == "/":
            return self.page("lesson", "", slug)
        if path == "/lessons":
            return self.page("grid", "", slug)
        m = re.match(r"^/lessons/(\d{4})$", path)
        if m:
            return self.page("lesson", m.group(1), slug)
        if path == "/api/pending":
            with PENDING_LOCK:
                return self.send(200, PENDING)
        if path == "/api/state":
            w = (st.get("workspaces") or {}).get(slug, {}) if slug else st
            body = {"ws": wsp, "slug": slug or slug_of(wsp), "current": current(slug), "agent": w.get("agent", st.get("agent", "claude")),
                    "page_version": int(max(os.path.getmtime(TMPL), os.path.getmtime(os.path.join(BOARD, "fig.js")))),
                    "layout": w.get("layout", st.get("layout", "tab")), "streaming": bool(w.get("streaming", st.get("streaming"))),
                    "lessons": lessons_meta(wsp)}
            if qs.get("all"):
                body["workspaces"] = hub()
            return self.send(200, body)
        if path == "/api/lesson":
            lid = qs.get("id", [current(slug)])[0]
            frm = int(qs.get("from", ["0"])[0] or 0)
            h = qs.get("hash", [""])[0]
            return self.send(200, read_lesson(lid, frm, h, wsp))
        if path == "/events":
            return self.events(qs.get("id", [current(slug)])[0], slug)
        if path.startswith("/assets/"):
            return self.static(os.path.join(lessons_dir(wsp), "assets", os.path.basename(path)))
        if path.startswith("/lib/"):
            lib = {"rough.js": os.path.join(ROOT, "node_modules", "roughjs", "bundled", "rough.js"), "fig.js": os.path.join(BOARD, "fig.js")}.get(os.path.basename(path))
            if lib: return self.static(lib)
        if path.startswith("/anim/"):
            rel = os.path.normpath(path[len("/anim/"):])
            if rel.startswith(".."):
                return self.send(404, "no", "text/plain")
            return self.static(os.path.join(BOARD, "anim", rel))
        return self.send(404, "not found", "text/plain")

    def static(self, p):
        if not os.path.isfile(p):
            return self.send(404, "missing", "text/plain")
        ext = os.path.splitext(p)[1].lower()
        ctype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml",
                 ".mp4": "video/mp4", ".webp": "image/webp", ".txt": "text/plain", ".md": "text/plain"}.get(ext, "application/octet-stream")
        with open(p, "rb") as f:
            self.send(200, f.read(), ctype)

    def events(self, lid, slug=""):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        last = None
        last_state = None
        try:
            while True:
                st = state()
                w = (st.get("workspaces") or {}).get(slug, {}) if slug else st
                cur = current(slug)
                p = lesson_path(lid or cur, ws(slug))
                sig = None
                if p and os.path.exists(p):
                    s = os.stat(p)
                    sig = (s.st_mtime_ns, s.st_size)
                ssig = (cur, w.get("streaming", st.get("streaming")), w.get("rev", st.get("rev")))
                if sig != last or ssig != last_state:
                    last, last_state = sig, ssig
                    payload = json.dumps({"current": cur, "streaming": bool(w.get("streaming", st.get("streaming"))), "size": sig[1] if sig else 0})
                    self.wfile.write(f"event: change\ndata: {payload}\n\n".encode())
                    self.wfile.flush()
                else:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                time.sleep(0.3)
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b""
        if u.path == "/ask":
            try:
                req = json.loads(raw.decode() or "{}")
            except Exception:
                return self.send(400, {"error": "bad json"})
            req["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            req.setdefault("lesson", current(req.get("ws")))
            # dedupe: same explain text+block+lesson within 120 s is a repeat click, not a new question
            if req.get("kind") == "explain":
                try:
                    key = (req.get("text"), req.get("block"), req.get("lesson"), req.get("depth"), req.get("parent"), req.get("grow"))
                    now = time.time()
                    for line in reversed(open(QUEUE).read().splitlines()[-20:]):
                        r = json.loads(line)
                        if r.get("kind") == "explain" and (r.get("text"), r.get("block"), r.get("lesson"), r.get("depth"), r.get("parent"), r.get("grow")) == key \
                           and now - calendar.timegm(time.strptime(r.get("ts", "1970-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ")) < 120:
                            return self.send(200, {"queued": False, "duplicate": True})
                except Exception as e:
                    sys.stderr.write(f"dedupe error: {e}\n")
            with open(QUEUE, "a") as f:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
            return self.send(200, wake(req))
        if u.path == "/api/listen":
            # The mic lives on the bridge, not in the page: bin/listen.sh uses on-device
            # Apple Speech, so it works in every host (cmux WKWebView, Claude app, Codex
            # app) rather than only in Chrome, which is all the Web Speech API would give.
            if not LISTEN_LOCK.acquire(blocking=False):
                return self.send(200, {"error": "already listening"})
            try:
                sh = os.path.join(BOARD, "..", "bin", "listen.sh")
                r = subprocess.run([sh], capture_output=True, text=True, timeout=90)
                text = (r.stdout or "").strip()
                if r.returncode != 0 or not text:
                    return self.send(200, {"error": (r.stderr or "no transcript").strip()[:200]})
                return self.send(200, {"text": text})
            except subprocess.TimeoutExpired:
                return self.send(200, {"error": "listening timed out"})
            except Exception as e:
                return self.send(200, {"error": str(e)[:200]})
            finally:
                LISTEN_LOCK.release()
        if u.path == "/render":
            # render.sh pokes this after updating state.json; bump rev so SSE clients reload
            bump_rev(urllib.parse.parse_qs(u.query).get("ws", [None])[0])
            return self.send(200, {"ok": True})
        return self.send(404, {"error": "no"})


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    srv.daemon_threads = True
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
