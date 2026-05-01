# AOSL Demo v0.1 Usage Note

## Metadata

| Field      | Value                                                          |
|------------|----------------------------------------------------------------|
| Date       | 2026-04-30                                                     |
| Project    | AI Output Stability Layer                                      |
| Framework  | Appearance Stability Framework                                 |
| App file   | `05_SRC\apps\aosl_demo_v0_1.py`                               |
| Status     | Early research prototype — not production-ready                |

---

## What the Demo Does

AOSL Demo v0.1 is a local Streamlit app for testing the AOSL scoring pipeline against real AI outputs.

It lets you:

- **Score a single AI output** — paste a prompt and output, select a judge model, and see a D score, stability score, stability tier, and C1–C10 constraint breakdown
- **Batch score a CSV** — upload a CSV of AI outputs, run them through the judge in sequence, and download scored results as CSV or Markdown
- **Inspect constraint scores** — see which of the ten AOSL constraints (C1–C10) fired on an output and how strongly
- **View the current evidence ladder** — compare the five archived baseline run levels (DeepSeek stable → synthetic flawed)
- **Read caveats** — understand what the scores mean and what has not yet been validated

The demo calls the OpenRouter API for judge scoring. No data is stored locally beyond the current browser session.

---

## How to Launch

Open PowerShell and run from the repo root:

```powershell
cd "C:\Users\ZBOOK\Desktop\AOSL - ENGINE"
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
py -m streamlit run 05_SRC\apps\aosl_demo_v0_1.py
```

Streamlit will open a browser tab automatically (default: `http://localhost:8501`).

**Alternative — use the launch script:**

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
py 05_SRC\scripts\run_aosl_demo_v0_1.py
```

The launch script is a thin wrapper around the same `streamlit run` command.

**Note:** the API key must be set in the same PowerShell session before launching. If the key is missing, all scoring buttons are disabled and the app shows a warning.

---

## Single-Output Scoring Workflow

1. Open the **Score Output** tab (first tab, default view)
2. Paste the **prompt** that was sent to the AI model
3. Paste the **AI output** to evaluate
4. Optionally paste any **source / context** that the output was supposed to draw from
5. Select a **judge model** (`deepseek/deepseek-chat` is the validated default)
6. Click **Score Output**

Results appear in the right panel:

| Result field       | What it means                                                               |
|--------------------|-----------------------------------------------------------------------------|
| **D score**        | Divergence score — fraction of constraint violations (0.0 = none, 1.0 = all) |
| **Stability score**| `1 − D` — fraction of constraints passed                                    |
| **Stability tier** | S0 (stable) → S3 (unstable), based on D thresholds                          |
| **C1–C10 table**   | Per-constraint score: 1.0 = pass, 0.5 = partial, 0.0 = fail                |
| **Weakest constraints** | The two or three constraints with the lowest scores on this output     |
| **Judge notes**    | Raw reasoning from the judge model (expandable)                              |

---

## Batch Scoring Workflow

### 1. Prepare a CSV

**Required columns** (exact names or close variants — see normalization note below):

| Column       | Description                        |
|--------------|------------------------------------|
| `prompt_id`  | Unique identifier for the row      |
| `prompt_text`| The prompt sent to the AI model    |
| `output_text`| The AI-generated output to score   |

**Optional columns:**

| Column                   | Description                                         |
|--------------------------|-----------------------------------------------------|
| `model_name`             | Name of the generator model                         |
| `expected_failure_focus` | Expected constraint failure label (e.g. `c7_missing_uncertainty`) |
| `temperature`            | Sampling temperature used                           |
| `repeat`                 | Repeat number if scoring multiple runs              |

A CSV template is available inside the **CSV format** expander in the Batch Score tab.

### 2. Header normalization

The app normalizes uploaded CSV column headers before validation. It handles:

- UTF-8 BOM (`﻿prompt_id` → `prompt_id`)
- Leading/trailing whitespace
- Uppercase or mixed case (`Prompt_ID` → `prompt_id`)
- Spaces in header names (`prompt id` → `prompt_id`)
- Hyphens in header names (`prompt-id` → `prompt_id`)

If required columns are still missing after normalization, the app shows the required columns, the detected normalized columns, and a correction hint.

### 3. Run batch scoring

1. Open the **Batch Score** tab
2. Upload your CSV using the file uploader
3. Review the 5-row preview to confirm columns parsed correctly
4. Set controls:
   - **Judge model** — choose the judge (default: `deepseek/deepseek-chat`)
   - **Limit rows** — set to 0 to score all rows, or a smaller number to test a subset
   - **max_tokens** — judge response length limit (default: 300)
   - **timeout (s)** — per-row API timeout in seconds (default: 60)
5. Click **Run Batch**

A progress bar tracks scoring row by row. When complete, the results panel shows:

- Mean D, Std D, Max D, and error count
- Constraint mean scores across all scored rows (C1–C10)
- Weakest constraints at the batch level
- Row-level results table

### 4. Download results

After scoring, two download buttons appear and remain available for the rest of the session:

- **Download scored CSV** — all rows with D score, stability score, tier, and C1–C10 columns
- **Download Markdown summary** — a formatted report with divergence summary, constraint means table, and row-level results

Both buttons survive a single click without disappearing (results are held in session state).

---

## Output Interpretation

| D range      | Suggested interpretation                                               |
|--------------|------------------------------------------------------------------------|
| < 0.10       | Low detected structural divergence — output appears well-formed        |
| 0.10 – 0.19  | Review recommended — one or more constraints may have fired            |
| ≥ 0.20       | Structural instability detected — human review recommended             |

**Important caveats on interpretation:**

- C1–C10 constraint scores are diagnostic aids, not ground truth labels. Do not treat a single constraint firing as a confirmed factual error.
- Aggregate D is more reliable than exact constraint attribution. Attribution match rates across validation runs have been below the 0.60 threshold target.
- All scores are judge-dependent. The validated judge is `deepseek/deepseek-chat`. The `google/gemini-2.0-flash-001` option is exploratory and has not been independently validated.

---

## Current Evidence Ladder

From archived validation baselines (all runs: deepseek/deepseek-chat judge, cheap mode):

```
DeepSeek stable  <  Llama stable  <  Llama pressured  <  DeepSeek pressured  <  Synthetic flawed
    0.0117       <     0.0250     <      0.0722        <       0.0939         <      0.2050
