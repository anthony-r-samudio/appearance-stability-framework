import csv
from pathlib import Path
from typing import Union

from AOSL.scoring.flatten import to_flat_rows
from AOSL.scoring.schema import ScoredOutput


def save_many_to_csv(outputs: list[ScoredOutput], path: Union[str, Path]) -> None:
    rows = to_flat_rows(outputs)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
