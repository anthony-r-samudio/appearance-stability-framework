# Gemma4:26b Judge Calibration v0.2

## Status and evidence limits

Gemma4:26b remains a candidate judge, not a qualified evidence judge.

VERIFIED configuration and completion facts below are supported by the
preserved run manifests, run summaries, and diagnostic RUN_NOTE.md.

Gold-comparison counts retained from the previous report and external
diagnostic analysis are REPORTED, pending reproduction from the frozen
inputs and results.jsonl files. The external comparison script and its
output were not part of the repository at this review checkpoint.

Interpretations are labeled INFERRED. Proposed work is labeled PROPOSED.

## Run identities and completion

All result directories below are relative to `results/`.
Directory names are preserved; the short labels are report aliases only.

| Label | Result directory | Attempted | Valid | Errors |
|---|---|---:|---:|---:|
| Base run01 | `gemma4_26b_run01` | 14 | 6 | 8 |
| Guidance run02 | `gemma4_26b_run02_guidance_bundle` | 14 | 7 | 7 |
| Guidance recovery03 | `gemma4_26b_run03_recovery_3200` | 6 | 2 | 4 |
| Guidance recovery04 | `gemma4_26b_run04_recovery_ctx16384` | 4 | 1 | 3 |
| Guidance C7 diagnostic | `gemma4_26b_c7_01_timeout1800_diagnostic` | 1 | 1 | 0 |
| Base-budget diagnostic | `gemma4_26b_run02_tokens3584_timeout1500` | 14 | 12 | 2 |

Recovery runs use selected subsets. Their completion rates must not be
treated as independent full-dataset comparisons or pooled as unique cases.

## Configuration and provenance (VERIFIED)

All listed runs use `gemma4:26b`, temperature 0, JSON format,
one repeat, and zero retries.

| Label | max_tokens | num_ctx | Timeout seconds | Boundary profile |
|---|---:|---:|---:|---|
| Base run01 | 1600 | 8192 | 600 | Base |
| Guidance run02 | 1600 | 8192 | 600 | Guidance |
| Guidance recovery03 | 3200 | 8192 | 900 | Guidance |
| Guidance recovery04 | 3200 | 16384 | 900 | Guidance |
| Guidance C7 diagnostic | 3200 | 16384 | 1800 | Guidance |
| Base-budget diagnostic | 3584 | 8192 | 1500 | Base |

Boundary-notes SHA-256:

- Base: `d3c4c1d640f5012eab8edd1d3788f0e6f39fabbc96280a5b9a2177f8eec6da81`
- Guidance: `735e8d0f73dfd38090de821ffa68d8296bfbb9418c2a1207c7cbc8c02ca9c2c4`

The guidance run, both guidance recoveries, and the guidance C7 diagnostic
share the guidance boundary-notes hash. Their manifests also show matching
prompt hashes for overlapping cases.

The base-budget diagnostic did not use the guidance bundle. Its RUN_NOTE.md
records that all 14 prompt hashes, input, boundary notes, runner, and scorer
match base run01.

Base run01 records source commit `86afad6`; the later runs record `632cada`.
The diagnostic note documents identical relevant code and input hashes
despite the source-commit difference.

Base run01 to base-budget diagnostic changes TWO execution parameters:
max_tokens from 1600 to 3584, and timeout from 600 to 1500 seconds.
This is not a strict one-variable experiment.

## Reported gold comparisons

The following counts are retained from the earlier report and external
diagnostic analysis; they require an in-repository reproduction.

| Label | Exact vectors / valid rows | Matching cells / valid cells |
|---|---:|---:|
| Base run01 | 6/6 | 60/60 |
| Guidance recovery03 | 2/2 | 20/20 |
| Guidance recovery04 | 1/1 | 10/10 |
| Base-budget diagnostic | 10/12 | 118/120 |

No complete gold-comparison count is established here for guidance run02.
The guidance C7 diagnostic is discussed below as a reported attribution
result, not as an exact-match success.

## Base-budget diagnostic

VERIFIED completion:

- 14 attempted, 12 valid, 2 errors.
- `cal_c4_01`: output-token limit; eval_count 3584, done_reason length.
- `cal_c7_02`: timeout at 1500 seconds.

REPORTED scoring:

- All 12 valid rows scored the intended target constraint 0.
- Ten valid rows matched the entire gold vector.
- `cal_c4_02`: C4 = 0, with off-target C7 = 0.5 instead of 1.
- `cal_c7_01`: C7 = 0, with off-target C4 = 0.5 instead of 1.
- The six cases completed in base run01 retained identical score vectors.

