# AOSL Content Stability Auditor v0.1

**Type:** Early prototype — research and internal use only
**Status:** Not validated, not production-ready
**Date:** 2026-05-02

---

## Purpose

The AOSL Content Stability Auditor applies the AOSL (AI Output Stability Layer)
structural constraint framework to content — pages, articles, landing pages, or
any text intended for AI-facing use — and estimates how structurally stable that
content is. Structural stability, in this context, means the degree to which
content is grounded, internally coherent, causally sound, appropriately scoped,
and traceable to evidence.

This is not an SEO tool. It does not measure keyword density, backlinks, page
speed, schema markup, or search engine ranking signals. It measures structural
properties of the content itself: whether claims are supported, whether causal
language is earned, whether scope is appropriate, and whether evidence is
traceable.

---

## Why This Connects to AI Visibility

AI platforms (including large-language-model-based search, AI assistants, and
retrieval-augmented generation systems) tend to summarize and cite content that
is structurally clear, well-sourced, and low in ambiguity. Content that is
overconfident, vaguely sourced, or causally incoherent is more likely to be
misrepresented, paraphrased inaccurately, or filtered out of AI-generated
summaries.

AOSL Content Stability addresses a specific subset of this problem:
**false stability** — content that appears fluent and confident but conceals
structural weaknesses in evidence, causality, scope, or epistemic calibration.
Structurally weak content is at higher risk of AI misinterpretation than
structurally sound content, all else equal.

This framing is distinct from "AI SEO." The auditor is not designed to
optimize content for ranking or recommendation. It is designed to identify
structural risks that make content less reliable for AI-assisted reading and
citation.

---

## Core Hypothesis

Content that scores low D (low structural divergence) across the AOSL C1–C10
constraints is more likely to be accurately summarized by AI systems and less
likely to have its claims distorted, amplified, or stripped of appropriate
uncertainty. Content that scores high D is more likely to be misrepresented,
whether by amplifying overconfident claims or by treating speculative assertions
as established facts.

This hypothesis has not been validated against AI citation behavior. It is a
structural inference based on the AOSL false-stability framework, not an
empirical finding.

---

## v0.1 Scope

This version is a local prototype using deterministic keyword/pattern heuristics.
It does not require an API key. It is intentionally simple.

**What v0.1 includes:**
- Heuristic scoring against all ten AOSL constraints (C1–C10)
- Divergence score D (raw and normalized)
- Stability score (0–100) and tier (S0–S3)
- AI citation readiness estimate (Low / Medium / High)
- AI misinterpretation risk estimate (Low / Medium / High)
- Extracted risky claims (sentences triggering constraint failures)
- Missing evidence gaps
- Recommended structural fixes
- AI-readable improvement suggestions
- JSON and Markdown report export
- Streamlit web UI and CLI runner

**What v0.1 does not include:**
- Real-judge scoring (requires API key — planned for v0.2)
- Factual accuracy checking
- Web scraping or URL-based auditing
- Competitor comparison
- Multi-page batch auditing
- Authentication, rate limiting, or persistent storage

---

## Inputs and Outputs

**Inputs:**
- Content text (pasted or from a `.txt` file)
- Optional: title, source URL, reviewer notes

**Outputs:**
- Stability score and tier
- D divergence score
- Per-constraint scores and explanations (C1–C10)
- Risky claims list
- Missing evidence list
- Recommended fixes list
- AI-readable improvements list
- JSON report
- Markdown report

Reports are saved to `04_RUNS/content_stability_auditor/`.

---

## C1–C10 Mapping to Content Stability

| Code | Constraint | Content Stability Interpretation |
|------|------------|----------------------------------|
| C1 | Factual Grounding | Are factual claims linked to named sources or evidence markers? |
| C2 | Logical Coherence | Is the argument internally consistent with no contradictions? |
| C3 | Causal Integrity | Are causal claims ("X leads to Y") supported by data or reasoning? |
| C4 | Epistemic Calibration | Are certainty levels appropriate — no "guaranteed" without evidence? |
| C5 | Scope Discipline | Are claims scoped to the appropriate audience or context? |
| C6 | Safety Integrity | Is sensitive (medical/legal/financial) content appropriately caveated? |
| C7 | Uncertainty Acknowledgment | Is uncertainty acknowledged where claims are speculative? |
| C8 | Quantitative Accuracy | Are numbers and statistics cited or contextualized? |
| C9 | Evidence Traceability | Are sources, links, or citations present and specific? |
| C10 | Constraint Interaction Consistency | Is the tone of confidence consistent with the level of evidence? |

---

## Scoring Formula

```
D_raw = sum(1 - Ci)  for i in C1..C10   # range: 0 (no violations) to 10 (all fail)
D_norm = D_raw / 10                       # normalized to 0–1
stability_score = (1 - D_raw / 10) * 100  # range: 0–100
```

Constraint scores: `1.0` (pass) / `0.5` (partial weakness) / `0.0` (clear weakness).

Stability tiers:

| Score | Tier | Label |
|-------|------|-------|
| 90–100 | S3 | Strong |
| 70–89.9 | S2 | Usable |
| 50–69.9 | S1 | Weak |
| 0–49.9 | S0 | Unstable |

---

## What This Supports

- **A rapid structural audit.** The auditor surfaces evidence gaps, overconfident
  language, and causal overreach in under a second, without an API call.

- **A starting point for human review.** The risky claims list and missing
  evidence list give a human reviewer a specific, prioritized set of issues to
  investigate — rather than a generic quality score.

- **Consistency with the AOSL research framework.** The same C1–C10 constraints
  used in AOSL judge calibration and the multi-agent review pipeline are applied
  here. This makes the content auditor a coherent extension of the existing
  research architecture.

---

## What This Does Not Prove

- **AI citation behavior is not predicted.** A high stability score does not
  mean any AI platform will cite, recommend, or summarize this content. A low
  score does not mean AI platforms will ignore it.

- **Factual accuracy is not checked.** The auditor measures structural patterns,
  not correctness. Content can score S3 (Strong) and still be factually wrong.

- **Heuristics are approximate.** The v0.1 heuristic has not been calibrated
  against human content quality ratings or validated against real AI citation
  outcomes. Scores should be treated as directional signals, not ground truth.

- **No human validation has been conducted.** The heuristic has not been compared
  against human content quality assessments. Its accuracy relative to expert
  judgment is unknown.

---

## Next Milestones

1. **Real-judge scoring (v0.2):** Replace the heuristic with `score_row_real_judge`
   using the content as `output_text` and a generic structural prompt. Requires
   `OPENROUTER_API_KEY`. Compare heuristic and real-judge scores on the same
   inputs.

2. **URL input (v0.3):** Accept a URL, fetch the page text, strip HTML, and
   audit the cleaned content. Requires a web scraping or extraction module.

3. **Batch auditing:** Accept a CSV of titles + URLs or text snippets. Score all,
   rank by D, export summary report.

4. **Human calibration:** Collect human content quality ratings on the same
   inputs scored by the auditor. Compare human ratings against AOSL D. Measure
   correlation and identify systematic heuristic errors.

5. **AI citation correlation study:** Measure whether content scoring higher
   stability D is less likely to be accurately cited by a target AI system.
   This is the core empirical test of the content stability hypothesis.

---

## Caveats

This is an early prototype. Use it to generate hypotheses and focus human review
attention — not to make final decisions about content quality, publication, or
AI strategy. Results are not guarantees. Human review is required before acting
on any specific finding.

---

```
Version : v0.1
Status  : early prototype — research use only
Created : 2026-05-02
```
