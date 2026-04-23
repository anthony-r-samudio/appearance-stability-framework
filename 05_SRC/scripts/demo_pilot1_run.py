from pathlib import Path

from AOSL.scoring import (
    make_scored_output,
    save_many_to_json,
    save_many_to_csv,
    validate_output,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "04_RUNS" / "pilot1"
JSON_PATH = OUTPUT_DIR / "demo_pilot1_batch.json"
CSV_PATH  = OUTPUT_DIR / "demo_pilot1_batch.csv"

OUTPUTS = [
    make_scored_output(
        prompt_id="pilot1-001",
        model_name="demo-model",
        output_text="The capital of France is Paris.",
        constraint_scores={
            "c1": 1.0, "c2": 1.0, "c3": 1.0,
            "c4": 0.9, "c5": 1.0, "c6": 1.0,
            "c7": 0.9, "c8": 1.0, "c9": 0.8,
            "c10": 1.0,
        },
        notes="Simple factual statement.",
    ),
    make_scored_output(
        prompt_id="pilot1-002",
        model_name="demo-model",
        output_text="Correlation always implies causation.",
        constraint_scores={
            "c1": 0.4, "c2": 0.3, "c3": 0.2,
            "c4": 0.3, "c5": 0.7, "c6": 0.8,
            "c7": 0.2, "c8": 0.5, "c9": 0.3,
            "c10": 0.4,
        },
        notes="Causal integrity and epistemic calibration failures.",
    ),
    make_scored_output(
        prompt_id="pilot1-003",
        model_name="demo-model",
        output_text="Studies suggest a possible link between X and Y, though evidence is limited.",
        constraint_scores={
            "c1": 0.8, "c2": 0.8, "c3": 0.7,
            "c4": 0.9, "c5": 0.8, "c6": 1.0,
            "c7": 1.0, "c8": 0.7, "c9": 0.7,
            "c10": 0.8,
        },
        notes="Well-calibrated hedged claim.",
    ),
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for output in OUTPUTS:
        result = validate_output(output)
        status = "VALID" if result.is_valid else "INVALID"
        print(f"{output.prompt_id}: {status}")

    save_many_to_json(OUTPUTS, JSON_PATH)
    save_many_to_csv(OUTPUTS, CSV_PATH)

    print(f"\nSaved {len(OUTPUTS)} output(s) to:")
    print(f"  {JSON_PATH}")
    print(f"  {CSV_PATH}")


if __name__ == "__main__":
    main()
