"""
run_hard_validation_real_judge.py

Runs the AOSL hard validation dataset through the real-judge batch scorer.

Input  : 04_RUNS/hard_validation/hard_validation_inputs.csv
Outputs: 04_RUNS/hard_validation/hard_validation_scores.csv
         04_RUNS/hard_validation/hard_validation_scores.jsonl

Usage
-----
Default (real-judge, deepseek, 60s timeout, 1 retry, continue-on-error):
    py 05_SRC/experiments/run_hard_validation_real_judge.py

Quick smoke test (first 2 rows only):
    py 05_SRC/experiments/run_hard_validation_real_judge.py --limit 2

Override judge model:
    py 05_SRC/experiments/run_hard_validation_real_judge.py --judge-model openai/gpt-4o-mini
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
    REAL_JUDGE_SCORER_LABEL,
    _check_api_key,
    load_input,
    save_outputs,
    score_row_real_judge,
)

# -- Paths ---------------------------------------------------------------------

RUN_DIR    = _REPO_ROOT / "04_RUNS" / "hard_validation"
INPUT_CSV  = RUN_DIR / "hard_validation_inputs.csv"
CSV_PATH   = RUN_DIR / "hard_validation_scores.csv"
JSONL_PATH = RUN_DIR / "hard_validation_scores.jsonl"


# -- Print helpers (self-contained, no dependency on demo runner) --------------

def _print_row_result(i: int, total: int, row: dict) -> None:
    is_err   = row.get("scorer_status") == "error" or bool(row.get("scorer_error"))
    err_flag = "  [JUDGE ERROR]" if is_err else ""

    div  = row.get("divergence",      "")
    stab = row.get("stability_score", "")
    tier = row.get("stability_tier",  "")

    div_str  = f"{float(div):.4f}"  if div  not in ("", None) else "N/A "
    stab_str = f"{float(stab):.4f}" if stab not in ("", None) else "N/A "

    focus = str(row.get("expected_failure_focus", ""))
    focus_tag = f"  focus={focus}" if focus else ""

    print(
        f"  [{i:>2}/{total}] "
        f"prompt={str(row.get('prompt_id', '?')):<5}  "
        f"div={div_str}  stab={stab_str}  tier={tier}"
        f"{focus_tag}"
        f"{err_flag}"
    )


def _print_ok_scores(row: dict) -> None:
    scores = "  ".join(f"{code}={row.get(code, '?')}" for code in CONSTRAINT_CODES)
    print(f"        [OK] {scores}")


def _make_error_row(row: dict, error_message: str) -> dict:
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
    judge_model:       str          = DEFAULT_JUDGE_MODEL,
    limit:             "int | None" = None,
    timeout:           int          = DEFAULT_TIMEOUT_SECONDS,
    retries:           int          = DEFAULT_RETRIES,
    continue_on_error: bool         = True,
) -> None:

    print("=" * 60)
    print("AOSL Hard Validation — Real Judge Batch")
    print(f"  input   : {INPUT_CSV}")
    print(f"  judge   : {judge_model}")
    print(f"  timeout : {timeout}s per call")
    print(f"  retries : {retries} (max {retries + 1} attempt(s) per row)")
    print(f"  on error: {'continue' if continue_on_error else 'abort'}")
    print(f"  outputs : {RUN_DIR}")
    print("=" * 60)
    print()

    # -- Check API key before loading data ------------------------------------
    try:
        _check_api_key()
    except EnvironmentError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    # -- Load input ------------------------------------------------------------
    if not INPUT_CSV.exists():
        print(f"ERROR: Input file not found: {INPUT_CSV}")
        sys.exit(1)

    rows = load_input(INPUT_CSV)
    print(f"Loaded {len(rows)} row(s) from {INPUT_CSV.name}.")

    if limit is not None and limit < len(rows):
        print(f"--limit {limit}: processing only the first {limit} row(s).")
        rows = rows[:limit]

    print()

    # -- Score loop ------------------------------------------------------------
    scored       = []
    errors       = 0
    total        = len(rows)
    max_attempts = retries + 1

    for i, row in enumerate(rows, start=1):
        pid   = row.get("prompt_id",  "?")
        focus = row.get("expected_failure_focus", "")
        focus_tag = f"  focus={focus}" if focus else ""
        print(f"  [JUDGE] row {i}/{total}  prompt={pid}{focus_tag}")

        result     = None
        last_error = ""

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                print(f"        [RETRY] attempt {attempt}/{max_attempts}")

            result = score_row_real_judge(row, judge_model=judge_model, timeout=timeout)

            if not result.get("scorer_error"):
                break
            last_error = str(result.get("scorer_error", "unknown error"))

        # -- Outcome -----------------------------------------------------------
        if result.get("scorer_error"):
            errors += 1
            short_err = last_error[:200]
            print(f"        [ERROR] {short_err}")

            if not continue_on_error:
                print()
                print("Aborting after first error.")
                print("Re-run with --continue-on-error to skip failed rows.")
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
    print("    py 05_SRC/analysis/summarize_hard_validation_scores.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score the AOSL hard validation dataset with a real OpenRouter judge."
    )
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"OpenRouter model ID for the judge. Default: {DEFAULT_JUDGE_MODEL}",
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
        help=f"Seconds to wait per judge call. Default: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        metavar="N",
        help=f"Retries after a failed call (0 = no retry). Default: {DEFAULT_RETRIES}",
    )
    parser.add_argument(
        "--no-continue-on-error",
        action="store_false",
        dest="continue_on_error",
        help="Abort on first error instead of skipping failed rows.",
    )
    parser.set_defaults(continue_on_error=True)
    args = parser.parse_args()
    main(
        judge_model       = args.judge_model,
        limit             = args.limit,
        timeout           = args.timeout,
        retries           = args.retries,
        continue_on_error = args.continue_on_error,
    )
