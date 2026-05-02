# AOSL Content Stability Auditor — v0.2 Calibration

Date: 2026-05-02

---

## Why v0.2

v0.1 produced a flat cluster of scores (70–75) across structurally different content, and scored the AOSL explanation page lowest (65.0 S1) when it should have scored among the highest. The root cause was a citation-blunt heuristic that:

- Penalized any content without URL sources, regardless of claim type
- Treated "is/are" sentences as factual claims requiring citations
- Failed to distinguish self-description, educational explanation, product positioning, and external authority claims

v0.2 goal: make scoring sensitive to claim type, claim strength, evidence expectation, and overclaim risk.

---

## What Changed

### 1. Claim Classifier (`classify_claims`)

A new function classifies each sentence before scoring. Claim types:

| Type | Evidence Expectation | Examples |
|------|---------------------|----------|
| heading | LOW | Title lines without terminal punctuation |
| disclaimer | LOW | "does not guarantee", "early research", "some marketers argue" |
| self_description | LOW | Sentences with "we", "our", "the platform" |
| educational_explanation | LOW | "is a framework for...", "refers to..." |
| product_positioning | LOW | General marketing statements |
| prediction_or_trend_claim | MEDIUM | "increasingly", "is changing", "becoming" |
| causal_claim (hedged) | MEDIUM | "could lead to", "may result in" |
| causal_claim (unhedged) | HIGH | "leads to", "results in" without hedge |
| absolute_claim | HIGH | "always", "instantly", "the only", "most advanced" |
| quantitative_claim | HIGH | Sentences with percentages or large numbers |
| authority_claim | VERY HIGH | "trusted by major companies", "world-leading" |
| disruption_claim | VERY HIGH | "replacing Google", "AI is replacing", "revolutionizing" |
| guarantee_claim | VERY HIGH | "guarantees success", "will definitely" |

### 2. C1 (Factual Grounding) — Claim-Type Aware

v0.1 penalized any sentence containing "is/are" without a URL.

v0.2 penalizes only when VERY HIGH or HIGH claims exist with insufficient evidence:
- PASS if no high-expectation external claims detected
- PARTIAL if high claims with limited evidence
- FAIL if VERY HIGH claims with zero evidence (named sources or URLs)

Self-description, educational explanation, and product positioning now correctly PASS C1.

### 3. C4 (Epistemic Calibration) — Authority Claims + Hedge Mitigation

v0.1 only checked _ABSOLUTE_MARKERS.

v0.2 adds:
- `_AUTHORITY_CLAIM_MARKERS`: "trusted by major companies", "world-leading", "#1 platform", etc.
- Negation-aware "guarantee" counting: "does not guarantee" is NOT an overclaim
- Hedge mitigation: if `hedge_count >= 2 × overclaim_count`, penalty is reduced one level

### 4. C5 (Scope Discipline) — Disruption Claims + Hedge Mitigation

v0.2 adds `_DISRUPTION_MARKERS`: "replacing Google", "AI is replacing", "revolutionizing".

Same hedge mitigation as C4. Well-hedged disruption claims (e.g., Brandi article) score PASS on C5 because hedge_count is 4× the overclaim_count.

Also fixed: scope marker `"all businesses"` was false-matching `"small businesses"` — now uses word-boundary regex matching.

### 5. C7 (Uncertainty Acknowledgment) — Substantive Zero-Hedge Detection

v0.2 adds: if word count > 60 and zero hedge markers found, C7 = PARTIAL. This penalizes marketing copy with no uncertainty acknowledgment, regardless of whether absolute markers are present.

C7 also now counts disruption and authority claims in its `total_confident` tally, not just absolute markers.

### 6. C9 (Evidence Traceability) — Named Systems as Soft Evidence

v0.1 auto-failed all content without URLs.

v0.2 counts named AI systems (ChatGPT, Claude, Gemini, Perplexity, Google AI, etc.) as soft evidence, capped at 3 evidence points. Rules:
- FAIL only if HIGH/VERY HIGH claims exist with zero total evidence (formal + soft)
- PARTIAL if no formal citations but no high-expectation claims (content is not making claims that require sources)
- PASS if total evidence (including named systems) is adequate

### 7. C10 (Constraint Interaction Consistency) — Severity Gap

v0.2 FAILS C10 (not just PARTIAL) when `c1 == 0.0 AND c9 == 0.0` — indicating both grounding and traceability have collapsed simultaneously. This correctly identifies content like the Writer homepage (authority claim + no evidence).

