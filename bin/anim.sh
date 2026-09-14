#!/bin/zsh
# anim.sh <Scene> <name> [ws] [quality]   Render a Manim animation from board/anim/scenes.py to $WS/lessons/assets/<name>.mp4 (quality: l|m|h, default m).
# Use for motion that is the lesson (a limit closing in, a rotation, a wave travelling). Still figures use bin/fig.mjs.
set -e
DIR=${0:A:h:h}; SCENE=$1; NAME=$2; WS=${3:-$PWD}; Q=${4:-m}; [ -d "$WS/lessons" ] || WS=$WS/learn
[ -n "$SCENE" ] && [ -n "$NAME" ] || { echo "usage: anim.sh <Scene> <name> [ws] [l|m|h]" >&2; exit 2; }
mkdir -p "$WS/lessons/assets"; cd "$DIR"
MEDIA=${BLACKBOARD_HOME:-$HOME/.cache/blackboard}/media; mkdir -p "$MEDIA"
if ! manim -q$Q --media_dir "$MEDIA" -o "$NAME" board/anim/scenes.py "$SCENE" >/tmp/anim-$$.log 2>&1; then tail -20 /tmp/anim-$$.log >&2; rm -f /tmp/anim-$$.log; exit 1; fi
rm -f /tmp/anim-$$.log
SRC=$(find "$MEDIA/videos" -name "$NAME.mp4" 2>/dev/null | head -1); [ -n "$SRC" ] || { echo "manim produced no $NAME.mp4" >&2; exit 1; }
cp "$SRC" "$WS/lessons/assets/$NAME.mp4"; echo "assets/$NAME.mp4"
