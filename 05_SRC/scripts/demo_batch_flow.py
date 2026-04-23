from pathlib import Path

from AOSL.scoring import (
    load_many_from_json,
    make_scored_output,
    save_many_to_json,
    to_flat_rows,
    validate_output,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "09_TEMP" / "demo_batch.json"


def main():
    # Build 3 example ScoredOutput objects
    output_1 = make_scored_output(
        prompt_id="batch-001",
        model_name="demo-model",
        output_text="First example output.",
        constraint_scores={
            "c1":  1.0,
            "c2":  1.0,
            "c3":  1.0,
            "c4":  1.0,
            "c5":  1.0,
            "c6":  1.0,
            "c7":  1.0,
            "c8":  1.0,
            "c9":  1.0,
            "c10": 1.0,
        },
        notes="All scores 1.0.",
    )

    output_2 = make_scored_output(
        prompt_id="batch-002",
        model_name="demo-model",
        output_text="Second example output.",
        constraint_scores={
            "c1":  0.9,
            "c2":  0.8,
            "c3":  0.7,
            "c4":  0.6,
            "c5":  0.8,
            "c6":  1.0,
            "c7":  0.7,
            "c8":  0.5,
            "c9":  0.6,
            "c10": 0.7,
        },
        notes="Mixed scores.",
    )

    output_3 = make_scored_output(
        prompt_id="batch-003",
        model_name="demo-model",
        output_text="Third example output.",
        constraint_scores={
            "c1":  0.5,
            "c2":  0.5,
            "c3":  0.5,
            "c4":  0.5,
            "c5":  0.5,
            "c6":  0.5,
            "c7":  0.5,
            "c8":  0.5,
            "c9":  0.5,
            "c10": 0.5,
        },
        notes="All scores 0.5.",
    )

    outputs = [output_1, output_2, output_3]

    # Validate each and print results
    for output in outputs:
        result = validate_output(output)
        print(f"Validation for {output.prompt_id}:")
        print(f"  is_valid:            {result.is_valid}")
        print(f"  unknown_codes:       {result.unknown_codes}")
        print(f"  missing_codes:       {result.missing_codes}")
        print(f"  out_of_range_scores: {result.out_of_range_scores}")

    # Save all to one JSON file
    save_many_to_json(outputs, OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")

    # Load back
    loaded = load_many_from_json(OUTPUT_PATH)
    print(f"Loaded back {len(loaded)} output(s)")

    # Flatten and print rows
    rows = to_flat_rows(loaded)
    print(f"\nFlat rows ({len(rows)} total):")
    for i, row in enumerate(rows, start=1):
        print(f"\n  Row {i}:")
        for key, value in row.items():
            print(f"    {key}: {value}")


if __name__ == "__main__":
    main()
