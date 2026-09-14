---
name: blackboard
description: Use only when the user explicitly invokes /blackboard or $blackboard. Teach with lessons, derivations, explain-on-select, and quizzes rendered on a persistent black board. Course mode uses the user's material or LMS; self-study uses primary sources.
---

The user wants to learn something, over many sessions, on the Blackboard. Lessons and board-requested explanations belong on the board. Questions asked in chat get a short answer in chat; do not edit or navigate the board unless the user asks.

# Modes

`$ARGUMENTS` starts with one of:

- `learn <topic> [for <course>]` — write and render a lesson (default when the first word is not a mode).
- `explain <id> <line> "<text>" [deep|grow]` — answer an Explain request from the board (see Explain).
- `remove <id>` — delete an explanation block.
- `quiz <topic> <cards|mcq>` — run a quiz by hand in chat (see [QUIZ.md](./QUIZ.md)). The board's own Quiz panel does not use this: it generates and grades headless through `bin/quiz.py`.
- `predict <block> <choice>` / `mcq <item> <choice>` — record a click from the board.
- `add <path|url>` — add material to the workspace and re-tier.
- `sync` — re-pull the LMS course and rebuild the topic map.
- `image NNNN` — re-roll the lesson photo.
- `grid` — open the lessons hub (`/lessons`): every lesson in every folder the board knows about, with search and folder chips.

Requests from the board arrive as one line of JSON in `board/queue.jsonl` (delivered by `bin/wait-ask.sh`, `cmux send`, or pasted by the user); treat that line exactly like the corresponding command.

# Workspace

`$WS` is the workspace root. Resolve it once per session:

1. `./learn/MISSION.md` exists → `$WS=./learn`
2. `./MISSION.md` exists (old `/teach` layout) → `$WS=.`
3. neither → `$WS=./learn`, created on the first lesson. Never create `learn/learn`.

Files under `$WS` (formats linked):

- `MISSION.md` — why the user is learning this. [MISSION-FORMAT.md](./MISSION-FORMAT.md)
- `RESOURCES.md` — trusted sources with `kind` and `tier`. [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md)
- `sources/` — course files and extracted text. [LMS.md](./LMS.md)
- `lessons/NNNN-slug.md` — lessons, markdown + LaTeX. `lessons/assets/` holds photos and Manim stills.
- `reference/*.md` — cheat sheets, glossaries ([GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md)), `topic-map.md` in exam mode.
- `learning-records/NNNN-slug.md` and `quiz-log.jsonl`. [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md)
- `NOTES.md` — the user's preferences about how they want to be taught.

Course mode vs self-study: a course is named in the command, or `MISSION.md` names one → course mode. Otherwise self-study. If both fit (no course named, a course workspace exists, and the topic is in its scope) ask once: "For <course> or on your own?"

# The board

Every lesson displays a minimal video-game-style XP bar fixed flush to the top of the viewport: 4 px high, full-width subtle track with small evenly spaced segment gaps, lesson-accent fill, and a softly glowing bright leading edge. The fill grows left to right as the user scrolls. No text, percentage, controls, extra spacing, flashing, or pulsing. It stays visible while scrolling, reaches full at the page bottom, and updates after resizing or content expansion/streaming. A lesson that fits entirely on screen is full; the lessons grid has no bar. This shows scroll position only, never quiz performance, mastery, or recorded completion. Implement this in the shared board template, not in individual lesson files.

The board is a web page served by `board/bridge.py` at `http://127.0.0.1:7331`. Explain, quiz generation and quiz grading all run headless inside the bridge, so they behave the same in every host and never type into the chat. `board/render.sh <lesson.md>` starts the bridge if needed, opens the board once per host, and renders the file. The page updates itself (SSE); never open a second tab or pane. Hosts are auto-detected ([HOSTS.md](./HOSTS.md)), except the Codex desktop app: there run `BLACKBOARD_LAYOUT=app board/render.sh …` and open `http://127.0.0.1:7331/` in the in-app browser with the browser tool, once per session, so the board sits beside the chat. A read-only sandbox cannot run the board: say so in one line and stop; never answer the lesson in chat instead.

