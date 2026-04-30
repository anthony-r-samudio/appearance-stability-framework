# AOSL Validation 30 Closeout v0.1

```
Date              : 2026-04-30
Dataset           : validation_30
Judge             : deepseek/deepseek-chat
Mode              : cheap (max_tokens=300)
Repeats           : 1
Boundary guidance : AOSL_JUDGE_BOUNDARY_COMPACT_v0.1.md
Rows scored       : 30 / 30
Errors            : 0
```

---

## Prior Baseline: 12-Row Hard Validation (3 Repeats)

The first controlled calibration run scored the 12-row hard-validation set three
times each (36 total scored rows) using the same judge and compact boundary guidance.

| Metric                        | Value                  |
|-------------------------------|------------------------|
| Total scored rows             | 36 / 36                |
| Errors                        | 0                      |
| Stable mean D                 | 0.0000  (n=3)          |
| Flawed mean D                 | 0.2633  (n=10)         |
| Mixed mean D                  | 0.3333  (n=1)          |
| Flawed/mixed mean D           | 0.2697  (n=11)         |
| Judge gap                     | 0.2697                 |
| Signal quality                | strong                 |
| Avg prompt repeat std dev     | 0.0409                 |
| Max constraint drift          | 0.5774                 |
| Attribution match rate        | 0.70  (7/10 mapped)    |
| Strategic verdict             | KEEP_BUT_RECALIBRATE   |

The verdict was `KEEP_BUT_RECALIBRATE` because max constraint drift (0.5774) exceeded
the 0.40 threshold, indicating that individual constraint scores were not yet stable
across repeats even though the divergence signal itself was strong and consistent.

---

## Validation 30: 30-Row Set (1 Repeat, Cheap Mode)

The validation_30 set scores 30 synthetic rows covering all 10 AOSL constraints (C1–C10)
with at least 2 examples per constraint, across 10 domain categories. This run used
`--cost-mode cheap` (300 max response tokens) and a single scoring pass.

| Metric                        | Value                  |
|-------------------------------|------------------------|
| Total scored rows             | 30 / 30                |
| Errors                        | 0                      |
| Stable mean D                 | 0.0000  (n=3)          |
| Flawed mean D                 | 0.2260  (n=25)         |
| Mixed mean D                  | 0.2500  (n=2)          |
| Flawed/mixed mean D           | 0.2278  (n=27)         |
| Judge gap                     | 0.2278                 |
| Signal quality                | strong                 |
| Avg prompt repeat std dev     | N/A (1 repeat)         |
| Attribution match rate        | 0.60  (15/25 mapped)   |
| Strategic verdict             | KEEP_ADV_JUDGE         |

The verdict was `KEEP_ADV_JUDGE` because the judge gap exceeded the 0.10 minimum,
repeat variance was within limits (N/A on 1 repeat, trivially 0.0000), and attribution
match rate met the 0.60 floor exactly.

---

## What This Shows

AOSL divergence scoring has now reproduced a stable-vs-flawed separation across two
controlled synthetic validation sets. The judge consistently assigns near-zero divergence
to stable outputs and meaningfully higher divergence to flawed or mixed outputs, with a
gap of 0.2278–0.2697 across both runs. This result holds across 10 constraint types and
10 domain categories.

---

## What This Does Not Yet Prove

- It does not prove generalization to real model outputs. Both validation sets are
  hand-crafted synthetics with intentional, legible failures. Real outputs will contain
  subtler, compound failures that may not produce clean divergence signals.

- It does not prove judge independence. Both baselines use the same judge model
  (deepseek/deepseek-chat). A second judge model has not been tested.

- It does not prove exact constraint attribution reliability. Attribution match rate
  is 0.60–0.70, which means the judge correctly identifies the primary failing constraint
  in roughly 3 out of 5 cases, not reliably across all constraints.

- It does not prove production readiness. Scoring latency, cost per row, and behavior
  under real input diversity have not been characterized.

---

## Main Finding

The divergence score is currently stronger than exact constraint attribution.

The judge reliably separates stable outputs from flawed ones at the aggregate level
(judge gap ~0.23–0.27). However, it frequently misattributes which specific constraint
is failing, particularly across the C3/C4/C7 cluster and the C9/C10 boundary pairs.
AOSL can be used as a divergence detector with reasonable confidence, but constraint-level
attribution should not yet be treated as reliable for individual scoring decisions.

---

## Weaknesses Observed

**C3 / C4 / C7 boundary ambiguity**
These three constraints overlap in practice. Outputs that express unwarranted certainty
(C7) or miscalibrate confidence (C4) often contain an implicit causal claim (C3), causing
the judge to pick the wrong primary failure. In validation_30, C7 examples were
misattributed to C3 or C4 in 3 of 3 cases.

**C9 absorbed by C1, C3, or C4**
Evidence traceability failures (C9) are frequently absorbed by adjacent constraints.
When an output presents a false or contested claim without sourcing, the judge tends to
penalize the content error (C1, C3) or the confidence posture (C4) rather than the
missing evidence basis (C9). In validation_30, 2 of 3 C9 examples were misattributed.

**C10 absorbed by C2**
Constraint Interaction Consistency failures (C10) are structurally similar to logical
contradictions (C2). When an output contains two incompatible prescriptions, the judge
tends to score it as a direct contradiction (C2) rather than as an architectural tension
between constraints (C10). Both C10 examples in validation_30 were scored as C2.

**1-repeat validation cannot measure repeat stability**
The cheap baseline (1 repeat) cannot produce prompt-level standard deviations. The
KEEP_ADV_JUDGE verdict is therefore based on a trivially zero std dev. Repeat stability
for validation_30 remains unmeasured until a 3-repeat run is completed.

---

## Strategic Verdict

| Use case                         | Verdict                |
|----------------------------------|------------------------|
| Divergence detection             | KEEP_ADV_JUDGE         |
| Exact constraint attribution     | KEEP_BUT_RECALIBRATE   |

Use AOSL divergence scoring to detect whether an output is flawed relative to a stable
reference. Do not rely on individual constraint scores for final attribution decisions
until a 3-repeat run on validation_30 confirms constraint-level stability.

---

## Next Phase

1. **Run validation_30 with 3 repeats** after budget review. This is the minimum
   required to measure prompt-level repeat std dev and confirm that the KEEP_ADV_JUDGE
   verdict holds under repeated scoring.

2. **Add a real model output validation set.** Replace at least a subset of synthetic
   examples with outputs generated by a live model responding to the same prompts. This
   is the only way to test whether AOSL divergence generalizes beyond synthetic inputs.

3. **Compare at least one second judge model.** Run the same validation_30 inputs
   through a second judge (e.g., a different provider or model size) and compare judge
   gap, attribution match rate, and repeat stability. Judge-independence is a prerequisite
   for treating AOSL as a model-agnostic scoring layer.

4. **Preserve AOSL as model-agnostic.** Do not embed judge-specific assumptions into
   scoring code, constraint definitions, or boundary notes. All tuning decisions should
   remain in the boundary guidance files, not in the rubric or the constraint schema.

---

```
Version : v0.1
Status  : milestone closeout — not a final evaluation
Scope   : synthetic validation only
```
