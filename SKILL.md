---
name: blackboard
description: Use when the user invokes /blackboard or $blackboard, or says "open the blackboard", "open my lessons" or "show lesson N". Teach with lessons, derivations, explain-on-select, and quizzes rendered on a persistent black board. Course mode uses the user's material or LMS; self-study uses primary sources.
---

## Temporary board

"temporary board", "blackboard temporário", "solve X on a plain board": a throwaway page with only what was asked, no banner photo, no lesson number or course line, no byline, no quiz, no check-ins, no learning record. Write it to `~/.cache/blackboard/scratch/learn/lessons/NNNN-slug.md` (next free number; outside every course folder) with front matter `plain: true` (plus `title:` only if a heading helps), render it with `BLACKBOARD_LAYOUT=app board/render.sh <file>` so nothing opens on its own, then open `http://localhost:7331/w/scratch/lessons/NNNN` in a new tab of this host's browser pane. The content still follows the derivation rules (one step per line, reasons in the margin).

Before anything else, run `bin/update.sh` once per session. In a git clone it pulls new versions at most once a day; elsewhere it does nothing. If it prints a line, pass that line to the user.

## Open the blackboard (the default)

"open the blackboard", "open my lessons", or `/blackboard` with no arguments: open the all-lessons menu `http://localhost:7331/` beside the chat in this host's browser pane (Claude desktop: the in-app Browser pane; cmux: the existing browser pane; Codex app: the in-app browser), always with `http://` since a bare `localhost:7331` becomes https and fails. "show lesson 3 (in math)" opens `http://localhost:7331/m/3`: any unique prefix of the course slug, then the lesson number. If the page does not load, run `bin/install.sh` (it installs the always-on bridge) and retry. Reply in one line. Every reply that renders or changes a lesson ends with a clickable link to it, e.g. `[Open lesson 0003](http://localhost:7331/m/3)`.

People never need the address: `bin/install.sh` (run automatically by the first `render.sh` on macOS) keeps the bridge running at login through launchd (`com.blackboard.bridge`) and adds a **Blackboard** app to `~/Applications` and the Dock that opens the menu in the default browser.

The user wants to learn something, over many sessions, on the Blackboard. Lessons and board-requested explanations belong on the board. Questions asked in chat get a short answer in chat; do not edit or navigate the board unless the user asks.

## Changing this skill while the user studies

The user keeps studying on the live board (port 7331) while the skill is being changed. Never disturb it:
1. Edit in the source checkout and test on the **dev board**: `bin/dev.sh` starts a separate bridge from the checkout on port 7390 (own state dir, same lesson folders); `bin/dev.sh restart` after editing `bridge.py`; `bin/dev.sh stop` when done. Open it only in a **new background tab** that you close afterwards. Never navigate, reload, scroll or click in the user's tab, never render into their workspace to test, and never click quiz answers on the dev board (they log to the real learning records).
2. Sync to the installed copy only when the change is finished and checked. The open page then shows a small "Board updated · reload" chip instead of reloading; the user reloads when they want and keeps their place.
3. Restart the live bridge (`launchctl kickstart -k gui/$UID/com.blackboard.bridge`) only when `bridge.py` changed, and say so in one line.
4. Every finished change is committed and pushed right away, without asking, in the source repo the skill is developed in (`$BLACKBOARD_SRC`, default `~/stuff/projects/cskills`; skip this step if it does not exist): `git -C "${BLACKBOARD_SRC:-$HOME/stuff/projects/cskills}" add -A skills/blackboard && git commit -m "blackboard: <what changed>" && git push` (on a rejected push, `git pull --rebase` then push). One commit per change the user asked for, and the source checkout is the only place edited; `~/.claude/skills` and `~/.codex/skills` are rsync copies.

# Lesson author routing (required)

