"""
summarize_fast_batch_scores.py

Reads the fast batch scoring CSV and prints a structured statistical summary.
Writes the same summary to fast_batch_summary.txt.

Run:
    py 05_SRC/analysis/summarize_fast_batch_scores.py
"""

import sys
from pathlib import Path

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────────

_REPO_ROOT   = Path(__file__).resolve().parents[2]
RUN_DIR      = _REPO_ROOT / "04_RUNS" / "fast_batch_validation"
CSV_PATH     = RUN_DIR / "fast_batch_scores.csv"
SUMMARY_PATH = RUN_DIR / "fast_batch_summary.txt"

# ── Constraint metadata ───────────────────────────────────────────────────────────

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

TOP_N_DIVERGENT = 3   # how many highest-divergence rows to show


# ── Helpers ───────────────────────────────────────────────────────────────────────

def _f(value, decimals: int = 4) -> str:
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def _section(lines: list, title: str) -> None:
    lines.append("")
    lines.append(f"  {title}")
    lines.append("  " + "-" * (len(title) + 2))


def _groupby_mean(lines: list, df: pd.DataFrame, group_col: str, metric: str) -> None:
    """Append a per-group mean table to lines, or a note if the column is absent."""
    if group_col not in df.columns or metric not in df.columns:
        lines.append(f"    ('{group_col}' column not found — skipping)")
        return
    grp = (
        df.dropna(subset=[group_col, metric])
        .groupby(group_col)[metric]
        .agg(["mean", "count"])
    )
    if grp.empty:
        lines.append(f"    (no data for '{group_col}')")
        return
    for name, row in grp.iterrows():
        lines.append(
            f"    {str(name):<24}  mean {metric} = {_f(row['mean'])}  "
            f"(n={int(row['count'])})"
        )


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:

    # ── Load ─────────────────────────────────────────────────────────────────────
    if not CSV_PATH.exists():
        print(
            f"ERROR: CSV not found.\n"
            f"Expected : {CSV_PATH}\n\n"
            f"Generate it first by running:\n"
            f"    py 05_SRC/experiments/run_fast_batch_scoring_demo.py"
        )
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)

    # Coerce numeric columns.
    for col in CONSTRAINT_COLS + ["divergence", "stability_score", "temperature"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Build lines ───────────────────────────────────────────────────────────────
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("AOSL Fast Batch Scores — Summary")
    lines.append("=" * 60)

    # 1. Row counts
    _section(lines, "Row Counts")
    lines.append(f"    Total rows      : {len(df)}")

    # 2. Mean divergence and stability_score
    _section(lines, "Overall Averages")
    if "divergence" in df.columns:
        lines.append(f"    Mean divergence     : {_f(df['divergence'].mean())}")
    if "stability_score" in df.columns:
        lines.append(f"    Mean stability_score: {_f(df['stability_score'].mean())}")

    # 3. Stability tier counts
    if "stability_tier" in df.columns:
        _section(lines, "Stability Tier Counts")
        tc = df["stability_tier"].value_counts()
        for tier in ("S0", "S1", "S2", "S3"):
            lines.append(f"    {tier} : {tc.get(tier, 0)}")

    # 4. Mean score per constraint
    present = [c for c in CONSTRAINT_COLS if c in df.columns]
    if present:
        _section(lines, "Mean Score per Constraint (c1–c10, sorted low → high)")
        means = df[present].mean().sort_values()
        for code, score in means.items():
            label  = CONSTRAINT_NAMES.get(code, code)
            marker = "  ← weakest" if code == means.index[0] else ""
            lines.append(f"    {label:<42}  {_f(score)}{marker}")

    # 5. Highest-divergence rows
    if "divergence" in df.columns:
        _section(lines, f"Top {TOP_N_DIVERGENT} Highest-Divergence Rows")
        top = df.nlargest(TOP_N_DIVERGENT, "divergence")
        for _, row in top.iterrows():
            pid   = row.get("prompt_id",  "?")
            model = row.get("model_name", "?")
            temp  = row.get("temperature", "")
            div   = row.get("divergence",  float("nan"))
            lines.append(
                f"    prompt={pid}  model={model}  "
                f"temp={temp}  divergence={_f(div)}"
            )

    # 6. Grouped means by model_name
    _section(lines, "Mean divergence by model_name")
    _groupby_mean(lines, df, "model_name", "divergence")

    # 7. Grouped means by temperature
    _section(lines, "Mean divergence by temperature")
    _groupby_mean(lines, df, "temperature", "divergence")

    # Footer
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Source  : {CSV_PATH}")
    lines.append(f"  Written : {SUMMARY_PATH}")
    lines.append("=" * 60)

    # ── Output ────────────────────────────────────────────────────────────────────
    text = "\n".join(lines) + "\n"
    print(text)

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(text, encoding="utf-8")
    print(f"Summary written to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
