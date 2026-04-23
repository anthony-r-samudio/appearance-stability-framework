from dataclasses import dataclass

from AOSL.constraints import BY_CODE
from AOSL.scoring.schema import ScoredOutput

SCORE_MIN = 0.0
SCORE_MAX = 1.0


def get_valid_codes() -> set[str]:
    return set(BY_CODE.keys())


def find_unknown_codes(scores: dict[str, float]) -> set[str]:
    return set(scores.keys()) - get_valid_codes()


def find_missing_codes(scores: dict[str, float]) -> set[str]:
    return get_valid_codes() - set(scores.keys())


def find_out_of_range_scores(scores: dict[str, float]) -> dict[str, float]:
    return {
        code: value
        for code, value in scores.items()
        if not (SCORE_MIN <= value <= SCORE_MAX)
    }


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    unknown_codes: set[str]
    missing_codes: set[str]
    out_of_range_scores: dict[str, float]


def validate_scores(scores: dict[str, float]) -> ValidationResult:
    unknown = find_unknown_codes(scores)
    missing = find_missing_codes(scores)
    out_of_range = find_out_of_range_scores(scores)
    return ValidationResult(
        is_valid=not unknown and not missing and not out_of_range,
        unknown_codes=unknown,
        missing_codes=missing,
        out_of_range_scores=out_of_range,
    )


def validate_output(output: ScoredOutput) -> ValidationResult:
    return validate_scores(output.constraint_scores)
