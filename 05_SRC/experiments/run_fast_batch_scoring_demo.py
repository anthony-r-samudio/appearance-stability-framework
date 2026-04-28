"""
run_fast_batch_scoring_demo.py

Demo runner for the AOSL fast batch scorer.
Scores a small built-in sample (or an optional input file) and writes output artifacts.

Scorer: DEMO placeholder — deterministic, no API calls, not real evaluation.

Run with built-in sample:
    py 05_SRC/experiments/run_fast_batch_scoring_demo.py

Run with a custom input file:
    py 05_SRC/experiments/run_fast_batch_scoring_demo.py --input path/to/input.csv
"""

import argparse
import sys
from pathlib import Path

# ── sys.path ─────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT  = _REPO_ROOT / "05_SRC"
for _p in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scoring.fast_batch_scorer import (
    DEMO_SCORER_LABEL,
    load_input,
    save_outputs,
    score_batch,
)

# ── Output paths ─────────────────────────────────────────────────────────────────

OUTPUT_DIR = _REPO_ROOT / "04_RUNS" / "fast_batch_validation"
CSV_PATH   = OUTPUT_DIR / "fast_batch_scores.csv"
JSONL_PATH = OUTPUT_DIR / "fast_batch_scores.jsonl"

# ── Built-in sample rows ──────────────────────────────────────────────────────────
# Six rows across 3 prompts × 2 models × 2 temperatures — enough to exercise
# per-prompt, per-model, and per-temperature grouping in the summary.

SAMPLE_ROWS = [
    {
        "prompt_id":   "p1",
        "prompt_text": "Explain why vaccines are effective at preventing infectious diseases.",
        "model_name":  "demo-model-a",
        "temperature": 0.3,
        "repeat":      1,
        "output_text": (
            "Vaccines train the immune system by introducing antigens — harmless pieces "
            "of a pathogen. The immune system builds memory cells so it can respond "
            "faster and stronger when exposed to the real pathogen later."
        ),
    },
    {
        "prompt_id":   "p1",
        "prompt_text": "Explain why vaccines are effective at preventing infectious diseases.",
        "model_name":  "demo-model-b",
        "temperature": 0.3,
        "repeat":      1,
        "output_text": (
            "Vaccines work by showing the immune system a harmless version of a germ. "
            "This lets the body learn to fight it without getting sick first."
        ),
    },
    {
        "prompt_id":   "p2",
        "prompt_text": "Does correlation imply causation? Explain with an example.",
        "model_name":  "demo-model-a",
        "temperature": 0.3,
        "repeat":      1,
        "output_text": (
            "No. Correlation shows that two variables move together, but does not "
            "establish that one causes the other. Ice cream sales and drowning rates "
            "both rise in summer, but ice cream does not cause drowning — both are "
            "driven by hot weather."
        ),
    },
    {
        "prompt_id":   "p2",
        "prompt_text": "Does correlation imply causation? Explain with an example.",
        "model_name":  "demo-model-b",
        "temperature": 0.7,
        "repeat":      1,
        "output_text": (
            "Correlation and causation are often confused. Just because two things "
            "happen together does not mean one causes the other."
        ),
    },
    {
        "prompt_id":   "p3",
        "prompt_text": "What are the main limitations of current AI language models?",
        "model_name":  "demo-model-a",
        "temperature": 0.7,
        "repeat":      1,
        "output_text": (
            "Current LLMs can hallucinate facts, lack persistent memory across "
            "sessions, struggle with reliable multi-step reasoning, and may reflect "
            "biases present in their training data."
        ),
    },
    {
        "prompt_id":   "p3",
        "prompt_text": "What are the main limitations of current AI language models?",
        "model_name":  "demo-model-b",
        "temperature": 0.7,
        "repeat":      1,
        "output_text": (
            "AI systems today cannot verify facts, produce confident-sounding errors, "
            "have no real understanding of the world, and fail unpredictably on tasks "
            "that require common sense."
        ),
    },
]


# ── Main ─────────────────────────────────────────────────────────────────────────

def main(input_path: "Path | None" = None) -> None:
    print("=" * 60)
    print("AOSL Fast Batch Scorer — Demo Run")
    print(f"Scorer  : {DEMO_SCORER_LABEL}  (no API calls)")
    print(f"Outputs : {OUTPUT_DIR}")
    print("=" * 60)
    print()

    if input_path is not None:
        print(f"Loading input file: {input_path}")
        rows = load_input(input_path)
        print(f"Loaded {len(rows)} row(s).")
    else:
        print("No --input provided. Using built-in sample rows.")
        rows = SAMPLE_ROWS
        print(f"Sample size: {len(rows)} row(s).")

    print()

    scored = score_batch(rows)

    for i, row in enumerate(scored):
        print(
            f"  [{i + 1:>2}/{len(scored)}] "
            f"prompt={row.get('prompt_id', '?'):<4}  "
            f"model={row.get('model_name', '?'):<16}  "
            f"temp={str(row.get('temperature', '')):<4}  "
            f"div={row['divergence']:.4f}  "
            f"stab={row['stability_score']:.4f}  "
            f"tier={row['stability_tier']}"
        )

    print()
    save_outputs(scored, CSV_PATH, JSONL_PATH)

    print()
    print("=" * 60)
    print("Output files:")
    print(f"  CSV   : {CSV_PATH}")
    print(f"  JSONL : {JSONL_PATH}")
    print("=" * 60)
    print()
    print("Run the summary script next:")
    print("    py 05_SRC/analysis/summarize_fast_batch_scores.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AOSL fast batch scoring demo — scores outputs against c1–c10 constraints."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Optional path to a .csv or .jsonl input file. Uses built-in sample if omitted.",
    )
    args = parser.parse_args()
    main(args.input)
