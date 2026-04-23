import subprocess
import sys
from pathlib import Path

from AOSL.agents.manual_output_orchestrator import get_master_script_paths, get_section_header

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_script(path: Path) -> None:
    for line in get_section_header(path):
        print(line)
    subprocess.run([sys.executable, str(path)], check=True)
    print()


def main():
    for script in get_master_script_paths(REPO_ROOT):
        run_script(script)
    print("Pilot 1 manual output master complete.")


if __name__ == "__main__":
    main()