```

| Level | Label               | Dataset                    | Generator                          | Mean D |
|-------|---------------------|----------------------------|------------------------------------|--------|
| 1     | DeepSeek stable     | real_model_validation_30   | deepseek/deepseek-chat             | 0.0117 |
| 2     | Llama stable        | real_model_validation_30   | meta-llama/llama-3.1-8b-instruct   | 0.0250 |
| 3     | Llama pressured     | real_failure_validation_30 | meta-llama/llama-3.1-8b-instruct   | 0.0722 |
| 4     | DeepSeek pressured  | real_failure_validation_30 | deepseek/deepseek-chat             | 0.0939 |
| 5     | Synthetic flawed    | validation_30              | synthetic hand-crafted             | 0.2050 |

The full ladder is also visible inside the **Evidence Ladder** tab of the demo.

---

## Caveats

- **Not a truth detector.** AOSL detects structural divergence patterns, not factual correctness. An output can score low D and still be factually wrong.
- **Judge-dependent.** All current results use `deepseek/deepseek-chat` as judge. Scores from other judges may differ. Cross-judge independence has not yet been tested at scale.
- **Cross-judge evidence is still exploratory.** `google/gemini-2.0-flash-001` is available in the demo as an option but is not yet a validated second judge for AOSL purposes.
- **Attribution remains weak.** Constraint-level scores (which specific C fired) should not yet be used for constraint-specific diagnostics. Use aggregate D as the primary signal.
- **Prompt sets are purpose-built.** Validation runs used prompts designed to invite structural failures. Detection on naturalistic, unstructured real-world prompts remains untested.
- **Not for high-stakes decisions without human review.** AOSL output is a screening signal, not a decision. Always apply human judgment before acting on scoring results.
- **Not production-ready.** This is an early research prototype running locally. It has no authentication, no rate limiting, no persistent storage, and no error recovery beyond single-row retry.

---

## Suggested Next Improvements

The following improvements would increase demo utility for founders, reviewers, and collaborators:

1. **Add example input buttons** — pre-fill the Score Output tab with a stable example and a pressured example so reviewers can see the contrast without needing their own prompts
2. **Add better report formatting** — the Markdown summary is functional but plain; a styled HTML export would be more presentable
3. **Add a cross-judge comparison view** — score the same output with two judges side by side and show the delta to make judge dependence visible
4. **Add demo screenshots** — static PNG captures of a stable run and a pressured run, placed in `07_DOCS\` or a `screenshots\` subfolder
5. **Package a small sample CSV** — place a 5–10 row example CSV in `03_DATA\` or `09_TEMP\` so reviewers can test batch scoring immediately without preparing their own file
6. **Add a short public README section** — a 3–5 paragraph section in the repo README explaining what AOSL is, what the demo does, and how to run it

---

```
Version : v0.1
Status  : early research prototype — not production-ready
Scope   : local Streamlit demo, single-session, no persistence
Created : 2026-04-30
Updated : 2026-04-30
```