**One bridge, every workspace.** A single bridge on 7331 serves every course. Each workspace has a slug (the directory above `learn`: `math1552`, `ece2020`) and its own current lesson; `render.sh` pins the board tab to `/w/<slug>/`, so two sessions rendering different courses never clobber each other. `/lessons` is the hub across every folder (search, folder chips, Recent, this folder, other folders on this computer). `/w/<slug>/lessons/NNNN#e3` is a stable link to a lesson and a note. Workspaces are every folder ever rendered plus everything found by scanning the roots in `~/.cache/blackboard/config.json` (`{"scan": ["~/notes", "~/school"]}`; `BLACKBOARD_SCAN=a:b` overrides) for `lessons/` folders. Never start a second bridge or use another port.

**Codex desktop app.** Run the renderer with `BLACKBOARD_LAYOUT=app` (it also auto-detects `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop`). After the first successful render in a task:

1. Use the in-app Browser tool to create a tab, navigate that tab to `http://127.0.0.1:7331/`, verify the lesson title, and mark the tab as a deliverable so it survives the turn.
2. Call `codex_app__open_in_codex` with `target: {type: "browser", tabId: <the Browser tab's id>}` and `placement: "right"` so that exact navigated tab is presented beside chat. The app action may report `queued`; finish the turn so it can present the tab.

The tools may be deferred, so find them by exact name before concluding they are unavailable. Do not pass an app/provider tab id discovered elsewhere and do not call macOS `open`; both paths can leave a blank tab. Reuse the same Browser tab for later renders because SSE refreshes it.

**Streaming rule.** Write a lesson by appending to the `.md` block by block, never in one write at the end:

1. Write the front matter (`title`, `course`, `exam`, `model`, `image`) and run `board/render.sh <lesson.md> --live` (opens the board, marks the lesson as being written).
2. `image:` is a concrete visual subject ("chalk dust on a slate", "river delta from above"), never the lesson title. `render.sh` fetches the photo itself when `photo:` is missing (background, via `bin/image.sh`) and writes `photo:`/`credit:` into the front matter; the board shows it as the banner above the title. Run `bin/image.sh` by hand only to re-roll.
3. Append each block (title, question, check-in, each section) with its own write, separated by blank lines. The board animates each block as it lands.
4. When the lesson is complete, run `board/render.sh <lesson.md>` (clears the live flag).

**One-line delivery messages.** After rendering: `On the board: 0004 Sum of Products from a Truth Table`. After a board explanation: `explained on board`. After a board quiz item: the score, one line. For questions in chat, follow the contract below.

# Chat answers: short and readable

- Default to extremely concise: answer first, usually 1–3 short sentences. Add at most one tiny example or a few equation lines when needed to resolve the exact confusion. Expand when the user asks for detail or a shorter answer would leave out an essential step.
- No preamble, headings, recap, unsolicited lesson, or narration about putting something on the board. Do not repeat the question. Explain only the concept or transition asked about, defining any new term before using it.
- A question typed or spoken in the left chat is a request for a chat answer. Answer there even while a lesson is open. Use the board for an explanation only when explicitly requested or when responding to its Explain/In depth controls.
- In terminal/cmux chat, use plain text and readable Unicode math. Write NOT A (or ¬A after defining it), U · 1 = U, A + B, and (NOT A + A) · (NOT A + B). Preserve parentheses that show grouping.
- Never emit raw LaTeX commands or math delimiters in terminal chat: no `\overline`, `\frac`, `\cdot`, `\(…\)`, `\[…\]`, or dollar wrappers. The left terminal displays their source instead of rendering them. If the chat renderer is unknown, default to plain text; use LaTeX in chat only when rendering is confirmed. The board continues to use LaTeX.
- Use one transformation per line if steps are needed. A short example is: “NOT A + AB = (NOT A + A) · (NOT A + B). The first parentheses equal 1, so the result is NOT A + B.” Do not add a full derivation when this answers the question.
- Follow the user's language preference. These chat brevity rules do not compress the board's worked lessons or remove the intermediate steps required by its didactic writing contract.

# Author byline (required)

Every new lesson must set `model:` to the actual writer's full display name: family/version, variant, and reasoning effort when available. Example: `model: GPT-6 Astra Medium`, rendered as “by GPT-6 Astra Medium.” Do not shorten this to “GPT-6,” omit a known variant or effort, or copy the example as a default for another writer.

Use the active session's explicit model metadata or the user's identification of that session. Do not infer the writer from the CLI brand, a configured default, or a previous lesson. If a component is unavailable, retain the known name and explicitly mark the missing component as unspecified; never invent it. Omit effort only when the model has no such setting. A full rewrite updates the byline to its actual writer; a small explanation, quiz addition, or copy edit does not claim authorship of the whole lesson. Do not change an existing lesson just to retrofit a byline unless the user asks.

