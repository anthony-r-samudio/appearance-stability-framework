import statistics
from pathlib import Path

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import load_many_from_json, to_flat_rows

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = REPO_ROOT / "09_TEMP" / "demo_batch.json"


def main():
    # Load outputs from batch file
    outputs = load_many_from_json(INPUT_PATH)
    print(f"Loaded {len(outputs)} output(s) from {INPUT_PATH.name}")

    # Flatten into rows
    rows = to_flat_rows(outputs)

    # Compute mean score for each canonical constraint
    print("\nMean scores per constraint:")
    for constraint in CONSTRAINTS:
        values = [
            row[constraint.code]
            for row in rows
            if row[constraint.code] is not None
        ]
        if values:
            mean = statistics.mean(values)
            print(f"  {constraint.code:<4}  {constraint.label:<40}  {mean:.4f}")
        else:
            print(f"  {constraint.code:<4}  {constraint.label:<40}  no data")


if __name__ == "__main__":
    main()
