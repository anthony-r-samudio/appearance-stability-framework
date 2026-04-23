from pathlib import Path

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import load_many_from_json, to_flat_rows

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = REPO_ROOT / "09_TEMP" / "demo_batch.json"


def main():
    outputs = load_many_from_json(INPUT_PATH)
    print(f"Loaded {len(outputs)} output(s) from {INPUT_PATH.name}\n")

    rows = to_flat_rows(outputs)
    codes = [c.code for c in CONSTRAINTS]

    # Compute column widths from data
    id_w    = max(len("prompt_id"),  max(len(r["prompt_id"])  for r in rows))
    model_w = max(len("model_name"), max(len(r["model_name"]) for r in rows))
    score_w = 5  # wide enough for "0.00"

    # Header
    header = (
        f"{'prompt_id':<{id_w}}  "
        f"{'model_name':<{model_w}}  "
        + "  ".join(f"{code:>{score_w}}" for code in codes)
    )
    print(header)
    print("-" * len(header))

    # Data rows
    for row in rows:
        score_cells = "  ".join(
            f"{row[code]:>{score_w}.2f}" if row[code] is not None else f"{'n/a':>{score_w}}"
            for code in codes
        )
        print(f"{row['prompt_id']:<{id_w}}  {row['model_name']:<{model_w}}  {score_cells}")


if __name__ == "__main__":
    main()
