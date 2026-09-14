---
title: Sum of Products from a Truth Table
course: ECE 2020
exam: Test 1, Q3–Q5
image: circuit board macro
photo: assets/0002.jpg
credit: Computer Circuit Board Macro (CC0 1.0, via Openverse/rawpixel)
prev: 0001
---

# Sum of Products from a Truth Table

*Question first: a table of 1s and 0s is in front of you. How do you turn it into a circuit?*

### Before we start · from lesson 0001: Boolean Algebra and the Basic Gates

::: checkin
- What does a bar over a variable mean in a Boolean expression? || NOT. $\overline{A}$ is 1 exactly when $A$ is 0.
- Why is $A + \overline{A} = 1$ no matter what $A$ is? || One of the two is always 1, and OR with a 1 is 1.
:::

## Try it without the tool

Here is the table. Try to write a ==formula== for $F$ by ==staring== at it.


::: exp e8 deep folded
**formula** — A formula here is a Boolean expression in $A$, $B$, $C$, $D$ built only from AND, OR, and NOT. Feed it any row of the table and it must evaluate to that row's $F$: a 1 on each bold row and a 0 on every other row. It has to match all eight rows at once, so guessing something that fits a few of them is no good. One correct answer for this table is
$$
F = \overline{C}\,D + C\,\overline{D},
$$
which reads "$C$ is 0 and $D$ is 1, or $C$ is 1 and $D$ is 0," and you can check it row by row. Any other expression that produces the same column is also a valid formula, since the table only fixes the outputs, never the shape of the expression. The point of trying it by eye first is to feel how hard the guessing is before the SOP recipe gives you one mechanically. → background
:::

::: exp e9
**staring** — Staring here means looking at the table and trying to guess the formula by eye, with no method, so you feel how hard the guess is before the SOP recipe builds it row by row. → background
:::
$$
\begin{array}{cccc|c}
A & B & C & D & F\\ \hline
0&0&0&0&0\\ 0&0&0&1&\mathbf{1}\\ 0&0&1&0&\mathbf{1}\\ 0&0&1&1&0\\
0&1&0&0&0\\ 0&1&0&1&\mathbf{1}\\ 0&1&1&0&\mathbf{1}\\ 0&1&1&1&0
\end{array}
$$

You do not need to spot a pattern. ==SOP== is a recipe that always works, and the pattern falls out at the end. → background

::: exp e6
**SOP** — short for Sum of Products: an OR ("sum") of AND terms ("products"), the standard form Test 1 asks for. → Exam: Test 1, Q3
:::

## The recipe

**==Sum of Products==** writes $F$ as an OR (sum) of AND terms (products), one term per row where $F = 1$. → Exam: Test 1, Q3

::: exp e4
**Sum of Products** — "sum" is the OR of several terms and "product" is the AND inside each term, so the name just says OR-of-ANDs.
:::

::: exp e7
**F** — the output of the circuit, one bit per row of the table, the thing the formula has to reproduce for every input combination. → Exam: Test 1, Q3
:::

### Step 1 — one AND term per 1-row

A variable that reads 1 is written plain. A variable that reads 0 gets a bar.

$$
\begin{aligned}
0\,0\,0\,1 &\;\to\; \overline{A}\,\overline{B}\,\overline{C}\,D \\
0\,0\,1\,0 &\;\to\; \overline{A}\,\overline{B}\,C\,\overline{D} \\
0\,1\,0\,1 &\;\to\; \overline{A}\,B\,\overline{C}\,D \\
0\,1\,1\,0 &\;\to\; \overline{A}\,B\,C\,\overline{D}
\end{aligned}
$$
units: $A,B,C,D$ inputs (1 bit each) · $\overline{X}$ = NOT $X$ · $XY$ = AND · $+$ = OR · $m_k$ = minterm, $k$ is the row read as a binary number

### Step 2 — OR them together

