"""
run_real_openrouter_validation.py

Generates and scores 3 prompts via OpenRouter.
Writes dashboard-compatible JSONL and CSV output.

No hardcoded API keys. Requires OPENROUTER_API_KEY in environment.

Set the key in PowerShell before running:
    $env:OPENROUTER_API_KEY = "sk-or-v1-..."

Run:
    py 05_SRC/scripts/run_real_openrouter_validation.py

View results:
    py -m streamlit run 05_SRC/apps/aosl_stability_dashboard.py
"""

import json
import sys
import time
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

GENERATOR_MODEL = FREE_GENERATOR_MODELS[0]   # deepseek/deepseek-chat
JUDGE_MODEL     = FREE_JUDGE_MODELS[0]       # deepseek/deepseek-chat
TEMPERATURE     = 0.7
RETRY_WAIT_SEC  = 20

OUTPUT_DIR = _REPO_ROOT / "04_RUNS" / "real_openrouter_validation"
JSONL_PATH = OUTPUT_DIR / "real_openrouter_validation.jsonl"
CSV_PATH   = OUTPUT_DIR / "real_openrouter_validation.csv"

PROMPTS = [
    {
        "prompt_id":   "real_p1",
        "prompt_text": "What is the boiling point of water at sea level, and why?",
    },
    {
        "prompt_id":   "real_p2",
        "prompt_text": "Explain in one or two sentences why the sky appears blue.",
    },
    {
        "prompt_id":   "real_p3",
        "prompt_text": "Name two evidence-based benefits of regular physical exercise.",
    },
]


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _generate_with_retry(model: str, prompt: str, temperature: float) -> str:
    """Call generate_response, retrying once after a 20-second wait on 429."""
    try:
        return generate_response(model, prompt, temperature=temperature)
    except Exception as exc:
        if "429" in str(exc):
            print(f"    [429] Rate limit hit — waiting {RETRY_WAIT_SEC}s before retry...")
            time.sleep(RETRY_WAIT_SEC)
            return generate_response(model, prompt, temperature=temperature)
        raise


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("AOSL Real OpenRouter Validation")
    print("=" * 60)
    print(f"Generator model : {GENERATOR_MODEL}")
    print(f"Judge model     : {JUDGE_MODEL}")
    print(f"Temperature     : {TEMPERATURE}")
    print(f"Prompts         : {len(PROMPTS)}")
    print(f"Output dir      : {OUTPUT_DIR}")
    print("=" * 60)
    print()

    results = []

    with open(JSONL_PATH, "w", encoding="utf-8") as fh:
        for idx, prompt in enumerate(PROMPTS):
            prompt_id   = prompt["prompt_id"]
            prompt_text = prompt["prompt_text"]
            n = idx + 1
            total = len(PROMPTS)

            print(f"[{n}/{total}] {prompt_id}")
            print(f"  Prompt   : {prompt_text}")

            # ── Step 1: Generate output ──────────────────────────────────────
            print(f"  [GENERATE] model={GENERATOR_MODEL}  temperature={TEMPERATURE}")
            try:
                output_text = _generate_with_retry(GENERATOR_MODEL, prompt_text, TEMPERATURE)
                gen_error   = None
                preview     = output_text[:120].replace("\n", " ")
                print(f"  Output   : {preview}{'...' if len(output_text) > 120 else ''}")
            except Exception as exc:
                output_text = ""
                gen_error   = str(exc)
                print(f"  [GENERATION ERROR] {gen_error}")

            # ── Step 2: Judge output → c1–c10, D, D_norm, stability_tier ────
            record = {
                "prompt_id":       prompt_id,
                "prompt_text":     prompt_text,
                "model_name":      GENERATOR_MODEL,
                "generator_model": GENERATOR_MODEL,
                "temperature":     TEMPERATURE,
                "output_text":     output_text,
            }

            if gen_error:
                # Skip judging — write an error record so the row still appears in CSV
                result = {
                    **record,
                    "record_id":     f"{prompt_id}__t{TEMPERATURE}",
                    "judge_model":   JUDGE_MODEL,
                    "error":         f"Generation failed: {gen_error}",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                }
            else:
                print(f"  [JUDGE]    model={JUDGE_MODEL}  temperature=0.0")
                result = score_one_record(record, idx, JUDGE_MODEL)

                if result.get("error"):
                    print(f"  [JUDGE ERROR] {result['error']}")
                else:
                    scores = result.get("constraint_scores", {})
                    D      = result.get("D", "?")
                    tier   = result.get("stability_tier", "?")
                    score_str = "  ".join(
                        f"{k}={v:.2f}" for k, v in scores.items()
                    )
                    print(f"  Scores   : {score_str}")
                    print(f"  D={D:.4f}  tier={tier}")

            fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            results.append(result)
            print()

    # ── CSV export ───────────────────────────────────────────────────────────────
    export_csv(JSONL_PATH, CSV_PATH)

    # ── Run summary ──────────────────────────────────────────────────────────────
    ok_results     = [r for r in results if not r.get("error")]
    error_results  = [r for r in results if r.get("error")]

    print()
    print("=" * 60)
    print("Run Summary")
    print("=" * 60)
    print(f"  Scored OK  : {len(ok_results)}")
    print(f"  Errors     : {len(error_results)}")

    if ok_results:
        valid_D = [r["D"] for r in ok_results]
        avg_D   = sum(valid_D) / len(valid_D)
        print(f"  Avg D      : {avg_D:.4f}")
        print(f"  Avg D_norm : {avg_D / 10:.4f}")
        print()
        for r in ok_results:
            print(
                f"  {r['record_id']:<28}  "
                f"D={r['D']:.4f}  "
                f"tier={r['stability_tier']}"
            )

    if error_results:
        print()
        for r in error_results:
            print(f"  [FAILED] {r.get('record_id', '?')}  —  {r.get('error', '')}")

    print()
    print(f"  JSONL : {JSONL_PATH}")
    print(f"  CSV   : {CSV_PATH}")
    print()
    print("=" * 60)
    print("To view results in the dashboard, run:")
    print()
    print("    py -m streamlit run 05_SRC/apps/aosl_stability_dashboard.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
