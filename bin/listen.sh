#!/bin/zsh
# listen.sh [locale]   Record one utterance with Apple Speech (on-device) and print the final text. Exit 2 on error.
# Runs the helper inside a tiny .app via `open` so macOS attributes mic/speech permission to "BlackboardListen", not the terminal.
set -e
DIR=${0:A:h}; APP=$DIR/BlackboardListen.app; BIN=$APP/Contents/MacOS/stt-helper
SRC=${STT_HELPER_SRC:-$DIR/stt-helper.swift}
if [ ! -x "$BIN" ]; then
  [ -f "$SRC" ] || { echo "stt-helper.swift not found at $SRC" >&2; exit 2; }
  mkdir -p "$APP/Contents/MacOS"
  swiftc -O "$SRC" -o "$BIN" >/dev/null 2>&1 || { echo "swiftc build failed" >&2; exit 2; }
  codesign -s - -f --deep "$APP" >/dev/null 2>&1 || true
fi
OUT=$(mktemp -t blackboard-listen).ndjson
open -W -a "$APP" --args "${1:-en-US}" "$OUT"
python3 - "$OUT" <<'PY'
import sys,json
for line in open(sys.argv[1],errors="replace"):
    try: r=json.loads(line)
    except Exception: continue
    if r.get("type")=="final": print(r.get("text","")); sys.exit(0)
    if r.get("type")=="error": print(r.get("message",""),file=sys.stderr); sys.exit(2)
print("no final transcript",file=sys.stderr); sys.exit(2)
PY