Before a new lesson or substantial rewrite, read [LESSON-WRITER.md](./LESSON-WRITER.md). The chatting model coordinates; a separate writer agent authors the lesson using the best-supported teaching model available in the current host, with explicitly selected effort. Run the quick model/evidence check before every lesson, record the decision, and dispatch with model and effort overrides. Do not silently inherit the parent model or hard-code a permanent winner. Even a parent already on the selected model delegates. When the writer finishes, a fresh tone-editor agent on the same model rewrites the prose to the Tone and Shape rules in TEMPLATES.md, without touching math, code, figures or quiz keys (see LESSON-WRITER.md **Tone pass**). A designated child writer or tone editor skips selection/delegation; never recurse. Explicit user model requests take precedence.

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
- `reference/chat/NNNN.json` — the board chat's history for lesson NNNN (see Chat). New chat renames it to `NNNN-<time>.json`.
- `learning-records/NNNN-slug.md` and `quiz-log.jsonl`. [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md)
- `NOTES.md` — the user's preferences about how they want to be taught.

Course mode vs self-study: a course is named in the command, or `MISSION.md` names one → course mode. Otherwise self-study. If both fit (no course named, a course workspace exists, and the topic is in its scope) ask once: "For <course> or on your own?"

# The board

Every lesson has a vertical reading-progress bar on the right, filling continuously from top to bottom like an HP bar. Use a muted olive/gold fill on a dark track; no draggable circle or needle. Chapter ticks remain alongside it: longer for `##`, shorter for `###`. Hover or keyboard focus shows the chapter's full title; click/Enter jumps to it. Clicking or dragging the track scrolls. The bar updates on scroll, resize, and content expansion; a page fitting on screen is full. This measures reading position only, never mastery or quiz XP. The lessons grid has no progress bar. Implement it in the shared template, not individual lessons.

**Chalk-writing animation:** every newly authored lesson block or explanation callout reveals its text progressively from left to right, letter by letter, with a subtle chalk edge. Preserve word wrapping, text selection, links, and accessible content. Equations use a left-to-right reveal without splitting KaTeX glyphs. Animate new/changed content arriving through SSE, including nested callouts, not unchanged content on reload or a fold toggle. New interactive blocks reveal their title/introduction; their controls and state changes remain immediately readable. Do not use flashing frames, flashing cursors, or forced scroll to signal new content. Respect reduced-motion preferences by showing content immediately. This is a visual reveal of received blocks, not a claim that the model streams individual tokens.

The board is a web page served by `board/bridge.py` at `http://127.0.0.1:7331`. Explain, quiz generation and quiz grading all run headless inside the bridge, so they behave the same in every host and never type into the chat. `board/render.sh <lesson.md>` starts the bridge if needed, opens the board once per host, and renders the file. The page updates itself (SSE); never open a second tab or pane. Hosts are auto-detected ([HOSTS.md](./HOSTS.md)), except the Codex desktop app: there run `BLACKBOARD_LAYOUT=app board/render.sh …` and open `http://127.0.0.1:7331/` in the in-app browser with the browser tool, once per session, so the board sits beside the chat. A read-only sandbox cannot run the board: say so in one line and stop; never answer the lesson in chat instead.

