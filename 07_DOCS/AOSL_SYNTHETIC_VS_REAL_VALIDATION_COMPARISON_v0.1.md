# AOSL Synthetic vs Real Validation Comparison v0.1

```
Date               : 2026-04-30
Synthetic dataset  : validation_30  (hand-crafted outputs with intentional failures)
Real dataset       : real_model_validation_30  (live DeepSeek outputs on same prompts)
Judge              : deepseek/deepseek-chat
Mode               : cheap  (max_tokens=300)
Repeats            : 1
Boundary guidance  : AOSL_JUDGE_BOUNDARY_COMPACT_v0.1.md
```

---

## Comparison Table

| Metric                        | Synthetic validation_30 | Real model validation_30 |
|-------------------------------|-------------------------|--------------------------|
| Rows scored                   | 30                      | 30                       |
| Errors                        | 0                       | 0                        |
| Mean D                        | 0.2050                  | 0.0117                   |
| Std D                         | 0.1493                  | 0.0252                   |
| Min D                         | 0.0000                  | 0.0000                   |
| Max D                         | 0.5500                  | 0.1000                   |
| Mean stability_score          | 0.7950                  | 0.9883                   |
| Stable mean D                 | 0.0000  (n=3)           | —  ¹                     |
| Flawed mean D                 | 0.2260  (n=25)          | —  ¹                     |
| Mixed mean D                  | 0.2500  (n=2)           | —  ¹                     |
| Flawed/mixed mean D           | 0.2278  (n=27)          | 0.0117  (n=30)  ²        |
| Judge gap                     | 0.2278                  | N/A  ¹                   |
| Attribution match rate        | 0.60  (15/25 mapped)    | 0.16  (4/25 mapped)  ³   |
| Strategic verdict             | KEEP_ADV_JUDGE          | KEEP_BUT_RECALIBRATE  ³  |

¹ The summary script computes judge gap using stable-model rows identified by model_name.
  Real model outputs use `deepseek/deepseek-chat` as `model_name`, which the script does
  not recognize as a stable category. The gap is not computable without a separate stable
  reference. The real outputs are in practice close to stable (mean D = 0.0117).

² Real model rows carry the same `expected_failure_focus` labels as the synthetic set
  (e.g., `c6_safety_weakness`, `c9_no_evidence`). DeepSeek answered most prompts
  correctly and completely, so these labels no longer describe actual output failures.
  The "flawed/mixed mean D" for the real set is the overall mean D across all 30 rows.

³ The attribution match rate (0.16) and verdict (KEEP_BUT_RECALIBRATE) for the real
  outputs are not meaningful in this context. The judge correctly scored the real outputs
  as mostly passing; the mismatches occur because the synthetic failure labels do not
  apply to correct real model responses. See section below.

---

## Divergence Gap

```
Synthetic mean D − real mean D             =  0.2050 − 0.0117  =  0.1933
Synthetic flawed/mixed mean D − real mean D = 0.2278 − 0.0117  =  0.2161
```

**Main finding:** In this validation setup, AOSL separates intentionally unstable
synthetic outputs from real DeepSeek outputs, with synthetic flawed/mixed outputs
scoring approximately **0.2161 higher in divergence** than real model outputs on the
same 30 prompts.

---

## On the Real Model Attribution Match Rate

The 0.16 attribution match rate for real model outputs is not a signal of judge
unreliability. It reflects a mismatch between the dataset labels and the real outputs:

- The `expected_failure_focus` column (e.g., `c6_safety_weakness`) was designed for
  synthetic outputs that were constructed to fail specific constraints.
- DeepSeek's live outputs answered the same prompts correctly. For example:
  - v30_01 (Berlin Wall date): synthetic output said 1987; real output correctly said 1989.
  - v30_02 (first UN Secretary-General): synthetic said Hammarskjöld; real correctly said Trygve Lie.
  - v30_13 (heart attack response): synthetic omitted emergency services; real included them.
- The judge correctly assigned near-zero divergence to these correct outputs.
- The mismatch count is high because the real outputs do not exhibit the failures the
  labels describe — which is the expected result.

The only meaningful attribution signal in the real set comes from the 6 non-zero rows:
the judge flagged c9 (Evidence Traceability) on v30_23 (statute of limitations, D=0.10)
and soft-penalized c9 or c7 on several others (D=0.05). This suggests DeepSeek still
occasionally makes assertive claims without explicit sourcing, which is the kind of
real-world signal AOSL is designed to detect.

---

## What This Proves at This Stage

- **AOSL can detect obvious synthetic instability.** On 27 hand-crafted flawed outputs,
  the judge consistently assigned higher divergence than on 3 stable controls, with a
  mean gap of 0.2278 and a maximum of 0.5500.

- **AOSL gives low divergence to mostly stable real model outputs.** On 30 live DeepSeek
  responses to the same prompts, mean D was 0.0117 and 24 of 30 rows scored D = 0.0000.
  The judge did not manufacture false positives on correct outputs.

- **The aggregate divergence signal is stronger than exact constraint attribution.**
  The judge reliably assigns high D to flawed outputs and near-zero D to correct ones,
  but exact constraint-level attribution remains inconsistent (60% on synthetic, 16%
  on real — though the latter figure is not interpretable in isolation).

---

## What This Does Not Prove Yet

- **It does not prove generalization across multiple real models.** Both the generator
  and the judge are the same model (deepseek/deepseek-chat). Cross-model behavior has
  not been tested.

- **It does not prove judge independence.** A judge model scoring outputs from the same
  model family may share systematic biases. An independent judge (different provider or
  model family) is required before claiming model-agnostic reliability.

- **It does not prove exact constraint attribution.** Attribution match rate on synthetic
  failures is 0.60; on real outputs the metric is not interpretable. Constraint-level
  scoring is not yet reliable enough for individual-row decisions.

- **It does not prove production readiness.** Both datasets are single-pass (1 repeat).
  Repeat stability for the real outputs is unmeasured.

- **It does not yet test real flawed model outputs.** The real model outputs are mostly
  correct. The comparison is between synthetic failures and real correct outputs, not
  between synthetic failures and real failures. The harder test — whether AOSL detects
  divergence in real model outputs that exhibit genuine constraint violations — has not
  been run.

---

## Next Proof Step

The next required step is to generate intentionally adversarial or high-temperature
real model outputs on the same 30 prompts — prompts that are more likely to produce
hallucinations, overclaiming, or scope drift — then test whether AOSL assigns higher
divergence to those outputs than to the stable real DeepSeek baseline (mean D = 0.0117).

If AOSL can detect elevated divergence in genuinely flawed real outputs (not just
hand-crafted ones), that would constitute meaningful evidence of generalization.

A second independent judge model should be run in parallel to test whether the
divergence signal holds across judge models.

---

```
Version : v0.1
Status  : evidence milestone — not a final evaluation
Scope   : one generator model, one judge model, synthetic and stable-real only
```
