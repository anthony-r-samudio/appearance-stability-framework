"""
summarize_openrouter_small_comparison.py

Reads the OpenRouter small comparison CSV and prints a structured summary.
Also writes the same summary to a .txt file.

Run:
    py 05_SRC/scripts/summarize_openrouter_small_comparison.py
"""

import sys
from pathlib import Path

import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────────

_REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
RUN_DIR      = _REPO_ROOT / "04_RUNS" / "openrouter_small_comparison"
CSV_PATH     = RUN_DIR / "openrouter_small_comparison.csv"
SUMMARY_PATH = RUN_DIR / "openrouter_small_comparison_summary.txt"

# ── Constraint metadata ──────────────────────────────────────────────────────────

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


# ── Formatting helpers ───────────────────────────────────────────────────────────

def _fmt(value) -> str:
    """Format a float to 4 decimal places, or return 'N/A' for missing values."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "N/A"


def _section(lines: list, title: str) -> None:
    """Append a titled section block to lines."""
    lines.append("")
    lines.append(f"  {title}")
    lines.append("  " + "-" * (len(title) + 2))


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:

    # ── Load CSV ─────────────────────────────────────────────────────────────────
    if not CSV_PATH.exists():
        print(
            f"ERROR: CSV file not found.\n"
            f"Expected: {CSV_PATH}\n\n"
            f"To generate it, run:\n"
            f"    py 05_SRC/scripts/run_openrouter_small_comparison.py"
        )
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)

    # Coerce numeric columns — they may read as strings if rows are mixed.
    for col in CONSTRAINT_COLS + ["D", "D_norm"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "temperature" in df.columns:
        df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    # Split OK rows from error rows.
    ok  = df[df["error"].isna() | (df["error"].astype(str).str.strip() == "")]
    err = df[~(df["error"].isna() | (df["error"].astype(str).str.strip() == ""))]

    # ── Build summary lines ───────────────────────────────────────────────────────
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("OpenRouter Small Comparison — Summary")
    lines.append("=" * 60)

    # 1. Row counts
    _section(lines, "Row Counts")
    lines.append(f"    Total rows      : {len(df)}")
    lines.append(f"    Successful rows : {len(ok)}")
    lines.append(f"    Error rows      : {len(err)}")

    if ok.empty:
        lines.append("")
        lines.append("  No successful rows found. Cannot compute statistics.")
        lines.append("=" * 60)
        _print_and_write(lines)
        return

    # 2–3. Average D and D_norm
    avg_D      = ok["D"].mean()
    avg_D_norm = ok["D_norm"].mean() if "D_norm" in ok.columns else avg_D / 10.0

    _section(lines, "Divergence Averages")
    lines.append(f"    Average D      : {_fmt(avg_D)}")
    lines.append(f"    Average D_norm : {_fmt(avg_D_norm)}")

    # 4. Stability tier counts
    _section(lines, "Stability Tier Counts")
    if "stability_tier" in ok.columns:
        tier_counts = ok["stability_tier"].value_counts()
        for tier in ("S0", "S1", "S2", "S3"):
            lines.append(f"    {tier} : {tier_counts.get(tier, 0)}")
    else:
        lines.append("    (stability_tier column not found)")

    # 5. Average D by generator_model
    _section(lines, "Average D by generator_model")
    if "generator_model" in ok.columns:
        by_model = ok.groupby("generator_model")["D"].agg(["mean", "count"])
        for model, row in by_model.iterrows():
            lines.append(f"    {str(model):<36}  avg D = {_fmt(row['mean'])}  (n={int(row['count'])})")
    else:
        lines.append("    (generator_model column not found)")

    # 6. Average D by temperature
    _section(lines, "Average D by temperature")
    if "temperature" in ok.columns:
        by_temp = ok.groupby("temperature")["D"].agg(["mean", "count"])
        for temp, row in by_temp.iterrows():
            lines.append(f"    temp={temp}  avg D = {_fmt(row['mean'])}  (n={int(row['count'])})")
    else:
        lines.append("    (temperature column not found)")

    # 7. Average D by prompt_id
    _section(lines, "Average D by prompt_id")
    if "prompt_id" in ok.columns:
        by_prompt = ok.groupby("prompt_id")["D"].agg(["mean", "count"])
        for pid, row in by_prompt.iterrows():
            lines.append(f"    {str(pid):<16}  avg D = {_fmt(row['mean'])}  (n={int(row['count'])})")
    else:
        lines.append("    (prompt_id column not found)")

    # 8. Weakest constraints by mean score
    _section(lines, "Constraint Mean Scores (c1–c10)")
    present_constraints = [c for c in CONSTRAINT_COLS if c in ok.columns]
    if present_constraints:
        means = ok[present_constraints].mean().sort_values()
        for code, score in means.items():
            label = CONSTRAINT_NAMES.get(code, code)
            marker = "  <-- weakest" if code == means.index[0] else ""
            lines.append(f"    {label:<42}  {_fmt(score)}{marker}")
    else:
        lines.append("    (no c1–c10 columns found)")

    # 9. Error details (if any)
    if not err.empty:
        _section(lines, f"Error Details ({len(err)} row(s))")
        for _, row in err.iterrows():
            rid   = row.get("record_id", "?")
            emsg  = str(row.get("error", ""))[:120]
            lines.append(f"    {rid} — {emsg}")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Source : {CSV_PATH}")
    lines.append(f"  Output : {SUMMARY_PATH}")
    lines.append("=" * 60)

    _print_and_write(lines)


def _print_and_write(lines: list[str]) -> None:
    """Print all lines to stdout and write them to SUMMARY_PATH."""
    text = "\n".join(lines) + "\n"
    print(text)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(text, encoding="utf-8")
    print(f"Summary written to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
