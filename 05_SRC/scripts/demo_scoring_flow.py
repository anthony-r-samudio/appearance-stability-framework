from pathlib import Path

from AOSL.scoring import (
    load_from_json,
    make_scored_output,
    save_to_json,
    to_flat_row,
    validate_output,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "09_TEMP" / "demo_output.json"


def main():
    # 1. Build one ScoredOutput
    output = make_scored_output(
        prompt_id="demo-001",
        model_name="demo-model",
        output_text="This is a demo output for the AOSL scoring flow.",
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
        notes="Demo run.",
    )

    # 2 & 3. Validate and print result
    result = validate_output(output)
    print("Validation result:")
    print(f"  is_valid:            {result.is_valid}")
    print(f"  unknown_codes:       {result.unknown_codes}")
    print(f"  missing_codes:       {result.missing_codes}")
    print(f"  out_of_range_scores: {result.out_of_range_scores}")

    # 4. Save to 09_TEMP/
    save_to_json(output, OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")

    # 5. Load back
    loaded = load_from_json(OUTPUT_PATH)
    print(f"\nLoaded: {loaded}")

    # 6 & 7. Flatten into a row and print
    row = to_flat_row(loaded)
    print("\nFlat row:")
    for key, value in row.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
