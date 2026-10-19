"""An Explain note is inserted after the block it explains, never inside fenced code, an interactive block or a table.

Run: python3 tests/test_explain_anchor.py
"""
import ast, os, re

SRC = os.path.join(os.path.dirname(__file__), "..", "bin", "explain.py")
# explain.py is a script that runs on import; load only the two pure helpers.
tree = ast.parse(open(SRC).read())
ns = {"re": re}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ("atomic_spans", "block_at"):
        exec(compile(ast.Module([node], []), SRC, "exec"), ns)
block_at = ns["block_at"]

LESSON = """Intro paragraph.

```java
public class Pet {
    private int age;

    // constructor: no return type
    public Pet(int age) {
        this.age = age;
    }
}
```

::: interactive trace
{"code": ["a", "b"],

 "steps": []}
:::

| a | b |
|---|---|
| 1 | 2 |

After.
"""


def line_of(text):
    return LESSON.split("\n").index(text) + 1


def check(selected_line, first, last):
    a, b, _ = block_at(LESSON, line_of(selected_line))
    lines = LESSON.split("\n")
    assert lines[a] == first and lines[b] == last, (selected_line, lines[a], lines[b])


check("    // constructor: no return type", "```java", "```")
check("    private int age;", "```java", "```")
check(' "steps": []}', "::: interactive trace", ":::")
check("| 1 | 2 |", "| a | b |", "| 1 | 2 |")
check("Intro paragraph.", "Intro paragraph.", "Intro paragraph.")
print("ok")
