#!/usr/bin/env python3
"""quiz.py <lesson.md> '<request json>'

Headless quiz worker for the board. Called by bridge.py in a background thread,
the same way bin/explain.py is. Two operations:

  {"op":"generate","topic":"the three rules"|"all","mode":"cards"|"mcq","count":4,"pending":"p1"}
      Writes new ::: card / ::: mcq items into the lesson's ::: quiz block.
      Prints {"ids": ["c4","c5"], "n": 2}.

  {"op":"grade","item":"c1","answer":"what the student said","pending":"p2"}
      Grades one flashcard answer 1-5 against its must: lines, writes a
      ::: score block under the card, appends to learning-records/quiz-log.jsonl.
      Prints {"item":"c1","score":4,"rationale":"...","missing":"..."}.

The lesson file change is picked up by the bridge's SSE loop; no render call needed.
"""
import json, os, re, shutil, subprocess, sys, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path, req = sys.argv[1], json.loads(sys.argv[2])
op = req.get("op", "generate")
src = open(path).read()


def course_mode(s):
    return bool(re.search(r"^course:\s*\S", s, re.M))


def quiz_block(s):
    """(start, end, inner) of the ::: quiz container, or None."""
    m = re.search(r"^::: quiz[^\n]*\n", s, re.M)
    if not m:
        return None
    i, depth = m.end(), 1
    while i < len(s) and depth > 0:
        nl = s.find("\n", i)
        line = s[i:nl if nl >= 0 else len(s)]
        if line.startswith("::: "):
            depth += 1
        elif re.match(r"^:::\s*$", line):
            depth -= 1
            if depth == 0:
                return m.start(), i, s[m.end():i]
        i = nl + 1 if nl >= 0 else len(s)
    return None


def next_id(s, prefix):
    ids = [int(x) for x in re.findall(rf"^::: (?:card|mcq|score) {prefix}(\d+)", s, re.M)]
    return (max(ids) + 1) if ids else 1


def topics_of(inner):
    m = re.search(r"^topics:\s*(.+)$", inner, re.M)
    return [t.strip() for t in m.group(1).split(",") if t.strip()] if m else []


def existing_questions(inner):
    """Question text of every item already in the quiz, so the writer does not repeat one."""
    out = []
    for m in re.finditer(r"^::: (?:card|mcq) \S+[^\n]*\n(.*?)^:::\s*$", inner, re.S | re.M):
        body = [l for l in m.group(1).split("\n") if l.strip() and not re.match(r"^(must|why|answer):", l.strip())]
        if body:
            out.append(body[0].strip()[:120])
    return out


def strip_math_fences(t):
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", t.strip())


def run_writer(prompt, model_env="BLACKBOARD_WRITER_MODEL", default_model=None, timeout=120):
    if shutil.which("claude"):
        cmd = ["claude", "-p", prompt, "--output-format", "text", "--no-session-persistence"]
        model = os.environ.get(model_env) or default_model
        if model:
            cmd += ["--model", model]
    elif shutil.which("codex"):
        cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt]
    else:
        raise RuntimeError("no headless writer: install Claude Code (claude) or Codex (codex)")
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE")}
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=SKILL, env=env)
    out = (r.stdout or "").strip()
    if r.returncode != 0 or not out:
        raise RuntimeError((r.stderr or out or "writer failed")[:300])
    if cmd[0] == "codex":
        out = out.strip().split("\n\n")[-1].strip()
    return out


def json_from(text):
    t = strip_math_fences(text)
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"[\[{].*[\]}]", t, re.S)
    if not m:
        raise RuntimeError("writer did not return JSON: " + t[:200])
    return json.loads(m.group(0))


LESSON_BODY = re.sub(r"^---\n.*?\n---\n", "", src, count=1, flags=re.S)
QB = quiz_block(src)

