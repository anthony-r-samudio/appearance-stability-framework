import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Add 05_SRC to sys.path so we can import from the api/ package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.openrouter_client import generate_response
from api.openrouter_client import score_output as judge_output
from api.model_registry import FREE_GENERATOR_MODELS, FREE_JUDGE_MODELS

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR  = REPO_ROOT / "04_RUNS" / "openrouter_demo"
OUTPUT_FILE = OUTPUT_DIR / "openrouter_temperature_sweep_3x3x3.json"

GENERATOR_MODEL = FREE_GENERATOR_MODELS[0]
JUDGE_MODEL     = FREE_JUDGE_MODELS[0]

RETRY_WAIT_SECONDS = 20

CONSTRAINT_KEYS = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"]
VALID_SCORES    = {0, 0.5, 1}

TEMPERATURES = [0.3, 0.6, 0.9]
REPEATS      = 3

PROMPTS = [
    {
        "prompt_id": "p1_factual",
        "text": "Explain why vaccines are effective at preventing infectious diseases.",
    },
    {
        "prompt_id": "p2_causal",
        "text": "Does correlation imply causation? Explain with an example.",
    },
    {
        "prompt_id": "p3_uncertainty",
        "text": (
            "What are the limitations of current AI systems? "
            "Be precise and acknowledge uncertainty."
        ),
    },
]

# Scoring template uses double-braces for literal braces in the JSON example.
SCORING_PROMPT_TEMPLATE = """\
You are an AOSL (AI Output Stability Layer) judge evaluating an AI-generated response.

Score the following output against each constraint. Use only these values: 0, 0.5, or 1.
  0   = constraint violated or absent
  0.5 = constraint partially met
  1   = constraint fully satisfied

Constraints:
  c1:  Factual Grounding
  c2:  Logical Coherence
  c3:  Causal Integrity
  c4:  Epistemic Calibration
  c5:  Scope Discipline
  c6:  Safety Integrity
  c7:  Uncertainty Acknowledgment
  c8:  Quantitative Accuracy
  c9:  Evidence Traceability
  c10: Constraint Interaction Consistency

PROMPT given to the AI:
{prompt_text}

OUTPUT produced by the AI:
{output_text}

Return ONLY valid JSON. No explanation. No text outside the JSON object.
Required format:
{{
  "c1": 0,
  "c2": 0,
  "c3": 0,
  "c4": 0,
  "c5": 0,
  "c6": 0,
  "c7": 0,
  "c8": 0,
  "c9": 0,
  "c10": 0,
  "notes": ""
}}"""


def build_scoring_prompt(prompt_text: str, output_text: str) -> str:
    return SCORING_PROMPT_TEMPLATE.format(
        prompt_text=prompt_text,
        output_text=output_text,
    )


def extract_json_from_text(text: str) -> dict:
    """Parse a JSON object from text. Handles ```json code fences and plain JSON."""
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


def calculate_divergence(score_dict: dict) -> float | None:
    """
    D = sum(1 - c_i) for c1..c10.
    Returns None if any constraint key is missing or has an invalid score value.
    Valid values are 0, 0.5, or 1.
    """
    total = 0.0
    for key in CONSTRAINT_KEYS:
        if key not in score_dict:
            return None
        val = score_dict[key]
        if float(val) not in VALID_SCORES:
            return None
        total += 1.0 - float(val)
    return total


