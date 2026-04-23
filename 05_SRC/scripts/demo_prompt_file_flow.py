import json
from pathlib import Path

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import (
    load_many_from_json,
    make_scored_output,
    save_many_to_json,
    to_flat_rows,
    validate_output,
)

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
INPUT_PATH  = REPO_ROOT / "09_TEMP" / "demo_prompts.json"
OUTPUT_PATH = REPO_ROOT / "09_TEMP" / "demo_prompt_file_outputs.json"

PLACEHOLDER_SCORES = {c.code: 1.0 for c in CONSTRAINTS}


def main():
    # 1. Read input prompts
    prompts = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(prompts)} prompt(s) from {INPUT_PATH.name}")

    # 2 & 3 & 4. Build, validate, and print results
    outputs = []
    for prompt in prompts:
        output = make_scored_output(
            prompt_id=prompt["prompt_id"],
            model_name="placeholder-model",
            output_text=f"Placeholder output for: {prompt['prompt_text']}",
            constraint_scores=PLACEHOLDER_SCORES.copy(),
            notes="Placeholder — real scoring not yet implemented.",
        )

        result = validate_output(output)
        print(f"\nValidation result for {output.prompt_id}:")
        print(f"  is_valid:            {result.is_valid}")
        print(f"  unknown_codes:       {result.unknown_codes}")
        print(f"  missing_codes:       {result.missing_codes}")
        print(f"  out_of_range_scores: {result.out_of_range_scores}")

        outputs.append(output)

    # 5. Save all outputs
    save_many_to_json(outputs, OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")

    # 6. Load back
    loaded = load_many_from_json(OUTPUT_PATH)
    print(f"Loaded back {len(loaded)} output(s)")

    # 7 & 8. Flatten and print summary
    rows = to_flat_rows(loaded)
    print(f"Flattened into {len(rows)} row(s)")
    for row in rows:
        print(f"\n  prompt_id:  {row['prompt_id']}")
        print(f"  model_name: {row['model_name']}")
        print(f"  c1–c10:     {[row[c.code] for c in CONSTRAINTS]}")


if __name__ == "__main__":
    main()
