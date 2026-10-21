# Exam mode

Active when RESOURCES.md has any entry with tier ≤ 4 (a topic list, professor notes, a practice exam, or a past exam). Then course lessons default to the Problem Ladder template and are built backward from the problems the student must solve.

## Build the topic map

Write `reference/topic-map.md` once, and rebuild it on `add` or `sync`. Read every tier ≤ 5 source fully first. For each problem found:

- source and label (e.g. "Practice Test 1, Q3")
- problem type (compute, derive, design, conceptual, MCQ)
- points, if given
- skill tested, in one line
- concepts and formulas needed
- the trap, if any, in one line
- whether a solution is provided

Then group problems by topic and assign a priority:

| priority | when |
|---|---|
| High | in the official scope and (professor emphasised, or in the most recent practice exam, or ≥ 2 sources) |
| Medium | in scope, appears once |
| Low | in scope, only in tier 6–7 material |
| Supplementary | useful for another High topic but not tested alone |
| Out of scope | not in the topic list; say why it was excluded |

If points are given, compute the share per topic; otherwise say "qualitative" and cite the evidence. Label anything inferred.

## Topic map format

```md
# Test 1 — topic map (built 2026-09-02 from Practice Test 1, Test 1 topic list, HW1–2)

| topic | priority | share | problems | skill | trap |
|---|---|---|---|---|---|
| K-map simplification | High | 30% (30/100) | PT1 Q3 (15), Q4 (15); HW2 P2 | pick prime implicants, don't-cares | diagonal cells never merge |
| SOP from truth table | High | 20% | PT1 Q2; HW2 P1 | minterm reading | writing POS when SOP is asked |
| Number systems | Medium | 10% | PT1 Q1 | base conversion | sign extension |
| Timing diagrams | Out of scope | — | — | — | not in the topic list (inferred from HW3 absence) |
```

Followed by one line per problem with its full text location (file + page), so lessons can quote it.

## Using the map

- `/blackboard learn <topic> for <course>` with a map → Problem Ladder for that topic, anchor = the highest-authority problem, variants = the other problems of that type plus one modified-number version.
- `/blackboard learn for <course>` with no topic → the highest-priority topic not yet covered by a lesson.
- Outside STEM lessons, every block carries `→ Exam: <problem>` or `→ background`. STEM exam-prep lessons carry no inline tags and open with the **Exam Topics Breakdown** (TEMPLATES.md).
- Assigned homework in the map is never solved; ladders use modified-number analogs and end with a nudge naming the assigned problem.

## What the student sees first

When the map is built, render it on the board once with a one-line note: what was used, what is missing (`## Gaps`), and which topic the next lesson will take.
