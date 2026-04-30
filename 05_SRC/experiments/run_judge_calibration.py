"""
run_judge_calibration.py

Scores the hard validation dataset multiple times with the same judge model
to measure judge repeatability across C1-C10 constraints.

Input  : 04_RUNS/hard_validation/hard_validation_inputs.csv  (default)
         Override with --input-csv PATH
Outputs: 04_RUNS/judge_calibration/judge_calibration_scores.csv
         04_RUNS/judge_calibration/judge_calibration_scores.jsonl

Boundary notes (optional, loaded automatically if present):
         01_CANON/AOSL_JUDGE_BOUNDARY_COMPACT_v0.1.md   (preferred)
         01_CANON/AOSL_CONSTRAINT_BOUNDARY_NOTES_v0.1.md (fallback)

Usage
-----
Quick smoke test (3 rows, 2 repeats):
    py 05_SRC/experiments/run_judge_calibration.py --limit 3 --repeats 2 --timeout 60 --retries 1

Full calibration run (12 rows, 3 repeats = 36 scored rows):
    py 05_SRC/experiments/run_judge_calibration.py --repeats 3 --timeout 60 --retries 1

Cost preview (no API calls):
    py 05_SRC/experiments/run_judge_calibration.py --dry-run --repeats 3
    py 05_SRC/experiments/run_judge_calibration.py --dry-run --no-boundary-notes

Chunked run (rows 0-4 only):
    py 05_SRC/experiments/run_judge_calibration.py --start-index 0 --chunk-size 5

Resume after interruption:
    py 05_SRC/experiments/run_judge_calibration.py --resume
"""

import argparse
import csv
import json
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
    build_judge_prompt,
    load_input,
    save_outputs,
    score_row_real_judge,
)

# -- Paths ---------------------------------------------------------------------

_DEFAULT_INPUT_CSV     = _REPO_ROOT / "04_RUNS" / "hard_validation" / "hard_validation_inputs.csv"
OUT_DIR                = _REPO_ROOT / "04_RUNS" / "judge_calibration"
CSV_PATH               = OUT_DIR / "judge_calibration_scores.csv"
JSONL_PATH             = OUT_DIR / "judge_calibration_scores.jsonl"
_BOUNDARY_COMPACT_PATH = _REPO_ROOT / "01_CANON" / "AOSL_JUDGE_BOUNDARY_COMPACT_v0.1.md"
_BOUNDARY_FULL_PATH    = _REPO_ROOT / "01_CANON" / "AOSL_CONSTRAINT_BOUNDARY_NOTES_v0.1.md"

# -- Cost presets --------------------------------------------------------------

_COST_MODE_TOKENS = {
    "cheap":    300,
    "standard": 800,
}


# -- Boundary notes loader -----------------------------------------------------

def _load_boundary_notes() -> str:
    """
    Load constraint boundary guidance for injection into every judge call.

    Priority:
      1. 01_CANON/AOSL_JUDGE_BOUNDARY_COMPACT_v0.1.md  (preferred — low token cost)
      2. 01_CANON/AOSL_CONSTRAINT_BOUNDARY_NOTES_v0.1.md  (fallback — full notes)

    Returns the file contents as a string, or "" if neither file exists.
    Prints one status line naming the file loaded and its character count.
    """
    for path in (_BOUNDARY_COMPACT_PATH, _BOUNDARY_FULL_PATH):
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            print(f"  [boundary notes] Loaded: {path.name}  ({len(content)} chars)")
            return content
    print(
        "  [boundary notes] WARNING: no boundary guidance file found — scoring without it.\n"
        f"                   Tried: {_BOUNDARY_COMPACT_PATH.name}, {_BOUNDARY_FULL_PATH.name}"
    )
    return ""


# -- Resume helpers ------------------------------------------------------------

def _load_existing_scored_rows() -> list:
    """
    Read existing scored rows from CSV_PATH (if it exists).
    Returns a list of dicts, or [] if the file is missing or empty.
    """
    if not CSV_PATH.exists():
        return []
    rows = []
    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
    except Exception as exc:
        print(f"  [resume] WARNING: could not read existing CSV: {exc}")
        return []
    return rows


