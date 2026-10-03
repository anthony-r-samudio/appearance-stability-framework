# Judge Calibration v0.2 — Freeze Record

## Status

Frozen before model-judge exposure.

## Canonical Dataset

Path:

04_RUNS/judge_calibration_v0_2/inputs/calibration_cases_v0_2.csv

Rows: 14
Unique prompt IDs: 14

Status value:

frozen_prejudge

## SHA256

884044AF0F59B681622B6E2AE420FD892666A0E4D7E33F9F9C765F798B52C2DA

## Source Repository State

Pre-freeze HEAD:

e1a9649d3b8752e6ca5e4d104c574c2e87543c95

Branch:

experiment/judge-calibration-v0.2

## Composition

- C2 Logical Coherence: 2
- C3 Causal Integrity: 2
- C4 Epistemic Calibration: 2
- C5 Scope Discipline: 2
- C6 Safety Integrity: 2
- C7 Uncertainty Acknowledgment: 2
- C9 Evidence Traceability: 2

Total: 14 cases

C1 and C8 were exercised in Judge Calibration v0.1.

C10 is intentionally excluded from the ordinary single-failure set and is treated separately as a construct-validity / boundary-probe problem.

## Freeze Discipline

The human reference annotations, prompt text, output text, ambiguity labels, and expected constraint vectors were established before model-judge exposure.

After this freeze:

- do not alter the canonical v0.2 dataset based on judge behavior
- do not change expected scores after seeing model output
- do not rewrite cases to improve judge agreement
- any substantive annotation or case change requires a new dataset version

Unexpected judge disagreement is evidence.

## Intended Next Step

Score this exact frozen dataset with the local judge candidates under preserved, reproducible configurations.

Gemma 4 26B is the primary local candidate.

GPT-OSS 20B remains a comparison judge and must not be assumed calibrated.
