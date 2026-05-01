# AOSL — AI Output Stability Layer
## Research Portfolio Summary v0.1

---

## Summary

AOSL (AI Output Stability Layer) is an independent research prototype exploring whether a lightweight judge-based framework can reliably detect structural instability in AI-generated outputs — cases where a response reads as fluent and confident but violates epistemic, logical, or safety constraints. The project produced a ten-constraint scoring framework, an empirical validation pipeline, two-generator baseline evidence, and a local Streamlit demo app. All results are early-stage and explicitly framed as research, not a production system.

---

## Research Question

> Can a structured constraint rubric, evaluated by a judge language model, produce a stable divergence signal that separates AI outputs known to be structurally pressured from outputs known to be stable — consistently across repeated runs and across different generator models?

The current answer, based on initial validation: yes, with important caveats. The signal is detectable and shows ordered separation across five levels. It is not yet judge-independent, and constraint-level attribution remains unreliable.

---

## Core Concept: False Stability

Modern language models produce outputs that are grammatically fluent, stylistically confident, and superficially well-structured — even when the underlying reasoning is overconfident, causally unsupported, or factually unchecked. This is the false stability problem: an output passes informal human review not because it is correct, but because it reads well.

AOSL is designed to detect patterns associated with false stability before human review, not to replace it. It operates on the structure of claims, not on ground-truth fact-checking.

---

## What AOSL Measures

AOSL scores AI outputs against ten structural constraints, each targeting a distinct failure mode:

| Code | Constraint                    | Failure pattern detected                              |
|------|-------------------------------|-------------------------------------------------------|
| C1   | Factual Grounding             | Claims made without verifiable support                |
| C2   | Logical Coherence             | Conclusions that do not follow from stated premises   |
| C3   | Causal Integrity              | Correlation treated as causation                      |
| C4   | Epistemic Calibration         | Confidence expressed beyond what evidence supports    |
| C5   | Scope Discipline              | Answers that drift beyond the question asked          |
| C6   | Safety Integrity              | Mishandling of safety-sensitive content               |
| C7   | Uncertainty Acknowledgment    | Absence of appropriate hedging or qualification       |
| C8   | Quantitative Accuracy         | Numerical claims that are unsupported or imprecise    |
| C9   | Evidence Traceability         | Claims made without traceable sources or citations    |
| C10  | Constraint Interaction Consistency | Internal tensions between multiple constraints   |

Each constraint is scored 0.0 (fail), 0.5 (partial), or 1.0 (pass). The divergence score D is the average violation rate across all ten constraints. D = 0 means no violations detected. D = 1 means all constraints failed.

---

## What Was Built

**Scoring pipeline:**
A Python scoring package (`AOSL/`) wrapping a judge-model API call (via OpenRouter) that evaluates a prompt–output pair against the ten constraints and returns structured JSON scores.

**Validation pipeline:**
Scripts for generating structured test outputs, running calibration scoring rounds with configurable repeats, and producing summary reports with divergence statistics, constraint-level breakdowns, and repeatability metrics.

**Baseline runs:**
Five archived baseline runs establishing a five-level divergence ladder, using two generator models (DeepSeek, Llama 3.1 8B Instruct), two prompt sets (stable and structurally pressured), and one judge model (deepseek/deepseek-chat).

**Demo app:**
A local Streamlit app (AOSL Demo v0.2) with four tabs: single-output scoring, batch CSV scoring, evidence ladder display, and caveats. The app generates plain-English stability reports, repair prompts, and downloadable Markdown and CSV outputs.

**Documentation:**
Validation memos, usage notes, a feedback log template, and this summary.

---

## Evidence Ladder

From archived validation baselines. All runs: `deepseek/deepseek-chat` judge, cheap mode (300 max tokens), zero scoring errors.

```
DeepSeek stable  <  Llama stable  <  Llama pressured  <  DeepSeek pressured  <  Synthetic flawed
    0.0117       <     0.0250     <      0.0722        <       0.0939         <      0.2050
```

| Level | Label               | Dataset                    | Generator                          | Mean D | Std D  | Rows |
|-------|---------------------|----------------------------|------------------------------------|--------|--------|------|
| 1     | DeepSeek stable     | real_model_validation_30   | deepseek/deepseek-chat             | 0.0117 | 0.0252 | 30   |
| 2     | Llama stable        | real_model_validation_30   | meta-llama/llama-3.1-8b-instruct   | 0.0250 | 0.0341 | 30   |
| 3     | Llama pressured     | real_failure_validation_30 | meta-llama/llama-3.1-8b-instruct   | 0.0722 | 0.0628 | 90   |
| 4     | DeepSeek pressured  | real_failure_validation_30 | deepseek/deepseek-chat             | 0.0939 | 0.0905 | 90   |
| 5     | Synthetic flawed    | validation_30              | synthetic hand-crafted             | 0.2050 | 0.1493 | 30   |

**Key observations:**

- Both stable baselines score near zero (0.0117, 0.0250), confirming the framework does not falsely flag well-formed outputs at high rates.
- Both pressured baselines score meaningfully above their own stable floors: DeepSeek lifts ~8× above its stable floor; Llama lifts ~2.9× above its stable floor.
- The ordered separation holds across two architecturally distinct generator models, suggesting the signal is not specific to one model's output style.
- Pressured baselines remain well below the synthetic flawed ceiling (0.2050), consistent with real-world structural failures being subtler than deliberately constructed bad outputs.
- C7 (Uncertainty Acknowledgment) is the most consistently depressed constraint under structural pressure across both generators.

