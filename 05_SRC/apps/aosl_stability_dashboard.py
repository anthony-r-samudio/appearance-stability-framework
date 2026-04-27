import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path

# --- Canonical constraint metadata ---
CONSTRAINT_NAMES = {
    "c1":  "c1  Factual Grounding",
    "c2":  "c2  Logical Coherence",
    "c3":  "c3  Causal Integrity",
    "c4":  "c4  Epistemic Calibration",
    "c5":  "c5  Scope Discipline",
    "c6":  "c6  Safety Integrity",
    "c7":  "c7  Uncertainty Acknowledgment",
    "c8":  "c8  Quantitative Accuracy",
    "c9":  "c9  Evidence Traceability",
    "c10": "c10 Constraint Interaction Consistency",
}
CONSTRAINT_COLS = list(CONSTRAINT_NAMES.keys())

FILTER_COLS = [
    "model_name", "generator_model", "judge_model",
    "prompt_id", "temperature", "stability_tier",
]

DEFAULT_SCAN_DIRS = ["04_RUNS/demo", "04_RUNS/openrouter_demo"]


# ------------------------------------------------------------------ loaders --

def _normalize_constraint_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Expand nested constraint_scores or parsed_score dicts into c1-c10 columns."""
    for nested_col in ("constraint_scores", "parsed_score"):
        if nested_col not in df.columns:
            continue
        expanded = df[nested_col].apply(lambda x: x if isinstance(x, dict) else {})
        for c in CONSTRAINT_COLS:
            if c not in df.columns:
                df[c] = expanded.apply(lambda d, _c=c: d.get(_c))
        df = df.drop(columns=[nested_col], errors="ignore")
    return df


def _normalize_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Rename known column aliases to canonical names."""
    return df.rename(columns={"divergence_D": "D"})


