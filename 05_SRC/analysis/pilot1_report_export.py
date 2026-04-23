import statistics
from pathlib import Path

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import load_many_from_json

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
INPUT_PATH  = REPO_ROOT / "04_RUNS" / "pilot1" / "demo_pilot1_batch.json"
OUTPUT_PATH = REPO_ROOT / "06_OUTPUTS" / "pilot1_summary.txt"


def build_report(outputs: list) -> str:
    lines = []
    lines.append("AOSL Pilot 1 Summary Report")
    lines.append("=" * 40)
    lines.append(f"Outputs scored: {len(outputs)}")
    lines.append("")
    lines.append(f"{'Code':<6} {'Label':<40} {'Mean':>6}")
    lines.append("-" * 55)

    for constraint in CONSTRAINTS:
        values = [
            o.constraint_scores[constraint.code]
            for o in outputs
            if constraint.code in o.constraint_scores
        ]
        if values:
            lines.append(f"{constraint.code:<6} {constraint.label:<40} {statistics.mean(values):>6.4f}")
        else:
            lines.append(f"{constraint.code:<6} {constraint.label:<40} {'no data':>6}")

    return "\n".join(lines) + "\n"


def main():
    outputs = load_many_from_json(INPUT_PATH)
    report = build_report(outputs)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")

    print(f"Report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
