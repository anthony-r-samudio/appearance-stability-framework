# AOSL Arithmetic Safeguard — v0.6 / v0.6.1

## Research status

Internal, AI-assisted evaluation of a narrow deterministic arithmetic safeguard.

**Primary v0.6: EXECUTION_FAILED.**

**Secondary v0.6.1: COMPLETED and met the numerical acceptance thresholds.**

These are separate outcomes. The secondary evaluation does not replace
or retroactively repair the failed primary evaluation.

## Scope

The safeguard checks arithmetic consistency in a constrained CHF
revenue-increase statement format.

This is not validation of the complete Appearance Stability Framework
(ASF) or the AI Output Stability Layer (AOSL) C1-C10 evaluation system.

The `RuleBasedC1` field represents a narrow arithmetic-violation flag:

- `0`: no arithmetic violation detected
- `1`: arithmetic violation detected

It is not the formal AOSL C1 Factual Grounding score.

## Frozen dataset

120 internally authored cases:

| Group | Cases | Purpose |
|---|---:|---|
| A_CORRECT | 30 | Correct arithmetic |
| B_INCORRECT | 30 | Incorrect arithmetic |
| C_UNSUPPORTED | 30 | Intended unsupported inputs |
| D_BOUNDARY | 30 | Boundary and adversarial cases |

Frozen expectations: 66 checks and 54 abstentions.

The dataset and labels were frozen and hashed before the primary run.

## Primary outcome — v0.6

The v0.5.1 evaluator failed with an unhandled
`System.Decimal.OverflowException`.

No complete primary result set was produced.

The original execution record and post-failure analysis are preserved
under `primary-v06-run01/`.

## Repair — v0.6.1

The separately versioned evaluator introduced guarded decimal parsing
and subtraction-overflow handling.

The original smoke test recorded 7/8 passing assertions. A later
diagnostic established that S04 failed because of a test expectation
that conflicted with the evaluator's existing zero-increase behavior.

Regression comparison: 6/6 records identical between v0.5.1 and
v0.6.1 on the tested non-overflow subset.

## Secondary post-failure outcome

The repaired evaluator processed all 120 cases.

| Metric | Result |
|---|---:|
| Execution | COMPLETED |
| Frozen-label agreement | 119/120 (99.17%) |
| Supported cases correct | 66/66 (100%) |
| Unexpected checks | 1/54 (1.85%) |
| Uncontrolled execution exceptions | 0 observed |

Both the >=95% supported-accuracy criterion and the <=5%
unexpected-check criterion were met in this secondary evaluation.

These results are internal evidence, not independent validation.

## V6-085 — Retrospective label discrepancy

The frozen label expected abstention for:

Evidence: Revenue was CHF 150 before and CHF 200 after.

Response: Revenue increased by CHF 49.

This input matches the supported arithmetic grammar, and the correct
difference is CHF 50.

The evaluator checked the claim and flagged the mismatch.

The reference label appears incorrect. This was identified after
observing the results.

The original frozen label remains unchanged, and the official
agreement remains 119/120.

## Evidence layout

- `V06_FROZEN_CASES.csv` — immutable study inputs
- `V06_FROZEN_LABELS.csv` — original reference expectations
- `V06_FREEZE_MANIFEST.json` — dataset provenance
- `primary-v06-run01/` — failed primary execution and analysis
- `v061-isolated-smoke01/` — smoke inputs, outputs, interpretation
- `v061-regression01/` — version-to-version comparison
- `secondary-v061-run01/` — repaired secondary execution and outputs

Additional files:

- `../../05_SRC/Invoke-AOSLSafeguard-v061-invariant.ps1`
- `../../07_DOCS/AOSL_V06_FINAL_EVIDENCE_REPORT.md`

## Limitations

The cases were internally authored with knowledge of the supported
grammar. Labels were not independently adjudicated.

No model C1 judgments were supplied, and no independent cross-model
or cross-judge evaluation was performed in this study.

The findings do not establish general-purpose factual grounding,
complete AOSL C1-C10 reliability, or production readiness.

## Research verdict

The overflow vulnerability was mitigated on the tested inputs.

The repaired secondary evaluation met the declared numerical
thresholds, while the primary evaluation remains an execution failure.

Further research should use independently reviewed challenge cases
and stronger coverage of unsupported formats, numeric boundaries,
and model-generated responses.
