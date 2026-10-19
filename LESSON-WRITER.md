# Dedicated lesson writer

Every new lesson and substantial lesson rewrite is authored by a separate writer agent, even when the parent already uses the chosen model. The parent handles the conversation, gathers sources, checks the result, and publishes it. This instruction authorizes lesson-writing delegation; it does not authorize unrelated parallel work, new user-facing tasks, or changes to the user's global model settings.

## Quick check before every lesson

Do this before instructional prose is written. A title/loading shell can appear immediately while the parent checks the model. Do not inherit the parent's model or effort silently.

1. Identify the current host and its actual callable models and supported efforts from the live delegation tool schema, model picker/catalog, or installed CLI metadata. Claude Code chooses among available Claude models; Codex app/CLI chooses among available Codex models. Do not switch providers or subscriptions without an explicit user request. An explicit writer-model request overrides ranking, subject to availability.
2. Read the teaching/lesson row in `~/stuff/cortex/stack/model-fit.md` if it exists. Ignore `pending`/`stale` rows and evidence older than 7 days for this quick selection. This file is a candidate recommendation, not proof of account availability or a dedicated teaching benchmark. Do not use a global Claude winner as the Codex recommendation.
3. Make a brief live check (normally 1–3 targeted searches): current provider model availability/release notes, plus current independent evidence on explanation quality, instruction following, and reasoning relevant to the topic. Open the supporting pages. Prefer direct teaching evaluations and this user's recorded lesson feedback; general text preference and reasoning benchmarks are proxies, not proof of superior learning outcomes. Never rank by coding scores alone. Compare within the host's available models. If several lessons are authored in the same session, reuse an evidence check younger than 24 hours but recheck callable models and failures for each lesson.
4. Choose the strongest supported teaching candidate, not the cheapest parent model. Select effort explicitly: use supported `medium` as the normal starting point for a straightforward lesson; increase to `high` or a model-specific supported equivalent for dense multi-step derivations, unfamiliar technical material, or known reasoning failures. Higher effort is not evidence of clearer teaching; keep the same concise didactic contract. Use higher extremes only when the task or evidence justifies their latency. A candidate-specific evidenced effort recommendation takes precedence over this heuristic.
5. Save a small decision receipt to `$WS/reference/lesson-writer-NNNN.json` before dispatch: checked_at (UTC), host, lesson path, selected model ID, supported effort, evidence URLs/dates, confidence, why this candidate fits, and any fallback. Create `reference/` if needed. Record requested versus resolved model separately when runtime metadata supplies both. Never invent a resolved identity.
6. Tell the user once, briefly: “Writing with <model> at <effort>.” If no direct teaching comparison exists, call it the best-supported available choice, not an objectively proven best teacher.

If browsing is unavailable, use a recent qualifying recommendation and disclose that the live check was unavailable. With no recent evidence, use the strongest verified available general reasoning/writing model as a provisional choice and record low confidence. Never manufacture a ranking. Do not stop useful source gathering while selecting the writer.

Names such as Fable, Opus, Astra, Sol, and Luna are examples, not permanent defaults. Resolve exact callable IDs at runtime. Do not treat a model named in an old lesson as today's winner.

## Dispatch on the current host

Prefer the host's native agent tool when it supports the selected model and explicit effort. Inspect the tool's actual schema; do not invent parameters.

- **Codex app:** use the available `spawn_agent`/collaboration equivalent, passing the selected `model` and `reasoning_effort`. If the schema only permits overrides with `fork_turns: "none"` (or a partial fork), use that and include a complete briefing. Do not use a full-history fork that silently inherits the parent's model. Do not create a new sidebar task. While the writer works, the parent independently verifies source scope, prepares assets, or checks worked examples.
- **Claude Code:** use its Agent/subagent facility with an explicit supported model and effort if both can be set. If native delegation cannot select the exact model or effort, run a separate headless Claude Code writer with explicit `--model <id>` and `--effort <level>`. Check installed `claude --help` first. Never accept `inherit` or an implicit default as the selected model.
- **CLI fallback:** a separate headless writer process counts as the dedicated agent. Claude uses `claude -p --model <id> --effort <level> --output-format json`; Codex uses `codex exec --model <id> -c 'model_reasoning_effort="<level>"'` with the current supported output options. Verify the installed help/schema before use. Supply prompts through stdin or structured tool arguments, not shell interpolation. Keep normal approval/sandbox boundaries. If the writer cannot edit the destination, have it return the authored blocks for the parent to save unchanged; do not relax permissions just to get an agent running.

