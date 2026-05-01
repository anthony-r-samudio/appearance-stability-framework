# AOSL Validation Roadmap v0.1

---

## Executive Summary

AOSL is not yet a proven product or validated scientific method. It is a research
prototype with early evidence for false-stability detection, a reproducible
benchmark, a human validation packet, and an agentic review-and-repair prototype.

The next phase should validate whether AOSL scores align with human judgments of
structural risk, and whether AOSL-guided repair meaningfully improves outputs as
assessed by both the scoring protocol and independent human raters. Until that
evidence exists, AOSL should be presented as a promising early-stage research
prototype, not as a finished evaluator.

---

## Current Status

The following artifacts currently exist in the project:

| Artifact | Status |
|----------|--------|
| C1–C10 scoring protocol | Defined and implemented |
| D divergence score | Computed and validated across 5 baseline levels |
| Five-level evidence ladder | Archived, reproducible |
| Benchmark package | `build_false_stability_benchmark_v0_1.py` + outputs |
| Streamlit demo app | `aosl_demo_v0_1.py`, v0.2 features |
| Example report (multi-agent) | `multi_agent_review_report_20260501_103352.md` |
| Human validation packet | `build_human_validation_packet_v0_1.py` + rating form |
| Multi-agent review prototype | `run_multi_agent_review_v0_1.py` |
| Agentic review memo | `AOSL_AGENTIC_REVIEW_MEMO_v0.1.md` |
| Research portfolio summary | `AOSL_RESEARCH_PORTFOLIO_SUMMARY_v0.1.md` |
| Public README section | Added to `README.md` |

This is a meaningful amount of prototype infrastructure. The gap is validation
evidence, not tooling.

---

## What AOSL Already Shows

The current evidence, taken together, establishes the following:

**Stable outputs score near zero.** Both real stable baselines (DeepSeek: 0.0117,
Llama: 0.0250) score near zero, confirming the framework does not falsely flag
well-formed outputs at high rates.

**Pressured outputs score higher.** Both real pressured baselines (Llama: 0.0722,
DeepSeek: 0.0939) score meaningfully above their own stable floors. DeepSeek lifts
~8× above its stable baseline; Llama lifts ~2.9×.

**Synthetic flawed outputs score highest.** The synthetic ceiling (0.2050) sits
above both pressured baselines, consistent with deliberately constructed failures
being more structurally extreme than real-world structural pressure.

**Two generator models show ordered separation.** The five-level ladder holds
across two architecturally distinct generators (DeepSeek and Llama 3.1 8B
Instruct), suggesting the signal is not specific to one model's output style.

**One agentic review run showed D improvement.** On a causal-leap example, the
five-agent pipeline reduced D from 0.4500 (S2) to 0.0000 (S0). All four failing
constraints (C3, C4, C7, C9) passed in the re-score run.

**AOSL can generate human-readable reports and repair prompts.** The Streamlit
demo and the multi-agent pipeline both produce plain-English stability reports,
constraint-level breakdowns, and structured repair guidance that non-technical
reviewers can act on.

---

## What AOSL Does Not Yet Prove

The following remain unvalidated and should not be claimed:

**Not judge-independent.** All baseline results, the benchmark ladder, and the
agentic review prototype use a single judge model (`deepseek/deepseek-chat`). A
second independent judge has not yet replicated the signal.

**Not human-validated.** No human raters have completed the validation packet.
Whether AOSL D aligns with human assessments of structural risk is unknown.

**Not proven on naturalistic tasks.** All validation prompts were purpose-built
to invite specific structural failures. Detection performance on unstructured,
diverse, real-world AI outputs has not been measured.

**Not compared against existing LLM evaluation tools.** AOSL has not been
benchmarked against generic critique prompts, G-Eval, MT-Bench, or any existing
LLM-as-judge evaluation framework. The claim of differentiation has not been
tested.

**Not proven to reduce human review time.** No user study or workflow measurement
has been run. The claim that AOSL helps reviewers work faster is aspirational.

**Not production-ready.** No authentication, rate limiting, persistent storage,
multi-user support, or error recovery. Not suitable for deployment.

**One successful repair run is not validation.** The agentic review prototype ran
once on one example, chosen to trigger known failures. This is a demonstration,
not a finding.

**Same judge model used for score, critique, and repair.** The model that scored
the original output also generated the critique and the repair. A model may
produce repairs that satisfy its own scoring preferences without producing
genuinely better outputs.

---

## Core Differentiation Hypothesis

AOSL is different only if it can reliably detect *false stability*: outputs that
appear fluent, complete, and confident while hiding structural weaknesses in
evidence, causality, uncertainty, scope, or constraint coherence.

This is the core claim. It is not yet proven. It must be the focus of the next
validation phase.

