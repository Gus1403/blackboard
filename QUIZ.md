# Quiz

Every lesson ships with its own quiz: four to six `::: mcq` items over the whole lesson, written with the lesson. Under them, the **More practice** panel generates four more items on one sub-topic or on **All topics**, as **Flashcards** or **Multiple choice**.

Generation and grading both run headless in `bin/quiz.py`, called by `bridge.py` in a background thread the same way `bin/explain.py` is. Neither wakes the interactive agent, so a quiz works identically in cmux, the Claude app and the Codex app, and nothing lands in the chat.

The interactive agent runs a quiz by hand only when the user asks for one in chat (`/blackboard quiz <topic> <cards|mcq>`).

## Writing flashcard prompts

1. Only quiz what the lesson explained. Never test a term the lesson did not introduce.
2. One idea per question, shortest possible answer. Split compound questions.
3. Prefer "why / how / what happens if" over "what is".
4. No yes/no, no true/false. The cue must force generation, not recognition.
5. No "list all of…". If a list matters, ask for one member with a discriminating cue, or for the order.
6. Cloze only for tightly worded facts or formulas; the gap must not be guessable from grammar.
7. Mix example-first ("here is a case, name the principle") and definition-first ("here is the principle, give a new example"). At least 1 in 4 questions is transfer to an unseen case.
8. One "explain it to someone new in two sentences" per topic; grade the causal chain, not the vocabulary.
9. When two concepts in the lesson are confusable, ask a contrast question ("how does X differ from Y when Z").
10. Reuse the student's own examples and numbers from the lesson as cues.
11. Shuffle: never ask the same surface twice. Re-parameterise numbers, swap the story, change which variable is unknown.

STEM items, in this order across a session: worked example → faded example (student supplies the last step, then the last two) → full problem; "find the wrong step" in a derivation; "why does step N follow from step N−1"; numeric problems with fresh parameters, graded on the reasoning path, not only the number.

Session shape: interleave sub-topics; re-queue a failed item after at least 3 other items; escalate from multiple choice to a flashcard on the same concept once it passes.

## Grading (1–5)

Write 2–4 must-have points for the question before asking it. Grade against those, not against a model answer's wording.

| Score | Meaning | Criteria |
|---|---|---|
| 5 | Perfect | All must-haves, precise terms, no hedging, adds a correct elaboration or example |
| 4 | Correct with a gap | Core mechanism right; one omission or imprecision; no misconception |
| 3 | Gist | Vague or incomplete, or correct only after a hint; no false claim |
| 2 | Misconception | Partial or confused; at least one identifiable false belief |
| 1 | Blank | Nothing, off-topic, "I don't know" |

Rules: any explicit false statement caps the score at 2. Score ≥ 3 passes. Repeating the question's wording never earns 5. Verbose is not complete.

What the board shows after an answer: `Score N / 5`, one line of rationale, the missing points in dim text. No "great job", no "almost there".

## Hint ladder (before revealing)

1. Score 1–2 on the first try → **Point**: name the lesson section or concept, no content ("think about what $\overline{B}+B$ equals"). Ask again.
2. Still < 3 → **Teach**: state the principle in the abstract, never the applied answer. Ask again; this attempt caps at 3.
3. Still < 3 → **Targeted reveal**: quote the student's wrong claim, show the one counterexample that breaks it, then the answer.
4. After any reveal → **Say it back**: the student restates it in one sentence. Grade that as its own item and re-queue the concept later in the session.
5. Never skip a rung in under 10 seconds.

## Stuck detector

Three terse replies in a row ("idk", "yes", "no", "sure", a single word) inside a quiz or Explain dialog → stop pushing that question. Zoom out to a smaller piece of it and switch to a binary-choice question ("is $\overline{A}$ 0 or 1 when $A=1$?"). Return to the original question only after two binary answers in a row are right.

## Multiple choice

- Stem is a complete question answerable before reading the options (cover-the-options test).
- Exactly 3 options, exactly one defensible key. Evaluate or derive every option before shipping. An equivalent expression is correct even when obtained in fewer or more steps; do not mark it wrong for skipping the preferred teaching sequence. If the stem asks for a specific intermediate step, state that constraint explicitly and ensure only one option meets it.
- Every distractor is a real misconception or a common procedural error, taken from the student's own quiz log when available.
- Options equal in length, grammar, specificity, and structure. No "all/none of the above", no negatives ("except"), no absolutes ("always/never").
- No word from the stem appearing only in the key. The key is not the longest or the middle option.
- At least half the items are application ("what would happen if…"), not recall.
- Randomise option order on render.
- Wrong pick → one line naming the misconception behind that option. No narration.

