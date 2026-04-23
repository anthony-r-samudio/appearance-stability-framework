# AOSL Engine — Project Context

## What AOSL Stands For

AI Output Stability Layer

## Purpose

This repository is the working implementation environment for AOSL: scoring runs, pilots,
prompt experiments, analytics, and output artifacts.

## Folder Structure

| Folder | Role |
|---|---|
| `00_CONFIG/` | Config files (e.g. Streamlit settings) |
| `01_CANON/` | Canonical definitions and locked project documents |
| `02_PROMPTS/` | Prompt sets and generators |
| `03_DATA/` | Raw, intermediate, scored, and combined datasets |
| `04_RUNS/` | Run-specific artifacts (pilots, sweeps) |
| `05_SRC/` | Source code: analysis, apps, experiments, scoring, utils, scripts |
| `06_OUTPUTS/` | Figures, tables, reports, cost outputs |
| `07_DOCS/` | Working documentation and reference images |
| `08_TESTS/` | Tests and validation scripts |
| `09_TEMP/` | Temporary scratch outputs |
| `10_MEMORY/` | Project memory and reference notes |
| `99_ARCHIVE/` | Deprecated or retired material |
| `AOSL/` | Python package (kept at repo root) |

## Package Note

The `AOSL` Python package is kept at the repo root (not inside `05_SRC/`) while the package
is still being built out. Install with `pip install -e .` from the repo root.
