from pathlib import Path

from AOSL.agents.manual_output_loader import get_run_dir, load_manual_output_batch
from AOSL.agents.manual_output_reporter import build_report_text

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
OUTPUT_NAME = "pilot1_manual_output_report.txt"


def main():
    batch       = load_manual_output_batch(REPO_ROOT)
    output_path = get_run_dir(REPO_ROOT) / OUTPUT_NAME
    output_path.write_text(build_report_text(batch), encoding="utf-8")
    print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