**One bridge, every workspace.** A single bridge on 7331 serves every course. Each workspace has a slug (the directory above `learn`: `math1552`, `ece2020`) and its own current lesson; `render.sh` pins the board tab to `/w/<slug>/`, so two sessions rendering different courses never clobber each other. `/lessons` is the hub across every folder (search, folder chips, Recent, this folder, other folders on this computer). `/w/<slug>/lessons/NNNN#e3` is a stable link to a lesson and a note, and `#s-<heading-slug>` to a section. A top bar holds, on the left, an **All lessons** link and the zoom control (− 100% +, keys `-` `+` `0`, 70% to 200% of the lesson column, remembered in this browser), and in the center a full-text search box: it matches anything written in any lesson in every folder (`/api/search` in the bridge), shows the matching line with the words highlighted and the section it sits in, and opens the lesson scrolled to that section (key `/`, arrows and Enter). The hub's search box uses the same full-text search. In the top-right corner the XP shows as a segmented health bar, one segment per quiz item, in the lesson's accent (gold when full), and the bar is the Contents button: XP counts verified answers only (multiple choice right, flashcards graded 4 or 5), and clicking the bar or pressing `t` opens the Contents drawer from the right. The drawer lists the `##` headings, the `###` of the current one, ✓ on sections scrolled past, the quiz score, and a dot on the section where new content just landed. Down the right edge runs a ruler-style scale of the lesson in the lesson's accent colour (as is the XP ring): one mark per `##` only (the major sections; `###` stay in the Contents drawer), each at its heading's true place in the document, beside a thin bar filled to the reading position; hovering a mark shows its title and clicking jumps there. On lesson pages the system scrollbar is hidden and the scale is the scrollbar: drag it or click anywhere on it to scroll. Selecting inside a display equation works like text: a drag that crosses lines selects whole visual lines (Explain receives those rows as TeX), a drag that stays on one line selects just the symbols it covers, going inside a fraction or power when the drag sits inside it (Explain receives e.g. `x^2 (in $x^{2}-x=0$)`), and inline math lights up as a whole formula. Multiple-choice answers stay changeable: picking another option replaces the verdict, and the key is revealed only once it is picked. Once an item is answered, a small **↺ Reset** button under it (keyboard-accessible) clears the pick, the verdict and the revealed key, returning the cards to unanswered and taking back that item's XP segment and the combo; it is quiet (no sound, no sparks). Every click is logged to `learning-records/quiz-log.jsonl` (`mode: mcq`, score 5 or 0), and a Reset appends `{mode: "mcq", item, event: "reset"}` with no score; earlier picks stay in the log as evidence. The latest event per item is restored when the page reloads (a reset restores as unanswered) and a restored pick counts for XP. A right pick plays a short celebration: gold 8-bit pixel sparks, a floating `+1 XP`, a combo counter for consecutive right picks, a square-wave chime (key `m` mutes, remembered per browser), and a `QUIZ CLEARED` fanfare when every item is right. It plays even with Reduce Motion on, because the user asked for it; it is brief and never loops. The same holds for the chalk-writing reveal of new blocks (word by word, then a sweep on display math): it ignores Reduce Motion, which is on on the user's Mac. Other board events get short 8-bit cues in the same voice and under the same `m` mute: a power-on arpeggio when a lesson starts streaming, a blip per new `##` section while it streams, a stage-clear jingle when it finishes, an item-get chime when an Explain note arrives, a soft low thud on a wrong pick, and a chime or thud when a flashcard is graded. A lesson whose front matter has `board: slate` gets a real-blackboard surface (a near-black textured board photo, `board/slate.jpg`, "Black smooth textured paper background" from magnific.com (Freepik free license: credit it if the skill is shared publicly), stacked on its mirror so it tiles, scrolling with the text, with a faint chalk bloom and a fine chalk grain (a static speckle mask, `board/chalk.png` inlined) on text, math and diagrams; drop a `board/slate-custom.jpg` next to it to use your own); it is on trial and may become the default. `###` subtitles are underlined, and bold `**Step N · …**` lead-ins at the start of a paragraph are boxed, with a hand-drawn chalk stroke in the lesson's accent, so they read as sub-steps of the `##` above. Headings are the navigation, so name them by what the section does; put each problem or major part at `##` so it gets a mark on the rail. Workspaces are every folder ever rendered plus everything found by scanning the roots in `~/.cache/blackboard/config.json` (`{"scan": ["~/notes", "~/school"]}`; `BLACKBOARD_SCAN=a:b` overrides) for `lessons/` folders. Never start a second bridge or use another port for lessons (the only exception is the dev board of `bin/dev.sh`, for testing skill changes).

