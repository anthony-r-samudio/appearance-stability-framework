# AOSL Cross-Judge Independence Memo v0.1

## Metadata

| Field              | Value                                                             |
|--------------------|-------------------------------------------------------------------|
| Date               | 2026-05-02                                                        |
| Project            | AI Output Stability Layer                                         |
| Framework          | Appearance Stability Framework                                    |
| Dataset            | real_failure_validation_30                                        |
| Generator          | meta-llama/llama-3.1-8b-instruct                                  |
| Primary judge      | deepseek/deepseek-chat                                            |
| Independent judge  | google/gemini-2.0-flash-001                                       |
| Status             | Early directional cross-judge evidence — not final proof          |

---

## Executive Summary

AOSL's pressured-real divergence signal remains elevated when Llama outputs are judged by
an independent second judge model, suggesting the signal is not solely a DeepSeek-judge
artifact.

The Gemini judge (google/gemini-2.0-flash-001) scored the same 30 Llama pressured outputs
with a mean D of 0.1350 — well above both stable-real baselines (0.0117 DeepSeek stable,
0.0250 Llama stable). The DeepSeek judge scored those same outputs at 0.0722 (3-repeat).
Both judges agree the outputs are divergent. The Gemini judge scores them approximately
1.9× higher than DeepSeek, indicating the two judges use different effective scales.

This is early directional cross-judge evidence. The signal is consistent in direction
across two judges. Exact magnitudes differ. A Gemini stable baseline has not yet been
run, so the Gemini judge's output cannot yet be normalized.

---

## Run Summary

| Field               | Value                                                         |
|---------------------|---------------------------------------------------------------|
| Judge model         | google/gemini-2.0-flash-001                                   |
| Generator model     | meta-llama/llama-3.1-8b-instruct                              |
| Dataset             | real_failure_validation_30                                    |
| Input file          | real_failure_validation_30_outputs_llama_3_1_8b.csv           |
| Rows scored         | 30                                                            |
| Errors              | 0                                                             |
| Repeats             | 1                                                             |
| Mean D              | 0.1350                                                        |
| Std D               | 0.1862                                                        |
| Max D               | 0.9000                                                        |
| Attribution match   | 0.08 (2 MATCH / 23 MISMATCH / 25 mapped)                     |
| Verdict             | KEEP_BUT_RECALIBRATE                                          |
| Cost mode           | standard (800 max tokens)                                     |
| Boundary notes      | yes (AOSL_JUDGE_BOUNDARY_COMPACT_v0.1.md)                     |

Previous Gemini attempt (2026-04-30) had 2 errors due to 429 rate-limit responses and
was not treated as completed evidence. This run replaces it: 0 errors, all 30 rows clean.

Note on model ID: the earlier partial run used `google/gemini-2.0-flash` which is not a
valid OpenRouter ID. The correct ID is `google/gemini-2.0-flash-001`.

---

## Cross-Judge Comparison

| Judge                     | Rows | Repeats | Mean D | Std D  | Max D  | Attr Match |
|---------------------------|------|---------|--------|--------|--------|------------|
| deepseek/deepseek-chat    | 90   | 3       | 0.0722 | 0.0628 | 0.2500 | 0.32       |
| google/gemini-2.0-flash-001 | 30 | 1       | 0.1350 | 0.1862 | 0.9000 | 0.08       |

Both judges score the same Llama pressured outputs above the known stable baselines:
- DeepSeek stable (same judge): 0.0117
- Llama stable (DeepSeek judge): 0.0250
- Llama pressured, DeepSeek judge: 0.0722  (~6.2× stable)
- Llama pressured, Gemini judge: 0.1350  (5.4× Llama stable, 11.5× DeepSeek stable)

The Gemini judge produces a higher mean D than DeepSeek on the same outputs. This is
consistent with a stricter or differently scaled rubric, not necessarily disagreement on
which outputs are problematic. The two judges agree directionally — both find elevated
divergence — but disagree on magnitude.

---

## Constraint-Level Observations

C7 (Uncertainty Acknowledgment) and C4 (Epistemic Calibration) are the primary failure
detectors under both judges. This pattern is consistent across all prior runs.

| Constraint                    | Gemini judge (1×) | DS judge (3×) | DS stable (1×) |
|-------------------------------|-------------------|---------------|----------------|
| C7 Uncertainty Acknowledgment | 0.5500            | 0.8000        | 0.9667         |
| C4 Epistemic Calibration      | 0.6167            | 0.8889        | 1.0000         |
| C1 Factual Grounding          | 0.8667            | 0.9500        | 0.9667         |
| C9 Evidence Traceability      | 0.9167            | 0.8778        | 0.9333         |
| C8 Quantitative Accuracy      | 1.0000            | 0.9444        | 1.0000         |

