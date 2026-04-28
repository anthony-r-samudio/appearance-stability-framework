"""
run_fast_batch_scoring_demo.py

Demo runner for the AOSL fast batch scorer.
Supports two scorer modes: demo (default) and real-judge (requires OPENROUTER_API_KEY).

Usage
-----
Demo mode (no API key needed):
    py 05_SRC/experiments/run_fast_batch_scoring_demo.py

Real-judge, 1 row, 60s timeout:
    py 05_SRC/experiments/run_fast_batch_scoring_demo.py --scorer real-judge --limit 1 --timeout 60

Real-judge, full batch, retries, continue on error:
    py 05_SRC/experiments/run_fast_batch_scoring_demo.py --scorer real-judge --limit 6 --timeout 60 --retries 1 --continue-on-error

Custom input file:
    py 05_SRC/experiments/run_fast_batch_scoring_demo.py --input path/to/input.csv --scorer real-judge
"""

import argparse
import sys
from pathlib import Path

# -- sys.path ------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT  = _REPO_ROOT / "05_SRC"
for _p in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scoring.fast_batch_scorer import (
    CONSTRAINT_CODES,
    DEFAULT_JUDGE_MODEL,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DEMO_SCORER_LABEL,
    REAL_JUDGE_SCORER_LABEL,
    _check_api_key,
    load_input,
    save_outputs,
    score_batch,
    score_row_real_judge,
)

# -- Output paths --------------------------------------------------------------

OUTPUT_DIR = _REPO_ROOT / "04_RUNS" / "fast_batch_validation"
CSV_PATH   = OUTPUT_DIR / "fast_batch_scores.csv"
JSONL_PATH = OUTPUT_DIR / "fast_batch_scores.jsonl"

# -- Built-in sample rows ------------------------------------------------------

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


# -- Print helpers -------------------------------------------------------------

def _print_row_result(i: int, total: int, row: dict) -> None:
    """Print the one-line summary for a scored (or error) row."""
    err_flag = ""
    if row.get("scorer_error") or row.get("scorer_status") == "error":
        err_flag = "  [JUDGE ERROR]"

    div  = row.get("divergence",      "")
    stab = row.get("stability_score", "")
    tier = row.get("stability_tier",  "")

    div_str  = f"{float(div):.4f}"  if div  not in ("", None) else "N/A "
    stab_str = f"{float(stab):.4f}" if stab not in ("", None) else "N/A "

    print(
        f"  [{i:>2}/{total}] "
        f"prompt={str(row.get('prompt_id', '?')):<4}  "
        f"model={str(row.get('model_name', '?')):<16}  "
        f"temp={str(row.get('temperature', '')):<4}  "
        f"div={div_str}  stab={stab_str}  tier={tier}"
        f"{err_flag}"
    )


def _print_ok_scores(row: dict) -> None:
    """Print a compact c1-c10 line after a successful judge call."""
    scores = "  ".join(f"{code}={row.get(code, '?')}" for code in CONSTRAINT_CODES)
    print(f"        [OK] {scores}")


def _make_error_row(row: dict, error_message: str) -> dict:
    """Build a row flagged as an error for output files (requirement 5)."""
    error_row = dict(row)
    error_row.setdefault("temperature", "")
    error_row.setdefault("repeat",      "")
    error_row["scorer_status"] = "error"
    error_row["error_message"] = error_message
    for code in CONSTRAINT_CODES:
        error_row[code] = ""
    error_row["divergence"]      = ""
    error_row["stability_score"] = ""
    error_row["stability_tier"]  = "ERROR"
    error_row["scorer"]          = REAL_JUDGE_SCORER_LABEL
    error_row["notes"]           = ""
    return error_row


# -- Main ----------------------------------------------------------------------