**AOSL is not unique because it uses LLM-as-judge.** Many existing evaluation
frameworks use this approach. LLM-as-judge evaluation is increasingly common and
is not a differentiator on its own.

**AOSL may be distinctive because of:**

- The false-stability framing — a named, precise problem distinct from accuracy
  or helpfulness
- The C1–C10 protocol — ten discrete, independently evaluable structural
  constraints rather than a holistic quality score
- The D divergence score — a quantitative measure of constraint violation rate
  with a calibrated reference ladder
- The benchmark — a reproducible five-level ordered baseline across two generators
- The agentic repair loop — using AOSL scores to guide targeted critique and
  verify improvement, not just flag problems

None of these are meaningful differentiators unless the scores align with human
structural-risk judgment. That is what validation must establish.

---

## Validation Questions

The following questions define the validation agenda:

1. **Human alignment:** Do human raters assign higher severity scores to outputs
   with higher AOSL D? Is the relationship monotonic or at least directionally
   consistent?

2. **Repair signal:** Do repaired outputs score lower D than original outputs
   across multiple examples — not just the one demo run?

3. **Human repair preference:** Do human raters, shown original and repaired
   outputs without knowing which is which, prefer the repaired versions?

4. **Cross-judge consistency:** Does a second independent judge model preserve
   the same broad ordering (stable < pressured < flawed) on the existing
   benchmark?

5. **Generic critique baseline:** Does AOSL produce more structured, actionable,
   and repeatable feedback than a generic "critique this answer" prompt? Does it
   catch weaknesses that generic critique misses?

6. **Review prioritization:** Can AOSL D be used to triage a batch of AI outputs
   so that human reviewers focus on the highest-risk items first?

---

## Validation Milestones

The following milestones define a staged validation path. They are ordered by
feasibility and evidence value.

---

### Milestone 1 — Human Alignment Pilot

**Prerequisite:** completed human rating forms  
**Input:** `06_OUTPUTS/human_validation/v0_1/human_validation_rating_form.csv`  
**Goal:** collect ratings from 2–3 human raters across the 30-item packet;
compare human severity scores against AOSL D  
**Output:** correlation analysis, agreement summary, human vs. AOSL comparison
report  
**Success criterion:** mean AOSL D rises monotonically (or near-monotonically)
with human severity labels; at least directional agreement between raters

---

### Milestone 2 — Repair Loop Evaluation

**Prerequisite:** Milestone 1 completed (or running in parallel with M1)  
**Input:** 10–30 examples, including stable, pressured, and synthetic inputs  
**Goal:** run `run_multi_agent_review_v0_1.py` across the full set; compare
original D vs. repaired D  
**Output:** before/after D table, distribution summary, examples where repair
fails or D worsens  
**Success criterion:** repaired outputs show lower D on average; human raters
(from M1 or a small follow-up) judge repaired outputs as structurally safer

---

### Milestone 3 — Cross-Judge Consistency

**Prerequisite:** none (can run independently)  
**Input:** existing benchmark outputs from `04_RUNS/`  
**Goal:** re-score all five benchmark levels using a second judge model different
from `deepseek/deepseek-chat`  
**Output:** judge agreement report; comparison of D values and ordering under
both judges  
**Success criterion:** both judges preserve the broad ordering
(stable < pressured < synthetic flawed), even if absolute D values differ

---

### Milestone 4 — Generic Critique Baseline

**Prerequisite:** none (can run independently)  
**Input:** same outputs used in benchmark or human validation packet  
**Goal:** prompt a model with "critique this answer" (no AOSL structure); compare
the resulting critiques against AOSL constraint-level reports  
**Output:** qualitative comparison; assessment of specificity, repeatability,
and actionability  
**Success criterion:** AOSL reports are more specific (naming which constraints
failed and why), more repeatable across runs, and more actionable than generic
critique output

---

### Milestone 5 — Real-World Task Pilot

**Prerequisite:** M1 and M2 completed  
**Input:** naturalistic AI-generated outputs from real use cases: reports,
summaries, structured analyses, instruction-following tasks  
**Goal:** apply AOSL scoring outside purpose-built prompts; measure whether D
distributes differently on naturalistic inputs  
**Output:** real-world validation memo; distribution of D across task types  
**Success criterion:** human raters find AOSL useful for review prioritization
on inputs they would encounter in actual work

---

## Evidence Needed Before Strong Claims

Before AOSL is presented as a validated research finding — rather than a research
prototype with early evidence — the following minimum evidence bar should be met:

- At least 30 human-rated outputs
- At least 2 raters, preferably 3
- Inter-rater agreement measured and reported
- Statistically meaningful correlation or monotonic relationship between human
  severity scores and AOSL D
