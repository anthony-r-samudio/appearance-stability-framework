from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "04_RUNS" / "pilot1" / "pilot1_manual_output_README.txt"

README = """\
Pilot 1 Manual Output — Run Artifacts
======================================

Purpose
-------
This folder contains scored output artifacts from the pilot1 manual-output
pipeline. Outputs were built from manually written model responses paired
with prompts from 02_PROMPTS/pilot1_prompts.jsonl. Scores are placeholder
values pending real evaluation.

Artifacts
---------
pilot1_manual_output_batch.json
    Source batch file. Contains all ScoredOutput records in JSON format.

pilot1_manual_output_table.csv
    Flat CSV export of the batch. One row per output. Columns: prompt_id,
    model_name, output_text, notes, c1 through c10.

pilot1_manual_output_report.txt
    Plain text summary report. Shows per-constraint mean scores across
    all outputs in the batch.

Analysis Scripts (05_SRC/analysis/)
-------------------------------------
pilot1_manual_output_check.py
    Validates that the batch file exists and all outputs contain required
    fields and canonical constraint score keys c1 through c10.

pilot1_manual_output_manifest.py
    Lists expected artifacts and whether each file exists. Prints loaded
    outputs and prompt_ids. Ends with PASS or FAIL.

pilot1_manual_output_overview.py
    Prints a compact terminal overview: total outputs, model names,
    prompt_ids, and score columns present.

pilot1_manual_output_summary.py
    Computes and prints per-constraint mean scores in canonical c1-c10 order.

pilot1_manual_output_table.py
    Prints a compact terminal table: prompt_id, model_name, and c1-c10 scores.

pilot1_manual_output_export.py
    Exports the batch to pilot1_manual_output_table.csv.

pilot1_manual_output_report_export.py
    Exports the per-constraint summary to pilot1_manual_output_report.txt.

run_pilot1_manual_output_analysis.py
    Runs: check, summary, table, export, report export in sequence.

run_pilot1_manual_output_full.py
    Runs: overview, summary, table, export, report export in sequence.

run_pilot1_manual_output_verified.py
    Runs: check, overview, summary, table, export, report export in sequence.

run_pilot1_manual_output_release_check.py
    Runs: check, manifest, overview, summary, table in sequence.
"""


def main():
    OUTPUT_PATH.write_text(README, encoding="utf-8")
    print(f"README written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