**Codex desktop app.** Run the renderer with `BLACKBOARD_LAYOUT=app` (it also auto-detects `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop`). After the first successful render in a task:

1. Use the in-app Browser tool to create a tab, navigate that tab to `http://127.0.0.1:7331/`, verify the lesson title, and mark the tab as a deliverable so it survives the turn.
2. Call `codex_app__open_in_codex` with `target: {type: "browser", tabId: <the Browser tab's id>}` and `placement: "right"` so that exact navigated tab is presented beside chat. The app action may report `queued`; finish the turn so it can present the tab.

The tools may be deferred, so find them by exact name before concluding they are unavailable. Do not pass an app/provider tab id discovered elsewhere and do not call macOS `open`; both paths can leave a blank tab. Reuse the same Browser tab for later renders because SSE refreshes it.

**Streaming rule.** Write a lesson by appending to the `.md` block by block, never in one write at the end:

1. Write the front matter (`title`, `course`, `exam`, `model`, `image`) and run `board/render.sh <lesson.md> --live` (opens the board, marks the lesson as being written).
   **The parent does this first, before course research**, while running the quick writer-model check; leave the writer byline pending until selection, then let the designated writer author the body. The board is never blank: the page immediately writes "Explain: <title>" in chalk. Then, while you research (read the syllabus, the LMS, sources), keep the board alive with `bin/brainstorm.sh <lesson.md> "note" ...` after every step or two. Each call sends the whole list: the page handwrites new lines and wipes removed or moved lines with a felt eraser. Use the shape `"Explain: <topic>"`, `"Goal: <what the student must be able to do>"`, `"Sources:"` followed by `"- <source you are reading>"` lines (add them as you open them, drop the ones you reject, reorder by how much you will use them), `"Outline:"` followed by `"- 1. <section>"` lines once the plan is clear. Real notes only: what you are actually reading and deciding. When the first body block lands, the board wipes the brainstorm itself and starts writing the lesson.
2. `image:` is required and names a concrete, photographable subject **from the lesson's own topic**: what the lesson is about, or the clearest physical stand-in for it ("Java source code on a laptop screen" for a Java classes lesson, "river delta from above" for sediment transport, "printed circuit board macro" for logic gates). Never the lesson title, and never a chalkboard, blackboard, slate, chalk, classroom or whiteboard unless the lesson is about that object: the page is already a blackboard, so a board photo says nothing about the lesson. `render.sh` refuses a board-photo subject and falls back to the title's topic, with a warning. After the first render, look at the banner; if it does not show the lesson's subject, change `image:` and re-roll. Every lesson has a banner, no exceptions. `render.sh` fetches the photo itself when `photo:` is missing (background, via `bin/image.sh`) and writes `photo:`/`credit:` into the front matter; the board shows it as the banner above the title. Banners must be unique across every workspace in All lessons. Never copy another lesson’s `photo:` or use a shared default. `image.sh` rejects already-used bytes, source URLs, and photo credits under a global lock; `render.sh` rejects manually copied duplicate banners. If the subject search fails, it tries the topic derived from the title and then reports failure; it never falls back to a chalkboard or reuses a banner. Run `python3 bin/banner_guard.py` before delivery; resolve missing or duplicate banners. A lock older than 10 minutes is cleared. Run `bin/image.sh` by hand only to re-roll. Before finishing a lesson, check that its front matter has `photo:`.
3. Append each block (title, question, check-in, each section) with its own write, separated by blank lines, and never rewrite earlier blocks while writing (a rewrite rebuilds the page). The board writes with one pen, top to bottom: words letter by letter, math swept left to right, `###` underlines, `**Step N · …**` boxes and diagram strokes drawn like a hand draws them, each in turn. Opening a lesson shows what is already there at once; only content that lands afterwards is written by the pen. There is no loading bar: before the body, the brainstorm; between blocks, a resting chalk stick.
4. When the lesson is complete, run `board/render.sh <lesson.md>` (clears the live flag).

