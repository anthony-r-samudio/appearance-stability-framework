from pathlib import Path

from AOSL.agents.manual_output_loader import get_run_dir, load_manual_output_batch
from AOSL.scoring import save_many_to_csv

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
OUTPUT_NAME = "pilot1_manual_output_table.csv"


def main():
    batch       = load_manual_output_batch(REPO_ROOT)
    output_path = get_run_dir(REPO_ROOT) / OUTPUT_NAME
    save_many_to_csv(batch, output_path)
    print(f"Exported {len(batch)} output(s) to {output_path}")


if __name__ == "__main__":
    main()
