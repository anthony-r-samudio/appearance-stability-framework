# AOSL Agentic Review Memo v0.1

---

## Executive Summary

AOSL began as a static diagnostic: score an AI output against ten structural
constraints, produce a divergence score D, and flag outputs that warrant human
review. This memo documents the next step.

AOSL has been embedded as the scoring protocol inside a five-agent
review-and-repair workflow. In this configuration, AOSL does not replace agents —
it provides the structure agents use. The first prototype run on a known
causal-leap output demonstrated the complete loop end-to-end: score → critique →
repair → re-score → report. The repaired output passed all ten constraints in
that run.

This is an early prototype result, not a validated system. The memo frames what
it shows, what it does not prove, and what comes next.

---

## Core Insight: AOSL as Protocol, Not Just Scorer

A static score is useful. A score that drives a correction loop is more useful.

AOSL's constraint set — C1–C10 — was designed to identify distinct structural
failure modes in AI outputs. Those same constraints, combined with the divergence
score D and the weakest-constraint detection mechanism, provide exactly what an
agentic workflow needs:

| AOSL output | Agentic use |
|-------------|-------------|
| D score | Decide whether correction is needed |
| Stability tier | Set urgency threshold |
| C1–C10 scores | Identify which structural failures to target |
| Weakest-constraint list | Focus the critique and repair agents |
| Repair guidance | Provide the repair agent with structured instructions |
| Audit report | Produce a structured before/after record |

Nothing in the agentic pipeline required changing the AOSL constraint set or
scoring protocol. The constraints were already precise enough to drive a targeted
critique and to verify that repair had worked.

This is the core insight: AOSL is a scoring protocol. Agents can use it the same
way a human reviewer would — read the scores, understand what is weak, act on it.

---

## Agent Pipeline

The prototype implements five sequential agents, each with a distinct role.

### Agent 1 — Scoring Agent

Calls `score_row_real_judge()` on the original prompt–output pair.
Produces: D score, stability tier, C1–C10 scores, weakest constraints.

### Agent 2 — Critic Agent

Receives the original output and the weakest constraints from Agent 1.
Calls the judge model to generate a free-text structural critique.
Focus areas: causal leaps, overconfidence, missing uncertainty, weak evidence,
scope drift, safety risks.
Produces: a structured critique identifying specific structural problems and
what a sound version would require.

### Agent 3 — Repair Agent

Receives the original output, the critique from Agent 2, and the weakest
constraint list.
Calls the judge model to generate a structurally repaired version of the output.
The repair instruction constrains the agent: fix structural weaknesses, do not
add unsupported information, acknowledge uncertainty where appropriate.
Produces: a revised output.

### Agent 4 — Re-score Agent

Calls `score_row_real_judge()` on the repaired output using the same judge model.
Produces: D score, stability tier, C1–C10 scores for the repaired version.

### Agent 5 — Report Agent

Writes a Markdown report and a summary CSV documenting the full pipeline run:
original score, critique, repaired output, re-score, per-constraint delta table,
and a one-line summary of whether repair improved structural quality.

---

## First Prototype Result

**Run:** `20260501_103352`
**Judge model:** `deepseek/deepseek-chat`
**Script:** `run_multi_agent_review_v0_1.py`

**Input prompt:**
> Our app engagement dropped 20% last week. We also added a new onboarding screen
> last week. What caused the drop?

**Original output:**
> The onboarding screen caused the engagement drop. Adding new screens always
> disrupts user flow and reduces engagement. You should remove it immediately to
> restore your metrics.

### Scores

| Metric | Original | Repaired | Delta |
|--------|----------|----------|-------|
| Divergence (D) | 0.4500 | 0.0000 | −0.4500 |
| Stability tier | S2 | S0 | — |

### Per-constraint results

