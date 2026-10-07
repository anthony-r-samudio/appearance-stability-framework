# RUN_NOTE: gemma4_26b_run02_tokens3584_timeout1500

## Status of this run

Controlled diagnostic. **Not a strict one-variable replication of run01.**
Not evidence that gemma4:26b is a qualified AOSL judge.

## Question

Were the 8 incomplete rows in `gemma4_26b_run01` failing because of the
1,600-token output budget, or because the neighbouring constraint boundaries
(C3/C7, C4/C7, C1/C8/C9) are difficult to distinguish?

## Differences from gemma4_26b_run01 (two execution parameters)

| parameter | run01 | this run |
|---|---|---|
| max_tokens | 1600 | 3584 |
| timeout_seconds | 600 | 1500 |

Rationale for the timeout change: run01 generated roughly 4.0-4.8 tokens/s,
and earlier local evidence (a 900 s run losing rows to timeouts; a single-row
diagnostic needing 3,010 tokens and 1,534 s) indicated that a 600 s timeout
would likely censor difficult rows before they could use the larger output
budget. The timeout was therefore raised as a non-scoring execution allowance
so that max_tokens could actually be tested. The intent is to remove two known
truncation mechanisms: output-token exhaustion and wall-clock timeout.

The source_commit also differs (run01: 86afad6; this run: 632cada). The commits
between them add files that this run does not use (the guidance bundle and the
v0.2 run01 preservation); runner, scorer, input and boundary-notes hashes are
identical to run01.

## Held constant (verified before launch, see run_manifest.json)

- Input: `04_RUNS/judge_calibration_v0_2/inputs/calibration_cases_v0_2.csv`,
  sha256 884044af0f59b681622b6e2ae420fd892666a0e4d7e33f9f9c765f798b52c2da, 14 rows
- Boundary notes: `01_CANON/AOSL_CONSTRAINT_BOUNDARY_NOTES_v0.1.md`,
  sha256 d3c4c1d640f5012eab8edd1d3788f0e6f39fabbc96280a5b9a2177f8eec6da81
- Guidance bundle `JUDGE_BOUNDARY_GUIDANCE_v0_2.md`: NOT used
- No new decision rules; gold labels and frozen inputs unmodified
- Model: gemma4:26b, digest 08ae7ec1744bd7f451c4a530afb39d2673ad9d07a8369b8a33a3613b41212a68 (Q4_K_M)
- Ollama 0.35.1; temperature 0; num_ctx 8192; format json; 1 repeat; 0 retries
- Runner sha256 9f799992...; scorer sha256 c9b018fd...
- All 14 prompt_sha256 values identical to run01 (same scoring prompt)

## Execution

- Launched 2026-10-07 13:17:20 Europe/Zurich (11:17:20 UTC) on ZBOOK, detached process.
- Working tree at launch had untracked local runs (gemma4_26b_run02_guidance_bundle,
  gemma4_26b_run03_recovery_3200, gemma4_26b_run04_recovery_ctx16384,
  gemma4_26b_c7_01_timeout1800_diagnostic and their recovery inputs). They were
  not touched and are not part of this run; see git_status in run_manifest.json.
- results.jsonl last written 2026-10-07 16:37 Europe/Zurich.

## Raw outcome (run_summary.json)

14 rows, 12 valid, 2 errors:
- cal_c4_01: token limit reached (eval_count 3584, done_reason=length)
- cal_c7_02: TimeoutError at 1500 s (no response file)

Gold comparison was computed afterwards by a scratch script outside the
repository; its numbers are not canonical until reviewed.
