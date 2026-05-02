"""
content_heuristic.py  (05_SRC/scoring/)

Local deterministic heuristic scorer for AOSL Content Stability Audits.
No API key required. v0.1 prototype — transparent and conservative.

Scores content text against AOSL C1-C10 constraints using keyword/pattern
heuristics. Not a substitute for real-judge scoring.

Public interface
----------------
    audit = score_content(content, title="", url="", notes="")
    md    = build_markdown_report(audit)
"""

import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Canonical constraint definitions
# ---------------------------------------------------------------------------

CONSTRAINT_CODES = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"]
CONSTRAINT_NAMES = {
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

# Tier thresholds (based on stability_score = (1 - D/10) * 100)
_TIERS = [
    (90.0, "S3", "Strong"),
    (70.0, "S2", "Usable"),
    (50.0, "S1", "Weak"),
    (0.0,  "S0", "Unstable"),
]

# ---------------------------------------------------------------------------
# Heuristic pattern lists
# ---------------------------------------------------------------------------

_SOURCE_MARKERS = [
    "according to", "research shows", "study shows", "studies show",
    "data shows", "data indicates", "evidence shows", "research suggests",
    "findings show", "report found", "survey found", "researchers found",
    "published in", "journal of", "university of", "per ", "source:",
    "cited in", "reference:", "reported by", "http://", "https://",
]

_CAUSAL_MARKERS = [
    "because ", "therefore ", "thus ", "hence ", "leads to", "lead to",
    "causes ", "cause ", "results in", "result in", "proves that",
    "demonstrates that", "shows that", "due to ", "as a result",
    "which means that", "this means ", "directly causes", "is the reason",
]

_ABSOLUTE_MARKERS = [
    "always ", "never ", "guarante",  # matches guarantee/guaranteed
    "undeniable", "undeniably", "definitively", "definitely ",
    "certainly ", "certainty ", "100%", "will always", "cannot fail",
    "no doubt", "without question", "there is no question",
    "the only ", "the best ", "the leading ", "is superior", "are superior",
    "best in class", "most powerful", "most advanced",
    "will disappear", "will fail", "will not survive",
]

_SCOPE_MARKERS = [
    "all companies", "all businesses", "every company", "every business",
    "anyone can ", "everyone can ", "universal solution", "for all industries",
    "across all ", "works for everyone", "applicable to all",
    "all users", "every user", "for any business", "for any organization",
    "no matter what", "for everyone", "all organizations",
]

_SAFETY_RISK_MARKERS = [
    "cures ", "cure ", "cured ", "heals ", "heal ", "treats ",
    "medical advice", "health advice", "legal advice",
    "financial advice", "investment advice",
    "guaranteed returns", "risk-free", "no risk investment",
    "guaranteed to work", "will definitely cure",
    "legally required", "you must legally",
    "safe investment", "100% safe", "no chance of loss",
]

_SAFETY_CAVEAT_MARKERS = [
    "consult a doctor", "consult a professional", "consult a physician",
    "not medical advice", "not legal advice", "not financial advice",
    "seek professional advice", "disclaimer", "results may vary",
    "past performance", "individual results may", "consult your",
]

_HEDGE_MARKERS = [
    "may ", "might ", "could ", "seems ", "appears to",
    "suggests ", "possibly ", "potentially ", "in some cases",
    "for some ", "research suggests", "evidence suggests",
    "it is possible", "likely ", "unlikely ", "generally ",
    "typically ", "often ", "sometimes ", "in many cases",
]

_FIX_MAP = {
    "c1":  "Add source attributions for key factual claims (e.g., 'According to [source]...').",
    "c2":  "Review content structure; remove or resolve contradictory statements.",
    "c3":  "Provide evidence or data to support causal claims ('X leads to Y').",
    "c4":  "Replace absolute language ('always', 'guaranteed') with qualified claims or add supporting evidence.",
    "c5":  "Narrow universal claims to specific audiences, contexts, or conditions.",
    "c6":  "Add appropriate disclaimers for medical, legal, or financial content.",
    "c7":  "Add hedging language ('may', 'research suggests') where claims are speculative.",
    "c8":  "Cite sources for all numerical statistics and percentages.",
    "c9":  "Add links, named sources, citations, or references to support assertions.",
    "c10": "Align claim confidence with available evidence throughout the content.",
}

_MISSING_EVIDENCE_MAP = {
    "c1": "Source attributions for factual assertions.",
    "c3": "Data or studies supporting causal claims.",
    "c4": "Evidence for absolute claims, or qualification language.",
    "c5": "Scope qualifiers (e.g., 'for most SMBs', 'in typical cases').",
    "c6": "Caveats or disclaimers for sensitive claims.",
    "c7": "Uncertainty acknowledgments for speculative claims.",
    "c8": "Sources or context for numerical statistics.",
    "c9": "Citations, links, or named sources.",
    "c10": "Consistent evidence level across all claims.",
}

_AI_READABLE_IMPROVEMENTS = [
    "Add a FAQ section to address common questions directly.",
    "Use clear heading structure (H1 -> H2 -> H3) to aid AI parsing.",
    "Separate factual claims from opinion or speculation with clear markers.",
    "Include a summary or TL;DR paragraph for AI extraction.",
    "Use structured bullet lists for factual claims rather than dense prose.",
    "Add a 'Sources' or 'References' section at the end.",
    "Replace vague authority phrases ('experts agree', 'studies show') with named specific sources.",
    "Clarify audience, scope, and what the content does not cover.",
]

_TIER_INTERPRETATIONS = {
    "S3": (
        "This content is structurally stable. Key claims appear grounded, "
        "scope is appropriate, and uncertainty is acknowledged where needed. "
        "It has reasonable AI citation readiness."
    ),
    "S2": (
        "This content is usable but has structural weaknesses. Addressing the "
        "flagged constraints would improve its reliability for AI-generated "
        "summaries or citations."
    ),
    "S1": (
        "This content has significant structural gaps. Multiple constraints are "
        "failing, which increases the risk of AI misinterpretation or citation "
        "of unsupported claims."
    ),
    "S0": (
        "This content is structurally unstable. It contains multiple unsupported "
        "claims, absolute language, or causal overreach. Major revision is needed "
        "before it is suitable for AI-facing use."
    ),
}

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 10]


