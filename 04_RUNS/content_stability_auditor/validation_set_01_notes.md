# AOSL Content Stability Auditor — Validation Set 01 Notes

Date: 2026-05-02

## Test Set

| Sample | Stability Score | D | Tier | Citation Ready | Misinterpretation Risk | Risky Claims |
|---|---:|---:|---|---|---|---:|
| Generic AI Landing Page | 75.0 | 2.50 | S2 Usable | Medium | Medium | 2 |
| Writer Enterprise AI Homepage | 75.0 | 2.50 | S2 Usable | Medium | Medium | 3 |
| SEOPress GEO Article | 70.0 | 3.00 | S2 Usable | Medium | Medium | 4 |
| Brandi AI Replacing Google Article | 75.0 | 2.50 | S2 Usable | Medium | Medium | 3 |
| AOSL Explanation Page | 65.0 | 3.50 | S1 Weak | Medium | Medium | 5 |

## Initial Interpretation

The prototype is functioning and produces structured reports, C1-C10 breakdowns, risky claims, missing evidence, and recommendations.

However, the first validation set shows that the v0.1 heuristic is too coarse. It penalizes missing citations heavily but does not yet distinguish well between generic marketing copy, qualified educational content, and sober framework explanation.

## What Worked

- The CLI runs successfully across multiple content samples.
- Reports are generated in JSON and Markdown.
- Unsupported or broad claims are being flagged.
- C1 Factual Grounding and C9 Evidence Traceability are actively detecting evidence gaps.
- The tool gives a usable first-pass stability estimate.

## What Needs Calibration

1. C1 should distinguish between:
   - factual external claims,
   - self-description,
   - product positioning,
   - conceptual explanation.

2. C9 should not automatically fail all short content without links. It should support a PARTIAL category for content that is transparent but uncited.

3. C4 should more strongly penalize absolute claims such as:
   - guaranteed,
   - leading,
   - replacing,
   - all businesses,
   - proven,
   - always.

4. C5 should penalize broad market claims more strongly.

5. Risky claim extraction should avoid flagging titles or harmless explanatory sentences as risky.

6. Educational content with qualification language should score better than generic promotional copy.

## Product Signal

This run supports continuing the AOSL Content Stability Auditor direction.

The tool already surfaces a market-relevant problem:
content can look clear and persuasive while lacking evidence traceability, citation readiness, or stable claim boundaries.

## What This Does Not Prove

This validation set does not prove that AOSL predicts whether AI systems will cite a webpage.

It also does not prove scoring accuracy yet.

It only shows that the prototype can run, produce structured audits, and reveal useful calibration needs.

## Next Calibration Target

Improve the heuristic so that the expected ranking becomes:

1. Best: structured educational content with qualified claims
2. Strong: enterprise content with concrete proof points
3. Middle: sober framework explanation
4. Weak: generic landing-page copy
5. Weakest: broad overclaiming market-disruption content

