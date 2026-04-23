import json
from pathlib import Path

from AOSL.scoring import load_many_from_json
from AOSL.scoring.schema import ScoredOutput


def get_run_dir(repo_root: Path) -> Path:
    return repo_root / "04_RUNS" / "pilot1"


def get_batch_path(repo_root: Path) -> Path:
    return get_run_dir(repo_root) / "pilot1_manual_output_batch.json"


def get_prompt_path(repo_root: Path) -> Path:
    return repo_root / "02_PROMPTS" / "pilot1_prompts.jsonl"


def load_manual_output_batch(repo_root: Path) -> list[ScoredOutput]:
    return load_many_from_json(get_batch_path(repo_root))


def load_pilot1_prompt_rows(repo_root: Path) -> list[dict]:
    rows = []
    with open(get_prompt_path(repo_root), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
