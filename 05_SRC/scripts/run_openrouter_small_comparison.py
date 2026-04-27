"""
run_openrouter_small_comparison.py

Runs a small multi-model, multi-temperature comparison via OpenRouter.
Scores each output with AOSL c1-c10 constraints and writes dashboard-compatible output.

Design:
  5 prompts × 2 generator models × 2 temperatures × 1 repeat = 20 records

No hardcoded API keys. Requires OPENROUTER_API_KEY in environment.

Set the key in PowerShell before running:
    $env:OPENROUTER_API_KEY = "sk-or-v1-..."

Run:
    py 05_SRC/scripts/run_openrouter_small_comparison.py

View results:
    py -m streamlit run 05_SRC/apps/aosl_stability_dashboard.py
"""

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ── sys.path setup ──────────────────────────────────────────────────────────────
# Repo root → imports AOSL package
# 05_SRC    → imports api package (openrouter_client, model_registry)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_ROOT  = _REPO_ROOT / "05_SRC"

for _p in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.model_registry import FREE_GENERATOR_MODELS, FREE_JUDGE_MODELS
from api.openrouter_client import generate_response
from AOSL.agents.fast_batch_scorer import export_csv, score_one_record

# ── Config ──────────────────────────────────────────────────────────────────────
#
# FREE_GENERATOR_MODELS from the registry contains only one model.
# A second model is defined here directly so the comparison can run across two
# distinct generators without modifying the registry.
#   - deepseek/deepseek-chat  : fixed baseline model from the registry
#   - openrouter/free         : OpenRouter's free-router fallback; avoids brittle
#                               free-tier model IDs that change or become unavailable

GENERATOR_MODELS = [
    FREE_GENERATOR_MODELS[0],   # deepseek/deepseek-chat (fixed baseline, from registry)
    "openrouter/free",          # OpenRouter free-router fallback
]

JUDGE_MODEL    = FREE_JUDGE_MODELS[0]   # deepseek/deepseek-chat
TEMPERATURES   = [0.3, 0.9]
REPEAT         = 1
RETRY_WAIT_SEC = 20

OUTPUT_DIR = _REPO_ROOT / "04_RUNS" / "openrouter_small_comparison"
JSONL_PATH = OUTPUT_DIR / "openrouter_small_comparison.jsonl"
CSV_PATH   = OUTPUT_DIR / "openrouter_small_comparison.csv"

PROMPTS = [
    {
        "prompt_id":   "cmp_p1",
        "prompt_text": "At what temperature does iron melt, and what determines why different metals melt at different temperatures?",
    },
    {
        "prompt_id":   "cmp_p2",
        "prompt_text": "If all mammals breathe air, and whales are mammals, what must be true about whales? Explain your reasoning.",
    },
    {
        "prompt_id":   "cmp_p3",
        "prompt_text": "Does eating sugar directly cause type 2 diabetes? Explain the causal chain carefully.",
    },
    {
        "prompt_id":   "cmp_p4",
        "prompt_text": "How confident should we be that humans will establish a permanent base on the Moon within 15 years?",
    },
    {
        "prompt_id":   "cmp_p5",
        "prompt_text": "What will the global average surface temperature increase be by 2100? Acknowledge the uncertainty in your answer.",
    },
]

TOTAL_PLANNED = len(PROMPTS) * len(GENERATOR_MODELS) * len(TEMPERATURES) * REPEAT


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _model_slug(model_id: str) -> str:
    """Return a short filesystem-safe token from a model ID, e.g. 'deepseek-chat'."""
    return model_id.split("/")[-1][:20]


