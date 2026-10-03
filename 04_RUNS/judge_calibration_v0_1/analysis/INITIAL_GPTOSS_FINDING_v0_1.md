# AOSL Judge Calibration v0.1 — Initial GPT-OSS Finding

## Status

Preliminary calibration finding.

This document records observed behavior from the first two GPT-OSS 20B calibration runs against the frozen pre-judge dataset.

It does not modify the frozen reference set or the constraint boundary notes.

## Frozen Dataset

Dataset:
04_RUNS/judge_calibration_v0_1/inputs/calibration_cases_v0_1.csv

SHA256:
3099FE9F0600A2A2DFFF692CE955A98230F111E06488C9C0C78641CFE266C226

Composition:
- 4 clean controls
- 2 C1 Factual Grounding failures
- 2 C8 Quantitative Accuracy failures

## Run 01

Judge:
gpt-oss:20b

Temperature:
0

Timeout:
180 seconds

Completion:
4 / 8 rows completed successfully

Observed successful cases:
- cal_clean_03 -> all constraints = 1
- cal_clean_04 -> all constraints = 1
- cal_c1_02 -> C1 = 0, all others = 1
- cal_c8_02 -> C1 = 0 and C8 = 0

## Run 02

Judge:
gpt-oss:20b

Temperature:
0

Timeout:
360 seconds

Completion:
6 / 8 rows completed successfully

Observed successful cases:
- cal_clean_02 -> all constraints = 1
- cal_clean_03 -> all constraints = 1
- cal_clean_04 -> all constraints = 1
- cal_c1_02 -> C1 = 0, all others = 1
- cal_c8_01 -> C1 = 0 and C8 = 0
- cal_c8_02 -> C1 = 0 and C8 = 0

Failures:
- cal_clean_01 -> TimeoutError
- cal_c1_01 -> incomplete or token-limited judge response

## Preliminary Findings

### 1. Execution reliability remains incomplete

Increasing the timeout from 180 to 360 seconds improved successful completion from 4/8 to 6/8.

This suggests that runtime behavior is currently a limiting engineering factor in calibration.

No scientific accuracy estimate should yet treat the eight-case dataset as fully observed.

### 2. Clean controls are behaving well among completed rows

All successfully completed clean-control judgments returned all ten constraints as 1.

This is encouraging for false-positive control, but the sample is still too small for a strong conclusion.

### 3. C1 attribution succeeded on the completed factual-grounding case

cal_c1_02 was scored as:

c1 = 0
c2-c10 = 1

This matches the human reference annotation.

### 4. C1 and C8 show repeated attribution overlap

Both completed quantitative-failure cases in Run 02 were scored:

c1 = 0
c8 = 0

The same C1+C8 pattern also occurred for cal_c8_02 in Run 01.

The current human reference annotation treats these cases as isolated C8 failures.

The repeated judge behavior suggests a possible boundary ambiguity between:

- C1 Factual Grounding
- C8 Quantitative Accuracy

The current C1 definition includes correctness of numbers, while C8 independently evaluates quantitative accuracy.

This overlap may allow the same arithmetic error to be interpreted as violations of both constraints.

## Interpretation

This is not yet evidence that GPT-OSS is incorrect.

It is also not yet evidence that the human annotations are incorrect.

The result indicates that the current rubric may not fully disambiguate numerical factual errors from quantitative reasoning errors.

This should be treated as a construct-boundary question.

## Next Investigation

Before modifying the rubric:

1. preserve the current runs unchanged
2. complete or retry the missing cases without modifying the frozen dataset
3. inspect the exact C1 and C8 wording used in the judge prompt
4. design an explicit C1-vs-C8 boundary rule as a proposed revision
5. test that proposed rule on a new dataset version rather than rewriting v0.1 post hoc

## Scientific Discipline

Do not modify:
- the frozen v0.1 dataset
- its human annotations
- the archived Run 01 or Run 02 outputs

Any rubric change should receive a new version identifier and be tested prospectively.

## Targeted Retry Finding

A targeted retry was performed on the two unresolved cases from Run 02.

Configuration:
- Judge: gpt-oss:20b
- Temperature: 0
- Max tokens: 1600
- Timeout: 600 seconds
- Dataset and boundary notes unchanged

### cal_clean_01

The previously unresolved clean arithmetic control completed successfully.

Result:
- c1-c10 = 1
- divergence = 0.0
- stability score = 1.0

This means all four clean controls have now produced a clean judgment in at least one successful run.

### cal_c1_01

The factual-grounding failure remained unresolved.

The judge response ended with:

- done_reason = length
- eval_count = 1600
- no final JSON content

The internal reasoning correctly identified early that:

- Sydney is not the capital of Australia
- C1 should receive a hard failure
- C2-C8 and C10 did not show obvious independent violations

However, the judge repeatedly looped over whether the unsourced factual statement also justified a C9 penalty.

The same case had previously exhausted an 800-token generation limit.

### Interpretation

This repeated token exhaustion suggests that the failure is not simply insufficient runtime allowance.

The judge appears to encounter a persistent decision conflict at the C1 Factual Grounding versus C9 Evidence Traceability boundary.

The current boundary notes state that a false claim should receive C1 as the primary failure, while C9 may receive a secondary penalty only when the lack of sourcing is independently notable.

For this simple common-knowledge factual question, that qualification appears insufficiently operationalized for GPT-OSS 20B.

This should be recorded as a judge/rubric interaction failure rather than converted into a completed calibration score.

Increasing the generation limit further would not resolve the underlying construct-boundary question and is not justified at this stage.

## Updated Preliminary State

Successful judgment coverage now exists for 7 of the 8 frozen calibration cases.

Observed signals include:

- all four clean controls have produced clean judgments
- the completed isolated C1 case matched the human annotation
- both quantitative failures were repeatedly attributed to both C1 and C8
- the remaining C1 case triggered repeated C1/C9 deliberation and token exhaustion

Two boundary questions therefore require prospective investigation:

1. C1 Factual Grounding versus C8 Quantitative Accuracy
2. C1 Factual Grounding versus C9 Evidence Traceability

No v0.1 frozen reference annotations or archived outputs should be modified in response to these findings.
