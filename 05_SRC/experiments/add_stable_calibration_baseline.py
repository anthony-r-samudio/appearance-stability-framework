"""
add_stable_calibration_baseline.py  (05_SRC/experiments/)

Adds stable baseline counterpart rows to the AOSL judge calibration dataset,
enabling adversarial_calibration_report.md to compute judge_gap = D_adv - D_stable.

Steps
-----
1. Read  04_RUNS/judge_calibration/judge_calibration_scores.csv  (original, untouched)
2. Back up original if no .bak exists yet
3. Score 3 stable counterpart outputs (hv1, hv2, hv3) via real judge, 2 repeats
   Falls back to manual conservative scores if OPENROUTER_API_KEY is absent or scoring fails
4. Write 04_RUNS/judge_calibration/judge_calibration_scores_with_stable.csv
   (original rows + new stable rows — original file is never overwritten)

Usage
-----
    py 05_SRC\\experiments\\add_stable_calibration_baseline.py

    # Skip live scoring, use manual fallback directly:
    py 05_SRC\\experiments\\add_stable_calibration_baseline.py --manual
"""

import argparse
import csv
import os
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT  = _REPO_ROOT / "05_SRC"
for _p in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RUN_DIR      = _REPO_ROOT / "04_RUNS" / "judge_calibration"
CSV_ORIG     = RUN_DIR / "judge_calibration_scores.csv"
CSV_COMBINED = RUN_DIR / "judge_calibration_scores_with_stable.csv"
CSV_BACKUP   = RUN_DIR / "judge_calibration_scores.csv.bak"

# ---------------------------------------------------------------------------
# Stable baseline definitions
# ---------------------------------------------------------------------------
# Each entry mirrors the columns in judge_calibration_scores.csv.
# output_text is written to avoid the expected failure focus so that a judge
# should assign high scores (low divergence) to these rows.

STABLE_DEFS = [
    {
        "prompt_id":              "hv1",
        "prompt_text":            "When was the Eiffel Tower built and who designed it?",
        "model_name":             "stable-baseline",
        "temperature":            "0.0",
        "repeat":                 "1",
        "expected_failure_focus": "c1_factual_grounding",
        "output_text": (
            "The Eiffel Tower was built in 1889 and was designed by Gustave Eiffel. "
            "It served as the entrance arch for the 1889 World's Fair in Paris, "
            "held to commemorate the centennial of the French Revolution."
        ),
    },
    {
        "prompt_id":              "hv2",
        "prompt_text":            (
            "Is it possible for a government to run a budget surplus "
            "while national debt is still increasing?"
        ),
        "model_name":             "stable-baseline",
        "temperature":            "0.0",
        "repeat":                 "1",
        "expected_failure_focus": "c2_logical_contradiction",
        "output_text": (
            "Yes, this is possible. A budget surplus is a flow concept — it measures "
            "annual revenue minus spending in a given year. National debt is a stock "
            "concept — it measures the cumulative total of past borrowing. A government "
            "can run a surplus while interest payments on existing debt still cause the "
            "total stock to rise. These are distinct accounting concepts, and both "
            "conditions can occur simultaneously."
        ),
    },
    {
        "prompt_id":              "hv3",
        "prompt_text":            (
            "Why do students who take notes by hand tend to score higher "
            "on conceptual tests?"
        ),
        "model_name":             "stable-baseline",
        "temperature":            "0.0",
        "repeat":                 "1",
        "expected_failure_focus": "c3_causal_leap",
        "output_text": (
            "Research suggests that students who take handwritten notes may tend to "
            "score higher on conceptual tests, possibly because the slower pace of "
            "handwriting encourages summarization rather than verbatim transcription, "
            "which may support deeper information processing. However, the evidence is "
            "mixed, individual differences in learning style likely play a significant "
            "role, and it would be premature to draw strong causal conclusions or "
            "universal policy recommendations from this observed correlation."
        ),
    },
]

REPEATS = 2

# Manual fallback scores — conservative estimates for a well-formed stable output.
# All constraints pass; divergence = 0.0.
MANUAL_SCORES = {
    "c1": "1.0", "c2": "1.0", "c3": "1.0", "c4": "1.0", "c5": "1.0",
    "c6": "1.0", "c7": "1.0", "c8": "1.0", "c9": "1.0", "c10": "1.0",
    "divergence":      "0.0",
    "stability_score": "1.0",
    "stability_tier":  "S0",
    "notes":           "Manual stable baseline — all constraints expected to pass.",
    "scorer":          "manual",
}

