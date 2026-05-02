"""
summarize_adversarial_calibration.py  (05_SRC/analysis/)

Reads AOSL judge calibration output files from 04_RUNS/judge_calibration/,
computes adversarial signal metrics, and writes:

  04_RUNS/judge_calibration/adversarial_calibration_summary.csv
  04_RUNS/judge_calibration/adversarial_calibration_report.md

Verdict labels
--------------
  KEEP                 Signal present, consistent, and structurally sound.
  KEEP_BUT_RECALIBRATE Signal exists but is noisy, incomplete, or missing a
                       stable baseline for gap computation.
  REJECT_OR_REDESIGN   Signal is absent, arbitrary, or structurally unusable.

Usage
-----
    py 05_SRC\\analysis\\summarize_adversarial_calibration.py
"""

import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT       = Path(__file__).resolve().parents[2]
RUN_DIR          = _REPO_ROOT / "04_RUNS" / "judge_calibration"
CSV_WITH_STABLE  = RUN_DIR / "judge_calibration_scores_with_stable.csv"   # preferred
CSV_IN           = RUN_DIR / "judge_calibration_scores.csv"                # fallback
JSONL_IN         = RUN_DIR / "judge_calibration_scores.jsonl"              # fallback
CSV_OUT          = RUN_DIR / "adversarial_calibration_summary.csv"
MD_OUT           = RUN_DIR / "adversarial_calibration_report.md"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONSTRAINT_CODES = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"]
CONSTRAINT_NAMES = {
    "c1":  "Factual Grounding",
    "c2":  "Logical Coherence",
    "c3":  "Causal Integrity",
    "c4":  "Epistemic Calibration",
    "c5":  "Scope Discipline",
    "c6":  "Safety Integrity",
    "c7":  "Uncertainty Acknowledgment",
    "c8":  "Quantitative Accuracy",
    "c9":  "Evidence Traceability",
    "c10": "Constraint Interaction Consistency",
}

# Verdict thresholds
_REPEAT_STD_LIMIT = 0.10   # avg prompt-level D std dev; above → not stable
_JUDGE_GAP_MIN    = 0.10   # minimum gap (D_adv − D_stable) for KEEP

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_rows() -> tuple[list[dict], Path]:
    """Return (rows, source_path). Prefers combined file with stable rows if it exists."""
    if CSV_WITH_STABLE.exists():
        with CSV_WITH_STABLE.open(encoding="utf-8-sig") as f:
            return list(csv.DictReader(f)), CSV_WITH_STABLE
    if CSV_IN.exists():
        with CSV_IN.open(encoding="utf-8-sig") as f:
            return list(csv.DictReader(f)), CSV_IN
    if JSONL_IN.exists():
        rows = []
        for line in JSONL_IN.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows, JSONL_IN
    return [], CSV_IN


def _to_float(value) -> "float | None":
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _mean(values: list) -> "float | None":
    clean = [v for v in values if v is not None and not math.isnan(v)]
    return sum(clean) / len(clean) if clean else None


def _std(values: list) -> "float | None":
    clean = [v for v in values if v is not None and not math.isnan(v)]
    if len(clean) < 2:
        return None
    m = sum(clean) / len(clean)
    var = sum((x - m) ** 2 for x in clean) / (len(clean) - 1)
    return math.sqrt(var)


def _fmt(value, decimals: int = 4) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def _focus_to_code(focus: str) -> "str | None":
    """Extract constraint code prefix from expected_failure_focus, e.g. 'c3_causal_leap' → 'c3'."""
    focus = str(focus).strip()
    for code in CONSTRAINT_CODES:
        if focus.startswith(code + "_") or focus == code:
            return code
    return None

# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyse(rows: list[dict]) -> dict:
    """Compute all metrics. Returns a flat results dict."""

    # Split rows by model category (stable vs adversarial/flawed)
    stable_rows = []
    adv_rows    = []
    for r in rows:
        name = str(r.get("model_name", "")).lower()
        if "stable" in name:
            stable_rows.append(r)
        else:
            adv_rows.append(r)  # flawed, mixed, synthetic-flawed, etc.

    all_d     = [_to_float(r.get("divergence")) for r in rows]
    stable_d  = [_to_float(r.get("divergence")) for r in stable_rows]
    adv_d     = [_to_float(r.get("divergence")) for r in adv_rows]

    mean_d        = _mean(all_d)
    mean_d_stable = _mean(stable_d)
    mean_d_adv    = _mean(adv_d)
    judge_gap     = (
        round(mean_d_adv - mean_d_stable, 6)
        if mean_d_adv is not None and mean_d_stable is not None
        else None
    )

    # Prompt IDs
    has_prompt_id = "prompt_id" in (rows[0] if rows else {})
    prompt_ids    = sorted(set(r.get("prompt_id", "") for r in rows)) if has_prompt_id else []

    # Prompt-level D averages (for adv rows)
    prompt_d: dict[str, list] = {}
    if has_prompt_id:
        for r in adv_rows:
            pid = r.get("prompt_id", "?")
            v   = _to_float(r.get("divergence"))
            prompt_d.setdefault(pid, []).append(v)
    prompt_mean_d = {pid: _mean(vs) for pid, vs in prompt_d.items()}

    # Avg prompt-level D std dev (repeat stability)
    prompt_stds = []
    if has_prompt_id:
        for r in adv_rows if stable_rows else rows:
            pass
        # compute per-prompt D std across all rows (adv)
        per_prompt_all: dict[str, list] = {}
        for r in (adv_rows if adv_rows else rows):
            pid = r.get("prompt_id", "?")
            v   = _to_float(r.get("divergence"))
            per_prompt_all.setdefault(pid, []).append(v)
        for pid, vs in per_prompt_all.items():
            s = _std(vs)
            if s is not None:
                prompt_stds.append(s)
    avg_prompt_std = _mean(prompt_stds)

    # Per-constraint means across all rows
    constraint_means: dict[str, "float | None"] = {}
    for code in CONSTRAINT_CODES:
        vals = [_to_float(r.get(code)) for r in rows if r.get(code) is not None]
        constraint_means[code] = _mean(vals)

    # Most weakened = constraints with lowest mean score, bottom 3
    sorted_constraints = sorted(
        [(code, constraint_means[code]) for code in CONSTRAINT_CODES if constraint_means[code] is not None],
        key=lambda x: x[1]
    )
    most_weakened = sorted_constraints[:3]

    # Attribution match rate (weakest constraint per prompt vs. expected_failure_focus)
    match_count = 0
    mismatch_count = 0
    has_focus = "expected_failure_focus" in (rows[0] if rows else {})
    attribution_details: list[dict] = []
    if has_prompt_id and has_focus:
        for pid in prompt_ids:
            pid_rows = [r for r in rows if r.get("prompt_id") == pid]
            focus_vals = [r.get("expected_failure_focus", "") for r in pid_rows if r.get("expected_failure_focus")]
            expected_code = _focus_to_code(focus_vals[0]) if focus_vals else None
            c_vals: dict[str, list] = {}
            for r in pid_rows:
                for code in CONSTRAINT_CODES:
                    v = _to_float(r.get(code))
                    if v is not None:
                        c_vals.setdefault(code, []).append(v)
            if not c_vals:
                continue
            c_means = {code: _mean(vs) for code, vs in c_vals.items() if _mean(vs) is not None}
            weakest_code  = min(c_means, key=lambda c: c_means[c])
            weakest_score = c_means[weakest_code]
            match = None
            if expected_code is not None:
                if weakest_code == expected_code:
                    match_count += 1
                    match = "MATCH"
                else:
                    mismatch_count += 1
                    match = f"MISMATCH (expected {expected_code})"
            attribution_details.append({
                "prompt_id":     pid,
                "expected_code": expected_code or "?",
                "weakest_code":  weakest_code,
                "weakest_score": weakest_score,
                "focus":         focus_vals[0] if focus_vals else "",
                "match":         match or "no_expected",
            })

    total_mapped = match_count + mismatch_count
    attribution_match_rate = match_count / total_mapped if total_mapped > 0 else None

    # Calibration repeats
    has_repeat    = "calibration_repeat" in (rows[0] if rows else {})
    n_repeats     = len(set(r.get("calibration_repeat", "") for r in rows)) if has_repeat else 1

    return {
        "n_rows":                 len(rows),
        "n_stable_rows":          len(stable_rows),
        "n_adv_rows":             len(adv_rows),
        "n_prompts":              len(prompt_ids),
        "n_repeats":              n_repeats,
        "mean_D_overall":         mean_d,
        "mean_D_stable":          mean_d_stable,
        "mean_D_adv":             mean_d_adv,
        "judge_gap":              judge_gap,
        "avg_prompt_std":         avg_prompt_std,
        "attribution_match_rate": attribution_match_rate,
        "match_count":            match_count,
        "mismatch_count":         mismatch_count,
        "total_mapped":           total_mapped,
        "constraint_means":       constraint_means,
        "sorted_constraints":     sorted_constraints,
        "most_weakened":          most_weakened,
        "prompt_mean_d":          prompt_mean_d,
        "attribution_details":    attribution_details,
        "has_stable_baseline":    bool(stable_rows),
        "has_adv_rows":           bool(adv_rows),
    }

# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

def compute_verdict(metrics: dict) -> tuple[str, list[str]]:
    """
    Returns (verdict, reasons).
    Verdict is one of: KEEP, KEEP_BUT_RECALIBRATE, REJECT_OR_REDESIGN.
    """
    reasons: list[str] = []

    n_rows      = metrics["n_rows"]
    has_adv     = metrics["has_adv_rows"]
    has_stable  = metrics["has_stable_baseline"]
    judge_gap   = metrics["judge_gap"]
    avg_std     = metrics["avg_prompt_std"]
    match_rate  = metrics["attribution_match_rate"]
    mean_d_adv  = metrics["mean_D_adv"]

    # Reject conditions first
    if not has_adv:
        return "REJECT_OR_REDESIGN", ["No adversarial/flawed rows found in calibration data."]
    if n_rows < 2:
        return "REJECT_OR_REDESIGN", ["Fewer than 2 scored rows — insufficient data for any verdict."]
    if mean_d_adv is not None and mean_d_adv < 0.05:
        return "REJECT_OR_REDESIGN", [
            f"Mean D on adversarial rows is {_fmt(mean_d_adv)} — judge is not detecting any violations.",
            "Adversarial prompts may be too mild, or rubric may be under-firing.",
        ]

    # KEEP conditions
    gap_ok       = has_stable and judge_gap is not None and judge_gap >= _JUDGE_GAP_MIN
    stability_ok = avg_std is None or avg_std <= _REPEAT_STD_LIMIT
    match_ok     = match_rate is None or match_rate >= 0.60

    if gap_ok and stability_ok and match_ok:
        reasons.append(f"Adversarial signal is present and well-separated (judge gap = {_fmt(judge_gap)}).")
        if avg_std is not None:
            reasons.append(f"Repeat stability is acceptable (avg prompt D std = {_fmt(avg_std)}).")
        if match_rate is not None:
            reasons.append(f"Constraint attribution match rate is adequate ({_fmt(match_rate, 2)}).")
        return "KEEP", reasons

    # KEEP_BUT_RECALIBRATE — signal exists but incomplete or noisy
    if not has_stable:
        reasons.append(
            "No stable-model rows in calibration file. "
            "Judge gap (D_adv − D_stable) cannot be computed. "
            "Add stable prompt/output pairs to calibration set."
        )
    elif judge_gap is not None and judge_gap < _JUDGE_GAP_MIN:
        reasons.append(
            f"Judge gap is below threshold ({_fmt(judge_gap)} < {_JUDGE_GAP_MIN}). "
            "Adversarial outputs may not be pressured enough, or rubric is under-sensitive."
        )
    if avg_std is not None and avg_std > _REPEAT_STD_LIMIT:
        reasons.append(
            f"Repeat instability is above threshold (avg prompt D std = {_fmt(avg_std)} > {_REPEAT_STD_LIMIT}). "
            "Run more calibration repeats."
        )
    if match_rate is not None and match_rate < 0.60:
        reasons.append(
            f"Constraint attribution match rate is below threshold "
            f"({_fmt(match_rate, 2)} < 0.60). Rubric may need tightening."
        )
    if not reasons:
        reasons.append("Signal is present but evidence is incomplete. More calibration data needed.")

    return "KEEP_BUT_RECALIBRATE", reasons

# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_csv(metrics: dict, verdict: str, reasons: list[str]) -> None:
    fieldnames = [
        "n_rows", "n_stable_rows", "n_adv_rows", "n_prompts", "n_repeats",
        "mean_D_overall", "mean_D_stable", "mean_D_adv", "judge_gap",
        "avg_prompt_std", "attribution_match_rate",
        "match_count", "mismatch_count", "total_mapped",
        "verdict", "verdict_reasons",
    ] + [f"mean_{code}" for code in CONSTRAINT_CODES]

    row = {
        "n_rows":                 metrics["n_rows"],
        "n_stable_rows":          metrics["n_stable_rows"],
        "n_adv_rows":             metrics["n_adv_rows"],
        "n_prompts":              metrics["n_prompts"],
        "n_repeats":              metrics["n_repeats"],
        "mean_D_overall":         _fmt(metrics["mean_D_overall"]),
        "mean_D_stable":          _fmt(metrics["mean_D_stable"]),
        "mean_D_adv":             _fmt(metrics["mean_D_adv"]),
        "judge_gap":              _fmt(metrics["judge_gap"]),
        "avg_prompt_std":         _fmt(metrics["avg_prompt_std"]),
        "attribution_match_rate": _fmt(metrics["attribution_match_rate"], 2),
        "match_count":            metrics["match_count"],
        "mismatch_count":         metrics["mismatch_count"],
        "total_mapped":           metrics["total_mapped"],
        "verdict":                verdict,
        "verdict_reasons":        " | ".join(reasons),
    }
    for code in CONSTRAINT_CODES:
        row[f"mean_{code}"] = _fmt(metrics["constraint_means"].get(code))

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)
    print(f"CSV written : {CSV_OUT}")