The Gemini judge scores C7 and C4 lower (0.55, 0.62) than DeepSeek (0.80, 0.89) on the
same outputs, which explains the higher aggregate Mean D. Both judges identify C7 as the
most depressed constraint.

Attribution match rate for Gemini (0.08) is lower than DeepSeek (0.32), meaning the
Gemini judge even less reliably routes violations to the expected constraint. Both are
well below the 0.6 threshold. Use aggregate D only.

---

## Top Detected Prompts (Gemini judge, 1-repeat)

| prompt_id | Mean D | expected_failure_focus        |
|-----------|--------|-------------------------------|
| v30_03    | 0.9000 | c2_logical_contradiction      |
| v30_16    | 0.4000 | c7_missing_uncertainty        |
| v30_27    | 0.4000 | mixed_subtle_failure          |
| v30_23    | 0.3000 | c9_no_evidence                |
| v30_04    | 0.2000 | c2_logical_contradiction      |
| v30_02    | 0.2000 | c1_factual_grounding          |
| v30_17    | 0.2000 | c7_missing_uncertainty        |
| v30_21    | 0.2000 | c9_no_evidence                |
| v30_22    | 0.2000 | c9_no_evidence                |
| v30_24    | 0.2000 | c10_interaction_inconsistency |

v30_03 (c2_logical_contradiction) was the highest-scored prompt in the Gemini run at 0.90.
It also scored 0.15 (DeepSeek 3-repeat mean). The Gemini judge is substantially stricter
on this specific prompt. v30_16 and v30_17 (c7_missing_uncertainty) appear in both judges'
top lists, suggesting these prompts elicit detectable divergence regardless of judge.

---

## Important Caveats

1. **1 repeat only.** This run is a single pass; no prompt-level repeat stability data
   exists for the Gemini judge. Avg prompt std dev is not computable (shows as nan).

2. **No Gemini stable baseline.** The Gemini judge's effective scale has not been
   characterized against stable outputs. The DeepSeek stable mean D of 0.0117 and Llama
   stable mean D of 0.0250 were scored by DeepSeek, not Gemini. A Gemini-scored stable
   baseline is required before the Gemini score can be properly normalized.

3. **Scale difference is unresolved.** Gemini scores the same outputs ~1.9× higher than
   DeepSeek. This may reflect a stricter rubric, different tokenization, or different
   interpretation of partial scores. Cross-judge magnitude comparison requires a shared
   baseline condition.

4. **Attribution is weaker under Gemini.** Match rate of 0.08 is below the 0.6 threshold
   and lower than DeepSeek (0.32). Constraint-level routing cannot be used for diagnostics
   from either judge, but is especially unreliable for Gemini.

5. **Prompt set is purpose-built.** All 30 prompts embed structural failure invitations.
   Behavior on naturalistic real-world prompts is untested.

6. **This does not prove production readiness.** Cross-judge directional consistency is
   one piece of evidence. It does not imply the system is ready for deployment or that
   divergence scores are calibrated across different judge models.

---

## Previous Partial Run Note

An earlier Gemini run (2026-04-30, archived as
`real_failure_validation_30_llama_3_1_8b_1repeat_standard_gemini_2_0_flash_judge_2error`)
had 2 errors (429 rate limits on v30_06, v30_22) and was not treated as completed evidence.
This run supersedes it with a clean 30/30 result. The old file is retained in valid_baselines
for audit purposes.

---

## Current Scientific Status

AOSL has now passed an initial cross-judge directional consistency test:
- Two independent judges (DeepSeek and Gemini) both produce elevated Mean D on the same
  Llama pressured outputs.
- Both judges identify C7 and C4 as the primary failure-detecting constraints.
- The ordering stable < pressured is preserved under both judges.

It has not yet passed a cross-judge calibrated-scale test. The magnitude difference
between judges (1.9×) remains unexplained without a shared stable baseline condition.

---

## Next Required Experiments

1. Run a stable Llama baseline scored by google/gemini-2.0-flash-001. This provides the
   reference floor for the Gemini judge and allows a normalized cross-judge comparison.

2. Run Gemini judge with 3 repeats on Llama pressured outputs (or at minimum, confirm
   the 1-repeat signal holds in a second pass).

3. Run Gemini judge on DeepSeek pressured outputs (real_failure_validation_30, DeepSeek
   generator). If Gemini also detects elevated D on DeepSeek generator outputs, the
   cross-judge evidence extends to both generators.

4. Update the cross-generator memo with cross-judge results once a Gemini stable
   baseline is available.

---

```
Version : v0.1
Status  : early directional cross-judge evidence — not final proof
Scope   : one generator, two judges, one pressure prompt set, 1 repeat (Gemini)
Created : 2026-05-02
```
