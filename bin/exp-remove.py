#!/usr/bin/env python3
"""exp-remove.py <lesson.md> <id>  — delete a ::: exp block (with children) and its ==words== mark if unreferenced."""
import re, sys
path, eid = sys.argv[1], sys.argv[2]
lines = open(path).read().split("\n")
start = next((i for i, l in enumerate(lines) if re.match(rf"^::: exp {re.escape(eid)}(\s|$)", l)), None)
if start is None:
    print(f"{eid} not found"); sys.exit(1)
depth, end = 0, None
for i in range(start, len(lines)):
    if lines[i].startswith("::: "): depth += 1
    elif re.match(r"^:::\s*$", lines[i]):
        depth -= 1
        if depth == 0: end = i; break
block = lines[start:end + 1]
label = re.search(r"\*\*(.+?)\*\*", "\n".join(block))
rest = lines[:start] + lines[end + 1:]
# drop one trailing blank line left behind
if start < len(rest) and start > 0 and rest[start - 1].strip() == "" and (start >= len(rest) or rest[start].strip() == ""):
    del rest[start]
text = "\n".join(rest)
if label:
    w = label.group(1).strip()
    if not re.search(rf"\*\*{re.escape(w)}\*\*", text):
        text = text.replace(f"=={w}==", w)
open(path, "w").write(text)
print(f"removed {eid}" + (f" (+{sum(1 for l in block if l.startswith('::: exp'))-1} nested)" if block else ""))
