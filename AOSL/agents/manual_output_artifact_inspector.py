from pathlib import Path

from AOSL.scoring.schema import ScoredOutput

ARTIFACT_NAMES = [
    "pilot1_manual_output_batch.json",
    "pilot1_manual_output_table.csv",
    "pilot1_manual_output_report.txt",
    "pilot1_manual_output_README.txt",
    "pilot1_manual_output_INDEX.txt",
    "pilot1_manual_output_prompt_table.csv",
]


def get_artifact_paths(run_dir: Path) -> dict[str, Path]:
    return {name: run_dir / name for name in ARTIFACT_NAMES}


def get_artifact_status_lines(run_dir: Path) -> list[str]:
    paths = get_artifact_paths(run_dir)
    lines = []
    for name, path in paths.items():
        status = "OK  " if path.exists() else "MISS"
        lines.append(f"  [{status}] {name}")
    return lines


def get_manifest_lines(run_dir: Path, batch: list[ScoredOutput]) -> list[str]:
    batch_path = run_dir / "pilot1_manual_output_batch.json"
    status_lines = get_artifact_status_lines(run_dir)

    lines = [
        "Pilot 1 Manual Output Manifest",
        "=" * 40,
        "",
        "Artifacts:",
    ]
    results = [("[MISS]" not in line) for line in status_lines]
    lines.extend(status_lines)

    if batch_path.exists():
        prompt_ids = [o.prompt_id for o in batch]
        lines.append(f"\nOutputs loaded : {len(batch)}")
        lines.append(f"Prompt IDs     : {', '.join(prompt_ids)}")
        results.append(len(batch) > 0)
    else:
        lines.append("\nBatch JSON missing — cannot load outputs.")
        results.append(False)

    lines.append("")
    lines.append("PASS" if all(results) else "FAIL")
    return lines


def get_prompt_manifest_lines(run_dir: Path, batch: list[ScoredOutput]) -> list[str]:
    batch_path  = run_dir / "pilot1_manual_output_batch.json"
    csv_path    = run_dir / "pilot1_manual_output_prompt_table.csv"

    lines = [
        "Pilot 1 Manual Output Prompt Manifest",
        "=" * 40,
    ]
    results = []

    for path in (batch_path, csv_path):
        exists = path.exists()
        status = "OK  " if exists else "MISS"
        lines.append(f"  [{status}] {path.name}")
        results.append(exists)

    if batch_path.exists():
        prompt_ids = [o.prompt_id for o in batch]
        lines.append(f"\nOutputs loaded : {len(batch)}")
        lines.append(f"Prompt IDs     : {', '.join(prompt_ids)}")
        results.append(len(batch) > 0)
    else:
        lines.append("\nBatch JSON missing — cannot load outputs.")
        results.append(False)

    lines.append("")
    lines.append("PASS" if all(results) else "FAIL")
    return lines


def get_inventory_lines(run_dir: Path) -> list[str]:
    paths = get_artifact_paths(run_dir)
    lines = [
        "Manual Output Artifact Inventory",
        "=" * 40,
    ]
    results = []
    for name, path in paths.items():
        exists = path.exists()
        status = "OK  " if exists else "MISS"
        lines.append(f"  [{status}] {name}")
        results.append(exists)
    lines.append("")
    lines.append("PASS" if all(results) else "FAIL")
    return lines