def _generate_with_retry(model: str, prompt: str, temperature: float) -> str:
    """Call generate_response, retrying once after a wait on HTTP 429."""
    try:
        return generate_response(model, prompt, temperature=temperature)
    except Exception as exc:
        if "429" in str(exc):
            print(f"    [429] Rate limit — waiting {RETRY_WAIT_SEC}s before retry...")
            time.sleep(RETRY_WAIT_SEC)
            return generate_response(model, prompt, temperature=temperature)
        raise


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 64)
    print("AOSL OpenRouter Small Comparison Run")
    print("=" * 64)
    print(f"Generator models : {GENERATOR_MODELS}")
    print(f"Judge model      : {JUDGE_MODEL}")
    print(f"Temperatures     : {TEMPERATURES}")
    print(f"Prompts          : {len(PROMPTS)}")
    print(f"Repeat           : {REPEAT}")
    print(f"Total planned    : {TOTAL_PLANNED} records")
    print(f"Output dir       : {OUTPUT_DIR}")
    print("=" * 64)
    print()

    results  = []
    run_num  = 0

    with open(JSONL_PATH, "w", encoding="utf-8") as fh:
        for prompt in PROMPTS:
            prompt_id   = prompt["prompt_id"]
            prompt_text = prompt["prompt_text"]

            for model in GENERATOR_MODELS:
                slug = _model_slug(model)

                for temperature in TEMPERATURES:
                    run_num += 1
                    print(f"[{run_num}/{TOTAL_PLANNED}] {prompt_id}  model={slug}  temp={temperature}")
                    print(f"  Prompt : {prompt_text[:90]}{'...' if len(prompt_text) > 90 else ''}")

                    # ── Step 1: Generate ────────────────────────────────────────
                    print(f"  [GENERATE]")
                    try:
                        output_text = _generate_with_retry(model, prompt_text, temperature)
                        gen_error   = None
                        preview     = output_text[:120].replace("\n", " ")
                        print(f"  Output : {preview}{'...' if len(output_text) > 120 else ''}")
                    except Exception as exc:
                        output_text = ""
                        gen_error   = str(exc)
                        print(f"  [GENERATION ERROR] {gen_error}")

                    # ── Step 2: Judge → c1–c10, D, D_norm, stability_tier ──────
                    record = {
                        "prompt_id":       prompt_id,
                        "prompt_text":     prompt_text,
                        "model_name":      model,
                        "generator_model": model,
                        "temperature":     temperature,
                        "repeat":          REPEAT,
                        "output_text":     output_text,
                    }

                    if gen_error:
                        result = {
                            **record,
                            "record_id":     f"{prompt_id}__{slug}__t{temperature}__r{REPEAT}",
                            "judge_model":   JUDGE_MODEL,
                            "error":         f"Generation failed: {gen_error}",
                            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        }
                    else:
                        print(f"  [JUDGE]  model={JUDGE_MODEL}  temperature=0.0")
                        result = score_one_record(record, run_num, JUDGE_MODEL)

                        # score_one_record builds record_id from prompt_id+temperature+repeat.
                        # Override here to include the model slug so records from different
                        # generators with the same prompt and temperature stay distinct.
                        result["record_id"] = f"{prompt_id}__{slug}__t{temperature}__r{REPEAT}"

                        if result.get("error"):
                            print(f"  [JUDGE ERROR] {result['error']}")
                        else:
                            scores    = result.get("constraint_scores", {})
                            D         = result.get("D", "?")
                            tier      = result.get("stability_tier", "?")
                            score_str = "  ".join(f"{k}={v:.2f}" for k, v in scores.items())
                            print(f"  Scores : {score_str}")
                            print(f"  D={D:.4f}  tier={tier}")

                    fh.write(json.dumps(result, ensure_ascii=False) + "\n")
                    results.append(result)
                    print()

    # ── CSV export ───────────────────────────────────────────────────────────────
    export_csv(JSONL_PATH, CSV_PATH)

    # ── Run summary ──────────────────────────────────────────────────────────────
    ok_results    = [r for r in results if not r.get("error")]
    error_results = [r for r in results if r.get("error")]

    print()
    print("=" * 64)
    print("Run Summary")
    print("=" * 64)
    print(f"  Total planned    : {TOTAL_PLANNED}")
    print(f"  Scored OK        : {len(ok_results)}")
    print(f"  Errors           : {len(error_results)}")

    if ok_results:
        valid_D    = [r["D"] for r in ok_results]
        avg_D      = sum(valid_D) / len(valid_D)
        avg_D_norm = avg_D / 10.0
        print(f"  Average D        : {avg_D:.4f}")
        print(f"  Average D_norm   : {avg_D_norm:.4f}")

        # Stability tier counts
        tier_counts: dict[str, int] = defaultdict(int)
        for r in ok_results:
            tier_counts[r["stability_tier"]] += 1
        print()
        print("  Stability tier counts:")
        for tier in ("S0", "S1", "S2", "S3"):
            print(f"    {tier} : {tier_counts.get(tier, 0)}")

        # By generator model
        print()
        print("  Average D by model:")
        by_model: dict[str, list] = defaultdict(list)
        for r in ok_results:
            by_model[r["generator_model"]].append(r["D"])
        for model, d_vals in by_model.items():
            print(f"    {_model_slug(model):<22}  avg D = {sum(d_vals)/len(d_vals):.4f}  (n={len(d_vals)})")

        # By temperature
        print()
        print("  Average D by temperature:")
        by_temp: dict[float, list] = defaultdict(list)
        for r in ok_results:
            by_temp[r["temperature"]].append(r["D"])
        for temp in sorted(by_temp):
            d_vals = by_temp[temp]
            print(f"    temp={temp}  avg D = {sum(d_vals)/len(d_vals):.4f}  (n={len(d_vals)})")

    if error_results:
        print()
        print("  Failed records:")
        for r in error_results:
            print(f"    [FAILED] {r.get('record_id', '?')}  —  {r.get('error', '')}")

    print()
    print(f"  JSONL : {JSONL_PATH}")
    print(f"  CSV   : {CSV_PATH}")
    print()
    print("=" * 64)
    print("To view results in the dashboard, run:")
    print()
    print("    py -m streamlit run 05_SRC/apps/aosl_stability_dashboard.py")
    print("=" * 64)


if __name__ == "__main__":
    main()
