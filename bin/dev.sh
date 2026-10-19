#!/bin/zsh
# Test board for working on this skill without touching the one the user is studying on.
#   bin/dev.sh          start (or reuse) a dev bridge from THIS checkout on port 7390, own state dir, prints the URL
#   bin/dev.sh stop     stop it
# It reads the same lesson folders (state/config copied from the live board) but never writes the live state,
# never restarts the live bridge, and the user's tabs never see it. Open the URL in a NEW background tab only.
BIN=${0:A:h}; BOARD=${BIN:h}/board
DEV_PORT=${BLACKBOARD_DEV_PORT:-7390}; LIVE_HOME=${BLACKBOARD_HOME:-$HOME/.cache/blackboard}; DEV_HOME=$HOME/.cache/blackboard-dev
if [ "$1" = stop ]; then pkill -f "BLACKBOARD_DEV=1" 2>/dev/null; lsof -ti tcp:$DEV_PORT | xargs kill 2>/dev/null; echo "dev board stopped"; exit 0; fi
mkdir -p "$DEV_HOME"
for f in state.json config.json; do [ -f "$LIVE_HOME/$f" ] && cp "$LIVE_HOME/$f" "$DEV_HOME/$f"; done
if ! curl -s -m 1 "http://127.0.0.1:$DEV_PORT/health" >/dev/null 2>&1; then
  BLACKBOARD_DEV=1 BLACKBOARD_HOME="$DEV_HOME" BLACKBOARD_PORT=$DEV_PORT nohup python3 "$BOARD/bridge.py" >"$DEV_HOME/bridge.log" 2>&1 &
  for i in {1..30}; do curl -s -m 1 "http://127.0.0.1:$DEV_PORT/health" >/dev/null 2>&1 && break; sleep 0.2; done
else
  # restart so bridge.py edits take effect (template edits need only a reload of the dev tab)
  [ "$1" = restart ] && { lsof -ti tcp:$DEV_PORT | xargs kill 2>/dev/null; sleep 0.5; exec zsh "$0"; }
fi
echo "http://127.0.0.1:$DEV_PORT/"