**One-line delivery messages.** After rendering: `On the board: 0004 Sum of Products from a Truth Table`. After a board explanation: `explained on board`. After a board quiz item: the score, one line. For questions in chat, follow the contract below.

# Chat answers: short and readable

- Default to extremely concise: answer first, usually 1–3 short sentences. Add at most one tiny example or a few equation lines when needed to resolve the exact confusion. Expand when the user asks for detail or a shorter answer would leave out an essential step.
- No preamble, headings, recap, unsolicited lesson, or narration about putting something on the board. Do not repeat the question. Explain only the concept or transition asked about, defining any new term before using it.
- A question typed or spoken in the left chat is a request for a chat answer. Answer there even while a lesson is open. Use the board for an explanation only when explicitly requested or when responding to its Explain control.
- In terminal/cmux chat, use plain text and readable Unicode math. Write NOT A (or ¬A after defining it), U · 1 = U, A + B, and (NOT A + A) · (NOT A + B). Preserve parentheses that show grouping.
- Never emit raw LaTeX commands or math delimiters in terminal chat: no `\overline`, `\frac`, `\cdot`, `\(…\)`, `\[…\]`, or dollar wrappers. The left terminal displays their source instead of rendering them. If the chat renderer is unknown, default to plain text; use LaTeX in chat only when rendering is confirmed. The board continues to use LaTeX.
- Use one transformation per line if steps are needed. A short example is: “NOT A + AB = (NOT A + A) · (NOT A + B). The first parentheses equal 1, so the result is NOT A + B.” Do not add a full derivation when this answers the question.
- Follow the user's language preference. These chat brevity rules do not compress the board's worked lessons or remove the intermediate steps required by its didactic writing contract.

# Lesson opening and chapters (required)

Every non-plain lesson starts below its title with a collapsed `::: prerequisites` block labeled **Prerequisites**. Inside: a simple list of the concepts the reader must already know, one short phrase per bullet. No introductory paragraph, time-budget prose, or repeated description of the lesson. If none, one bullet: “None.” This is an inventory, not hidden instruction: explain any prerequisite the learner has not demonstrated in the chapter where it is needed.

Next comes **Contents**: a short linked list of chapters, each with a brief phrase saying what it covers. Organize the body like a book: `## Chapter 1 · <topic>`, `## Chapter 2 · <topic>`, with `###` subsections. Even a short lesson can have one chapter. Keep Quiz and Sources as end matter; do not turn every small step into a chapter. Replace long opening roadmaps and pass tables with this compact index. See TEMPLATES.md for the exact frame.

Place 1–2 checkpoint questions after each chapter and 2–3 fresh mixed questions in the final quiz; retrieve earlier material briefly next study session. Use the large answer-card design in QUIZ.md. For every quiz, read QUIZ.md's **Source fidelity** first. Use relevant supplied questions as the basis, matching their topic, difficulty, reasoning, and option style. This applies to authored quizzes AND generated More practice.

# Author byline (required)

Every new lesson must set `model:` to the actual writer's full display name: family/version, variant, and reasoning effort when available. Example: `model: GPT-6 Astra Medium`, rendered as “by GPT-6 Astra Medium.” Do not shorten this to “GPT-6,” omit a known variant or effort, or copy the example as a default for another writer.

Use the designated writer agent's explicit runtime model metadata and effort, not the parent chat session's identity. If there is no delegation for a small edit, use the active session's explicit metadata. Do not infer the writer from the CLI brand, a configured default, or a previous lesson. If a component is unavailable, retain the known name and explicitly mark the missing component as unspecified; never invent it. Omit effort only when the model has no such setting. A full rewrite updates the byline to its actual writer; a small explanation, quiz addition, or copy edit does not claim authorship of the whole lesson. Do not change an existing lesson just to retrofit a byline unless the user asks.

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

