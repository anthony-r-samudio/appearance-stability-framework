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

import argparse
import csv
import json
import math
import sys
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
_REPEAT_STD_LIMIT       = 0.10   # avg prompt-level D std dev; above → not stable
_JUDGE_GAP_MIN          = 0.10   # minimum gap (D_adv − D_stable) for KEEP
_ATTRIBUTION_MIN        = 0.60   # primary-weakest match rate for KEEP
_COFIRED_FIRED_RATE_MIN = 0.60   # expected constraint fired (at all) rate for KEEP

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

    # Avg prompt-level D std dev (repeat stability) — computed on adversarial rows
    prompt_stds = []
    if has_prompt_id:
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

    # Co-firing: does the expected constraint fire at all (not just be weakest)?
    # A constraint "fires" when its mean score < 1.0 for a given prompt's adversarial rows.
    cofiring_details: list[dict] = []
    expected_fired_count  = 0
    cofired_total_mapped  = 0

    if has_prompt_id and has_focus and attribution_details:
        for d in attribution_details:
            pid           = d["prompt_id"]
            expected_code = d["expected_code"] if d["expected_code"] != "?" else None

            # Use only adversarial rows for this prompt
            pid_adv = [r for r in adv_rows if r.get("prompt_id") == pid]
            if not pid_adv:
                pid_adv = [r for r in rows if r.get("prompt_id") == pid]

            c_pid: dict[str, list] = {}
            for r in pid_adv:
                for code in CONSTRAINT_CODES:
                    v = _to_float(r.get(code))
                    if v is not None:
                        c_pid.setdefault(code, []).append(v)
            c_means_pid = {
                code: _mean(vs) for code, vs in c_pid.items() if _mean(vs) is not None
            }
            fired_codes = sorted(
                code for code, m in c_means_pid.items() if m is not None and m < 1.0
            )
            n_fired      = len(fired_codes)
            expected_fired = None
            if expected_code is not None:
                cofired_total_mapped += 1
                expected_fired = expected_code in fired_codes
                if expected_fired:
                    expected_fired_count += 1

            cofiring_details.append({
                "prompt_id":      pid,
                "expected_code":  expected_code or "?",
                "fired_codes":    ", ".join(fired_codes) if fired_codes else "none",
                "n_fired":        n_fired,
                "expected_fired": expected_fired,  # None if no expected code
            })

    expected_constraint_fired_rate = (
        expected_fired_count / cofired_total_mapped
        if cofired_total_mapped > 0 else None
    )

    # Calibration repeats
    has_repeat = "calibration_repeat" in (rows[0] if rows else {})
    n_repeats  = len(set(r.get("calibration_repeat", "") for r in rows)) if has_repeat else 1

    return {
        "n_rows":                        len(rows),
        "n_stable_rows":                 len(stable_rows),
        "n_adv_rows":                    len(adv_rows),
        "n_prompts":                     len(prompt_ids),
        "n_repeats":                     n_repeats,
        "mean_D_overall":                mean_d,
        "mean_D_stable":                 mean_d_stable,
        "mean_D_adv":                    mean_d_adv,
        "judge_gap":                     judge_gap,
        "avg_prompt_std":                avg_prompt_std,
        "attribution_match_rate":        attribution_match_rate,
        "match_count":                   match_count,
        "mismatch_count":                mismatch_count,
        "total_mapped":                  total_mapped,
        "expected_constraint_fired_rate": expected_constraint_fired_rate,
        "expected_fired_count":          expected_fired_count,
        "cofired_total_mapped":          cofired_total_mapped,
        "constraint_means":              constraint_means,
        "sorted_constraints":            sorted_constraints,
        "most_weakened":                 most_weakened,
        "prompt_mean_d":                 prompt_mean_d,
        "attribution_details":           attribution_details,
        "cofiring_details":              cofiring_details,
        "has_stable_baseline":           bool(stable_rows),
        "has_adv_rows":                  bool(adv_rows),
    }

# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

