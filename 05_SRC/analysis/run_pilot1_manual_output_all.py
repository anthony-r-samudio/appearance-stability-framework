import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SCRIPTS = [
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_check.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_manifest.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_inventory.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_overview.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_summary.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_table.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_export.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_report_export.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_readme.py",
    REPO_ROOT / "05_SRC" / "analysis" / "pilot1_manual_output_index.py",
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
    print("Pilot 1 manual output all complete.")


if __name__ == "__main__":
    main()
