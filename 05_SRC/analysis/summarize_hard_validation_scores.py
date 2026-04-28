"""
summarize_hard_validation_scores.py

Reads the hard validation scoring CSV and prints a structured summary.
Writes the same summary to hard_validation_summary.txt.

Run:
    py 05_SRC/analysis/summarize_hard_validation_scores.py
"""

import sys
from pathlib import Path

import pandas as pd

# -- Paths ---------------------------------------------------------------------

_REPO_ROOT   = Path(__file__).resolve().parents[2]
RUN_DIR      = _REPO_ROOT / "04_RUNS" / "hard_validation"
CSV_PATH     = RUN_DIR / "hard_validation_scores.csv"
SUMMARY_PATH = RUN_DIR / "hard_validation_summary.txt"

# -- Constraint metadata -------------------------------------------------------

CONSTRAINT_NAMES = {
    "c1":  "c1  Factual Grounding",
    "c2":  "c2  Logical Coherence",
    "c3":  "c3  Causal Integrity",
    "c4":  "c4  Epistemic Calibration",
    "c5":  "c5  Scope Discipline",
    "c6":  "c6  Safety Integrity",
    "c7":  "c7  Uncertainty Acknowledgment",
    "c8":  "c8  Quantitative Accuracy",
    "c9":  "c9  Evidence Traceability",
    "c10": "c10 Constraint Interaction Consistency",
}
CONSTRAINT_COLS = list(CONSTRAINT_NAMES.keys())

TOP_N_DIVERGENT = 5


# -- Helpers -------------------------------------------------------------------

def _f(value, decimals: int = 4) -> str:
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def _section(lines: list, title: str) -> None:
    lines.append("")
    lines.append(f"  {title}")
    lines.append("  " + "-" * (len(title) + 2))


def _is_error_row(row: "pd.Series") -> bool:
    return str(row.get("stability_tier", "")).strip() == "ERROR" \
        or str(row.get("scorer_status",  "")).strip() == "error"


# -- Main ----------------------------------------------------------------------

def main() -> None:

    # -- Load ------------------------------------------------------------------
    if not CSV_PATH.exists():
        print(
            f"ERROR: CSV not found.\n"
            f"Expected : {CSV_PATH}\n\n"
            f"Generate it first by running:\n"
            f"    py 05_SRC/experiments/run_hard_validation_real_judge.py"
        )
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)

    for col in CONSTRAINT_COLS + ["divergence", "stability_score", "temperature"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Separate OK rows from error rows.
    if "stability_tier" in df.columns or "scorer_status" in df.columns:
        tier_col   = df.get("stability_tier",  pd.Series(dtype=str))
        status_col = df.get("scorer_status",   pd.Series(dtype=str))
        err_mask   = (tier_col.astype(str).str.strip() == "ERROR") | \
                     (status_col.astype(str).str.strip() == "error")
        ok  = df[~err_mask]
        err = df[err_mask]
    else:
        ok  = df
        err = df.iloc[0:0]   # empty

    # -- Build output lines ----------------------------------------------------
    lines: list = []
    lines.append("=" * 60)
    lines.append("AOSL Hard Validation Scores — Summary")
    lines.append("=" * 60)

    # 1. Row counts
    _section(lines, "Row Counts")
    lines.append(f"    Total rows      : {len(df)}")
    lines.append(f"    Successful rows : {len(ok)}")
    lines.append(f"    Error rows      : {len(err)}")

    if ok.empty:
        lines.append("")
        lines.append("  No successful rows. Cannot compute statistics.")
        lines.append("=" * 60)
        _print_and_write(lines)
        return

    # 2. Overall averages
    _section(lines, "Overall Averages (successful rows)")
    if "divergence" in ok.columns:
        lines.append(f"    Mean divergence     : {_f(ok['divergence'].mean())}")
    if "stability_score" in ok.columns:
        lines.append(f"    Mean stability_score: {_f(ok['stability_score'].mean())}")

    # 3. Stability tier counts
    if "stability_tier" in ok.columns:
        _section(lines, "Stability Tier Counts")
        tc = ok["stability_tier"].value_counts()
        for tier in ("S0", "S1", "S2", "S3"):
            lines.append(f"    {tier} : {tc.get(tier, 0)}")

    # 4. Mean score per constraint, sorted low to high
    present = [c for c in CONSTRAINT_COLS if c in ok.columns]
    if present:
        _section(lines, "Mean Score per Constraint (sorted low to high)")
        means = ok[present].mean().sort_values()
        for code, score in means.items():
            label  = CONSTRAINT_NAMES.get(code, code)
            marker = "  <- weakest" if code == means.index[0] else ""
            lines.append(f"    {label:<42}  {_f(score)}{marker}")

    # 5. Top N highest-divergence rows
    if "divergence" in ok.columns:
        _section(lines, f"Top {TOP_N_DIVERGENT} Highest-Divergence Rows")
        top = ok.nlargest(TOP_N_DIVERGENT, "divergence")
        for _, row in top.iterrows():
            pid   = row.get("prompt_id",  "?")
            focus = row.get("expected_failure_focus", "")
            div   = row.get("divergence",  float("nan"))
            tier  = row.get("stability_tier", "")
            lines.append(
                f"    prompt={pid:<5}  "
                f"divergence={_f(div)}  tier={tier}  "
                f"focus={focus}"
            )

    # 6. Mean divergence by expected_failure_focus
    if "expected_failure_focus" in ok.columns and "divergence" in ok.columns:
        _section(lines, "Mean Divergence by expected_failure_focus")
        grp = (
            ok.dropna(subset=["expected_failure_focus", "divergence"])
            .groupby("expected_failure_focus")["divergence"]
            .agg(["mean", "count"])
            .sort_values("mean", ascending=False)
        )
        for focus, row in grp.iterrows():
            lines.append(
                f"    {str(focus):<36}  "
                f"mean div = {_f(row['mean'])}  (n={int(row['count'])})"
            )
    else:
        _section(lines, "Mean Divergence by expected_failure_focus")
        lines.append("    (expected_failure_focus column not found)")

    # 7. Error rows
    if not err.empty:
        _section(lines, f"Error Rows ({len(err)})")
        msg_col = "error_message" if "error_message" in err.columns else "scorer_error"
        for _, row in err.iterrows():
            pid  = row.get("prompt_id", "?")
            msg  = str(row.get(msg_col, ""))[:120]
            lines.append(f"    prompt={pid}  {msg}")

    # Footer
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Source  : {CSV_PATH}")
    lines.append(f"  Written : {SUMMARY_PATH}")
    lines.append("=" * 60)

    _print_and_write(lines)


def _print_and_write(lines: list) -> None:
    text = "\n".join(lines) + "\n"
    print(text)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(text, encoding="utf-8")
    print(f"Summary written to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
