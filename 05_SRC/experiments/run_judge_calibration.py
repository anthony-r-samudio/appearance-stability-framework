"""
run_judge_calibration.py

Scores the hard validation dataset multiple times with the same judge model
to measure judge repeatability across C1-C10 constraints.

Input  : 04_RUNS/hard_validation/hard_validation_inputs.csv
Outputs: 04_RUNS/judge_calibration/judge_calibration_scores.csv
         04_RUNS/judge_calibration/judge_calibration_scores.jsonl

Usage
-----
Quick smoke test (3 rows, 2 repeats):
    py 05_SRC/experiments/run_judge_calibration.py --limit 3 --repeats 2 --timeout 60 --retries 1

Full calibration run (12 rows, 3 repeats = 36 scored rows):
    py 05_SRC/experiments/run_judge_calibration.py --repeats 3 --timeout 60 --retries 1
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
    DEFAULT_MAX_TOKENS,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    REAL_JUDGE_SCORER_LABEL,
    _check_api_key,
    load_input,
    save_outputs,
    score_row_real_judge,
)

# -- Paths ---------------------------------------------------------------------

INPUT_CSV  = _REPO_ROOT / "04_RUNS" / "hard_validation" / "hard_validation_inputs.csv"
OUT_DIR    = _REPO_ROOT / "04_RUNS" / "judge_calibration"
CSV_PATH   = OUT_DIR / "judge_calibration_scores.csv"
JSONL_PATH = OUT_DIR / "judge_calibration_scores.jsonl"


# -- Print helpers -------------------------------------------------------------

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
        f"    [{i:>2}/{total}] "
        f"prompt={str(row.get('prompt_id', '?')):<5}  "
        f"div={div_str}  stab={stab_str}  tier={tier}"
        f"{focus_tag}"
        f"{err_flag}"
    )


def _print_ok_scores(row: dict) -> None:
    scores = "  ".join(f"{code}={row.get(code, '?')}" for code in CONSTRAINT_CODES)
    print(f"          [OK] {scores}")


def _make_error_row(row: dict, error_message: str, calibration_repeat: int) -> dict:
    error_row = dict(row)
    error_row.setdefault("temperature", "")
    error_row.setdefault("repeat",      "")
    error_row["calibration_repeat"] = calibration_repeat
    error_row["scorer_status"]      = "error"
    error_row["error_message"]      = error_message
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
    repeats:           int          = 3,
    limit:             "int | None" = None,
    timeout:           int          = DEFAULT_TIMEOUT_SECONDS,
    retries:           int          = DEFAULT_RETRIES,
    continue_on_error: bool         = True,
    max_tokens:        int          = DEFAULT_MAX_TOKENS,
) -> None:

    print("=" * 60)
    print("AOSL Judge Calibration Runner")
    print(f"  input      : {INPUT_CSV}")
    print(f"  judge      : {judge_model}")
    print(f"  repeats    : {repeats}")
    print(f"  timeout    : {timeout}s per call")
    print(f"  retries    : {retries} (max {retries + 1} attempt(s) per row)")
    print(f"  max_tokens : {max_tokens}")
    print(f"  on error   : {'continue' if continue_on_error else 'abort'}")
    print(f"  outputs    : {OUT_DIR}")
    print("=" * 60)
    print()

    try:
        _check_api_key()
    except EnvironmentError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    if not INPUT_CSV.exists():
        print(f"ERROR: Input file not found: {INPUT_CSV}")
        sys.exit(1)

    rows = load_input(INPUT_CSV)
    if limit is not None and limit < len(rows):
        print(f"--limit {limit}: using first {limit} of {len(rows)} row(s).")
        rows = rows[:limit]
    else:
        print(f"Loaded {len(rows)} row(s).")

    total_calls = len(rows) * repeats
    print(f"Total judge calls planned: {total_calls}  ({len(rows)} rows x {repeats} repeats)")
    print()

    # -- Score loop: outer = repeats, inner = rows ----------------------------
    all_scored   = []
    errors       = 0
    max_attempts = retries + 1

    for rpt in range(1, repeats + 1):
        print(f"--- Repeat {rpt} / {repeats} ---")
        n_rows = len(rows)

        for i, row in enumerate(rows, start=1):
            pid   = row.get("prompt_id",  "?")
            focus = row.get("expected_failure_focus", "")
            focus_tag = f"  focus={focus}" if focus else ""
            print(f"  [JUDGE] row {i}/{n_rows}  prompt={pid}{focus_tag}")

            result     = None
            last_error = ""

            for attempt in range(1, max_attempts + 1):
                if attempt > 1:
                    print(f"          [RETRY] attempt {attempt}/{max_attempts}")

                result = score_row_real_judge(row, judge_model=judge_model, timeout=timeout, max_tokens=max_tokens)

                if not result.get("scorer_error"):
                    break
                last_error = str(result.get("scorer_error", "unknown error"))
                if result.get("scorer_credit_error"):
                    break

            # -- Outcome -------------------------------------------------------
            if result.get("scorer_error"):
                errors += 1
                short_err = last_error[:200]
                print(f"          [ERROR] {short_err}")

                if not continue_on_error:
                    print()
                    print("Aborting after first error.")
                    print("Re-run with --no-continue-on-error removed to skip failed rows.")
                    sys.exit(1)

                error_row = _make_error_row(row, short_err, rpt)
                _print_row_result(i, n_rows, error_row)
                all_scored.append(error_row)

            else:
                result["calibration_repeat"] = rpt
                _print_ok_scores(result)
                _print_row_result(i, n_rows, result)
                all_scored.append(result)

        print()

    if errors:
        print(f"  {errors} row(s) failed judging — see 'scorer_status'/'error_message' columns.")
        print()

    # -- Save ------------------------------------------------------------------
    print(f"Saving {len(all_scored)} scored row(s)...")
    save_outputs(all_scored, CSV_PATH, JSONL_PATH)

    print()
    print("=" * 60)
    print("Output files:")
    print(f"  CSV   : {CSV_PATH}")
    print(f"  JSONL : {JSONL_PATH}")
    print("=" * 60)
    print()
    print("Run the summary script next:")
    print("    py 05_SRC/analysis/summarize_judge_calibration.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score the hard validation dataset multiple times to measure judge repeatability."
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        metavar="N",
        help="Number of times to score each row. Default: 3",
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
        help="Use only the first N rows from the input file.",
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
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        metavar="N",
        help=f"Max tokens for the judge response. Default: {DEFAULT_MAX_TOKENS}",
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
        repeats           = args.repeats,
        limit             = args.limit,
        timeout           = args.timeout,
        retries           = args.retries,
        continue_on_error = args.continue_on_error,
        max_tokens        = args.max_tokens,
    )
