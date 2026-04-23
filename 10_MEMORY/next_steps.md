# AOSL Next Steps

## Current State
Prompt-file pipeline is verified end-to-end. Pilot1 workflow is complete. All runner scripts are working.

## Next: Real Scoring

The pipeline infrastructure is in place. The next meaningful step is replacing placeholder scores with real scored outputs.

### Scoring
- [ ] Replace placeholder scores in `run_pilot1_prompt_pipeline.py` with real model outputs and scores
- [ ] Add real output_text from a model response

### Data
- [ ] Add scored outputs to `03_DATA/scored/` once real scoring is in place

### Package Stubs (implement only when explicitly requested)
- [ ] `AOSL/eval/` — no scope defined yet
- [ ] `AOSL/storage/` — no scope defined yet
- [ ] `AOSL/API/` — no scope defined yet

## Deferred
- Divergence logic — not requested
- Evaluator logic — not requested