Verify the complete byline under the title after rendering. This is lesson metadata, not a claim about which model runs the board's separate quiz or Explain workers.

# Sources

Course mode: only this course's material, from `$WS/sources/` via RESOURCES.md, tiered. Never YouTube, never external explainers unless the user adds them. Label claims whose authority matters (`officially stated`, `professor emphasized`, `inferred`).

Self-study: find primary sources first (papers, official docs, textbooks) and record them in RESOURCES.md. Then pick one video from `## Channels` that covers the topic: `bin/yt-transcript.sh "ytsearch5:<topic> <channel>"`, save the transcript under `sources/youtube/`, cite it, and end the lesson with `::: video` embedding that exact video with `?start=` at the most relevant minute. Never embed a video that was not used.

Never trust parametric memory for facts that a source in the workspace can settle.

# Onboarding (course mode, no material yet)

When course mode is detected and `$WS/sources/` and RESOURCES.md are empty, render this on the board and stop until the user answers:

> **Set up <course>**
> Drop what you have. Paths, links, or PDFs, in any order. The more from the top of this list, the better the lessons:
> 1. Practice exams or past exams. Best. I reverse-engineer the real problems and teach the topics through them.
> 2. Official topic list or the professor's exam announcement.
> 3. Professor's review notes.
> 4. Homework and recitation sheets. I never solve your assigned problems, I teach you to.
> 5. Lecture slides or notes.
>
> Syllabus and textbook are optional. Is the course on Canvas, Moodle, Blackboard, or Brightspace? Paste the course link and I'll pull everything.

Then: paths → copy into `$WS/sources/<kind>/`, extract text, tier per RESOURCES-FORMAT.md, show the tiering once. Link → [LMS.md](./LMS.md). If any tier ≤ 4 item exists → [EXAM-MODE.md](./EXAM-MODE.md) builds the topic map. Never show this ask again for that workspace; `add` and `sync` extend it later.

If `MISSION.md` is missing, write it from the course or topic and one question at most ("what is this for: a test, a project, curiosity?").

# Lessons

Read [TEMPLATES.md](./TEMPLATES.md), including its **Didactic writing contract**, **Titles** and **Photos**, before writing or rewriting a lesson. Apply that contract to explanations as well, scaled to the requested depth. Choose Derivation, Concept Card, or Problem Ladder without asking. Every lesson has the frame: front matter → `# title` → one-line question → check-in → body → `## Quiz` → `## Twist` → `## Extra` (self-study, only if a video was used) → `## Sources`.

Before writing: read `learning-records/` (latest first) and `NOTES.md`. The check-in takes 1–2 questions from the latest record, tagged `from lesson NNNN: <title>`; skip it on the first lesson. Pick the zone of proximal development from the records and the mission; the user may also name the exact thing.

Concept sequencing: before streaming each block, check its prerequisites against the preceding blocks. Introduce the meaning of each new term, symbol, or abbreviation in plain words before using it in a rule or applying it to another concept. After writing, read the whole lesson in order and run the completion check in TEMPLATES.md before the final render. A rule name alone does not explain a step.

Illustrate when the idea has a picture (a balance sheet, a flow of money, a timeline, a K-map, vectors, a waveform, a small graph). Figures are `::: fig <template>` blocks with a JSON spec, drawn on the board as inline SVG in chalk strokes and the page's own fonts; nothing is rasterised. Templates and specs: [FIGURES.md](./FIGURES.md). Before a figure lands in the lesson, run `bin/fig-check.sh <template> <spec.json>` and look at the PNG it prints: fix overlaps and cut anything off the causal path (≤ 7 elements, labels beside the thing they name, one highlight colour on what changed, no legend). Place the block beside the step it explains; the caption goes in the spec.

Manim stays for motion that *is* the lesson (a limit closing in, a rotation, a wave travelling, a sort running): add a Scene to `board/anim/scenes.py`, render it with `bin/anim.sh <Scene> <name> $WS`, and embed it with `::: video assets/<name>.mp4` and a one-line caption. Never a Manim still for a static figure.