| Metric | Value | Denominator or policy |
|---|---:|---|
| Completion | 12/14 = 85.71% | All attempted rows |
| Full-vector exact | 10/12 = 83.33% | Valid rows only |
| End-to-end exact yield | 10/14 = 71.43% | All attempted rows |
| Exact target detection | 12/12 = 100% | Valid rows only |
| End-to-end target yield | 12/14 = 85.71% | All attempted rows |
| Cell agreement | 118/120 = 98.33% | Valid rows only |
| Correct-cell yield | 118/140 = 84.29% | Incomplete rows receive zero credit |
| Off-target false failures | 2/108 = 1.85% | Valid off-target cells only |

An incomplete row has no observed score vector. Giving it zero credit in
an end-to-end yield metric is an evaluation policy, not an observed scoring
error in every cell.

## All-ones baseline and class imbalance

REPORTED dataset structure: 14 single-failure cases, each with one gold
constraint at 0 and nine at 1; no clean controls or 0.5 gold labels.

Under that structure, a constant all-ones baseline achieves:

- Cell agreement: 126/140 = 90%.
- Exact target detection: 0/14.
- Full-vector exact match: 0/14.
- Off-target false failures: 0.

The baseline exposes why cell agreement and off-target false failures
cannot serve alone as judge-quality measures.

The diagnostic's 98.33% cell agreement applies only to completed rows.
Its 84.29% correct-cell yield includes incomplete rows receiving zero
credit. These are different metrics and must be labeled separately.

Prioritize completion, target detection, full-vector exact match, and
off-target errors together.

## Completion budgets and context limits

VERIFIED: completion increased from 6/14 in base run01 to 12/14 in the
base-budget diagnostic, with identical scoring prompts but larger output
and timeout allowances.

INFERRED: the combined execution allowances relieved substantial
completion censoring. Their individual causal contributions are not
isolated by this comparison.

REPORTED: both recovered C3 cases used more than 1600 generated tokens
and matched gold exactly. This is consistent with the old output ceiling
having prevented those successful trajectories from completing.

The guidance recoveries are not direct tests of the base prompt's budget.
They use a different boundary profile and selected difficult cases.

The earlier external analysis estimated guidance prompts at roughly 6300
tokens. If representative, an 8192-token context would leave roughly 1890
tokens before accounting for other overhead, potentially restricting a
requested 3200-token generation allowance.

That estimate is not verified by the manifests alone. Confirm actual
prompt_eval_count and context behavior from preserved responses before
stating an effective generation ceiling.

Recovery04 completed one of four selected cases at num_ctx 16384. This
does not establish that increasing context cannot help: subset selection,
timeouts, runtime behavior, and lack of repeats limit the conclusion.

## Observed variation under temperature 0

REPORTED: the two C9 cases completed in roughly 1260 generated tokens in
the base-budget diagnostic, whereas their identical run01 prompts did
not complete within 1600 tokens. A C6 case also changed token count while
retaining its scores.

INFERRED: temperature 0 did not produce identical execution trajectories
across these runs. The C9 recovery cannot be attributed solely to the
larger output-token allowance.

The mechanism and score-vector repeat variance remain unmeasured.
Runtime behavior, numerical variation, and execution conditions may
contribute. Controlled same-configuration repeats are still required.

## C4/C7 boundary question

REPORTED: the completed base-budget cases show reciprocal partial
cross-attribution between C4 and C7.

REPORTED: the guidance C7 diagnostic scored `cal_c7_01` as C4 = 0 and
C7 = 0.5, reversing the primary attribution seen in the base-budget run.

INFERRED: these results identify an unresolved attribution problem.
They do not establish whether the cause is overlapping definitions,
ambiguous cases, insufficient boundary guidance, or judge instability.
Guidance and execution settings also differ between those diagnostics.

Do not revise C4/C7 definitions solely because this judge confused them.

## Current verdict

CANDIDATE JUDGE - NOT QUALIFIED.

Reported target detection is encouraging, but two incomplete cases,
reciprocal C4/C7 cross-attribution, limited case coverage, and unmeasured
repeat variance prevent qualification.

These results describe judge calibration on this dataset. They do not
establish broad validity of AOSL or suitability for unrestricted
evidence-generation use.

## Next steps (PROPOSED)

1. Preserve all existing run directories and raw artifacts unchanged.
2. Reproduce gold comparisons from frozen inputs and results in the repo.
3. Audit C4/C7 definitions, boundary notes, gold rationales, and reasoning
   for cal_c4_02, cal_c7_01, and the guidance C7 diagnostic.
4. Classify the attribution problem before changing cases or definitions.
5. Design controlled repeats after the boundary audit.
6. Freeze qualification criteria before a subsequent judge comparison.