def call_with_retry(fn, *args, **kwargs) -> str:
    """Call fn(*args, **kwargs). On 429, wait RETRY_WAIT_SECONDS and retry once."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        if "429" in str(e):
            print(f"    429 rate limit hit. Waiting {RETRY_WAIT_SECONDS}s before retry...")
            time.sleep(RETRY_WAIT_SECONDS)
            try:
                return fn(*args, **kwargs)
            except Exception as e2:
                raise e2
        raise


def avg(values: list[float]) -> str:
    """Return formatted average or 'N/A' for an empty list."""
    if not values:
        return "N/A"
    return f"{sum(values) / len(values):.4f}"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_runs = len(PROMPTS) * len(TEMPERATURES) * REPEATS

    print("=" * 60)
    print("AOSL OpenRouter — Repeated Temperature Sweep")
    print("=" * 60)
    print(f"Generator    : {GENERATOR_MODEL}")
    print(f"Judge        : {JUDGE_MODEL}")
    print(f"Prompts      : {len(PROMPTS)}")
    print(f"Temperatures : {TEMPERATURES}")
    print(f"Repeats      : {REPEATS}")
    print(f"Total runs   : {total_runs}")
    print("=" * 60)
    print()

    results = []
    run_num = 0

    for prompt in PROMPTS:
        prompt_id   = prompt["prompt_id"]
        prompt_text = prompt["text"]

        for temp in TEMPERATURES:
            for repeat in range(1, REPEATS + 1):
                run_num += 1
                print(f"[{run_num}/{total_runs}] {prompt_id}  temp={temp}  repeat={repeat}")

                print(f"  [GENERATE] temperature={temp}")
                try:
                    output_text = call_with_retry(
                        generate_response, GENERATOR_MODEL, prompt_text,
                        temperature=temp,
                    )
                    print(f"  Output : {output_text[:100].replace(chr(10), ' ')}...")
                except Exception as e:
                    print(f"  ERROR  : {e}")
                    output_text = f"[GENERATION ERROR: {e}]"

                print(f"  [JUDGE] temperature=0.0")
                try:
                    scoring_prompt = build_scoring_prompt(prompt_text, output_text)
                    raw_score_text = call_with_retry(
                        judge_output, JUDGE_MODEL, scoring_prompt,
                        temperature=0.0,
                    )
                    print(f"  Score  : {raw_score_text[:80].replace(chr(10), ' ')}...")
                except Exception as e:
                    print(f"  ERROR  : {e}")
                    raw_score_text = f"[JUDGE ERROR: {e}]"

                parsed_score = extract_json_from_text(raw_score_text)
                divergence_D = calculate_divergence(parsed_score)

                if parsed_score:
                    print(f"  Parsed : {parsed_score}")
                else:
                    print("  Parsed : (no valid JSON found)")

                if divergence_D is not None:
                    print(f"  D      : {divergence_D}")
                else:
                    print("  D      : (could not calculate — missing or invalid scores)")

                print()

                results.append({
                    "prompt_id":       prompt_id,
                    "prompt_text":     prompt_text,
                    "temperature":     temp,
                    "repeat":          repeat,
                    "generator_model": GENERATOR_MODEL,
                    "output_text":     output_text,
                    "judge_model":     JUDGE_MODEL,
                    "raw_score_text":  raw_score_text,
                    "parsed_score":    parsed_score,
                    "divergence_D":    divergence_D,
                    "timestamp_utc":   datetime.now(timezone.utc).isoformat(),
                })

    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # --- Summary ---
    all_D    = [r["divergence_D"] for r in results if r["divergence_D"] is not None]
    n_failed = sum(1 for r in results if r["divergence_D"] is None)

    by_temp:           defaultdict[float, list[float]] = defaultdict(list)
    by_prompt:         defaultdict[str,   list[float]] = defaultdict(list)
    by_prompt_x_temp:  defaultdict[tuple, list[float]] = defaultdict(list)

    for r in results:
        if r["divergence_D"] is not None:
            by_temp[r["temperature"]].append(r["divergence_D"])
            by_prompt[r["prompt_id"]].append(r["divergence_D"])
            by_prompt_x_temp[(r["prompt_id"], r["temperature"])].append(r["divergence_D"])

    print("=" * 60)
    print("BATCH SUMMARY")
    print("=" * 60)
    print(f"Total runs         : {len(results)}")
    print(f"Failed (D=None)    : {n_failed}")
    print(f"Avg divergence     : {avg(all_D)}")
    print()
    print("By temperature:")
    for temp in TEMPERATURES:
        print(f"  temp={temp}  avg D = {avg(by_temp[temp])}")
    print()
    print("By prompt:")
    for prompt in PROMPTS:
        pid = prompt["prompt_id"]
        print(f"  {pid:<20}  avg D = {avg(by_prompt[pid])}")
    print()
    print("By prompt × temperature:")
    for prompt in PROMPTS:
        pid = prompt["prompt_id"]
        for temp in TEMPERATURES:
            cell_D = by_prompt_x_temp[(pid, temp)]
            print(f"  {pid:<20}  temp={temp}  avg D = {avg(cell_D)}")
    print()
    print(f"Output file        : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
