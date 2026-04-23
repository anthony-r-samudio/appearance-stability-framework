from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoredOutput:
    prompt_id: str
    model_name: str
    output_text: str
    constraint_scores: dict[str, float]  # keys are c1–c10 constraint codes
    notes: Optional[str] = None
