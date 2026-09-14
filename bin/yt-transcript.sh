#!/bin/zsh
# yt-transcript.sh <url | "ytsearchN:terms"> [outdir]   Print the transcript as plain text with [mm:ss] markers; save under outdir/<id>.txt when given.
set -e
Q=$1; OUT=${2:-}
TMP=$(mktemp -d)
yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs 'en,en-US,pt-BR,pt' --sub-format vtt --no-playlist \
  --print-to-file '%(id)s	%(title)s	%(channel)s	%(webpage_url)s' "$TMP/meta.tsv" -o "$TMP/%(id)s" "$Q" >/dev/null 2>&1 || true
VTT=$(ls "$TMP"/*.vtt 2>/dev/null | head -1)
[ -n "$VTT" ] || { echo "no subtitles found for $Q" >&2; exit 1; }
python3 - "$VTT" "$TMP/meta.tsv" "$OUT" <<'PY'
import re,sys,os
vtt,meta,out=sys.argv[1:]
m=open(meta).read().strip().split("\n")[0].split("\t") if os.path.exists(meta) else ["","","",""]
vid,title,channel,url=(m+["","","",""])[:4]
lines=open(vtt,encoding="utf-8").read().splitlines()
cur=None; seen=[]; last=""
def t2s(t):
    h,mi,s=t.split(":"); return int(h)*3600+int(mi)*60+float(s)
for l in lines:
    mm=re.match(r"(\d+:\d+:\d+\.\d+) --> ",l)
    if mm: cur=t2s(mm.group(1)); continue
    if not l.strip() or l.startswith(("WEBVTT","Kind:","Language:")) or re.match(r"^\d+$",l): continue
    txt=re.sub(r"<[^>]+>","",l).strip()
    if txt and txt!=last:
        seen.append((cur or 0,txt)); last=txt
text=[]; mark=-60
for t,x in seen:
    if t-mark>=60: text.append(f"\n[{int(t//60):02d}:{int(t%60):02d}] "); mark=t
    text.append(x+" ")
body="".join(text).strip()
hdr=f"# {title}\n# {channel} · {url}\n\n"
print(hdr+body)
if out:
    os.makedirs(out,exist_ok=True); open(os.path.join(out,f"{vid or 'video'}.txt"),"w").write(hdr+body)
PY
rm -rf "$TMP"
