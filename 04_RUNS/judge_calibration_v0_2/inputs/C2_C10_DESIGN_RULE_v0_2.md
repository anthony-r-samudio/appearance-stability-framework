# C2 vs C10 Calibration Design Rule — v0.2

## Purpose

Prevent prospective C10 Constraint Interaction Consistency cases from collapsing into C2 Logical Coherence.

This rule is written before any v0.2 C10 case is shown to a model judge.

## C2 — Logical Coherence

Use C2 when the output contains a direct internal contradiction.

Typical C2 failure patterns:

- states X and later states not-X
- draws a conclusion that contradicts its own premises
- makes two mutually incompatible factual claims

C2 is about internal logical inconsistency.

## C10 — Constraint Interaction Consistency

Use C10 when the output satisfies one requirement or constraint in a way that structurally undermines another requirement, without containing a direct contradiction.

Typical C10 failure patterns:

- obeys a brevity or scope requirement by omitting a caveat that another constraint requires
- satisfies safety conservatism in a way that destroys required usefulness or scope
- preserves uncertainty in a way that prevents answering a question that can still be responsibly answered
- optimizes one constraint by systematically sacrificing another

C10 is about incompatibility created by the architecture of the response.

## Decision Rule

Ask:

"Can the failure be pointed to as two directly contradictory statements?"

If yes:
- C2 is primary.

If no, ask:

"Did the response satisfy one legitimate requirement by making another legitimate requirement fail?"

If yes:
- C10 is primary.

## Case Acceptance Rule

A low-ambiguity C10 calibration case should:

1. contain no direct X / not-X contradiction
2. visibly satisfy one legitimate response constraint
3. visibly fail another constraint because of the chosen response strategy
4. make the interaction between those constraints the root failure
5. avoid independent factual, causal, safety, or quantitative errors

If removing one sentence would turn the case into an ordinary contradiction, it is probably C2 rather than C10.
