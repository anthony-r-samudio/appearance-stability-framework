from pathlib import Path

from AOSL.agents.manual_output_artifact_inspector import get_prompt_manifest_lines
from AOSL.agents.manual_output_loader import get_run_dir, load_manual_output_batch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    run_dir = get_run_dir(REPO_ROOT)
    batch   = load_manual_output_batch(REPO_ROOT)
    for line in get_prompt_manifest_lines(run_dir, batch):
        print(line)


if __name__ == "__main__":
    main()