def compute_verdicts(metrics: dict) -> dict:
    """
    Returns a dict with keys: detection, attribution, cofiring, overall.
    Each value is a (verdict_str, reasons_list) tuple.
    verdict_str is one of: KEEP, KEEP_BUT_RECALIBRATE, REJECT_OR_REDESIGN.
    """
    n_rows       = metrics["n_rows"]
    has_adv      = metrics["has_adv_rows"]
    has_stable   = metrics["has_stable_baseline"]
    judge_gap    = metrics["judge_gap"]
    avg_std      = metrics["avg_prompt_std"]
    match_rate   = metrics["attribution_match_rate"]
    mean_d_adv   = metrics["mean_D_adv"]
    cofired_rate = metrics.get("expected_constraint_fired_rate")

    # --- Detection verdict (judge gap + repeat stability) ---
    det_reasons: list[str] = []
    if not has_adv or n_rows < 2:
        det_verdict = "REJECT_OR_REDESIGN"
        det_reasons.append("No adversarial rows or insufficient data.")
    elif mean_d_adv is not None and mean_d_adv < 0.05:
        det_verdict = "REJECT_OR_REDESIGN"
        det_reasons.append(
            f"Mean D_adv = {_fmt(mean_d_adv)} — judge is not detecting violations."
        )
    elif not has_stable:
        det_verdict = "KEEP_BUT_RECALIBRATE"
        det_reasons.append("No stable baseline — judge gap cannot be computed.")
    elif judge_gap is not None and judge_gap < _JUDGE_GAP_MIN:
        det_verdict = "KEEP_BUT_RECALIBRATE"
        det_reasons.append(
            f"Judge gap {_fmt(judge_gap)} < {_JUDGE_GAP_MIN} threshold. "
            "Adversarial outputs may not be pressured enough."
        )
    elif avg_std is not None and avg_std > _REPEAT_STD_LIMIT:
        det_verdict = "KEEP_BUT_RECALIBRATE"
        det_reasons.append(
            f"Repeat instability: avg prompt D std = {_fmt(avg_std)} > {_REPEAT_STD_LIMIT}. "
            "Run more calibration repeats."
        )
    else:
        det_verdict = "KEEP"
        det_reasons.append(f"Judge gap = {_fmt(judge_gap)} (>= {_JUDGE_GAP_MIN} threshold).")
        if avg_std is not None:
            det_reasons.append(f"Repeat stability OK: avg prompt D std = {_fmt(avg_std)}.")
        else:
            det_reasons.append("Repeat stability: only one repeat — cannot assess.")

    # --- Attribution verdict (primary-weakest constraint match) ---
    attr_reasons: list[str] = []
    if match_rate is None:
        attr_verdict = "KEEP_BUT_RECALIBRATE"
        attr_reasons.append(
            "No expected_failure_focus data — attribution cannot be assessed."
        )
    elif match_rate >= _ATTRIBUTION_MIN:
        attr_verdict = "KEEP"
        attr_reasons.append(
            f"Attribution match rate {_fmt(match_rate, 2)} >= {_ATTRIBUTION_MIN} threshold."
        )
    else:
        attr_verdict = "KEEP_BUT_RECALIBRATE"
        attr_reasons.append(
            f"Attribution match rate {_fmt(match_rate, 2)} < {_ATTRIBUTION_MIN} threshold. "
            "Expected constraint was not consistently the primary weakest constraint."
        )

    # --- Co-firing verdict (expected constraint fires at all) ---
    cf_reasons: list[str] = []
    if cofired_rate is None:
        cf_verdict = "KEEP_BUT_RECALIBRATE"
        cf_reasons.append(
            "Co-firing rate could not be computed — no expected_failure_focus data."
        )
    elif cofired_rate >= _COFIRED_FIRED_RATE_MIN:
        cf_verdict = "KEEP"
        cf_reasons.append(
            f"Expected constraint fired in {_fmt(cofired_rate, 2)} of mapped prompts "
            f"(>= {_COFIRED_FIRED_RATE_MIN} threshold)."
        )
    else:
        cf_verdict = "KEEP_BUT_RECALIBRATE"
        cf_reasons.append(
            f"Expected constraint fired rate {_fmt(cofired_rate, 2)} < {_COFIRED_FIRED_RATE_MIN}. "
            "Expected constraints not consistently triggering even as secondary failures."
        )

    # --- Overall (conservative: worst sub-verdict wins) ---
    sub_verdicts = [det_verdict, attr_verdict, cf_verdict]
    if "REJECT_OR_REDESIGN" in sub_verdicts:
        overall = "REJECT_OR_REDESIGN"
    elif all(v == "KEEP" for v in sub_verdicts):
        overall = "KEEP"
    else:
        overall = "KEEP_BUT_RECALIBRATE"

    overall_reasons = (
        [f"[Detection] {r}"   for r in det_reasons]
        + [f"[Attribution] {r}" for r in attr_reasons]
        + [f"[Co-firing] {r}"   for r in cf_reasons]
    )

    return {
        "detection":   (det_verdict,  det_reasons),
        "attribution": (attr_verdict, attr_reasons),
        "cofiring":    (cf_verdict,   cf_reasons),
        "overall":     (overall,      overall_reasons),
    }