def _postprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalize_aliases(df)
    df = _normalize_constraint_scores(df)
    # coerce c1-c10 and D columns to numeric
    for c in CONSTRAINT_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for col in ("D", "D_norm"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _load_csv(path: str) -> pd.DataFrame:
    return _postprocess(pd.read_csv(path))


def _load_jsonl(path: str) -> pd.DataFrame:
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return _postprocess(pd.DataFrame(records))


def _load_json(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        first = next(iter(data.values()), None)
        records = first if isinstance(first, list) else list(data.values())
    else:
        raise ValueError("JSON file must contain a list of records or a dict of lists.")
    return _postprocess(pd.DataFrame(records))


def load_file(path: str) -> "tuple[pd.DataFrame | None, str | None]":
    """Return (df, error). df is None if loading failed."""
    path = path.strip()
    if not os.path.exists(path):
        return None, f"File not found: `{path}`"
    ext = Path(path).suffix.lower()
    try:
        if ext == ".csv":
            return _load_csv(path), None
        elif ext == ".jsonl":
            return _load_jsonl(path), None
        elif ext == ".json":
            return _load_json(path), None
        else:
            return None, (
                f"Unsupported file type `{ext}`. "
                "This dashboard supports .csv, .jsonl, and .json files."
            )
    except Exception as exc:
        return None, f"Could not load `{Path(path).name}`: {exc}"


def scan_default_dirs(repo_root: str) -> list:
    found = []
    for rel_dir in DEFAULT_SCAN_DIRS:
        abs_dir = os.path.join(repo_root, rel_dir)
        if os.path.isdir(abs_dir):
            for fname in sorted(os.listdir(abs_dir)):
                if fname.endswith((".csv", ".jsonl", ".json")):
                    found.append(os.path.join(abs_dir, fname))
    return found


# --------------------------------------------------------------- dashboard ---

def main():
    st.set_page_config(page_title="AOSL Stability Dashboard", layout="wide")
    st.title("AOSL Stability Dashboard")
    st.caption("AI Output Stability Layer — run output viewer")

    repo_root = str(Path(__file__).resolve().parents[2])

    # ---- sidebar: file selection ----------------------------------------
    st.sidebar.header("Load Data")
    available = scan_default_dirs(repo_root)
    selected_paths = []

    if available:
        st.sidebar.subheader("Run output files found")
        for fpath in available:
            label = os.path.relpath(fpath, repo_root)
            if st.sidebar.checkbox(label, value=True, key=f"chk_{fpath}"):
                selected_paths.append(fpath)
    else:
        st.sidebar.info(
            "No files found in 04_RUNS/demo or 04_RUNS/openrouter_demo.\n"
            "Use the custom path box below."
        )

    st.sidebar.subheader("Custom file path")
    custom = st.sidebar.text_input(
        "Paste an absolute path (.csv, .jsonl, .json)",
        placeholder="C:\\...\\my_run.csv",
    )
    if custom.strip():
        selected_paths.append(custom.strip())

    if not selected_paths:
        st.info(
            "No files selected. "
            "Tick one or more files in the sidebar, or paste a custom path."
        )
        return

    # ---- load and combine -----------------------------------------------
    frames = []
    for fpath in selected_paths:
        df, err = load_file(fpath)
        if err:
            st.warning(f"**Load error:** {err}")
        else:
            df["_source_file"] = os.path.relpath(fpath, repo_root)
            frames.append(df)

    if not frames:
        st.error("No files loaded successfully. Check the warnings above.")
        return

    data = pd.concat(frames, ignore_index=True)

    # ---- sidebar: filters -----------------------------------------------
    st.sidebar.header("Filters")
    mask = pd.Series([True] * len(data), index=data.index)

    for col in FILTER_COLS:
        if col not in data.columns:
            continue
        unique_vals = sorted(data[col].dropna().astype(str).unique())
        if not unique_vals:
            continue
        chosen = st.sidebar.multiselect(
            f"{col}",
            options=unique_vals,
            default=unique_vals,
            key=f"flt_{col}",
        )
        mask = mask & data[col].astype(str).isin(chosen)

    filtered = data[mask].copy()

    # ---- summary metrics ------------------------------------------------
    st.header("Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total rows", len(filtered))

    if "model_name" in filtered.columns:
        models = filtered["model_name"].dropna().unique().tolist()
        c2.metric("Models", len(models))
        c2.caption(", ".join(str(m) for m in models[:6]))
    elif "generator_model" in filtered.columns:
        models = filtered["generator_model"].dropna().unique().tolist()
        c2.metric("Generator models", len(models))
        c2.caption(", ".join(str(m) for m in models[:6]))

    if "prompt_id" in filtered.columns:
        prompts = filtered["prompt_id"].dropna().unique().tolist()
        c3.metric("Prompt IDs", len(prompts))
        c3.caption(", ".join(str(p) for p in prompts[:6]))

    # divergence scores
    st.subheader("Divergence Scores")
    dc1, dc2 = st.columns(2)
    if "D" in filtered.columns:
        d_mean = filtered["D"].dropna().mean()
        dc1.metric("Average D", f"{d_mean:.3f}" if pd.notna(d_mean) else "N/A")
    else:
        dc1.info("`D` column not present in loaded data.")

    if "D_norm" in filtered.columns:
        dn_mean = filtered["D_norm"].dropna().mean()
        dc2.metric("Average D_norm", f"{dn_mean:.3f}" if pd.notna(dn_mean) else "N/A")
    else:
        dc2.info("`D_norm` column not present in loaded data.")

    # stability tier counts
    if "stability_tier" in filtered.columns:
        st.subheader("Stability Tier Counts")
        tier_counts = (
            filtered["stability_tier"]
            .value_counts()
            .rename_axis("stability_tier")
            .reset_index(name="count")
        )
        st.dataframe(tier_counts, use_container_width=True)
    else:
        st.info("`stability_tier` column not present. Tier counts unavailable.")

    # ---- constraint scores ----------------------------------------------
    present = [c for c in CONSTRAINT_COLS if c in filtered.columns]
    if present:
        st.header("Constraint Scores (c1–c10)")
        means = filtered[present].mean()
        means_df = pd.DataFrame({
            "Constraint": [CONSTRAINT_NAMES[c] for c in present],
            "Mean Score": [round(means[c], 3) if pd.notna(means[c]) else None for c in present],
        })
        st.dataframe(means_df, use_container_width=True)

        valid_means = means.dropna()
        if not valid_means.empty:
            st.subheader("Weakest Constraints")
            for ckey, score in valid_means.nsmallest(3).items():
                st.write(f"- **{CONSTRAINT_NAMES[ckey]}**: {score:.3f}")
    else:
        st.info(
            "No c1–c10 constraint score columns found in loaded data. "
            "Files that contain a `constraint_scores` or `parsed_score` "
            "nested dict will be expanded automatically."
        )

    # ---- prompt-level table ---------------------------------------------
    if "prompt_id" in filtered.columns:
        st.header("Prompt-Level Summary")
        agg = {c: "mean" for c in present}
        if "D" in filtered.columns:
            agg["D"] = "mean"
        if "D_norm" in filtered.columns:
            agg["D_norm"] = "mean"
        if agg:
            prompt_tbl = (
                filtered.groupby("prompt_id")
                .agg(agg)
                .round(3)
                .reset_index()
            )
            st.dataframe(prompt_tbl, use_container_width=True)

    # ---- output preview -------------------------------------------------
    st.header("Output Preview (first 50 rows)")
    preview_priority = [
        "_source_file", "prompt_id", "model_name", "generator_model",
        "temperature", "stability_tier", "D", "D_norm",
        "output_text", "prompt_text",
    ]
    preview_cols = [c for c in preview_priority if c in filtered.columns]
    st.dataframe(
        filtered[preview_cols].head(50) if preview_cols else filtered.head(50),
        use_container_width=True,
    )

    # ---- export ---------------------------------------------------------
    st.header("Export")
    st.download_button(
        label="Download filtered data as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="aosl_filtered_export.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
