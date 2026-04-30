"""
aosl_demo_v0_1.py

AOSL Demo v0.1 — AI Output Stability Checker

Launch with:
    py -m streamlit run 05_SRC/apps/aosl_demo_v0_1.py
"""

import os
import sys
from pathlib import Path

import streamlit as st

# -- sys.path ------------------------------------------------------------------
# File lives at 05_SRC/apps/ — parents[2] is repo root, parents[1] is 05_SRC.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT  = _REPO_ROOT / "05_SRC"
for _p in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scoring.fast_batch_scorer import (
    CONSTRAINT_CODES,
    DEFAULT_JUDGE_MODEL,
    score_row_real_judge,
)

# -- Constants -----------------------------------------------------------------

CONSTRAINT_LABELS = {
    "c1":  "Factual Grounding",
    "c2":  "Logical Coherence",
    "c3":  "Causal Integrity",
    "c4":  "Epistemic Calibration",
    "c5":  "Scope Discipline",
    "c6":  "Safety Integrity",
    "c7":  "Uncertainty Acknowledgment",
    "c8":  "Quantitative Accuracy",
    "c9":  "Evidence Traceability",
    "c10": "Constraint Interaction Consistency",
}

JUDGE_OPTIONS = {
    "deepseek/deepseek-chat (default)":        "deepseek/deepseek-chat",
    "google/gemini-2.0-flash-001 (exploratory)": "google/gemini-2.0-flash-001",
}

EVIDENCE_LADDER = [
    ("DeepSeek stable",    "real_model_validation_30",   "deepseek/deepseek-chat",           0.0117, 1),
    ("Llama stable",       "real_model_validation_30",   "meta-llama/llama-3.1-8b-instruct", 0.0250, 1),
    ("Llama pressured",    "real_failure_validation_30", "meta-llama/llama-3.1-8b-instruct", 0.0722, 3),
    ("DeepSeek pressured", "real_failure_validation_30", "deepseek/deepseek-chat",           0.0939, 3),
    ("Synthetic flawed",   "validation_30",              "synthetic hand-crafted",           0.2050, 1),
]

_D_LOW    = 0.10
_D_MEDIUM = 0.20

# -- Page config ---------------------------------------------------------------

st.set_page_config(
    page_title="AOSL Demo v0.1 — AI Output Stability Checker",
    layout="wide",
)

st.title("AOSL Demo v0.1 — AI Output Stability Checker")
st.caption(
    "AI Output Stability Layer · Early research prototype · "
    "Not a truth detector · Local use only"
)

# -- Tabs ----------------------------------------------------------------------

tab_score, tab_ladder, tab_caveats = st.tabs(
    ["Score Output", "Evidence Ladder", "Caveats"]
)


# =============================================================================
# Tab 1 — Score Output
# =============================================================================