def main(
    input_path:        "Path | None" = None,
    scorer:            str           = "demo",
    judge_model:       str           = DEFAULT_JUDGE_MODEL,
    limit:             "int | None"  = None,
    timeout:           int           = DEFAULT_TIMEOUT_SECONDS,
    retries:           int           = DEFAULT_RETRIES,
    continue_on_error: bool          = False,
) -> None:

    scorer_label = REAL_JUDGE_SCORER_LABEL if scorer == "real-judge" else DEMO_SCORER_LABEL

    print("=" * 60)
    print("AOSL Fast Batch Scorer")
    print(f"  scorer  : {scorer_label}")
    if scorer == "real-judge":
        print(f"  judge   : {judge_model}")
        print(f"  timeout : {timeout}s per call")
        print(f"  retries : {retries} (max {retries + 1} attempt(s) per row)")
        print(f"  on error: {'continue' if continue_on_error else 'abort'}")
    else:
        print("  (no API calls)")
    print(f"  outputs : {OUTPUT_DIR}")
    print("=" * 60)
    print()

    # -- Load rows -------------------------------------------------------------
    if input_path is not None:
        print(f"Loading input file: {input_path}")
        rows = load_input(input_path)
        print(f"Loaded {len(rows)} row(s).")
    else:
        print("No --input provided. Using built-in sample rows.")
        rows = SAMPLE_ROWS
        print(f"Sample size: {len(rows)} row(s).")

    if limit is not None and limit < len(rows):
        print(f"--limit {limit}: processing only the first {limit} row(s).")
        rows = rows[:limit]

    print()

    # -- Demo mode: unchanged --------------------------------------------------
    if scorer != "real-judge":
        scored = score_batch(rows, scorer=scorer, judge_model=judge_model)

        errors = 0
        for i, row in enumerate(scored, start=1):
            if row.get("scorer_error"):
                errors += 1
            _print_row_result(i, len(scored), row)

        if errors:
            print(f"\n  {errors} row(s) had errors — see 'scorer_error' column.")

    # -- Real-judge mode: manual loop with full visibility --------------------
    else:
        try:
            _check_api_key()
        except EnvironmentError as exc:
            print(f"ERROR: {exc}")
            sys.exit(1)

        scored = []
        errors = 0
        total  = len(rows)
        max_attempts = retries + 1  # retries=1 → try up to 2 times

        for i, row in enumerate(rows, start=1):
            pid        = row.get("prompt_id",  "?")
            model_name = row.get("model_name", "?")
            print(f"  [JUDGE] scoring row {i}/{total}  prompt={pid}  model={model_name}")

            result     = None
            last_error = ""

            for attempt in range(1, max_attempts + 1):
                if attempt > 1:
                    print(f"        [RETRY] attempt {attempt}/{max_attempts}")

                result = score_row_real_judge(row, judge_model=judge_model, timeout=timeout)

                if not result.get("scorer_error"):
                    break           # success — stop retrying
                last_error = str(result.get("scorer_error", "unknown error"))

            # -- Outcome -------------------------------------------------------
            if result.get("scorer_error"):
                errors += 1
                # Truncate error to avoid accidentally printing sensitive content
                short_err = last_error[:200]
                print(f"        [ERROR] {short_err}")

                if not continue_on_error:
                    print()
                    print("Aborting after first error.")
                    print("Re-run with --continue-on-error to skip failed rows and save partial output.")
                    sys.exit(1)

                error_row = _make_error_row(row, short_err)
                _print_row_result(i, total, error_row)
                scored.append(error_row)

            else:
                _print_ok_scores(result)
                _print_row_result(i, total, result)
                scored.append(result)

        if errors:
            print(f"\n  {errors} row(s) failed judging — see 'scorer_status'/'error_message' columns.")

    # -- Save ------------------------------------------------------------------
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
        description="AOSL fast batch scoring — scores outputs against c1-c10 constraints."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to a .csv or .jsonl input file. Uses built-in sample if omitted.",
    )
    parser.add_argument(
        "--scorer",
        choices=["demo", "real-judge"],
        default="demo",
        help="Scoring mode. 'demo' uses a deterministic placeholder (default). "
             "'real-judge' calls an OpenRouter judge model (requires OPENROUTER_API_KEY).",
    )
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"OpenRouter model ID for the judge (real-judge mode only). "
             f"Default: {DEFAULT_JUDGE_MODEL}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N rows. Useful for quick tests.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"Seconds to wait for each judge API call before failing. "
             f"Default: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        metavar="N",
        help=f"Number of retries after a failed judge call (0 = no retry). "
             f"Default: {DEFAULT_RETRIES}",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=False,
        help="If set, log failed rows and continue. Without this flag, the "
             "run aborts on the first error.",
    )
    args = parser.parse_args()
    main(
        input_path        = args.input,
        scorer            = args.scorer,
        judge_model       = args.judge_model,
        limit             = args.limit,
        timeout           = args.timeout,
        retries           = args.retries,
        continue_on_error = args.continue_on_error,
    )
