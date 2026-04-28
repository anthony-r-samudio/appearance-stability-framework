"""
fast_batch_scorer.py  (05_SRC/scoring/)

Batch-scoring pipeline for AOSL c1–c10 constraint evaluation.

Scorer: DEMO placeholder (deterministic, hash-based, no API calls).
        Outputs are NOT real evaluations — for pipeline testing only.
        Scorer is clearly identified in every output row via the 'scorer' field.

Public API:
    load_input(path)          → list[dict]   — reads .csv or .jsonl
    score_batch(rows)         → list[dict]   — scores every row
    save_outputs(rows, ...)   → None         — writes CSV + JSONL
    score_row(row)            → dict         — scores one row (also usable standalone)
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

# ── sys.path: repo root needed for AOSL package ─────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from AOSL.constraints.definitions import CONSTRAINTS

# ── Constants ────────────────────────────────────────────────────────────────────

CONSTRAINT_CODES  = [c.code for c in CONSTRAINTS]   # ["c1", ..., "c10"]
DEMO_SCORER_LABEL = "demo-placeholder-v1"

# Canonical CSV column order for scored output rows.
OUTPUT_FIELDS = [
    "prompt_id", "prompt_text", "model_name", "temperature", "repeat",
    *CONSTRAINT_CODES,
    "divergence", "stability_score", "stability_tier",
    "notes", "scorer",
]


# ── Demo scorer ──────────────────────────────────────────────────────────────────

def _demo_score(output_text: str, constraint_code: str) -> float:
    """
    Deterministic hash-based score for one output × constraint pair.
    Returns a float in [0.5, 1.0]. Same inputs always produce the same score.
    NOT a real evaluation.
    """
    key = f"{output_text[:300]}|{constraint_code}"
    raw = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return round(0.5 + raw * 0.5, 4)


def score_output_demo(output_text: str) -> dict[str, float]:
    """Return deterministic demo c1–c10 scores for one output text."""
    return {code: _demo_score(output_text, code) for code in CONSTRAINT_CODES}


# ── Metrics ──────────────────────────────────────────────────────────────────────
# Formula mirrors AOSL.agents.fast_batch_scorer.compute_metrics exactly.
# Reimplemented here to avoid importing the openai-dependent agents module.

def _compute_metrics(scores: dict[str, float]) -> dict:
    """
    D             = sum(1 - c_i) for c1..c10  (raw divergence, range 0–10)
    D_norm        = D / 10                     (normalised, range 0–1)
    divergence    = D_norm
    stability_score = 1 - D_norm              (higher = more stable)
    stability_tier: S0 (≤0.10) · S1 (≤0.25) · S2 (≤0.50) · S3 (>0.50)
    """
    D      = sum(1.0 - scores[k] for k in CONSTRAINT_CODES)
    D_norm = D / 10.0
    if D_norm <= 0.10:
        tier = "S0"
    elif D_norm <= 0.25:
        tier = "S1"
    elif D_norm <= 0.50:
        tier = "S2"
    else:
        tier = "S3"
    return {
        "divergence":      round(D_norm,        6),
        "stability_score": round(1.0 - D_norm,  6),
        "stability_tier":  tier,
    }


# ── Row scorer ───────────────────────────────────────────────────────────────────

def score_row(row: dict) -> dict:
    """
    Score one input row.
    Adds c1–c10 scores, divergence, stability_score, stability_tier, scorer label.
    Preserves all original fields. Missing optional fields default to empty string.
    """
    output_text = str(row.get("output_text", ""))
    scores      = score_output_demo(output_text)
    metrics     = _compute_metrics(scores)

    result = dict(row)
    result.update(scores)
    result.update(metrics)
    result["scorer"] = DEMO_SCORER_LABEL
    result.setdefault("temperature", "")
    result.setdefault("repeat",      "")
    result.setdefault("notes",       "")
    return result


# ── Batch scorer ─────────────────────────────────────────────────────────────────

def score_batch(rows: list[dict]) -> list[dict]:
    """Score a list of input rows. Returns a list of enriched scored row dicts."""
    return [score_row(row) for row in rows]


# ── I/O ──────────────────────────────────────────────────────────────────────────

def load_input(path: "str | Path") -> list[dict]:
    """
    Load input rows from a .csv or .jsonl file.
    Each row must have at minimum: prompt_id, model_name, output_text.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}\n"
            "Check the path and try again."
        )
    ext = path.suffix.lower()
    if ext == ".csv":
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    if ext == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows
    raise ValueError(
        f"Unsupported file type '{ext}'. "
        "Supported formats: .csv, .jsonl"
    )


def save_outputs(rows: list[dict], csv_path: Path, jsonl_path: Path) -> None:
    """Write scored rows to a flat CSV and a JSONL file."""
    if not rows:
        print("  [WARN] No rows to save.")
        return

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Build column order: canonical OUTPUT_FIELDS first, then any extra columns.
    seen     = {k for row in rows for k in row}
    ordered  = [f for f in OUTPUT_FIELDS if f in seen]
    extras   = [k for k in dict.fromkeys(k for row in rows for k in row)
                if k not in ordered]
    fieldnames = ordered + extras

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
