import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

STABLE = ROOT / "04_RUNS/gemini_2_5_matched_llama_t07/gemini_2_5_stable_llama_t07_scores.csv"
PRESSURED = ROOT / "04_RUNS/gemini_2_5_matched_llama_t07/gemini_2_5_pressured_llama_t07_scores.csv"
REPORT = ROOT / "04_RUNS/gemini_2_5_matched_llama_t07/comparison_stable_vs_pressured_t07.md"

def load(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def get_d(row):
    for key in ("divergence", "D", "d", "divergence_score"):
        if key in row and row[key] not in ("", None):
            return float(row[key])
    if "stability_score" in row and row["stability_score"] not in ("", None):
        return 1.0 - float(row["stability_score"])
    raise KeyError(f"Could not find divergence field. Fields: {list(row)}")

stable_rows = load(STABLE)
pressured_rows = load(PRESSURED)

stable = {r["prompt_id"]: r for r in stable_rows}
pressured = {r["prompt_id"]: r for r in pressured_rows}

ids = sorted(set(stable) & set(pressured))

if len(ids) != 30:
    raise RuntimeError(f"Expected 30 matched prompt_ids, found {len(ids)}")

pairs = []
for pid in ids:
    ds = get_d(stable[pid])
    dp = get_d(pressured[pid])
    pairs.append((pid, ds, dp, dp - ds))

stable_d = [x[1] for x in pairs]
pressured_d = [x[2] for x in pairs]
diffs = [x[3] for x in pairs]

mean_s = statistics.mean(stable_d)
mean_p = statistics.mean(pressured_d)
median_s = statistics.median(stable_d)
median_p = statistics.median(pressured_d)
mean_diff = statistics.mean(diffs)
sd_diff = statistics.stdev(diffs)
dz = mean_diff / sd_diff if sd_diff else float("nan")

n = len(diffs)
se = sd_diff / math.sqrt(n)
tcrit_95_df29 = 2.045229642
ci_lo = mean_diff - tcrit_95_df29 * se
ci_hi = mean_diff + tcrit_95_df29 * se

higher = sum(d > 0 for d in diffs)
same = sum(d == 0 for d in diffs)
lower = sum(d < 0 for d in diffs)

ratio = mean_p / mean_s if mean_s else float("inf")

try:
    from scipy.stats import ttest_rel, wilcoxon
    t_result = ttest_rel(pressured_d, stable_d)
    t_stat = float(t_result.statistic)
    t_p = float(t_result.pvalue)

    w_result = wilcoxon(pressured_d, stable_d, zero_method="wilcox")
    w_stat = float(w_result.statistic)
    w_p = float(w_result.pvalue)
except Exception:
    t_stat = t_p = w_stat = w_p = None

constraint_rows = []
for i in range(1, 11):
    key = f"c{i}"
    if key not in stable_rows[0] or key not in pressured_rows[0]:
        continue
    sm = statistics.mean(float(stable[pid][key]) for pid in ids)
    pm = statistics.mean(float(pressured[pid][key]) for pid in ids)
    constraint_rows.append((key.upper(), sm, pm, pm - sm))

lines = []
lines.append("# Gemini 2.5 Flash — Matched T=0.7 Stable vs Pressured Llama")
lines.append("")
lines.append("## Design")
lines.append("")
lines.append("- Generator: `meta-llama/llama-3.1-8b-instruct`")
lines.append("- Generation temperature: `0.7` for both conditions")
lines.append("- Generation max tokens: `500`")
lines.append("- Stable outputs: 30")
lines.append("- Structurally pressured outputs: 30")
lines.append("- Judge: `google/gemini-2.5-flash`")
lines.append("- Judge temperature: `0.0`")
lines.append("- Judge max tokens: `800`")
lines.append("- Judge repeats: `1`")
lines.append("- Same AOSL boundary notes and scorer configuration")
lines.append("")
lines.append("## Primary result")
lines.append("")
lines.append(f"- Stable mean D: **{mean_s:.4f}**")
lines.append(f"- Pressured mean D: **{mean_p:.4f}**")
lines.append(f"- Mean paired increase: **{mean_diff:+.4f}**")
lines.append(f"- Stable median D: **{median_s:.4f}**")
lines.append(f"- Pressured median D: **{median_p:.4f}**")
lines.append(f"- Pressured / stable mean ratio: **{ratio:.2f}x**")
lines.append(f"- Higher D under pressure: **{higher}/{n}**")
lines.append(f"- Unchanged: **{same}/{n}**")
lines.append(f"- Lower D under pressure: **{lower}/{n}**")
lines.append("")
lines.append("## Paired statistical analysis")
lines.append("")
lines.append(f"- Paired mean difference: **{mean_diff:+.4f}**")
lines.append(f"- 95% CI for mean paired difference: **[{ci_lo:+.4f}, {ci_hi:+.4f}]**")
lines.append(f"- Paired effect size (Cohen's dz): **{dz:.3f}**")

if t_p is not None:
    lines.append(f"- Paired t-test: **t={t_stat:.3f}, p={t_p:.4f}**")
    lines.append(f"- Wilcoxon signed-rank: **W={w_stat:.3f}, p={w_p:.4f}**")
else:
    lines.append("- SciPy unavailable; paired t-test and Wilcoxon p-values were not computed.")

lines.append("")
lines.append("## Constraint means")
lines.append("")
lines.append("| Constraint | Stable | Pressured | Pressured - Stable |")
lines.append("|---|---:|---:|---:|")
for c, sm, pm, delta in constraint_rows:
    lines.append(f"| {c} | {sm:.4f} | {pm:.4f} | {delta:+.4f} |")

lines.append("")
lines.append("## Prompt-level paired results")
lines.append("")
lines.append("| Prompt | Stable D | Pressured D | Delta D |")
lines.append("|---|---:|---:|---:|")
for pid, ds, dp, delta in sorted(pairs, key=lambda x: x[3], reverse=True):
    lines.append(f"| {pid} | {ds:.4f} | {dp:.4f} | {delta:+.4f} |")

lines.append("")
lines.append("## Interpretation boundary")
lines.append("")
lines.append(
    "This matched-temperature run tests whether the structurally pressured prompt condition "
    "produces greater AOSL divergence than the stable condition when generator model, "
    "generation temperature, generation token budget, judge model, and judge configuration "
    "are held constant."
)
lines.append("")
lines.append(
    "Because only one generated output and one judge pass are available per prompt-condition "
    "pair, this run does not estimate generation-repeat variance or judge-repeatability."
)
lines.append("")
lines.append(
    "The result should therefore be treated as evidence from one matched 30-pair experiment, "
    "not as a final estimate of the effect across repeated generations, judges, or model families."
)

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Wrote: {REPORT}")
print(f"Stable mean D    : {mean_s:.4f}")
print(f"Pressured mean D : {mean_p:.4f}")
print(f"Mean delta       : {mean_diff:+.4f}")
print(f"Ratio            : {ratio:.2f}x")
print(f"Higher/same/lower: {higher}/{same}/{lower}")
print(f"Cohen dz         : {dz:.3f}")
print(f"95% CI           : [{ci_lo:+.4f}, {ci_hi:+.4f}]")
if t_p is not None:
    print(f"Paired t p       : {t_p:.4f}")
    print(f"Wilcoxon p       : {w_p:.4f}")
