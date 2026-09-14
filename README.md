# Blackboard

A teaching skill for Claude Code and Codex. You ask for a lesson, the agent writes it on a black board in your browser: derivations one step per line, real photos of the thing, chalk diagrams, a quiz at the end. Select any sentence and ask why. Nothing gets pasted into your chat.

![board](research/board.png)

## Install

```
npx skills@latest add caioba-codes/blackboard
```

Or copy this folder to `~/.claude/skills/blackboard` and `~/.codex/skills/blackboard`.

Then, from any folder with your material in it:

```
/blackboard learn how the NVIDIA DGX Spark works
/blackboard learn u-substitution for MATH 1552
```

The first line is self-study: it reads primary sources and writes the lesson. The second is course mode: it uses your own files (syllabus, past exams, homework) and tags every block with the exam problem it serves.

## What you get

1. One board page at `http://127.0.0.1:7331`, one lesson at a time, written block by block while you watch.
2. Fixed templates. Derivation, Concept Card, Problem Ladder. One operation per line, the reason in the margin, the answer boxed.
3. Explain on select. Highlight words, click Explain. A note appears under the sentence, typeset like the lesson, and folds away on click.
4. A quiz at the end of every lesson. Multiple choice built in, flashcards on demand, graded by voice or text.
5. Photos when the subject is a physical thing. The object itself as the banner, its parts beside the sections that discuss them.
6. A hub across every folder on the machine. Search, recent, this folder, the others.
7. Homework is never solved for you unless you ask for exactly that.

## Requirements

- macOS or Linux, Python 3.10+
- `claude` (Claude Code) or `codex` on PATH. Explain and quiz grading run headless through it.
- `node` for the chalk figures (roughjs). `npm install` in this folder once.
- Optional: `pandoc` + `tectonic` (worksheets to PDF), `yt-dlp` (transcripts), `pdftotext`, `manim`.
- Voice answers need macOS (on-device Apple Speech).

Run `bin/doctor.sh` to check all of it.

## Hosts

- Claude Code or Codex desktop: the board opens beside the chat.
- cmux: the board is a tab in your browser pane, pinned to the folder you are working in.
- Plain terminal: a browser tab.
- Headless machine: render, screenshot, send the picture. See `HOSTS.md`.

## Files

`SKILL.md` is what the agent reads. `TEMPLATES.md` is the writing contract. `QUIZ.md`, `EXAM-MODE.md`, `LMS.md`, `FIGURES.md`, `HOSTS.md` cover the rest. `board/` is the server and the page. `bin/` holds the headless writers and helpers. `ROADMAP.md` is what comes next.

## License

MIT
