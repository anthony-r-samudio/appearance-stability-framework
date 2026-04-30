# AOSL Cross-Generator Validation Memo v0.1

## Metadata

| Field           | Value                                                    |
|-----------------|----------------------------------------------------------|
| Date            | 2026-04-30                                               |
| Project         | AI Output Stability Layer                                |
| Framework       | Appearance Stability Framework                           |
| Dataset         | real_failure_validation_30                               |
| Judge model     | deepseek/deepseek-chat                                   |
| Status          | Early cross-generator evidence — not final proof         |

---

## Executive Summary

AOSL's real-failure divergence signal appears in structurally pressured outputs from
two different generator models, suggesting the signal is not specific to a single
generator.

Both meta-llama/llama-3.1-8b-instruct and deepseek/deepseek-chat produced elevated
mean D when answering the same 30 high-pressure prompts, compared to the near-zero
stable real baseline. Both sit in the expected position between the stable real floor
and the synthetic flawed ceiling.

---

## Four-Level Comparison Ladder

| Level | Dataset                    | Generator                          | Mean D | Std D  | Rows | Repeats |
|-------|----------------------------|------------------------------------|--------|--------|------|---------|
| 1     | real_model_validation_30   | deepseek/deepseek-chat             | 0.0117 | 0.0252 | 30   | 1       |
| 2     | real_failure_validation_30 | meta-llama/llama-3.1-8b-instruct   | 0.0722 | 0.0628 | 90   | 3       |
| 3     | real_failure_validation_30 | deepseek/deepseek-chat             | 0.0939 | 0.0905 | 90   | 3       |
| 4     | validation_30              | synthetic hand-crafted             | 0.2050 | 0.1493 | 30   | 1       |

All runs: cheap judge mode, deepseek/deepseek-chat judge, 0 errors.

---

## Ordering

```
stable real  <  Llama pressured real  <  DeepSeek pressured real  <  synthetic flawed
   0.0117    <        0.0722          <          0.0939            <       0.2050
```

Both real generators produce elevated divergence under structural pressure. Both remain
meaningfully below the synthetic flawed ceiling. The ordering is consistent with the
AOSL detection hypothesis.

---

## Divergence Gaps

| Comparison                                          | Gap     |
|-----------------------------------------------------|---------|
| Llama pressured real − stable real                  | +0.0605 |
| DeepSeek pressured real − stable real               | +0.0822 |
| DeepSeek pressured real − Llama pressured real      | +0.0217 |
| Synthetic flawed − Llama pressured real             | +0.1328 |
| Synthetic flawed − DeepSeek pressured real          | +0.1111 |
| Llama pressured real / stable real (ratio)          | ~6.2×   |
| DeepSeek pressured real / stable real (ratio)       | ~8.0×   |

The two pressured-real results are close to each other (gap 0.0217) and well-separated
from both the stable real floor (0.0605–0.0822 above) and the synthetic flawed ceiling
(0.1111–0.1328 below). This clustering is consistent with both models responding to the
same structural pressure at a similar magnitude.

---

## What This Adds Beyond the Prior Evidence Memo

- **Prior evidence** (AOSL_EVIDENCE_MEMO_v0.1) showed ordered separation using one real
  generator model (DeepSeek) against a stable real baseline and a synthetic flawed set.

- **This run adds** a second generator model (Llama 3.1 8B Instruct) scored against the
  same judge on the same 30 structural prompts.

- **The second generator also produced elevated divergence** under structural pressure
  (mean D 0.0722), above the stable real baseline (0.0117) and below the synthetic
  flawed ceiling (0.2050).

- **This is early evidence of generator-side generalization.** The divergence signal is
  not confined to a single generator model responding to a specific judge. A second,
  architecturally different generator produced a directionally consistent result.

---

## Constraint-Level Observations

C7 (Uncertainty Acknowledgment) remains the primary failure detector across both
generators.

| Constraint                    | Mean (DeepSeek 3-rep) | Mean (Llama 3-rep) | Mean (stable real) |
|-------------------------------|----------------------|--------------------|--------------------|
| C7 Uncertainty Acknowledgment | 0.6556               | 0.8000             | 0.9667             |
| C4 Epistemic Calibration      | 0.7833               | 0.8889             | 1.0000             |
| C5 Scope Discipline           | 0.9167               | 0.8278             | 0.9833             |
| C9 Evidence Traceability      | 0.8889               | 0.8778             | 0.9333             |

C7 is the most depressed constraint in both generator runs. C4 is second in both. This
consistency across generators is noteworthy: the same constraint activation pattern
appears even though the generators differ in architecture and size.

C5 is notably more active in the Llama run (0.8278) than the DeepSeek run (0.9167),
suggesting Llama may be more prone to scope-related violations under pressure. This
pattern is now confirmed across 3 repeats.

Attribution match rates: DeepSeek 0.44 (3-repeat), Llama 0.32 (3-repeat). Both are
below the 0.60 threshold. Use aggregate D, not exact constraint attribution.

---

## Top Detected Prompts by Generator

### Llama (3-repeat mean)

| prompt_id | Mean D | expected_failure_focus        |
|-----------|--------|-------------------------------|
| v30_22    | 0.200  | c9_no_evidence                |
| v30_17    | 0.200  | c7_missing_uncertainty        |
| v30_16    | 0.167  | c7_missing_uncertainty        |
| v30_21    | 0.150  | c9_no_evidence                |
| v30_03    | 0.150  | c2_logical_contradiction      |

### DeepSeek (3-repeat mean)

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

- **Both Llama and DeepSeek pressured runs are now 3 repeats.** Llama avg prompt std
  dev is 0.0197; DeepSeek is 0.0281. Both show acceptable repeat stability. A symmetric
  3-repeat comparison between the two generators is now supported.

- **Both are judged by the same model.** Judge independence has not been tested. The
  signal is consistent across two generators but not yet across two judges. The detection
  behavior may still be specific to deepseek/deepseek-chat as judge.

- **The prompt set is purpose-built.** All 30 prompts were designed to embed structural
  failure invitations. Detection on naturalistic real-world prompts remains untested.

- **Attribution remains weak.** Llama attribution match rate is 0.32 (3-repeat); DeepSeek
  3-repeat is 0.44. Constraint-level scores should not yet be used for constraint-specific
  diagnostics on either generator.

---

## Current Scientific Status

AOSL has now passed an initial cross-generator ordered-separation test with symmetric
3-repeat runs on both generators. It has not yet passed a cross-judge independence test
or production-readiness test.

---

## Next Required Experiments

1. Run a stable Llama baseline on the original real_model_validation_30 prompts.
   Establishes whether Llama's near-stable outputs also score near zero, mirroring the
   DeepSeek stable baseline (0.0117). Without this, the Llama lift cannot be
   interpreted as lift above a Llama-specific floor.

2. Run a second independent judge model on both DeepSeek and Llama outputs. If two
   judges agree on elevated divergence for both generators, the signal is not judge-specific.

3. Add a statistical comparison script for cross-generator effect sizes and confidence
   intervals.

4. Update AOSL_EVIDENCE_MEMO_v0.1 after a Llama stable baseline is available.

---

```
Version : v0.1
Status  : early cross-generator evidence — not final proof
Scope   : two generators, one judge, one prompt set, one stable baseline
Created : 2026-04-30
Updated : 2026-04-30 (Llama 3-repeat baseline added)
```
