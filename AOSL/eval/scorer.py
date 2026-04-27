import json

import anthropic

from AOSL.constraints.definitions import CONSTRAINTS

_SCORING_MODEL = "claude-sonnet-4-6"

_CONSTRAINT_LINES = "\n".join(
    f"  {c.code}: {c.label}" for c in CONSTRAINTS
)


def score_output(prompt_text: str, output_text: str) -> dict[str, float]:
    """Score one AI output against all AOSL constraints c1-c10.

    Returns a dict mapping each constraint code to a float in [0.0, 1.0].
    Raises ValueError if any score cannot be parsed or is out of range.
    """
    client = anthropic.Anthropic()

    scoring_prompt = f"""You are scoring an AI-generated output against 10 quality constraints.

For each constraint listed below, assign a score from 0.0 (complete failure) to 1.0 (perfect compliance).

Constraints:
{_CONSTRAINT_LINES}

PROMPT given to the AI:
{prompt_text}

OUTPUT produced by the AI:
{output_text}

Return ONLY a valid JSON object with constraint codes as keys and float scores as values.
Example format:
{{"c1": 0.8, "c2": 0.9, "c3": 0.7, "c4": 0.8, "c5": 0.9, "c6": 1.0, "c7": 0.8, "c8": 0.7, "c9": 0.6, "c10": 0.8}}

Do not include any explanation or extra text outside the JSON object."""

    message = client.messages.create(
        model=_SCORING_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": scoring_prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Scorer: could not parse JSON from model response.\n"
            f"Raw response: {raw!r}\n"
            f"JSON error: {e}"
        ) from e

    scores: dict[str, float] = {}
    for c in CONSTRAINTS:
        if c.code not in parsed:
            raise ValueError(
                f"Scorer: missing score for constraint '{c.code}'.\n"
                f"Parsed response: {parsed}"
            )
        val = parsed[c.code]
        if not isinstance(val, (int, float)):
            raise ValueError(
                f"Scorer: score for '{c.code}' is not a number: {val!r}"
            )
        score = float(val)
        if not (0.0 <= score <= 1.0):
            raise ValueError(
                f"Scorer: score for '{c.code}' is out of range [0.0, 1.0]: {score}"
            )
        scores[c.code] = score

    return scores
