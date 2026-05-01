# AOSL Engine

Working repository for AOSL implementation, pilots, scoring, analytics, and outputs.

---

## AOSL Demo v0.2 — AI Output Stability Checker

AOSL is an experimental review layer that flags when AI outputs are fluent but structurally weak, overconfident, unsupported, or unsafe to trust without review.

### What the demo does

- Score a single AI output against 10 structural constraints (C1–C10)
- Batch-score a CSV of AI outputs and download results
- Show per-constraint scores with PASS / PARTIAL / FAIL
- Generate a plain-English stability report explaining what is weak and why
- Recommend an action (use as-is, review, or escalate to human review)
- Generate a repair prompt — a copy-ready instruction for regenerating the output
- Download individual Markdown reports and batch CSV/Markdown summaries
- View the current evidence ladder comparing stable and pressured baseline runs

### How to launch (Windows PowerShell)

```powershell
cd "C:\Users\ZBOOK\Desktop\AOSL - ENGINE"
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
py -m streamlit run 05_SRC\apps\aosl_demo_v0_1.py
```

Requires an [OpenRouter](https://openrouter.ai) API key. Scoring uses `deepseek/deepseek-chat` as the default judge model.

### Sample CSV

A ready-to-use 5-row sample CSV is included:

```
03_DATA\sample_inputs\aosl_demo_sample_outputs.csv
```

It contains 2 stable outputs, 1 overconfident output, 1 causal-leap output, and 1 weak-evidence output. Upload it in the Batch Score tab to see the demo in action without preparing your own data.

### Current evidence ladder

From archived validation baselines (all runs: `deepseek/deepseek-chat` judge, cheap mode):

```
DeepSeek stable  <  Llama stable  <  Llama pressured  <  DeepSeek pressured  <  Synthetic flawed
    0.0117       <     0.0250     <      0.0722        <       0.0939         <      0.2050
```

D = average constraint violation rate. 0 means no violations detected. Both stable baselines score near zero. Both pressured baselines score meaningfully higher. The ordering is consistent with the AOSL detection hypothesis across two generator models.

### Caveats

- **Not a truth detector.** AOSL flags structural divergence patterns, not factual errors. An output can score low D and still be factually wrong.
- **Judge-dependent.** All results use `deepseek/deepseek-chat` as judge. Scores from other judges may differ.
- **Constraint attribution is still weak.** Per-constraint scores (which C fired) are diagnostic signals, not reliable labels. Use aggregate D as the primary signal.
- **Cross-judge evidence is exploratory.** A second judge has not yet confirmed the signal independently.
- **Not production-ready.** This is a local research prototype with no auth, rate limiting, or persistent storage.
- **Human review required for high-stakes use.** AOSL output is a screening signal, not a decision.

### Internal documentation

- [AOSL Demo v0.2 Usage Note](07_DOCS/AOSL_DEMO_V0_1_NOTE.md) — full usage guide with workflows and interpretation
- [Cross-Generator Validation Memo v0.1](07_DOCS/AOSL_CROSS_GENERATOR_VALIDATION_MEMO_v0.1.md) — evidence behind the five-level ladder

---

## Structure
- 00_CONFIG = config files
- 01_CANON = canonical definitions and locked project docs
- 02_PROMPTS = prompt sets and generators
- 03_DATA = raw, intermediate, scored, combined datasets
- 04_RUNS = run-specific artifacts
- 05_SRC = source code
- 06_OUTPUTS = figures, tables, reports, cost outputs
- 07_DOCS = working documentation
- 08_TESTS = tests and validation scripts
- 09_TEMP = temporary scratch outputs
- 10_MEMORY = project memory/reference notes
- 99_ARCHIVE = deprecated or retired material

## Rule
Do not move files or rename paths without checking imports and file references.