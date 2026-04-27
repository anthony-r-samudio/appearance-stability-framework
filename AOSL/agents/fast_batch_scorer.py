"""
fast_batch_scorer.py

Concurrent batch scoring for AOSL outputs via OpenRouter.

Features:
  - Loads records from JSON (list) or JSONL files
  - Skips already-scored record IDs (resume support)
  - Scores concurrently with ThreadPoolExecutor
  - Appends results to output JSONL incrementally (crash-safe)
  - Computes D, D_norm, stability_tier per record
  - Exports flat CSV with c1-c10 columns
"""

import csv
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from openai import OpenAI

from AOSL.constraints.definitions import CONSTRAINTS

# ── Constants ───────────────────────────────────────────────────────────────────

CONSTRAINT_KEYS = [c.code for c in CONSTRAINTS]  # ["c1", "c2", ..., "c10"]

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_CONSTRAINT_LINES = "\n".join(
    f"  {c.code}: {c.label}" for c in CONSTRAINTS
)

_SCORING_PROMPT_TEMPLATE = """\
You are an AOSL (AI Output Stability Layer) constraint scorer.

Score the following AI-generated output against each of the 10 AOSL constraints.
Assign a float score from 0.0 (complete failure) to 1.0 (perfect compliance).

Constraints:
{constraint_lines}

PROMPT given to the AI:
{prompt_text}

OUTPUT produced by the AI:
{output_text}

Return ONLY a valid JSON object with constraint codes as keys and float scores as values.
No explanation. No text outside the JSON object.
Example format:
{{"c1": 0.8, "c2": 0.9, "c3": 0.7, "c4": 0.8, "c5": 0.9, "c6": 1.0, "c7": 0.8, "c8": 0.7, "c9": 0.6, "c10": 0.8}}"""

# CSV column order for export.
_CSV_FIELDNAMES = [
    "record_id", "prompt_id", "model_name", "generator_model",
    "temperature", "repeat", "judge_model",
    "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10",
    "D", "D_norm", "stability_tier",
    "output_text", "prompt_text", "notes",
    "error", "timestamp_utc",
]


# ── OpenRouter client ────────────────────────────────────────────────────────────

def _get_openrouter_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY environment variable is not set.\n"
            'Set it with: $env:OPENROUTER_API_KEY="sk-or-v1-..."'
        )
    return OpenAI(base_url=_OPENROUTER_BASE_URL, api_key=api_key)


