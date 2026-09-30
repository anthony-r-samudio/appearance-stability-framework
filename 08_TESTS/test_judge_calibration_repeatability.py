import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "05_SRC/analysis/summarize_judge_calibration.py"
)
spec = importlib.util.spec_from_file_location("calibration_summary", SCRIPT)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class TestCalibrationRepeatability(unittest.TestCase):
    def _report(self, offsets, failed_second_repeat=False):
        rows = []
        for pid, model, baseline in (("stable", "stable", 0.0),
                                     ("flawed", "flawed", 0.4)):
            for repeat, offset in enumerate(offsets, start=1):
                rows.append({
                    "prompt_id": pid,
                    "model_name": model,
                    "calibration_repeat": repeat,
                    "divergence": baseline + offset,
                    "stability_score": 1.0 - baseline - offset,
                    "c1": 0.0,
                    "expected_failure_focus": "c1_factual",
                    "scorer_status": "error" if failed_second_repeat and repeat == 2 else "ok",
                })
        with (
            patch.object(summary, "_load_csv_or_jsonl", return_value=pd.DataFrame(rows)),
            patch.object(summary, "_print_and_write") as write,
        ):
            summary.main()
        return "\n".join(write.call_args.args[0])

    def test_single_successful_repeat_is_not_measurable(self):
        for offsets, failed in (([0.0], False), ([0.0, 0.1], True)):
            with self.subTest(offsets=offsets, failed=failed):
                report = self._report(offsets, failed)
                self.assertIn("Avg prompt-level D std dev  : N/A", report)
                self.assertIn("Repeatability               : not measurable — requires at least 2 repeats", report)
                self.assertIn("Avg prompt repeat std dev       : N/A", report)
                self.assertIn("Max per-prompt constraint drift : N/A", report)
                self.assertIn("| DO_NOT_SCALE_YET |", report)
                self.assertIn("Repeatability is not measurable", report)
                for claim in ("acceptable initial stability", "moderate instability",
                              "high instability", "repeat variance is acceptable"):
                    self.assertNotIn(claim, report)

    def test_multiple_repeats_retain_thresholds(self):
        for offsets, label, verdict in (
            ([0.0, 0.1], "acceptable initial stability", "KEEP_ADV_JUDGE"),
            ([0.0, 0.2], "moderate instability", "DO_NOT_SCALE_YET"),
            ([0.0, 0.4], "high instability", "DO_NOT_SCALE_YET"),
            ([0.0, 0.0, 0.0], "acceptable initial stability", "KEEP_ADV_JUDGE"),
        ):
            with self.subTest(offsets=offsets):
                report = self._report(offsets)
                self.assertIn("Repeatability               : " + label, report)
                self.assertIn("| " + verdict + " |", report)
                self.assertNotIn("not measurable", report)


if __name__ == "__main__":
    unittest.main()