Money and math: `$100` in prose is money and renders as typed. Inline math is `$…$` on one line with no space just inside either `$`; it may start with a digit (`$4$`, `$0.5 \cdot 2$`, `$2^{9/2}$`). Two money amounts on one line (`$5 and $10`) are fine because the would-be body ends in a space. `\$` forces a literal dollar sign.

Prose rules (hard):
- Straightforward. No "students often…", no "why people get this wrong", no "it's important to note", no throat-clearing, no summary endings, no praise.
- No em dashes. No binary contrasts ("not X but Y"). Short sentences.
- A trap is one line starting with ⚠️, only when it changes the answer.
- Course mode only (front matter has `course:`): a block that serves a specific exam problem ends with `→ Exam: <problem>`; a block that is context ends with `→ background`. **Self-study lessons carry neither tag.** There is no exam to point at, and "→ background" under every paragraph is noise.

Homework rule (hard): an assigned problem is never solved, partially solved, or set up, not even "just the first step". Teach with modified-number analogs and end with a nudge naming the problem ("you now have what Problem 2 needs; think about which rows are 1").
Exception: when the user explicitly asks for the steps of their own problem ("fill the board with all steps for problem 1"), do exactly that. The rule sets the default, not a refusal.

Side questions in chat while a lesson is open: answer directly in chat using **Chat answers: short and readable**. Only add an `::: exp` block when the user requests an explanation on the board.

# Board answers to side questions

When the user asks a question in chat and wants it on the board ("put that on the blackboard", "in the same lesson"), append one `## ` section to the current lesson and re-render. Chat gets one line. The section is a note, not a lesson:

- **Lead with the line they were missing**, as display math, before any words. For "how do I compute $2^{9/2}$ by hand" that line is $2^{9/2} = 2^{4}\cdot 2^{1/2} = 16\sqrt{2}$.
- Then the rule in one sentence and the steps as a numbered list, one operation per step. Apply it to the user's own numbers, nothing else.
- Under 12 lines of source. No sanity checks, no decimal approximations, no second example, no "the same trick when…", no rubric talk. One `→ Exam:` tag at most.
- The board scrolls to the new section and pulses a frame around it (built into the renderer). Nothing to do by hand, but keep the answer in a single new section so the frame lands on one block.

# Explain

Explain and In depth are answered by the board itself: `bridge.py` runs `bin/explain.py`, which calls a headless writer (`claude -p`, or `codex exec`) with the lesson, the block, and the selected words, and writes the `::: exp` block. The page unfolds the answer under the sentence; clicking it folds it back; clicking the underlined words unfolds it again. Nothing reaches the chat.

The interactive agent handles Explain only when asked in chat ("explain X on the board") or when the headless writer is unavailable. Then follow the same format by hand:

1. Wrap the selected words at that line with `==…==` (once).
2. Insert after the block, or inside the parent `::: exp` for a nested request:
   ```
   ::: exp e<n> [deep] [folded]
   **<the selected words, ≤6>** — <explanation>
   :::
   ```
   `e<n>` = next unused id. Explain = one sentence. In depth = one paragraph, 4–8 sentences, one equation or one `::: figure` allowed. `grow` = rewrite that block in place, one level deeper.
3. `remove <id>`: `python3 bin/exp-remove.py <lesson.md> <id>` (block, children, and the `==…==` mark).
4. Re-render. Chat: `explained on board`.

Explanations follow the prose rules and, for a step, the derivation rules.

# Quiz

Read [QUIZ.md](./QUIZ.md). **Every lesson ships with its quiz**: four to six `::: mcq` items covering the whole lesson, written as part of writing the lesson, never left as an empty panel. Flashcards are generated from the More practice panel and shown as a deck, one card at a time, that turns on Validate.

The board runs the loop on its own. Speak fills the answer box from `bin/listen.sh` through the bridge, Validate grades headless in `bin/quiz.py` with a fast model, and the verdict is written back as a `::: score` block. Nothing reaches the chat. Every item is logged; a misconception seen twice goes into the learning record.

# Learning records

Write one when the user demonstrated understanding, disclosed prior knowledge, corrected a misconception, or shifted the mission. Coverage is not learning. Quiz results are the usual evidence.

# Reference documents

Lessons are rarely reread; `reference/` is. Keep a glossary once terms accumulate, and cheat sheets for syntax, formulas, and procedures. Lessons link to them.

# Wisdom

When a question needs experience rather than knowledge, answer, then point to a community from RESOURCES.md. Respect a recorded opt-out.
