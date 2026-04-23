from pathlib import Path

from AOSL.scoring import load_many_from_json, save_many_to_csv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_PATH  = REPO_ROOT / "04_RUNS" / "pilot1" / "demo_pilot1_batch.json"
OUTPUT_PATH = REPO_ROOT / "04_RUNS" / "pilot1" / "demo_pilot1_batch_export.csv"


def main():
    outputs = load_many_from_json(INPUT_PATH)
    save_many_to_csv(outputs, OUTPUT_PATH)
    print(f"Exported {len(outputs)} output(s) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