GEN_RULES = """You write quiz items for a student revising one lesson on a black board.

Hard rules, from the skill's QUIZ.md:
- Only quiz what the lesson explained. Never test a term the lesson did not introduce.
- One idea per question, shortest possible answer. No compound questions.
- Prefer "why / how / what happens if" over "what is".
- No yes/no and no true/false. The cue must force generation, not recognition.
- No "list all of". Ask for one member with a discriminating cue, or for the order.
- At least one item in four is transfer to a case the lesson did not show.
- Reuse the lesson's own examples and numbers as cues.
- Never repeat a question already in the quiz.
- Plain and direct. No "students often", no praise, no throat-clearing, no em dashes.
- LaTeX with $...$ is fine for symbols. Keep every string on one line.
"""

CARD_FORMAT = """Return only a JSON array, no prose around it. Each element:
{"q": "the question", "answer": "the model answer, one or two sentences", "must": ["must-have point 1", "must-have point 2"]}
"answer" is shown on the back of the card after the student answers: the answer a strong student would give, complete and short.
"must" holds 2 to 4 points a correct spoken answer has to contain. They are graded against, never shown before the flip."""

MCQ_FORMAT = """Return only a JSON array, no prose around it. Each element:
{"q": "the stem", "options": ["...","...","..."], "key": 0, "why": "one line shown after any pick"}
Exactly 3 options. "key" is the 0-based index of the single defensible answer.
Every wrong option is a real misconception or a common procedural error.
Options equal in length, grammar and specificity. No "all of the above", no negatives, no absolutes.
The stem must be answerable before reading the options. The key is not the longest option."""


def do_generate():
    if not QB:
        return {"error": "lesson has no ::: quiz block"}
    start, end, inner = QB
    topic = (req.get("topic") or "all").strip()
    mode = req.get("mode", "cards")
    count = max(1, min(8, int(req.get("count") or 4)))
    tops = topics_of(inner)
    scope = ("the whole lesson, interleaving these sub-topics: " + ", ".join(tops)) if topic.lower() in ("all", "all topics", "") else f'the sub-topic "{topic}"'
    seen = existing_questions(inner)
    avoid = ("\nQuestions already in the quiz, do not repeat or re-word these:\n" + "\n".join("- " + q for q in seen)) if seen else ""
    fmt = MCQ_FORMAT if mode == "mcq" else CARD_FORMAT
    prompt = f"""{GEN_RULES}
Write exactly {count} items covering {scope}.

{fmt}
{avoid}

The lesson:
{LESSON_BODY}"""
    items = json_from(run_writer(prompt))
    if not isinstance(items, list):
        return {"error": "writer did not return a list"}

    blocks, ids = [], []
    if mode == "mcq":
        n = next_id(src, "q")
        for it in items[:count]:
            opts = [str(o).replace("\n", " ") for o in (it.get("options") or [])][:3]
            if not it.get("q") or len(opts) < 2:
                continue
            key = "abc"[min(max(int(it.get("key") or 0), 0), len(opts) - 1)]
            iid = f"q{n}"; n += 1; ids.append(iid)
            lines = [f"::: mcq {iid} {key}", str(it["q"]).replace("\n", " ")]
            lines += [f"- {o}" for o in opts]
            lines.append("why: " + str(it.get("why") or "").replace("\n", " "))
            lines.append(":::")
            blocks.append("\n".join(lines))
    else:
        n = next_id(src, "c")
        for it in items[:count]:
            if not it.get("q"):
                continue
            iid = f"c{n}"; n += 1; ids.append(iid)
            musts = [str(m).replace("\n", " ") for m in (it.get("must") or [])][:4]
            lines = [f"::: card {iid}", str(it["q"]).replace("\n", " ")]
            if it.get("answer"):
                lines.append("answer: " + str(it["answer"]).replace("\n", " "))
            lines += [f"must: {m}" for m in musts]
            lines.append(":::")
            blocks.append("\n".join(lines))

    if not blocks:
        return {"error": "writer returned no usable items"}
    add = "\n" + "\n\n".join(blocks) + "\n"
    out = src[:end] + add + src[end:]
    open(path, "w").write(out)
    return {"ids": ids, "n": len(ids)}


