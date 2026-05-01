"""
aosl_demo_v0_1.py

AOSL Demo v0.1 — AI Output Stability Checker

Launch with:
    py -m streamlit run 05_SRC/apps/aosl_demo_v0_1.py
"""

import csv
import datetime
import io
import os
import statistics
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
    "deepseek/deepseek-chat (default)":          "deepseek/deepseek-chat",
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

_BATCH_CSV_REQUIRED = {"prompt_id", "prompt_text", "output_text"}
_BATCH_CSV_OPTIONAL = {"model_name", "expected_failure_focus", "temperature", "repeat"}

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

tab_score, tab_batch, tab_ladder, tab_caveats = st.tabs(
    ["Score Output", "Batch Score", "Evidence Ladder", "Caveats"]
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
                    d_color = "#2e7d32"
                    interp  = "Likely stable. No significant structural violations detected."
                elif d_score < _D_MEDIUM:
                    d_color = "#e65100"
                    interp  = "Review recommended. Structural concerns are present."
                else:
                    d_color = "#c62828"
                    interp  = "Structurally unstable. Human review required before use."

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
# Tab 2 — Batch Score
# =============================================================================

with tab_batch:
    st.subheader("Batch Score")
    st.markdown(
        "Upload a CSV of AI outputs to score in batch. "
        "Each row is scored independently. Results can be downloaded as CSV or Markdown."
    )

    api_key_b = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key_b:
        st.warning(
            "**OPENROUTER_API_KEY is not set.** "
            "Scoring will be disabled until the key is present."
        )

    # ── CSV template download ─────────────────────────────────────────────────

    with st.expander("CSV format — required and optional columns"):
        st.markdown(
            "**Required:** `prompt_id`, `prompt_text`, `output_text`  \n"
            "**Optional:** `model_name`, `expected_failure_focus`, `temperature`, `repeat`"
        )
        template_buf = io.StringIO()
        template_writer = csv.writer(template_buf)
        template_writer.writerow(
            ["prompt_id", "prompt_text", "output_text",
             "model_name", "expected_failure_focus", "temperature", "repeat"]
        )
        template_writer.writerow(
            ["ex-001", "What is the speed of light?",
             "The speed of light is 300,000 km/s.",
             "my-model", "c8_quantitative_error", "0.7", "1"]
        )
        st.download_button(
            "Download CSV template",
            data=template_buf.getvalue(),
            file_name="aosl_batch_template.csv",
            mime="text/csv",
        )

    # ── Upload ────────────────────────────────────────────────────────────────

    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded is None:
        st.info("Upload a CSV file to begin.")

    else:
        content = uploaded.read().decode("utf-8-sig", errors="replace")
        reader  = csv.DictReader(io.StringIO(content))
        raw_rows = list(reader)
        raw_fieldnames = reader.fieldnames or []

        # Normalize column names: strip BOM/whitespace, lowercase, spaces/hyphens→underscores
        def _norm(name: str) -> str:
            return name.strip().lstrip("﻿").lower().replace(" ", "_").replace("-", "_")

        col_map = {raw: _norm(raw) for raw in raw_fieldnames}
        all_rows = [{col_map.get(k, k): v for k, v in row.items()} for row in raw_rows]
        fieldnames = set(col_map.values())

        missing_cols = _BATCH_CSV_REQUIRED - fieldnames
        if missing_cols:
            st.error(
                f"CSV is missing required column(s): **{', '.join(sorted(missing_cols))}**  \n"
                f"Required: `prompt_id`, `prompt_text`, `output_text`  \n"
                f"Detected (after normalization): `{', '.join(sorted(fieldnames)) or 'none'}`  \n"
                "Check that your CSV has `prompt_id`, `prompt_text`, and `output_text` headers."
            )
        elif not all_rows:
            st.error("CSV has no data rows.")
        else:
            st.success(f"Loaded {len(all_rows)} row(s).")

            # Preview
            preview_cols = [c for c in ["prompt_id", "prompt_text", "output_text", "model_name"] if c in fieldnames]
            preview_rows = [{c: r.get(c, "") for c in preview_cols} for r in all_rows[:5]]
            st.markdown(f"**Preview** (first {min(5, len(all_rows))} rows):")
            st.dataframe(preview_rows, use_container_width=True)

            # ── Controls ─────────────────────────────────────────────────────

            st.divider()
            col_b1, col_b2, col_b3, col_b4 = st.columns(4)

            with col_b1:
                judge_label_b = st.selectbox(
                    "Judge model",
                    options=list(JUDGE_OPTIONS.keys()),
                    key="batch_judge",
                )
                judge_model_b = JUDGE_OPTIONS[judge_label_b]

            with col_b2:
                limit_b = st.number_input(
                    "Limit rows (0 = all)",
                    min_value=0,
                    max_value=len(all_rows),
                    value=0,
                    step=1,
                )

            with col_b3:
                max_tokens_b = st.number_input(
                    "max_tokens",
                    min_value=100,
                    max_value=800,
                    value=300,
                    step=50,
                )

            with col_b4:
                timeout_b = st.number_input(
                    "timeout (s)",
                    min_value=10,
                    max_value=120,
                    value=60,
                    step=10,
                )

            rows_to_score = all_rows if int(limit_b) == 0 else all_rows[:int(limit_b)]
            st.caption(
                f"{len(rows_to_score)} row(s) will be scored · "
                f"judge: {judge_model_b} · "
                f"max_tokens: {int(max_tokens_b)} · "
                f"timeout: {int(timeout_b)}s"
            )

            run_batch_btn = st.button(
                "Run Batch",
                type="primary",
                disabled=(not api_key_b),
            )
            if not api_key_b:
                st.caption("Scoring disabled — set OPENROUTER_API_KEY first.")

            # ── Scoring loop ─────────────────────────────────────────────────

            if run_batch_btn:
                total         = len(rows_to_score)
                progress_bar  = st.progress(0)
                status_text   = st.empty()
                scored_results = []

                for i, row in enumerate(rows_to_score):
                    pid = str(row.get("prompt_id", i + 1))
                    status_text.text(f"Scoring {i + 1}/{total}: {pid}")

                    result = score_row_real_judge(
                        row,
                        judge_model=judge_model_b,
                        timeout=int(timeout_b),
                        max_tokens=int(max_tokens_b),
                    )
                    scored_results.append(result)
                    progress_bar.progress((i + 1) / total)

                status_text.text(f"Done. {total} row(s) scored.")

                # ── Aggregate stats ───────────────────────────────────────────

                ok_rows  = [r for r in scored_results if not r.get("scorer_error")]
                err_rows = [r for r in scored_results if r.get("scorer_error")]

                d_vals = []
                for r in ok_rows:
                    raw = r.get("divergence")
                    if raw not in (None, ""):
                        try:
                            d_vals.append(float(raw))
                        except (ValueError, TypeError):
                            pass

                mean_d = statistics.mean(d_vals)                    if d_vals else None
                std_d  = statistics.stdev(d_vals)                   if len(d_vals) > 1 else None
                max_d  = max(d_vals)                                if d_vals else None

                st.divider()
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Mean D",  f"{mean_d:.4f}" if mean_d is not None else "—")
                m2.metric("Std D",   f"{std_d:.4f}"  if std_d  is not None else "—")
                m3.metric("Max D",   f"{max_d:.4f}"  if max_d  is not None else "—")
                m4.metric("Errors",  len(err_rows))

                # ── Constraint mean table ─────────────────────────────────────

                st.divider()
                st.markdown("**Mean Constraint Scores across scored rows (C1–C10)**")

                constraint_means = {}
                for code in CONSTRAINT_CODES:
                    vals = []
                    for r in ok_rows:
                        raw = r.get(code)
                        if raw not in (None, ""):
                            try:
                                vals.append(float(raw))
                            except (ValueError, TypeError):
                                pass
                    constraint_means[code] = statistics.mean(vals) if vals else None

                cmean_table = [
                    {
                        "Code":       code,
                        "Constraint": CONSTRAINT_LABELS.get(code, code),
                        "Mean Score": f"{constraint_means[code]:.4f}"
                                      if constraint_means[code] is not None else "—",
                    }
                    for code in CONSTRAINT_CODES
                ]
                st.table(cmean_table)

                ranked = [
                    (code, constraint_means[code])
                    for code in CONSTRAINT_CODES
                    if constraint_means.get(code) is not None and constraint_means[code] < 1.0
                ]
                ranked.sort(key=lambda x: x[1])
                if ranked:
                    st.markdown("**Weakest constraints (batch mean):**")
                    for code, val in ranked[:3]:
                        st.markdown(
                            f"- **{code}** {CONSTRAINT_LABELS.get(code, code)} "
                            f"— mean {val:.4f}"
                        )

                # ── Row-level results table ───────────────────────────────────

                st.divider()
                st.markdown("**Row-Level Results**")

                display_cols = (
                    ["prompt_id"]
                    + CONSTRAINT_CODES
                    + ["divergence", "stability_score", "stability_tier", "scorer_error"]
                )
                display_rows = []
                for r in scored_results:
                    dr = {}
                    for col in display_cols:
                        v = r.get(col, "")
                        dr[col] = "" if v is None else v
                    display_rows.append(dr)

                st.dataframe(display_rows, use_container_width=True)

                # ── Build downloads and persist in session_state ──────────────

                # Build ordered field list for CSV export
                _priority = (
                    ["prompt_id", "prompt_text", "output_text", "model_name",
                     "temperature", "repeat", "expected_failure_focus"]
                    + CONSTRAINT_CODES
                    + ["divergence", "stability_score", "stability_tier",
                       "notes", "scorer", "scorer_error", "scorer_credit_error"]
                )
                seen_keys: set = set()
                export_fields = []
                for k in _priority:
                    if k not in seen_keys:
                        export_fields.append(k)
                        seen_keys.add(k)
                for r in scored_results:
                    for k in r:
                        if k not in seen_keys:
                            export_fields.append(k)
                            seen_keys.add(k)

                csv_buf = io.StringIO()
                writer  = csv.DictWriter(
                    csv_buf, fieldnames=export_fields, extrasaction="ignore"
                )
                writer.writeheader()
                writer.writerows(scored_results)
                st.session_state["batch_csv"] = csv_buf.getvalue()

                # Build Markdown summary
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                md_buf = io.StringIO()
                md_buf.write("# AOSL Batch Score Report\n\n")
                md_buf.write(f"**Date:** {now_str}  \n")
                md_buf.write(f"**Judge:** {judge_model_b}  \n")
                md_buf.write(f"**Rows scored:** {total}  \n")
                md_buf.write(f"**Errors:** {len(err_rows)}  \n\n")

                md_buf.write("## Divergence Summary\n\n")
                md_buf.write("| Metric | Value |\n|---|---|\n")
                md_buf.write(f"| Mean D | {mean_d:.4f} |\n" if mean_d is not None else "| Mean D | — |\n")
                md_buf.write(f"| Std D  | {std_d:.4f} |\n"  if std_d  is not None else "| Std D  | — |\n")
                md_buf.write(f"| Max D  | {max_d:.4f} |\n"  if max_d  is not None else "| Max D  | — |\n")
                md_buf.write(f"| Errors | {len(err_rows)} |\n\n")

                md_buf.write("## Constraint Means (C1–C10)\n\n")
                md_buf.write("| Code | Constraint | Mean Score |\n|---|---|---|\n")
                for code in CONSTRAINT_CODES:
                    val = constraint_means.get(code)
                    val_str = f"{val:.4f}" if val is not None else "—"
                    md_buf.write(f"| {code} | {CONSTRAINT_LABELS.get(code, code)} | {val_str} |\n")

                md_buf.write("\n## Row-Level Results\n\n")
                header_codes = " | ".join(CONSTRAINT_CODES)
                sep_codes    = " | ".join("---" for _ in CONSTRAINT_CODES)
                md_buf.write(f"| prompt_id | D | Tier | {header_codes} | Error |\n")
                md_buf.write(f"|---|---|---| {sep_codes} |---|\n")
                for r in scored_results:
                    pid_md   = str(r.get("prompt_id", ""))
                    raw_d    = r.get("divergence")
                    d_md     = f"{float(raw_d):.4f}" if raw_d not in (None, "") else "—"
                    tier_md  = str(r.get("stability_tier", ""))
                    codes_md = " | ".join(str(r.get(c, "")) for c in CONSTRAINT_CODES)
                    err_md   = str(r.get("scorer_error", ""))[:80] if r.get("scorer_error") else ""
                    md_buf.write(f"| {pid_md} | {d_md} | {tier_md} | {codes_md} | {err_md} |\n")

                md_buf.write(
                    "\n---\n"
                    "_Generated by AOSL Demo v0.1 — not a truth detector — "
                    "early research prototype_\n"
                )
                st.session_state["batch_md"] = md_buf.getvalue()

                # ── Error details ─────────────────────────────────────────────

                if err_rows:
                    with st.expander(f"Error details ({len(err_rows)} row(s))"):
                        for r in err_rows:
                            pid_e = r.get("prompt_id", "?")
                            err_e = r.get("scorer_error", "unknown error")
                            st.markdown(f"- **{pid_e}**: {err_e}")

            # ── Persistent downloads (survive download-button rerenders) ──────

            if "batch_csv" in st.session_state:
                st.divider()
                st.markdown("**Downloads**")
                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    st.download_button(
                        "Download scored CSV",
                        data=st.session_state["batch_csv"],
                        file_name="aosl_batch_scored.csv",
                        mime="text/csv",
                        key="dl_csv_persist",
                    )
                with dl_col2:
                    st.download_button(
                        "Download Markdown summary",
                        data=st.session_state["batch_md"],
                        file_name="aosl_batch_summary.md",
                        mime="text/markdown",
                        key="dl_md_persist",
                    )


# =============================================================================
# Tab 3 — Evidence Ladder
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
# Tab 4 — Caveats
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
