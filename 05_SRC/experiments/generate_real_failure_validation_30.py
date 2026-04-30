"""
generate_real_failure_validation_30.py

Generates real model outputs for the real_failure_validation_30 prompt set.
Each prompt is purpose-written to apply structural pressure (false premise,
forced certainty, causal overclaim, quantitative trap, etc.) that is more
likely to elicit genuine constraint violations than a generic no-hedge prefix.

The output CSV is directly compatible with run_judge_calibration.py --input-csv.

Input  : 04_RUNS/real_failure_validation_30/real_failure_validation_30_prompts.csv
Output : 04_RUNS/real_failure_validation_30/real_failure_validation_30_outputs.csv
         (or real_failure_validation_30_outputs_<suffix>.csv if --output-suffix given)

Prompt file schema  : prompt_id, original_prompt_id, prompt_text,
                      expected_failure_focus, pressure_type
Output file schema  : prompt_id, prompt_text, model_name, output_text,
                      temperature, repeat, expected_failure_focus

Usage
-----
Dry-run (no API calls):
    py 05_SRC/experiments/generate_real_failure_validation_30.py --dry-run

Generate first 5 rows (cheap test):
    py 05_SRC/experiments/generate_real_failure_validation_30.py --limit 5 --max-tokens 300

Generate all 30 rows:
    py 05_SRC/experiments/generate_real_failure_validation_30.py

Resume after interruption:
    py 05_SRC/experiments/generate_real_failure_validation_30.py --resume

Generate with a second model (separate output file):
    py 05_SRC/experiments/generate_real_failure_validation_30.py \\
        --model meta-llama/llama-3.1-8b-instruct \\
        --output-suffix llama_3_1_8b

Score the outputs:
    py 05_SRC/experiments/run_judge_calibration.py \\
        --input-csv 04_RUNS/real_failure_validation_30/real_failure_validation_30_outputs.csv \\
        --dry-run
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

# -- sys.path ------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT  = _REPO_ROOT / "05_SRC"
for _p in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.openrouter_client import CreditError, generate_response

# -- Paths ---------------------------------------------------------------------

_PROMPTS_CSV = (
    _REPO_ROOT / "04_RUNS" / "real_failure_validation_30"
    / "real_failure_validation_30_prompts.csv"
)
_DEFAULT_OUTPUT_CSV = (
    _REPO_ROOT / "04_RUNS" / "real_failure_validation_30"
    / "real_failure_validation_30_outputs.csv"
)

# -- Defaults ------------------------------------------------------------------

_DEFAULT_MODEL      = "deepseek/deepseek-chat"
_DEFAULT_TEMP       = 0.9
_DEFAULT_MAX_TOKENS = 500
_DEFAULT_REPEAT     = 1

# -- Output schema (must match judge calibration runner input schema) ----------

_OUTPUT_FIELDS = [
    "prompt_id",
    "prompt_text",
    "model_name",
    "output_text",
    "temperature",
    "repeat",
    "expected_failure_focus",
]


# -- Helpers -------------------------------------------------------------------

def _sanitize_suffix(suffix: str) -> str:
    """Make suffix safe for Windows filenames: lowercase, replace separators."""
    s = suffix.lower()
    s = re.sub(r'[/\\: ]+', '_', s)
    return s


def _resolve_output_csv(output_suffix: "str | None") -> Path:
    """Return the output CSV path, incorporating suffix if provided."""
    if not output_suffix:
        return _DEFAULT_OUTPUT_CSV
    safe = _sanitize_suffix(output_suffix)
    return (
        _REPO_ROOT / "04_RUNS" / "real_failure_validation_30"
        / f"real_failure_validation_30_outputs_{safe}.csv"
    )


def _check_api_key() -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set.\n"
            "Set it in PowerShell before running:\n"
            "    $env:OPENROUTER_API_KEY = 'sk-or-v1-...'\n"
            "Then re-run the script."
        )


def _load_prompts() -> list:
    if not _PROMPTS_CSV.exists():
        print(f"ERROR: Prompts file not found: {_PROMPTS_CSV}")
        sys.exit(1)
    with open(_PROMPTS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_existing_outputs(path: Path) -> list:
    if not path.exists():
        return []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception as exc:
        print(f"  [resume] WARNING: could not read existing outputs: {exc}")
        return []


def _build_done_set(existing: list) -> set:
    """Return prompt_ids that already have a successful (non-error) output."""
    done = set()
    for row in existing:
        pid = str(row.get("prompt_id", "")).strip()
        out = str(row.get("output_text", "")).strip()
        if pid and out and not out.startswith("[ERROR"):
            done.add(pid)
    return done


def _save_csv(rows: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# -- Main ----------------------------------------------------------------------

def main(
    model:         str          = _DEFAULT_MODEL,
    temperature:   float        = _DEFAULT_TEMP,
    max_tokens:    int          = _DEFAULT_MAX_TOKENS,
    repeat:        int          = _DEFAULT_REPEAT,
    limit:         "int | None" = None,
    start_index:   int          = 0,
    chunk_size:    "int | None" = None,
    resume:        bool         = False,
    dry_run:       bool         = False,
    output_suffix: "str | None" = None,
) -> None:

    output_csv = _resolve_output_csv(output_suffix)

    print("=" * 60)
    print("AOSL Real Failure Validation 30 — Generator")
    print(f"  prompts        : {_PROMPTS_CSV}")
    print(f"  output         : {output_csv}")
    print(f"  model          : {model}")
    print(f"  temperature    : {temperature}")
    print(f"  max_tokens     : {max_tokens}")
    print(f"  repeat         : {repeat}")
    print(f"  limit          : {limit if limit is not None else 'none'}")
    print(f"  start_index    : {start_index}")
    print(f"  chunk_size     : {chunk_size if chunk_size is not None else 'none (all)'}")
    print(f"  resume         : {'yes' if resume else 'no'}")
    print(f"  dry run        : {'yes (no API calls, no file writes)' if dry_run else 'no'}")
    print(f"  output_suffix  : {output_suffix if output_suffix else '(none — default file)'}")
    print(f"  pressure mode  : structural (false_premise, causal_overclaim, quantitative_trap, etc.)")
    print("=" * 60)
    print()

    if not dry_run:
        try:
            _check_api_key()
        except EnvironmentError as exc:
            print(f"ERROR: {exc}")
            sys.exit(1)

    # -- Load and slice prompts ------------------------------------------------
    prompts = _load_prompts()
    total_loaded = len(prompts)

    if limit is not None and limit < len(prompts):
        print(f"--limit {limit}: using first {limit} of {len(prompts)} prompt(s).")
        prompts = prompts[:limit]
    else:
        print(f"Loaded {total_loaded} prompt(s).")

    if start_index > 0:
        if start_index >= len(prompts):
            print(f"ERROR: --start-index {start_index} >= available prompts ({len(prompts)}). Nothing to generate.")
            sys.exit(1)
        print(f"--start-index {start_index}: skipping first {start_index} prompt(s).")
        prompts = prompts[start_index:]

    if chunk_size is not None and chunk_size < len(prompts):
        print(f"--chunk-size {chunk_size}: using next {chunk_size} of {len(prompts)} available prompt(s).")
        prompts = prompts[:chunk_size]

    print(f"Selected {len(prompts)} prompt(s) for generation.")

    # -- Resume: load existing outputs and build skip set ----------------------
    existing_rows = []
    already_done  = set()
    if resume:
        existing_rows = _load_existing_outputs(output_csv)
        already_done  = _build_done_set(existing_rows)
        print(f"  [resume] Existing successful outputs: {len(already_done)}")

    # -- Dry-run: show plan, no API calls -------------------------------------
    if dry_run:
        live_calls = sum(
            1 for p in prompts
            if not (resume and str(p.get("prompt_id", "")).strip() in already_done)
        )
        skipped = len(prompts) - live_calls

        print()
        print("DRY-RUN — high-pressure generation plan (no API calls, no file writes)")
        print()
        print(f"  {'prompt_id':<10}  {'pressure_type':<22}  {'expected_failure_focus':<30}  status")
        print("  " + "-" * 90)
        for p in prompts:
            pid      = str(p.get("prompt_id", "?"))
            focus    = str(p.get("expected_failure_focus", ""))
            pressure = str(p.get("pressure_type", ""))
            status   = "SKIP (already done)" if (resume and pid in already_done) else "GENERATE"
            print(f"  {pid:<10}  {pressure:<22}  {focus:<30}  {status}")

        print()
        print(f"  selected prompts     : {len(prompts)}")
        if resume:
            print(f"  resume skipped       : {skipped}")
        print(f"  live generation calls: {live_calls}")
        print(f"  model                : {model}")
        print(f"  temperature          : {temperature}")
        print(f"  max_tokens           : {max_tokens}")
        print(f"  output file          : {output_csv}")
        print()
        if resume and live_calls == 0:
            print("Resume dry-run: all selected prompts are already successfully generated. No live calls needed.")
        else:
            print("Add credits to OpenRouter or lower --max-tokens before running live.")
        return

    # -- Generation loop -------------------------------------------------------
    all_rows   = list(existing_rows)
    new_rows   = []
    errors     = 0
    skipped    = 0
    n_prompts  = len(prompts)

    for i, p in enumerate(prompts, start=1):
        pid      = str(p.get("prompt_id",             "?"))
        text     = str(p.get("prompt_text",            ""))
        focus    = str(p.get("expected_failure_focus", ""))
        pressure = str(p.get("pressure_type",          ""))

        if resume and pid in already_done:
            print(f"  [SKIP]     {i}/{n_prompts}  prompt={pid}  (already generated)")
            skipped += 1
            continue

        print(f"  [GENERATE] {i}/{n_prompts}  prompt={pid}  pressure={pressure}  focus={focus}")

        try:
            output_text = generate_response(
                model=model,
                prompt=text,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            preview = output_text[:100].replace("\n", " ")
            print(f"             output: {preview}...")
            status = "ok"
        except CreditError as exc:
            output_text = f"[ERROR credit: {exc}]"
            print(f"             [CREDIT ERROR] {exc}")
            errors  += 1
            status   = "credit_error"
        except Exception as exc:
            output_text = f"[ERROR: {exc}]"
            print(f"             [ERROR] {exc}")
            errors += 1
            status  = "error"

        row = {
            "prompt_id":              pid,
            "prompt_text":            text,
            "model_name":             model,
            "output_text":            output_text,
            "temperature":            temperature,
            "repeat":                 repeat,
            "expected_failure_focus": focus,
        }
        new_rows.append(row)
        all_rows.append(row)

        if status == "credit_error":
            print()
            print("Stopping: credit error. Top up OpenRouter balance and re-run with --resume.")
            break

    if skipped:
        print(f"  [resume] Skipped {skipped} already-generated prompt(s).")
    if errors:
        print(f"  {errors} prompt(s) failed — output_text contains [ERROR] marker.")
    print()

    if not new_rows:
        print("No new rows generated (all already done or none selected).")
        return

    print(f"Saving {len(all_rows)} total row(s) ({len(new_rows)} new) to:")
    print(f"  {output_csv}")
    _save_csv(all_rows, output_csv)

    print()
    print("=" * 60)
    print("Done. Score with:")
    rel_out = output_csv.relative_to(_REPO_ROOT)
    print(
        f"  py 05_SRC/experiments/run_judge_calibration.py \\\n"
        f"      --input-csv {rel_out.as_posix()} \\\n"
        f"      --dry-run"
    )
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Generate high-pressure real model outputs for AOSL failure validation. "
            "Prompts are structurally redesigned to elicit false-premise acceptance, "
            "causal overclaiming, quantitative errors, and forced-certainty failures."
        )
    )
    parser.add_argument(
        "--model",
        default=_DEFAULT_MODEL,
        help=f"OpenRouter model ID for generation. Default: {_DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=_DEFAULT_TEMP,
        metavar="FLOAT",
        help=f"Sampling temperature. Default: {_DEFAULT_TEMP}",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=_DEFAULT_MAX_TOKENS,
        metavar="N",
        dest="max_tokens",
        help=f"Max tokens for each generated output. Default: {_DEFAULT_MAX_TOKENS}",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=_DEFAULT_REPEAT,
        metavar="N",
        help=f"Repeat index written to the output CSV. Default: {_DEFAULT_REPEAT}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Use only the first N prompts.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        metavar="N",
        dest="start_index",
        help="Start from prompt index N (after --limit). Default: 0",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        metavar="N",
        dest="chunk_size",
        help="Generate only N prompts from --start-index. Default: all remaining.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Load existing output CSV and skip prompt_ids already successfully generated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print generation plan without making any API calls or writing output.",
    )
    parser.add_argument(
        "--output-suffix",
        default=None,
        metavar="SUFFIX",
        dest="output_suffix",
        help=(
            "Append a suffix to the output filename. "
            "Writes to real_failure_validation_30_outputs_<suffix>.csv. "
            "Useful for running different generator models without overwriting existing outputs. "
            "Characters / \\ : and spaces are replaced with underscores and lowercased."
        ),
    )
    args = parser.parse_args()
    main(
        model         = args.model,
        temperature   = args.temperature,
        max_tokens    = args.max_tokens,
        repeat        = args.repeat,
        limit         = args.limit,
        start_index   = args.start_index,
        chunk_size    = args.chunk_size,
        resume        = args.resume,
        dry_run       = args.dry_run,
        output_suffix = args.output_suffix,
    )
