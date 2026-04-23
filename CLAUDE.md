# CLAUDE.md

## Project Identity
This repository is for AOSL implementation work.

AOSL = AI Output Stability Layer.

## Core Rules
- Prioritize structural integrity over persuasive fluency.
- Preserve canonical terminology.
- Do not silently rename core terms, metrics, constraint codes, schema fields, or scoring concepts.
- Keep changes small, safe, and explicit.
- Show full file contents before finishing when creating or editing code.
- Prefer beginner-friendly implementations.

## Canonical Constraint Set
- c1 = Factual Grounding
- c2 = Logical Coherence
- c3 = Causal Integrity
- c4 = Epistemic Calibration
- c5 = Scope Discipline
- c6 = Safety Integrity
- c7 = Uncertainty Acknowledgment
- c8 = Quantitative Accuracy
- c9 = Evidence Traceability
- c10 = Constraint Interaction Consistency

## Package Rule
The `AOSL` Python package lives at repo root.
Do not move it without explicit instruction.

Install from repo root with:
`py -m pip install -e .`

## Workflow Rules
- Use existing helpers before creating new ones.
- Do not invent complex architecture unless explicitly requested.
- Prefer one small useful module or script at a time.
- Keep build, validation, serialization, and analysis concerns clearly separated.
- Do not add evaluator logic or divergence logic unless explicitly requested.

## Environment Rules
- Windows-first instructions only.
- Use PowerShell command examples.
- Prefer full-file replacements over patch fragments when editing code.

## Repo Structure Intent
- `AOSL/` = package code
- `05_SRC/scripts/` = runnable demo/workflow scripts
- `05_SRC/analysis/` = analysis scripts
- `09_TEMP/` = temporary outputs
- `10_MEMORY/` = durable project context and progress

## Response Mode
Default to execution mode:
- step-by-step
- practical
- minimal theory
- small safe batches
