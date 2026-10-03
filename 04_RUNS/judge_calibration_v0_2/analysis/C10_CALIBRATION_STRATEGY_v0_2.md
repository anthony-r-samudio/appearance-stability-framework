# C10 Calibration Strategy — v0.2

## Status

C10 is not currently treated as an ordinary low-ambiguity single-failure calibration target.

## Reason

C10 Constraint Interaction Consistency is relational by definition.

A C10 failure occurs when satisfying one legitimate constraint or response requirement structurally undermines another.

That creates a methodological problem for a pure single-failure vector:

- if another constraint is genuinely undermined, marking every adjacent constraint as fully satisfied may be conceptually inconsistent
- if the adjacent constraint is not actually violated, the case may not demonstrate a true interaction failure
- direct contradictions should be scored as C2 rather than C10

## v0.2 Decision

The main calibration set will contain low-ambiguity single-failure cases for:

- C2
- C3
- C4
- C5
- C6
- C7
- C9

C10 will be evaluated separately using boundary probes.

Those probes should test whether judges recognize a constraint-interaction problem and whether they consistently attribute the same case to C10 or to the adjacent constraint.

## Interpretation

Failure to isolate C10 cleanly is itself construct-validity evidence.

If C10 repeatedly collapses into neighboring constraints, this may indicate that:

1. the C10 definition needs refinement
2. C10 functions better as a meta-constraint than a peer constraint
3. C10 should be scored from interactions among other constraint scores rather than independently

No redesign decision is made yet.

The purpose of v0.2 is to observe the problem prospectively rather than force symmetry across all constraints.
