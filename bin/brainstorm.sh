#!/bin/zsh
# brainstorm.sh <lesson.md> "note" ["note" ...]   Put planning notes on the board while the lesson is researched.
# brainstorm.sh <lesson.md> --clear                Wipe them (the board also wipes them itself when the first block lands).
# Each call sends the WHOLE list: the page writes new lines by hand and erases lines that were removed or moved.
# Style: "Explain: <topic>", "Goal: ...", "Sources:" then "- <source>" lines, "Outline:" then "- <part>" lines.
# Needs the lesson rendered first with render.sh <lesson.md> --live (title only is fine), so the board shows it.
HOME_DIR=${BLACKBOARD_HOME:-$HOME/.cache/blackboard}
[ -n "$1" ] || { echo "usage: brainstorm.sh <lesson.md> \"note\" ... | --clear"; exit 1; }
python3 - "$HOME_DIR/state.json" "$@" <<'PY'
import json, os, re, sys, time
st_path, lesson, *lines = sys.argv[1:]
lesson = os.path.abspath(lesson)
m = re.match(r"(\d{4})", os.path.basename(lesson))
if not m: sys.exit("brainstorm: lesson file must be named NNNN-slug.md")
ws = os.path.dirname(os.path.dirname(lesson))
try: st = json.load(open(st_path))
except Exception: st = {}
wss = st.setdefault("workspaces", {})
slug = next((k for k, w in wss.items() if os.path.abspath(w.get("path", "")) == ws), None)
if not slug:
    base = os.path.basename(ws)
    if base == "learn": base = os.path.basename(os.path.dirname(ws))
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "ws"
w = wss.setdefault(slug, {"path": ws})
w["brainstorm"] = {"lesson": m.group(1), "lines": [] if lines == ["--clear"] else lines, "rev": int(time.time() * 1000)}
tmp = st_path + ".tmp"; json.dump(st, open(tmp, "w")); os.replace(tmp, st_path)
print(f"brainstorm: {len(w['brainstorm']['lines'])} line(s) on {slug}/{m.group(1)}")
PY