with tab_score:

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        st.warning(
            "**OPENROUTER_API_KEY is not set.**  \n"
            "Set it in PowerShell before launching:  \n"
            "```\n$env:OPENROUTER_API_KEY = 'sk-or-v1-...'\n```  \n"
            "Then re-run:  \n"
            "```\npy -m streamlit run 05_SRC/apps/aosl_demo_v0_1.py\n```"
        )

    col_in, col_out = st.columns([1, 1], gap="large")

    # ── Inputs ────────────────────────────────────────────────────────────────

    with col_in:
        st.subheader("Input")

        prompt_text = st.text_area(
            "Prompt",
            height=140,
            placeholder="Paste the prompt that was sent to the AI model.",
        )
        output_text = st.text_area(
            "AI Output",
            height=200,
            placeholder="Paste the AI-generated output to evaluate.",
        )
        source_text = st.text_area(
            "Source / Context (optional)",
            height=100,
            placeholder="Paste any reference source or context used to produce the output.",
        )

        judge_label = st.selectbox(
            "Judge model",
            options=list(JUDGE_OPTIONS.keys()),
        )
        judge_model = JUDGE_OPTIONS[judge_label]

        score_btn = st.button(
            "Score Output",
            type="primary",
            disabled=(not api_key),
        )
        if not api_key:
            st.caption("Scoring disabled — set OPENROUTER_API_KEY first.")

    # ── Results ───────────────────────────────────────────────────────────────

    with col_out:
        st.subheader("Results")

        if not score_btn:
            st.markdown(
                "<p style='color:#888; padding-top:1.5rem'>"
                "Results appear here after scoring."
                "</p>",
                unsafe_allow_html=True,
            )

        elif not output_text.strip():
            st.error("AI Output is required.")

        else:
            with st.spinner(f"Scoring with {judge_model} …"):
                row = {
                    "prompt_id":   "demo",
                    "prompt_text": prompt_text.strip(),
                    "output_text": output_text.strip(),
                    "model_name":  "user-input",
                    "temperature": "",
                    "repeat":      1,
                }
                result = score_row_real_judge(
                    row,
                    judge_model=judge_model,
                    timeout=60,
                    max_tokens=300,
                )

            # ── Error handling ────────────────────────────────────────────────

            if result.get("scorer_error"):
                err = str(result["scorer_error"])
                if result.get("scorer_credit_error"):
                    st.error(
                        "**Credit error (HTTP 402).** "
                        "OpenRouter rejected the request.  \n"
                        "Top up your OpenRouter balance and retry.  \n"
                        f"Detail: {err}"
                    )
                else:
                    st.error(f"**Scoring error:** {err}")

            else:
                # ── Extract results ───────────────────────────────────────────

                d_score    = float(result.get("divergence",      0.0))
                stab_score = float(result.get("stability_score", 1.0 - d_score))
                tier       = str(result.get("stability_tier", "—"))
                notes      = str(result.get("notes", ""))

                constraint_vals = {
                    code: result.get(code) for code in CONSTRAINT_CODES
                }

                # ── D score display ───────────────────────────────────────────

                if d_score < _D_LOW:
                    d_color = "#2e7d32"   # dark green
                    interp  = "Likely stable. No significant structural violations detected."
                elif d_score < _D_MEDIUM:
                    d_color = "#e65100"   # dark orange
                    interp  = "Review recommended. Structural concerns are present."
                else:
                    d_color = "#c62828"   # dark red
                    interp  = (
                        "Structurally unstable. Human review required before use."
                    )

                st.markdown(
                    f"<div style='font-size:3rem; font-weight:700; "
                    f"color:{d_color}; line-height:1.1; margin-bottom:0.2rem'>"
                    f"D = {d_score:.4f}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"**Stability score:** {stab_score:.4f}"
                    f" &nbsp;|&nbsp; **Tier:** {tier}"
                    f" &nbsp;|&nbsp; **Judge:** `{judge_model}`"
                )
                st.info(f"**Interpretation:** {interp}")
                st.caption(
                    "D = average constraint violation rate (0 = no violations, "
                    "1 = all violated). Does not detect factual truth."
                )

                st.divider()

                # ── C1–C10 table ──────────────────────────────────────────────

                st.markdown("**C1–C10 Constraint Scores**")

                table_rows = []
                for code in CONSTRAINT_CODES:
                    val = constraint_vals.get(code)
                    label = CONSTRAINT_LABELS.get(code, code)
                    if val is None:
                        score_str = "—"
                        status    = "—"
                    else:
                        v = float(val)
                        score_str = f"{v:.1f}"
                        if v == 0.0:
                            status = "FAIL"
                        elif v == 0.5:
                            status = "PARTIAL"
                        else:
                            status = "pass"
                    table_rows.append({
                        "Code":       code,
                        "Constraint": label,
                        "Score":      score_str,
                        "Status":     status,
                    })

                st.table(table_rows)

                # ── Weakest constraints ───────────────────────────────────────

                scored_pairs = [
                    (code, float(constraint_vals[code]))
                    for code in CONSTRAINT_CODES
                    if constraint_vals.get(code) is not None
                ]
                scored_pairs.sort(key=lambda x: x[1])
                weakest = [p for p in scored_pairs if p[1] < 1.0]

                if weakest:
                    st.markdown("**Weakest constraints:**")
                    for code, val in weakest[:3]:
                        label = CONSTRAINT_LABELS.get(code, code)
                        st.markdown(f"- **{code}** {label} — {val:.1f}")
                else:
                    st.success("All constraints passed (D = 0).")

                # ── Judge notes ───────────────────────────────────────────────

                if notes:
                    with st.expander("Judge notes"):
                        st.write(notes)