Read [TEMPLATES.md](./TEMPLATES.md), including its **Didactic writing contract**, **Titles** and **Photos**, before writing or rewriting a lesson. Apply that contract to explanations as well, scaled to the requested depth. Choose Derivation, Concept Card, or Problem Ladder without asking. Every lesson has the frame: front matter → `# title` → Prerequisites dropdown → short Contents → one-line question → conditional check-in → numbered chapters → `## Quiz` → `## Twist` → `## Extra` (self-study, only if a video was used) → `## Sources`.

Before writing: read `learning-records/` (latest first) and `NOTES.md`. Include “Before we start” ONLY when the lesson actually builds on an earlier lesson (for example HW2 after HW1), not merely because its number is higher. Set `prev:` to that prerequisite lesson and take 1–2 relevant retrieval questions from its record, tagged `from lesson NNNN: <title>`. Omit the entire section for standalone lessons. Pick the zone of proximal development from the records and the mission; the user may also name the exact thing.

Concept sequencing: before streaming each block, check its prerequisites against the preceding blocks. Introduce the meaning of each new term, symbol, or abbreviation in plain words before using it in a rule or applying it to another concept. After writing, read the whole lesson in order and run the completion check in TEMPLATES.md before the final render. A rule name alone does not explain a step.

Illustrate when the idea has a picture (a balance sheet, a flow of money, a timeline, a K-map, vectors, a waveform, a small graph). Figures are `::: fig <template>` blocks with a JSON spec, drawn on the board as inline SVG in chalk strokes and the page's own fonts; nothing is rasterised. Templates and specs: [FIGURES.md](./FIGURES.md). Before a figure lands in the lesson, run `bin/fig-check.sh <template> <spec.json>` and look at the PNG it prints: fix overlaps and cut anything off the causal path (≤ 7 elements, labels beside the thing they name, one highlight colour on what changed, no legend). Place the block beside the step it explains; the caption goes in the spec.

**3D and physical objects: use `anatomy`.** When the idea is a physical or spatial thing whose shape is the explanation (an engine, a gear train, a valve, a lock, a dial gauge, a relay, a pump, a bridge truss, a molecule, an organ) and a flat `::: fig` would lose the depth, invoke the `anatomy` skill (`/anatomy`) to build the figure instead of drawing it with `::: fig raw`. Ask it for a lone dark-theme SVG (`figureSvg({ standalone: "dark" })`), have the parts the lesson names be parts in the drawing, save it as `$WS/lessons/assets/NNNN-<name>.svg`, check the PNG anatomy's own checks produce, and place it beside the step it explains with `::: figure assets/NNNN-<name>.svg` and a one-line caption saying what to look at. The board shows it as a still: anatomy's motion and drag live in its HTML page, which the board does not embed. Abstract relationships (flows, balance sheets, graphs, K-maps) stay `::: fig`. If `anatomy` is not installed, say so in one line and fall back to `::: fig raw` or a `::: photo`.

**Illustrate when it improves understanding.** Add a diagram whenever it makes an explanation easier to visualize or understand than prose alone, whether in an introduction, worked example, comparison, or later explanation. The trigger is teaching value, not first mention of a concept. Place it beside the explanation it clarifies. Do not add a diagram merely because a term is new, or assume one visual somewhere in the lesson is enough. Name the same parts in prose and drawing; distinguish control signals from conducting paths, mark connection points and gaps, and label simplified models. Show contrasting states when that helps explain what changes. Add one short sentence guiding the reader through the visual. Prefer a schematic for relationships and a real photo for physical appearance. During review, ask “Would a diagram make this easier to picture or understand?” If yes, add one there; if it adds no clarity, leave it out.