## Twist question

After the quiz, one item with a changed input or a counterexample to the lesson's main claim ("row 0011 is now 1 as well; does $F$ still factor?"). Answer behind a toggle. It exists to catch fluency without understanding; if it fails, write the misconception to the learning record and offer one more ladder rung, then stop.

## Logging

Every graded item appends one line to `learning-records/quiz-log.jsonl`:

```json
{"ts":"2026-09-02T19:40:11Z","lesson":"0004","topic":"simplifying SOP","mode":"cards","score":4,"misconception":null}
```

`misconception` is a short sentence describing the wrong belief when the score is ≤ 2, otherwise `null`. The grid's quiz dots and the next lesson's check-in read this file. When a misconception appears twice, add a line to the current learning record under **Misconceptions** so later quizzes re-probe it in a new context.

## Voice

The Speak button on a flashcard posts to the bridge's `/api/listen`, which runs `bin/listen.sh`: one utterance, Apple Speech, on-device, en-US. The transcript lands in the card's answer box, where it can be edited before Validate. Two presses at once are refused by a lock rather than starting a second recorder. If `listen.sh` exits non-zero the card shows the reason next to the box and typing still works; voice is never the only way to answer.

## The flashcard deck

Modelled on Quizlet's Flashcards mode and Anki's review screen: one card on the stage, a counter, arrows. Never a column of cards.

1. The stage shows one card. Front: the question, and one answer box at the bottom. The student types, or presses **Speak**; Speak posts to `/api/listen`, which runs `bin/listen.sh` on the bridge (on-device Apple Speech) and drops the transcript into the same box, still editable. Enter validates; Shift+Enter is a newline.
2. **Validate** posts `{kind:"grade", item, answer}`. The card breathes while `bin/quiz.py` grades against the `must:` lines with a fast model.
3. The card **turns**. The back shows the `answer:` line (the model answer), then the verdict: the student's words, the score as five pips, one line of rationale, and what was missing. The verdict is painted from the grader's reply at once and also written into the lesson as a `::: score` block, so it survives a reload and feeds the grid's dots.
4. **→** slides the card out to the left and the next one in. **←** goes back; a graded card arrives showing its back, and a click turns it over. **Show answer** turns a card without grading and marks it not graded.
5. After the last card, a summary card: cards, graded, average, how many scored 2 or under. **Start over** returns to the first card; **Generate more** scrolls to the panel.

The deck's position, typed answers and which cards are turned live in page memory keyed by lesson, because every write to the lesson file triggers a full re-render.

Grading is on meaning, not transcription. Speech-to-text noise, missing punctuation and informal phrasing are never errors.

The mic lives on the bridge rather than in the page on purpose: the browser's Web Speech API is Chrome-only and would fail in the cmux WKWebView, while the bridge always runs on the student's own machine.

## Board syntax for quiz items

Written inside the lesson's `::: quiz` block, after the `topics:` line. Plain headings, no decoration.

A flashcard carries its own answer and its own rubric. `answer:` is what the back shows. `must:` lines are what a correct answer has to contain; they stay off the front and are read by the grader.

```md
::: card c1
Why does $\int \csc^2(ax)\,dx$ carry a minus sign?
answer: It is $-\frac{1}{a}\cot(ax) + C$, and cotangent is a co-function; Rule 3 makes every co-function answer negative.
must: the answer is cotangent, a co-function
must: Rule 3 makes every co-function answer negative
:::
```

```md
### Question 1

::: mcq q1 b
Inputs $A = 1$, $B = 0$. Which expression evaluates to 1?
- $A \cdot B$
- $\overline{A} + B$
- $A + B$
why: OR needs only one input at 1, and $A$ is 1.
:::

### Question 2

::: card r2
Two product terms share every variable except one. Why can you drop that variable?
must: the odd variable appears once true and once complemented
must: $X\overline{Y} + XY = X$, so it factors out
:::

::: score r2 4
*"because the one that changes is or'd with its complement so it's one"*

Missing: the rule has a name, $X\overline{Y} + XY = X$. Say it back in one sentence.
:::
```

`why:` is one line shown after any pick, right or wrong. Explain the operation or causal rule that produces the answer, not only its theorem name. Any explanation of a distractor must describe an error that could actually produce that distractor. Options are shuffled on render; the key letter (`a`/`b`/`c`) refers to the order written.
