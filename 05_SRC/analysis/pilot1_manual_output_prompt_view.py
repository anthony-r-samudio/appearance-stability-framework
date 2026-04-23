from pathlib import Path

from AOSL.agents.manual_output_loader import load_manual_output_batch, load_pilot1_prompt_rows
from AOSL.agents.manual_output_prompt_linker import get_prompt_linked_rows

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
PREVIEW_LEN = 72


def main():
    prompt_rows = load_pilot1_prompt_rows(REPO_ROOT)
    batch       = load_manual_output_batch(REPO_ROOT)
    rows        = get_prompt_linked_rows(prompt_rows, batch)

    print("Pilot 1 Manual Output — Prompt View")
    print("=" * 60)
    print(f"  {'prompt_id':<12} {'model_name':<10} {'prompt preview'}")
    print(f"  {'-'*12} {'-'*10} {'-'*PREVIEW_LEN}")

    for row in rows:
        print(f"  {row['prompt_id']:<12} {row['model_name']:<10} {row['prompt_preview']}")

    print()
    print(f"Total outputs: {len(rows)}")


if __name__ == "__main__":
    main()