**Visual and interactive teaching contract.** Every new or substantially rewritten lesson includes at least one instructional visual tied to a specific explanation. The banner photo does not count. Every math lesson includes a manipulable mathematical example or a meaningful animation; a video is not mandatory when interaction teaches the idea better. For CS execution/state topics, prefer a step-through code trace with active line, variables, output, Previous/Next, Play/Pause, and Reset. For other subjects choose the medium that exposes the mechanism: circuit-state changes, a timeline, a causal diagram, or an image with a specific observation task. Never add decorative motion just to meet the rule.

Read [INTERACTIVES.md](./INTERACTIVES.md) when authoring an interactive block. Built-in `::: interactive trace` supports verified authored execution states; `::: interactive function` supports a polynomial graph with one coefficient slider. Do not present a precomputed trace as a live compiler. For unsupported concepts use the existing SVG figure templates or implement a suitable scoped interaction; do not invent renderer syntax. Put the visual beside the paragraph it explains, give the learner one thing to change or predict, and explain what the observed change means. Keep a short static takeaway so review does not require replaying a video.

Use Manim when continuous motion or a geometric transformation is clearer as an animation: add a Scene to `board/anim/scenes.py`, render with `bin/anim.sh <Scene> <name> $WS`, and embed `::: video assets/<name>.mp4` with a one-line observation prompt. Videos need replay/controls and must not autoplay in a distracting loop. A static figure is sufficient when motion adds no information, but does not by itself satisfy the math interaction/animation requirement.

Before finishing a lesson, verify the instructional visual renders; exercise interactive controls at initial, intermediate, and final states (or watch the animation); check values against the worked example; verify reset and keyboard operation. If a required visual cannot be produced, report the gap instead of claiming the lesson meets this contract.

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
- New content stays in place without a flashing frame or forced scroll.

# Chat

A chat panel docks on the right of every lesson page, like the Claude app beside the lesson. A round button in the top bar and ⌘⇧. (Ctrl+Shift+. elsewhere) open and close it; the open state carries across lessons, and the lesson column moves left to make room. Each lesson has its own Claude Code session, run by `bridge.py` as `claude -p` with the workspace as its directory and resumed on every turn, and its own history in `$WS/reference/chat/NNNN.json`; the **+** button archives that file and starts fresh. Every turn tells the model which lesson the user is reading and lists the lesson's sources (its `## Sources` section and `RESOURCES.md`, resolved to files and URLs), so it can quote them word for word. Tool steps show live above the reply and fold away when it ends. The square button stops a reply; a reply keeps running and is saved when the page goes away. The model is `BLACKBOARD_CHAT_MODEL` (default `opus`) at medium effort. It may read only the workspace, TEMPLATES.md and the exact files the lesson cites, fetch only the sites the lesson cites, and search the web; edits are allowed only inside the workspace. Anything else is denied without a prompt. Its instructions are `board/chat-system.md`. It does not load the user's own CLAUDE.md, hooks or MCP servers, and only the board's own pages may call it.

# Explain

Selecting words on the board raises **Explain**, **Definition** (the latter only for 1–5 words) and **Ask**, which opens the chat with the selection quoted in the composer. There is no separate In depth control. Explain writes an expandable callout below the selected paragraph; Definition adds a clickable dotted underline to the selected term and opens a small popup. Explain never adds an underline.

## Definition

A one-sentence meaning of the selected term **as this lesson uses it**, shown in a small popup at the selection. The popup closes on an outside click, Escape or scroll; the dotted term remains clickable to reopen it (Enter/Space also work). Definition anchors persist per workspace and lesson in this browser, including across reloads; they are separate from the server definition cache and from Explain blocks. Nothing is written to the lesson file and nothing reaches the chat. `POST /define` in the bridge answers it through `bin/define.py`.

Measured on a Karnaugh-map lesson: **0.00 s** for a term the lesson defines or precompute already covered, **0.7 s** for anything else, **0.01 s** for a repeat after a bridge restart.

Four things sit in front of the model, cheapest first:

