from pathlib import Path

from AOSL.agents.manual_output_loader import load_manual_output_batch
from AOSL.agents.manual_output_reporter import get_summary_lines

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    batch = load_manual_output_batch(REPO_ROOT)
    for line in get_summary_lines(batch):
        print(line)


if __name__ == "__main__":
    main()
