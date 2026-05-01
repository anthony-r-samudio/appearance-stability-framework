# AOSL False-Stability Benchmark v0.1

## Summary

This benchmark summarizes archived AOSL baseline scoring runs across five levels
of structural pressure. It establishes an ordered evidence ladder — from stable
real model outputs to deliberately flawed synthetic outputs — without new API calls.
All runs use `deepseek/deepseek-chat` as judge in cheap mode (300 max tokens),
with zero scoring errors across all five-level baseline runs.

---

## Five-Level Evidence Ladder

| Level | Label               | Dataset                    | Generator                          | Mean D | Std D  | Rows | Repeats |
|-------|---------------------|----------------------------|------------------------------------|--------|--------|------|---------|
| 1     | DeepSeek stable     | real_model_validation_30   | deepseek/deepseek-chat             | 0.0117 | 0.0252 | 30   | 1       |
| 2     | Llama stable        | real_model_validation_30   | meta-llama/llama-3.1-8b-instruct   | 0.0250 | 0.0341 | 30   | 1       |
| 3     | Llama pressured     | real_failure_validation_30 | meta-llama/llama-3.1-8b-instruct   | 0.0722 | 0.0628 | 90   | 3       |
| 4     | DeepSeek pressured  | real_failure_validation_30 | deepseek/deepseek-chat             | 0.0939 | 0.0905 | 90   | 3       |
| 5     | Synthetic flawed    | validation_30              | synthetic hand-crafted             | 0.2050 | 0.1493 | 30   | 1       |

---

## Ordering

```
DeepSeek stable  <  Llama stable  <  Llama pressured  <  DeepSeek pressured  <  Synthetic flawed
    0.0117       <     0.0250     <      0.0722        <       0.0939         <      0.2050
```

Both stable baselines score near zero, confirming the framework does not falsely
flag well-formed outputs at high rates. Both pressured baselines score meaningfully
above their own stable floors. The synthetic flawed ceiling sits well above all
real-output baselines.

---

## Divergence Gaps

| Comparison                                          | Gap     |
|-----------------------------------------------------|---------|
| Llama stable − DeepSeek stable                      | +0.0133 |
| Llama pressured − Llama stable (own floor)          | +0.0472 |
| Llama pressured / Llama stable (ratio)              | ~2.9×   |
| DeepSeek pressured − DeepSeek stable (own floor)    | +0.0822 |
| DeepSeek pressured / DeepSeek stable (ratio)        | ~8.0×   |
| DeepSeek pressured − Llama pressured                | +0.0217 |
| Synthetic flawed − Llama pressured                  | +0.1328 |
| Synthetic flawed − DeepSeek pressured               | +0.1111 |

---

## Interpretation

- **Stable outputs score near zero.** Both real-model stable baselines (DeepSeek 0.0117,
  Llama 0.0250) confirm the framework does not generate spurious violations on
  unpressured, well-formed AI outputs.

- **Pressured outputs score higher.** Both real-failure baselines score meaningfully
  above their own generator's stable floor. DeepSeek pressured lifts ~8× above its
  stable floor; Llama pressured lifts ~2.9× above its stable floor.

- **Synthetic flawed outputs score highest.** The synthetic ceiling (0.2050) sits
  well above both pressured real baselines, consistent with deliberately constructed
  failures being more severe than naturalistic structural weaknesses.

- **The ordering is consistent across generators.** Two architecturally different
  generator models produce the same directional result: near-zero D on stable prompts,
  elevated D on structurally pressured prompts.

---

## Caveats

- **Judge-dependent.** All results use a single judge model (`deepseek/deepseek-chat`).
  The signal has not been independently replicated with a second judge at scale.

- **Purpose-built prompt sets.** Pressured prompts were designed to invite specific
  structural failures. Detection on naturalistic real-world prompts remains untested.

- **Constraint attribution is weak.** Per-constraint attribution match rates (0.32–0.44)
  are below the 0.60 target threshold. Aggregate D is the reliable signal.
  Constraint-level diagnosis is not yet validated.

- **Not a truth detector.** AOSL detects structural divergence patterns, not factual
  correctness. A low-D output may still be factually wrong.

- **Cross-judge evidence is exploratory.** Exploratory second-judge runs exist but
  have not been formally validated as a replication of the primary signal.

- **Not production-ready.** This is an independent research prototype. It is not
  suitable for deployment without further validation.

---

## Portfolio Note

AOSL is currently best framed as an independent research prototype exploring false
stability in AI outputs. The false stability problem — outputs that read as confident
and fluent but violate structural epistemic or logical constraints — is real and
underaddressed in current AI evaluation practice.

This benchmark provides early empirical grounding for the AOSL detection hypothesis:
a structured constraint rubric, evaluated by a judge model, can produce a stable
and ordered divergence signal across different generator models and prompt conditions.
It does not yet prove the signal is judge-independent or generalizes to naturalistic
prompts.

**Independent research prototype by Anthony Rodriguez Samudio.**

---

```
Version : v0.1
Judge   : deepseek/deepseek-chat
Mode    : cheap (300 max tokens)
Errors  : 0 across all five-level baseline runs
Created : 2026-05-01
Status  : research artifact — not a product benchmark
```
