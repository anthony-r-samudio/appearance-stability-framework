import json
from pathlib import Path

from AOSL.scoring import (
    make_scored_output,
    save_many_to_json,
    save_many_to_csv,
    validate_output,
)

REPO_ROOT       = Path(__file__).resolve().parent.parent.parent
PROMPTS_PATH    = REPO_ROOT / "02_PROMPTS" / "pilot1_prompts.jsonl"
OUTPUTS_PATH    = REPO_ROOT / "03_DATA" / "raw" / "pilot1_manual_outputs.jsonl"
OUTPUT_DIR      = REPO_ROOT / "04_RUNS" / "pilot1"
JSON_PATH       = OUTPUT_DIR / "pilot1_manual_output_batch.json"
CSV_PATH        = OUTPUT_DIR / "pilot1_manual_output_batch.csv"

# Placeholder scores — replace with real scores when available.
PLACEHOLDER_SCORES = {
    "c1": 0.7, "c2": 0.7, "c3": 0.7,
    "c4": 0.7, "c5": 0.7, "c6": 0.7,
    "c7": 0.7, "c8": 0.7, "c9": 0.7,
    "c10": 0.7,
}


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prompts = {p["prompt_id"]: p for p in load_jsonl(PROMPTS_PATH)}
    manual_outputs = {o["prompt_id"]: o for o in load_jsonl(OUTPUTS_PATH)}

    print(f"Loaded {len(prompts)} prompt(s) from {PROMPTS_PATH.name}")
    print(f"Loaded {len(manual_outputs)} manual output(s) from {OUTPUTS_PATH.name}\n")

    outputs = []
    for prompt_id, prompt in prompts.items():
        if prompt_id not in manual_outputs:
            print(f"  {prompt_id}: SKIPPED (no manual output found)")
            continue

        output = make_scored_output(
            prompt_id=prompt_id,
            model_name="manual",
            output_text=manual_outputs[prompt_id]["output_text"],
            constraint_scores=PLACEHOLDER_SCORES.copy(),
            notes=f"Prompt: {prompt['text']}",
        )
        result = validate_output(output)
        status = "VALID" if result.is_valid else "INVALID"
        print(f"  {prompt_id}: {status}")
        outputs.append(output)

    save_many_to_json(outputs, JSON_PATH)
    save_many_to_csv(outputs, CSV_PATH)

    print(f"\nSaved {len(outputs)} output(s) to:")
    print(f"  {JSON_PATH}")
    print(f"  {CSV_PATH}")


if __name__ == "__main__":
    main()
