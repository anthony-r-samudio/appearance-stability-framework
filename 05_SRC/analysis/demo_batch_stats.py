import statistics
from pathlib import Path

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import load_many_from_json

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = REPO_ROOT / "09_TEMP" / "demo_batch.json"


def main():
    outputs = load_many_from_json(INPUT_PATH)
    print(f"Loaded {len(outputs)} output(s) from {INPUT_PATH.name}\n")

    print(f"{'Code':<6} {'Label':<40} {'Mean':>6} {'Min':>6} {'Max':>6}")
    print("-" * 68)

    for constraint in CONSTRAINTS:
        values = [
            o.constraint_scores[constraint.code]
            for o in outputs
            if constraint.code in o.constraint_scores
        ]
        if values:
            print(
                f"{constraint.code:<6} {constraint.label:<40}"
                f" {statistics.mean(values):>6.4f}"
                f" {min(values):>6.4f}"
                f" {max(values):>6.4f}"
            )
        else:
            print(f"{constraint.code:<6} {constraint.label:<40} {'no data':>6}")


if __name__ == "__main__":
    main()
