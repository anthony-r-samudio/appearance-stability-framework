import json
from pathlib import Path

from AOSL.scoring import (
    make_scored_output,
    save_many_to_json,
    save_many_to_csv,
    validate_output,
)

REPO_ROOT    = Path(__file__).resolve().parent.parent.parent
PROMPTS_PATH = REPO_ROOT / "02_PROMPTS" / "pilot1_prompts.jsonl"
OUTPUT_DIR   = REPO_ROOT / "04_RUNS" / "pilot1"
JSON_PATH    = OUTPUT_DIR / "pilot1_prompt_pipeline_batch.json"
CSV_PATH     = OUTPUT_DIR / "pilot1_prompt_pipeline_batch.csv"

# Placeholder scores used for all prompts.
# Replace these with real scores when a scorer is available.
PLACEHOLDER_SCORES = {
    "c1": 0.7, "c2": 0.7, "c3": 0.7,
    "c4": 0.7, "c5": 0.7, "c6": 0.7,
    "c7": 0.7, "c8": 0.7, "c9": 0.7,
    "c10": 0.7,
}


def load_prompts(path: Path) -> list[dict]:
    prompts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                prompts.append(json.loads(line))
    return prompts


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prompts = load_prompts(PROMPTS_PATH)
    print(f"Loaded {len(prompts)} prompt(s) from {PROMPTS_PATH.name}\n")

    outputs = []
    for prompt in prompts:
        output = make_scored_output(
            prompt_id=prompt["prompt_id"],
            model_name="placeholder",
            output_text="[Placeholder model output — not yet evaluated.]",
            constraint_scores=PLACEHOLDER_SCORES.copy(),
            notes=f"Prompt: {prompt['text']}",
        )
        result = validate_output(output)
        status = "VALID" if result.is_valid else "INVALID"
        print(f"  {output.prompt_id}: {status}")
        outputs.append(output)

    save_many_to_json(outputs, JSON_PATH)
    save_many_to_csv(outputs, CSV_PATH)

    print(f"\nSaved {len(outputs)} output(s) to:")
    print(f"  {JSON_PATH}")
    print(f"  {CSV_PATH}")


if __name__ == "__main__":
    main()
