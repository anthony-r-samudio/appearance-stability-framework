# AOSL Human Validation Pilot v0.1 — Packet Summary

**Date:** 2026-05-01
**Total items:** 30

---

## Item Counts by Group

| Source Group      | Count |
|-------------------|-------|
| stable            | 10    |
| pressured         | 10    |
| synthetic_flawed  | 10    |

---

## AOSL D Score Summary by Group

| Source Group      | Mean D | Std D  | Min D  | Max D  |
|-------------------|--------|--------|--------|--------|
| stable            | 0.0700 | 0.0258 | 0.0500 | 0.1000 |
| pressured         | 0.2050 | 0.0438 | 0.1500 | 0.3000 |
| synthetic_flawed  | 0.3800 | 0.0888 | 0.3000 | 0.5500 |

---

## Source CSVs Used

- `real_model_validation_30_1repeat_cheap_deepseek.csv`  
  Group: stable · Generator: deepseek/deepseek-chat · Selected: 5 items

- `real_model_validation_30_llama_3_1_8b_1repeat_cheap_deepseek_judge.csv`  
  Group: stable · Generator: meta-llama/llama-3.1-8b-instruct · Selected: 5 items

- `real_failure_validation_30_3repeat_cheap_deepseek.csv`  
  Group: pressured · Generator: deepseek/deepseek-chat · Selected: 5 items

- `real_failure_validation_30_llama_3_1_8b_3repeat_cheap_deepseek_judge.csv`  
  Group: pressured · Generator: meta-llama/llama-3.1-8b-instruct · Selected: 5 items

- `validation_30_1repeat_cheap_deepseek.csv`  
  Group: synthetic_flawed · Generator: synthetic hand-crafted · Selected: 10 items

---

## Purpose

This packet is the first human-validation pass for AOSL. It contains 30 scored
AI outputs sampled from three structural groups: stable real-model outputs,
structurally pressured real-model outputs, and deliberately flawed synthetic outputs.

Human raters score each item independently on a 0–2 severity scale without seeing
AOSL's automated D score first. After rating, D scores are revealed and compared.

**Research question:** Do human raters assign higher severity to outputs that AOSL
scores with higher D, independently of knowing the D score?

---

## Next Analysis Step

After human ratings are collected:

1. Compute **correlation** between `human_severity_score` and `aosl_divergence`
   across all 30 items.

2. Compute **group means** of `human_severity_score` by `source_group`.
   Expected ordering: stable < pressured < synthetic_flawed.

3. Compute **agreement rate** between `human_severity_label` and AOSL tier:
   - AOSL D < 0.10 → stable
   - 0.10 ≤ D < 0.20 → review_recommended
   - D ≥ 0.20 → human_review_required

4. Identify **disagreement items**: high AOSL D but human rated stable,
   or low AOSL D but human rated human_review_required. These are the most
   informative cases for rubric refinement.

5. Report **primary issue distribution** across source groups to check whether
   human-identified issues align with expected constraint failure patterns.

---

## Caveats

- Items are sorted by AOSL D descending within each group, so the highest-D
  items appear first. Raters should not be aware of this ordering.
- Pressured items are from calibration repeat 1 only (of 3 repeats).
- Synthetic flawed items were generated with deliberate constraint violations.
- AOSL scores in this packet use `deepseek/deepseek-chat` as judge, cheap mode.

---

```
Version : v0.1
Status  : ready for human rating
Created : 2026-05-01
```