### 8. Structural Fixes

- `_sentences()` now splits on `\n\n+` (paragraph breaks) before sentence boundaries. This prevents title lines embedded in file content from merging with the first paragraph sentence.
- BOM (U+FEFF) stripped from content in `score_content()`.
- `_is_disclaimer()` filters disclaimer sentences from risky_claims output.
- Heading-like lines (no terminal punctuation, ≤ 12 words) classified as LOW evidence expectation.

---

## v0.1 vs v0.2 Comparison

| Sample | v0.1 Score | v0.1 Tier | v0.2 Score | v0.2 Tier |
|--------|:----------:|-----------|:----------:|-----------|
| SEOPress GEO Article | 70.0 | S2 Usable | 100.0 | S3 Strong |
| AOSL Explanation | 65.0 | S1 Weak | 100.0 | S3 Strong |
| Brandi AI Replacing Google | 75.0 | S2 Usable | 95.0 | S3 Strong |
| Generic AI Landing Page | 75.0 | S2 Usable | 80.0 | S2 Usable |
| Writer Enterprise AI | 75.0 | S2 Usable | 60.0 | S1 Weak |

v0.1 range: 65–75 (10 points). v0.2 range: 60–100 (40 points).

---

## Why This Ranking Is Correct

**SEOPress (100.0):** Educational content about GEO. Names 5 AI systems as soft evidence. Contains qualified language ("may increase the chance", "does not guarantee"). No overclaims. All constraints PASS.

**AOSL Explanation (100.0):** Purely self-referential. All claims are self-description or disclaimers ("does not prove", "does not guarantee", "early research"). Names 5 AI systems as soft evidence for C9. No overclaims.

**Brandi AI Replacing Google (95.0):** Article about AI search disruption that explicitly qualifies its own disruption claim ("This claim is partly true in some user behaviors, but it may be too broad if stated without data"). Hedge count (4+) exceeds overclaim count by 4×. C5 PASSES via hedge mitigation. Only C9 is PARTIAL (no named sources in article body).

**Generic AI Landing Page (80.0):** Marketing copy with no hedges and no evidence. "Generate copy instantly" triggers C4 PARTIAL. Zero hedge markers triggers C7 PARTIAL. No formal sources with product positioning → C9 PARTIAL. C10 PARTIAL from c4+c9 misalignment.

**Writer Enterprise AI (60.0):** "Writer says it is trusted by major companies" — an authority claim (VERY HIGH evidence expectation) with zero evidence (no named clients, no citations, no verifiable data). C1 FAIL, C9 FAIL, C10 FAIL. C4 and C7 PARTIAL (one confident claim, no hedges).

---

## What This Does Not Prove

- v0.2 scores do not prove that AI platforms will or will not cite these pages.
- Claim classification is heuristic-based and will misclassify edge cases (e.g., content that uses "our" but makes external claims, or disruption claims buried in long prose).
- The scorer does not detect factual errors. High-scoring content can still be factually wrong.
- Hedge mitigation can be gamed: adding hedges without substantive qualification will improve scores without improving quality.
- Results have not been validated against actual AI citation behavior.

---

## What v0.3 Should Target

1. **Differentiate self-referential vs externally-grounded educational content.** SEOPress and AOSL both score 100, but SEOPress makes claims about external practices (GEO) while AOSL only describes itself. A v0.3 heuristic should distinguish these and award a small bonus to externally-grounded educational content.

2. **Detect hedge-gaming.** Hedge mitigation currently rewards any high hedge count. v0.3 should check whether hedges are substantive ("this claim is partly true in some user behaviors") vs decorative ("may possibly perhaps...").

3. **Add C3 sensitivity to soft causal language.** "May increase the chance that AI systems interpret the page correctly" is a causal claim but does not fire C3. v0.3 should detect soft causal language and apply a PARTIAL with hedge-aware evidence check.

4. **Named-source specificity.** "Anthropic", "OpenAI", "Google DeepMind" as organizations vs "ChatGPT", "Claude", "Gemini" as specific systems. v0.3 should treat organizational citations as stronger evidence than product name mentions.

5. **Validate against real AI citation behavior.** Run a set of known-cited vs known-uncited pages through the heuristic and measure whether higher stability scores correlate with actual citation frequency.

---

```
Scorer  : heuristic-v2
Status  : early prototype — not for production use
```
