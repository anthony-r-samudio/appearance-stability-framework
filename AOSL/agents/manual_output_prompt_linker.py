from AOSL.scoring.schema import ScoredOutput


def build_prompt_lookup(prompt_rows: list[dict]) -> dict[str, dict]:
    lookup = {}
    for row in prompt_rows:
        prompt_id = row.get("prompt_id", "")
        if prompt_id:
            lookup[prompt_id] = row
    return lookup


def get_prompt_preview(prompt_row: dict, max_length: int = 72) -> str:
    text = prompt_row.get("text", "[prompt not found]")
    text = text.replace("\n", " ").strip()
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def get_prompt_linked_rows(
    prompt_rows: list[dict],
    batch: list[ScoredOutput],
) -> list[dict]:
    lookup = build_prompt_lookup(prompt_rows)
    rows = []
    for output in batch:
        prompt_row = lookup.get(output.prompt_id, {})
        rows.append({
            "prompt_id":      output.prompt_id,
            "model_name":     output.model_name,
            "prompt_preview": get_prompt_preview(prompt_row),
        })
    return rows
