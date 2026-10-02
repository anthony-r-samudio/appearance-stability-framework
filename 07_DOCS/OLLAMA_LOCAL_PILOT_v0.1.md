# Local Ollama scoring pilot

This adds a separate CSV judge runner using Ollama's native HTTP API. It leaves
the OpenRouter client, archived runs, existing scoring parser and demo unchanged.
It reuses `build_judge_prompt` and the existing normalized divergence/tier metrics.
The alternative is a shared provider abstraction; this pilot avoids changing all
existing callers before the local route has been exercised.

## Profile and limitations

The profile is `ollama-native-json-strict-v1`: one repeat, no automatic retries,
JSON response mode, temperature 0 by default, 800 generated tokens and an 8192-token
context. Exact request settings and optional boundary guidance are recorded.
The parser requires exactly c1-c10 in {0, 0.5, 1} plus string notes. Missing,
duplicate, boolean, nonnumeric, out-of-range and intermediate scores are errors;
they are never rounded. In contrast, the existing OpenRouter parser clamps scores.
JSON mode and this strict parser are methodological differences, so local results
must not be pooled with archived OpenRouter/Gemini scores as a matched comparison.

The installed `qwen2.5:3b` is an integration-test judge, not a calibrated evaluator.
This route does not regenerate source outputs. Context truncation by the backend
is not independently detected; check prompt lengths before a substantive study.
Temperature 0 does not guarantee reproducibility across hardware/runtime changes.
Timeouts are HTTP socket timeouts, not a hard whole-run deadline.

## EliteBook PowerShell

From the repository root, with the existing environment:

```powershell
$venvRoot = Join-Path $env:USERPROFILE "Documents\AI-Lab\environments\aosl"
$pilotDir = Join-Path $env:USERPROFILE ("Documents\AI-Lab\elitebook-runs\ollama-smoke-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
& "$venvRoot\Scripts\python.exe" 05_SRC\experiments\run_ollama_local_scoring.py `
    --input-csv 03_DATA\sample_inputs\aosl_demo_sample_outputs.csv `
    --output-dir "$pilotDir" --limit 1 --dry-run
```

After inspecting that plan, repeat the command without `--dry-run`. A later
five-item integration pilot can use `--limit 5` and a fresh output directory.
Use `--boundary-notes PATH` only when deliberately selecting that guidance;
the default inserts no extra boundary document. No API key is required.

Dry runs read local sources only: no network requests and no writes. Actual runs
refuse any existing output directory, freeze the full input file, and record which
leading rows were selected. Per-row ordinals preserve repeated prompt IDs.
The run saves source snapshots, input and prompt hashes, commit/status, metadata,
model digest/template/parameters, exact requests, raw response bytes, parsed results
and a summary. Invalid responses retain their raw evidence with no invented scores.
Failed runs are retained; choose another fresh directory to retry.

Only localhost or numeric private LAN addresses are accepted; no configured proxy
is used. Cloud-backed models are rejected when identified in server metadata.
This assumes a trusted local Ollama installation, and does not expose any ports.
Tests use simulated server responses; actual model scoring must be verified on the
EliteBook. Test success is an engineering check, not evidence of judge validity.
