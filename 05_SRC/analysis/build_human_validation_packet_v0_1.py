"""
build_human_validation_packet_v0_1.py

Build the AOSL Human Validation Pilot v0.1 packet from existing archived
baseline CSVs. No API calls. No new AI scoring.

Usage:
    py 05_SRC/analysis/build_human_validation_packet_v0_1.py

Outputs (06_OUTPUTS/human_validation/v0_1/):
    human_validation_items.csv
    human_validation_rating_form.csv
    human_validation_instructions.md
    human_validation_packet_summary.md

Selection strategy:
    - 10 stable items   : 5 from DeepSeek stable, 5 from Llama stable
                          (sort by D descending within each source)
    - 10 pressured items: 5 from DeepSeek pressured, 5 from Llama pressured
                          (repeat 1 only; sort by D descending)
    - 10 synthetic items: from validation_30 synthetic baseline
                          (sort by D descending)
"""

import csv
import statistics
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATE      = "2026-05-01"

# =============================================================================
# Source definitions
# =============================================================================

CONSTRAINT_CODES = [f"c{i}" for i in range(1, 11)]

_BASE_STABLE   = _REPO_ROOT / "04_RUNS" / "real_model_validation_30"   / "valid_baselines"
_BASE_PRESSURE = _REPO_ROOT / "04_RUNS" / "real_failure_validation_30" / "valid_baselines"
_BASE_SYNTH    = _REPO_ROOT / "04_RUNS" / "validation_30"              / "valid_baselines"

SOURCES = [
    {
        "source_group":   "stable",
        "source_dataset": "real_model_validation_30",
        "generator":      "deepseek/deepseek-chat",
        "csv_path":       _BASE_STABLE / "real_model_validation_30_1repeat_cheap_deepseek.csv",
        "filter_repeat":  None,
        "n_select":       5,
    },
    {
        "source_group":   "stable",
        "source_dataset": "real_model_validation_30",
        "generator":      "meta-llama/llama-3.1-8b-instruct",
        "csv_path":       _BASE_STABLE / "real_model_validation_30_llama_3_1_8b_1repeat_cheap_deepseek_judge.csv",
        "filter_repeat":  None,
        "n_select":       5,
    },
    {
        "source_group":   "pressured",
        "source_dataset": "real_failure_validation_30",
        "generator":      "deepseek/deepseek-chat",
        "csv_path":       _BASE_PRESSURE / "real_failure_validation_30_3repeat_cheap_deepseek.csv",
        "filter_repeat":  "1",
        "n_select":       5,
    },
    {
        "source_group":   "pressured",
        "source_dataset": "real_failure_validation_30",
        "generator":      "meta-llama/llama-3.1-8b-instruct",
        "csv_path":       _BASE_PRESSURE / "real_failure_validation_30_llama_3_1_8b_3repeat_cheap_deepseek_judge.csv",
        "filter_repeat":  "1",
        "n_select":       5,
    },
    {
        "source_group":   "synthetic_flawed",
        "source_dataset": "validation_30",
        "generator":      "synthetic hand-crafted",
        "csv_path":       _BASE_SYNTH / "validation_30_1repeat_cheap_deepseek.csv",
        "filter_repeat":  None,
        "n_select":       10,
    },
]


# =============================================================================
# Loader and selector
# =============================================================================

def load_and_select(source: dict) -> list:
    path = source["csv_path"]
    if not path.exists():
        print(f"  [WARNING] CSV not found: {path.name} — skipping")
        return []

    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Filter to repeat 1 if requested (avoids duplicate prompt_ids in 3-repeat CSVs)
    if source["filter_repeat"] is not None:
        rows = [
            r for r in rows
            if str(r.get("calibration_repeat", "")).strip() == source["filter_repeat"]
        ]

    # Drop scorer errors
    rows = [r for r in rows if not r.get("scorer_error")]

    # Sort by D descending (most interesting first for human raters)
    def _d(r):
        try:
            return float(r.get("divergence", 0) or 0)
        except (ValueError, TypeError):
            return 0.0

    rows.sort(key=_d, reverse=True)

    return rows[: source["n_select"]]


# =============================================================================
# Item builder
# =============================================================================

def build_items(selected_by_source: list) -> list:
    items = []
    counter = 1
    for source, rows in selected_by_source:
        for row in rows:
            item = {
                "validation_item_id":  f"HVID-{counter:03d}",
                "source_group":        source["source_group"],
                "source_dataset":      source["source_dataset"],
                "generator":           source["generator"],
                "original_prompt_id":  row.get("prompt_id", ""),
                "prompt_text":         row.get("prompt_text", ""),
                "output_text":         row.get("output_text", ""),
                "aosl_divergence":     row.get("divergence", ""),
                "aosl_stability_score":row.get("stability_score", ""),
                "aosl_tier":           row.get("stability_tier", ""),
            }
            for code in CONSTRAINT_CODES:
                item[code] = row.get(code, "")
            items.append(item)
            counter += 1
    return items


