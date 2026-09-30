import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "05_SRC/experiments/generate_real_failure_validation_30.py"
)
spec = importlib.util.spec_from_file_location("failure_generator", SCRIPT)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class TestFailureValidationResume(unittest.TestCase):
    def test_resume_replaces_errors_and_preserves_other_rows(self):
        for result in ("retry succeeded", RuntimeError("retry failed"),
                       generator.CreditError("no credits")):
            with self.subTest(result=result), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output_csv = root / "outputs.csv"
                existing = [
                    {"prompt_id": "done", "output_text": "existing success"},
                    {"prompt_id": "retry", "output_text": "[ERROR: old failure]"},
                    {"prompt_id": "retry", "output_text": "[ERROR credit: old failure]"},
                    {"prompt_id": "unrelated", "output_text": "[ERROR: keep me]"},
                ]
                generator._save_csv(existing, output_csv)
                original = generator._load_existing_outputs(output_csv)
                prompts = [
                    {"prompt_id": "done", "prompt_text": "skip this"},
                    {"prompt_id": "retry", "prompt_text": "retry this"},
                ]
                with (
                    patch.object(generator, "_REPO_ROOT", root),
                    patch.object(generator, "_resolve_output_csv", return_value=output_csv),
                    patch.object(generator, "_load_prompts", return_value=prompts),
                    patch.object(generator, "_check_api_key"),
                    patch.object(generator, "generate_response", side_effect=[result]) as generate,
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    generator.main(resume=True)

                generate.assert_called_once_with(
                    model=generator._DEFAULT_MODEL,
                    prompt="retry this",
                    temperature=generator._DEFAULT_TEMP,
                    max_tokens=generator._DEFAULT_MAX_TOKENS,
                )
                rows = generator._load_existing_outputs(output_csv)
                ids = [row["prompt_id"] for row in rows]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(set(ids), {"done", "retry", "unrelated"})
                by_id = {row["prompt_id"]: row for row in rows}
                self.assertEqual(by_id["done"], original[0])
                self.assertEqual(by_id["unrelated"], original[3])
                expected = (
                    f"[ERROR credit: {result}]" if isinstance(result, generator.CreditError)
                    else f"[ERROR: {result}]" if isinstance(result, Exception)
                    else result
                )
                self.assertEqual(by_id["retry"]["output_text"], expected)
                self.assertEqual(
                    "retry" in generator._build_done_set(rows),
                    not isinstance(result, Exception),
                )


if __name__ == "__main__":
    unittest.main()
