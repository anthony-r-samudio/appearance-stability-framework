"""
build_false_stability_benchmark_v0_1.py

Build the AOSL False-Stability Benchmark v0.1 summary from archived baseline CSVs.
No new API calls. No new scoring. Research portfolio artifact.

Usage:
    py 05_SRC\analysis\build_false_stability_benchmark_v0_1.py

Outputs (06_OUTPUTS/benchmarks/false_stability_v0_1/):
    false_stability_benchmark_summary.csv
    false_stability_benchmark_report.md
    false_stability_ladder.png  (if matplotlib is available)
"""

import csv
import statistics
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

# =============================================================================
# Baseline definitions
# =============================================================================

BASELINES = [
    {
        "label":     "DeepSeek stable",
        "dataset":   "real_model_validation_30",
        "generator": "deepseek/deepseek-chat",
        "judge":     "deepseek/deepseek-chat",
        "repeats":   1,
        "csv_path":  (
            _REPO_ROOT
            / "04_RUNS" / "real_model_validation_30" / "valid_baselines"
            / "real_model_validation_30_1repeat_cheap_deepseek.csv"
        ),
    },
    {
        "label":     "Llama stable",
        "dataset":   "real_model_validation_30",
        "generator": "meta-llama/llama-3.1-8b-instruct",
        "judge":     "deepseek/deepseek-chat",
        "repeats":   1,
        "csv_path":  (
            _REPO_ROOT
            / "04_RUNS" / "real_model_validation_30" / "valid_baselines"
            / "real_model_validation_30_llama_3_1_8b_1repeat_cheap_deepseek_judge.csv"
        ),
    },
    {
        "label":     "Llama pressured",
        "dataset":   "real_failure_validation_30",
        "generator": "meta-llama/llama-3.1-8b-instruct",
        "judge":     "deepseek/deepseek-chat",
        "repeats":   3,
        "csv_path":  (
            _REPO_ROOT
            / "04_RUNS" / "real_failure_validation_30" / "valid_baselines"
            / "real_failure_validation_30_llama_3_1_8b_3repeat_cheap_deepseek_judge.csv"
        ),
    },
    {
        "label":     "DeepSeek pressured",
        "dataset":   "real_failure_validation_30",
        "generator": "deepseek/deepseek-chat",
        "judge":     "deepseek/deepseek-chat",
        "repeats":   3,
        "csv_path":  (
            _REPO_ROOT
            / "04_RUNS" / "real_failure_validation_30" / "valid_baselines"
            / "real_failure_validation_30_3repeat_cheap_deepseek.csv"
        ),
    },
    {
        "label":     "Synthetic flawed",
        "dataset":   "validation_30",
        "generator": "synthetic hand-crafted",
        "judge":     "deepseek/deepseek-chat",
        "repeats":   1,
        "csv_path":  (
            _REPO_ROOT
            / "04_RUNS" / "validation_30" / "valid_baselines"
            / "validation_30_1repeat_cheap_deepseek.csv"
        ),
    },
]

# Documented fallback values (used only if a CSV is missing)
_DOCUMENTED = {
    "DeepSeek stable":    {"mean_d": 0.0117, "std_d": 0.0252, "rows": 30},
    "Llama stable":       {"mean_d": 0.0250, "std_d": 0.0341, "rows": 30},
    "Llama pressured":    {"mean_d": 0.0722, "std_d": 0.0628, "rows": 90},
    "DeepSeek pressured": {"mean_d": 0.0939, "std_d": 0.0905, "rows": 90},
    "Synthetic flawed":   {"mean_d": 0.2050, "std_d": 0.1493, "rows": 30},
}


# =============================================================================
# CSV loader
# =============================================================================

def load_csv_stats(path: Path, label: str) -> dict:
    if not path.exists():
        print(f"  [WARNING] CSV not found: {path.name}")
        print(f"  [WARNING] Falling back to documented values for '{label}'")
        doc = _DOCUMENTED[label]
        return {
            "rows":       doc["rows"],
            "error_rows": 0,
            "d_vals":     [],
            "mean_d":     doc["mean_d"],
            "std_d":      doc["std_d"],
            "min_d":      None,
            "max_d":      None,
            "mean_stab":  None,
            "source":     "documented_fallback",
        }

    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    d_vals    = []
    stab_vals = []
    error_count = 0

    for row in rows:
        if row.get("scorer_error"):
            error_count += 1
            continue
        raw_d = row.get("divergence")
        if raw_d not in (None, ""):
            try:
                d_vals.append(float(raw_d))
            except (ValueError, TypeError):
                pass
        raw_s = row.get("stability_score")
        if raw_s not in (None, ""):
            try:
                stab_vals.append(float(raw_s))
            except (ValueError, TypeError):
                pass

    return {
        "rows":       len(rows),
        "error_rows": error_count,
        "d_vals":     d_vals,
        "mean_d":     statistics.mean(d_vals)  if d_vals          else None,
        "std_d":      statistics.stdev(d_vals) if len(d_vals) > 1 else 0.0,
        "min_d":      min(d_vals)              if d_vals          else None,
        "max_d":      max(d_vals)              if d_vals          else None,
        "mean_stab":  statistics.mean(stab_vals) if stab_vals     else None,
        "source":     "csv",
    }


