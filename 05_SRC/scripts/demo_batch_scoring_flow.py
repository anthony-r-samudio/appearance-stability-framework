from pathlib import Path

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import (
    load_many_from_json,
    make_scored_output,
    save_many_to_json,
    to_flat_rows,
    validate_output,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "09_TEMP" / "demo_batch_scored_outputs.json"


def main():
    # 1. Build two example ScoredOutput objects with slightly different scores
    output_1 = make_scored_output(
        prompt_id="batch-001",
        model_name="demo-model",
        output_text="First demo output in the batch.",
        constraint_scores={c.code: 1.0 for c in CONSTRAINTS},
        notes="Demo batch — all scores 1.0.",
    )

    output_2 = make_scored_output(
        prompt_id="batch-002",
        model_name="demo-model",
        output_text="Second demo output in the batch.",
        constraint_scores={c.code: 0.7 for c in CONSTRAINTS},
        notes="Demo batch — all scores 0.7.",
    )

    outputs = [output_1, output_2]

    # 2 & 3. Validate both and print results
    for output in outputs:
        result = validate_output(output)
        print(f"Validation result for {output.prompt_id}:")
        print(f"  is_valid:            {result.is_valid}")
        print(f"  unknown_codes:       {result.unknown_codes}")
        print(f"  missing_codes:       {result.missing_codes}")
        print(f"  out_of_range_scores: {result.out_of_range_scores}")

    # 4. Save to 09_TEMP/
    save_many_to_json(outputs, OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")

    # 5. Load back
    loaded = load_many_from_json(OUTPUT_PATH)
    print(f"\nLoaded {len(loaded)} outputs:")
    for output in loaded:
        print(f"  {output}")

    # 6 & 7. Flatten into rows and print
    rows = to_flat_rows(loaded)
    print("\nFlat rows:")
    for i, row in enumerate(rows, start=1):
        print(f"\n  Row {i}:")
        for key, value in row.items():
            print(f"    {key}: {value}")


if __name__ == "__main__":
    main()
