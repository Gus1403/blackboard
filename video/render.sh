#!/usr/bin/env bash
# render.sh [project-dir] [workers]: full render (resumable) + finish + contact sheets, then writes RENDERED.
# project-dir defaults to the directory holding this script. workers defaults to VIDEO_WORKERS or min(4, cpus).
# One render per project at a time: an exclusive kernel lock on <project>/.render.lock (holder pid inside).
# Optional machine-wide serialisation: VIDEO_RENDER_LOCK=<lock file path>, waiting at most
# VIDEO_RENDER_LOCK_WAIT seconds (default 0: fail at once if another render holds it).
# Exit: 0 done, 1 render/finish failed (see render.log / finish.log), 75 lock busy.
set -uo pipefail
D="${1:-$(cd "$(dirname "$0")" && pwd)}"
WORKERS="${2:-${VIDEO_WORKERS:-}}"
cd "$D" || { echo "render.sh: no such project dir: $D" >&2; exit 1; }
D="$(pwd)"
trap 'exit 130' INT TERM
# lock <fd> <file> <max wait seconds>: flock(2) on <file>, already open on fd <fd> of this shell. The lock belongs to
# that open file, which this shell and every render child share, so the kernel drops it when the last of them exits:
# a crashed render leaves no stale lock to take over. The file stays in place (deleting it would let two renders
# lock two different files).
lock() {
  python3 - "$1" "$2" "$3" "$$" <<'PY'
import fcntl, os, sys, time
fd, path, wait, pid = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
try:
    end = time.monotonic() + float(wait)
except ValueError:
    sys.exit(f"render.sh: lock wait must be a number of seconds, got {wait!r}")
while True:
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        break
    except BlockingIOError:
        left = end - time.monotonic()
        if left <= 0:
            try:
                holder = open(path).read().strip() or "?"
            except OSError:
                holder = "?"
            print(f"render.sh: lock busy: {path} held by pid {holder}", file=sys.stderr)
            sys.exit(75)
        time.sleep(min(1.0, left))
os.ftruncate(fd, 0)
os.write(fd, f"{pid}\n".encode())
PY
}
exec 9>>"$D/.render.lock" || { echo "render.sh: cannot open lock file $D/.render.lock (a directory left by an older render.sh? remove it when no render runs)" >&2; exit 1; }
lock 9 "$D/.render.lock" 0 || exit $?
if [ -n "${VIDEO_RENDER_LOCK:-}" ]; then
  exec 8>>"$VIDEO_RENDER_LOCK" || { echo "render.sh: cannot open lock file $VIDEO_RENDER_LOCK" >&2; exit 1; }
  lock 8 "$VIDEO_RENDER_LOCK" "${VIDEO_RENDER_LOCK_WAIT:-0}" || exit $?
fi
rm -f RENDERED
mkdir -p qa
node capture.mjs all $WORKERS > render.log 2>&1 || { echo RENDER_FAILED >> render.log; echo "render.sh: RENDER_FAILED, see $D/render.log" >&2; exit 1; }
./finish.sh > finish.log 2>&1 || { echo FINISH_FAILED >> finish.log; echo "render.sh: FINISH_FAILED, see $D/finish.log" >&2; exit 1; }
rm -f qa/sheet_*.jpg
ffmpeg -v error -y -i final.mp4 -vf "fps=1/20,scale=384:-1,tile=6x8" qa/sheet_%d.jpg
echo DONE > RENDERED
echo "render.sh: DONE $D/final.mp4"
