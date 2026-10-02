import csv
import importlib.util
import io
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import threading
from urllib.error import HTTPError

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "05_SRC/experiments/run_ollama_local_scoring.py"
spec = importlib.util.spec_from_file_location("ollama_local_scoring", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture
def paths(tmp_path):
    source = tmp_path / "input.csv"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["prompt_id", "prompt_text", "output_text"])
        writer.writeheader()
        writer.writerow({"prompt_id": "same-id", "prompt_text": "What is 2 + 2?", "output_text": "2 + 2 = 4."})
        writer.writerow({"prompt_id": "same-id", "prompt_text": "What is 2 + 2?", "output_text": "2 + 2 = 5."})
    return source, tmp_path / "run"


def valid_scores():
    return dict.fromkeys(runner.CONSTRAINT_CODES, 1) | {"notes": "No violations detected."}


def fake_server(monkeypatch, judge_text=None, done_reason="stop", cloud=False):
    calls = []
    text = json.dumps(valid_scores()) if judge_text is None else judge_text
    raw = json.dumps({"done": True, "done_reason": done_reason, "message": {"content": text}}, indent=2).encode()

    def request(base_url, endpoint, timeout, payload=None):
        calls.append((base_url, endpoint, payload))
        if endpoint == "/api/version":
            return b'{"version":"test-version"}'
        if endpoint == "/api/tags":
            model = {"name": "qwen2.5:3b", "digest": "sha256:test-model"}
            if cloud:
                model["remote_host"] = "https://example.com"
            return json.dumps({"models": [model]}).encode()
        if endpoint == "/api/show":
            return b'{"template":"test-template","parameters":"test-parameters"}'
        assert endpoint == "/api/chat"
        return raw

    monkeypatch.setattr(runner, "request_bytes", request)
    return calls, raw


def invoke(paths, *extra):
    source, destination = paths
    return runner.main(["--input-csv", str(source), "--output-dir", str(destination), *extra])


def test_dry_run_no_requests_or_files(paths, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Dry run contacted a server")
    monkeypatch.setattr(runner, "request_bytes", forbidden)
    original = paths[0].read_bytes()
    assert invoke(paths, "--dry-run") == 0
    assert not paths[1].exists()
    assert paths[0].read_bytes() == original


def test_valid_run_preserves_input_request_raw_response_and_provenance(paths, monkeypatch):
    calls, raw = fake_server(monkeypatch)
    original = paths[0].read_bytes()
    assert invoke(paths, "--limit", "2") == 0
    source, destination = paths
    assert source.read_bytes() == original == (destination / "frozen_input.csv").read_bytes()
    assert (destination / "row_0001.response.json").read_bytes() == raw
    manifest = json.loads((destination / "run_manifest.json").read_text())
    assert manifest["input_sha256"] == runner.sha256(original)
    assert manifest["selected_rows"] == 2
    assert manifest["scorer_sha256"] and manifest["runner_sha256"]
    records = [json.loads(line) for line in (destination / "results.jsonl").read_text().splitlines()]
    assert [record["row_index"] for record in records] == [1, 2]
    assert records[0]["divergence"] == 0 and records[0]["stability_tier"] == "S0"
    chats = [payload for _, endpoint, payload in calls if endpoint == "/api/chat"]
    assert len(chats) == 2
    assert chats[0]["messages"][0]["content"] == runner.build_judge_prompt("What is 2 + 2?", "2 + 2 = 4.")
    assert chats[0]["format"] == "json" and chats[0]["options"]["temperature"] == 0
    assert json.loads((destination / "model_identity.json").read_text())["digest"] == "sha256:test-model"


@pytest.mark.parametrize("invalid", [
    {**valid_scores(), "c1": 0.7}, {**valid_scores(), "c1": True},
    {**valid_scores(), "c1": "1"}, {**valid_scores(), "c1": None},
    {**valid_scores(), "c1": float("nan")}, {**valid_scores(), "notes": 1},
    {key: value for key, value in valid_scores().items() if key != "c7"},
    {**valid_scores(), "extra": 1}, [valid_scores()],
])
def test_invalid_scores_are_not_normalized(invalid):
    with pytest.raises(ValueError):
        runner.strict_scores(json.dumps(invalid))


def test_duplicate_keys_rejected():
    raw = json.dumps(valid_scores()).replace('"c1": 1', '"c1": 0, "c1": 1')
    with pytest.raises(ValueError, match="Duplicate"):
        runner.strict_scores(raw)


@pytest.mark.parametrize("text,reason", [("not JSON", "stop"), (json.dumps(valid_scores()), "length")])
def test_failed_judge_keeps_raw_and_has_no_scores(paths, monkeypatch, text, reason):
    _, raw = fake_server(monkeypatch, text, reason)
    assert invoke(paths) == 1
    assert (paths[1] / "row_0001.response.json").read_bytes() == raw
    record = json.loads((paths[1] / "results.jsonl").read_text())
    assert record["status"] == "error"
    assert "scores" not in record and "divergence" not in record


def test_existing_directory_rejected_even_in_dry_run(paths, monkeypatch):
    paths[1].mkdir()
    sentinel = paths[1] / "existing-evidence.txt"
    sentinel.write_text("unchanged")
    calls, _ = fake_server(monkeypatch)
    with pytest.raises(SystemExit):
        invoke(paths, "--dry-run")
    assert sentinel.read_text() == "unchanged" and not calls


def test_cloud_model_rejected_before_judging(paths, monkeypatch):
    calls, _ = fake_server(monkeypatch, cloud=True)
    assert invoke(paths) == 1
    assert not any(endpoint == "/api/chat" for _, endpoint, _ in calls)
    assert (paths[1] / "setup_error.json").exists()


def test_http_error_body_preserved(paths, monkeypatch):
    fake_server(monkeypatch)
    original = runner.request_bytes
    def request(base_url, endpoint, timeout, payload=None):
        if endpoint == "/api/chat":
            raise HTTPError(base_url + endpoint, 500, "Server error", {}, io.BytesIO(b"raw failure"))
        return original(base_url, endpoint, timeout, payload)
    monkeypatch.setattr(runner, "request_bytes", request)
    assert invoke(paths) == 1
    assert (paths[1] / "row_0001.http_error.bin").read_bytes() == b"raw failure"


@pytest.mark.parametrize("value", ["https://example.com", "http://8.8.8.8:11434", "http://localhost:11434/api", "http://user:pass@localhost:11434"])
def test_nonlocal_or_ambiguous_url_rejected(value):
    with pytest.raises(ValueError):
        runner.local_url(value)


def test_native_http_transport_and_redirect_refusal():
    received = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"done":true}')

        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "http://example.com/")
            self.end_headers()

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            payload = {"model": "local-test", "prompt": "Rodríguez"}
            assert runner.request_bytes(base_url, "/api/chat", 2, payload) == b'{"done":true}'
            assert received == [payload]
            with pytest.raises(HTTPError) as exc:
                runner.request_bytes(base_url, "/redirect", 2)
            assert exc.value.code == 302
        finally:
            server.shutdown()
            thread.join(timeout=2)
