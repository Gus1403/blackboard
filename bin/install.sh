#!/bin/zsh
# One-time setup so nobody has to know the board's address (macOS; idempotent, safe to re-run).
#  1. launchd agent com.blackboard.bridge: the bridge starts at login and restarts if it dies.
#  2. ~/Applications/Blackboard.app (also added to the Dock): click it -> the all-lessons menu
#     in the default browser, starting the bridge first if needed.
# render.sh runs this once, the first time it finds the agent missing. --force rebuilds both.
set -e
BIN=${0:A:h}; BOARD=${BIN:h}/board
HOME_DIR=${BLACKBOARD_HOME:-$HOME/.cache/blackboard}; mkdir -p "$HOME_DIR"
PORT=${BLACKBOARD_PORT:-7331}
LABEL=com.blackboard.bridge
PLIST=$HOME/Library/LaunchAgents/$LABEL.plist
APP=$HOME/Applications/Blackboard.app
PY=$(command -v python3)
[ "$(uname)" = Darwin ] || { echo "install.sh: macOS only; start the board with board/render.sh"; exit 0; }
FORCE=; [ "$1" = --force ] && FORCE=1

# 1. always-on bridge. PATH is captured now because explain/quiz call the agent CLIs headless.
if [ -n "$FORCE" ] || [ ! -f "$PLIST" ] || ! grep -q "$BOARD/bridge.py" "$PLIST"; then
  mkdir -p "${PLIST:h}"
  cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>$BOARD/bridge.py</string></array>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>$PATH</string>
    <key>BLACKBOARD_HOME</key><string>$HOME_DIR</string>
    <key>BLACKBOARD_PORT</key><string>$PORT</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME_DIR/bridge.log</string>
  <key>StandardErrorPath</key><string>$HOME_DIR/bridge.log</string>
</dict></plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  # a bridge started by hand (render.sh fallback) holds the port; hand it over to launchd
  pkill -f "$BOARD/bridge.py" 2>/dev/null || true
  pkill -f "blackboard/board/bridge.py" 2>/dev/null || true
  sleep 0.5
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  for i in {1..30}; do curl -s -m 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break; sleep 0.2; done
  echo "blackboard: bridge runs at login ($LABEL)"
fi

# 2. the app icon
if [ -n "$FORCE" ] || [ ! -d "$APP" ]; then
  mkdir -p "${APP:h}"
  rm -rf "$APP"
  osacompile -o "$APP" -e "do shell script \"curl -s -m 1 http://127.0.0.1:$PORT/health >/dev/null || (launchctl kickstart gui/\$(id -u)/$LABEL; for i in $(seq 1 40); do curl -s -m 1 http://127.0.0.1:$PORT/health >/dev/null && break; sleep 0.3; done); true\"" -e "open location \"http://localhost:$PORT/\""
  # icon: board/app-icon.png (1024 px, transparent; source board/app-icon.svg)
  T=$(mktemp -d); SET=$T/icon.iconset; mkdir -p "$SET"
  cp "$BOARD/app-icon.png" "$T/sq.png"
  for s in 16 32 128 256 512; do
    sips -z $s $s "$T/sq.png" --out "$SET/icon_${s}x${s}.png" >/dev/null
    sips -z $((s*2)) $((s*2)) "$T/sq.png" --out "$SET/icon_${s}x${s}@2x.png" >/dev/null
  done
  iconutil -c icns "$SET" -o "$APP/Contents/Resources/applet.icns" && touch "$APP"
  rm -rf "$T"
  # Dock, once
  if ! defaults read com.apple.dock persistent-apps 2>/dev/null | grep -q "Blackboard.app"; then
    defaults write com.apple.dock persistent-apps -array-add "<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>file://$APP/</string><key>_CFURLStringType</key><integer>15</integer></dict></dict></dict>"
    killall Dock 2>/dev/null || true
  fi
  echo "blackboard: app at $APP (and in the Dock)"
fi
