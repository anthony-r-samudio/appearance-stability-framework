from pathlib import Path

from AOSL.agents.manual_output_artifact_inspector import get_inventory_lines

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUN_DIR   = REPO_ROOT / "04_RUNS" / "pilot1"


def main():
    for line in get_inventory_lines(RUN_DIR):
        print(line)


if __name__ == "__main__":
    main()
