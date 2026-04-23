# AOSL Progress Log

## Current Status
AOSL Phase 1 operational prototype, pilot1 workflow, and prompt-file pipeline are verified working end-to-end.

## Environment
- OS: Windows
- Editor: VS Code
- Repo root: `AOSL - ENGINE`
- Package install command: `py -m pip install -e .`

## Canonical Constraint Set
- c1 = Factual Grounding
- c2 = Logical Coherence
- c3 = Causal Integrity
- c4 = Epistemic Calibration
- c5 = Scope Discipline
- c6 = Safety Integrity
- c7 = Uncertainty Acknowledgment
- c8 = Quantitative Accuracy
- c9 = Evidence Traceability
- c10 = Constraint Interaction Consistency

## Implemented Modules

### AOSL/constraints
- `definitions.py`
- `__init__.py`

Implemented:
- `Constraint`
- `CONSTRAINTS`
- `BY_CODE`

### AOSL/scoring
- `schema.py`
- `validation.py`
- `examples.py`
- `builders.py`
- `serialization.py`
- `io.py`
- `flatten.py`
- `csv_io.py`
- `__init__.py`

Implemented:
- `ScoredOutput`
- `validate_scores(...)`
- `validate_output(...)`
- `find_unknown_codes(...)`
- `find_missing_codes(...)`
- `find_out_of_range_scores(...)`
- `ValidationResult`
- `EXAMPLE_OUTPUT`
- `make_scored_output(...)`
- `to_dict(...)`
- `to_json(...)`
- `save_to_json(...)`
- `load_from_json(...)`
- `save_many_to_json(...)`
- `load_many_from_json(...)`
- `save_many_to_csv(...)`
- `to_flat_row(...)`
- `to_flat_rows(...)`

## Prompt Files

- `02_PROMPTS/pilot1_prompts.jsonl` — 5 prompts in JSONL format (prompt_id, text)

## Implemented Scripts

### Demo Scripts
- `05_SRC/scripts/demo_scoring_flow.py`
- `05_SRC/scripts/demo_batch_flow.py`
- `05_SRC/scripts/run_phase1_demo.py`

### Demo Analysis Scripts
- `05_SRC/analysis/demo_batch_summary.py`
- `05_SRC/analysis/demo_batch_table.py`
- `05_SRC/analysis/demo_batch_export.py`
- `05_SRC/analysis/demo_batch_stats.py`
- `05_SRC/analysis/demo_validation_report.py`

### Pilot 1 Scripts
- `05_SRC/scripts/demo_pilot1_run.py`
- `05_SRC/scripts/run_pilot1_demo.py`
- `05_SRC/scripts/run_pilot1_prompt_pipeline.py`
- `05_SRC/scripts/run_pilot1_prompt_pipeline_demo.py`

### Pilot 1 Analysis Scripts
- `05_SRC/analysis/pilot1_summary.py`
- `05_SRC/analysis/pilot1_table.py`
- `05_SRC/analysis/pilot1_export.py`
- `05_SRC/analysis/pilot1_report_export.py`
- `05_SRC/analysis/pilot1_prompt_pipeline_summary.py`
- `05_SRC/analysis/pilot1_prompt_pipeline_table.py`

## Verified Working
Confirmed in terminal:
- `import AOSL` works
- constraint definitions import correctly
- scoring schema imports correctly
- validation works
- example output validates
- JSON save/load works
- many-output JSON save/load works
- CSV export works
- flattening works
- demo single flow works
- demo batch flow works
- batch summary analysis works
- batch table analysis works
- batch export to CSV works
- per-constraint stats (mean, min, max) works
- validation report works
- full Phase 1 demo runner works
- pilot1 batch created and saved to 04_RUNS/pilot1/
- pilot1 summary analysis works
- pilot1 table view works
- pilot1 CSV export works
- pilot1 report exported to 06_OUTPUTS/pilot1_summary.txt
- full pilot1 demo runner works
- prompt-file pipeline reads pilot1_prompts.jsonl and saves batch to 04_RUNS/pilot1/
- pilot1 prompt pipeline summary analysis works
- pilot1 prompt pipeline table view works
- full pilot1 prompt pipeline demo runner works

## Current State Summary
The project has:
- a working core domain layer
- working demo workflows
- working demo analysis scripts (summary, table, export, stats, validation report)
- a working pilot1 workflow (run, summary, table, export, report export)
- a working prompt-file pipeline (reads JSONL prompts, builds ScoredOutput, saves JSON and CSV)
- analysis scripts for the prompt pipeline batch (summary, table)
- runner scripts for the Phase 1 demo, pilot1, and prompt pipeline sequences
