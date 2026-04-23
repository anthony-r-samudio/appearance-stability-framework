import json
from dataclasses import asdict

from AOSL.scoring.schema import ScoredOutput


def to_dict(output: ScoredOutput) -> dict:
    return asdict(output)


def to_json(output: ScoredOutput) -> str:
    return json.dumps(to_dict(output), indent=2)
