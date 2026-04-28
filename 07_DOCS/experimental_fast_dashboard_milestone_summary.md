# Experimental Fast Dashboard — Milestone Summary

**Branch:** `experimental-fast-batch-scoring`
**Latest tag:** `aosl-fast-dashboard-v0.8`

---

## Purpose

Build a fast scoring and dashboard loop for AOSL: generate or load model outputs, score them against c1–c10 constraints via OpenRouter, compute divergence metrics, and view results interactively in a Streamlit dashboard.

---

## Milestones

| Tag | Description |
|-----|-------------|
| v0.1 | AOSL Stability Dashboard created (`05_SRC/apps/aosl_stability_dashboard.py`) — loads CSV/JSONL run outputs, filters by model/prompt/temperature/tier, displays constraint scores and divergence metrics, exports filtered CSV |
| v0.2 | Validation data generator (`validate_fast_batch_dashboard_input.py`) — 8 hardcoded records across all four stability tiers, confirms dashboard loads correctly without API calls |
| v0.3 | Dashboard auto-scans `04_RUNS/dashboard_validation/`; replaced deprecated `use_container_width=True` with `width="stretch"` on all dataframe calls |
| v0.4 | Real OpenRouter validation runner (`run_real_openrouter_validation.py`) — 3 prompts × 1 model × 1 temperature, writes dashboard-compatible JSONL + CSV |
| v0.5 | Dashboard auto-scans `04_RUNS/real_openrouter_validation/` |
| v0.6 | OpenRouter small comparison runner (`run_openrouter_small_comparison.py`) — 5 prompts × 2 generator models × 2 temperatures × 1 repeat = 20 scored records |
| v0.7 | Dashboard auto-scans `04_RUNS/openrouter_small_comparison/` |
| v0.8 | Small comparison summary script (`summarize_openrouter_small_comparison.py`) — prints and writes structured text summary of the 20-record run |

---

## Current Result — 20-Record OpenRouter Small Comparison

**Run config:** 5 prompts × 2 models (`deepseek/deepseek-chat`, `openrouter/free`) × 2 temperatures (0.3, 0.9) × 1 repeat

### Row counts

| Metric | Value |
|--------|-------|
| Total rows | 20 |
| Successful rows | 20 |
| Error rows | 0 |

### Divergence averages

| Metric | Value |
|--------|-------|
| Average D | 0.7850 |
| Average D_norm | 0.0785 |

### Stability tier distribution

| Tier | Count |
|------|-------|
| S0 | 11 |
| S1 | 9 |
| S2 | 0 |
| S3 | 0 |

### Average D by generator model

| Model | Avg D |
|-------|-------|
| deepseek/deepseek-chat | 0.8150 |
| openrouter/free | 0.7550 |

### Average D by temperature

| Temperature | Avg D |
|-------------|-------|
| 0.3 | 0.6300 |
| 0.9 | 0.9400 |

### Average D by prompt

| Prompt | Avg D |
|--------|-------|
| cmp_p1 (iron melting point) | 0.2250 |
| cmp_p2 (whale syllogism) | 0.0250 |
| cmp_p3 (sugar and diabetes) | 1.3750 |
| cmp_p4 (Moon base confidence) | 1.8250 |
| cmp_p5 (2100 temperature rise) | 0.4750 |

### Weakest constraint

| Constraint | Mean Score |
|------------|------------|
| c8 Quantitative Accuracy | 0.8900 |
| c9 Evidence Traceability | 0.8975 |
| c7 Uncertainty Acknowledgment | 0.9025 |

---

## Interpretation

This is not yet evidence of model superiority. It is a small validation run showing that AOSL can capture prompt-level and temperature-level divergence patterns.

Notable signals:
- Temperature has a clear effect: higher temperature (0.9) produces nearly 50% more divergence than lower temperature (0.3).
- Prompt difficulty drives divergence more than model choice: cmp_p4 (Moon base) and cmp_p3 (sugar/diabetes) are the hardest prompts regardless of model.
- The two models scored similarly overall (Δ avg D = 0.06), but this sample is too small to draw conclusions.
- c8 Quantitative Accuracy is the weakest constraint across the run, consistent with prompts that involve uncertain or contested quantities.

---

## Next Recommended Milestone

**v0.9** — Larger controlled comparison:

> 10 prompts × 2 models × 3 temperatures × 1 repeat = **60 records**

This would provide enough data to begin evaluating whether divergence differences between models and temperatures are consistent across prompts, without yet claiming statistical significance.

---

## Notes

- Generated run folders (`04_RUNS/*/`) remain untracked unless intentionally frozen as canonical evidence.
- All scripts on this branch are safe to run independently — none modify stable pipeline files or the AOSL package.
- The dashboard reads any combination of run folders simultaneously via the sidebar checkboxes.
