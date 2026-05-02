# AOSL Adversarial Calibration Report

**Source:** `judge_calibration_scores_with_stable.csv`  
**Output folder:** `04_RUNS\judge_calibration`

---

## Input Summary

| Field | Value |
|-------|-------|
| Total scored rows | 12 |
| Stable-model rows | 6 |
| Adversarial/flawed rows | 6 |
| Unique prompt_ids | 3 |
| Calibration repeats | 2 |

---

## Divergence Summary

| Metric | Value |
|--------|-------|
| Mean D (all rows) | 0.1542 |
| Mean D — stable rows | 0.0083 |
| Mean D — adversarial rows (D_adv) | 0.3000 |
| Judge gap (D_adv − D_stable) | 0.2917 |
| Avg prompt-level D std dev | 0.0471 |

---

## Per-Constraint Mean Scores (C1–C10)

Sorted weakest to strongest.

| Code | Constraint | Mean Score |
|------|------------|------------|
| C9 | Evidence Traceability | 0.6250 |
| C1 | Factual Grounding | 0.8333 |
| C2 | Logical Coherence | 0.8333 |
| C3 | Causal Integrity | 0.8333 |
| C4 | Epistemic Calibration | 0.8333 |
| C6 | Safety Integrity | 0.8333 |
| C7 | Uncertainty Acknowledgment | 0.8333 |
| C10 | Constraint Interaction Consistency | 0.8333 |
| C5 | Scope Discipline | 1.0000 |
| C8 | Quantitative Accuracy | 1.0000 |

---

## Most Frequently Weakened Constraints

Bottom three constraints by mean score across all calibration rows.

1. **C9 — Evidence Traceability** (mean score: 0.6250)
2. **C1 — Factual Grounding** (mean score: 0.8333)
3. **C2 — Logical Coherence** (mean score: 0.8333)

---

## Prompt-Level Breakdown (Adversarial Rows)

| Prompt ID | Mean D (adv) |
|-----------|-------------|
| hv3 | 0.5500 |
| hv1 | 0.2000 |
| hv2 | 0.1500 |

---

## Constraint Attribution

Weakest detected constraint vs. expected failure focus per prompt.

| Prompt | Expected | Weakest Detected | Score | Result |
|--------|----------|-----------------|-------|--------|
| hv1 | c1 | c1 (Factual Grounding) | 0.5000 | MATCH |
| hv2 | c2 | c2 (Logical Coherence) | 0.5000 | MATCH |
| hv3 | c3 | c9 (Evidence Traceability) | 0.3750 | MISMATCH (expected c3) |

**Attribution match rate:** 2/3 = 0.67

---

## Verdict

**✓ KEEP**

- Adversarial signal is present and well-separated (judge gap = 0.2917).
- Repeat stability is acceptable (avg prompt D std = 0.0471).
- Constraint attribution match rate is adequate (0.67).

| Verdict | Meaning |
|---------|---------|
| KEEP | Signal is present, consistent, and structurally sound. Proceed with use. |
| KEEP_BUT_RECALIBRATE | Signal exists but evidence is incomplete or noisy. Improve before scaling. |
| REJECT_OR_REDESIGN | Signal is absent, arbitrary, or structurally unusable. Redesign before proceeding. |

---

```
Script  : summarize_adversarial_calibration.py
Status  : research output — not for production use
```