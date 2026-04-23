from AOSL.scoring import make_scored_output, validate_output

INVALID_OUTPUTS = [
    make_scored_output(
        prompt_id="invalid-001",
        model_name="demo-model",
        output_text="Missing c3, c5, c9.",
        constraint_scores={
            "c1": 0.9, "c2": 0.8, "c4": 0.7,
            "c6": 1.0, "c7": 0.6, "c8": 0.5,
            "c10": 0.7,
        },
    ),
    make_scored_output(
        prompt_id="invalid-002",
        model_name="demo-model",
        output_text="Score out of range on c1 and c8.",
        constraint_scores={
            "c1": 1.5, "c2": 0.8, "c3": 0.7,
            "c4": 0.6, "c5": 0.8, "c6": 1.0,
            "c7": 0.7, "c8": -0.2, "c9": 0.6,
            "c10": 0.7,
        },
    ),
    make_scored_output(
        prompt_id="invalid-003",
        model_name="demo-model",
        output_text="Unknown code cx included.",
        constraint_scores={
            "c1": 0.9, "c2": 0.8, "c3": 0.7,
            "c4": 0.6, "c5": 0.8, "c6": 1.0,
            "c7": 0.7, "c8": 0.5, "c9": 0.6,
            "c10": 0.7, "cx": 0.3,
        },
    ),
]


def main():
    for output in INVALID_OUTPUTS:
        result = validate_output(output)
        print(f"prompt_id:          {output.prompt_id}")
        print(f"  is_valid:           {result.is_valid}")
        print(f"  unknown_codes:      {result.unknown_codes or 'none'}")
        print(f"  missing_codes:      {result.missing_codes or 'none'}")
        print(f"  out_of_range_scores:{result.out_of_range_scores or 'none'}")
        print()


if __name__ == "__main__":
    main()