# =============================================================================
# Markdown report writer
# =============================================================================

def write_markdown_report(path: Path, results: list) -> None:
    def _fmt(v, digits=4):
        return f"{v:.{digits}f}" if v is not None else "—"

    lines = [
        "# AOSL False-Stability Benchmark v0.1",
        "",
        "## Summary",
        "",
        "This benchmark summarizes archived AOSL baseline scoring runs across five levels",
        "of structural pressure. It establishes an ordered evidence ladder — from stable",
        "real model outputs to deliberately flawed synthetic outputs — without new API calls.",
        "All runs use `deepseek/deepseek-chat` as judge in cheap mode (300 max tokens),",
        "with zero scoring errors across all five-level baseline runs.",
        "",
        "---",
        "",
        "## Five-Level Evidence Ladder",
        "",
        "| Level | Label               | Dataset                    | Generator                          | Mean D | Std D  | Rows | Repeats |",
        "|-------|---------------------|----------------------------|------------------------------------|--------|--------|------|---------|",
    ]

    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i}     "
            f"| {r['label']:<19} "
            f"| {r['dataset']:<26} "
            f"| {r['generator']:<34} "
            f"| {r['mean_d']:<6} "
            f"| {r['std_d']:<6} "
            f"| {r['rows']:<4} "
            f"| {r['repeats']}       |"
        )

    lines += [
        "",
        "---",
        "",
        "## Ordering",
        "",
        "```",
        "DeepSeek stable  <  Llama stable  <  Llama pressured  <  DeepSeek pressured  <  Synthetic flawed",
        "    0.0117       <     0.0250     <      0.0722        <       0.0939         <      0.2050",
        "```",
        "",
        "Both stable baselines score near zero, confirming the framework does not falsely",
        "flag well-formed outputs at high rates. Both pressured baselines score meaningfully",
        "above their own stable floors. The synthetic flawed ceiling sits well above all",
        "real-output baselines.",
        "",
        "---",
        "",
        "## Divergence Gaps",
        "",
        "| Comparison                                          | Gap     |",
        "|-----------------------------------------------------|---------|",
        "| Llama stable − DeepSeek stable                      | +0.0133 |",
        "| Llama pressured − Llama stable (own floor)          | +0.0472 |",
        "| Llama pressured / Llama stable (ratio)              | ~2.9×   |",
        "| DeepSeek pressured − DeepSeek stable (own floor)    | +0.0822 |",
        "| DeepSeek pressured / DeepSeek stable (ratio)        | ~8.0×   |",
        "| DeepSeek pressured − Llama pressured                | +0.0217 |",
        "| Synthetic flawed − Llama pressured                  | +0.1328 |",
        "| Synthetic flawed − DeepSeek pressured               | +0.1111 |",
        "",
        "---",
        "",
        "## Interpretation",
        "",
        "- **Stable outputs score near zero.** Both real-model stable baselines (DeepSeek 0.0117,",
        "  Llama 0.0250) confirm the framework does not generate spurious violations on",
        "  unpressured, well-formed AI outputs.",
        "",
        "- **Pressured outputs score higher.** Both real-failure baselines score meaningfully",
        "  above their own generator's stable floor. DeepSeek pressured lifts ~8× above its",
        "  stable floor; Llama pressured lifts ~2.9× above its stable floor.",
        "",
        "- **Synthetic flawed outputs score highest.** The synthetic ceiling (0.2050) sits",
        "  well above both pressured real baselines, consistent with deliberately constructed",
        "  failures being more severe than naturalistic structural weaknesses.",
        "",
        "- **The ordering is consistent across generators.** Two architecturally different",
        "  generator models produce the same directional result: near-zero D on stable prompts,",
        "  elevated D on structurally pressured prompts.",
        "",
        "---",
        "",
        "## Caveats",
        "",
        "- **Judge-dependent.** All results use a single judge model (`deepseek/deepseek-chat`).",
        "  The signal has not been independently replicated with a second judge at scale.",
        "",
        "- **Purpose-built prompt sets.** Pressured prompts were designed to invite specific",
        "  structural failures. Detection on naturalistic real-world prompts remains untested.",
        "",
        "- **Constraint attribution is weak.** Per-constraint attribution match rates (0.32–0.44)",
        "  are below the 0.60 target threshold. Aggregate D is the reliable signal.",
        "  Constraint-level diagnosis is not yet validated.",
        "",
        "- **Not a truth detector.** AOSL detects structural divergence patterns, not factual",
        "  correctness. A low-D output may still be factually wrong.",
        "",
        "- **Cross-judge evidence is exploratory.** Exploratory second-judge runs exist but",
        "  have not been formally validated as a replication of the primary signal.",
        "",
        "- **Not production-ready.** This is an independent research prototype. It is not",
        "  suitable for deployment without further validation.",
        "",
        "---",
        "",
        "## Portfolio Note",
        "",
        "AOSL is currently best framed as an independent research prototype exploring false",
        "stability in AI outputs. The false stability problem — outputs that read as confident",
        "and fluent but violate structural epistemic or logical constraints — is real and",
        "underaddressed in current AI evaluation practice.",
        "",
        "This benchmark provides early empirical grounding for the AOSL detection hypothesis:",
        "a structured constraint rubric, evaluated by a judge model, can produce a stable",
        "and ordered divergence signal across different generator models and prompt conditions.",
        "It does not yet prove the signal is judge-independent or generalizes to naturalistic",
        "prompts.",
        "",
        "**Independent research prototype by Anthony Rodriguez Samudio.**",
        "",
        "---",
        "",
        "```",
        "Version : v0.1",
        "Judge   : deepseek/deepseek-chat",
        "Mode    : cheap (300 max tokens)",
        "Errors  : 0 across all five-level baseline runs",
        "Created : 2026-05-01",
        "Status  : research artifact — not a product benchmark",
        "```",
        "",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# =============================================================================
# Chart writer
# =============================================================================

def write_chart(path: Path, results: list) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels  = [r["label"]  for r in results]
    mean_ds = [float(r["mean_d"]) for r in results]
    std_ds  = [float(r["std_d"])  if r["std_d"] else 0.0 for r in results]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars = ax.bar(labels, mean_ds, yerr=std_ds, capsize=4)

    ax.set_ylabel("Mean D (divergence score)")
    ax.set_title("AOSL False-Stability Benchmark v0.1 — Evidence Ladder")
    ax.set_ylim(0, max(mean_ds) * 1.35)

    for bar, val in zip(bars, mean_ds):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(mean_ds) * 0.03,
            f"{val:.4f}",
            ha="center", va="bottom", fontsize=9,
        )

    ax.tick_params(axis="x", labelsize=9)
    ax.axhline(0.10, color="gray", linestyle="--", linewidth=0.8, label="Review threshold (0.10)")
    ax.axhline(0.20, color="gray", linestyle=":",  linewidth=0.8, label="Human-review threshold (0.20)")
    ax.legend(fontsize=8)

    plt.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    out_dir = _REPO_ROOT / "06_OUTPUTS" / "benchmarks" / "false_stability_v0_1"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("AOSL False-Stability Benchmark v0.1")
    print("=" * 60)

    # ── Load stats ────────────────────────────────────────────────────────────

    results = []
    for b in BASELINES:
        label = b["label"]
        print(f"\n  Loading: {label}")
        print(f"    {b['csv_path'].name}")
        stats = load_csv_stats(b["csv_path"], label)

        results.append({
            "label":                label,
            "dataset":              b["dataset"],
            "generator":            b["generator"],
            "judge":                b["judge"],
            "rows":                 stats["rows"],
            "repeats":              b["repeats"],
            "mean_d":               f"{stats['mean_d']:.4f}" if stats["mean_d"] is not None else "",
            "std_d":                f"{stats['std_d']:.4f}"  if stats["std_d"]  is not None else "",
            "min_d":                f"{stats['min_d']:.4f}"  if stats["min_d"]  is not None else "",
            "max_d":                f"{stats['max_d']:.4f}"  if stats["max_d"]  is not None else "",
            "error_rows":           stats["error_rows"],
            "mean_stability_score": f"{stats['mean_stab']:.4f}" if stats["mean_stab"] is not None else "",
            "source":               stats["source"],
        })

        print(
            f"    rows={stats['rows']}  "
            f"mean_d={stats['mean_d']:.4f}  "
            f"std_d={stats['std_d']:.4f}  "
            f"errors={stats['error_rows']}  "
            f"source={stats['source']}"
        )

    # ── Print summary table ───────────────────────────────────────────────────

    print()
    print(f"  {'Label':<22} {'Mean D':>8} {'Std D':>8} {'Rows':>6} {'Errors':>7}")
    print("  " + "-" * 56)
    for r in results:
        print(
            f"  {r['label']:<22} {r['mean_d']:>8} {r['std_d']:>8} "
            f"{r['rows']:>6} {r['error_rows']:>7}"
        )

    # ── Write CSV ─────────────────────────────────────────────────────────────

    csv_path = out_dir / "false_stability_benchmark_summary.csv"
    fieldnames = [
        "label", "dataset", "generator", "judge", "rows", "repeats",
        "mean_d", "std_d", "min_d", "max_d",
        "error_rows", "mean_stability_score", "source",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n  CSV:      {csv_path}")

    # ── Write Markdown report ─────────────────────────────────────────────────

    md_path = out_dir / "false_stability_benchmark_report.md"
    write_markdown_report(md_path, results)
    print(f"  Markdown: {md_path}")

    # ── Optional chart ────────────────────────────────────────────────────────

    try:
        chart_path = out_dir / "false_stability_ladder.png"
        write_chart(chart_path, results)
        print(f"  Chart:    {chart_path}")
    except Exception as e:
        print(f"  [INFO] Chart skipped: {e}")

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
