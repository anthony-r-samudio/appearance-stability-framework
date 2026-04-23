import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SCRIPTS = [
    REPO_ROOT / "05_SRC" / "scripts"  / "run_pilot1_prompt_pipeline.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_prompt_pipeline_summary.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_prompt_pipeline_table.py",
]


def run_script(path: Path) -> None:
    print("=" * 60)
    print(f"Running: {path.relative_to(REPO_ROOT)}")
    print("=" * 60)
    subprocess.run([sys.executable, str(path)], check=True)
    print()


def main():
    for script in SCRIPTS:
        run_script(script)
    print("Pilot 1 prompt pipeline demo complete.")


if __name__ == "__main__":
    main()
