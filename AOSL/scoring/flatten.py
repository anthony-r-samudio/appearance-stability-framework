from AOSL.constraints import CONSTRAINTS
from AOSL.scoring.schema import ScoredOutput


def to_flat_row(output: ScoredOutput) -> dict:
    row = {
        "prompt_id":   output.prompt_id,
        "model_name":  output.model_name,
        "output_text": output.output_text,
        "notes":       output.notes,
    }
    for constraint in CONSTRAINTS:
        row[constraint.code] = output.constraint_scores.get(constraint.code)
    return row


def to_flat_rows(outputs: list[ScoredOutput]) -> list[dict]:
    return [to_flat_row(output) for output in outputs]