def _count_any(text_lower: str, patterns: list[str]) -> int:
    return sum(1 for p in patterns if p in text_lower)


def _matching_sentences(text: str, patterns: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for sent in _sentences(text):
        if any(p in sent.lower() for p in patterns) and sent not in seen:
            seen.add(sent)
            result.append(sent)
    return result


def _sentences_with_numbers(text: str) -> list[str]:
    pat = re.compile(r'\b\d+[\.,]?\d*\s*%|\b\d{4,}|\$[\d,]+')
    return [s for s in _sentences(text) if pat.search(s)]


def _status(score: float) -> str:
    if score >= 1.0:
        return "PASS"
    if score >= 0.5:
        return "PARTIAL"
    return "FAIL"


def _tier(stability_score: float) -> tuple[str, str]:
    for threshold, code, label in _TIERS:
        if stability_score >= threshold:
            return code, label
    return "S0", "Unstable"

# ---------------------------------------------------------------------------
# Per-constraint scorers
# Each returns (score: float, explanation: str, risky_sentences: list[str])
# ---------------------------------------------------------------------------

def _c1(text: str, tl: str):
    src = _count_any(tl, _SOURCE_MARKERS)
    fact_sents = [s for s in _sentences(text) if re.search(r'\b(?:is|are|was|were)\b|\d+%', s)]
    if src == 0 and len(fact_sents) > 2:
        return 0.0, "Multiple factual claims detected but no source markers.", fact_sents[:3]
    if src < max(1, len(fact_sents) // 4):
        return 0.5, f"Few source markers ({src}) relative to apparent factual claims.", fact_sents[:2]
    return 1.0, f"Source markers present ({src}). Factual grounding appears adequate.", []


def _c2(text: str, tl: str):
    contradict = ["but also ", "yet also ", "however it is also true"]
    n = _count_any(tl, contradict)
    words = len(text.split())
    abs_count = _count_any(tl, _ABSOLUTE_MARKERS)
    sents = _matching_sentences(text, contradict)
    if n > 0:
        return 0.0, "Potentially contradictory statements detected.", sents[:2]
    if words < 60 and abs_count > 1:
        return 0.5, "Short content with multiple strong claims; logical support is thin.", []
    return 1.0, "No obvious coherence problems detected.", []


def _c3(text: str, tl: str):
    causal = _count_any(tl, _CAUSAL_MARKERS)
    src = _count_any(tl, _SOURCE_MARKERS)
    sents = _matching_sentences(text, _CAUSAL_MARKERS)
    if causal == 0:
        return 1.0, "No causal claims detected.", []
    if src == 0:
        return 0.0, f"{causal} causal claim(s) with no source support.", sents[:3]
    if causal > src:
        return 0.5, f"{causal} causal claim(s) with limited source support ({src}).", sents[:2]
    return 1.0, f"Causal claims ({causal}) have source markers ({src}).", []


def _c4(text: str, tl: str):
    n = _count_any(tl, _ABSOLUTE_MARKERS)
    sents = _matching_sentences(text, _ABSOLUTE_MARKERS)
    if n > 3:
        return 0.0, f"{n} absolute or certainty claims detected.", sents[:3]
    if n > 0:
        return 0.5, f"{n} absolute or certainty claim(s) detected.", sents[:2]
    return 1.0, "No unwarranted certainty language detected.", []


def _c5(text: str, tl: str):
    n = _count_any(tl, _SCOPE_MARKERS)
    sents = _matching_sentences(text, _SCOPE_MARKERS)
    if n > 2:
        return 0.0, f"Multiple universal scope claims ({n}).", sents[:3]
    if n > 0:
        return 0.5, f"Universal scope language detected ({n} instance(s)).", sents[:2]
    return 1.0, "Scope appears appropriately bounded.", []


def _c6(text: str, tl: str):
    risk = _count_any(tl, _SAFETY_RISK_MARKERS)
    caveat = _count_any(tl, _SAFETY_CAVEAT_MARKERS)
    sents = _matching_sentences(text, _SAFETY_RISK_MARKERS)
    if risk == 0:
        return 1.0, "No safety-sensitive claims detected.", []
    if caveat == 0:
        return 0.0, f"Safety-sensitive claims without caveats ({risk} found).", sents[:3]
    return 0.5, "Safety-sensitive claims present; verify caveats are adequate.", sents[:1]


def _c7(text: str, tl: str):
    hedge = _count_any(tl, _HEDGE_MARKERS)
    absol = _count_any(tl, _ABSOLUTE_MARKERS)
    words = len(text.split())
    if absol > 2 and hedge == 0:
        return 0.0, "Confident claims throughout with no uncertainty language.", []
    if absol > hedge and words > 50:
        return 0.5, f"Fewer hedges ({hedge}) than absolute claims ({absol}).", []
    return 1.0, f"Uncertainty language present ({hedge} hedge marker(s)).", []


def _c8(text: str, tl: str):
    num_sents = _sentences_with_numbers(text)
    src = _count_any(tl, _SOURCE_MARKERS)
    if not num_sents:
        return 1.0, "No significant quantitative claims detected.", []
    if src == 0:
        return 0.0, f"{len(num_sents)} numeric claim(s) with no source markers.", num_sents[:3]
    if len(num_sents) > src * 2:
        return 0.5, f"{len(num_sents)} numeric claim(s) with limited sources ({src}).", num_sents[:2]
    return 1.0, "Numeric claims have source markers.", []


def _c9(text: str, tl: str):
    src = _count_any(tl, _SOURCE_MARKERS)
    urls = len(re.findall(r'https?://', text))
    citations = len(re.findall(r'\[\d+\]|\[\^', text))
    total = src + urls + citations
    if total == 0:
        return 0.0, "No citations, links, or named sources found.", []
    if total <= 2:
        return 0.5, f"Limited evidence traceability ({total} source marker(s)).", []
    return 1.0, f"Evidence markers present ({total}).", []


def _c10(scores: dict):
    c4 = scores["c4"]
    c9 = scores["c9"]
    c1 = scores["c1"]
    if c4 <= 0.0 and c9 == 0.0:
        return 0.0, "High-confidence claims with no evidence — tone and evidence are misaligned.", []
    if (c4 < 1.0 and c9 < 1.0) or (c1 < 1.0 and c9 == 0.0):
        return 0.5, "Claim confidence and evidence level are partially misaligned.", []
    return 1.0, "Claim confidence and evidence level appear consistent.", []

# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def score_content(
    content: str,
    title:   str = "",
    url:     str = "",
    notes:   str = "",
) -> dict:
    """
    Run the heuristic content stability audit.

    Parameters
    ----------
    content : str   Full text of the content to audit.
    title   : str   Optional title or headline.
    url     : str   Optional source URL.
    notes   : str   Optional reviewer notes.

    Returns
    -------
    dict    Structured audit result. All fields documented in module docstring.
    """
    if not content.strip():
        content = "(empty)"

    tl = content.lower()

    # Run per-constraint scorers
    c1s, c1e, c1r   = _c1(content, tl)
    c2s, c2e, c2r   = _c2(content, tl)
    c3s, c3e, c3r   = _c3(content, tl)
    c4s, c4e, c4r   = _c4(content, tl)
    c5s, c5e, c5r   = _c5(content, tl)
    c6s, c6e, c6r   = _c6(content, tl)
    c7s, c7e, c7r   = _c7(content, tl)
    c8s, c8e, c8r   = _c8(content, tl)
    c9s, c9e, c9r   = _c9(content, tl)

    raw = {
        "c1": c1s, "c2": c2s, "c3": c3s, "c4": c4s, "c5": c5s,
        "c6": c6s, "c7": c7s, "c8": c8s, "c9": c9s,
    }
    c10s, c10e, c10r = _c10(raw)
    raw["c10"] = c10s

    # Aggregate metrics
    divergence_raw  = sum(1.0 - raw[c] for c in CONSTRAINT_CODES)
    divergence      = round(divergence_raw / 10.0, 4)
    stability_score = round((1.0 - divergence_raw / 10.0) * 100.0, 1)
    tier_code, tier_label = _tier(stability_score)

    # Derived signals
    c9_score = raw["c9"]
    if stability_score >= 80 and c9_score >= 0.5:
        citation_readiness = "High"
    elif stability_score >= 60 or c9_score >= 0.5:
        citation_readiness = "Medium"
    else:
        citation_readiness = "Low"

    if stability_score >= 80:
        misinterpretation_risk = "Low"
    elif stability_score >= 60:
        misinterpretation_risk = "Medium"
    else:
        misinterpretation_risk = "High"

    # Per-constraint detail list
    detail_rows = [
        ("c1", c1s, c1e, c1r), ("c2", c2s, c2e, c2r), ("c3", c3s, c3e, c3r),
        ("c4", c4s, c4e, c4r), ("c5", c5s, c5e, c5r), ("c6", c6s, c6e, c6r),
        ("c7", c7s, c7e, c7r), ("c8", c8s, c8e, c8r), ("c9", c9s, c9e, c9r),
        ("c10", c10s, c10e, c10r),
    ]
    constraint_details = [
        {
            "code":        code,
            "name":        CONSTRAINT_NAMES[code],
            "score":       score,
            "status":      _status(score),
            "explanation": expl,
        }
        for code, score, expl, _ in detail_rows
    ]

    # Risky claims (aggregate from all constraint scorers, deduplicated)
    risky_claims: list[str] = []
    for _, _, _, sents in detail_rows:
        for s in sents:
            if s not in risky_claims:
                risky_claims.append(s)

    # Missing evidence and fixes (only for failing/partial constraints)
    missing_evidence = [
        _MISSING_EVIDENCE_MAP[c]
        for c in CONSTRAINT_CODES
        if raw.get(c, 1.0) < 1.0 and c in _MISSING_EVIDENCE_MAP
    ]
    recommended_fixes = [
        _FIX_MAP[c]
        for c in CONSTRAINT_CODES
        if raw.get(c, 1.0) < 1.0
    ]

    return {
        # Metadata
        "title":      title,
        "url":        url,
        "notes":      notes,
        "word_count": len(content.split()),
        "scored_at":  datetime.now().isoformat(timespec="seconds"),
        "scorer":     "heuristic-v1",

        # Raw scores (C1-C10)
        **{c: raw[c] for c in CONSTRAINT_CODES},

        # Aggregate metrics
        "divergence_raw":       round(divergence_raw, 4),
        "divergence":           divergence,
        "stability_score":      stability_score,
        "stability_tier":       tier_code,
        "stability_tier_label": tier_label,

        # Derived signals
        "ai_citation_readiness":     citation_readiness,
        "ai_misinterpretation_risk": misinterpretation_risk,

        # Structured details
        "constraint_details":       constraint_details,
        "risky_claims":             risky_claims,
        "missing_evidence":         missing_evidence,
        "recommended_fixes":        recommended_fixes,
        "ai_readable_improvements": _AI_READABLE_IMPROVEMENTS,
    }

# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_markdown_report(audit: dict) -> str:
    """Build a Markdown audit report from an audit dict returned by score_content()."""

    lines: list[str] = []

    lines += [
        "# AOSL Content Stability Audit",
        "",
        "---",
        "",
        "## Input",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Title | {audit.get('title') or '(not provided)'} |",
        f"| URL | {audit.get('url') or '(not provided)'} |",
        f"| Date | {audit.get('scored_at', '')} |",
        f"| Word count | {audit.get('word_count', 0)} |",
        f"| Scorer | {audit.get('scorer', 'heuristic-v1')} |",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Stability Score | {audit['stability_score']} / 100 |",
        f"| Divergence D | {audit['divergence_raw']:.2f} (raw) / {audit['divergence']:.4f} (normalized) |",
        f"| Stability Tier | {audit['stability_tier']} — {audit['stability_tier_label']} |",
        f"| AI Citation Readiness | {audit['ai_citation_readiness']} |",
        f"| AI Misinterpretation Risk | {audit['ai_misinterpretation_risk']} |",
        "",
        "---",
        "",
        "## C1–C10 Scores",
        "",
        "| Code | Constraint | Score | Status | Explanation |",
        "|------|------------|-------|--------|-------------|",
    ]

    for d in audit["constraint_details"]:
        lines.append(
            f"| {d['code'].upper()} | {d['name']} | {d['score']:.1f} "
            f"| {d['status']} | {d['explanation']} |"
        )

    lines += ["", "---", ""]

    if audit.get("risky_claims"):
        lines += ["## Main Risks", ""]
        for claim in audit["risky_claims"]:
            lines.append(f'- "{claim}"')
        lines += ["", "---", ""]
    else:
        lines += [
            "## Main Risks",
            "",
            "No high-risk sentences detected by the heuristic.",
            "",
            "---",
            "",
        ]

    if audit.get("missing_evidence"):
        lines += ["## Missing Evidence", ""]
        for item in audit["missing_evidence"]:
            lines.append(f"- {item}")
        lines += ["", "---", ""]

    if audit.get("recommended_fixes"):
        lines += ["## Recommended Fixes", ""]
        for fix in audit["recommended_fixes"]:
            lines.append(f"- {fix}")
        lines += ["", "---", ""]

    if audit.get("ai_readable_improvements"):
        lines += ["## AI-Readable Improvements", ""]
        for item in audit["ai_readable_improvements"]:
            lines.append(f"- {item}")
        lines += ["", "---", ""]

    tier = audit.get("stability_tier", "S0")
    interp = _TIER_INTERPRETATIONS.get(tier, "")
    lines += [
        "## What This Means",
        "",
        interp,
        "",
        "---",
        "",
        "## What This Does Not Prove",
        "",
        (
            "This v0.1 audit uses local keyword heuristics, not a trained model or human expert. "
            "It does not prove that AI platforms will cite, recommend, or rank this content. "
            "It does not detect factual errors — content can score high D and still be factually correct, "
            "or score low D and still be factually wrong. "
            "It is an estimate of structural readiness and evidence traceability, not a quality guarantee. "
            "Results should be reviewed by a human before taking action."
        ),
        "",
        "---",
        "",
        "```",
        "Scorer  : heuristic-v1",
        "Status  : early prototype — not for production use",
        "```",
    ]

    return "\n".join(lines)
