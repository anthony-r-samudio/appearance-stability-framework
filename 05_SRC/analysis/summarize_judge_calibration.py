"""
summarize_judge_calibration.py

Reads the judge calibration CSV and reports repeatability statistics.
Writes the same summary to judge_calibration_summary.txt.

Run:
    py 05_SRC/analysis/summarize_judge_calibration.py
"""

import re
import sys
from pathlib import Path

import pandas as pd

# -- Paths ---------------------------------------------------------------------

_REPO_ROOT   = Path(__file__).resolve().parents[2]
RUN_DIR      = _REPO_ROOT / "04_RUNS" / "judge_calibration"
CSV_PATH     = RUN_DIR / "judge_calibration_scores.csv"
SUMMARY_PATH = RUN_DIR / "judge_calibration_summary.txt"

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

TOP_N_VARIABLE = 5


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


def _focus_to_code(focus: str) -> "str | None":
    """Extract constraint code from expected_failure_focus. Returns None if not mappable."""
    m = re.match(r"^(c\d+)_", str(focus))
    return m.group(1) if m else None


def _print_and_write(lines: list) -> None:
    text = "\n".join(lines) + "\n"
    print(text)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(text, encoding="utf-8")
    print(f"Summary written to: {SUMMARY_PATH}")


# -- Main ----------------------------------------------------------------------