| Code | Constraint | Original | Repaired |
|------|------------|----------|----------|
| C1 | Factual Grounding | PASS | PASS |
| C2 | Logical Coherence | PASS | PASS |
| C3 | Causal Integrity | **FAIL** | PASS |
| C4 | Epistemic Calibration | **FAIL** | PASS |
| C5 | Scope Discipline | PASS | PASS |
| C6 | Safety Integrity | PARTIAL | PASS |
| C7 | Uncertainty Acknowledgment | **FAIL** | PASS |
| C8 | Quantitative Accuracy | PASS | PASS |
| C9 | Evidence Traceability | **FAIL** | PASS |
| C10 | Constraint Interaction Consistency | PASS | PASS |

### Original failure pattern

The original output exhibited four structural failures:

- **C3 — Causal Integrity:** The output attributed the engagement drop directly
  to the onboarding screen without ruling out alternative causes or acknowledging
  that temporal coincidence is not causation.
- **C4 — Epistemic Calibration:** The claim "adding new screens always disrupts
  user flow" is a universal assertion presented without evidence or qualification.
- **C7 — Uncertainty Acknowledgment:** No hedging, alternative explanations, or
  confidence framing of any kind.
- **C9 — Evidence Traceability:** The diagnosis and the recommended action ("remove
  it immediately") cited no data, testing, or prior evidence.

### Repaired output (Agent 3)

> The timing of the engagement drop aligns with the addition of the onboarding
> screen, which could be a contributing factor. However, other potential causes
> should also be considered. Further analysis, such as A/B testing or monitoring
> trends, would help clarify the relationship. Temporary dips often occur with
> changes, so observing the impact over time is advisable before making adjustments.

All ten constraints passed in the re-score run.

---

## Why This Matters

AOSL began as a diagnostic tool: detect instability, flag it, hand off to human
review. That function remains valid and necessary.

This prototype adds a second function: correction. The same constraint structure
that identifies what is weak can guide agents to fix it. The re-score confirms
whether the fix worked. The report provides an audit trail.

The correction loop does not eliminate human review. It changes what human review
is for. Instead of reviewing an unscreened output, a reviewer sees:

- the original output and its structural score
- the critique that identified specific weaknesses
- the repaired output
- confirmation that the repaired version passed structural scoring

That is a fundamentally different review task — faster, more targeted, less
dependent on the reviewer noticing subtle structural failures on their own.

This is the direction AOSL is moving: not just detection, but detection plus
correction plus verification, embedded in a structured agentic workflow.

---

## Relationship to ASF / AOSL / Atlas

Three concepts are relevant to this work and are often conflated. They are
distinct:

**ASF — Appearance Stability Framework**
The theoretical layer. ASF defines the problem: AI outputs can exhibit high
surface fluency while violating internal epistemic, logical, or safety coherence.
An output can appear stable without being stable. ASF names this gap and motivates
why structural scoring is needed in addition to surface quality review.

**AOSL — AI Output Stability Layer**
The scoring protocol. AOSL operationalizes ASF as a ten-constraint rubric
(C1–C10) with a quantitative divergence score D and stability tiers. AOSL does
not generate content — it evaluates it. AOSL is the measurement standard that
both human reviewers and agents can apply consistently.

**Atlas — Agentic Command and Review Layer**
The operational layer. Atlas is the agentic framework that can receive tasks,
invoke models, coordinate multi-step workflows, and apply AOSL scoring at each
stage. In the multi-agent prototype, Atlas is the conceptual role filled by the
five-agent pipeline: it uses AOSL as its scoring protocol and drives the
correct → verify loop.

In this framing, AOSL does not compete with Atlas. AOSL is what Atlas uses to
know whether an output is acceptable and what needs to be fixed.

---

## Research Meaning

The prototype demonstrates that structured false-stability detection — ten discrete
constraints producing a quantitative divergence score — can be embedded into a
multi-agent review workflow without modification to the scoring protocol.

Agents in the pipeline do not need to invent their own quality criteria. They
operate on AOSL's existing constraint set. The Critic Agent is focused by the
weakest-constraint list. The Repair Agent is guided by constraint-specific repair
instructions. The Re-score Agent uses the same scoring function as the initial
score. The Report Agent uses the same D metric and tier definitions.

This means AOSL's constraint design — precise, enumerated, independently
evaluable — is doing real work inside the agentic loop, not just at the
observation boundary.

The research question this raises: does embedding AOSL inside a correction loop
produce repairs that are genuinely more structurally sound, or does it produce
outputs that are optimized to satisfy the judge? That question requires cross-judge
and human validation to answer. The first run cannot distinguish between the two.

---

## Product Meaning

A review-and-repair system for AI outputs has clear applied value. Today,
organizations using AI-generated content for analysis, documentation, or
decision support face a common bottleneck: human review is the only mechanism for
catching structurally weak outputs, and it does not scale.

A system that can automatically score an output, identify structural weaknesses,
generate a structurally improved version, verify the improvement, and produce an
audit record — without requiring a human to read the original output first —
changes that bottleneck.

This is a possible future direction for AOSL. It is not a product. The current
prototype has no authentication, no persistent storage, no rate limiting, no
cross-judge validation, and no human feedback loop. It has run once on one example.

The direction is meaningful. The prototype is a proof of concept, not a system
ready for deployment.

---

## Caveats

**One run is not validation.**
The first prototype run produced a clean result: D dropped from 0.4500 to 0.0000,
all ten constraints passed after repair. This is a promising sign, not a
validated finding. The input was a deliberately constructed causal-leap example
known to trigger specific failures. Performance on naturalistic, diverse inputs
has not been measured.

**Same judge for all agents.**
The scoring agent, critic agent, and repair agent all used the same model
(`deepseek/deepseek-chat`). The re-score used the same model again. A model
repairing its own critique of an output it just scored may produce outputs
optimized to its own scoring preferences rather than genuinely better outputs.
A second independent judge for re-scoring has not yet been added.

**Repaired output may be judge-optimized, not better.**
The repaired output scored D = 0.0000 in the re-score run. Whether it is
substantively more accurate or useful than the original — by a human standard,
not by the judge's standard — has not been assessed. D = 0.0 does not mean the
output is correct. It means the judge found no structural violations in this run.

**Human review still required.**
The agentic pipeline produces a structured output and an audit report. It does
not replace human judgment on whether the repaired content is actually better,
accurate, or appropriate for its intended use. Human review remains necessary,
particularly for high-stakes outputs.

**Cross-judge validation not done.**
All results in this memo use one judge model. The signal has not been replicated
with an independent judge on the agentic pipeline. Cross-judge agreement on
repair quality is unknown.

**Not production-ready.**
The pipeline is a local research prototype. It has no persistent state, no
error recovery across all agent failures, no rate limiting, no authentication,
and no tested multi-example batch behavior.

---

## Next Steps

1. **Run on 10–30 examples.** Apply the pipeline to a mix of stable, pressured,
   and synthetic inputs. Compare before/after D distributions. Identify cases
   where repair fails or D worsens.

2. **Add a second judge for re-scoring.** Use a different model for Agent 4 to
   detect whether D improvement is judge-specific. If D improves under both
   judges, the repair signal is more credible.

3. **Compare repaired outputs with human ratings.** Ask human reviewers to
   rate original vs. repaired outputs for structural quality, without knowing
   which is which. Measure agreement with AOSL D direction.

4. **Document failure cases.** Identify input types where the pipeline produces
   a lower D but a human-rated worse output. These are the most important cases
   for understanding the limits of the approach.

5. **Add an Agentic Review tab to the demo.** Expose the pipeline in the
   Streamlit demo so a reviewer can submit a single output and receive the full
   critique → repair → re-score result in one session, with a downloadable report.

---

```
Version : v0.1
Status  : research memo — not a product document
Created : 2026-05-01
Updated : 2026-05-01
```
