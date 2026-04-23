from pathlib import Path

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import load_many_from_json, to_flat_rows

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = REPO_ROOT / "04_RUNS" / "pilot1" / "pilot1_prompt_pipeline_batch.json"

SCORE_COLS = [c.code for c in CONSTRAINTS]


def main():
    outputs = load_many_from_json(INPUT_PATH)
    rows = to_flat_rows(outputs)
    print(f"Loaded {len(rows)} output(s) from {INPUT_PATH.name}\n")

    header = f"{'prompt_id':<16} {'model_name':<14}" + "".join(f" {code:>5}" for code in SCORE_COLS)
    print(header)
    print("-" * len(header))

    for row in rows:
        scores = "".join(
            f" {row[code]:>5.2f}" if row[code] is not None else f" {'n/a':>5}"
            for code in SCORE_COLS
        )
        print(f"{row['prompt_id']:<16} {row['model_name']:<14}{scores}")


if __name__ == "__main__":
    main()
