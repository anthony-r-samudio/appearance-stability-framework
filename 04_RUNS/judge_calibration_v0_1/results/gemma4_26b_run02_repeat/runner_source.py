"""Isolated native Ollama judge pilot; never changes the OpenRouter pipeline."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import ipaddress
import json
import math
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "05_SRC"))
from scoring.fast_batch_scorer import CONSTRAINT_CODES, build_judge_prompt, _compute_metrics

PROFILE = "ollama-native-json-strict-v1"


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def local_url(value):
    parsed = urlsplit(value)
    host = parsed.hostname
    if parsed.scheme != "http" or parsed.path not in ("", "/") or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Use an HTTP Ollama base URL without credentials or a path.")
    if host != "localhost":
        try:
            address = ipaddress.ip_address(host or "")
        except ValueError as exc:
            raise ValueError("Use localhost or a numeric LAN IP address.") from exc
        if not (address.is_loopback or address.is_private):
            raise ValueError("This pilot only accepts localhost or private LAN addresses.")
    return value.rstrip("/")


def request_bytes(base_url, endpoint, timeout, payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(base_url + endpoint, data=data, headers={"Content-Type": "application/json"})
    # A local request must not be forwarded through an environment-configured proxy.
    with build_opener(ProxyHandler({}), NoRedirects()).open(request, timeout=timeout) as response:
        return response.read()


def strict_scores(raw_text):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate judge key: {key}")
            result[key] = value
        return result

    parsed = json.loads(raw_text, object_pairs_hook=unique_object)
    if not isinstance(parsed, dict) or set(parsed) != set(CONSTRAINT_CODES) | {"notes"}:
        raise ValueError("Judge must return exactly c1-c10 and notes.")
    for code in CONSTRAINT_CODES:
        value = parsed[code]
        if type(value) not in (int, float) or value not in (0, 0.5, 1):
            raise ValueError(f"Invalid {code}: {value!r}; no score rounding is performed.")
    if not isinstance(parsed["notes"], str):
        raise ValueError("Judge notes must be a string.")
    return {code: parsed[code] for code in CONSTRAINT_CODES}, parsed["notes"]


def run(args):
    base_url = local_url(args.base_url)
    if args.limit < 1 or args.max_tokens < 1 or args.num_ctx < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError("Limit, max tokens, context and timeout must be positive.")
    if not math.isfinite(args.temperature) or args.temperature < 0:
        raise ValueError("Temperature must be finite and nonnegative.")
    source = args.input_csv.resolve()
    destination = args.output_dir.resolve()
    if destination.exists():
        raise FileExistsError(f"Output directory already exists; choose a fresh directory: {destination}")
    data = source.read_bytes()
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not {"prompt_text", "output_text"}.issubset(reader.fieldnames):
        raise ValueError("CSV must have unique headers including prompt_text and output_text.")
    all_rows = list(reader)
    rows = all_rows[:args.limit]
    if not rows:
        raise ValueError("Input CSV has no rows.")
    for row in rows:
        if None in row or any(value is None for value in row.values()) or not row["prompt_text"].strip() or not row["output_text"].strip():
            raise ValueError("Selected rows must be well-formed with nonempty prompt_text/output_text.")
    boundary = args.boundary_notes.read_bytes() if args.boundary_notes else b""
    boundary_text = boundary.decode("utf-8-sig")
    prompts = [build_judge_prompt(row["prompt_text"], row["output_text"], boundary_text) for row in rows]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        git_status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True)
    except (OSError, subprocess.CalledProcessError):
        commit, git_status = None, "Git provenance unavailable"
    manifest = {
        "profile": PROFILE, "purpose": "local integration pilot; not calibrated evidence",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit, "git_status": git_status,
        "input_csv": str(source), "input_sha256": sha256(data),
        "input_rows": len(all_rows), "selected_rows": len(rows), "selection": "first N rows in file order",
        "output_dir": str(destination), "base_url": base_url, "judge_model": args.model,
        "temperature": args.temperature, "max_tokens": args.max_tokens,
        "num_ctx": args.num_ctx, "timeout_seconds": args.timeout,
        "repeats": 1, "retries": 0, "format": "json",
        "boundary_notes_sha256": sha256(boundary),
        "prompt_sha256": [sha256(prompt.encode("utf-8")) for prompt in prompts],
        "runner_sha256": sha256(Path(__file__).read_bytes()),
        "scorer_sha256": sha256((REPO_ROOT / "05_SRC/scoring/fast_batch_scorer.py").read_bytes()),
    }
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        print("Dry run: no server requests and no files written.")
        return 0

    destination.mkdir(parents=True, exist_ok=False)
    (destination / "frozen_input.csv").write_bytes(data)
    (destination / "boundary_notes.txt").write_bytes(boundary)
    (destination / "runner_source.py").write_bytes(Path(__file__).read_bytes())
    (destination / "scorer_source.py").write_bytes((REPO_ROOT / "05_SRC/scoring/fast_batch_scorer.py").read_bytes())
    write_json(destination / "run_manifest.json", manifest)
    # Preserve metadata bytes before interpreting them. Missing models never auto-pull.
    try:
        for name, endpoint in (("version", "/api/version"), ("tags", "/api/tags")):
            raw = request_bytes(base_url, endpoint, args.timeout)
            (destination / f"ollama_{name}.json").write_bytes(raw)
        tags = json.loads((destination / "ollama_tags.json").read_bytes())
        matches = [model for model in tags["models"] if model.get("name") == args.model]
        if len(matches) != 1 or not matches[0].get("digest"):
            raise ValueError("Model must be installed with the exact requested name and a digest.")
        model_info = matches[0]
        raw_show = request_bytes(base_url, "/api/show", args.timeout, {"model": args.model})
        (destination / "ollama_show.json").write_bytes(raw_show)
        show = json.loads(raw_show)
        if args.model.endswith("-cloud") or any(item.get(key) for item in (model_info, show) for key in ("remote_host", "remote_model")):
            raise ValueError("Cloud-backed Ollama models are not allowed in this local pilot.")
        write_json(destination / "model_identity.json", model_info)
    except Exception as exc:
        if isinstance(exc, HTTPError):
            (destination / "setup_http_error.bin").write_bytes(exc.read())
        write_json(destination / "setup_error.json", {"error_type": type(exc).__name__, "error": str(exc)})
        print(f"Setup failed; details preserved in {destination}", file=sys.stderr)
        return 1

    errors = 0
    with (destination / "results.jsonl").open("x", encoding="utf-8") as handle:
        for index, (row, prompt) in enumerate(zip(rows, prompts), 1):
            prefix = destination / f"row_{index:04d}"
            payload = {"model": args.model, "messages": [{"role": "user", "content": prompt}],
                       "stream": False, "format": "json",
                       "options": {"temperature": args.temperature, "num_predict": args.max_tokens, "num_ctx": args.num_ctx}}
            write_json(prefix.with_suffix(".request.json"), payload)
            record = {"row_index": index, "input": row, "profile": PROFILE, "status": "error"}
            try:
                raw = request_bytes(base_url, "/api/chat", args.timeout, payload)
                prefix.with_suffix(".response.json").write_bytes(raw)
                response = json.loads(raw)
                if response.get("done") is not True or response.get("done_reason") == "length":
                    raise ValueError("Incomplete or token-limited judge response.")
                raw_text = response["message"]["content"]
                prefix.with_suffix(".judge.txt").write_text(raw_text, encoding="utf-8")
                scores, notes = strict_scores(raw_text)
                record.update(status="ok", scores=scores, notes=notes, **_compute_metrics(scores))
            except Exception as exc:
                if isinstance(exc, HTTPError):
                    prefix.with_suffix(".http_error.bin").write_bytes(exc.read())
                record.update(error_type=type(exc).__name__, error=str(exc))
                errors += 1
            handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            handle.flush()
            print(f"Row {index}/{len(rows)}: {record['status']}", flush=True)
    write_json(destination / "run_summary.json", {"rows": len(rows), "valid": len(rows) - errors, "errors": errors})
    print(f"Saved pilot to {destination}")
    return 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=800)
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--boundary-notes", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
