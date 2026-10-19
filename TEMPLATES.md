# Lesson templates

Every lesson is one markdown file, `lessons/NNNN-slug.md`, rendered on the board. Pick the template without asking:

- a question that is solved by manipulating symbols (algebra, limits, Boolean simplification, circuit analysis) → **Derivation**
- a "what is / how does X work" question → **Concept Card**
- course mode with a topic map (practice exams present) → **Problem Ladder**, with Derivation blocks inside for the steps

## Board rules (all templates)

1. One idea per block. A block is a paragraph, a display equation, a figure, or a toggle. Never two mechanisms in one block.
2. Question before answer. The reader sees the question, then predicts, then the answer appears.
3. Picture beside the step it explains. Labels on the picture, not in prose.
4. Fixed slots. Same geometry every lesson: title → Prerequisites dropdown → short Contents → conditional check-in → numbered chapters → quiz → twist → extra → sources.
5. Erase, don't add. Word caps below are real. Anything off-path is cut.
6. Every lesson ships with its quiz. `## Quiz` is not an empty panel: write four to six `::: mcq` items covering the whole lesson, in the order the lesson taught them, before calling the lesson done. The student never has to generate anything to start revising. Each item restates the expression, inputs or figure facts it depends on, so it is answerable without scrolling back into the lesson. The "More practice" panel below them generates flashcards or more multiple choice, on one sub-topic or on all of them.
7. Name the actual writer fully. Follow SKILL.md’s **Author byline** contract: `model:` includes family/version, variant, and reasoning effort when available, e.g. `GPT-6 Astra Medium`. The title byline must preserve the full value.
8. Code lines stay at or under 60 characters, so a block fits the column at any zoom. An explanatory comment goes on its own line above the statement it explains, at the same indentation, never trailing a long line. Wrap anything longer. In an `::: interactive` trace, shorten comments rather than add lines, so the step line numbers stay right.
9. Code in a question: a stem, check-in question or answer that shows more than one statement of code puts that code in a fenced ```java block, formatted as real code with line breaks and indentation, then the question sentence on its own line after it. Never inline a class or several statements into a sentence. A single short expression stays inline in backticks.

Prose: plain and direct. No "students often…", no "why people get this wrong", no importance puffery, no throat-clearing, no summary endings, no em dashes, no binary contrasts ("it's not X, it's Y"). A trap is one line starting with ⚠️ and only when it changes the answer.

## Didactic writing contract

Use these conventions for lessons and rewrites. They capture what worked in practice: small understandable steps, with the reason visible. Scale the depth to demonstrated knowledge and the task; coverage alone is not evidence that a prerequisite is understood. For ordinary chat questions, use SKILL.md's **Chat answers: short and readable** contract instead of reproducing a lesson template.

### Shape of each explanation

Every explanation follows the same order, from a whole chapter down to a single step:

1. **What you need first.** The prerequisites, each explained in plain words before it is used.
2. **How it works.** The mechanism step by step, in the order it happens. For a rule, go case by case.
3. **One complete worked example.**
4. **Then the rule**, with its course name.
5. **A quick check.** Plug in values or read the result back.

Do not end with a "common mistake" or "why people get this wrong" paragraph.

### Tone: simple and to the point

- Keep a step or instruction to 20 words or fewer, and a description to 25. Put one idea in each sentence.
- Say the operation and its result with the actual symbols and values. Avoid roundabout or figurative phrasing such as "work it out before the OR", "the term drops out" or "B gets absorbed".
- Use short common words: "use", not "utilize"; "before", not "prior to"; "about", not "approximately".
- Give each thing one name and keep it. Never switch to a synonym for variety.
- Write in the active voice and the simple present tense. Keep "the", "a" and "this".
- Never stack more than three nouns.
- Prefer the literal mechanism to a metaphor. If an analogy really helps, use one and say where it stops matching.

Tone target. Write like this:

> You'll need to simplify $A + AB$. First, the symbols. $A$ and $B$ are each 0 or 1. $+$ is OR: the result is 1 if either side is 1. $AB$ is AND: the result is 1 only if both are 1. Now try both values of $A$. If $A = 1$: $1 + AB = 1$, because OR with a 1 is always 1. If $A = 0$: $AB = 0$, so $0 + 0 = 0$. Both times the answer is $A$. So $A + AB = A$. This is called absorption. Check: $A = 1$, $B = 0$ gives $1 + 0 = 1$.

Not like this: "AB is one piece, so work it out before the OR."

### Sequence meaning before use

- Start with the task the learner will be able to perform. Name the actual homework or exam skill; keep enrichment off the main path.
- Establish only the prerequisites that task needs. Define a new concept in familiar words, introduce its notation, explain what that notation means, then use it. Do not define one unknown term through another unknown term.
- Introduce symbols beside their first use, including overloaded operators, bars, parentheses, subscripts, abbreviations, and implicit multiplication when relevant. Read an unfamiliar expression aloud in prose before manipulating it.
- Explain an operation before using it inside a larger operation. Make grouping and order explicit. For nested expressions, name the pieces and treat each group as one piece until it is that group's turn.
- Keep names stable throughout an example. Distinguish input values, intermediate results, outputs, and placeholders in a general rule. When matching a rule, point out exactly which piece of the example fills each placeholder.
- Use a meaning-level concrete case to make an abstract rule understandable. Then state the general rule before applying it in a derivation. Do not begin with a wall of named theorems.

### Build a small example into a method

- Give the setup: what is given, what is wanted, and the rule needed for the next step. Introduce later rules just before they are needed, rather than front-loading a catalogue.
- Begin with the smallest example that exposes the mechanism. Work one truth-table row before showing all rows; trace one intermediate wire before a complete circuit; evaluate one case before generalizing.
- Explain why a rule works with a short causal argument or a complete small case split. “Absorption” or “identity” can label a reason after its meaning is established; neither word substitutes for an explanation.
- Name the action, show the change, and give the reason. Use one operation per equation line. Separate factoring, complement replacement, and identity cleanup instead of collapsing all three into a single equality chain.
- For a difficult step, put a short paragraph immediately before its equation: identify the piece being changed and what stays in place. Keep the equation's right-margin reason short.
- Show intermediate results explicitly. Use helper columns, named wires, or short stage headings so the learner does not have to carry several unfinished operations in memory.
- Finish one simple worked example before adding a complication. Change one feature in the next example, explain the new decision it requires, and reuse the established method.
- Use modified practice analogs for assigned work, preserving the tested skill without revealing or setting up the assigned answer. Do not promise what the homework's final answer will look like.
- End a worked example with a concrete sanity check: substitute inputs, inspect an endpoint, check units, or read a circuit back into an expression. State that a spot check detects mistakes; use a derivation or exhaustive cases to establish equivalence.
- When several task types coexist, provide a compact task → first move → check table. Keep it actionable; omit a recap paragraph that only repeats the lesson.

### Language and visual conventions

- Follow **Tone: simple and to the point** above. Prefer concrete verbs such as “flip,” “factor out,” “replace,” and “feed into” over shorthand such as “fires,” “dies,” “shadows,” or “collapses.”
- Explain the meaning in plain words before giving its technical name when that helps. Keep the course's technical vocabulary available so the student can recognize it on the assignment.
- Avoid clever commentary, rhetorical flourishes, “obvious,” “clearly,” “just,” and “as you know” when they hide a missing explanation. Follow the shared bans on praise, throat-clearing, em dashes, and artificial binary contrasts.
- One idea per paragraph. Use headings that name the action or decision. Do not compress several new concepts into a dense paragraph merely to meet a word cap.
- Keep the reasoning needed for the task visible. The Prerequisites toggle lists expected prior knowledge only. Toggles may hide predictions, retrieval answers, and optional detail; explanations needed to follow the next line stay visible.
- Use tables for repeated comparisons after explaining one representative case. Give columns operational labels such as “NOT Q” or “previous column OR R”; avoid unexplained shorthand.
- Use a small diagram when it clarifies actual connections or dependencies. Label intermediate results at the point they are produced. Read the diagram in prose once so the learner knows how to trace it.
- A block flow is a wiring plan; identify it as such if the assignment requires standard circuit symbols. Distinguish the representation being taught from the required submission format.
- A warning must identify the precise action that changes the answer. When useful, supply one small counterexample, such as inputs that distinguish two parenthesis or bar placements.
- Respect the user's language preference; do not infer a language switch from a technical term. Preserve the course workspace's language convention unless asked to change it.
- Fit the session's time budget by cutting tangents and duplicate examples. Preserve the prerequisite explanations and intermediate steps that make the remaining examples understandable.

**Illustrate when it improves understanding.** Add a diagram whenever it makes an explanation easier to visualize or understand than prose alone, whether in an introduction, worked example, comparison, or later explanation. The trigger is teaching value, not first mention of a concept. Place it beside the explanation it clarifies. Do not add a diagram merely because a term is new, or assume one visual somewhere in the lesson is enough. Name the same parts in prose and drawing; distinguish control signals from conducting paths, mark connection points and gaps, and label simplified models. Show contrasting states when that helps explain what changes. Add one short sentence guiding the reader through the visual. Prefer a schematic for relationships and a real photo for physical appearance. During review, ask “Would a diagram make this easier to picture or understand?” If yes, add one there; if it adds no clarity, leave it out.

### Practice and completion check

- Ask a small prediction after teaching the prerequisite and before revealing the outcome. The reveal explains the causal step.
- Cover the taught skills with 1–2 checkpoint MCQs after each chapter and 2–3 fresh mixed MCQs at the end, grounded in relevant supplied questions, following QUIZ.md Source fidelity. Match source difficulty, reasoning and alternatives; change parameters or adapt free-response questions to MCQ. Do not replace exam-level questions with easy recall or quiz an untaught prerequisite.
- Write explanations that connect the answer to the rule and identify the actual mistaken operation. Verify every option; mathematically equivalent alternatives cannot be marked wrong merely because one uses more steps.
- End with a changed-input or changed-structure question whose answer is hidden. This checks whether the learner understands the role of a condition, grouping, or operator.
- Before the final render, read top to bottom as a learner. Does every term and symbol appear after its plain explanation? Is every rule explained before it is applied? Is every transition supported by a visible intermediate step? Is every check correct? Does each explanation follow the Shape order? Does every sentence follow the Tone rules?
- Verify section order, the full author byline, rendered math, figure labels, and quiz keys. Fix rendering or ambiguous questions before declaring the lesson ready. Do not infer mastery or completion from having rewritten or displayed material.

## Lesson frame

```md
---
title: Sum of Products from a Truth Table
course: ECE 2020          # omit in self-study
exam: Test 1, Q3–Q5       # omit if unknown / self-study
model: GPT-6 Astra Medium # example only; use the actual session's full writer identity
image: circuit board macro   # a photographable subject from the lesson's topic, never a chalkboard
photo: assets/0004.jpg     # filled by bin/image.sh
credit: Photo by … (Openverse, CC0)
prev: 0003                 # previous lesson number, omit on the first
---

