"""
aosl_content_stability_auditor.py  (05_SRC/apps/)

AOSL Content Stability Auditor v0.2 — Streamlit app.

Launch:
    streamlit run 05_SRC\\apps\\aosl_content_stability_auditor.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# sys.path — allow imports from 05_SRC and repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT  = _REPO_ROOT / "05_SRC"
for _p in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scoring.content_heuristic import (
    score_content,
    build_markdown_report,
    CONSTRAINT_CODES,
    CONSTRAINT_NAMES,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = _REPO_ROOT / "04_RUNS" / "content_stability_auditor"

_STATUS_ICON = {"PASS": "✓", "PARTIAL": "~", "FAIL": "✗"}

_TIER_COLOR = {
    "S3": "green",
    "S2": "blue",
    "S1": "orange",
    "S0": "red",
}

_READINESS_COLOR = {
    "High":   "green",
    "Medium": "orange",
    "Low":    "red",
}

_RISK_COLOR = {
    "Low":    "green",
    "Medium": "orange",
    "High":   "red",
}

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AOSL Content Stability Auditor v0.2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("AOSL Auditor v0.2")
    st.caption("AI Output Stability Layer — Content Edition")
    st.markdown("---")
    st.markdown(
        "**What this does**\n\n"
        "Scores your content against the AOSL C1–C10 structural constraints "
        "and estimates AI citation readiness and misinterpretation risk. "
        "v0.2 classifies claims by type and evidence expectation."
    )
    st.markdown("---")
    st.markdown(
        "**What this does not do**\n\n"
        "- Does not check factual accuracy\n"
        "- Does not guarantee AI citation or ranking\n"
        "- Does not replace human review\n"
        "- Uses local heuristics only (no API call)"
    )
    st.markdown("---")
    st.markdown(
        "**Scorer:** `heuristic-v2`  \n"
        "**Version:** v0.2 prototype  \n"
        "**Status:** local research tool"
    )

# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------
st.title("AOSL Content Stability Auditor v0.2")
st.caption(
    "Paste content below to score it against the AOSL C1–C10 structural constraints. "
    "v0.2 classifies claims by type and evidence expectation. "
    "No API key required. Results are estimates, not guarantees."
)
st.markdown("---")

# --- Input form ---
with st.form("audit_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        page_title = st.text_input(
            "Content title or headline",
            placeholder="e.g. Why AI Search Is Changing Content Strategy",
        )
    with col2:
        source_url = st.text_input(
            "Source URL (optional)",
            placeholder="https://example.com/article",
        )

    content_text = st.text_area(
        "Paste content here",
        height=280,
        placeholder=(
            "Paste the full text of the page, article, landing page, or AI output "
            "you want to audit..."
        ),
    )

    reviewer_notes = st.text_input(
        "Notes or context (optional)",
        placeholder="e.g. Product landing page targeting enterprise buyers",
    )

    submitted = st.form_submit_button("Run AOSL Audit", type="primary")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if submitted:
    if not content_text.strip():
        st.error("Please paste content before running the audit.")
        st.stop()

    with st.spinner("Running AOSL structural audit..."):
        audit = score_content(
            content=content_text,
            title=page_title,
            url=source_url,
            notes=reviewer_notes,
        )

    st.markdown("---")

    # ── A. Summary card ─────────────────────────────────────────────────────
    st.subheader("Summary")

    met1, met2, met3, met4, met5 = st.columns(5)
    with met1:
        st.metric("Stability Score", f"{audit['stability_score']} / 100")
    with met2:
        st.metric("Divergence D", f"{audit['divergence_raw']:.2f}")
    with met3:
        tier_label = f"{audit['stability_tier']} — {audit['stability_tier_label']}"
        st.metric("Stability Tier", tier_label)
    with met4:
        st.metric("AI Citation Readiness", audit["ai_citation_readiness"])
    with met5:
        st.metric("AI Misinterpretation Risk", audit["ai_misinterpretation_risk"])

    # Tier interpretation
    _TIER_INTERP = {
        "S3": "Structurally stable. Key claims appear grounded and uncertainty is acknowledged.",
        "S2": "Usable with weaknesses. Addressing flagged constraints would improve reliability.",
        "S1": "Significant structural gaps. Multiple constraints failing — misinterpretation risk is elevated.",
        "S0": "Structurally unstable. Major revision needed before AI-facing use.",
    }
    tier_color = _TIER_COLOR.get(audit["stability_tier"], "gray")
    st.markdown(
        f":{tier_color}[**{audit['stability_tier']}:** {_TIER_INTERP.get(audit['stability_tier'], '')}]"
    )

    st.markdown("---")

    # ── B. C1–C10 score table ───────────────────────────────────────────────
    st.subheader("C1–C10 Constraint Scores")

    for d in audit["constraint_details"]:
        icon  = _STATUS_ICON.get(d["status"], "?")
        color = "green" if d["status"] == "PASS" else ("orange" if d["status"] == "PARTIAL" else "red")
        with st.expander(
            f":{color}[{icon}]  **{d['code'].upper()} — {d['name']}**   "
            f"Score: {d['score']:.1f}  ({d['status']})"
        ):
            st.write(d["explanation"])

    st.markdown("---")

    # ── C. Claim Analysis (new in v0.2) ──────────────────────────────────────
    claim_analysis = audit.get("claim_analysis", [])
    if claim_analysis:
        st.subheader("Claim Analysis")
        st.caption(
            "Sentences classified as elevated-expectation or flagged claims. "
            "Disclaimer sentences and heading-like phrases are excluded."
        )
        _EXP_COLOR = {"VERY HIGH": "red", "HIGH": "orange", "MEDIUM": "blue", "LOW": "gray"}
        for c in claim_analysis:
            color = _EXP_COLOR.get(c["evidence_expectation"], "gray")
            with st.expander(
                f":{color}[**{c['evidence_expectation']}**]  {c['type']}  —  "
                f"{c['text'][:70]}{'...' if len(c['text']) > 70 else ''}"
            ):
                st.write(f"**Full sentence:** {c['text']}")
                if c.get("risk_reason"):
                    st.warning(c["risk_reason"])
        st.markdown("---")

    # ── D. Risky claims ──────────────────────────────────────────────────────
    st.subheader("Risky Claims")
    if audit.get("risky_claims"):
        st.caption(
            "Sentences detected as potentially unsupported, overconfident, "
            "vague, or causally weak. Disclaimer sentences are filtered out."
        )
        for claim in audit["risky_claims"]:
            st.markdown(f"> {claim}")
    else:
        st.info("No high-risk sentences detected by the heuristic.")

    st.markdown("---")

    # ── E. Missing evidence ─────────────────────────────────────────────────
    st.subheader("Missing Evidence")
    if audit.get("missing_evidence"):
        st.caption("What is absent that would strengthen this content.")
        for item in audit["missing_evidence"]:
            st.markdown(f"- {item}")
    else:
        st.success("No obvious evidence gaps detected.")

    st.markdown("---")

    # ── F. Recommended fixes + AI-readable improvements ─────────────────────
    st.subheader("Recommended Fixes")
    if audit.get("recommended_fixes"):
        for fix in audit["recommended_fixes"]:
            st.markdown(f"- {fix}")
    else:
        st.success("No structural fixes required.")

    st.subheader("AI-Readable Improvements")
    st.caption(
        "General improvements that increase the likelihood of accurate AI "
        "summarization and citation, regardless of current score."
    )
    for item in audit.get("ai_readable_improvements", []):
        st.markdown(f"- {item}")

    st.markdown("---")

    # ── G. Export ───────────────────────────────────────────────────────────
    st.subheader("Export Report")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = (page_title or "audit")[:40].replace(" ", "_").replace("/", "-")
    stem = f"content_audit_{ts}_{slug}"

    md_content   = build_markdown_report(audit)
    json_payload = {k: v for k, v in audit.items() if k != "ai_readable_improvements"}
    json_content = json.dumps(json_payload, indent=2, ensure_ascii=False)

    # Save to disk automatically
    md_path   = OUTPUT_DIR / f"{stem}.md"
    json_path = OUTPUT_DIR / f"{stem}.json"
    md_path.write_text(md_content,   encoding="utf-8")
    json_path.write_text(json_content, encoding="utf-8")

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="Download Markdown Report",
            data=md_content,
            file_name=f"{stem}.md",
            mime="text/markdown",
        )
    with col_dl2:
        st.download_button(
            label="Download JSON Report",
            data=json_content,
            file_name=f"{stem}.json",
            mime="application/json",
        )

    st.caption(
        f"Reports also saved to:  \n"
        f"`{md_path.relative_to(_REPO_ROOT)}`  \n"
        f"`{json_path.relative_to(_REPO_ROOT)}`"
    )

    st.markdown("---")
    st.caption(
        "**Disclaimer:** This is an early prototype using keyword heuristics (heuristic-v2). "
        "Claim classification is heuristic-based and may misclassify edge cases. "
        "Results are estimates only. They do not prove AI platforms will cite, "
        "recommend, or rank this content. Human review is required before taking action."
    )
