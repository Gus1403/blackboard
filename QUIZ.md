# Quiz

Every non-plain lesson uses **chapter checkpoints plus a short mixed final quiz**. After each chapter, place 1–2 source-matched MCQs under `### Checkpoint`, directly in the lesson (standalone `::: mcq` blocks). At the end, keep ONE `## Quiz` / `::: quiz` container with 2–3 fresh questions mixing different chapters and the More practice panel. Counts are design defaults, not a scientifically established optimum; keep short lessons proportional. All items count toward the same lesson XP and preserve normal answer logging.

Ask the learner to attempt checkpoint questions without looking back, then read corrective feedback. Final questions use changed inputs and do not name the method/chapter to use. Do not simply duplicate checkpoint questions. At the next study session, briefly retrieve earlier material, prioritizing recorded mistakes; this is an in-session teaching step, not an automatic reminder. Retain actual source difficulty at both placements.

Research basis: [Weinstein et al. 2016](https://pubmed.ncbi.nlm.nih.gov/26950160/) found no delayed-retention superiority for interspersed versus end-only questions; [Szpunar et al. 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3631699/) supports interim testing for lecture attention; [Rohrer et al. 2020](https://doi.org/10.1037/edu0000367) supports mixed mathematics practice. This hybrid is a practical design inference, not a proven universally optimal schedule.

Answer design: large clickable cards on the dark board, chalk borders and text, with muted red triangle, blue diamond, gold circle, and green square icons by displayed position. Retain the source's option count; never add a fourth weak distractor just to fill a grid. Use two columns when answers fit, one column for long expressions and narrow screens. Keep native keyboard-accessible radios, visible focus, non-color correctness indicators, changeable answers, XP, and reload persistence.

Generation and grading both run headless in `bin/quiz.py`, called by `bridge.py` in a background thread the same way `bin/explain.py` is. Neither wakes the interactive agent, so a quiz works identically in cmux, the Claude app and the Codex app, and nothing lands in the chat.

The interactive agent runs a quiz by hand only when the user asks for one in chat (`/blackboard quiz <topic> <cards|mcq>`).

## Source fidelity (required; overrides generic item-writing preferences)

Before writing any lesson quiz, More practice set, flashcard, or twist, inspect the user's relevant sources: practice exams, past exams, quizzes, problem sets, homework, and their answer keys. Match what the lesson actually teaches.

- If a supplied question directly applies, reuse its structure with changed numbers, inputs, expressions, or context. Preserve its tested skill, reasoning steps, constraints, and difficulty. Recompute the answer and every alternative; changing numbers alone can make an item trivial or ambiguous.
- Otherwise build a close analog of a relevant source question. Mirror its question pattern, wording/tone, distractor style, and difficulty. Do not substitute a vocabulary check for a multi-step exam problem.
- If sources contain only free-response/freewrite questions, adapt those problems into MCQs. Preserve the reasoning required; add plausible alternatives from mistakes in that solution process.
- Preserve the source's option count and meaningful features (including “except” or “none” when relevant). Generic preferences below apply only where the source gives no pattern. Exactly one defensible key remains mandatory.
- Record the actual source filename and question/page plus what changed in a Markdown comment immediately before each authored item. For generated items, include that reference in the answer explanation. Never invent a source citation or claim to have read an unavailable question.
- Independently invent questions only when there are no relevant supplied question sources, such as a non-school lesson without user-provided material. First inspect the available sources; missing extraction/access is not evidence that no relevant source exists. If expected sources cannot be read, report that gap rather than silently inventing exam-style questions.
- Assigned work uses changed-parameter practice analogs. Test only taught material, but retain the source difficulty. This rule also applies to flashcards when requested: retain the source problem and assess its reasoning without alternatives.

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

## Multiple choice

- Stem is a complete question answerable before reading the options (cover-the-options test).
- Self-contained: every stem restates the facts it needs (the expression, the inputs, the table row, the circuit) so the student answers without scrolling back. Never "in problem 1", "from the example above" or a bare wire name like n2; write "For $W=\overline{R}S+T$ with $RST=111$…" instead.
- Code in a question: a stem, check-in question or answer that shows more than one statement of code puts that code in a fenced ```java block, formatted as real code with line breaks and indentation, then the question sentence on its own line after it. Never inline a class or several statements into a sentence. A single short expression stays inline in backticks.

  ````
  ::: mcq c2a a
  ```java
  public class Pet {
      private int age = 5;
  }
  ```
  What does `new Pet().getAge()` return?
  - `5`
  ...
  ````
- Match the source option count; default to 3 when there is no source pattern. Exactly one defensible key. Evaluate or derive every option before shipping. An equivalent expression is correct even when obtained in fewer or more steps; do not mark it wrong for skipping the preferred teaching sequence. If the stem asks for a specific intermediate step, state that constraint explicitly and ensure only one option meets it.
- Every distractor is a real misconception or a common procedural error, taken from the student's own quiz log when available.
- Options equal in length, grammar, specificity, and structure. No "all/none of the above", no negatives ("except"), no absolutes ("always/never").
- No word from the stem appearing only in the key. The key is not the longest or the middle option.
- At least half the items are application ("what would happen if…"), not recall.
- Randomise option order on render.
- Answers stay changeable on the board: the student can pick another option at any time and the newest pick is what counts (logged, restored on reload, XP). A wrong pick shows "Not quite" without revealing the key; the `why:` line appears once the right option is picked, in an olive callout like an Explain note. A `why:` with more than one step writes them down, not sideways: one short sentence, then `$$\begin{aligned} … \\ … \end{aligned}$$` on the same line, one operation per row.
- Wrong pick → one line naming the misconception behind that option. No narration.

## Chat quiz (by hand)

Board quizzes run headless in `bin/quiz.py`. When the user asks for a quiz in chat (`/blackboard quiz <topic> <cards|mcq>`), grade with the table above and:

- Below 3 on a first try: point to the concept without giving content, and ask again. Still below 3: state the principle in the abstract (that attempt caps at 3). Still below 3: show the one counterexample that breaks their claim, then the answer, and have them say it back in one sentence.
- Three terse replies in a row ("idk", "yes", a single word): switch to a smaller binary-choice question, and return to the original after two right answers.
- The lesson's `## Twist` (a changed input or a counterexample, answer behind a toggle) catches fluency without understanding. If it fails, write the misconception to the learning record.

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