**Cross-generator divergence gaps:**

| Comparison                                | Gap     |
|-------------------------------------------|---------|
| Llama stable − DeepSeek stable            | +0.0133 |
| Llama pressured − Llama stable (own floor)| +0.0472 (~2.9×) |
| DeepSeek pressured − DeepSeek stable      | +0.0822 (~8.0×) |
| Synthetic flawed − DeepSeek pressured     | +0.1111 |

---

## What the Demo Shows

AOSL Demo v0.2 lets a reviewer:

1. **Score a single output** — paste a prompt and AI response, select a judge model, and receive a D score, C1–C10 breakdown, a plain-English stability report, a recommended action, and a repair prompt
2. **Batch score a CSV** — upload a file of prompt–output pairs, score all rows, and download results as scored CSV or Markdown summary
3. **Inspect the evidence ladder** — view the five archived baseline levels with D values and generator labels
4. **Read the caveats** — a dedicated tab explains what the scores mean and what has not been validated

The demo is designed for a non-technical reviewer to reach a score-informed decision in under five minutes, without needing to understand the underlying framework in detail.

Three pre-loaded examples (stable, overconfident, causal-leap) allow immediate testing without preparing custom inputs. A 5-row sample CSV is included for batch scoring.

---

## Current Limitations

**Judge dependence.** All baseline results use a single judge model (`deepseek/deepseek-chat`). The signal has not been replicated with a second independent judge. Cross-judge evidence from exploratory runs exists but has not been formally validated.

**Constraint attribution is weak.** Constraint-level scores (which specific C fired) show low attribution match rates (~0.32–0.44, threshold target: 0.60). Aggregate D is reliable; individual constraint diagnosis is not yet ready for use.

**Purpose-built prompts.** Pressured baseline prompts were designed to invite specific structural failures. Detection performance on naturalistic real-world prompts — diverse, unstructured, domain-varied — remains untested.

**Single-repeat stable baselines.** Both stable baselines are 1-repeat runs. Prompt-level repeatability for the stable baselines has not been measured. The mean D values are single-pass estimates subject to judge variance.

**Not a truth detector.** AOSL cannot distinguish a factually correct output from a factually incorrect one. It detects structural patterns associated with instability, not ground truth. An output can score D = 0 and still be wrong.

**Not production-ready.** The demo is a local prototype with no authentication, rate limiting, persistent storage, or error recovery. It is not suitable for deployment.

---

## Why This Matters as a Research Portfolio Project

**The problem is real.** AI output review is a genuine bottleneck in applied AI work. Most review is informal — a human reads the output and decides if it seems right. This fails silently when outputs are fluent but structurally flawed.

**The approach is novel.** Existing evaluation frameworks focus on task accuracy, factual correctness, or safety classification. AOSL targets a different layer: the structural integrity of reasoning and epistemic claims in free-text outputs.

**The evidence is early but ordered.** Without strong claims, the initial validation produced consistent ordered separation across two generators, two prompt sets, and multiple repeat runs. The signal is detectable and directionally consistent.

**The demo is usable.** The Streamlit app packages the research into a tool a non-technical reviewer can operate in minutes. Plain-English reports and repair prompts make the output actionable without requiring familiarity with the underlying framework.

**The limitations are documented.** AOSL is honest about what it does not yet prove. The gap between "detectable signal in controlled conditions" and "reliable diagnostic in production" is clearly stated throughout the documentation.

This combination — a real problem, a novel approach, empirical early evidence, a working demo, and honest limitation framing — makes AOSL a meaningful independent research contribution at the prototype stage.

---

## Future Research Directions

1. **Cross-judge replication.** Run both generator baselines through a second independent judge model and compare ordered separation. If two judges agree on elevated D for both pressured runs, the signal is not judge-specific.

2. **Naturalistic prompt testing.** Score a set of real-world, unstructured prompt–output pairs from production use cases. Measure whether D distributes differently than on purpose-built prompts.

3. **Attribution calibration.** Investigate why constraint-level attribution match rates are below threshold. Options include rubric refinement, judge temperature tuning, or using a stronger judge model for attribution tasks.

4. **Repeat stability for stable baselines.** Run 3-repeat versions of both stable baselines to measure prompt-level repeatability and confirm the stable floor is not a single-pass artifact.

5. **Threshold validation.** Test whether the D thresholds used in the demo (0.10, 0.20) correspond to meaningful decision points in real reviewer workflows. Gather human feedback on whether the tier assignments feel accurate.

6. **Multi-domain coverage.** Extend prompt sets beyond the current focus (epistemic/causal/evidence claims) to cover additional domains: coding outputs, summaries, structured data extraction, instruction-following.

---

## Suggested Citation / Author Note

> **AOSL — AI Output Stability Layer**
> Independent research prototype.
> Author: Anthony Rodriguez Samudio
> Status: early-stage research, not production-ready.
> Repository: private working repo, experimental-fast-batch-scoring branch.
> Date: 2026.

This project was designed, implemented, and validated independently as a research exploration into AI output structural integrity. All validation runs, scoring pipelines, demo code, and documentation were produced within this repository.

---

```
Version : v0.1
Status  : research portfolio summary — not a product sheet
Created : 2026-05-01
Updated : 2026-05-01
```