- Before/after D improvement demonstrated across at least 10 examples
- Cross-judge ordering preserved on benchmark data
- At least one documented failure analysis: cases where AOSL and humans disagree,
  or where repair did not improve human ratings

Without this evidence, every claim about AOSL's validity should be qualified with
"in early prototype testing" or "in initial controlled conditions."

---

## What Would Make AOSL Research-Worthy

AOSL becomes a meaningful research contribution if it can demonstrate that:

1. **False stability is a recognizable failure mode.** Human raters, shown outputs
   from stable and pressured conditions, reliably assess the pressured outputs as
   structurally weaker — and AOSL D tracks this.

2. **C1–C10 captures it meaningfully.** The ten constraints cover the structural
   failure modes that human raters identify most often, with reasonable alignment
   between constraint-level flags and human issue labels.

3. **AOSL D aligns with human structural-risk judgment better than chance or
   generic critique.** This is the core claim. If AOSL D is no more correlated
   with human severity than a generic helpfulness score or a generic critique
   prompt, the framework is not adding value.

Meeting this bar would make AOSL worth describing in a research write-up or
technical report as an independent contribution to the field of AI output
evaluation.

---

## What Would Make AOSL Product-Worthy Later

AOSL becomes a product only if it can demonstrate in user studies that it:

- Saves human review time — reviewers using AOSL complete review faster and with
  higher confidence
- Improves output quality — downstream users of AOSL-reviewed outputs experience
  fewer structural failures
- Helps triage many AI outputs — reviewers prioritize effectively when guided by
  AOSL D, not just by reading outputs sequentially
- Produces reports users understand — non-technical reviewers act correctly on
  AOSL output without needing to understand the framework
- Solves a workflow problem better than asking an AI to critique itself — the
  structured protocol, not just the API call, is doing the work

None of these product conditions can be assessed from the current prototype. They
require designed user studies with real workflows and users.

---

## Recommended Next Build

The one next analysis script that would be most useful after human data is
collected:

```
05_SRC\analysis\analyze_human_validation_v0_1.py
```

This script would:
- Load completed human rating forms (multiple raters)
- Compute mean human severity scores per item
- Compute inter-rater agreement
- Compare human severity against AOSL D per item
- Report correlation, directional agreement, and failure cases
- Write a summary report to `06_OUTPUTS/human_validation/v0_1/`

**Do not build this script until at least one completed human rating form exists.**
Building analysis infrastructure before data exists produces waste. The bottleneck
is human data, not code.

---

## Immediate Non-Coding Next Step

Send the human validation packet to 2–3 raters and collect completed CSVs.

The rating form is ready:

```
06_OUTPUTS\human_validation\v0_1\human_validation_rating_form.csv
```

Instructions are included in the packet. Raters need no background in AOSL —
they review prompt–output pairs and rate severity on a 0–4 scale with issue
labels. Each rater should take 30–60 minutes for the full 30-item set.

No new code needs to be written before this step. The validation bottleneck is
human input, not infrastructure.

---

## Caveats

**AOSL is not a truth detector.** AOSL flags structural patterns associated with
instability, not factual errors. An output can score D = 0.0 and still be
factually wrong. This distinction must be stated clearly in all public-facing
descriptions.

**AOSL does not replace expert review.** For high-stakes domains — medical,
legal, financial, safety-critical — AOSL is at most a screening layer. Expert
review remains required.

**Current evidence is internal.** All validation runs were designed, executed,
and interpreted by the same person who built the system. Independent replication
has not occurred.

**Purpose-built prompts limit generalization.** The benchmark and human
validation packet use prompts designed to trigger specific structural failures.
Results may not transfer to naturalistic, diverse real-world inputs.

**Judge dependence remains unresolved.** Cross-judge validation (Milestone 3)
is a prerequisite before any strong claim about AOSL's reliability. A signal that
disappears under a different judge is not a robust signal.

**Agentic repair may overfit to judge preferences.** In the current pipeline,
the same judge model scores, critiques, and repairs. The repaired output has not
been assessed by an independent judge or human rater. D = 0.0 after repair may
reflect judge self-consistency, not genuine structural improvement.

---

## Closing Positioning Statement

AOSL should currently be presented as an independent research prototype for
studying and operationalizing false-stability detection in AI outputs, not as a
finished evaluator or commercial product.

The early evidence — ordered benchmark separation, two-generator replication, a
reproducible pipeline, and a proof-of-concept agentic repair run — is sufficient
to describe AOSL as a serious research exploration. It is not sufficient to claim
AOSL is validated, reliable, or superior to existing evaluation approaches.

The path from here to a credible research claim runs through human raters, not
through more code.

---

```
Version : v0.1
Status  : research planning document — not a product roadmap
Created : 2026-05-01
Updated : 2026-05-01
```
