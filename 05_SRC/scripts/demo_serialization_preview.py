import json

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import make_scored_output, to_dict, to_json


def main():
    # 1. Build one example ScoredOutput
    output = make_scored_output(
        prompt_id="serial-001",
        model_name="demo-model",
        output_text="Example output for serialization preview.",
        constraint_scores={c.code: 0.9 for c in CONSTRAINTS},
        notes="Serialization demo.",
    )

    # 2 & 4. Convert to dict and print
    as_dict = to_dict(output)
    print("Single object — dict preview:")
    print(as_dict)

    # 3 & 4. Convert to JSON and print
    as_json = to_json(output)
    print("\nSingle object — JSON preview:")
    print(as_json)

    # 5. Build a batch of 2 outputs
    output_2 = make_scored_output(
        prompt_id="serial-002",
        model_name="demo-model",
        output_text="Second example output for serialization preview.",
        constraint_scores={c.code: 0.7 for c in CONSTRAINTS},
        notes="Serialization demo — second item.",
    )

    batch = [output, output_2]

    # 6 & 7. Serialize batch using to_dict + standard library json, then print
    batch_json = json.dumps([to_dict(o) for o in batch], indent=2)
    print("\nBatch — JSON preview:")
    print(batch_json)


if __name__ == "__main__":
    main()
