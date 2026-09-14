---
title: Boolean Algebra and the Basic Gates
course: ECE 2020
image: vintage relay switches
photo: assets/0001.jpg
credit: Electricity Switches by Michal Jarmoluk (CC0 1.0, via Openverse/stocksnap)
---

# Boolean Algebra and the Basic Gates

*Question first: why can a light switch do arithmetic?*

## One-liner

==Boolean algebra== is arithmetic on two values, 0 and 1, with three operations: AND, OR, NOT.


::: exp e1 folded
**Boolean algebra** — Boolean algebra here means the rule system for combining bits, where every value is either 0 or 1 and every calculation is built only from AND, OR, and NOT, so a switch that is open (0) or closed (1) can carry out the same operations. → background
:::
## Mechanism

1. AND outputs 1 only when every input is 1.
2. OR outputs 1 when any input is 1.
3. NOT flips the bit.

$$A + \overline{A} = 1 \qquad A \cdot \overline{A} = 0$$
units: $A$ one bit · $\overline{A}$ NOT $A$ · $+$ OR · $\cdot$ AND

## Quiz

::: quiz
topics: AND/OR/NOT, complement laws

### Question 1

::: mcq q1 c
Inputs $A = 1$, $B = 0$. Which expression evaluates to 1?
- $A \cdot B$
- $\overline{A} + B$
- $A + B$
why: OR needs only one input at 1, and $A$ is 1.
:::

### Question 2

::: mcq q2 a
Three inputs go into one OR gate. The output is 0. What do you know about the inputs?
- All three are 0
- At least one is 0
- Exactly one is 0
why: OR gives 0 only when every input is 0.
:::

### Question 3

::: mcq q3 b
$\overline{\overline{A}}$ for $A = 0$ equals:
- 1
- 0
- undefined
why: NOT applied twice returns the original value.
:::
:::
