import json
from pathlib import Path
from typing import Union

from AOSL.scoring.schema import ScoredOutput
from AOSL.scoring.serialization import to_dict, to_json


def save_to_json(output: ScoredOutput, path: Union[str, Path]) -> None:
    Path(path).write_text(to_json(output), encoding="utf-8")


def save_many_to_json(outputs: list[ScoredOutput], path: Union[str, Path]) -> None:
    data = [to_dict(output) for output in outputs]
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_from_json(path: Union[str, Path]) -> ScoredOutput:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ScoredOutput(**data)


def load_many_from_json(path: Union[str, Path]) -> list[ScoredOutput]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [ScoredOutput(**item) for item in data]
