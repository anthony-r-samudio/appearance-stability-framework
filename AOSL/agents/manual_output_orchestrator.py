from pathlib import Path


def get_master_script_paths(repo_root: Path) -> list[Path]:
    analysis = repo_root / "05_SRC" / "analysis"
    return [
        analysis / "pilot1_manual_output_check.py",
        analysis / "pilot1_manual_output_manifest.py",
        analysis / "pilot1_manual_output_inventory.py",
        analysis / "pilot1_manual_output_overview.py",
        analysis / "pilot1_manual_output_prompt_view.py",
        analysis / "pilot1_manual_output_summary.py",
        analysis / "pilot1_manual_output_table.py",
        analysis / "pilot1_manual_output_export.py",
        analysis / "pilot1_manual_output_report_export.py",
        analysis / "pilot1_manual_output_readme.py",
        analysis / "pilot1_manual_output_index.py",
    ]


def get_prompt_master_script_paths(repo_root: Path) -> list[Path]:
    analysis = repo_root / "05_SRC" / "analysis"
    return [
        analysis / "pilot1_manual_output_check.py",
        analysis / "pilot1_manual_output_overview.py",
        analysis / "pilot1_manual_output_prompt_manifest.py",
        analysis / "pilot1_manual_output_prompt_view.py",
        analysis / "pilot1_manual_output_prompt_export.py",
        analysis / "pilot1_manual_output_summary.py",
        analysis / "pilot1_manual_output_table.py",
    ]


def get_section_header(script_path: Path) -> list[str]:
    return [
        "=" * 60,
        f"Running: {script_path.name}",
        "=" * 60,
    ]
