#!/usr/bin/env python3
"""lint.py <lesson.md>  -- warn about derivation steps written sideways.
A display equation with more than one `=` or any `\\Rightarrow` outside an aligned/cases block is a chain of steps on one line.
The board's rule is one operation per line, reason in the margin. Prints warnings; exit 0 always."""
import re, sys
s = open(sys.argv[1]).read()
warn = 0
for m in re.finditer(r"\$\$(.*?)\$\$", s, re.S):
    body = m.group(1)
    if re.search(r"\\begin\{(aligned|cases|array|matrix)", body):
        continue
    # several independent formulas on one line (a reference table) are separated by \qquad, \quad or commas; judge each chunk
    chunks = re.split(r"\\qquad|\\quad|,\s", body)
    eq = max(len(re.findall(r"(?<![<>!:])=(?!=)", c)) for c in chunks)
    arrows = body.count("\\Rightarrow") + body.count("\\implies")
    if eq >= 3 or arrows >= 2 or (arrows == 1 and eq >= 2):
        line = s[:m.start()].count("\n") + 1
        print(f"  lint: line {line}: sideways derivation ({eq} '=' on one line). Use \\begin{{aligned}} with one step per line.", file=sys.stderr); warn += 1
for m in re.finditer(r"(?<!\$)\$(?!\$)([^$\n]+)\$(?!\$)", s):
    eqi = len(re.findall(r"(?<![<>!:])=(?!=)", m.group(1)))
    if eqi >= 3 or ("\\Rightarrow" in m.group(1) and eqi >= 2):
        line = s[:m.start()].count("\n") + 1
        print(f"  lint: line {line}: a chain of steps inside inline math. Break it into a display block, one step per line.", file=sys.stderr); warn += 1
if warn: print(f"  lint: {warn} sideways step(s). TEMPLATES.md: one operation per line.", file=sys.stderr)
