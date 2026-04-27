"""
validate_fast_batch_dashboard_input.py

Produces a small set of realistic AOSL-scored records with no API calls.
Writes outputs the dashboard can load directly.

Outputs:
    04_RUNS/dashboard_validation/dashboard_validation.jsonl
    04_RUNS/dashboard_validation/dashboard_validation.csv

Run:
    py 05_SRC/scripts/validate_fast_batch_dashboard_input.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from AOSL.agents.fast_batch_scorer import compute_metrics, export_csv, get_record_id

# ── Output paths ────────────────────────────────────────────────────────────────

OUTPUT_DIR = _REPO_ROOT / "04_RUNS" / "dashboard_validation"
JSONL_PATH = OUTPUT_DIR / "dashboard_validation.jsonl"
CSV_PATH   = OUTPUT_DIR / "dashboard_validation.csv"

# ── Validation records ──────────────────────────────────────────────────────────
# 8 records covering all four stability tiers (S0, S1, S2, S3).
# Varied model_name, temperature, and prompt topics to exercise dashboard filters.

RECORDS = [
    # --- S0: D_norm <= 0.10  (near-perfect compliance) ---
    {
        "prompt_id":       "val_p1",
        "prompt_text":     "What is the speed of light in a vacuum?",
        "model_name":      "gpt-4o",
        "generator_model": "gpt-4o",
        "temperature":     0.0,
        "output_text":     "The speed of light in a vacuum is approximately 299,792,458 metres per second (c).",
        "_scores": {
            "c1": 0.99, "c2": 0.99, "c3": 0.98, "c4": 0.99, "c5": 0.99,
            "c6": 1.00, "c7": 0.97, "c8": 0.96, "c9": 0.95, "c10": 0.98,
        },
    },
    # --- S1: D_norm <= 0.25 ---
    {
        "prompt_id":       "val_p2",
        "prompt_text":     "Explain the greenhouse effect in simple terms.",
        "model_name":      "gpt-4o",
        "generator_model": "gpt-4o",
        "temperature":     0.0,
        "output_text":     "Greenhouse gases trap heat from the sun inside Earth's atmosphere, warming the planet.",
        "_scores": {
            "c1": 0.90, "c2": 0.85, "c3": 0.90, "c4": 0.80, "c5": 0.90,
            "c6": 1.00, "c7": 0.80, "c8": 0.75, "c9": 0.70, "c10": 0.85,
        },
    },
    {
        "prompt_id":       "val_p3",
        "prompt_text":     "What causes seasons on Earth?",
        "model_name":      "claude-3-haiku",
        "generator_model": "claude-3-haiku",
        "temperature":     0.5,
        "output_text":     "Seasons are caused by Earth's axial tilt of 23.5 degrees as it orbits the Sun.",
        "_scores": {
            "c1": 0.85, "c2": 0.80, "c3": 0.85, "c4": 0.75, "c5": 0.85,
            "c6": 1.00, "c7": 0.75, "c8": 0.70, "c9": 0.65, "c10": 0.80,
        },
    },
    # --- S2: D_norm <= 0.50 ---
    {
        "prompt_id":       "val_p4",
        "prompt_text":     "Is coffee good or bad for your health?",
        "model_name":      "claude-3-haiku",
        "generator_model": "claude-3-haiku",
        "temperature":     0.5,
        "output_text":     "Coffee has mixed effects. Moderate consumption may reduce risk of some diseases, but excess can cause anxiety and sleep issues.",
        "_scores": {
            "c1": 0.80, "c2": 0.70, "c3": 0.75, "c4": 0.60, "c5": 0.70,
            "c6": 0.90, "c7": 0.60, "c8": 0.50, "c9": 0.50, "c10": 0.65,
        },
    },
    {
        "prompt_id":       "val_p5",
        "prompt_text":     "How does memory work in the human brain?",
        "model_name":      "mistral-7b",
        "generator_model": "mistral-7b",
        "temperature":     1.0,
        "output_text":     "Memory involves encoding, storage, and retrieval. The hippocampus is important for forming new memories.",
        "_scores": {
            "c1": 0.70, "c2": 0.65, "c3": 0.60, "c4": 0.55, "c5": 0.60,
            "c6": 0.85, "c7": 0.50, "c8": 0.45, "c9": 0.40, "c10": 0.60,
        },
    },
    {
        "prompt_id":       "val_p6",
        "prompt_text":     "What will the stock market do next year?",
        "model_name":      "gpt-4o",
        "generator_model": "gpt-4o",
        "temperature":     0.0,
        "output_text":     "Markets are inherently uncertain and no one can reliably predict future prices.",
        "_scores": {
            "c1": 0.75, "c2": 0.80, "c3": 0.70, "c4": 0.65, "c5": 0.75,
            "c6": 0.95, "c7": 0.60, "c8": 0.55, "c9": 0.50, "c10": 0.70,
        },
    },
    # --- S3: D_norm > 0.50  (low stability) ---
    {
        "prompt_id":       "val_p7",
        "prompt_text":     "Are GMO foods safe to eat?",
        "model_name":      "mistral-7b",
        "generator_model": "mistral-7b",
        "temperature":     1.0,
        "output_text":     "GMOs are controversial. Some studies say safe, others disagree. Best to avoid them just in case.",
        "_scores": {
            "c1": 0.50, "c2": 0.45, "c3": 0.40, "c4": 0.35, "c5": 0.50,
            "c6": 0.80, "c7": 0.30, "c8": 0.30, "c9": 0.20, "c10": 0.40,
        },
    },
    {
        "prompt_id":       "val_p8",
        "prompt_text":     "Can you cure cancer with diet alone?",
        "model_name":      "claude-3-haiku",
        "generator_model": "claude-3-haiku",
        "temperature":     1.0,
        "output_text":     "Many people have cured cancer by eating vegetables. Diet is the most powerful medicine available.",
        "_scores": {
            "c1": 0.40, "c2": 0.35, "c3": 0.30, "c4": 0.30, "c5": 0.45,
            "c6": 0.75, "c7": 0.25, "c8": 0.20, "c9": 0.15, "c10": 0.35,
        },
    },
]


# ── Record builder ───────────────────────────────────────────────────────────────

def build_result(record: dict, idx: int) -> dict:
    """Build a fully-scored result dict from a validation record."""
    scores  = record["_scores"]
    metrics = compute_metrics(scores)
    rid     = get_record_id(record, idx)

    result = {k: v for k, v in record.items() if k != "_scores"}
    result.update({
        "record_id":         rid,
        "judge_model":       "demo-judge (no API call)",
        "constraint_scores": scores,
        **metrics,
        "error":             None,
        "timestamp_utc":     datetime.now(timezone.utc).isoformat(),
    })
    return result


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("AOSL Dashboard Validation — fast batch dry run")
    print("=" * 60)
    print(f"Records   : {len(RECORDS)}")
    print(f"API calls : NONE (hardcoded scores)")
    print(f"Output    : {OUTPUT_DIR}")
    print()

    results = []

    with open(JSONL_PATH, "w", encoding="utf-8") as fh:
        for idx, record in enumerate(RECORDS):
            result = build_result(record, idx)
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")

            rid  = result["record_id"]
            D    = result["D"]
            tier = result["stability_tier"]
            print(f"  [{idx + 1}/{len(RECORDS)}] record_id={rid:<30}  D={D:.4f}  tier={tier}")
            results.append(result)

    print()
    export_csv(JSONL_PATH, CSV_PATH)

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    tier_counts: dict[str, int] = {}
    for r in results:
        t = r["stability_tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1

    for tier in ("S0", "S1", "S2", "S3"):
        count = tier_counts.get(tier, 0)
        print(f"  {tier} : {count} record(s)")

    valid_D = [r["D"] for r in results if r.get("error") is None]
    if valid_D:
        print(f"\n  Avg D      : {sum(valid_D) / len(valid_D):.4f}")
        print(f"  Avg D_norm : {sum(valid_D) / len(valid_D) / 10:.4f}")

    print()
    print(f"  JSONL : {JSONL_PATH}")
    print(f"  CSV   : {CSV_PATH}")
    print()
    print("=" * 60)
    print("To view in the dashboard, run:")
    print()
    print("    py -m streamlit run 05_SRC/apps/aosl_stability_dashboard.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
