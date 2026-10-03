# AOSL Judge Calibration v0.2

## Purpose

Extend judge calibration beyond C1 Factual Grounding and C8 Quantitative Accuracy.

Judge Calibration v0.1 remains frozen and unchanged.

v0.2 tests whether local judges can correctly identify additional AOSL constraint failures before any claim of broad judge validity is made.

## Primary Questions

1. Can judges distinguish the remaining AOSL constraint families?
2. Can single-failure cases remain isolated rather than attracting adjacent penalties?
3. Does Gemma 4 26B retain the repeatability observed in v0.1?
4. Are failures observed across judges or specific to individual judge models?
5. Which constraints show construct-boundary ambiguity?

## Initial Scope

Prospective single-failure cases for:

- C2 Logical Coherence
- C3 Causal Integrity
- C4 Epistemic Calibration
- C5 Scope Discipline
- C6 Safety Integrity
- C7 Uncertainty Acknowledgment
- C9 Evidence Traceability
- C10 Constraint Interaction Consistency

Initial target:
- 2 low-ambiguity cases per constraint
- 16 cases total

## Experimental Discipline

Human reference annotations must be created before model scoring.

The dataset must be frozen and hashed before any judge sees it.

Judge outputs must not be used to retroactively modify the frozen human reference.

Unexpected disagreement is evidence.

## Initial Judge Plan

Primary local candidate:
- Gemma 4 26B

Comparison judge:
- GPT-OSS 20B

Gemma's strong v0.1 performance is provisional and must not be assumed to generalize to the new constraint families.

## Interpretation

Engineering completion, judge repeatability, human-reference agreement, and construct validity are separate questions.

Judge Calibration v0.2 should be capable of weakening confidence in both the judge and the AOSL constraint structure.
