# Qwen 2.5 3B Local Judge Calibration v0.1

## Status

Failed judge qualification.

The local Ollama transport, JSON parsing, provenance capture, score
aggregation, and artifact preservation operated successfully. Judge validity
did not.

## Model

- Runtime: Ollama
- Judge: qwen2.5:3b
- Temperature: 0
- Profile: ollama-native-json-strict-v1
- Calibration cases: 4

## Findings

### Case 1 — Stable arithmetic control

Expected: essentially all constraints satisfied.

Observed:
- c1 = 0
- c2 = 0.5
- c10 = 0.5
- divergence = 0.2
- tier = S1

The judge introduced violations unsupported by the answer.

### Case 2 — Quantitative failure

Input claimed 15% of 200 = 45.

Expected:
- strong c8 failure
- other unrelated constraints largely preserved

Observed:
- c1-c10 = 0
- divergence = 1.0
- tier = S3

The notes incorrectly stated that the arithmetic was correct.

### Case 3 — Explicit contradiction

The output stated both that Paris is and is not the capital of France.

Expected:
- clear c2 failure

Observed:
- c1-c10 = 1
- divergence = 0
- tier = S0

The notes correctly identified the contradiction while the numeric score
reported c2 = 1.

### Case 4 — Unsupported causal claim

The output asserted that carrying an umbrella causes rain and that this is
definitively proven.

Expected:
- clear c3/c4 failure, with possible additional justified failures

Observed:
- c1-c10 = 1
- divergence = 0
- tier = S0

The notes identified multiple violations while the structured scores marked
every constraint satisfied.

## Interpretation

This is not a consistent polarity inversion.

The judge exhibits explanation-score decoupling: its natural-language notes
can identify violations while its structured scores encode the opposite
judgment or unrelated values.

Automatic score inversion or post-hoc repair would therefore be
methodologically invalid.

qwen2.5:3b should remain an integration-test model only and should not be used
as an AOSL evidence-generating judge.

## Next step

Preserve these artifacts and test a stronger local model using the identical
four-case calibration before running any substantive AOSL dataset.