# =============================================================================
# Tab 2 — Evidence Ladder
# =============================================================================

with tab_ladder:
    st.subheader("AOSL Evidence Ladder")
    st.markdown(
        "Archived baselines from AOSL validation runs. "
        "All scored with deepseek/deepseek-chat as judge."
    )

    ladder_rows = [
        {
            "Level":     label,
            "Dataset":   dataset,
            "Generator": generator,
            "Mean D":    f"{mean_d:.4f}",
            "Repeats":   repeats,
        }
        for label, dataset, generator, mean_d, repeats in EVIDENCE_LADDER
    ]
    st.table(ladder_rows)

    st.markdown(
        """
**Ordering:**
```
DS stable  <  Llama stable  <  Llama pressured  <  DS pressured  <  Synthetic flawed
  0.0117   <    0.0250      <      0.0722        <    0.0939      <      0.2050
```
"""
    )

    st.markdown(
        """
**Key gaps:**

| Comparison | Gap |
|---|---|
| Llama stable − DeepSeek stable | +0.0133 |
| Llama pressured − Llama stable (own floor) | +0.0472 (~2.9×) |
| DeepSeek pressured − DeepSeek stable (own floor) | +0.0822 (~8.0×) |
| Synthetic flawed − DeepSeek pressured | +0.1111 |
"""
    )

    st.caption(
        "Source: 04_RUNS/real_model_validation_30/ and "
        "04_RUNS/real_failure_validation_30/valid_baselines/ — "
        "see 07_DOCS/AOSL_CROSS_GENERATOR_VALIDATION_MEMO_v0.1.md for full analysis."
    )


# =============================================================================
# Tab 3 — Caveats
# =============================================================================

with tab_caveats:
    st.subheader("Important Caveats")
    st.markdown(
        """
**This tool is an early research prototype. Read before use.**

---

**Not a truth detector.**
AOSL measures structural consistency across 10 stability constraints.
It does not verify facts, detect hallucinations directly, or determine whether an
AI output is correct. A high stability score does not mean the output is true.

---

**Judge-dependent.**
All AOSL scores depend on the judge model. A different judge may assign different
constraint scores for the same output. Cross-judge consistency has been tested only
at an exploratory level.

---

**Constraint attribution is weak.**
The judge identifies *which* constraints are violated, but attribution match rates
in validation runs are below the 0.60 reliability threshold. Use the aggregate D
score as the primary signal, not individual constraint breakdowns.

---

**Cross-judge evidence is exploratory.**
Second-judge runs (google/gemini-2.0-flash-001) have been run on a limited prompt
set. Results are preliminary and should not be treated as strong validation.

---

**Purpose-built prompt sets.**
The evidence ladder baselines were generated from structured validation prompt sets
designed to embed or avoid structural failure patterns. Performance on naturalistic
real-world prompts remains untested at scale.

---

**Human review required for high-stakes use.**
This tool is intended for research and exploratory use only. Do not use AOSL scores
as the sole basis for any consequential decision. Always apply human judgment.

---
"""
    )
    st.caption(
        "AOSL Demo v0.1 · AI Output Stability Layer · "
        "Early research prototype · Not production-ready"
    )
