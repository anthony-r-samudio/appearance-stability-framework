# validation_30 — AOSL 30-Prompt Validation Set

## 1. Purpose

This dataset provides a larger, more diverse evaluation corpus for testing whether AOSL
divergence scoring generalizes beyond the 12-row hard-validation set used in the initial
calibration runs.

The goal is to stress-test the judge across a wider range of constraint types, domain
categories, and failure modes before scaling AOSL to real model outputs.

---

## 2. Why This Exists After the 12-Row Baseline

The archived baseline (`04_RUNS/judge_calibration/valid_baselines/`) confirmed that the
judge can reliably separate stable from flawed outputs (judge gap = 0.2697) and achieves
repeatable scoring (avg repeat std dev = 0.0409). However, 12 rows is a narrow sample:

- One row per constraint (C1–C10), plus 1 stable and 1 mixed
- All from a single domain distribution
- Verdict was `KEEP_BUT_RECALIBRATE` due to attribution match rate of 0.70 and max
  constraint drift of 0.5774

A 30-row set with at least 2 examples per constraint and 10 domain categories provides:

- Better coverage for detecting constraint-specific judge drift
- A more stable estimate of divergence means and standard deviations
- Multiple examples per constraint to test attribution consistency

---

## 3. Dataset Composition

| Category              | Count |
|-----------------------|-------|
| Stable control        | 3     |
| Flawed or mixed       | 27    |
| **Total**             | **30** |

### Constraint coverage

| Focus                          | Count |
|--------------------------------|-------|
| c1_factual_grounding           | 2     |
| c2_logical_contradiction       | 2     |
| c3_causal_leap                 | 3     |
| c4_overconfidence              | 3     |
| c5_scope_creep                 | 2     |
| c6_safety_weakness             | 3     |
| c7_missing_uncertainty         | 3     |
| c8_quantitative_error          | 2     |
| c9_no_evidence                 | 3     |
| c10_interaction_inconsistency  | 2     |
| mixed_subtle_failure           | 2     |
| control_stable                 | 3     |

---

## 4. Domain Categories Covered

- Factual / historical
- Governance / institutional
- Legal / policy
- Medical / safety-adjacent
- Financial / investment
- Technical / programming
- Causal explanation
- Math / quantitative
- Social / advice
- AI evaluation / meta-reasoning

---

## 5. Dry-Run Token Estimate

Before spending any credits, preview the prompt sizes and total token budget:

```
py 05_SRC\experiments\run_judge_calibration.py --dry-run --cost-mode cheap --input-csv 04_RUNS\validation_30\validation_30_inputs.csv
```

---

## 6. Cheap 1-Repeat Validation (Low Cost, Fast)

Run a single pass over all 30 rows at the cheap token preset (300 max response tokens):

```
py 05_SRC\experiments\run_judge_calibration.py --cost-mode cheap --repeats 1 --input-csv 04_RUNS\validation_30\validation_30_inputs.csv
```

This produces one scored row per prompt. Use it to confirm the judge can score all 30
rows without errors and that the constraint attribution looks plausible before committing
to a full 3-repeat run.

---

## 7. Full 3-Repeat Validation

Run three full passes at the standard token preset to measure repeat stability:

```
py 05_SRC\experiments\run_judge_calibration.py --cost-mode standard --repeats 3 --input-csv 04_RUNS\validation_30\validation_30_inputs.csv
```

This produces 90 scored rows total. The summary script will compute per-prompt divergence
std dev, judge gap, attribution match rate, and the strategic verdict.

To resume after an interruption:

```
py 05_SRC\experiments\run_judge_calibration.py --cost-mode standard --repeats 3 --resume --input-csv 04_RUNS\validation_30\validation_30_inputs.csv
```

---

## 8. What Success Would Mean

A successful validation run would show:

- **All 30 × 3 = 90 rows scored** without judge errors
- **avg prompt repeat std dev ≤ 0.10** (judge is repeatable)
- **Judge gap ≥ 0.15** (flawed outputs score measurably worse than controls)
- **Attribution match rate ≥ 0.75** (judge identifies the expected failing constraint
  in at least 75% of flawed rows)
- **Max constraint drift ≤ 0.40** (no single constraint collapses to pure noise)
- **Verdict: KEEP_ADV_JUDGE** or **KEEP_BUT_RECALIBRATE** (not DO_NOT_SCALE_YET)

If these thresholds are met, it provides evidence that AOSL divergence scoring is
consistent and interpretable enough to apply to real model output comparisons.

---

## 9. What This Dataset Does Not Prove

- **Generalization to real model outputs.** All outputs here are hand-crafted synthetics
  with intentional, legible failures. Real outputs will have subtler, compound failures.
- **Judge calibration across models.** Results reflect the specific judge model configured
  in the runner. A different judge may produce different attribution patterns.
- **Constraint weights or relative severity.** This dataset treats all constraints
  equally. AOSL currently uses equal weighting; this dataset does not validate weighted
  scoring.
- **Coverage of all failure subtypes.** Each constraint has 2–3 examples, each drawn
  from a different domain. Some domain × constraint combinations are not represented.

---

## Version

```
Created  : 2026-04-30
Rows     : 30
Columns  : prompt_id, prompt_text, model_name, output_text, temperature, repeat,
           expected_failure_focus
Status   : initial draft — not yet scored
```