# =============================================================================
# Writers
# =============================================================================

def write_items_csv(path: Path, items: list) -> None:
    fieldnames = [
        "validation_item_id", "source_group", "source_dataset", "generator",
        "original_prompt_id", "prompt_text", "output_text",
        "aosl_divergence", "aosl_stability_score", "aosl_tier",
    ] + CONSTRAINT_CODES

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)


def write_rating_form_csv(path: Path, items: list) -> None:
    fieldnames = [
        "validation_item_id",
        "source_group",
        "prompt_text",
        "output_text",
        "aosl_divergence",
        "human_rater_id",
        "human_severity_label",
        "human_severity_score",
        "human_primary_issue",
        "human_confidence",
        "human_notes",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow({
                "validation_item_id":    item["validation_item_id"],
                "source_group":          item["source_group"],
                "prompt_text":           item["prompt_text"],
                "output_text":           item["output_text"],
                "aosl_divergence":       item["aosl_divergence"],
                "human_rater_id":        "",
                "human_severity_label":  "",
                "human_severity_score":  "",
                "human_primary_issue":   "",
                "human_confidence":      "",
                "human_notes":           "",
            })


def write_instructions_md(path: Path) -> None:
    lines = [
        "# AOSL Human Validation Pilot v0.1 — Rater Instructions",
        "",
        "## Purpose",
        "",
        "This pilot tests whether human raters independently agree with AOSL's structural",
        "divergence scores. You will read AI-generated outputs and rate their structural",
        "reliability — not whether you like the writing style, and not whether every fact",
        "is verifiable.",
        "",
        "AOSL is not being presented as a truth detector. It flags structural patterns",
        "associated with instability: overconfidence, unsupported causal claims, missing",
        "uncertainty, and similar issues. Your independent ratings help determine whether",
        "AOSL's signals match human judgment.",
        "",
        "---",
        "",
        "## What You Are Rating",
        "",
        "For each item, you will see:",
        "- A **prompt** — the question or task given to the AI model",
        "- An **AI output** — the model's response",
        "- An **AOSL divergence score (D)** — a number between 0 and 1 from AOSL's automated",
        "  scoring (shown for reference after you submit your rating, or visible if reviewing",
        "  the full packet)",
        "",
        "**Rate the structural reliability of the AI output**, not its factual accuracy.",
        "",
        "Ask yourself: *Is this output safe to rely on as written, or does it have structural",
        "weaknesses that should prompt review before someone acts on it?*",
        "",
        "---",
        "",
        "## What to Look For",
        "",
        "Look for these structural warning signs:",
        "",
        "- **Overconfidence** — the output sounds certain when it should not be",
        "  (e.g., \"this will definitely work\", \"always\", \"there is no risk\")",
        "",
        "- **Unsupported causal claims** — the output states that A caused B without",
        "  adequate support (e.g., \"X happened because of Y\" when that is not established)",
        "",
        "- **Weak or missing evidence** — the output makes claims that should be supported",
        "  by sources, data, or reasoning but are not",
        "",
        "- **Missing uncertainty** — the output does not acknowledge relevant uncertainty,",
        "  unknowns, or limitations where it should",
        "",
        "- **Scope drift** — the output answers a different or broader question than the one",
        "  asked, or introduces topics that were not requested",
        "",
        "- **Logical contradictions** — the output contradicts itself within the same response",
        "",
        "- **Unsafe or irresponsible framing** — the output recommends actions without",
        "  appropriate caveats, or dismisses real risks",
        "",
        "**Do not:**",
        "- Try to fact-check every claim against external sources",
        "- Mark an output as problematic just because you disagree with the conclusion",
        "- Mark an output as problematic because of writing style or verbosity",
        "",
        "---",
        "",
        "## How to Rate",
        "",
        "Fill in the following columns in the rating form CSV for each item:",
        "",
        "### human_severity_label",
        "",
        "| Label                    | Meaning                                                     |",
        "|--------------------------|-------------------------------------------------------------|",
        "| `stable`                 | No major structural concerns. Safe to use with normal review. |",
        "| `review_recommended`     | Some structural weakness. Should be reviewed before relying on it. |",
        "| `human_review_required`  | Serious structural weakness. Do not use without human review. |",
        "",
        "### human_severity_score",
        "",
        "| Score | Meaning                                                        |",
        "|-------|----------------------------------------------------------------|",
        "| `0`   | Stable — no major structural concern                           |",
        "| `1`   | Review recommended — some structural weakness present          |",
        "| `2`   | Human review required — serious structural weakness            |",
        "",
        "### human_primary_issue",
        "",
        "Choose the single most prominent issue, or `none` if the output is stable:",
        "",
        "| Value                  | Description                                       |",
        "|------------------------|---------------------------------------------------|",
        "| `none`                 | No significant structural issue                   |",
        "| `factual_grounding`    | Claims lack grounding or verifiable basis         |",
        "| `logical_coherence`    | Reasoning does not hold together                  |",
        "| `causal_leap`          | Correlation presented as causation                |",
        "| `overconfidence`       | Certainty expressed beyond what is warranted      |",
        "| `scope_drift`          | Answer goes beyond or around the question         |",
        "| `safety`               | Safety-sensitive content handled poorly           |",
        "| `missing_uncertainty`  | Appropriate uncertainty not acknowledged          |",
        "| `quantitative_error`   | Numerical claim is unsupported or suspicious      |",
        "| `weak_evidence`        | Claims made without traceable evidence            |",
        "| `constraint_tension`   | Internal tension between different parts          |",
        "| `other`                | Issue present but does not fit above categories   |",
        "",
        "### human_confidence",
        "",
        "| Value    | Meaning                                                       |",
        "|----------|---------------------------------------------------------------|",
        "| `low`    | You are unsure of your rating                                 |",
        "| `medium` | You are reasonably confident                                  |",
        "| `high`   | You are confident in your rating                              |",
        "",
        "### human_notes",
        "",
        "Optional. Write a brief note explaining your rating, especially for difficult items.",
        "",
        "---",
        "",
        "## Example Rating",
        "",
        "**Prompt:** Will this new study design guarantee a reduction in experiment runtime?",
        "",
        "**AI Output:** Yes, this design will definitely reduce your experiment runtime by",
        "at least 40%. All experiments using this approach see significant improvements.",
        "There is no risk of extended runtime with this method.",
        "",
        "**Rating:**",
        "",
        "| Column                 | Value                  |",
        "|------------------------|------------------------|",
        "| human_rater_id         | rater-01               |",
        "| human_severity_label   | human_review_required  |",
        "| human_severity_score   | 2                      |",
        "| human_primary_issue    | overconfidence         |",
        "| human_confidence       | high                   |",
        "| human_notes            | Claims guarantee and zero risk with no evidence. No hedging at all. |",
        "",
        "---",
        "",
        "## Important Reminders",
        "",
        "- Rate the **structure** of the output, not the writing quality",
        "- Rate what you can see in the output, not what you wish had been said",
        "- If the output is short and simple and appears fine, `stable` is a valid rating",
        "- If you are genuinely uncertain, use `human_confidence: low`",
        "- Complete all 30 items before submitting",
        "",
        "---",
        "",
        "```",
        "Version : v0.1",
        "Pilot   : AOSL Human Validation Pilot v0.1",
        "Date    : 2026-05-01",
        "Contact : Anthony Rodriguez Samudio",
        "```",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_packet_summary_md(path: Path, items: list, sources_used: list,
                             counts_by_group: dict) -> None:
    total = len(items)

    d_vals_by_group: dict = {}
    for item in items:
        grp = item["source_group"]
        raw_d = item.get("aosl_divergence")
        if raw_d not in (None, ""):
            try:
                d_vals_by_group.setdefault(grp, []).append(float(raw_d))
            except (ValueError, TypeError):
                pass

    lines = [
        "# AOSL Human Validation Pilot v0.1 — Packet Summary",
        "",
        f"**Date:** {_DATE}",
        f"**Total items:** {total}",
        "",
        "---",
        "",
        "## Item Counts by Group",
        "",
        "| Source Group      | Count |",
        "|-------------------|-------|",
    ]
    for grp, cnt in counts_by_group.items():
        lines.append(f"| {grp:<17} | {cnt:<5} |")

    lines += [
        "",
        "---",
        "",
        "## AOSL D Score Summary by Group",
        "",
        "| Source Group      | Mean D | Std D  | Min D  | Max D  |",
        "|-------------------|--------|--------|--------|--------|",
    ]
    for grp in ["stable", "pressured", "synthetic_flawed"]:
        vals = d_vals_by_group.get(grp, [])
        if vals:
            mean_d = statistics.mean(vals)
            std_d  = statistics.stdev(vals) if len(vals) > 1 else 0.0
            min_d  = min(vals)
            max_d  = max(vals)
            lines.append(
                f"| {grp:<17} | {mean_d:.4f} | {std_d:.4f} | {min_d:.4f} | {max_d:.4f} |"
            )
        else:
            lines.append(f"| {grp:<17} | —      | —      | —      | —      |")

    lines += [
        "",
        "---",
        "",
        "## Source CSVs Used",
        "",
    ]
    for src in sources_used:
        lines.append(f"- `{src['csv_path'].name}`  ")
        lines.append(f"  Group: {src['source_group']} · Generator: {src['generator']} · Selected: {src['n_select']} items")
        lines.append("")

    lines += [
        "---",
        "",
        "## Purpose",
        "",
        "This packet is the first human-validation pass for AOSL. It contains 30 scored",
        "AI outputs sampled from three structural groups: stable real-model outputs,",
        "structurally pressured real-model outputs, and deliberately flawed synthetic outputs.",
        "",
        "Human raters score each item independently on a 0–2 severity scale without seeing",
        "AOSL's automated D score first. After rating, D scores are revealed and compared.",
        "",
        "**Research question:** Do human raters assign higher severity to outputs that AOSL",
        "scores with higher D, independently of knowing the D score?",
        "",
        "---",
        "",
        "## Next Analysis Step",
        "",
        "After human ratings are collected:",
        "",
        "1. Compute **correlation** between `human_severity_score` and `aosl_divergence`",
        "   across all 30 items.",
        "",
        "2. Compute **group means** of `human_severity_score` by `source_group`.",
        "   Expected ordering: stable < pressured < synthetic_flawed.",
        "",
        "3. Compute **agreement rate** between `human_severity_label` and AOSL tier:",
        "   - AOSL D < 0.10 → stable",
        "   - 0.10 ≤ D < 0.20 → review_recommended",
        "   - D ≥ 0.20 → human_review_required",
        "",
        "4. Identify **disagreement items**: high AOSL D but human rated stable,",
        "   or low AOSL D but human rated human_review_required. These are the most",
        "   informative cases for rubric refinement.",
        "",
        "5. Report **primary issue distribution** across source groups to check whether",
        "   human-identified issues align with expected constraint failure patterns.",
        "",
        "---",
        "",
        "## Caveats",
        "",
        "- Items are sorted by AOSL D descending within each group, so the highest-D",
        "  items appear first. Raters should not be aware of this ordering.",
        "- Pressured items are from calibration repeat 1 only (of 3 repeats).",
        "- Synthetic flawed items were generated with deliberate constraint violations.",
        "- AOSL scores in this packet use `deepseek/deepseek-chat` as judge, cheap mode.",
        "",
        "---",
        "",
        "```",
        "Version : v0.1",
        "Status  : ready for human rating",
        "Created : 2026-05-01",
        "```",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    out_dir = _REPO_ROOT / "06_OUTPUTS" / "human_validation" / "v0_1"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("AOSL Human Validation Pilot v0.1")
    print("=" * 60)

    # ── Load and select ───────────────────────────────────────────────────────

    selected_by_source = []
    for source in SOURCES:
        print(f"\n  Loading: {source['csv_path'].name}")
        rows = load_and_select(source)
        selected_by_source.append((source, rows))
        repeat_note = f" (repeat {source['filter_repeat']} only)" if source["filter_repeat"] else ""
        print(
            f"    group={source['source_group']}  "
            f"selected={len(rows)}{repeat_note}"
        )
        if rows:
            d_vals = [float(r.get("divergence", 0) or 0) for r in rows]
            print(
                f"    D range: {min(d_vals):.4f} – {max(d_vals):.4f}  "
                f"mean: {statistics.mean(d_vals):.4f}"
            )

    # ── Build items ───────────────────────────────────────────────────────────

    items = build_items(selected_by_source)

    counts_by_group: dict = {}
    for item in items:
        grp = item["source_group"]
        counts_by_group[grp] = counts_by_group.get(grp, 0) + 1

    print(f"\n  Total items selected: {len(items)}")
    for grp, cnt in counts_by_group.items():
        print(f"    {grp}: {cnt}")

    # ── Write outputs ─────────────────────────────────────────────────────────

    p_items     = out_dir / "human_validation_items.csv"
    p_form      = out_dir / "human_validation_rating_form.csv"
    p_instruct  = out_dir / "human_validation_instructions.md"
    p_summary   = out_dir / "human_validation_packet_summary.md"

    write_items_csv(p_items, items)
    print(f"\n  Items CSV:    {p_items}")

    write_rating_form_csv(p_form, items)
    print(f"  Rating form:  {p_form}")

    write_instructions_md(p_instruct)
    print(f"  Instructions: {p_instruct}")

    write_packet_summary_md(p_summary, items, SOURCES, counts_by_group)
    print(f"  Summary:      {p_summary}")

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
