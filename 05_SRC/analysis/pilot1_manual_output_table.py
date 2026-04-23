from pathlib import Path

from AOSL.agents.manual_output_loader import load_manual_output_batch
from AOSL.agents.manual_output_reporter import get_table_rows
from AOSL.constraints import CONSTRAINTS

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
SCORE_COLS = [c.code for c in CONSTRAINTS]


def main():
    batch = load_manual_output_batch(REPO_ROOT)
    rows  = get_table_rows(batch)

    header = f"{'prompt_id':<16} {'model_name':<14}" + "".join(f" {code:>5}" for code in SCORE_COLS)
    print(header)
    print("-" * len(header))

    for row in rows:
        scores = "".join(f" {row[code]:>5.2f}" for code in SCORE_COLS)
        print(f"{row['prompt_id']:<16} {row['model_name']:<14}{scores}")


if __name__ == "__main__":
    main()
