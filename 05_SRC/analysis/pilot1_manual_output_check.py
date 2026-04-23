from pathlib import Path

from AOSL.agents.manual_output_loader import get_batch_path, load_manual_output_batch
from AOSL.agents.manual_output_validator import get_check_lines

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    if not get_batch_path(REPO_ROOT).exists():
        print(f"  [FAIL] Batch file not found: {get_batch_path(REPO_ROOT).name}")
        print()
        print("FAIL")
        return

    batch = load_manual_output_batch(REPO_ROOT)
    for line in get_check_lines(batch):
        print(line)


if __name__ == "__main__":
    main()
