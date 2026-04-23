from AOSL.constraints import CONSTRAINTS
from AOSL.scoring.schema import ScoredOutput


def get_overview_lines(batch: list[ScoredOutput]) -> list[str]:
    model_names = sorted({o.model_name for o in batch})
    prompt_ids  = [o.prompt_id for o in batch]
    score_cols  = [c.code for c in CONSTRAINTS]

    lines = [
        "Pilot 1 Manual Output — Overview",
        "=" * 40,
        f"Total outputs : {len(batch)}",
        f"Model names   : {', '.join(model_names)}",
        f"Prompt IDs    : {', '.join(prompt_ids)}",
        f"Score columns : {', '.join(score_cols)}",
    ]
    return lines


def get_summary_lines(batch: list[ScoredOutput]) -> list[str]:
    lines = [
        "Per-Constraint Mean Scores",
        "=" * 40,
    ]
    for constraint in CONSTRAINTS:
        code   = constraint.code
        label  = constraint.label
        scores = [o.constraint_scores[code] for o in batch if code in o.constraint_scores]
        mean   = sum(scores) / len(scores) if scores else 0.0
        lines.append(f"  {code:<4} {label:<36} {mean:.3f}")
    return lines


def get_table_rows(batch: list[ScoredOutput]) -> list[dict]:
    rows = []
    for output in batch:
        row = {
            "prompt_id":  output.prompt_id,
            "model_name": output.model_name,
        }
        for constraint in CONSTRAINTS:
            code     = constraint.code
            row[code] = output.constraint_scores.get(code, 0.0)
        rows.append(row)
    return rows


def build_report_text(batch: list[ScoredOutput]) -> str:
    lines = get_summary_lines(batch)
    lines.append("")
    lines.append(f"Total outputs: {len(batch)}")
    return "\n".join(lines) + "\n"
