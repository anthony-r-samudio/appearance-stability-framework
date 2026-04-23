import os
import tempfile
import unittest

from AOSL.constraints import CONSTRAINTS
from AOSL.scoring import (
    load_from_json,
    make_scored_output,
    save_to_json,
    to_dict,
    to_flat_row,
    validate_output,
)


class TestScoringSmoke(unittest.TestCase):

    def _make_canonical_scores(self):
        return {c.code: 1.0 for c in CONSTRAINTS}

    def _make_output(self):
        return make_scored_output(
            prompt_id="smoke-001",
            model_name="test-model",
            output_text="Smoke test output.",
            constraint_scores=self._make_canonical_scores(),
            notes="Smoke test.",
        )

    def test_make_and_validate_output(self):
        output = self._make_output()
        result = validate_output(output)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.unknown_codes, set())
        self.assertEqual(result.missing_codes, set())
        self.assertEqual(result.out_of_range_scores, {})

    def test_to_dict_contains_expected_keys(self):
        output = self._make_output()
        d = to_dict(output)
        for key in ("prompt_id", "model_name", "output_text", "constraint_scores", "notes"):
            self.assertIn(key, d)

    def test_to_flat_row_contains_constraint_codes(self):
        output = self._make_output()
        row = to_flat_row(output)
        for constraint in CONSTRAINTS:
            self.assertIn(constraint.code, row)

    def test_save_and_load_json_roundtrip(self):
        output = self._make_output()
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        try:
            save_to_json(output, tmp.name)
            loaded = load_from_json(tmp.name)
            self.assertEqual(loaded, output)
        finally:
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