$$
\begin{aligned}
F &= \overline{A}\,\overline{B}\,\overline{C}\,D + \overline{A}\,\overline{B}\,C\,\overline{D} + \overline{A}\,B\,\overline{C}\,D + \overline{A}\,B\,C\,\overline{D} \\
  &= \sum m(1,2,5,6)
\end{aligned}
$$

### Predict before we simplify

Every term has $\overline{A}$. What happens to $F$ when $A = 1$?

::: predict
- F becomes 1
- F becomes 0
- Depends on B
reveal: $F = 0$. Every product contains $\overline{A}$, and $\overline{A} = 0$ kills every product. *What surprised you?*
:::

### Step 3 — simplify

$$
\begin{aligned}
F &= \overline{A}\left[\,\overline{B}\,\overline{C}\,D + \overline{B}\,C\,\overline{D} + B\,\overline{C}\,D + B\,C\,\overline{D}\,\right] && \text{factor out } \overline{A} \\
  &= \overline{A}\left[\,\overline{C}\,D\,(\overline{B}+B) + C\,\overline{D}\,(\overline{B}+B)\,\right] && \text{group by the } CD \text{ part} \\
  &= \overline{A}\left[\,\overline{C}\,D + C\,\overline{D}\,\right] && \overline{B}+B=1 \\
  &= \overline{A}\,(C \oplus D) && \text{XOR form}
\end{aligned}
$$

::: exp e5
**factor out A** — every one of the four terms contains $\overline{A}$, so by the distributive law $\overline{A}X + \overline{A}Y = \overline{A}(X+Y)$ it can be pulled in front of one bracket. → Exam: Test 1, Q3
:::

::: numeric
Row 0101: $A=0, B=1, C=0, D=1$. $\overline{A} = 1$, $C \oplus D = 0 \oplus 1 = 1$, so $F = 1$. Matches the table.
:::

::: figure /anim/media/images/scenes/endpoint_check.png
Manim still: the two merged pairs on the K-map. Each loop is one product term after simplification.
:::

⚠️ Two adjacent 1s on a K-map merge only if they differ in one variable. Diagonal cells never merge.

**Not this:** a Product of Sums starts from the 0-rows and gives $F$ as an AND of OR terms. Same function, different shape. Test 1 asks for SOP unless it says otherwise. → Exam: Test 1, Q5

## Result

$$\boxed{\,F = \overline{A}\,(C \oplus D)\,}$$

$F$ is 1 exactly when $C$ and $D$ differ, and only in the $A = 0$ half. → Exam: Test 1, Q4

## Quiz

::: quiz
topics: minterms, simplifying SOP, K-map merging, SOP vs POS

### Question 1

::: recall r1
Two product terms share every variable except one. Why can you drop that variable, and what is left?
:::

::: score 4
*"because the one that changes is or'd with its complement so it's one, and you keep the common part"*

Correct mechanism. Missing: the rule has a name, $X\overline{Y} + XY = X$. Say it back in one sentence.
:::

### Question 2

::: mcq q2 b
$F = \sum m(1,3)$ over inputs $A, B$. Which is the simplified SOP?
- $\overline{A}\,B + A\,B$
- $B$
- $A + B$
why: $m_1 = \overline{A}B$ and $m_3 = AB$ differ only in $A$, so they merge to $B$.
:::
:::

## Twist

Same table, but row 0011 is now 1 as well. Does $F$ still factor to $\overline{A}(C \oplus D)$? Work it before opening.

::: checkin
- Check || No. $\sum m(1,2,3,5,6)$: $m_1, m_3$ merge to $\overline{A}\,\overline{B}\,D$ and $m_2, m_3$ to $\overline{A}\,\overline{B}\,C$; with $m_5, m_6$ you get $F = \overline{A}(\overline{B}C + \overline{B}D + B\overline{C}D + BC\overline{D})$. The XOR is gone.
:::

## Sources

- Week 2 Lecture 2 slides (ECE 2020-B, 2026-09-02) · slides · tier 6
- Test 1 topic list, Canvas announcement · topic-list · tier 1
- Practice Test 1, Q3–Q5 · practice-exam · tier 3