def main() -> None:

    # -- Load ------------------------------------------------------------------
    if not CSV_PATH.exists():
        print(
            f"ERROR: CSV not found.\n"
            f"Expected : {CSV_PATH}\n\n"
            f"Generate it first by running:\n"
            f"    py 05_SRC/experiments/run_judge_calibration.py"
        )
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)

    for col in CONSTRAINT_COLS + ["divergence", "stability_score", "calibration_repeat"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Separate OK rows from error rows.
    tier_col   = df["stability_tier"].astype(str).str.strip()   if "stability_tier" in df.columns else pd.Series("", index=df.index)
    status_col = df["scorer_status"].astype(str).str.strip()    if "scorer_status"  in df.columns else pd.Series("", index=df.index)
    err_mask   = (tier_col == "ERROR") | (status_col == "error")
    ok  = df[~err_mask].copy()
    err = df[err_mask].copy()

    # -- Build lines -----------------------------------------------------------
    lines: list = []
    lines.append("=" * 60)
    lines.append("AOSL Judge Calibration — Summary")
    lines.append("=" * 60)

    # 1. Row counts
    _section(lines, "Row Counts")
    lines.append(f"    Total scored rows   : {len(df)}")
    n_prompts = df["prompt_id"].nunique() if "prompt_id" in df.columns else "?"
    lines.append(f"    Unique prompt_ids   : {n_prompts}")
    n_repeats = int(ok["calibration_repeat"].nunique()) if "calibration_repeat" in ok.columns and not ok.empty else "?"
    lines.append(f"    Calibration repeats : {n_repeats}")
    lines.append(f"    Error rows          : {len(err)}")

    if ok.empty:
        lines.append("")
        lines.append("  No successful rows. Cannot compute statistics.")
        lines.append("=" * 60)
        _print_and_write(lines)
        return

    # 2. Overall mean divergence
    _section(lines, "Overall Mean Divergence (successful rows)")
    lines.append(f"    Mean divergence     : {_f(ok['divergence'].mean())}")
    lines.append(f"    Mean stability_score: {_f(ok['stability_score'].mean())}")

    # 3. Mean divergence by calibration_repeat
    if "calibration_repeat" in ok.columns:
        _section(lines, "Mean Divergence by calibration_repeat")
        grp = (
            ok.dropna(subset=["calibration_repeat", "divergence"])
            .groupby("calibration_repeat")["divergence"]
            .agg(["mean", "std", "count"])
            .sort_index()
        )
        for rpt, row in grp.iterrows():
            std_str = _f(row["std"]) if not pd.isna(row["std"]) else "N/A"
            lines.append(
                f"    repeat {int(rpt)}  "
                f"mean div = {_f(row['mean'])}  "
                f"std = {std_str}  "
                f"(n={int(row['count'])})"
            )

    # 4. Mean divergence by prompt_id
    if "prompt_id" in ok.columns:
        _section(lines, "Mean Divergence by prompt_id")
        by_prompt = (
            ok.groupby("prompt_id")["divergence"]
            .agg(["mean", "std", "count"])
            .sort_values("mean", ascending=False)
        )
        for pid, row in by_prompt.iterrows():
            std_str = _f(row["std"]) if not pd.isna(row["std"]) else "N/A (1 repeat)"
            lines.append(
                f"    {str(pid):<6}  "
                f"mean div = {_f(row['mean'])}  "
                f"std = {std_str}  "
                f"(n={int(row['count'])})"
            )

    # 5. Divergence std dev by prompt_id (variability ranking)
    if "prompt_id" in ok.columns:
        by_std = (
            ok.groupby("prompt_id")["divergence"]
            .std()
            .dropna()
            .sort_values(ascending=False)
        )
        if not by_std.empty:
            _section(lines, f"Highest Divergence Variability (top {TOP_N_VARIABLE} prompt_ids by std dev)")
            for pid, std in by_std.head(TOP_N_VARIABLE).items():
                focus = ""
                if "expected_failure_focus" in ok.columns:
                    matches = ok.loc[ok["prompt_id"] == pid, "expected_failure_focus"]
                    focus = str(matches.iloc[0]) if not matches.empty else ""
                lines.append(
                    f"    {str(pid):<6}  std dev = {_f(std)}  focus={focus}"
                )

    # 6. Mean score per constraint
    present = [c for c in CONSTRAINT_COLS if c in ok.columns]
    if present:
        _section(lines, "Mean Score per Constraint (sorted low to high)")
        means = ok[present].mean().sort_values()
        for code, score in means.items():
            label  = CONSTRAINT_NAMES.get(code, code)
            marker = "  <- weakest" if code == means.index[0] else ""
            lines.append(f"    {label:<42}  {_f(score)}{marker}")

    # 7. Constraint std dev across all repeats
    if present:
        _section(lines, "Constraint Score Std Dev across Repeats (sorted high to low)")
        stds = ok[present].std().sort_values(ascending=False)
        for code, std in stds.items():
            label = CONSTRAINT_NAMES.get(code, code)
            lines.append(f"    {label:<42}  std = {_f(std)}")

    # 8. Per-prompt weakest constraint + comparison to expected_failure_focus
    if present and "prompt_id" in ok.columns:
        _section(lines, "Weakest Constraint per prompt_id vs. Expected Failure Focus")
        pid_groups = ok.groupby("prompt_id")

        for pid, grp in sorted(pid_groups, key=lambda x: x[0]):
            constraint_means = grp[present].mean()
            weakest_code     = constraint_means.idxmin()
            weakest_score    = constraint_means.min()
            weakest_label    = CONSTRAINT_NAMES.get(weakest_code, weakest_code)

            focus = ""
            if "expected_failure_focus" in grp.columns:
                focus_vals = grp["expected_failure_focus"].dropna().unique()
                focus = str(focus_vals[0]) if len(focus_vals) > 0 else ""

            expected_code = _focus_to_code(focus)

            if expected_code is None:
                match_note = f"(no mapping for '{focus}')"
            elif weakest_code == expected_code:
                match_note = "MATCH"
            else:
                match_note = f"MISMATCH — expected {expected_code}"

            lines.append(
                f"    {str(pid):<6}  weakest={weakest_label:<42}  "
                f"mean={_f(weakest_score)}  {match_note}"
            )

    # 9. Interpretation
    _section(lines, "Judge Repeatability Interpretation")
    if "prompt_id" in ok.columns and not ok.empty:
        prompt_stds = ok.groupby("prompt_id")["divergence"].std().dropna()
        if prompt_stds.empty:
            lines.append("    Not enough repeats to compute variability (need >= 2).")
        else:
            avg_std = prompt_stds.mean()
            lines.append(f"    Average prompt-level divergence std dev : {_f(avg_std)}")
            lines.append("")
            if avg_std <= 0.10:
                lines.append("    Judge repeatability: acceptable initial stability")
            elif avg_std <= 0.20:
                lines.append("    Judge repeatability: moderate instability; rubric tightening recommended")
            else:
                lines.append("    Judge repeatability: high instability; judge/rubric calibration required")
    else:
        lines.append("    (insufficient data)")

    # 10. Error details
    if not err.empty:
        _section(lines, f"Error Rows ({len(err)})")
        msg_col = "error_message" if "error_message" in err.columns else "scorer_error"
        for _, row in err.iterrows():
            pid = row.get("prompt_id", "?")
            rpt = row.get("calibration_repeat", "?")
            msg = str(row.get(msg_col, ""))[:120]
            lines.append(f"    prompt={pid}  repeat={rpt}  {msg}")

    # Footer
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Source  : {CSV_PATH}")
    lines.append(f"  Written : {SUMMARY_PATH}")
    lines.append("=" * 60)

    _print_and_write(lines)


if __name__ == "__main__":
    main()
