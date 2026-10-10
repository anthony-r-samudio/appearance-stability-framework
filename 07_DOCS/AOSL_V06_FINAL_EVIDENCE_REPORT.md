# AOSL v0.6 / v0.6.1 — Final Evidence Report

## Study classification

Internal, AI-assisted, post-failure arithmetic-safeguard validation.

This study assesses a narrow deterministic CHF revenue-increase checking rule.
It does not validate the full Appearance Stability Framework (ASF) or the
AI Output Stability Layer (AOSL) C1-C10 evaluation system.

## Frozen design

- Cases: 120
- Group A: 30 correct arithmetic claims
- Group B: 30 incorrect arithmetic claims
- Group C: 30 intended unsupported-format cases
- Group D: 30 boundary and adversarial cases
- Frozen expectations: 66 arithmetic checks, 54 abstentions
- Dataset authorship: internal, AI-assisted
- Independent label review: none
- External preregistration: none

The dataset and reference labels were hashed before the primary evaluation.

## Primary v0.6 outcome

Status: EXECUTION_FAILED.

Evaluator: v0.5.1.

Observed failure: unhandled System.Decimal OverflowException.

No complete primary result set was produced, so primary classification
accuracy is unavailable.

Post-failure inspection identified out-of-range decimal values in:

- V6-119: after and claimed fields
- V6-120: claimed field

These findings reproduce the parsing failure mechanism, although the
original exception did not report a case ID.

The primary evaluation was not rerun or replaced.

## Repair v0.6.1

The separately versioned repair introduced guarded numeric conversion and
handling for decimal subtraction overflow.

It preserved the strict ASCII-digit matching rules, used invariant-culture
numeric parsing, and retained the existing model-comparison logic.

Validation before the secondary study:

- Eight-case smoke test: original assertions 7/8
- Retrospective smoke review: 8/8 status and arithmetic-flag expectations
- S04 mismatch: smoke-test oracle expected an empty computed difference for a
  zero-increase abstention; original evaluator behavior retains 0
- Overflow smoke cases S07 and S08: controlled abstention, no exception
- Six-case v0.5.1 versus v0.6.1 regression: 6/6 identical result records

The retrospective interpretation does not replace the recorded smoke result.

## Secondary v0.6.1 outcome

Evaluation type: SECONDARY_POST_FAILURE.

Status: COMPLETED.

- Results: 120/120
- Raw arithmetic checks: 67
- Raw abstentions: 53
- Frozen-label agreement: 119/120 (99.17%)
- Supported-case correctness: 66/66 (100%)
- Unexpected checks against frozen abstention labels: 1/54 (1.85%)
- Uncontrolled execution exceptions: 0 observed

The secondary run met the protocol's numerical thresholds:
at least 95% supported-case accuracy, at most 5% unexpected checking
among cases labeled for abstention, and zero uncontrolled exceptions.

These findings concern the repaired secondary run only.
They do not convert the failed primary study into a success.

## V6-085 reference-label discrepancy

Frozen evidence:
Revenue was CHF 150 before and CHF 200 after.

Frozen response:
Revenue increased by CHF 49.

Frozen reference: NOT_CHECKED, C_UNSUPPORTED.

Observed result: CHECKED_NO_MODEL_COMPARISON.
Computed difference: CHF 50.
RuleBasedC1: 1, indicating an arithmetic mismatch.

Review conclusion: this input matches the supported grammar. Its claimed
increase is incorrect. The unexpected-check result is consistent with the
evaluator's specified arithmetic behavior.

This is a retrospective reference-label error assessment.

The original frozen label remains unchanged and the official comparison
remains 119/120. No post-hoc relabeling is incorporated into that score.

## Important interpretation constraints

- RuleBasedC1=0 means no arithmetic violation.
- RuleBasedC1=1 means an arithmetic violation.
- RuleBasedC1 is not the full AOSL C1 Factual Grounding score.
- No model C1 judgments were included in this run.
- No claim is made about full AOSL C1-C10 attribution accuracy.
- No cross-generator or cross-judge reliability was measured here.
- The cases were internally authored with knowledge of the rule.
- Post-failure repair and retrospective oracle inspection limit
  confirmatory strength and external validity.
- No production reliability or general-domain correctness is established.

## Final verdict

Primary v0.6: FAILED due to uncontrolled numeric overflow.

Secondary v0.6.1: COMPLETED and met the frozen protocol's numerical
acceptance thresholds, with one frozen-label disagreement subsequently
assessed as an authoring error.

Engineering conclusion: the identified decimal parsing vulnerability was
successfully mitigated on the tested cases.

Research conclusion: promising narrow internal evidence for a deterministic
arithmetic safeguard, not independent validation of the broader AOSL system.

## Next research direction

Freeze and archive this cycle. Subsequent work should use a separately
designed, independently reviewed challenge set with stronger coverage of
unsupported formats, numeric boundaries, and model-generated outputs.
