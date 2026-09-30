import contextlib
import io
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "05_SRC/analysis/compare_gemini_matched_llama_t07.py"
)


class TestMatchedComparisonIntegrity(unittest.TestCase):
    def _run(self, stable_ids, pressured_ids):
        inputs = [
            io.StringIO("prompt_id,divergence\n" + "".join(
                f"{pid},{index / 100 + offset}\n" for index, pid in enumerate(ids)
            ))
            for ids, offset in ((stable_ids, 0), (pressured_ids, 0.2))
        ]
        with (
            patch.object(Path, "open", side_effect=inputs),
            patch.object(Path, "write_text") as write,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            try:
                result = runpy.run_path(str(SCRIPT))
            except RuntimeError:
                write.assert_not_called()
                raise
        write.assert_called_once()
        return result

    def test_duplicate_ids_rejected_in_either_input(self):
        ids = [f"p{i:02}" for i in range(30)]
        for label in ("stable", "pressured"):
            with self.subTest(label=label):
                duplicate = ids[:-1] + [ids[0]]
                with self.assertRaisesRegex(RuntimeError, label + r".*duplicate.*p00"):
                    self._run(duplicate if label == "stable" else ids,
                              duplicate if label == "pressured" else ids)

    def test_mismatched_ids_rejected(self):
        ids = [f"p{i:02}" for i in range(30)]
        with self.assertRaisesRegex(RuntimeError, r"missing.*p29.*extra.*unexpected"):
            self._run(ids, ids[:-1] + ["unexpected"])

    def test_wrong_row_counts_rejected(self):
        ids = [f"p{i:02}" for i in range(30)]
        for count in (29, 31):
            for label in ("stable", "pressured"):
                with self.subTest(count=count, label=label):
                    wrong = [f"p{i:02}" for i in range(count)]
                    with self.assertRaisesRegex(RuntimeError, label + f".*30.*{count}"):
                        self._run(wrong if label == "stable" else ids,
                                  wrong if label == "pressured" else ids)

    def test_valid_pairs_accepted(self):
        ids = [f"p{i:02}" for i in range(30)]
        result = self._run(ids, list(reversed(ids)))
        self.assertEqual(result["ids"], ids)
        self.assertEqual(result["n"], 30)
        self.assertAlmostEqual(result["mean_diff"], 0.2)


if __name__ == "__main__":
    unittest.main()
