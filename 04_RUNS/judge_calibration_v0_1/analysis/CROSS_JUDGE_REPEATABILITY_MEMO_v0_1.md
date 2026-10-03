# AOSL Judge Calibration v0.1 — Cross-Judge Repeatability Memo

## Status

Preliminary cross-judge calibration result.

This memo compares GPT-OSS 20B and Gemma 4 26B on the same frozen eight-case calibration set.

No changes were made to:
- the frozen dataset
- human reference annotations
- boundary notes
- scorer
- runner
- temperature

## Frozen Dataset

Dataset:
04_RUNS/judge_calibration_v0_1/inputs/calibration_cases_v0_1.csv

SHA256:
3099FE9F0600A2A2DFFF692CE955A98230F111E06488C9C0C78641CFE266C226

Composition:
- 4 clean controls
- 2 C1 Factual Grounding failures
- 2 C8 Quantitative Accuracy failures

## GPT-OSS 20B

Observed behavior across initial runs and targeted retry:

- execution reliability was incomplete
- clean controls that completed were scored clean
- cal_c1_02 matched the human reference
- cal_c1_01 repeatedly exhausted generation limits while deliberating over C1 versus C9
- both C8 failures were scored as C1 + C8 rather than isolated C8

Usable successful judgment coverage eventually reached 7 of 8 frozen cases.

## Gemma 4 26B — Run 01

Completion:
8 / 8

Agreement with frozen human reference:
8 / 8

Observed pattern:
- 4 clean controls -> all constraints = 1
- 2 C1 failures -> C1 = 0 only
- 2 C8 failures -> C8 = 0 only

No execution failures occurred.

## Gemma 4 26B — Run 02

Configuration was identical to Run 01.

Completion:
8 / 8

Agreement with frozen human reference:
8 / 8

Observed pattern:
- 4 clean controls -> all constraints = 1
- 2 C1 failures -> C1 = 0 only
- 2 C8 failures -> C8 = 0 only

No execution failures occurred.

## Repeatability

Gemma produced identical constraint score vectors across Run 01 and Run 02 for all eight cases.

Observed repeatability on this frozen set:

- 8 / 8 case-level score-vector agreement
- 80 / 80 individual constraint-score agreement
- no completion failures
- no attribution changes across runs

## Cross-Judge Interpretation

The earlier C1/C8 and C1/C9 difficulties observed with GPT-OSS were not reproduced by Gemma under the same frozen dataset and rubric.

This weakens the interpretation that the observed ambiguity is necessarily an unavoidable defect in the current AOSL constraint structure.

The current evidence is more consistent with one or both of the following:

1. judge-specific behavior in GPT-OSS 20B
2. a judge-by-rubric interaction in which some models operationalize the constraint boundaries more reliably than others

This does not prove that the C1/C8 or C1/C9 boundaries are fully resolved.

## Limitations

The calibration set is very small.

It currently contains only:
- clean controls
- C1 failures
- C8 failures

The cases are intentionally simple and low ambiguity.

Two identical Gemma runs at temperature 0 are encouraging but are not sufficient to establish broad judge validity.

No conclusion should yet be generalized to C2-C7, C9, or C10.

## Current Decision

Gemma 4 26B is the strongest local judge candidate tested so far under this calibration protocol.

GPT-OSS 20B should not currently be treated as a calibrated local judge.

Do not modify the v0.1 rubric based only on GPT-OSS behavior.

## Next Scientific Step

Broaden the prospective calibration set to include additional constraint families while preserving the current frozen v0.1 dataset unchanged.

Priority should be given to low-ambiguity single-failure cases for:

- C2 Logical Coherence
- C3 Causal Integrity
- C4 Epistemic Calibration
- C5 Scope Discipline
- C6 Safety Integrity
- C7 Uncertainty Acknowledgment
- C9 Evidence Traceability
- C10 Constraint Interaction Consistency

Human reference annotations should again be frozen before any model judge sees the new cases.

## Scientific Discipline

The current findings separate three questions:

- engineering reliability
- judge repeatability
- construct validity

Success on one does not establish success on the others.
