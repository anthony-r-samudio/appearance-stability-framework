# Gemma4:26b Judge Calibration v0.2



## Status



VERIFIED experimental summary of Gemma4:26b local judge calibration runs.



## Run comparison



| Run | Attempted | Valid | Errors | Exact valid rows | Exact rate | Constraint agreement |

|---|---:|---:|---:|---:|---:|---:|

| run01 | 14 | 6 | 8 | 6/6 | 100% | 60/60 = 100% |

| run02 | 14 | 12 | 2 | 10/12 | 83.33% | 118/120 = 98.33% |

| run03 | 6 | 2 | 4 | 2/2 | 100% | 20/20 = 100% |

| run04 | 4 | 1 | 3 | 1/1 | 100% | 10/10 = 100% |



## Run01



- 14 rows attempted.

- 6 valid judgments.

- 8 errors.

- All valid judgments exactly matched the frozen gold scores.

- Main limitation: high rate of incomplete or token-limited responses.



## Run02



Configuration:



- model: `gemma4:26b`

- temperature: `0`

- `num\_ctx`: `8192`

- `max\_tokens`: `3584`

- timeout: `1500 s`

- 14 rows attempted.



Results:



- 12 valid judgments.

- 2 errors.

- 10 of 12 valid rows matched all ten gold constraint scores exactly.

- 118 of 120 individual constraint scores matched gold.

- Per-score agreement: 98.33%.

- Exact-row agreement among valid rows: 83.33%.

- End-to-end exact yield: 10/14 = 71.43%.



Operational failures:



- `cal\_c4\_01`: incomplete or token-limited response.

- `cal\_c7\_02`: timeout.



Scoring mismatches:



- `cal\_c4\_02`: expected `c7 = 1`, actual `c7 = 0.5`.

- `cal\_c7\_01`: expected `c4 = 1`, actual `c4 = 0.5`.



These mismatches indicate a possible C4/C7 boundary interaction rather than broad scoring instability.



## Run03



- Targeted recovery run.

- 6 rows attempted.

- 2 valid.

- 4 errors.

- Both valid rows exactly matched gold.

- Increasing the generation allowance did not improve operational reliability.



## Run04



- Recovery run with `num\_ctx = 16384`.

- 4 rows attempted.

- 1 valid.

- 3 timeouts.

- The single valid row exactly matched gold.

- Increasing context size did not solve the operational failures.



## Interpretation



VERIFIED:



- Gemma4:26b shows very high scoring fidelity when it returns a valid judgment.

- Run02 is the strongest configuration tested so far.

- Run02 achieved 98.33% individual constraint-score agreement on valid rows.

- The only valid scoring deviations were reciprocal C4/C7 half-score attributions.

- Larger token or context budgets did not reliably improve completion.

- Operational reliability remains substantially weaker than scoring fidelity.



INFERRED:



- The C4/C7 deviations may reflect a genuine rubric-boundary ambiguity rather than random judge failure.

- Gemma4:26b is promising as a calibration judge, but the current CPU-only local deployment is not reliable enough for unrestricted evidence-generation use.



## Current verdict



\*\*KEEP FOR CALIBRATION / CONDITIONAL JUDGE\*\*



Do not treat Gemma4:26b as a fully qualified production evidence judge yet.



## Next steps



1\. Freeze run01-run04 as evidence.

2\. Review the C4/C7 boundary definitions.

3\. Avoid further parameter sweeps until the rubric boundary is examined.

4\. Preserve the run artifacts and provenance.

5\. Compare Gemma against the other local judges only after this calibration state is documented.


