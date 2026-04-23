import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SCRIPTS = [
    REPO_ROOT / "05_SRC" / "scripts"  / "demo_pilot1_run.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_summary.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_table.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_export.py",
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
    print("Pilot 1 demo complete.")


if __name__ == "__main__":
    main()
