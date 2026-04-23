from AOSL.constraints import CONSTRAINTS
from AOSL.scoring.schema import ScoredOutput


def get_required_score_codes() -> list[str]:
    return [c.code for c in CONSTRAINTS]


def check_prompt_ids(batch: list[ScoredOutput]) -> tuple[bool, int]:
    missing = sum(1 for o in batch if not o.prompt_id)
    return missing == 0, missing


def check_model_names(batch: list[ScoredOutput]) -> tuple[bool, int]:
    missing = sum(1 for o in batch if not o.model_name)
    return missing == 0, missing


def check_constraint_coverage(batch: list[ScoredOutput]) -> dict[str, bool]:
    codes = get_required_score_codes()
    return {
        code: all(code in o.constraint_scores for o in batch)
        for code in codes
    }


def get_check_lines(batch: list[ScoredOutput]) -> list[str]:
    lines = [
        "Manual Output Validation",
        "=" * 40,
    ]

    def result(label: str, passed: bool) -> str:
        status = "OK  " if passed else "FAIL"
        return f"  [{status}] {label}"

    lines.append(result(f"Outputs loaded: {len(batch)}", len(batch) > 0))

    prompt_id_ok, missing_pids = check_prompt_ids(batch)
    lines.append(result("All outputs have prompt_id", prompt_id_ok))

    model_name_ok, missing_models = check_model_names(batch)
    lines.append(result("All outputs have model_name", model_name_ok))

    coverage = check_constraint_coverage(batch)
    for code, ok in coverage.items():
        label = CONSTRAINTS[next(i for i, c in enumerate(CONSTRAINTS) if c.code == code)].label
        lines.append(result(f"All outputs have score key: {code} ({label})", ok))

    all_passed = (
        len(batch) > 0
        and prompt_id_ok
        and model_name_ok
        and all(coverage.values())
    )
    lines.append("")
    lines.append("PASS" if all_passed else "FAIL")

    return lines
