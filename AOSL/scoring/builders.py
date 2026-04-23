from typing import Optional

from AOSL.scoring.schema import ScoredOutput


def make_scored_output(
    prompt_id: str,
    model_name: str,
    output_text: str,
    constraint_scores: dict[str, float],
    notes: Optional[str] = None,
) -> ScoredOutput:
    return ScoredOutput(
        prompt_id=prompt_id,
        model_name=model_name,
        output_text=output_text,
        constraint_scores=constraint_scores,
        notes=notes,
    )
