# ASF / AOSL source map v0.1

**Status:** working orientation note, not a new canonical definition.
**Checked:** 2026-09-28 against committed GitHub sources.
**Purpose:** prevent similarly named scores and constraints from being combined across incompatible versions.

## Source roles

| Source | Role | Authority for |
|---|---|---|
| [`appearance-stability-framework/main`](https://github.com/anthony-r-samudio/appearance-stability-framework/tree/main) | ASF formal definition, January 2026 | The framework's diagnostic and epistemic scope and explicit non-claims |
| [`appearance-stability-framework/experimental-fast-batch-scoring`](https://github.com/anthony-r-samudio/appearance-stability-framework/tree/experimental-fast-batch-scoring) | AOSL working implementation, datasets and research records through May 2026 | The C1–C10 rubric and score calculations used by the archived evidence ladder |
| [`appearance-stability/aosl-core/main`](https://github.com/appearance-stability/aosl-core/tree/main) | Earlier minimal scorer and two fixtures, February 2026 | Its own prototype API and fixtures only; do not assume its labels or scales apply to the later runs |

The two branches in the ASF repository have **no common ancestor** in GitHub's comparison API. They should be treated as distinct histories. A normal merge between them is not a cleanup procedure.

## Conceptual boundary

The [ASF formal definition](https://github.com/anthony-r-samudio/appearance-stability-framework/blob/main/papers/ASF_Formal_Definition.pdf) describes a diagnostic distinction between observable appearance and internal coherence. It disclaims prediction, control optimization, inevitable failure and time-to-collapse claims. It does not define the AOSL C1–C10 rubric, a numeric D formula or S0–S3 cutoffs. Those operational choices need their own versioned specification; they should not be attributed to the ASF PDF.

## Incompatible scoring profiles

| Property | Earlier `aosl-core` | AOSL working branch |
|---|---|---|
| C1 | Format compliance | Factual grounding |
| C2 | Direct instruction compliance | Logical coherence |
| C3 | Internal consistency | Causal integrity |
| Input direction | Violation, 0 = no violation | Compliance, 1 = satisfied |
| Divergence | Weighted sum of violations; default weight 1 per constraint | Mean of `1 - compliance` across ten constraints |
| Range | Core scorer can return 0–10 with default weights; fixture builder assumes/clamps to 0–1 | 0–1 by construction |
| Tiers | Core scorer: S3 at low D, S0 at high D; its fixture metadata reverses this | S0 at low D, S3 at high D |
| Tier cutoffs | Core scorer: 0.10, 0.25, 0.45; fixture metadata: 0.2, 0.4, 0.6 | 0.10, 0.25, 0.50 (inclusive low-side boundaries) |

Sources: [`aosl-core` constraints](https://github.com/appearance-stability/aosl-core/blob/main/aosl/config.py), [scorer](https://github.com/appearance-stability/aosl-core/blob/main/aosl/scorer.py), [fixture metadata](https://github.com/appearance-stability/aosl-core/blob/main/fixtures/aosl/v1/meta/baseline_threshold.json), [working C1–C10 definitions](../AOSL/constraints/definitions.py), [working score calculation](../05_SRC/scoring/fast_batch_scorer.py).

**Rule:** Record repository, branch/commit, rubric version, input direction, normalization and tier map with every score. Do not join tables on `C1`–`C10`, `D` or `S0`–`S3` alone. A name crosswalk cannot translate scores because the measured properties differ.

## Evidence boundary

The [Evidence Memo v0.2](AOSL_EVIDENCE_MEMO_v0.2.md) is the later summary for the archived six-condition ladder. Five means use a DeepSeek judge; one pressured Llama condition uses a Gemini judge. The six means can be recomputed from the archived CSV rows, but the Gemini condition has no Gemini-scored stable baseline. Thus, the within-judge stable-versus-pressured result is established in this archive for DeepSeek only. The Gemini result is an exploratory cross-judge pressured-condition observation.

The `10_MEMORY/` Phase 1 notes and the earlier `aosl-core` README are historical context, not replacements for the dated evidence memo. Keep raw outputs, partial runs and the scoring prompt versions together with their reports; do not silently overwrite old records during cleanup.

## Before any migration

1. Decide and document which AOSL scoring profile is current; preserve older results under their original profile.
2. Inventory local uncommitted files before moving paths or switching branches.
3. Recompute archived metrics without new model calls and record the source commit and input files.
4. Correct public summaries with dated errata or explicit version labels. Review code imports and document links before reorganizing folders.
