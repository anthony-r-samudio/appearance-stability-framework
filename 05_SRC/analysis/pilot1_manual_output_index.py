from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "04_RUNS" / "pilot1" / "pilot1_manual_output_INDEX.txt"

INDEX = """\
Pilot 1 Manual Output — Index
==============================

Artifacts (04_RUNS/pilot1/)
----------------------------
pilot1_manual_output_batch.json   Source batch. All ScoredOutput records in JSON.
pilot1_manual_output_table.csv    Flat CSV export. One row per output.
pilot1_manual_output_report.txt   Per-constraint mean score summary.
pilot1_manual_output_README.txt   Artifact and script reference guide.

Analysis Scripts (05_SRC/analysis/)
-------------------------------------
pilot1_manual_output_check.py         Validates batch file and required fields.
pilot1_manual_output_manifest.py      Checks artifact existence. Prints PASS/FAIL.
pilot1_manual_output_overview.py      Terminal overview: counts, models, prompt_ids.
pilot1_manual_output_summary.py       Per-constraint mean scores (c1-c10).
pilot1_manual_output_table.py         Terminal table: prompt_id, model, c1-c10.
pilot1_manual_output_export.py        Exports batch to CSV.
pilot1_manual_output_report_export.py Exports summary to report.txt.
pilot1_manual_output_readme.py        Writes README.txt to run folder.

Runner Scripts (05_SRC/analysis/)
-----------------------------------
run_pilot1_manual_output_analysis.py      check, summary, table, export, report_export
run_pilot1_manual_output_full.py          overview, summary, table, export, report_export
run_pilot1_manual_output_verified.py      check, overview, summary, table, export, report_export
run_pilot1_manual_output_release_check.py check, manifest, overview, summary, table
run_pilot1_manual_output_bundle.py        check, manifest, overview, summary, table, export, report_export, readme
"""


def main():
    OUTPUT_PATH.write_text(INDEX, encoding="utf-8")
    print(f"INDEX written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