# ── JSON extraction ──────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """
    Parse a JSON object from model output text.
    Handles ```json ... ``` fences and bare JSON objects.
    Returns an empty dict if nothing can be parsed.
    """
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        candidate = brace_match.group(0) if brace_match else ""

    if not candidate:
        return {}

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {}


# ── Judge call ───────────────────────────────────────────────────────────────────

def _call_judge(judge_model: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """
    Call the OpenRouter judge model and return validated c1–c10 scores.
    Raises ValueError on parse failure, missing keys, or out-of-range values.
    """
    client  = _get_openrouter_client()
    scoring = _SCORING_PROMPT_TEMPLATE.format(
        constraint_lines=_CONSTRAINT_LINES,
        prompt_text=prompt_text or "(not provided)",
        output_text=output_text,
    )

    response = client.chat.completions.create(
        model=judge_model,
        messages=[{"role": "user", "content": scoring}],
        temperature=0.0,
    )
    raw    = response.choices[0].message.content.strip()
    parsed = _extract_json(raw)

    if not parsed:
        raise ValueError(f"Could not parse JSON from judge. Raw: {raw!r}")

    scores: dict[str, float] = {}
    for key in CONSTRAINT_KEYS:
        if key not in parsed:
            raise ValueError(f"Missing '{key}' in judge response: {parsed}")
        val = parsed[key]
        if not isinstance(val, (int, float)):
            raise ValueError(f"Score for '{key}' is not a number: {val!r}")
        score = float(val)
        if not (0.0 <= score <= 1.0):
            raise ValueError(f"Score for '{key}' out of range [0.0, 1.0]: {score}")
        scores[key] = score

    return scores


# ── Metrics ──────────────────────────────────────────────────────────────────────

def _stability_tier(d_norm: float) -> str:
    """
    Classify a normalized divergence score into an AOSL stability tier.
      S0 = D_norm <= 0.10  (highest stability)
      S1 = D_norm <= 0.25
      S2 = D_norm <= 0.50
      S3 = D_norm >  0.50  (lowest stability)
    """
    if d_norm <= 0.10:
        return "S0"
    if d_norm <= 0.25:
        return "S1"
    if d_norm <= 0.50:
        return "S2"
    return "S3"


def compute_metrics(scores: dict[str, float]) -> dict:
    """
    Compute divergence metrics from a set of c1–c10 constraint scores.

    D      = sum(1 - c_i) for i in c1..c10   (raw divergence, range 0–10)
    D_norm = D / 10                            (normalized, range 0–1)
    stability_tier = S0 / S1 / S2 / S3
    """
    D      = sum(1.0 - scores[k] for k in CONSTRAINT_KEYS)
    D_norm = D / 10.0
    return {
        "D":              round(D,      6),
        "D_norm":         round(D_norm, 6),
        "stability_tier": _stability_tier(D_norm),
    }


# ── Record helpers ───────────────────────────────────────────────────────────────

def _get_prompt_text(record: dict) -> str:
    """
    Extract the original prompt text from a record.
    Checks prompt_text first, then falls back to the notes field
    (which pilot1 records store as 'Prompt: {text}').
    """
    if "prompt_text" in record:
        return str(record["prompt_text"])
    notes = record.get("notes", "")
    if isinstance(notes, str) and notes.startswith("Prompt: "):
        return notes[len("Prompt: "):]
    return ""


def get_record_id(record: dict, idx: int) -> str:
    """
    Build a stable unique ID for a record to support resume/skip logic.

    For simple runs:        prompt_id         → "p1_factual"
    For temperature sweeps: prompt_id + temp  → "p1_factual__t0.6__r2"
    Falls back to row index if prompt_id is absent.
    """
    parts = [str(record.get("prompt_id", f"row{idx}"))]
    if "temperature" in record:
        parts.append(f"t{record['temperature']}")
    if "repeat" in record:
        parts.append(f"r{record['repeat']}")
    return "__".join(parts)


# ── I/O ──────────────────────────────────────────────────────────────────────────

def load_input_records(path: Path) -> list[dict]:
    """
    Load records from a JSON list file or JSONL file.

    Supports:
      - JSON:  a single list  [{"prompt_id": ...}, ...]
      - JSONL: one JSON dict per line
    """
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    if text.startswith("["):
        return json.loads(text)

    records = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def load_scored_ids(output_path: Path) -> set[str]:
    """
    Read an existing output JSONL file and return the set of successfully-scored
    record IDs. Records with an error are NOT included, so they get retried.
    """
    if not output_path.exists():
        return set()

    scored: set[str] = set()
    for line in output_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if "record_id" in rec and rec.get("error") is None:
                scored.add(rec["record_id"])
        except json.JSONDecodeError:
            pass
    return scored


# ── Single-record scorer ─────────────────────────────────────────────────────────

def score_one_record(record: dict, idx: int, judge_model: str) -> dict:
    """
    Score one record. Returns a result dict that preserves all input fields and
    adds: record_id, judge_model, constraint_scores, D, D_norm, stability_tier,
    error (None on success), timestamp_utc.

    Never raises — errors are captured into the 'error' field so the batch
    can continue even if individual records fail.
    """
    record_id   = get_record_id(record, idx)
    prompt_text = _get_prompt_text(record)
    output_text = record.get("output_text", "")

    try:
        scores  = _call_judge(judge_model, prompt_text, output_text)
        metrics = compute_metrics(scores)
        return {
            **record,
            "record_id":         record_id,
            "judge_model":       judge_model,
            "constraint_scores": scores,
            **metrics,
            "error":             None,
            "timestamp_utc":     datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        return {
            **record,
            "record_id":     record_id,
            "judge_model":   judge_model,
            "error":         str(exc),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }


# ── Batch runner ─────────────────────────────────────────────────────────────────

def run_batch(
    records:     list[dict],
    judge_model: str,
    output_path: Path,
    workers:     int = 4,
) -> list[dict]:
    """
    Score all records concurrently using ThreadPoolExecutor.

    - Skips records whose record_id is already in output_path (resume).
    - Appends each result to output_path (JSONL) immediately after scoring.
    - Prints progress: [N/total], [SKIP], [ERROR] lines.
    - Returns all result dicts produced in this run (excludes previously skipped).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    already_scored = load_scored_ids(output_path)
    write_lock     = Lock()

    to_score: list[tuple[int, dict]] = []
    skip_count = 0

    for idx, record in enumerate(records):
        rid = get_record_id(record, idx)
        if rid in already_scored:
            print(f"  [SKIP] record_id={rid}")
            skip_count += 1
        else:
            to_score.append((idx, record))

    total = len(to_score)
    done  = 0

    print(f"\nRecords to score : {total}  |  Already done : {skip_count}")
    print(f"Judge model      : {judge_model}")
    print(f"Workers          : {workers}\n")

    results: list[dict] = []

    def _score_and_write(pair: tuple[int, dict]) -> dict:
        idx, record = pair
        result = score_one_record(record, idx, judge_model)
        line   = json.dumps(result, ensure_ascii=False)
        with write_lock:
            with open(output_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_score_and_write, pair): pair for pair in to_score}
        for future in as_completed(futures):
            done  += 1
            result = future.result()
            rid    = result.get("record_id", "?")

            if result.get("error") is not None:
                print(f"  [ERROR] [{done}/{total}] record_id={rid}  reason={result['error']}")
            else:
                tier = result.get("stability_tier", "?")
                D    = result.get("D", "?")
                print(f"  [{done}/{total}] scored record_id={rid}  D={D}  tier={tier}")

            results.append(result)

    return results


# ── CSV export ───────────────────────────────────────────────────────────────────

def export_csv(jsonl_path: Path, csv_path: Path) -> None:
    """
    Read a scored JSONL file and write a flat CSV.

    Each row contains metadata, c1–c10 scores as individual columns,
    summary metrics (D, D_norm, stability_tier), and text fields.
    """
    rows: list[dict] = []

    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue

        rec    = json.loads(line)
        scores = rec.get("constraint_scores") or {}

        row: dict = {f: rec.get(f, "") for f in _CSV_FIELDNAMES}
        for key in CONSTRAINT_KEYS:
            row[key] = scores.get(key, "")

        rows.append(row)

    if not rows:
        print("  [CSV] No rows to export.")
        return

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  [CSV] Written: {csv_path}  ({len(rows)} rows)")
