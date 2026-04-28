"""
summarize_judge_calibration.py

Reads the judge calibration CSV and reports repeatability statistics,
adversarial signal quality, and a strategic verdict.

Sections
--------
A  Basic run summary
B  Divergence summary (mean / min / max / std; by model category)
C  Constraint stability (mean, std, score distribution per constraint)
D  Repeat stability (per-prompt divergence std dev, most unstable prompts)
E  Adversarial signal (judge gap between flawed and stable outputs)
F  Strategic verdict  KEEP_ADV_JUDGE | KEEP_BUT_RECALIBRATE | DO_NOT_SCALE_YET

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
JSONL_PATH   = RUN_DIR / "judge_calibration_scores.jsonl"
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

# Verdict thresholds
_REPEAT_STD_LIMIT       = 0.10   # avg prompt-level D std dev — above → DO_NOT_SCALE_YET
_JUDGE_GAP_MIN          = 0.10   # min judge gap to claim useful signal
_MATCH_RATE_MIN         = 0.60   # min constraint attribution match rate
_CONSTRAINT_DRIFT_LIMIT = 0.40   # max per-prompt per-constraint std dev allowed for KEEP


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
    m = re.match(r"^(c\d+)_", str(focus))
    return m.group(1) if m else None


def _print_and_write(lines: list) -> None:
    text = "\n".join(lines) + "\n"
    print(text)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(text, encoding="utf-8")
    print(f"Summary written to: {SUMMARY_PATH}")


def _load_csv_or_jsonl() -> "pd.DataFrame | None":
    """Try CSV first, fall back to JSONL."""
    if CSV_PATH.exists():
        return pd.read_csv(CSV_PATH)
    if JSONL_PATH.exists():
        import json
        rows = []
        for line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return pd.DataFrame(rows) if rows else None
    return None


# -- Section builders ----------------------------------------------------------

def _section_a(lines: list, df: pd.DataFrame, ok: pd.DataFrame, err: pd.DataFrame) -> None:
    _section(lines, "A  Basic Run Summary")
    lines.append(f"    Total scored rows   : {len(df)}")
    n_prompts = df["prompt_id"].nunique() if "prompt_id" in df.columns else "?"
    lines.append(f"    Unique prompt_ids   : {n_prompts}")
    n_repeats = int(ok["calibration_repeat"].nunique()) if "calibration_repeat" in ok.columns and not ok.empty else "?"
    lines.append(f"    Calibration repeats : {n_repeats}")
    lines.append(f"    Error rows          : {len(err)}")
    if "scorer" in ok.columns and not ok.empty:
        scorers = ok["scorer"].dropna().unique().tolist()
        lines.append(f"    Scorer(s)           : {', '.join(str(s) for s in scorers)}")
    if "model_name" in ok.columns and not ok.empty:
        models = ok["model_name"].dropna().unique().tolist()
        lines.append(f"    Model names         : {', '.join(str(m) for m in sorted(models))}")


def _section_b(lines: list, ok: pd.DataFrame) -> None:
    _section(lines, "B  Divergence Summary")
    d = ok["divergence"].dropna()
    lines.append(f"    Mean D              : {_f(d.mean())}")
    lines.append(f"    Std  D              : {_f(d.std())}")
    lines.append(f"    Min  D              : {_f(d.min())}")
    lines.append(f"    Max  D              : {_f(d.max())}")
    lines.append(f"    Mean stability_score: {_f(ok['stability_score'].mean())}")

    # By model category if model_name present
    if "model_name" in ok.columns:
        lines.append("")
        lines.append("    Mean D by model category:")
        cats = {
            "stable":  ok[ok["model_name"].str.contains("stable", case=False, na=False)],
            "flawed":  ok[ok["model_name"].str.contains("flawed",  case=False, na=False)],
            "mixed":   ok[ok["model_name"].str.contains("mixed",   case=False, na=False)],
        }
        for label, subset in cats.items():
            if not subset.empty:
                lines.append(f"      {label:<8}  n={len(subset):<4}  mean D={_f(subset['divergence'].mean())}")

    # By calibration_repeat
    if "calibration_repeat" in ok.columns:
        lines.append("")
        lines.append("    Mean D by calibration_repeat:")
        grp = (
            ok.dropna(subset=["calibration_repeat", "divergence"])
            .groupby("calibration_repeat")["divergence"]
            .agg(["mean", "std", "count"])
            .sort_index()
        )
        for rpt, row in grp.iterrows():
            std_str = _f(row["std"]) if not pd.isna(row["std"]) else "N/A"
            lines.append(
                f"      repeat {int(rpt)}  mean={_f(row['mean'])}  std={std_str}  n={int(row['count'])}"
            )


def _section_c(lines: list, ok: pd.DataFrame, present: list) -> None:
    _section(lines, "C  Constraint Stability (c1-c10)")
    if not present:
        lines.append("    (no constraint columns found)")
        return
    lines.append(f"    {'Constraint':<44}  {'mean':>6}  {'std':>6}  {'#0':>4}  {'#0.5':>5}  {'#1':>4}")
    lines.append("    " + "-" * 76)
    means = ok[present].mean().sort_values()
    for code in means.index:
        col  = ok[code].dropna()
        mean = col.mean()
        std  = col.std()
        n0   = int((col == 0.0).sum())
        n05  = int((col == 0.5).sum())
        n1   = int((col == 1.0).sum())
        label = CONSTRAINT_NAMES.get(code, code)
        lines.append(
            f"    {label:<44}  {_f(mean):>6}  {_f(std):>6}  {n0:>4}  {n05:>5}  {n1:>4}"
        )


def _section_d(lines: list, ok: pd.DataFrame, present: list) -> None:
    _section(lines, "D  Repeat Stability")

    if "prompt_id" not in ok.columns:
        lines.append("    (prompt_id column missing)")
        return

    # Per-prompt divergence std dev
    by_prompt = (
        ok.groupby("prompt_id")["divergence"]
        .agg(["mean", "std", "count"])
        .sort_values("mean", ascending=False)
    )
    prompt_stds = ok.groupby("prompt_id")["divergence"].std().dropna()
    avg_std = prompt_stds.mean() if not prompt_stds.empty else float("nan")

    lines.append(f"    Avg prompt-level D std dev  : {_f(avg_std)}")
    stability_label = (
        "acceptable initial stability" if avg_std <= 0.10
        else "moderate instability — rubric tightening recommended" if avg_std <= 0.20
        else "high instability — judge/rubric recalibration required"
    )
    lines.append(f"    Repeatability               : {stability_label}")
    lines.append("")
    lines.append(f"    {'prompt_id':<8}  {'mean D':>7}  {'std D':>7}  {'n':>3}  expected_failure_focus")
    lines.append("    " + "-" * 62)
    for pid, row in by_prompt.iterrows():
        std_str = _f(row["std"]) if not pd.isna(row["std"]) else "N/A "
        focus = ""
        if "expected_failure_focus" in ok.columns:
            vals = ok.loc[ok["prompt_id"] == pid, "expected_failure_focus"].dropna().unique()
            focus = str(vals[0]) if len(vals) > 0 else ""
        lines.append(
            f"    {str(pid):<8}  {_f(row['mean']):>7}  {std_str:>7}  {int(row['count']):>3}  {focus}"
        )

    # Most unstable by std dev
    if not prompt_stds.empty:
        lines.append("")
        lines.append(f"    Top {TOP_N_VARIABLE} most unstable prompt_ids (by repeat std dev):")
        for pid, std in prompt_stds.sort_values(ascending=False).head(TOP_N_VARIABLE).items():
            focus = ""
            if "expected_failure_focus" in ok.columns:
                vals = ok.loc[ok["prompt_id"] == pid, "expected_failure_focus"].dropna().unique()
                focus = str(vals[0]) if len(vals) > 0 else ""
            lines.append(f"      {str(pid):<8}  std={_f(std)}  focus={focus}")

    # Per-prompt weakest constraint vs expected focus
    if present:
        lines.append("")
        lines.append("    Weakest constraint vs. expected failure focus:")
        for pid, grp in sorted(ok.groupby("prompt_id"), key=lambda x: x[0]):
            constraint_means = grp[present].mean()
            weakest_code  = constraint_means.idxmin()
            weakest_score = constraint_means.min()
            weakest_label = CONSTRAINT_NAMES.get(weakest_code, weakest_code)
            focus = ""
            if "expected_failure_focus" in grp.columns:
                vals = grp["expected_failure_focus"].dropna().unique()
                focus = str(vals[0]) if len(vals) > 0 else ""
            expected_code = _focus_to_code(focus)
            if expected_code is None:
                match_note = f"(no mapping for '{focus}')"
            elif weakest_code == expected_code:
                match_note = "MATCH"
            else:
                match_note = f"MISMATCH — expected {expected_code}"
            lines.append(
                f"      {str(pid):<8}  weakest={weakest_label:<42}  "
                f"mean={_f(weakest_score)}  {match_note}"
            )


def _section_e(lines: list, ok: pd.DataFrame) -> "float | None":
    """
    Adversarial signal summary.
    Uses model_name to split stable vs. flawed/mixed rows.
    Returns judge_gap (mean D flawed - mean D stable), or None if not computable.
    """
    _section(lines, "E  Adversarial Signal Summary")

    if "model_name" not in ok.columns or ok.empty:
        lines.append("    (model_name column missing — cannot compute adversarial signal)")
        return None

    stable_mask = ok["model_name"].str.contains("stable", case=False, na=False)
    flawed_mask = ok["model_name"].str.contains("flawed|mixed", case=False, na=False)
    stable = ok[stable_mask]
    adv    = ok[flawed_mask]

    if stable.empty:
        lines.append("    (no stable-model rows found — cannot compute baseline D)")
        return None
    if adv.empty:
        lines.append("    (no flawed/mixed-model rows found — cannot compute adversarial D)")
        return None

    mean_stable = stable["divergence"].mean()
    mean_adv    = adv["divergence"].mean()
    judge_gap   = mean_adv - mean_stable

    lines.append(f"    Mean D — stable rows       : {_f(mean_stable)}  (n={len(stable)})")
    lines.append(f"    Mean D — flawed/mixed rows  : {_f(mean_adv)}  (n={len(adv)})")
    lines.append(f"    Judge gap (adv − stable)    : {_f(judge_gap)}")
    lines.append("")

    signal_quality = (
        "strong" if judge_gap > 0.20
        else "moderate" if judge_gap > 0.10
        else "weak"
    )
    lines.append(f"    Signal quality              : {signal_quality}")

    # Per-prompt gap vs. stable baseline
    if "prompt_id" in ok.columns:
        lines.append("")
        lines.append(f"    {'prompt_id':<8}  {'mean D':>7}  {'gap vs stable':>14}  {'repeat std':>11}  focus")
        lines.append("    " + "-" * 70)
        by_prompt = ok.groupby("prompt_id")
        rows_sorted = sorted(
            by_prompt,
            key=lambda x: x[1]["divergence"].mean() - mean_stable,
            reverse=True,
        )
        for pid, grp in rows_sorted:
            mean_d  = grp["divergence"].mean()
            gap_row = mean_d - mean_stable
            std_d   = grp["divergence"].std()
            std_str = _f(std_d) if not pd.isna(std_d) else "N/A "
            focus   = ""
            if "expected_failure_focus" in grp.columns:
                vals  = grp["expected_failure_focus"].dropna().unique()
                focus = str(vals[0]) if len(vals) > 0 else ""
            lines.append(
                f"    {str(pid):<8}  {_f(mean_d):>7}  {_f(gap_row):>14}  {std_str:>11}  {focus}"
            )

    return judge_gap


def _section_f(lines: list, ok: pd.DataFrame, judge_gap: "float | None", present: list) -> None:
    _section(lines, "F  Strategic Verdict")

    # --- Compute metrics -------------------------------------------------------

    # Avg prompt-level repeat std dev
    avg_prompt_std = float("nan")
    if "prompt_id" in ok.columns and not ok.empty:
        prompt_stds = ok.groupby("prompt_id")["divergence"].std().dropna()
        avg_prompt_std = prompt_stds.mean() if not prompt_stds.empty else 0.0

    # Per-prompt per-constraint std dev — find max and count drifty pairs
    max_constraint_drift = 0.0
    drifty_pairs: list = []
    if present and "prompt_id" in ok.columns:
        for pid, grp in ok.groupby("prompt_id"):
            for code in present:
                vals = grp[code].dropna()
                if len(vals) < 2:
                    continue
                std = float(vals.std())
                if std > max_constraint_drift:
                    max_constraint_drift = std
                if std > _CONSTRAINT_DRIFT_LIMIT:
                    drifty_pairs.append(f"{pid}/{code}({_f(std, 2)})")

    # Constraint attribution match rate
    match_count = mismatch_count = 0
    if "prompt_id" in ok.columns and "expected_failure_focus" in ok.columns and present:
        for pid, grp in ok.groupby("prompt_id"):
            vals = grp["expected_failure_focus"].dropna().unique()
            focus = str(vals[0]) if len(vals) > 0 else ""
            expected_code = _focus_to_code(focus)
            if expected_code is None:
                continue
            constraint_means = grp[present].mean()
            weakest = constraint_means.idxmin()
            if weakest == expected_code:
                match_count += 1
            else:
                mismatch_count += 1
    total_mapped = match_count + mismatch_count
    match_rate = match_count / total_mapped if total_mapped > 0 else 0.0

    # --- Print diagnostics ----------------------------------------------------

    std_ok  = not pd.isna(avg_prompt_std)
    gap_ok  = judge_gap is not None

    lines.append(f"    Avg prompt repeat std dev       : {_f(avg_prompt_std)}  (limit={_REPEAT_STD_LIMIT})")
    lines.append(f"    Max per-prompt constraint drift : {_f(max_constraint_drift)}  (limit={_CONSTRAINT_DRIFT_LIMIT})")
    lines.append(
        f"    Attribution match rate          : {_f(match_rate, 2)}"
        f"  ({match_count} MATCH / {mismatch_count} MISMATCH / {total_mapped} mapped)"
        f"  (min={_MATCH_RATE_MIN})"
    )
    lines.append(f"    Judge gap                       : {_f(judge_gap) if gap_ok else 'N/A'}  (min={_JUDGE_GAP_MIN})")
    if drifty_pairs:
        lines.append(f"    High-drift pairs (std>{_CONSTRAINT_DRIFT_LIMIT})   : {', '.join(drifty_pairs[:10])}")
    lines.append("")

    # --- Verdict rules (evaluated in priority order) --------------------------

    if std_ok and avg_prompt_std > _REPEAT_STD_LIMIT:
        verdict = "DO_NOT_SCALE_YET"
        reason  = (
            f"Repeat instability too high "
            f"(avg prompt D std dev={_f(avg_prompt_std)} > {_REPEAT_STD_LIMIT}). "
            "Run more calibration repeats and tighten rubric before scaling."
        )
    elif (
        gap_ok
        and judge_gap > _JUDGE_GAP_MIN
        and match_rate >= _MATCH_RATE_MIN
        and max_constraint_drift <= _CONSTRAINT_DRIFT_LIMIT
    ):
        verdict = "KEEP_ADV_JUDGE"
        reason  = (
            f"Judge consistently detects flawed outputs "
            f"(gap={_f(judge_gap)}), repeat variance is acceptable "
            f"(avg std={_f(avg_prompt_std)}), and constraint attribution "
            f"match rate is adequate ({_f(match_rate, 2)})."
        )
    else:
        verdict = "KEEP_BUT_RECALIBRATE"
        reasons = []
        if not gap_ok or (judge_gap is not None and judge_gap <= _JUDGE_GAP_MIN):
            reasons.append(f"weak adversarial signal (gap={_f(judge_gap)})")
        if match_rate < _MATCH_RATE_MIN:
            reasons.append(
                f"constraint attribution match rate below threshold "
                f"({_f(match_rate, 2)} < {_MATCH_RATE_MIN})"
            )
        if max_constraint_drift > _CONSTRAINT_DRIFT_LIMIT:
            reasons.append(
                f"some constraint scores drift across repeats "
                f"(max drift={_f(max_constraint_drift)} > {_CONSTRAINT_DRIFT_LIMIT})"
            )
        reason = "Signal detected but: " + "; ".join(reasons) + "."

    lines.append(f"    Reason  : {reason}")
    lines.append("")
    border = "=" * (len(verdict) + 4)
    lines.append(f"    {border}")
    lines.append(f"    | {verdict} |")
    lines.append(f"    {border}")


# -- Main ----------------------------------------------------------------------

def main() -> None:

    # -- Load ------------------------------------------------------------------
    df = _load_csv_or_jsonl()
    if df is None:
        print(
            f"ERROR: No calibration output found.\n"
            f"Expected : {CSV_PATH}\n"
            f"       or: {JSONL_PATH}\n\n"
            f"Generate it first by running:\n"
            f"    py 05_SRC/experiments/run_judge_calibration.py"
        )
        sys.exit(1)

    for col in CONSTRAINT_COLS + ["divergence", "stability_score", "calibration_repeat"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    tier_col   = df["stability_tier"].astype(str).str.strip()   if "stability_tier" in df.columns else pd.Series("", index=df.index)
    status_col = df["scorer_status"].astype(str).str.strip()    if "scorer_status"  in df.columns else pd.Series("", index=df.index)
    err_mask   = (tier_col == "ERROR") | (status_col == "error")
    ok  = df[~err_mask].copy()
    err = df[err_mask].copy()

    present = [c for c in CONSTRAINT_COLS if c in ok.columns]

    # -- Build lines -----------------------------------------------------------
    lines: list = []
    lines.append("=" * 60)
    lines.append("AOSL Judge Calibration — Summary")
    lines.append("=" * 60)

    if ok.empty:
        lines.append("")
        lines.append("  No successful rows. Cannot compute statistics.")
        lines.append("=" * 60)
        _print_and_write(lines)
        return

    _section_a(lines, df, ok, err)
    _section_b(lines, ok)
    _section_c(lines, ok, present)
    _section_d(lines, ok, present)
    judge_gap = _section_e(lines, ok)
    _section_f(lines, ok, judge_gap, present)

    # -- Error details ---------------------------------------------------------
    if not err.empty:
        _section(lines, f"Error Rows ({len(err)})")
        msg_col = "error_message" if "error_message" in err.columns else "scorer_error"
        for _, row in err.iterrows():
            pid = row.get("prompt_id", "?")
            rpt = row.get("calibration_repeat", "?")
            msg = str(row.get(msg_col, ""))[:120]
            lines.append(f"    prompt={pid}  repeat={rpt}  {msg}")

    # -- Footer ----------------------------------------------------------------
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Source  : {CSV_PATH}")
    lines.append(f"  Written : {SUMMARY_PATH}")
    lines.append("=" * 60)

    _print_and_write(lines)


if __name__ == "__main__":
    main()
