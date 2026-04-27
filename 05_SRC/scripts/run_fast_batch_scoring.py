"""
run_fast_batch_scoring.py

Command-line entry point for the AOSL fast batch scorer.

Usage:
    py 05_SRC\scripts\run_fast_batch_scoring.py ^
      --input  04_RUNS\pilot1\pilot1_manual_output_batch.json ^
      --output 04_RUNS\pilot1\pilot1_fast_scored.jsonl ^
      --csv    04_RUNS\pilot1\pilot1_fast_scored.csv ^
      --workers 5 ^
      --judge-model deepseek/deepseek-chat

Resume:
    Re-run the exact same command. Already-scored record IDs are skipped
    automatically. Delete the --output file first to start fresh.
"""

import argparse
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so AOSL package is importable
# when running this script directly (without pip install -e .).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from AOSL.agents.fast_batch_scorer import (
    export_csv,
    load_input_records,
    run_batch,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AOSL fast batch scorer — score AI outputs via OpenRouter.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to input JSON (list) or JSONL file containing output records.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path for output JSONL file. Results are appended (resume-safe).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Path for CSV export. Defaults to --output with .csv extension.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent scoring workers.",
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default="deepseek/deepseek-chat",
        help="OpenRouter model ID to use as the judge.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path  = args.input.resolve()
    output_path = args.output.resolve()
    csv_path    = (args.csv or args.output.with_suffix(".csv")).resolve()
    judge_model = args.judge_model
    workers     = args.workers

    # ── Validate input ───────────────────────────────────────────────────────
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    # ── Load records ─────────────────────────────────────────────────────────
    print(f"\nInput  : {input_path}")
    print(f"Output : {output_path}")
    print(f"CSV    : {csv_path}")

    records = load_input_records(input_path)
    print(f"Loaded : {len(records)} record(s)")

    if not records:
        print("[WARN] Input file is empty. Nothing to score.")
        sys.exit(0)

    # ── Run batch scoring ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("AOSL Fast Batch Scorer")
    print("=" * 60)

    run_batch(
        records=records,
        judge_model=judge_model,
        output_path=output_path,
        workers=workers,
    )

    # ── Export CSV ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Exporting CSV...")
    export_csv(output_path, csv_path)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Done.")
    print(f"  JSONL : {output_path}")
    print(f"  CSV   : {csv_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
