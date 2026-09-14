#!/bin/zsh
# still.sh <Scene> <name> [ws]   Render a Manim scene from board/anim/scenes.py as a PNG, crop it to its content, save to $WS/lessons/assets/<name>.png.
# Prints the path to use in `::: figure`. Manim's 16:9 frame leaves wide black margins; the crop is what makes the figure large on the board.
set -e
DIR=${0:A:h:h}; SCENE=$1; NAME=$2; WS=${3:-$PWD}; [ -d "$WS/lessons" ] || WS=$WS/learn
[ -n "$SCENE" ] && [ -n "$NAME" ] || { echo "usage: still.sh <Scene> <name> [ws]" >&2; exit 2; }
mkdir -p "$WS/lessons/assets"
cd "$DIR"
MEDIA=${BLACKBOARD_HOME:-$HOME/.cache/blackboard}/media; mkdir -p "$MEDIA"
if ! manim -s -qh --media_dir "$MEDIA" -o "$NAME" board/anim/scenes.py "$SCENE" >/tmp/still-$$.log 2>&1; then tail -20 /tmp/still-$$.log >&2; rm -f /tmp/still-$$.log; exit 1; fi
rm -f /tmp/still-$$.log
SRC=$(find "$MEDIA/images" -name "$NAME.png" 2>/dev/null | head -1)
[ -n "$SRC" ] || { echo "manim produced no $NAME.png" >&2; exit 1; }
PY="$(dirname "$(readlink -f "$(which manim)")")/python"; [ -x "$PY" ] || PY=python3   # manim's venv ships Pillow
"$PY" - "$SRC" "$WS/lessons/assets/$NAME.png" <<'PY'
import os, sys
from PIL import Image, ImageChops
src, dst = sys.argv[1:]
im = Image.open(src).convert("RGB")
bg = Image.new("RGB", im.size, im.getpixel((0, 0)))
diff = ImageChops.add(ImageChops.difference(im, bg), ImageChops.difference(im, bg), 2.0, -10)
box = diff.getbbox() or (0, 0, im.width, im.height)
pad = int(0.035 * im.width)
box = (max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad))
im.crop(box).save(dst, optimize=True)
print(f"assets/{os.path.basename(dst)}")
PY
