#!/usr/bin/env bash
# update.sh — keep a git-cloned Blackboard current. Run at the start of every /blackboard.
# At most one check a day; fast-forward only; silent when offline, already current, or the checkout has local changes.
# A copy without .git (an rsync install) is left alone. Prints one line only when it updated.
# BLACKBOARD_UPDATE=0 turns it off; BLACKBOARD_UPDATE=force skips the once-a-day wait.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
[ "${BLACKBOARD_UPDATE:-1}" = 0 ] && exit 0
[ -d "$DIR/.git" ] || exit 0
STAMP="${XDG_CACHE_HOME:-$HOME/.cache}/blackboard/last-update-check"
if [ "${BLACKBOARD_UPDATE:-1}" != force ] && [ -f "$STAMP" ] && [ -n "$(find "$STAMP" -mmin -1440 2>/dev/null)" ]; then exit 0; fi
mkdir -p "$(dirname "$STAMP")" && touch "$STAMP"
g() { git -C "$DIR" "$@"; }
[ -z "$(g status --porcelain --untracked-files=no 2>/dev/null)" ] || exit 0
UP=$(g rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null) || exit 0
# 8-second cap on the network call, without depending on GNU timeout.
( GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5" \
  perl -e 'alarm 8; exec @ARGV' git -C "$DIR" fetch -q ) 2>/dev/null || exit 0
OLD=$(g rev-parse HEAD); NEW=$(g rev-parse "$UP")
[ "$OLD" = "$NEW" ] && exit 0
g merge-base --is-ancestor "$OLD" "$NEW" || exit 0
g merge -q --ff-only "$UP" >/dev/null 2>&1 || exit 0
N=$(g rev-list --count "$OLD..$NEW")
echo "Blackboard updated ($N new commit$([ "$N" = 1 ] || echo s)): $(g log -1 --format=%s)"
if g diff --name-only "$OLD" "$NEW" | grep -q '^package\(-lock\)\?\.json$'; then (cd "$DIR" && npm install --silent >/dev/null 2>&1) || true; fi
if g diff --name-only "$OLD" "$NEW" | grep -q '^board/bridge\.py$' && [ "$(uname)" = Darwin ]; then
  launchctl kickstart -k "gui/$(id -u)/com.blackboard.bridge" >/dev/null 2>&1 || true
fi
exit 0