def _build_already_done_set(existing_rows: list) -> set:
    """
    Return a set of (prompt_id, calibration_repeat) strings for rows that
    have already been successfully scored (no scorer_status == 'error').
    """
    done = set()
    for row in existing_rows:
        if row.get("scorer_status") == "error":
            continue
        pid = str(row.get("prompt_id", "")).strip()
        rpt = str(row.get("calibration_repeat", "")).strip()
        if pid and rpt:
            done.add((pid, rpt))
    return done


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
    judge_model:         str          = DEFAULT_JUDGE_MODEL,
    repeats:             int          = 3,
    limit:               "int | None" = None,
    start_index:         int          = 0,
    chunk_size:          "int | None" = None,
    cost_mode:           str          = "standard",
    timeout:             int          = DEFAULT_TIMEOUT_SECONDS,
    retries:             int          = DEFAULT_RETRIES,
    continue_on_error:   bool         = True,
    max_tokens:          "int | None" = None,
    dry_run:             bool         = False,
    no_boundary_notes:   bool         = False,
    resume:              bool         = False,
    input_csv:           "Path | None" = None,
) -> None:

    # -- Resolve input_csv: explicit arg > module default ---------------------
    if input_csv is None:
        input_csv = _DEFAULT_INPUT_CSV
    else:
        input_csv = Path(input_csv)
        if not input_csv.is_absolute():
            input_csv = _REPO_ROOT / input_csv
    input_csv = input_csv.resolve()

    # -- Resolve max_tokens: explicit flag > cost_mode preset -----------------
    if max_tokens is None:
        max_tokens = _COST_MODE_TOKENS.get(cost_mode, DEFAULT_MAX_TOKENS)
        tokens_source = f"cost_mode={cost_mode}"
    else:
        tokens_source = "--max-tokens (explicit)"

    if no_boundary_notes:
        print("  [boundary notes] Disabled via --no-boundary-notes")
        boundary_notes = ""
    else:
        boundary_notes = _load_boundary_notes()

    print("=" * 60)
    print("AOSL Judge Calibration Runner")
    print(f"  input          : {input_csv}")
    print(f"  judge          : {judge_model}")
    print(f"  repeats        : {repeats}")
    print(f"  limit          : {limit if limit is not None else 'none'}")
    print(f"  start_index    : {start_index}")
    print(f"  chunk_size     : {chunk_size if chunk_size is not None else 'none (all)'}")
    print(f"  cost_mode      : {cost_mode}")
    print(f"  max_tokens     : {max_tokens}  ({tokens_source})")
    print(f"  timeout        : {timeout}s per call")
    print(f"  retries        : {retries} (max {retries + 1} attempt(s) per row)")
    if no_boundary_notes:
        bn_label = "disabled (--no-boundary-notes)"
    else:
        bn_label = "no (file missing)"
        for _p in (_BOUNDARY_COMPACT_PATH, _BOUNDARY_FULL_PATH):
            if _p.exists():
                bn_label = f"yes ({_p.name})"
                break
    print(f"  boundary notes : {bn_label}")
    print(f"  dry run        : {'yes (no API calls, no file writes)' if dry_run else 'no'}")
    print(f"  resume         : {'yes' if resume else 'no'}")
    print(f"  on error       : {'continue' if continue_on_error else 'abort'}")
    print(f"  outputs        : {OUT_DIR}")
    print("=" * 60)
    print()

    if not dry_run:
        try:
            _check_api_key()
        except EnvironmentError as exc:
            print(f"ERROR: {exc}")
            sys.exit(1)

    if not input_csv.exists():
        print(f"ERROR: Input file not found: {input_csv}")
        sys.exit(1)

    # -- Load and slice rows ---------------------------------------------------
    rows = load_input(input_csv)
    total_loaded = len(rows)

    if limit is not None and limit < len(rows):
        print(f"--limit {limit}: using first {limit} of {len(rows)} row(s).")
        rows = rows[:limit]
    else:
        print(f"Loaded {total_loaded} row(s).")

    if start_index > 0:
        if start_index >= len(rows):
            print(f"ERROR: --start-index {start_index} >= available rows ({len(rows)}). Nothing to score.")
            sys.exit(1)
        print(f"--start-index {start_index}: skipping first {start_index} row(s).")
        rows = rows[start_index:]

    if chunk_size is not None and chunk_size < len(rows):
        print(f"--chunk-size {chunk_size}: using next {chunk_size} of {len(rows)} available row(s).")
        rows = rows[:chunk_size]

    print(f"Selected {len(rows)} row(s) for scoring.")

    # -- Resume: load existing results and build skip set ----------------------
    existing_rows = []
    already_done  = set()
    if resume:
        existing_rows = _load_existing_scored_rows()
        already_done  = _build_already_done_set(existing_rows)
        print(f"  [resume] Existing successful results: {len(already_done)}")

    # -- Dry-run: prompt size diagnostics, no API calls -----------------------
    if dry_run:
        print()
        print("DRY-RUN — prompt size + budget diagnostics (no API calls, no file writes)")
        print()
        bn_chars = len(boundary_notes) if boundary_notes else 0

        # Per-row prompt size table (unchanged regardless of resume)
        row_prompt_tokens = {}   # pid -> p_tokens
        print(
            f"  {'prompt_id':<8}  {'prompt_chars':>12}  {'~tokens':>7}  "
            f"{'max_tok':>7}  {'~total':>7}  {'boundary_notes':>14}"
        )
        print("  " + "-" * 65)
        for row in rows:
            pid         = str(row.get("prompt_id", "?"))
            prompt_text = str(row.get("prompt_text", ""))
            output_text = str(row.get("output_text", ""))
            full_prompt = build_judge_prompt(prompt_text, output_text, boundary_notes)
            p_chars     = len(full_prompt)
            p_tokens    = p_chars // 4
            total_est   = p_tokens + max_tokens
            bn_note     = f"{bn_chars} chars" if boundary_notes else "none"
            print(
                f"  {pid:<8}  {p_chars:>12}  {p_tokens:>7}  "
                f"{max_tokens:>7}  {total_est:>7}  {bn_note:>14}"
            )
            row_prompt_tokens[pid] = p_tokens

        # Budget accounting — subtract already-done pairs when --resume is active
        total_planned    = len(rows) * repeats
        resume_skipped   = 0
        live_prompt_tok  = 0

        for row in rows:
            pid = str(row.get("prompt_id", "?"))
            p_tokens = row_prompt_tokens[pid]
            for rpt in range(1, repeats + 1):
                if resume and (pid, str(rpt)) in already_done:
                    resume_skipped += 1
                else:
                    live_prompt_tok += p_tokens

        live_calls           = total_planned - resume_skipped
        live_response_tokens = live_calls * max_tokens
        live_token_budget    = live_prompt_tok + live_response_tokens

        print()
        print(f"  selected rows                 : {len(rows)}")
        print(f"  repeats                       : {repeats}")
        print(f"  total planned calls           : {total_planned}")
        if resume:
            print(f"  resume skipped calls          : {resume_skipped}")
            print(f"  remaining live calls          : {live_calls}")
        print(f"  est. prompt tokens            : {live_prompt_tok:,}")
        print(f"  est. response tokens          : {live_response_tokens:,}  ({max_tokens} × {live_calls} calls)")
        print(f"  est. token budget             : {live_token_budget:,}")
        print()
        print(f"  judge model : {judge_model}")
        print(f"  max_tokens  : {max_tokens}  (reserved for judge response)")
        print()
        if resume and live_calls == 0:
            print("Resume dry-run: all selected prompt/repeat pairs are already successfully scored. No live calls needed.")
        else:
            print("Add credits to OpenRouter or lower --max-tokens / --cost-mode cheap before running live.")
        return

    total_calls = len(rows) * repeats
    print(f"Total judge calls planned: {total_calls}  ({len(rows)} rows x {repeats} repeats)")
    print()

    # -- Score loop: outer = repeats, inner = rows ----------------------------
    all_scored   = list(existing_rows)   # start with pre-existing rows if resuming
    new_scored   = []
    errors       = 0
    skipped      = 0
    max_attempts = retries + 1

    for rpt in range(1, repeats + 1):
        print(f"--- Repeat {rpt} / {repeats} ---")
        n_rows = len(rows)

        for i, row in enumerate(rows, start=1):
            pid   = str(row.get("prompt_id",  "?"))
            focus = row.get("expected_failure_focus", "")
            focus_tag = f"  focus={focus}" if focus else ""

            # -- Resume: skip already-done (prompt_id, repeat) pairs ----------
            if resume and (pid, str(rpt)) in already_done:
                print(f"  [SKIP]  row {i}/{n_rows}  prompt={pid}  repeat={rpt}  (already scored)")
                skipped += 1
                continue

            print(f"  [JUDGE] row {i}/{n_rows}  prompt={pid}{focus_tag}")

            result     = None
            last_error = ""

            for attempt in range(1, max_attempts + 1):
                if attempt > 1:
                    print(f"          [RETRY] attempt {attempt}/{max_attempts}")

                result = score_row_real_judge(
                    row, judge_model=judge_model, timeout=timeout,
                    max_tokens=max_tokens, boundary_notes=boundary_notes,
                )

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
                new_scored.append(error_row)
                all_scored.append(error_row)

            else:
                result["calibration_repeat"] = rpt
                _print_ok_scores(result)
                _print_row_result(i, n_rows, result)
                new_scored.append(result)
                all_scored.append(result)

        print()

    if resume and skipped:
        print(f"  [resume] Skipped {skipped} already-scored row(s).")
    if errors:
        print(f"  {errors} row(s) failed judging — see 'scorer_status'/'error_message' columns.")
        print()

    if not new_scored:
        print("No new rows scored (all already done or none selected).")
        return

    # -- Save (all_scored = existing + new, overwrites file with full set) ----
    print(f"Saving {len(all_scored)} total row(s) ({len(new_scored)} new)...")
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
        "--input-csv",
        default=None,
        metavar="PATH",
        dest="input_csv",
        help=(
            "Path to the input CSV to score. Relative paths are resolved from the repo root. "
            f"Default: {_DEFAULT_INPUT_CSV.relative_to(_REPO_ROOT)}"
        ),
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
        "--start-index",
        type=int,
        default=0,
        metavar="N",
        dest="start_index",
        help="Start scoring from row N (after --limit is applied). Default: 0",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        metavar="N",
        dest="chunk_size",
        help="Score only N rows from --start-index. Default: all remaining rows.",
    )
    parser.add_argument(
        "--cost-mode",
        default="standard",
        choices=["cheap", "standard"],
        dest="cost_mode",
        help="Token budget preset. cheap=300, standard=800. Overridden by --max-tokens. Default: standard",
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
        default=None,
        metavar="N",
        help=f"Max tokens for the judge response. Overrides --cost-mode. Default: None (uses cost-mode preset)",
    )
    parser.add_argument(
        "--no-continue-on-error",
        action="store_false",
        dest="continue_on_error",
        help="Abort on first error instead of skipping failed rows.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print prompt size and budget diagnostics without making any API calls or writing outputs.",
    )
    parser.add_argument(
        "--no-boundary-notes",
        action="store_true",
        default=False,
        dest="no_boundary_notes",
        help="Skip loading boundary guidance files. Useful for cost comparison via --dry-run.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Load existing output CSV and skip prompt_id+repeat pairs already successfully scored.",
    )
    parser.set_defaults(continue_on_error=True)
    args = parser.parse_args()
    main(
        judge_model         = args.judge_model,
        repeats             = args.repeats,
        limit               = args.limit,
        start_index         = args.start_index,
        chunk_size          = args.chunk_size,
        cost_mode           = args.cost_mode,
        timeout             = args.timeout,
        retries             = args.retries,
        continue_on_error   = args.continue_on_error,
        max_tokens          = args.max_tokens,
        dry_run             = args.dry_run,
        no_boundary_notes   = args.no_boundary_notes,
        resume              = args.resume,
        input_csv           = args.input_csv,
    )
