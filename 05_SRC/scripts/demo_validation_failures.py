from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import validate_scores


def print_result(case_name: str, scores: dict) -> None:
    result = validate_scores(scores)
    print(f"\nCase: {case_name}")
    print(f"  is_valid:            {result.is_valid}")
    print(f"  unknown_codes:       {result.unknown_codes}")
    print(f"  missing_codes:       {result.missing_codes}")
    print(f"  out_of_range_scores: {result.out_of_range_scores}")


def main():
    valid_scores = {c.code: 1.0 for c in CONSTRAINTS}

    missing_code_scores = {
        code: value
        for code, value in valid_scores.items()
        if code != "c1"
    }

    unknown_code_scores = {**valid_scores, "c999": 1.0}

    out_of_range_scores = {**valid_scores, "c1": 1.5}

    print_result("valid_scores",         valid_scores)
    print_result("missing_code_scores",  missing_code_scores)
    print_result("unknown_code_scores",  unknown_code_scores)
    print_result("out_of_range_scores",  out_of_range_scores)


if __name__ == "__main__":
    main()
