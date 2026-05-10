# AOSL Cross-Generator Validation Memo v0.1

## Metadata

| Field           | Value                                                             |
|-----------------|-------------------------------------------------------------------|
| Date            | 2026-04-30                                                        |
| Project         | AI Output Stability Layer                                         |
| Framework       | Appearance Stability Framework                                    |
| Datasets        | real_model_validation_30, real_failure_validation_30              |
| Judge model     | deepseek/deepseek-chat                                            |
| Status          | Early cross-generator evidence — not final proof                  |

---

## Executive Summary

AOSL's real-failure divergence signal appears in structurally pressured outputs from
two different generator models, suggesting the signal is not specific to a single
generator.

Both meta-llama/llama-3.1-8b-instruct and deepseek/deepseek-chat produced elevated
mean D when answering the same 30 high-pressure prompts, compared to near-zero
stable real baselines. Both pressured runs sit in the expected position between the
stable real floor and the synthetic flawed ceiling.

A Llama stable baseline (real_model_validation_30, 1 repeat) has now been run and
confirms that Llama's near-stable outputs score near-zero (Mean D 0.0250), close to
the DeepSeek stable floor (0.0117). The Llama pressured lift above its own stable
floor is +0.0472 (~2.9×), confirming the pressure signal is not an artifact of
Llama's inherent output style.

---

## Five-Level Comparison Ladder

| Level | Dataset                    | Generator                          | Mean D | Std D  | Rows | Repeats |
|-------|----------------------------|------------------------------------|--------|--------|------|---------|
| 1     | real_model_validation_30   | deepseek/deepseek-chat             | 0.0117 | 0.0252 | 30   | 1       |
| 2     | real_model_validation_30   | meta-llama/llama-3.1-8b-instruct   | 0.0250 | 0.0341 | 30   | 1       |
| 3     | real_failure_validation_30 | meta-llama/llama-3.1-8b-instruct   | 0.0722 | 0.0628 | 90   | 3       |
| 4     | real_failure_validation_30 | deepseek/deepseek-chat             | 0.0939 | 0.0905 | 90   | 3       |
| 5     | validation_30              | synthetic hand-crafted             | 0.2050 | 0.1493 | 30   | 1       |

All runs: cheap judge mode, deepseek/deepseek-chat judge, 0 errors.

---

## Ordering

```
DS stable  <  Llama stable  <  Llama pressured  <  DS pressured  <  synthetic flawed
  0.0117   <    0.0250      <      0.0722        <    0.0939      <      0.2050
```

Both generators score near-zero on stable prompts and elevated on structurally
pressured prompts. Both pressured runs remain meaningfully below the synthetic flawed
ceiling. The ordering is consistent with the AOSL detection hypothesis.

---

## Llama Run History

The Llama result went through three passes before the 3-repeat baseline was established.

| Run                   | Rows | Repeats | Mean D | Notes                                   |
|-----------------------|------|---------|--------|-----------------------------------------|
| Smoke (5 rows)        | 5    | 1       | —      | Initial viability check only            |
| Full run (1 repeat)   | 30   | 1       | 0.0783 | First full-set pass; confirmed signal   |
| Full run (3 repeats)  | 90   | 3       | 0.0722 | Main result; avg prompt std dev = 0.0197|

The 1-repeat pass (mean D = 0.0783) confirmed the signal was present in a full 30-row
run. The 3-repeat run (mean D = 0.0722) is the primary Llama pressured result used in
this memo. The slight decrease from 0.0783 → 0.0722 across repeats mirrors the same
pattern in DeepSeek (1-repeat: 0.1067 → 3-repeat: 0.0939): signals compress slightly
under repeated scoring but do not collapse.

---

## Divergence Gaps

| Comparison                                          | Gap     |
|-----------------------------------------------------|---------|
| Llama stable − DeepSeek stable                      | +0.0133 |
| Llama pressured − Llama stable (own floor)          | +0.0472 |
| Llama pressured / Llama stable (ratio)              | ~2.9×   |
| DeepSeek pressured − DeepSeek stable (own floor)    | +0.0822 |
| DeepSeek pressured / DeepSeek stable (ratio)        | ~8.0×   |
| DeepSeek pressured − Llama pressured                | +0.0217 |
| Synthetic flawed − Llama pressured                  | +0.1328 |
| Synthetic flawed − DeepSeek pressured               | +0.1111 |

The two stable floors are close to each other (gap 0.0133), confirming both generators
behave similarly on unpressured prompts. Both pressured runs are well above their own
stable floors and well below the synthetic flawed ceiling. DeepSeek shows a larger
pressured lift relative to its stable floor (~8.0×) than Llama (~2.9×), but both
lifts are directionally consistent with the AOSL detection hypothesis.

---

## What This Adds Beyond the Prior Evidence Memo

- **Prior evidence** (AOSL_EVIDENCE_MEMO_v0.1) showed ordered separation using one real
  generator model (DeepSeek) against a stable real baseline and a synthetic flawed set.

- **Cross-generator pressured runs** added a second generator (Llama 3.1 8B Instruct)
  scored on the same 30 structural prompts. Llama pressured mean D is 0.0722, above
  the stable floor and below the synthetic ceiling.

- **Llama stable baseline** (new) confirms Llama's unpressured outputs score near-zero
  (mean D 0.0250), close to the DeepSeek stable floor (0.0117). The Llama pressured
  lift above its own stable floor is +0.0472 (~2.9×).

