from dataclasses import dataclass


@dataclass(frozen=True)
class Constraint:
    code: str
    label: str


CONSTRAINTS = (
    Constraint("c1",  "Factual Grounding"),
    Constraint("c2",  "Logical Coherence"),
    Constraint("c3",  "Causal Integrity"),
    Constraint("c4",  "Epistemic Calibration"),
    Constraint("c5",  "Scope Discipline"),
    Constraint("c6",  "Safety Integrity"),
    Constraint("c7",  "Uncertainty Acknowledgment"),
    Constraint("c8",  "Quantitative Accuracy"),
    Constraint("c9",  "Evidence Traceability"),
    Constraint("c10", "Constraint Interaction Consistency"),
)

BY_CODE = {c.code: c for c in CONSTRAINTS}
