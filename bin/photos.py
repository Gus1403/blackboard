#!/usr/bin/env python3
"""photos.py <lesson.md>  -- resolve every `::: photo` block that has a query: but no src:.

For each one, fetch a licensed photo with bin/image.sh (Openverse → Wikimedia Commons), save it as
lessons/assets/<NNNN>-p<k>.jpg and write `src:` and `credit:` lines into the block. The board shows a
"finding a photo" placeholder until then and re-renders when the file changes. Run by render.sh in the
background; safe to re-run (blocks with src: are skipped)."""
import os, re, subprocess, sys

path = os.path.abspath(sys.argv[1])
ws = os.path.dirname(os.path.dirname(path))
lid = re.match(r"^(\d{4})", os.path.basename(path)).group(1)
here = os.path.dirname(os.path.abspath(__file__))
src = open(path).read()

blocks = list(re.finditer(r"^::: photo[^\n]*\n(.*?)^:::\s*$", src, re.S | re.M))
todo = [(i, m) for i, m in enumerate(blocks, 1) if re.search(r"^query:", m.group(1), re.M) and not re.search(r"^(src|missing):", m.group(1), re.M)]
if not todo:
    sys.exit(0)

results = {}
for k, m in todo:
    q = re.search(r"^query:\s*(.+)$", m.group(1), re.M).group(1).strip()
    r = subprocess.run([os.path.join(here, "image.sh"), q, f"{lid}-p{k}", ws], capture_output=True, text=True)
    lines = dict(l.split(":", 1) for l in r.stdout.strip().splitlines() if ":" in l) if r.returncode == 0 else {}
    if lines.get("photo"):
        results[k] = (lines["photo"].strip(), lines.get("credit", "").strip())
    else:
        sys.stderr.write(f"photo {k} ({q}): {r.stderr.strip()[-200:]}\n")
        results[k] = (None, "")  # mark it so the board drops the placeholder instead of waiting forever

# write back (re-read: the writer may have appended since)
s = open(path).read()
out, pos = [], 0
for k, m in enumerate(re.finditer(r"^::: photo[^\n]*\n(.*?)^:::\s*$", s, re.S | re.M), 1):
    if k not in results or re.search(r"^(src|missing):", m.group(1), re.M):
        continue
    photo, credit = results[k]
    body_end = m.start(1) + len(m.group(1))
    insert = (f"src: {photo}\n" + (f"credit: {credit}\n" if credit else "")) if photo else "missing: no licensed photo found\n"
    out.append(s[pos:body_end]); out.append(insert); pos = body_end
out.append(s[pos:])
open(path, "w").write("".join(out))
print(f"resolved {len(results)} of {len(todo)} photos")
