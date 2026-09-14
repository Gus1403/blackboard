#!/bin/zsh
# fig-check.sh <template> <spec.json> [name]   Render a figure spec to SVG + PNG in the scratch dir and print both paths, so the agent can look before placing it.
set -e
DIR=${0:A:h:h}; TPL=$1; SPEC=$2; NAME=${3:-fig}; OUT=${TMPDIR:-/tmp}/blackboard-fig; mkdir -p "$OUT"
node "$DIR/bin/fig.mjs" "$TPL" "$SPEC" "$OUT/$NAME.svg"
# wrap in a dark page so the PNG matches the board; qlmanage renders SVG without web fonts (layout check only)
python3 - "$OUT/$NAME.svg" <<'PY'
import sys,re
p=sys.argv[1]; s=open(p).read()
s=s.replace('<svg ', '<svg style="background:#0c0c0c" ',1); open(p,'w').write(s)
PY
qlmanage -t -s 1440 -o "$OUT" "$OUT/$NAME.svg" >/dev/null 2>&1 && echo "$OUT/$NAME.svg.png" || echo "png failed; open $OUT/$NAME.svg" >&2
