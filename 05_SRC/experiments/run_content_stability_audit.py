"""
run_content_stability_audit.py  (05_SRC/experiments/)

CLI runner for the AOSL Content Stability Auditor v0.1.

Reads a local text file, runs the heuristic stability audit, and writes
a JSON report and a Markdown report into the output directory.

Usage
-----
    py 05_SRC\\experiments\\run_content_stability_audit.py --input 09_TEMP\\sample_content.txt --title "Sample Article"

    py 05_SRC\\experiments\\run_content_stability_audit.py --help
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

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
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = _REPO_ROOT / "04_RUNS" / "content_stability_auditor"

# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------

def _print_summary(audit: dict, md_path: Path, json_path: Path) -> None:
    tier   = audit["stability_tier"]
    label  = audit["stability_tier_label"]
    score  = audit["stability_score"]
    D      = audit["divergence_raw"]
    cit    = audit["ai_citation_readiness"]
    risk   = audit["ai_misinterpretation_risk"]

    print()
    print("=" * 60)
    print("AOSL Content Stability Audit — Summary")
    print("=" * 60)
    if audit.get("title"):
        print(f"  Title   : {audit['title']}")
    if audit.get("url"):
        print(f"  URL     : {audit['url']}")
    print(f"  Words   : {audit['word_count']}")
    print()
    print(f"  Stability Score : {score} / 100")
    print(f"  Divergence D    : {D:.2f} (raw)")
    print(f"  Tier            : {tier} — {label}")
    print(f"  Citation Ready  : {cit}")
    print(f"  Misintp. Risk   : {risk}")
    print()
    print("  C1–C10 Breakdown:")
    for d in audit["constraint_details"]:
        bar = "PASS   " if d["score"] >= 1.0 else ("PARTIAL" if d["score"] >= 0.5 else "FAIL   ")
        print(f"    {d['code'].upper():<4} {bar}  {d['name']}")
    print()
    if audit.get("risky_claims"):
        print(f"  Risky claims detected : {len(audit['risky_claims'])}")
        for claim in audit["risky_claims"][:3]:
            print(f"    - \"{claim[:80]}{'...' if len(claim) > 80 else ''}\"")
        if len(audit["risky_claims"]) > 3:
            print(f"    ... and {len(audit['risky_claims']) - 3} more (see report)")
    print()
    print(f"  Reports saved:")
    print(f"    JSON     : {json_path}")
    print(f"    Markdown : {md_path}")
    print()
    print("=" * 60)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AOSL Content Stability Auditor v0.1 — CLI runner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py 05_SRC\\experiments\\run_content_stability_audit.py \\\n"
            "      --input 09_TEMP\\sample_content.txt \\\n"
            "      --title \"Sample Article\"\n"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        metavar="PATH",
        help="Path to the .txt file to audit.",
    )
    parser.add_argument(
        "--title", "-t",
        default="",
        metavar="TEXT",
        help="Optional title or headline for the content.",
    )
    parser.add_argument(
        "--url", "-u",
        default="",
        metavar="URL",
        help="Optional source URL.",
    )
    parser.add_argument(
        "--notes", "-n",
        default="",
        metavar="TEXT",
        help="Optional notes or context.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        metavar="PATH",
        help=(
            f"Directory to write output files. "
            f"Default: 04_RUNS/content_stability_auditor/"
        ),
    )
    args = parser.parse_args()

    # Resolve paths
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = _REPO_ROOT / input_path
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    if not output_dir.is_absolute():
        output_dir = _REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read content
    content = input_path.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        print(f"ERROR: Input file is empty: {input_path}")
        sys.exit(1)

    print(f"Auditing: {input_path.name}  ({len(content.split())} words)")

    # Run audit
    audit = score_content(
        content=content,
        title=args.title or input_path.stem,
        url=args.url,
        notes=args.notes,
    )

    # Build output filenames
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = (args.title or input_path.stem)[:40].replace(" ", "_").replace("/", "-")
    stem = f"content_audit_{ts}_{slug}"

    json_path = output_dir / f"{stem}.json"
    md_path   = output_dir / f"{stem}.md"

    # Save JSON (exclude content from export to keep it compact)
    json_payload = {k: v for k, v in audit.items() if k != "ai_readable_improvements"}
    json_path.write_text(
        json.dumps(json_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Save Markdown
    md_path.write_text(build_markdown_report(audit), encoding="utf-8")

    # Print summary
    _print_summary(audit, md_path, json_path)


if __name__ == "__main__":
    main()
