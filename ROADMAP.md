# Blackboard roadmap: rewarding without decoration

Brainstormed 2026-09-13. Principle: **reward with information, never with decoration.** No confetti, badges, mascots, points that do not map to understanding, levels, avatars, daily-goal nagging, or leaderboards. Every reward is a true fact about progress, shown with restraint, in the board's existing palette (chalk on black, serif, one accent).

Everything below keys off quiz results and dates, never off courses, so it works for any folder and any user.

## 1. The XP bar means something
The bar at the top already exists. Fill it by verified understanding, not by scroll: each quiz item answered right fills a segment; each flashcard scored 4 or 5 fills one; an Explain you asked for adds nothing. A lesson with a full bar gets a thin gold rule under its title in the hub. That is the whole completion system.

## 2. Boss at the end
The lesson's built-in quiz is the boss. Visually locked (dim, "reach the end") until the reader has scrolled through the body, then it opens. 100% earns the gold rule in the hub. Misses become the next lesson's check-in: the "you died, try again" loop with pedagogy behind it.

## 3. Streaks by day, per folder, quiet
A small "3 days" mark beside the folder name in the hub. A missed day resets it. No notifications, no guilt copy.

## 4. A ledger, not a trophy room
One page, `/progress`: lessons finished, items answered, accuracy by topic chip, a heatmap of days. All in the board's palette. Numbers in a serif on black are satisfying on their own.

## 5. Retention is the score that matters
Cards missed earlier come back on later lessons' check-ins. When a previously-missed card is answered right a week later, the board says so in one line: "You missed this on 9/8. Right today." Costs nothing, most rewarding sentence in learning.

## 6. Sound and motion stay minimal
One chalk tap on a correct answer, the existing chalk-writing animation for new blocks, the pulse frame for changes. Nothing loops, nothing bounces.

## 7. Difficulty as a dial the reader turns
"Twist" is already hard mode. Optional but tracked: solving the twist is the only way the gold rule becomes a double rule. The one visible tier of prestige.

## Order of work
First slice: 1 + 2 + 5 together (the bar that fills only with verified answers, the boss quiz at the end, missed cards resurfacing). That is the loop. Everything else is polish on it. Data already exists in `learning-records/quiz-log.jsonl`; the bar and the hub read it, nothing new is stored.

## Also parked
- Grade a photo of handwriting inline on the lesson (rubric verdict under the block).
- Problem ladder from a review sheet as a deck.
- Compact stylesheet for tablet widths (the board is plain HTTP, so it can be served over a LAN).
- Timed exam mode: n problems, a clock, then the rubric check.