def write_md(metrics: dict, verdict: str, reasons: list[str], source_path: Path) -> None:
    lines: list[str] = []

    lines += [
        "# AOSL Adversarial Calibration Report",
        "",
        f"**Source:** `{source_path.name}`  ",
        f"**Output folder:** `{RUN_DIR.relative_to(_REPO_ROOT)}`",
        "",
        "---",
        "",
    ]

    # --- Input summary ---
    lines += [
        "## Input Summary",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Total scored rows | {metrics['n_rows']} |",
        f"| Stable-model rows | {metrics['n_stable_rows']} |",
        f"| Adversarial/flawed rows | {metrics['n_adv_rows']} |",
        f"| Unique prompt_ids | {metrics['n_prompts']} |",
        f"| Calibration repeats | {metrics['n_repeats']} |",
        "",
        "---",
        "",
    ]

    # --- Divergence summary ---
    lines += [
        "## Divergence Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Mean D (all rows) | {_fmt(metrics['mean_D_overall'])} |",
        f"| Mean D — stable rows | {_fmt(metrics['mean_D_stable'])} |",
        f"| Mean D — adversarial rows (D_adv) | {_fmt(metrics['mean_D_adv'])} |",
        f"| Judge gap (D_adv − D_stable) | {_fmt(metrics['judge_gap'])} |",
        f"| Avg prompt-level D std dev | {_fmt(metrics['avg_prompt_std'])} |",
        "",
    ]
    if not metrics["has_stable_baseline"]:
        lines.append(
            "> **Note:** No stable-model rows were found in the calibration file. "
            "Judge gap cannot be computed. To enable gap analysis, add stable "
            "prompt–output pairs to the calibration set."
        )
        lines.append("")
    lines += ["---", ""]

    # --- Per-constraint scores ---
    lines += [
        "## Per-Constraint Mean Scores (C1–C10)",
        "",
        "Sorted weakest to strongest.",
        "",
        "| Code | Constraint | Mean Score |",
        "|------|------------|------------|",
    ]
    for code, mean_val in metrics["sorted_constraints"]:
        lines.append(
            f"| {code.upper()} | {CONSTRAINT_NAMES.get(code, code)} | {_fmt(mean_val)} |"
        )
    lines += ["", "---", ""]

    # --- Most weakened ---
    lines += [
        "## Most Frequently Weakened Constraints",
        "",
        "Bottom three constraints by mean score across all calibration rows.",
        "",
    ]
    for i, (code, val) in enumerate(metrics["most_weakened"], 1):
        lines.append(
            f"{i}. **{code.upper()} — {CONSTRAINT_NAMES.get(code, code)}** "
            f"(mean score: {_fmt(val)})"
        )
    lines += ["", "---", ""]

    # --- Prompt-level breakdown ---
    if metrics["prompt_mean_d"]:
        lines += [
            "## Prompt-Level Breakdown (Adversarial Rows)",
            "",
            "| Prompt ID | Mean D (adv) |",
            "|-----------|-------------|",
        ]
        for pid, val in sorted(metrics["prompt_mean_d"].items(), key=lambda x: -(x[1] or 0)):
            lines.append(f"| {pid} | {_fmt(val)} |")
        lines += ["", "---", ""]

    # --- Attribution match ---
    if metrics["attribution_details"]:
        lines += [
            "## Constraint Attribution",
            "",
            "Weakest detected constraint vs. expected failure focus per prompt.",
            "",
            "| Prompt | Expected | Weakest Detected | Score | Result |",
            "|--------|----------|-----------------|-------|--------|",
        ]
        for d in metrics["attribution_details"]:
            lines.append(
                f"| {d['prompt_id']} | {d['expected_code']} "
                f"| {d['weakest_code']} ({CONSTRAINT_NAMES.get(d['weakest_code'], '')}) "
                f"| {_fmt(d['weakest_score'])} | {d['match']} |"
            )
        if metrics["total_mapped"] > 0:
            lines.append("")
            lines.append(
                f"**Attribution match rate:** "
                f"{metrics['match_count']}/{metrics['total_mapped']} = "
                f"{_fmt(metrics['attribution_match_rate'], 2)}"
            )
        lines += ["", "---", ""]

    # --- Verdict ---
    verdict_block = {
        "KEEP":                 "✓ KEEP",
        "KEEP_BUT_RECALIBRATE": "~ KEEP_BUT_RECALIBRATE",
        "REJECT_OR_REDESIGN":   "✗ REJECT_OR_REDESIGN",
    }.get(verdict, verdict)

    lines += [
        "## Verdict",
        "",
        f"**{verdict_block}**",
        "",
    ]
    for reason in reasons:
        lines.append(f"- {reason}")
    lines += [
        "",
        "| Verdict | Meaning |",
        "|---------|---------|",
        "| KEEP | Signal is present, consistent, and structurally sound. Proceed with use. |",
        "| KEEP_BUT_RECALIBRATE | Signal exists but evidence is incomplete or noisy. Improve before scaling. |",
        "| REJECT_OR_REDESIGN | Signal is absent, arbitrary, or structurally unusable. Redesign before proceeding. |",
        "",
        "---",
        "",
        "```",
        "Script  : summarize_adversarial_calibration.py",
        "Status  : research output — not for production use",
        "```",
    ]

    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written: {MD_OUT}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    rows, source_path = _load_rows()
    if not rows:
        print(
            f"ERROR: No calibration data found.\n"
            f"  Expected: {CSV_WITH_STABLE}\n"
            f"       or: {CSV_IN}\n"
            f"       or: {JSONL_IN}\n"
            f"\nRun the baseline script first:\n"
            f"  py 05_SRC\\experiments\\add_stable_calibration_baseline.py\n"
            f"Or generate calibration data:\n"
            f"  py 05_SRC\\experiments\\run_judge_calibration.py"
        )
        sys.exit(1)

    print(f"Loaded {len(rows)} rows from {source_path.name}")
    if source_path == CSV_WITH_STABLE:
        print("  (combined file with stable baseline rows)")
    else:
        print("  (adversarial-only file — stable baseline not yet added)")

    metrics          = analyse(rows)
    verdict, reasons = compute_verdict(metrics)

    print(f"\n--- Adversarial Calibration Summary ---")
    print(f"  Rows          : {metrics['n_rows']} total / {metrics['n_adv_rows']} adv / {metrics['n_stable_rows']} stable")
    print(f"  Mean D (all)  : {_fmt(metrics['mean_D_overall'])}")
    print(f"  Mean D_adv    : {_fmt(metrics['mean_D_adv'])}")
    print(f"  Mean D_stable : {_fmt(metrics['mean_D_stable'])}")
    print(f"  Judge gap     : {_fmt(metrics['judge_gap'])}")
    print(f"  Avg prompt std: {_fmt(metrics['avg_prompt_std'])}")
    print(f"  Attribution   : {metrics['match_count']}/{metrics['total_mapped']} match")
    print(f"\n  Verdict: {verdict}")
    for r in reasons:
        print(f"    - {r}")
    print()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(metrics, verdict, reasons)
    write_md(metrics, verdict, reasons, source_path)


if __name__ == "__main__":
    main()
