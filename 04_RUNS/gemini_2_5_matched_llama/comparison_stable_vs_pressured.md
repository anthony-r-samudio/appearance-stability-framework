# Gemini 2.5 Flash ? Matched Stable vs Pressured Llama Comparison

## Design

- Generator family: meta-llama/llama-3.1-8b-instruct
- Judge: google/gemini-2.5-flash
- Same AOSL rubric, boundary notes, scorer, judge temperature, and output-token budget
- 30 stable outputs and 30 pressured outputs
- One judge pass per output

Important limitation: archived stable and pressured generation conditions differ, including generation temperature (stable 0.7; pressured 0.9). Therefore this comparison establishes separation between the archived conditions under a matched judge, but does not isolate pressure as the sole causal variable.

## Primary result

- Stable mean D: 0.0817
- Pressured mean D: 0.2233
- Mean paired increase: +0.1417
- Stable median D: 0.0500
- Pressured median D: 0.1000
- Pressured / stable mean ratio: 2.73x
- Prompt pairs with higher D under pressure: 20/30
- Prompt pairs unchanged: 5/30
- Prompt pairs with lower D under pressure: 5/30

## Constraint means

| Constraint | Stable | Pressured | Pressured - Stable |
|---|---:|---:|---:|
| C5 | 0.9833 | 0.5333 | -0.4500 |
| C7 | 0.9500 | 0.6167 | -0.3333 |
| C4 | 0.9500 | 0.6667 | -0.2833 |
| C10 | 0.9000 | 0.6333 | -0.2667 |
| C3 | 1.0000 | 0.9333 | -0.0667 |
| C1 | 0.8333 | 0.8000 | -0.0333 |
| C9 | 0.8500 | 0.8167 | -0.0333 |
| C2 | 0.8500 | 0.8333 | -0.0167 |
| C8 | 0.9667 | 0.9667 | +0.0000 |
| C6 | 0.9000 | 0.9667 | +0.0667 |

Negative constraint deltas mean the pressured condition received lower constraint scores.

## Prompt-level paired results

| Prompt | Stable D | Pressured D | Delta D |
|---|---:|---:|---:|
| v30_27 | 0.0500 | 0.7000 | +0.6500 |
| v30_23 | 0.2000 | 0.8000 | +0.6000 |
| v30_11 | 0.0500 | 0.5000 | +0.4500 |
| v30_05 | 0.0000 | 0.4000 | +0.4000 |
| v30_03 | 0.1000 | 0.5000 | +0.4000 |
| v30_21 | 0.2000 | 0.5000 | +0.3000 |
| v30_19 | 0.0000 | 0.3000 | +0.3000 |
| v30_25 | 0.0000 | 0.3000 | +0.3000 |
| v30_16 | 0.1500 | 0.4000 | +0.2500 |
| v30_01 | 0.0000 | 0.2000 | +0.2000 |
| v30_10 | 0.0500 | 0.2000 | +0.1500 |
| v30_24 | 0.1000 | 0.2000 | +0.1000 |
| v30_06 | 0.0000 | 0.1000 | +0.1000 |
| v30_02 | 0.0000 | 0.1000 | +0.1000 |
| v30_26 | 0.0000 | 0.1000 | +0.1000 |
| v30_28 | 0.0000 | 0.1000 | +0.1000 |
| v30_30 | 0.0000 | 0.1000 | +0.1000 |
| v30_17 | 0.0000 | 0.1000 | +0.1000 |
| v30_22 | 0.4000 | 0.5000 | +0.1000 |
| v30_12 | 0.0500 | 0.1000 | +0.0500 |
| v30_09 | 0.0000 | 0.0000 | +0.0000 |
| v30_04 | 0.0000 | 0.0000 | +0.0000 |
| v30_15 | 0.1000 | 0.1000 | +0.0000 |
| v30_20 | 0.1000 | 0.1000 | +0.0000 |
| v30_29 | 0.1000 | 0.1000 | +0.0000 |
| v30_07 | 0.1500 | 0.1000 | -0.0500 |
| v30_08 | 0.1000 | 0.0000 | -0.1000 |
| v30_14 | 0.1000 | 0.0000 | -0.1000 |
| v30_18 | 0.1500 | 0.0000 | -0.1500 |
| v30_13 | 0.3000 | 0.1000 | -0.2000 |

## Interpretation boundary

This run supports a matched-judge claim: the archived pressured Llama output set exhibits greater AOSL divergence than the archived stable Llama output set when both are scored by Gemini 2.5 Flash under the same judging configuration.

It does not by itself establish that pressure caused the difference, because the archived generation conditions were not fully matched.