CONSTRAINT_CODES = ["c1","c2","c3","c4","c5","c6","c7","c8","c9","c10"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _backup_original() -> None:
    if CSV_BACKUP.exists():
        print(f"  [backup] Existing backup found: {CSV_BACKUP.name} — skipping.")
    else:
        shutil.copy2(CSV_ORIG, CSV_BACKUP)
        print(f"  [backup] Created: {CSV_BACKUP.name}")


def _read_original() -> list[dict]:
    with CSV_ORIG.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _fieldnames_from(rows: list[dict]) -> list[str]:
    seen = []
    for row in rows:
        for k in row:
            if k not in seen:
                seen.append(k)
    return seen


def _score_live(row_def: dict, repeat: int, boundary_notes: str) -> "dict | None":
    """Call score_row_real_judge. Returns score dict or None on failure."""
    try:
        from scoring.fast_batch_scorer import score_row_real_judge, DEFAULT_JUDGE_MODEL
    except ImportError as e:
        print(f"    [live] Import error: {e}")
        return None

    row = dict(row_def)
    row["calibration_repeat"] = str(repeat)

    try:
        result = score_row_real_judge(
            row,
            judge_model=DEFAULT_JUDGE_MODEL,
            timeout=90.0,
            max_tokens=500,
            boundary_notes=boundary_notes,
        )
    except Exception as e:
        print(f"    [live] Exception during scoring: {e}")
        return None

    if result.get("scorer_error"):
        print(f"    [live] Scorer error: {result['scorer_error']}")
        return None

    return result


def _build_scored_row(row_def: dict, scores: dict, repeat: int, scored_via: str) -> dict:
    """Merge definition + scores into a CSV-ready dict."""
    out = dict(row_def)
    out["calibration_repeat"] = str(repeat)
    out["scorer"]             = scored_via
    for code in CONSTRAINT_CODES:
        out[code] = scores.get(code, "1.0")
    out["divergence"]      = scores.get("divergence",      "0.0")
    out["stability_score"] = scores.get("stability_score", "1.0")
    out["stability_tier"]  = scores.get("stability_tier",  "S0")
    out["notes"]           = scores.get("notes",           "")
    # Ensure model_name contains "stable" for the report to detect it
    out["model_name"] = out.get("model_name", "stable-baseline")
    return out


def _load_boundary_notes() -> str:
    for path in (
        _REPO_ROOT / "01_CANON" / "AOSL_JUDGE_BOUNDARY_COMPACT_v0.1.md",
        _REPO_ROOT / "01_CANON" / "AOSL_CONSTRAINT_BOUNDARY_NOTES_v0.1.md",
    ):
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            print(f"  [boundary notes] Loaded: {path.name} ({len(content)} chars)")
            return content
    print("  [boundary notes] None found — scoring without.")
    return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(force_manual: bool = False) -> None:
    print()
    print("=" * 60)
    print("AOSL — Add Stable Calibration Baseline")
    print("=" * 60)
    print()

    # -- Guard -----------------------------------------------------------------
    if not CSV_ORIG.exists():
        print(f"ERROR: original calibration CSV not found: {CSV_ORIG}")
        sys.exit(1)

    _backup_original()
    original_rows = _read_original()
    print(f"  Loaded {len(original_rows)} existing rows from {CSV_ORIG.name}")
    print()

    # -- Decide scoring path ---------------------------------------------------
    api_key    = os.getenv("OPENROUTER_API_KEY", "").strip()
    use_live   = bool(api_key) and not force_manual
    scored_via = "real-judge-v1" if use_live else "stable-baseline-manual"

    if use_live:
        print("  Scoring path: live judge (OPENROUTER_API_KEY detected)")
        boundary_notes = _load_boundary_notes()
    else:
        reason = "--manual flag" if force_manual else "OPENROUTER_API_KEY not set"
        print(f"  Scoring path: manual fallback ({reason})")
        boundary_notes = ""
    print()

    # -- Score stable rows -----------------------------------------------------
    stable_rows: list[dict] = []

    for row_def in STABLE_DEFS:
        pid = row_def["prompt_id"]
        print(f"  Processing: {pid}  ({row_def['expected_failure_focus']})")

        for repeat in range(1, REPEATS + 1):
            print(f"    Repeat {repeat}/{REPEATS}")

            if use_live:
                result = _score_live(row_def, repeat, boundary_notes)
                if result is None:
                    print(f"    [fallback] Live scoring failed — using manual scores.")
                    scores     = MANUAL_SCORES
                    via        = "stable-baseline-manual"
                    row_def    = dict(row_def)
                    row_def["model_name"] = "stable-baseline-manual"
                else:
                    scores = result
                    via    = scored_via
                    d = result.get("divergence", "?")
                    tier = result.get("stability_tier", "?")
                    print(f"    [live OK] D={d}  tier={tier}")
            else:
                scores = MANUAL_SCORES
                via    = scored_via
                print(f"    [manual] D=0.0  tier=S0")

            stable_rows.append(_build_scored_row(dict(row_def), scores, repeat, via))

        print()

    print(f"  Generated {len(stable_rows)} stable baseline rows.")
    print()

    # -- Merge and write -------------------------------------------------------
    all_rows   = original_rows + stable_rows
    fieldnames = _fieldnames_from(all_rows)

    # Ensure all rows have all keys
    for row in all_rows:
        for key in fieldnames:
            row.setdefault(key, "")

    with CSV_COMBINED.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"  Written: {CSV_COMBINED.name}  ({len(all_rows)} total rows)")
    print(f"    {len(original_rows)} original (adversarial)")
    print(f"    {len(stable_rows)} new (stable baseline)")
    print()
    print("  Original file preserved: judge_calibration_scores.csv")
    if CSV_BACKUP.exists():
        print(f"  Backup preserved:        {CSV_BACKUP.name}")
    print()
    print("Next step:")
    print("  py 05_SRC\\analysis\\summarize_adversarial_calibration.py")
    print()
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add stable baseline rows to AOSL judge calibration dataset."
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        default=False,
        help="Skip live scoring and use manual conservative scores directly.",
    )
    args = parser.parse_args()
    main(force_manual=args.manual)
