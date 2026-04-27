"""
demo_fast_batch_scoring.py

Dry-run demo for the AOSL fast batch scorer.

Uses 3 fake records with hardcoded constraint scores.
No external API calls. No OPENROUTER_API_KEY required.

Validates that the full pipeline works:
  load_input_records → compute_metrics → JSONL write → export_csv

Run:
    py 05_SRC\scripts\demo_fast_batch_scoring.py
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from AOSL.agents.fast_batch_scorer import (
    compute_metrics,
    export_csv,
    get_record_id,
)

# ── Fake input records (no API needed) ──────────────────────────────────────────

FAKE_RECORDS = [
    {
        "prompt_id":   "demo_p1",
        "prompt_text": "Explain why vaccines are effective.",
        "model_name":  "demo-model",
        "output_text": "Vaccines work by training the immune system using antigens.",
        # Hardcoded scores simulating a high-quality output.
        "_demo_scores": {
            "c1": 0.9, "c2": 0.9, "c3": 0.8, "c4": 0.9, "c5": 0.8,
            "c6": 1.0, "c7": 0.7, "c8": 0.6, "c9": 0.5, "c10": 0.8,
        },
    },
    {
        "prompt_id":   "demo_p2",
        "prompt_text": "Does correlation imply causation?",
        "model_name":  "demo-model",
        "output_text": "Correlation does not imply causation. For example, ice cream sales and drowning rates both rise in summer, but ice cream does not cause drowning.",
        # Scores simulating a mid-range output.
        "_demo_scores": {
            "c1": 0.8, "c2": 0.7, "c3": 0.5, "c4": 0.6, "c5": 0.7,
            "c6": 1.0, "c7": 0.5, "c8": 0.5, "c9": 0.4, "c10": 0.6,
        },
    },
    {
        "prompt_id":   "demo_p3",
        "prompt_text": "What are the limitations of current AI systems?",
        "model_name":  "demo-model",
        "output_text": "AI systems hallucinate, lack common sense, and cannot reliably verify facts.",
        # Scores simulating a lower-quality output.
        "_demo_scores": {
            "c1": 0.5, "c2": 0.5, "c3": 0.4, "c4": 0.4, "c5": 0.6,
            "c6": 0.9, "c7": 0.3, "c8": 0.3, "c9": 0.2, "c10": 0.4,
        },
    },
]

OUTPUT_DIR  = _REPO_ROOT / "04_RUNS" / "demo"
JSONL_PATH  = OUTPUT_DIR / "demo_fast_batch_scoring.jsonl"
CSV_PATH    = OUTPUT_DIR / "demo_fast_batch_scoring.csv"


def build_demo_result(record: dict, idx: int) -> dict:
    """Build a scored result dict using the fake pre-set scores."""
    from datetime import datetime, timezone

    scores  = record["_demo_scores"]
    metrics = compute_metrics(scores)
    rid     = get_record_id(record, idx)

    # Drop the internal _demo_scores key; preserve all other fields.
    result = {k: v for k, v in record.items() if k != "_demo_scores"}
    result.update({
        "record_id":         rid,
        "judge_model":       "demo-judge (no API call)",
        "constraint_scores": scores,
        **metrics,
        "error":             None,
        "timestamp_utc":     datetime.now(timezone.utc).isoformat(),
    })
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("AOSL Fast Batch Scorer — Dry-Run Demo")
    print("=" * 60)
    print(f"Records   : {len(FAKE_RECORDS)}")
    print(f"API calls : NONE (hardcoded scores)")
    print(f"Output    : {JSONL_PATH}")
    print()

    results = []

    # Write JSONL incrementally (same pattern as the real batch runner).
    with open(JSONL_PATH, "w", encoding="utf-8") as fh:
        for idx, record in enumerate(FAKE_RECORDS):
            result = build_demo_result(record, idx)
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")

            rid  = result["record_id"]
            D    = result["D"]
            tier = result["stability_tier"]
            print(f"  [{idx + 1}/{len(FAKE_RECORDS)}] scored record_id={rid}  D={D}  tier={tier}")
            results.append(result)

    print()
    export_csv(JSONL_PATH, CSV_PATH)

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    for r in results:
        print(
            f"  {r['record_id']:<12}  "
            f"D={r['D']:.4f}  "
            f"D_norm={r['D_norm']:.4f}  "
            f"tier={r['stability_tier']}"
        )

    valid_D = [r["D"] for r in results if r.get("error") is None]
    if valid_D:
        avg_D = sum(valid_D) / len(valid_D)
        print(f"\n  Avg D : {avg_D:.4f}")

    print()
    print(f"  JSONL : {JSONL_PATH}")
    print(f"  CSV   : {CSV_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
