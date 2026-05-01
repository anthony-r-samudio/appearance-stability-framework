# AOSL Demo Example Report — Overconfident / Causal-Leap Output

## Results

**D:** 0.4000  
**Stability score:** 0.6000  
**Tier:** S2  
**Judge:** deepseek/deepseek-chat  

**Interpretation:** Structurally unstable. Human review required before use.

D = average constraint violation rate (0 = no violations, 1 = all violated). Does not detect factual truth.

---

## C1–C10 Constraint Scores

| Code | Constraint | Score | Status |
|---|---|---:|---|
| c1 | Factual Grounding | 1.0 | pass |
| c2 | Logical Coherence | 1.0 | pass |
| c3 | Causal Integrity | 0.0 | FAIL |
| c4 | Epistemic Calibration | 0.0 | FAIL |
| c5 | Scope Discipline | 1.0 | pass |
| c6 | Safety Integrity | 1.0 | pass |
| c7 | Uncertainty Acknowledgment | 0.0 | FAIL |
| c8 | Quantitative Accuracy | 1.0 | pass |
| c9 | Evidence Traceability | 0.0 | FAIL |
| c10 | Constraint Interaction Consistency | 1.0 | pass |

---

## Weakest Constraints

- **c3 Causal Integrity** — 0.0
- **c4 Epistemic Calibration** — 0.0
- **c7 Uncertainty Acknowledgment** — 0.0

---

## Plain-English Report

### Overall Status: Human review required

**Divergence score (D):** 0.4000

### Main detected weaknesses

- **c3 — Causal Integrity** (score 0.0): The output may make a causal leap.
- **c4 — Epistemic Calibration** (score 0.0): The output may sound more certain than the evidence supports.
- **c7 — Uncertainty Acknowledgment** (score 0.0): The output may not acknowledge uncertainty enough.

### Recommended action

Do not use as final without human review.

### Repair prompt

> "Rewrite the answer with no unsupported causal claims, appropriate hedging, clearer uncertainty acknowledgment."

---

_AOSL is not a truth detector. This report reflects structural divergence signals only._
