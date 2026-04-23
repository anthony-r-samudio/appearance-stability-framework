import csv
from pathlib import Path

from AOSL.agents.manual_output_loader import get_run_dir, load_manual_output_batch, load_pilot1_prompt_rows
from AOSL.agents.manual_output_prompt_linker import get_prompt_linked_rows

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
OUTPUT_NAME = "pilot1_manual_output_prompt_table.csv"


def main():
    prompt_rows = load_pilot1_prompt_rows(REPO_ROOT)
    batch       = load_manual_output_batch(REPO_ROOT)
    rows        = get_prompt_linked_rows(prompt_rows, batch)
    output_path = get_run_dir(REPO_ROOT) / OUTPUT_NAME

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["prompt_id", "model_name", "prompt_preview"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Prompt table exported to {output_path}")


if __name__ == "__main__":
    main()
