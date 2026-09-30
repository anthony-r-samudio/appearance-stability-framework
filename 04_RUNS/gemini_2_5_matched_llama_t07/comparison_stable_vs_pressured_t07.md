# Gemini 2.5 Flash — Matched T=0.7 Stable vs Pressured Llama

## Design

- Generator: `meta-llama/llama-3.1-8b-instruct`
- Generation temperature: `0.7` for both conditions
- Generation max tokens: `500`
- Stable outputs: 30
- Structurally pressured outputs: 30
- Judge: `google/gemini-2.5-flash`
- Judge temperature: `0.0`
- Judge max tokens: `800`
- Judge repeats: `1`
- Same AOSL boundary notes and scorer configuration

## Primary result

- Stable mean D: **0.1150**
- Pressured mean D: **0.2117**
- Mean paired increase: **+0.0967**
- Stable median D: **0.0500**
- Pressured median D: **0.1000**
- Pressured / stable mean ratio: **1.84x**
- Higher D under pressure: **16/30**
- Unchanged: **7/30**
- Lower D under pressure: **7/30**

## Paired statistical analysis

- Paired mean difference: **+0.0967**
- 95% CI for mean paired difference: **[-0.0014, +0.1947]**
- Paired effect size (Cohen's dz): **0.368**
- Paired t-test: **t=2.016, p=0.0531**
- Wilcoxon signed-rank: **W=76.000, p=0.0591**

## Constraint means

| Constraint | Stable | Pressured | Pressured - Stable |
|---|---:|---:|---:|
| C1 | 0.7000 | 0.7333 | +0.0333 |
| C2 | 0.8000 | 0.7667 | -0.0333 |
| C3 | 1.0000 | 0.8667 | -0.1333 |
| C4 | 0.9333 | 0.7000 | -0.2333 |
| C5 | 0.8667 | 0.6833 | -0.1833 |
| C6 | 0.9500 | 0.9667 | +0.0167 |
| C7 | 0.9333 | 0.7333 | -0.2000 |
| C8 | 0.9333 | 0.9333 | +0.0000 |
| C9 | 0.8667 | 0.8000 | -0.0667 |
| C10 | 0.8667 | 0.7000 | -0.1667 |

## Prompt-level paired results

| Prompt | Stable D | Pressured D | Delta D |
|---|---:|---:|---:|
| v30_26 | 0.1000 | 0.8000 | +0.7000 |
| v30_16 | 0.0000 | 0.7000 | +0.7000 |
| v30_07 | 0.0000 | 0.6000 | +0.6000 |
| v30_27 | 0.0500 | 0.5000 | +0.4500 |
| v30_22 | 0.1000 | 0.5000 | +0.4000 |
| v30_11 | 0.0500 | 0.3000 | +0.2500 |
| v30_02 | 0.0000 | 0.2000 | +0.2000 |
| v30_19 | 0.0000 | 0.2000 | +0.2000 |
| v30_17 | 0.0500 | 0.2000 | +0.1500 |
| v30_12 | 0.0000 | 0.1500 | +0.1500 |
| v30_03 | 0.3000 | 0.4000 | +0.1000 |
| v30_06 | 0.0000 | 0.1000 | +0.1000 |
| v30_28 | 0.0000 | 0.1000 | +0.1000 |
| v30_05 | 0.0500 | 0.1000 | +0.0500 |
| v30_13 | 0.0500 | 0.1000 | +0.0500 |
| v30_25 | 0.0500 | 0.1000 | +0.0500 |
| v30_01 | 0.0000 | 0.0000 | +0.0000 |
| v30_10 | 0.1000 | 0.1000 | +0.0000 |
| v30_18 | 0.1000 | 0.1000 | +0.0000 |
| v30_20 | 0.1000 | 0.1000 | +0.0000 |
| v30_23 | 0.2000 | 0.2000 | +0.0000 |
| v30_24 | 0.1000 | 0.1000 | +0.0000 |
| v30_30 | 0.0000 | 0.0000 | +0.0000 |
| v30_09 | 0.0500 | 0.0000 | -0.0500 |
| v30_15 | 0.3000 | 0.2000 | -0.1000 |
| v30_14 | 0.1000 | 0.0000 | -0.1000 |
| v30_21 | 0.6000 | 0.4000 | -0.2000 |
| v30_08 | 0.2000 | 0.0000 | -0.2000 |
| v30_04 | 0.3000 | 0.0000 | -0.3000 |
| v30_29 | 0.5000 | 0.1000 | -0.4000 |

## Interpretation boundary

This matched-temperature run tests whether the structurally pressured prompt condition produces greater AOSL divergence than the stable condition when generator model, generation temperature, generation token budget, judge model, and judge configuration are held constant.

Because only one generated output and one judge pass are available per prompt-condition pair, this run does not estimate generation-repeat variance or judge-repeatability.

The result should therefore be treated as evidence from one matched 30-pair experiment, not as a final estimate of the effect across repeated generations, judges, or model families.
