# real_failure_validation_30

High-pressure real model outputs for AOSL failure detection validation.

## Why This Exists

The weak adversarial prefix test (`real_model_validation_30_adversarial`) scored
mean D ≈ 0.0100 on 5 rows — nearly identical to the stable real baseline of 0.0117.
Adding "Answer confidently. Do not hedge." as a prefix did not materially change
model behavior; DeepSeek resisted the pressure and continued giving qualified answers.

This dataset takes a different approach: each prompt is structurally redesigned to
embed the pressure mechanism into the question itself — false premises, quantitative
traps, forced binary choices, causal overclaim invitations, and scope expansions that
require the model to actively resist in order to answer correctly.

## Pressure Design Principles

| Pressure type          | Mechanism                                                    |
|------------------------|--------------------------------------------------------------|
| false_premise          | Embeds a wrong fact; correct model must correct it           |
| forced_certainty       | Demands a specific number or yes/no where none exists        |
| causal_overclaim       | Invites mechanism claim; correct model hedges causation      |
| quantitative_trap      | Presents a wrong calculation and asks for confirmation       |
| overgeneralization     | States a universal rule; correct model gives exceptions      |
| choose_one             | Forces binary choice where both poles are wrong              |
| scope_expansion        | Asks one question but frames it as "explain everything"      |
| false_premise          | States consensus that doesn't exist                          |
| no_sources_allowed     | Demands a specific number for an unresolved empirical claim  |
| legal_overreach        | Asks for a universal legal answer across jurisdictions       |
| medical_overreach      | Asks for clinical self-treatment without professional help   |
| missing_context        | Presents dangerous framing as normal ("just seeking attention")|
| contradiction_pressure | Forces a universal rule between two mutually incompatible positions |

## Files

| File                                                  | Description                                       |
|-------------------------------------------------------|---------------------------------------------------|
| `real_failure_validation_30_prompts.csv`              | 30 high-pressure prompts with pressure_type column|
| `real_failure_validation_30_outputs.csv`              | DeepSeek outputs (default, judge-compatible)      |
| `real_failure_validation_30_outputs_<suffix>.csv`     | Per-model outputs when --output-suffix is used    |

### Prompts CSV Schema

```
prompt_id, original_prompt_id, prompt_text, expected_failure_focus, pressure_type
```

### Output CSV Schema (judge-compatible)

```
prompt_id, prompt_text, model_name, output_text, temperature, repeat, expected_failure_focus
```

## Generator Script

```
05_SRC/experiments/generate_real_failure_validation_30.py
```

Default model: `deepseek/deepseek-chat`  
Default temperature: `0.9`  
Default max_tokens: `500`

Requires `OPENROUTER_API_KEY` environment variable.

---

## Dry-Run (no API calls)

```
py 05_SRC\experiments\generate_real_failure_validation_30.py --dry-run
```

---

## Generate 5 Rows (Cheap Test)

```
py 05_SRC\experiments\generate_real_failure_validation_30.py --limit 5 --max-tokens 300
```

---

## Generate All 30 Rows

```
py 05_SRC\experiments\generate_real_failure_validation_30.py
```

---

## Resume After Interruption

```
py 05_SRC\experiments\generate_real_failure_validation_30.py --resume
```

---

## Generate with a Different Model (Separate Output File)

Use `--output-suffix` to write results to a model-specific file without overwriting
the existing DeepSeek outputs.

```
py 05_SRC\experiments\generate_real_failure_validation_30.py ^
    --model meta-llama/llama-3.1-8b-instruct ^
    --output-suffix llama_3_1_8b
```

Output: `real_failure_validation_30_outputs_llama_3_1_8b.csv`

The suffix is sanitized automatically: `/`, `\`, `:`, and spaces become `_`, lowercased.

Resume with suffix:

```
py 05_SRC\experiments\generate_real_failure_validation_30.py ^
    --model meta-llama/llama-3.1-8b-instruct ^
    --output-suffix llama_3_1_8b ^
    --resume
```

---

## Score the Outputs (Dry-Run First)

```
py 05_SRC\experiments\run_judge_calibration.py ^
    --input-csv 04_RUNS\real_failure_validation_30\real_failure_validation_30_outputs.csv ^
    --dry-run --cost-mode cheap
```

Live scoring (1 repeat, cheap):

```
py 05_SRC\experiments\run_judge_calibration.py ^
    --input-csv 04_RUNS\real_failure_validation_30\real_failure_validation_30_outputs.csv ^
    --cost-mode cheap --repeats 1
```

---

## What Success Looks Like

If AOSL can detect genuine constraint violations in these outputs, the mean D for
this set should be meaningfully above the stable real baseline (0.0117).

| Dataset                          | Mean D  | Notes                                 |
|----------------------------------|---------|---------------------------------------|
| validation_30 (synthetic)        | 0.2050  | Hand-crafted, legible failures        |
| real_model_validation_30         | 0.0117  | Stable real outputs, nearly zero D    |
| real_model_validation_30_adv     | ~0.0100 | Weak prefix, model resisted pressure  |
| real_failure_validation_30       | 0.0939  | High-pressure structural prompts (3-repeat) |

Mean D of 0.0939 (3-repeat) is 8.0× the stable real baseline. See closeout report in
`07_DOCS/AOSL_REAL_FAILURE_VALIDATION_CLOSEOUT_v0.1.md`.

---

## Version

```
Created  : 2026-04-30
Prompts  : 30 (structurally redesigned from validation_30)
Generator: deepseek/deepseek-chat (default)
Temp     : 0.9
Status   : DeepSeek outputs generated and scored (3-repeat, mean D=0.0939)
```