GRADE_RULES = """You grade one spoken or typed answer from a student revising a lesson, on a 1 to 5 scale.

| Score | Meaning |
|---|---|
| 5 | All must-have points, precise terms, no hedging, adds a correct elaboration |
| 4 | Core mechanism right; one omission or imprecision; no misconception |
| 3 | Gist only: vague or incomplete, but no false claim |
| 2 | At least one identifiable false belief |
| 1 | Nothing, off-topic, or "I don't know" |

Any explicit false statement caps the score at 2. Repeating the question's wording never earns 5.
Verbose is not complete. Speech-to-text noise, missing punctuation and informal phrasing are not errors:
grade the meaning, not the transcript.

Return only JSON, no prose around it:
{"score": 4, "rationale": "one line, plain, no praise", "missing": "the must-have points not said, or empty string"}
"rationale" is one short sentence saying what was right or wrong. Never "great job", never "almost there"."""


def card_at(item):
    m = re.search(rf"^::: card {re.escape(item)}[^\n]*\n(.*?)^:::\s*$", src, re.S | re.M)
    if not m:
        return None, None, None
    body = m.group(1)
    musts = [l.strip()[5:].strip() for l in body.split("\n") if l.strip().startswith("must:")]
    ans = next((l.strip()[7:].strip() for l in body.split("\n") if l.strip().startswith("answer:")), "")
    q = "\n".join(l for l in body.split("\n") if l.strip() and not l.strip().startswith(("must:", "answer:"))).strip()
    return q, musts + ([f"(model answer) {ans}"] if ans else []), m.end()


def log_score(item, score, misconception):
    d = os.path.join(os.path.dirname(os.path.dirname(path)), "learning-records")
    os.makedirs(d, exist_ok=True)
    lid = re.match(r"^(\d{4})", os.path.basename(path))
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "lesson": lid.group(1) if lid else "",
           "topic": req.get("topic", ""), "item": item, "mode": "cards",
           "score": score, "misconception": misconception or None}
    with open(os.path.join(d, "quiz-log.jsonl"), "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def do_grade():
    item = req.get("item", "")
    answer = (req.get("answer") or "").strip()
    q, musts, after = card_at(item)
    if q is None:
        return {"error": f"card {item} not found"}
    if not answer:
        return {"error": "no answer given"}
    prompt = f"""{GRADE_RULES}

The question: {q}

The must-have points:
{chr(10).join('- ' + m for m in musts) if musts else '- (none recorded; grade against the lesson)'}

Lesson context:
{LESSON_BODY[:6000]}

The student's answer:
{answer}"""
    r = json_from(run_writer(prompt, model_env="BLACKBOARD_GRADER_MODEL",
                             default_model="claude-haiku-4-5-20251001", timeout=90))
    score = min(5, max(1, int(r.get("score") or 1)))
    rationale = str(r.get("rationale") or "").strip()
    missing = str(r.get("missing") or "").strip()

    body = [f"*\"{answer.replace(chr(10), ' ')}\"*", "", rationale]
    if missing:
        body += ["", f"Missing: {missing}"]
    blk = f"\n\n::: score {item} {score}\n" + "\n".join(body) + "\n:::\n"
    s = re.sub(rf"\n*::: score {re.escape(item)} \d+\n.*?\n:::", "", src, flags=re.S)
    after2 = re.search(rf"^::: card {re.escape(item)}[^\n]*\n.*?^:::\s*$", s, re.S | re.M)
    s = s[:after2.end()] + blk + s[after2.end():] if after2 else s + blk
    open(path, "w").write(s)
    log_score(item, score, missing if score <= 2 else None)
    return {"item": item, "score": score, "rationale": rationale, "missing": missing}


try:
    out = do_grade() if op == "grade" else do_generate()
except Exception as e:
    out = {"error": str(e)[:300]}
out["pending"] = req.get("pending")
print(json.dumps(out, ensure_ascii=False))
sys.exit(1 if "error" in out else 0)