1. **The lesson's own words** — a table row, a `**Term** — …` note, a `Term:` line, or a `GLOSSARY.md` entry in the workspace: returned verbatim, no model (`via: lesson`). Write definition tables and this tier answers instantly and in your own wording.
2. **Precompute** — serving a lesson page starts a background pass over that lesson's own terms (emphasis used more than once, table keys, inline code, words already asked about; schedule rows, formula fragments and advice phrases are skipped, 40 terms max). Each is defined and cached while the student reads, so the click is a cache hit. It runs one at a time and yields to any real click, and only when a local model is installed: 40 terms through the cloud CLI would be minutes of quota for definitions nobody asked for.
3. **Disk cache** — `~/.cache/blackboard/defs/<slug>/<lesson>.json`, so a lesson pays for a term once, ever, across restarts. Delete that file to re-generate.
4. **Local model** — Ollama, for anything still missing. `BLACKBOARD_DEFINE_LOCAL` picks the model; by default the definer prefers a plain instruct model (`llama3.2:3b`, `gemma3`, …) and falls back to the smallest installed. **Avoid a hybrid reasoning model here:** on Ollama 0.33 neither `think: false` nor `/no_think` silences qwen3, and its scratchpad arrives instead of the definition. The bridge keeps the model warm (`keep_alive` 30 m, a one-token ping at startup and on each page view).

`claude -p` (`BLACKBOARD_DEFINE_MODEL`, default Haiku) is the fallback when Ollama is not running: correct, but 12–20 s.

The definer is given the block the student selected from, the lines around it, the other lines of the lesson that use the term, and the lesson title and course, so "cell" in a K-map lesson is a map cell and "prime" is an implicant. Output is normalised on the way back: a leading "A <term> is …" is trimmed (the popup shows the term as its title), prose wrapped in `$…$` by a small model is unwrapped, and a scratchpad opener triggers one stricter retry.

Answers are cached per lesson and term, hovering the button prefetches, and concurrent requests for the same term wait on one result instead of running the model twice. A selection over 5 words has no Definition button: that is an Explain.

Explain is answered by `bridge.py` running `bin/explain.py` with the lesson, source block, and selection. The worker writes an `::: exp` block. Nothing reaches the chat.

**Callout presentation:** a full-width block below the selected paragraph, framed like chalk on the board: a hand-drawn-looking border (uneven radii) in the lesson's accent over a dark translucent fill, a title in accent chalk, ivory body text, a lightbulb icon, and a visible toggle. Keep the explanation inside this distinct background even when expanded. Open new callouts automatically; folding hides only the body and leaves the whole clickable header visible. The header supports keyboard activation. Clicking or selecting the explanation body does not collapse it. A discreet × removes the block. Show a quiet loading/error message inside the same callout. When the answer arrives, apply the chalk-writing animation to its text; no blinking, flashing frames, or forced scroll. Writing, folding or removing a callout rewrites the lesson file and rebuilds the page; the rebuild keeps the first visible block at the same screen position, and `#s-…`/`#e…` deep links apply only on the first load, never on a rebuild. Existing notes, including legacy `deep` notes, use this same presentation. Legacy `==…==` Explain markers render as ordinary text.

The interactive agent handles Explain when explicitly asked in chat or when the headless writer is unavailable:

1. Leave the selected paragraph untouched. Do **not** add `==…==`, dotted underlines, or an inline explanation link.
2. Insert after the source block, or inside the parent's `::: exp` for a nested request:
   ```
   ::: exp e<n> [folded]
   **<short descriptive title>** — <explanation>
   :::
   ```
   Use the next unused id. A short selection label is an acceptable title; prefer wording that identifies the question. Write enough to resolve the doubt, usually a short paragraph, with steps or equations when useful. No separate shallow/deep user choice is needed. Preserve older `deep` flags when editing existing files for compatibility.
3. `remove <id>`: `python3 bin/exp-remove.py <lesson.md> <id>` removes that block and children (and cleans up legacy markers).
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