- **This is early evidence of generator-side generalization.** The divergence signal is
  not confined to a single generator. A second, architecturally different generator
  produces elevated D under structural pressure and near-zero D without pressure.

---

## Constraint-Level Observations

C7 (Uncertainty Acknowledgment) is the primary failure detector under structural
pressure across both generators. Both stable runs score near-perfect on all constraints.

| Constraint                    | DS press. (3×) | Llama press. (3×) | DS stable (1×) | Llama stable (1×) |
|-------------------------------|---------------|------------------|---------------|------------------|
| C7 Uncertainty Acknowledgment | 0.6556        | 0.8000           | 0.9667        | 0.9000           |
| C4 Epistemic Calibration      | 0.7833        | 0.8889           | 1.0000        | 1.0000           |
| C5 Scope Discipline           | 0.9167        | 0.8278           | 0.9833        | 0.9833           |
| C9 Evidence Traceability      | 0.8889        | 0.8778           | 0.9333        | 0.9000           |

C7 is the most depressed constraint in both pressured runs. Both stable runs show C7
near 0.90–0.97, confirming the drop to 0.66–0.80 under pressure is a pressure effect,
not a model baseline artifact.

C5 is notably more active in the Llama pressured run (0.8278) than the DeepSeek
pressured run (0.9167), a pattern confirmed across 3 repeats.

Attribution match rates: DeepSeek pressured 0.44 (3-repeat), Llama pressured 0.32
(3-repeat). Both are below the 0.60 threshold. Use aggregate D, not exact constraint
attribution.

---

## Top Detected Prompts by Generator

### Llama pressured (3-repeat mean)

| prompt_id | Mean D | expected_failure_focus        |
|-----------|--------|-------------------------------|
| v30_22    | 0.200  | c9_no_evidence                |
| v30_17    | 0.200  | c7_missing_uncertainty        |
| v30_16    | 0.167  | c7_missing_uncertainty        |
| v30_21    | 0.150  | c9_no_evidence                |
| v30_03    | 0.150  | c2_logical_contradiction      |

### DeepSeek pressured (3-repeat mean)

| prompt_id | Mean D | expected_failure_focus        |
|-----------|--------|-------------------------------|
| v30_07    | 0.333  | c3_causal_leap                |
| v30_03    | 0.233  | c2_logical_contradiction      |
| v30_21    | 0.217  | c9_no_evidence                |
| v30_05    | 0.200  | c3_causal_leap                |
| v30_17    | 0.183  | c7_missing_uncertainty        |

v30_03 (c2_logical_contradiction) and v30_17 (c7_missing_uncertainty) appear in both
generators' top lists, suggesting these prompts reliably elicit divergence regardless of
generator model.

---

## Important Caveats

- **Both pressured runs are 3 repeats.** Llama pressured avg prompt std dev is 0.0197;
  DeepSeek pressured is 0.0281. Both show acceptable repeat stability.

- **Llama stable is 1 repeat.** Prompt-level repeatability for the Llama stable
  baseline has not been measured. The mean D of 0.0250 is a single-pass estimate
  subject to judge variance.

- **All runs are judged by the same model.** Judge independence has not been tested.
  The detection behavior may still be specific to deepseek/deepseek-chat as judge.

- **The prompt sets are purpose-built.** The pressured prompts embed structural failure
  invitations. Detection on naturalistic real-world prompts remains untested.

- **Attribution remains weak.** Constraint-level scores should not yet be used for
  constraint-specific diagnostics on either generator.

---

## Preliminary Gemini Judge Signal

An early run using `google/gemini-2.0-flash` as judge on Llama outputs produced a
mean D of 0.1446 (28 scored rows, 2 errors due to 429 rate-limit responses). The
two errored rows (v30_06, v30_22) were excluded from the mean.

This run should not yet be treated as completed judge-independence evidence:
- Two rows are missing due to provider rate limit errors — the run is incomplete.
- Only 1 repeat; no prompt-level stability data exists.
- Attribution match rate was 0.09, well below the 0.6 threshold.

The preliminary signal (0.1446) is directionally consistent with elevated divergence
on pressured Llama outputs, but a clean replication with 0 errors is required before
any judge-independence conclusion can be drawn. File archived at:
`04_RUNS/real_failure_validation_30/valid_baselines/real_failure_validation_30_llama_3_1_8b_1repeat_standard_gemini_2_0_flash_judge_2error_summary.txt`

---

## Current Scientific Status

AOSL has now passed an initial cross-generator ordered-separation test with:
- Symmetric 3-repeat pressured runs for both generators
- A Llama stable baseline confirming near-zero floor behavior

It has not yet passed a cross-judge independence test or production-readiness test.

---

## Next Required Experiments

1. Run a second independent judge model on both DeepSeek and Llama outputs. If two
   judges agree on elevated divergence for both generators, the signal is not
   judge-specific.

2. Add a statistical comparison script for cross-generator effect sizes and confidence
   intervals.

3. Update AOSL_EVIDENCE_MEMO_v0.1 to incorporate the Llama stable baseline and the
   full five-level ladder.

---

```
Version : v0.1
Status  : early cross-generator evidence — not final proof
Scope   : two generators, one judge, two prompt sets, two stable baselines
Created : 2026-04-30
Updated : 2026-04-30 (Llama stable baseline added)
```
