"""
run_aosl_demo_v0_1.py

Launches the AOSL Demo v0.1 Streamlit app.

Usage:
    py 05_SRC\scripts\run_aosl_demo_v0_1.py

Requires:
    py -m pip install streamlit
    $env:OPENROUTER_API_KEY = 'sk-or-v1-...'
"""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_APP       = _REPO_ROOT / "05_SRC" / "apps" / "aosl_demo_v0_1.py"


def main() -> None:
    print("=" * 60)
    print("AOSL Demo v0.1 — AI Output Stability Checker")
    print(f"  app : {_APP}")
    print("=" * 60)
    print()

    if not _APP.exists():
        print(f"ERROR: App file not found: {_APP}")
        sys.exit(1)

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(_APP)],
        check=False,
    )


if __name__ == "__main__":
    main()