# Sum of Products from a Truth Table

::: prerequisites
- AND, OR, NOT
- Truth-table rows
- Basic Boolean algebra
:::

**Contents**
1. [Chapter 1 · Build an SOP](#s-chapter-1-build-an-sop) — turn rows into terms.
2. [Chapter 2 · Simplify it](#s-chapter-2-simplify-it) — combine terms.

*Question first: a table of 1s and 0s is in front of you. How do you turn it into a circuit?*

### Before we start  ·  from lesson 0003: Boolean Algebra and the Basic Gates
::: checkin
- What does a bar over a variable mean?  ||  NOT. $\overline{A}$ is 1 exactly when $A$ is 0.
- Why is $A+\overline{A}=1$?  ||  One of the two is always 1.
:::

## Chapter 1 · Build an SOP

…body (one of the three templates)…

## Chapter 2 · Simplify it

…next topic…

### Checkpoint

…1–2 standalone source-matched `::: mcq` blocks; also add a checkpoint after Chapter 1…

## Quiz

…2–3 fresh questions mixing the chapters; one final quiz container only…

::: quiz
topics: minterms, simplifying SOP, K-map merging

::: mcq q1 b
Two product terms differ in exactly one variable. What happens to that variable when you merge them?
- It becomes its complement
- It is dropped, because $X\overline{Y} + XY = X$
- It moves to the other term
why: The variable appears once true and once complemented, and $\overline{Y}+Y = 1$.
:::

::: mcq q2 a
A truth table has a 1 in row 0110. Which minterm is that?
- $\overline{A}BC\overline{D}$
- $A\overline{B}\,\overline{C}D$
- $\overline{A}\,\overline{B}CD$
why: A 0 is the complemented variable, a 1 the plain one, read left to right.
:::
:::

## Twist
…one changed-input question, answer behind a toggle…

## Extra          # self-study only, only when the video was a source
::: video https://www.youtube.com/embed/ID?start=95
Ben Eater, "Making logic gates from transistors"
:::

## Sources
- Week 2 slides (tier 6, lecture notes)
- Practice Test 1, Q3–Q5 (tier 3)
```

The “Before we start” block above is conditional: include it only for a genuine continuation of lesson 0003; otherwise omit both the heading and check-in, and omit `prev:`. Chapter links must match the rendered heading anchors.

Before finishing a new lesson, apply the visual/interactive contract in SKILL.md. Math needs an interaction or meaningful animation; a banner photo does not count. See [INTERACTIVES.md](./INTERACTIVES.md) for working schemas.

Block syntax the renderer understands:

- `::: interactive trace` or `::: interactive function` / JSON spec / `:::` → manipulable lesson example; see INTERACTIVES.md.
- `::: prerequisites` / short `- concept` lines / `:::` → collapsed **Prerequisites** list at the top of every non-plain lesson.
- `::: checkin … :::` with `- question || answer` items → Notion-style toggles. An item may continue on lines indented two spaces and hold a fenced code block; the first `||` outside code splits question from answer.
- `units: …` on the line after a display equation → "symbols & units" toggle.
- `::: numeric … :::` → collapsed numeric detail under an abstract step.
- `::: predict` / option lines / `reveal: …` / `:::` → prediction buttons; the reveal opens after a click.
- `::: exp e12 [folded] … :::` → an expandable olive callout with a lightbulb/title header and a separate body. Written only after an Explain request, not prefilled in a fresh lesson. Legacy `deep` flags still render in the same style.
- Do not add `==words==` for Explain; legacy markers render as plain text. Dotted clickable underlines belong exclusively to the Definition button and reopen its popup.
- `::: fig <template>` / JSON spec / `:::` → inline chalk SVG (taccounts, bars, flow, timeline, table, kmap, vectors, wave, raw). Specs in [FIGURES.md](./FIGURES.md). `caption` in the spec becomes the figcaption.
- `::: photo [side|wide]` / `query: <what to fetch>` / `caption: …` / `:::` → a real photograph of the thing being discussed, fetched by `bin/photos.py` from licensed sources and saved under `assets/`; `src: https://…` skips the fetch when a specific image (a maker's press photo) is the only good one. `side` floats it right at 44% width with the text flowing on the left; `wide` spans the column. Rules in **Photos** below.
- `::: figure assets/x.svg|png` / caption / `:::` → an existing image; `.svg` is inlined so the page fonts apply; add `wide` for a full-width `.png`.
- `::: video assets/x.mp4` / caption / `:::` → a Manim animation rendered with `bin/anim.sh`; a YouTube embed URL gives an iframe.
- `$100` in prose is money and stays as typed. Inline math never starts with a digit or a space: `$F = 1$`, `${}0.5$`. `\$` is a literal dollar sign.
- `::: video URL` / caption / `:::` → embedded video.
- `::: quiz` / `topics: a, b, c` / items / `:::` → the quiz. Items render first, the "More practice" panel under them.
- `::: mcq q1 b` / stem / `- option` lines / `why: …` / `:::` → one multiple-choice item in a numbered list; the letter is the key in the order written, options shuffle on render. The stem may hold a fenced code block (rendered as a code box, question sentence after it); an option that is a whole statement of code in backticks shows as a small preformatted box.
- `::: card c1` / question / `answer: …` / `must: …` lines / `:::` → one flashcard. Every card in a quiz joins one deck, shown one card at a time where the first card sat: the front holds the question and an answer box (typed, or filled by Speak); Validate grades it and the card turns to show `answer:` and the verdict. `must:` lines are the grader's rubric and stay off the front. Cards are generated by `bin/quiz.py`; a lesson does not ship with them.
- `::: score c1 4` / the answer, the rationale, `Missing: …` / `:::` → the verdict on the back of that card. Written by `bin/quiz.py`, never by hand.
- `→ Exam: …` or `→ background` at the end of a block → course tag (course mode only).
- A markdown table → a booktabs table (rules at the top, under the header, and at the bottom; no vertical rules, no fills). Math works in any cell. See **Tables** below.

## Tables

Use a table whenever the same two or three questions get asked of every item in a set: a family of formulas, gate truth tables, a ladder of problems, two things told apart attribute by attribute. Anything the reader will scan across and down rather than read in order.

Do not use one for a sequence (that is a Derivation), for a single fact, or for two rows. Never use `\begin{array}` or `\begin{matrix}` to fake a table — a real markdown table gets the rules, the spacing and the header treatment.

```md
| $\displaystyle\int \cdots dx$ | comes from | answer |
|---|---|---|
| $\sin(ax)$ | $\frac{d}{dx}\cos x = -\sin x$ | $-\frac{1}{a}\cos(ax) + C$ |
| $\cos(ax)$ | $\frac{d}{dx}\sin x = \cos x$ | $\frac{1}{a}\sin(ax) + C$ |
```

Rules:

1. **Three or four columns, never more.** Column 1 is the thing being looked up; the rest answer one question each. A fifth column means two tables.
2. **Header names the question**, in two or three words: "comes from", "answer", "when to use it". The board renders headers as small dim capitals, so they read as labels, not data.
3. **Parallel cells.** Every cell in a column has the same shape — all integrands, all derivatives, all answers. A cell that breaks the pattern is prose and belongs under the table.
4. **Sorted so the pattern is visible.** Put the rows that share a sign, a co-function, or a trap next to each other. The order is the teaching.
5. **One line per cell.** If a cell needs a sentence, the table is the wrong block.
6. **Numbers right-aligned** with `|---:|`; text and math left. Digits are already tabular.
7. **One line under the table** naming the pattern the rows just made ("three are co-functions and all three are negative"). The table shows, that line tells.

The board scrolls a wide table horizontally rather than squeezing it, so a long third column is fine.

A markdown table is the default. `::: fig table` (see [FIGURES.md](./FIGURES.md)) is only for the case a markdown table cannot do: highlighting a specific cell or row to point at it from the prose.

## Template 1 — Derivation

For anything solved step by step. Rules (from the board style research):

1. **Setup block first.** State what is given and wanted. Explain the next rule before applying it; introduce additional rules at the stage that needs them.
2. **One operation per line.** One substitution, one expansion, one cancellation, one limit. Never two.
3. **One `=` per line, in a column.** `\begin{aligned} LHS &= … \\ &= … \end{aligned}`. LHS written once.
4. **Reason in the right margin.** `&& \text{(reason)}` on every line. No unexplained jumps. The board renders everything after `&&` as a chalk margin note (dashed rule, accent colour, smaller, a "why" label on the first), so it reads as an aside, never as a step: put only the reason or the formula being used there, never part of the derivation.
5. **Meaning before symbolic application.** A small concrete case may introduce a rule. In the derivation, state its general form before substituting values; keep required reasoning visible.
6. **Expand explicitly.** $(a+b)^2 \to a^2+2ab+b^2$ written out.
7. **Separate cleanup steps.** Simplify when the method needs it, one operation per line; box the final result. A simplification lesson should expose each simplification as its own justified step.
8. **Sanity check last.** One check (an endpoint, a limit, a row of the table).
9. **Layout.** Display math left-aligned, one `aligned` block per stage, a `###` heading per stage ("Setup", "Step 1 — width", …). Derivation steps never side by side; a figure may sit beside its caption.

Add a `::: predict` before the result when the outcome is guessable ("what happens to F when A = 1?").

## Template 2 — Concept Card

For "what is / how does it work". Eight blocks, in this order, with caps:

| # | Block | Rule | Cap |
|---|---|---|---|
| 0 | **Try it without the tool** | Show the problem the concept solves by attempting it without the concept and watching it fail or stall. | 60 words |
| 1 | **One-liner** | *X is a [kind of thing] that [what makes it different], used to [why it exists].* Plain words, no term not yet defined. | 25 words |
| 2 | **Concrete example** | Smallest real instance with numbers, code, or wire values. Inline figure if useful. Example before the general rule. | 60 words + 1 figure |
| 3 | **Mechanism** | Numbered steps, one per line, each naming what changes and why. A `::: predict` before the outcome. | 4–6 steps, ≤15 words each |
| 4 | **Analogy + where it breaks** | One analogy, then one line "breaks here:". Never an analogy without the break. | 2 lines |
| 5 | **Distinguishing case** | When two concepts are confusable, use one concrete case that exposes the difference. Omit otherwise. | 40 words |
| 6 | **⚠️ trap** | Only if it changes the answer. One line. Otherwise omit the block. | 1 line |
| 7 | **Check** | One question whose wrong options are the real confusions; answer behind a toggle. | 1 question |

Optional 8: **Level-up**, one line pointing at the formal definition or notation.

### Mini-example (neural network output)

0. Try to classify a photo with a fixed rule: "cat if more than 40% of pixels are brown". It fails on a brown dog. You need a rule that is learned, not typed.
1. A neural network is a stack of layers that turns numbers into numbers by repeated weighted sums and a squashing function.
2. Inputs (2, 3); weights (0.5, −1); bias 1 → $0.5·2 − 1·3 + 1 = −1$ → ReLU → 0. *[figure: 2 nodes → 1 node, weights on edges]*
3. (i) multiply each input by its weight; (ii) add them and the bias; (iii) apply the activation; (iv) that number feeds the next layer; (v) the last layer's numbers are the output.
4. Like a spreadsheet of formulas feeding each other. Breaks here: the weights are learned, not typed.
5. Not a lookup table: it never stores the photo.
7. If all weights are 0, the output is: (a) the input (b) activation(bias) (c) undefined.

## Template 3 — Problem Ladder (exam mode)

Used when `reference/topic-map.md` exists. Teaches a topic through the real problems that test it.

1. **What this prepares you for.** The exam problems (source, number, type, points, priority) this topic covers. → Exam tags on every block from here on.
2. **Ladder.** Table of 2–5 representative problems: source, type, the skill each teaches, what makes it different from the others. Variants, never duplicates.
3. **Anchor problem.** Full problem text (a modified-number version of a real problem is fine, labelled "Modified-number version of <source>"). Then think-first prompts behind a toggle: what is asked, what is given, which principle, which equation, what to solve first. Then the solution as a Derivation, concepts introduced at the step that needs them, each with its one-liner.
4. **Variants.** For each: full text, what changed, what stayed, the new skill, solution (Derivation), the trap it introduces if any.
5. **Reusable method.** A checklist: when to use it, how to recognise the problem type, what to write first, which equations, in what order, what to check.
6. **Quiz** with re-parameterised versions of the ladder problems.

Assigned homework is never solved, partially solved, or set up. If a ladder problem is an assigned one, replace it with a modified-number analog and end the lesson with a nudge naming the assigned problem.

## Steps go down, never sideways (hard)

A derivation is a column, one operation per line, the reason in the right margin, the result boxed. Never `a = b = c = d` on one line and never `A \Rightarrow B \Rightarrow C` inside a sentence, for a worked example or a "small" step alike. Solving for the crossings of two curves is a derivation. Evaluating a bracket at its limits is a derivation. `render.sh` runs `bin/lint.py` and prints a warning for every sideways chain; fix them before the render counts as done.

```
$$\begin{aligned}
x^{2} &= 2x + 3 \\
x^{2} - 2x - 3 &= 0 &&\text{move everything left} \\
(x-3)(x+1) &= 0 &&\text{factor} \\
x &= -1,\; 3 &&\text{the limits}
\end{aligned}$$
```

## Titles

A title is a YouTube title, not a file name. Short, concrete, says what you will be able to do or understand after reading: "How to Solve All 5.5 Problems", "Test 1 Formula Sheet", "How Absorption Works", "How the NVIDIA DGX Spark Actually Works", "Split the Fraction First". Rules:

- No em dashes, no colons, no "Problem 1 — every step" suffixes, no "Step by Step" padding.
- Two to seven words. Lead with "How to", "How X Works", "Why X", or the thing itself.
- The `title:` in front matter and the `# ` line are the same string. The hub and the tab show it, so it must read well at a glance next to other courses' lessons.

## Photos

**The banner is the subject.** When the lesson is about a specific object (a machine, a chip, a building, an animal), the banner photo is that object, not a generic image of its category: a DGX Spark lesson opens with the DGX Spark, never with "a computer chip". If the free sources cannot produce the object itself, use the maker's press photo as the banner (`photo: assets/NNNN.jpg` copied from a press image, `credit: <maker> press image`) and leave `image:` for abstract lessons only. Check the banner after the first render; a wrong banner is worse than none.

Real photographs go between topics **only when the lesson is talking about a physical thing** and a photo of that thing exists: a machine, a chip, a board, an organ, a building, an instrument. Then:

- At least one photo of the thing itself, `wide`, near the top.
- A photo of a part **at the section that discusses that part** (the die, the connector, the cooling), `side` so the text keeps flowing, and only if a good photo of that exact part exists. A photo of something adjacent is worse than no photo.
- `query:` names the object precisely as a photographer would caption it ("NVIDIA DGX Spark desktop computer front", "GB10 Grace Blackwell chip package"); the caption says what the reader should notice in it.
- Never for abstract topics (a limit, an integral, a proof, a tax rule): those get `::: fig` drawings, not stock photos.
- Two or three photos per lesson is normal; more than five means the lesson is a gallery.