def compute_verdict(metrics: dict) -> tuple[str, list[str]]:
    """Backward-compatible wrapper. Returns (overall_verdict, overall_reasons)."""
    return compute_verdicts(metrics)["overall"]

# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_csv(metrics: dict, verdicts: dict, out_path: "Path | None" = None) -> None:
    out_path = out_path or CSV_OUT

    det_v,  det_r  = verdicts["detection"]
    attr_v, attr_r = verdicts["attribution"]
    cf_v,   cf_r   = verdicts["cofiring"]
    ov_v,   ov_r   = verdicts["overall"]

    fieldnames = [
        "n_rows", "n_stable_rows", "n_adv_rows", "n_prompts", "n_repeats",
        "mean_D_overall", "mean_D_stable", "mean_D_adv", "judge_gap",
        "avg_prompt_std",
        "attribution_match_rate", "expected_constraint_fired_rate",
        "match_count", "mismatch_count", "total_mapped",
        "verdict_detection", "verdict_attribution", "verdict_cofiring", "verdict_overall",
        "verdict_reasons",
    ] + [f"mean_{code}" for code in CONSTRAINT_CODES]

    row = {
        "n_rows":                          metrics["n_rows"],
        "n_stable_rows":                   metrics["n_stable_rows"],
        "n_adv_rows":                      metrics["n_adv_rows"],
        "n_prompts":                       metrics["n_prompts"],
        "n_repeats":                       metrics["n_repeats"],
        "mean_D_overall":                  _fmt(metrics["mean_D_overall"]),
        "mean_D_stable":                   _fmt(metrics["mean_D_stable"]),
        "mean_D_adv":                      _fmt(metrics["mean_D_adv"]),
        "judge_gap":                       _fmt(metrics["judge_gap"]),
        "avg_prompt_std":                  _fmt(metrics["avg_prompt_std"]),
        "attribution_match_rate":          _fmt(metrics["attribution_match_rate"], 2),
        "expected_constraint_fired_rate":  _fmt(metrics.get("expected_constraint_fired_rate"), 2),
        "match_count":                     metrics["match_count"],
        "mismatch_count":                  metrics["mismatch_count"],
        "total_mapped":                    metrics["total_mapped"],
        "verdict_detection":               det_v,
        "verdict_attribution":             attr_v,
        "verdict_cofiring":                cf_v,
        "verdict_overall":                 ov_v,
        "verdict_reasons":                 " | ".join(ov_r),
    }
    for code in CONSTRAINT_CODES:
        row[f"mean_{code}"] = _fmt(metrics["constraint_means"].get(code))

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)
    print(f"CSV written : {out_path}")