Check the dispatch result, error status, and runtime model metadata before claiming success. A selected model may be listed yet unavailable due to account access or quota. If the writer fails, select the next strongest eligible model **within the same host**, update the receipt, disclose the fallback in one line, and launch another writer. If a user explicitly required one exact model, report that failure rather than silently substituting. Never let the parent quietly write the lesson when delegation failed. If no writer is callable, retain existing content and explain the concrete blocker.

## Writer briefing and ownership

Pass all of the following to the writer:

- `Role: Blackboard lesson writer. Writer already selected; do not run model selection or spawn another writer.` This prevents recursive delegation.
- Exact absolute lesson/workspace paths and bounded write scope. Existing user annotations, quiz records, unrelated lessons and global settings must be preserved.
- User's requested topic, language, demonstrated prior knowledge, target assignment/exam, time budget, and explicit teaching preferences.
- Absolute paths to SKILL.md, TEMPLATES.md, QUIZ.md, relevant mission/learning records, and all source files or inspected excerpts. Require source reading, source-matched quiz items, and answer verification.
- Selected model and effort, plus instruction to use actual runtime identity for the byline. The parent model must not appear as the author merely because it saves or renders the file.
- Full lesson requirements: compact prerequisites, chapter contents, conditional prerequisite check-in, source-grounded teaching, diagrams wherever they make an explanation easier to visualize or understand, placed beside that explanation (not automatically at first mention), an `image:` subject taken from the lesson's own topic (never a chalkboard or classroom), unique banner, and streaming blocks. Child writes body blocks; parent owns browser navigation and the final render. Do not have both write the same file concurrently.
- Code blocks: every line at or under 60 characters; comments go on their own line above the statement, never trailing a long line.
- Questions with code (`::: mcq` stems, `::: checkin` questions and answers): more than one statement goes in a fenced ```java block with real indentation, then the question sentence on its own line. Never inline a class or several statements into a sentence.

The parent may create the initial metadata/loading shell without claiming to have authored the lesson. The writer can stream sequential blocks into the lesson when it has scoped access. When it returns blocks instead, save those blocks sequentially. Follow up with that same writer for substantial teaching corrections; parent edits are limited to mechanical integration and verification fixes, with authorship kept accurate.

## Tone pass (second agent)

When the writer finishes a new lesson or substantial rewrite, a second agent edits it for tone and order before the completion check. Writing and editing are separate jobs, and a fresh reader catches drift that the writer approves in its own text.

- **Model:** the same model and effort the writer used, taken from the receipt. Dispatch it the same way as the writer. Run it only after the writer is done; never let two agents write the file at once.
- **Fresh context:** do not fork the writer's conversation. The briefing is the lesson path, the absolute path to TEMPLATES.md (sections **Shape of each explanation**, **Tone: simple and to the point** and **Sequence meaning before use**), and this role line: `Role: Blackboard tone editor. Do not run model selection, spawn agents, or add new teaching content.`
- **What it does:** it reads the lesson top to bottom as a learner, then works through these steps:
  1. Rewrite prose sentences to follow the Tone rules.
  2. Check that every term, symbol and notation appears after its plain explanation. Where one appears first, move its explanation earlier or add one plain sentence before the first use.
  3. Where an explanation is out of Shape order, reorder paragraphs within its section.
- **What it must not change:** math (inline and display), equations, code blocks, `::: fig` and `::: interactive` specs, `::: mcq` and `::: checkin` questions, options and keys, front matter, headings, and Sources. It edits prose only.
- **Parent checks:** before dispatch, copy the writer's version to `$WS/reference/lesson-NNNN.draft.md`. Afterwards, diff the two. Revert any hunk that touches something on the must-not-change list. Then run the completion check below.
- **Byline and receipt:** the byline stays the writer's. Add `tone_editor` (model, effort, outcome) to the receipt.
- **If it fails:** keep the writer's version, say so in one line, and continue to completion.

## Completion

Wait for the writer and the tone pass to finish. Verify coverage against sources, every quiz key, the prerequisite list, chapter links, diagrams and math, unique banner, and the actual writer byline. Rendering or model reputation is not proof of correctness. Record writer identity/outcome in the receipt; keep prompts and model-selection details out of the student's lesson body.

This route applies to new lessons and substantial lesson rewrites. It does not switch the left-hand chat, regenerate existing lessons just because a new model launches, or change the separate quiz/Explain/definition workers unless explicitly requested.

Implementation references (verify again when host capabilities change):
- [Official OpenAI subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Claude Code custom subagents](https://code.claude.com/docs/en/sub-agents)
- Local `codex exec --help`, `claude --help`, and the live host tool schemas are authoritative for installed controls.