def write_md(metrics: dict, verdicts: dict, source_path: Path,
             out_path: "Path | None" = None) -> None:
    out_path   = out_path or MD_OUT
    folder_rel = source_path.parent.relative_to(_REPO_ROOT)
    lines: list[str] = []

    det_v,  det_r  = verdicts["detection"]
    attr_v, attr_r = verdicts["attribution"]
    cf_v,   cf_r   = verdicts["cofiring"]
    ov_v,   ov_r   = verdicts["overall"]

    _VERDICT_LABEL = {
        "KEEP":                 "KEEP",
        "KEEP_BUT_RECALIBRATE": "KEEP_BUT_RECALIBRATE",
        "REJECT_OR_REDESIGN":   "REJECT_OR_REDESIGN",
    }

    lines += [
        "# AOSL Adversarial Calibration Report",
        "",
        f"**Source:** `{source_path.name}`  ",
        f"**Output folder:** `{folder_rel}`",
        "",
        "---",
        "",
    ]

    # --- Input summary ---
    lines += [
        "## Input Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
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

    # --- Co-firing analysis ---
    if metrics.get("cofiring_details"):
        lines += [
            "## Constraint Co-Firing Analysis",
            "",
            "Whether the expected constraint fired at all (score < 1.0) on adversarial rows, "
            "regardless of whether it was the primary weakest constraint.",
            "",
            "| Prompt | Expected | Fired Constraints | # Fired | Expected Fired? |",
            "|--------|----------|-------------------|---------|-----------------|",
        ]
        for d in metrics["cofiring_details"]:
            ef = d["expected_fired"]
            if ef is None:
                ef_label = "N/A"
            elif ef:
                ef_label = "YES"
            else:
                ef_label = f"NO ({d['expected_code']} silent)"
            lines.append(
                f"| {d['prompt_id']} | {d['expected_code']} "
                f"| {d['fired_codes']} | {d['n_fired']} | {ef_label} |"
            )
        n_fired_total  = metrics["expected_fired_count"]
        n_total_mapped = metrics["cofired_total_mapped"]
        rate           = metrics.get("expected_constraint_fired_rate")
        lines.append("")
        lines.append(
            f"**Expected constraint fired rate:** "
            f"{n_fired_total}/{n_total_mapped} = {_fmt(rate, 2)}"
        )
        lines += ["", "---", ""]

    # --- Verdict (sub-verdicts + overall) ---
    def _vblock(v: str) -> str:
        return {
            "KEEP":                 "KEEP",
            "KEEP_BUT_RECALIBRATE": "KEEP_BUT_RECALIBRATE",
            "REJECT_OR_REDESIGN":   "REJECT_OR_REDESIGN",
        }.get(v, v)

    lines += [
        "## Verdict",
        "",
        "### Detection",
        f"**{_vblock(det_v)}**",
        "",
    ]
    for r in det_r:
        lines.append(f"- {r}")
    lines += [""]

    lines += [
        "### Attribution",
        f"**{_vblock(attr_v)}**",
        "",
    ]
    for r in attr_r:
        lines.append(f"- {r}")
    lines += [""]

    lines += [
        "### Co-Firing",
        f"**{_vblock(cf_v)}**",
        "",
    ]
    for r in cf_r:
        lines.append(f"- {r}")
    lines += [""]

    lines += [
        "### Overall",
        f"**{_vblock(ov_v)}**",
        "",
        "The overall verdict is the most conservative of the three sub-verdicts above.",
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

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written: {out_path}")


# ---------------------------------------------------------------------------
# Path resolution for --run-dir
# ---------------------------------------------------------------------------

def _resolve_run_paths(run_dir: "Path | None") -> tuple[list[dict], Path, Path, Path]:
    """
    Return (rows, source_path, out_csv, out_md).

    When run_dir is None: use the module-level defaults (existing 3-prompt set).
    When run_dir is given: scan for the first *scores*.csv in that directory
    (excluding *summary* files) and name outputs after the directory stem.
    """
    if run_dir is None:
        rows, src = _load_rows()
        return rows, src, CSV_OUT, MD_OUT

    # -- Custom run dir --------------------------------------------------------
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        print(f"ERROR: --run-dir directory does not exist: {run_dir}")
        sys.exit(1)

    # Find input CSV: prefer *_scores_with_stable.csv, then first *scores*.csv
    candidates = sorted(
        [p for p in run_dir.glob("*scores*.csv") if "summary" not in p.name.lower()],
        key=lambda p: ("with_stable" not in p.name, p.name),
    )
    if not candidates:
        print(f"ERROR: No '*scores*.csv' file found in {run_dir}")
        print("       Run the build script first, then retry.")
        sys.exit(1)

    src = candidates[0]
    with src.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    stem    = run_dir.name                    # e.g. "judge_calibration_12"
    out_csv = run_dir / f"{stem}_summary.csv"
    out_md  = run_dir / f"{stem}_report.md"
    return rows, src, out_csv, out_md


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute adversarial calibration metrics and write CSV + Markdown report."
    )
    parser.add_argument(
        "--run-dir",
        default=None,
        metavar="PATH",
        help=(
            "Directory containing a '*scores*.csv' file to analyse. "
            "Output files are written to this directory, named after the directory. "
            "Default: 04_RUNS/judge_calibration/ (existing 3-prompt set)."
        ),
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else None
    if run_dir is not None and not run_dir.is_absolute():
        run_dir = _REPO_ROOT / run_dir

    rows, source_path, out_csv, out_md = _resolve_run_paths(run_dir)

    if not rows:
        print(
            f"ERROR: No calibration data found.\n"
            f"  Looked in: {source_path.parent}\n"
            f"\nRun the baseline script first:\n"
            f"  py 05_SRC\\experiments\\add_stable_calibration_baseline.py\n"
            f"Or build the 12-prompt set:\n"
            f"  py 05_SRC\\experiments\\build_12_prompt_calibration_set.py"
        )
        sys.exit(1)

    print(f"Loaded {len(rows)} rows from {source_path.name}")
    if run_dir is None and source_path == CSV_WITH_STABLE:
        print("  (combined file with stable baseline rows)")
    elif run_dir is None:
        print("  (adversarial-only file — stable baseline not yet added)")

    metrics  = analyse(rows)
    verdicts = compute_verdicts(metrics)

    det_v,  _ = verdicts["detection"]
    attr_v, _ = verdicts["attribution"]
    cf_v,   _ = verdicts["cofiring"]
    ov_v,   _ = verdicts["overall"]

    print(f"\n--- Adversarial Calibration Summary ---")
    print(f"  Rows          : {metrics['n_rows']} total / {metrics['n_adv_rows']} adv / {metrics['n_stable_rows']} stable")
    print(f"  Mean D (all)  : {_fmt(metrics['mean_D_overall'])}")
    print(f"  Mean D_adv    : {_fmt(metrics['mean_D_adv'])}")
    print(f"  Mean D_stable : {_fmt(metrics['mean_D_stable'])}")
    print(f"  Judge gap     : {_fmt(metrics['judge_gap'])}")
    print(f"  Avg prompt std: {_fmt(metrics['avg_prompt_std'])}")
    print(f"  Attribution   : {metrics['match_count']}/{metrics['total_mapped']} match "
          f"= {_fmt(metrics['attribution_match_rate'], 2)}")
    print(f"  Co-firing     : {metrics['expected_fired_count']}/{metrics['cofired_total_mapped']} fired "
          f"= {_fmt(metrics.get('expected_constraint_fired_rate'), 2)}")
    print(f"\n  Detection verdict    : {det_v}")
    print(f"  Attribution verdict  : {attr_v}")
    print(f"  Co-firing verdict    : {cf_v}")
    print(f"  Overall verdict      : {ov_v}")
    print()

    source_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(metrics, verdicts, out_csv)
    write_md(metrics, verdicts, source_path, out_md)


if __name__ == "__main__":
    main()
