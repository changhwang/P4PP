import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.p4pp.gui.app import P4PPApp


class _Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class MeasurementCsvTests(unittest.TestCase):
    def test_smits_factor_is_written_with_notes_columns(self):
        with tempfile.TemporaryDirectory() as output_dir:
            app = SimpleNamespace(
                controller=SimpleNamespace(
                    latest_result=98.1188,
                    latest_raw_result=100.0,
                    latest_std=0.5,
                    cycle_results=[100.0],
                    pos_lin=0,
                    pos_rot=0,
                ),
                control_panel=SimpleNamespace(
                    get_sample_name=lambda: "square_sample",
                    get_save_dir=lambda: output_dir,
                ),
                meas_settings=SimpleNamespace(
                    get_cycles=lambda: 1,
                    shape_var=_Value("Rectangular"),
                    spacing_var=_Value("1.016"),
                    dim1_var=_Value("20"),
                    dim2_var=_Value("20"),
                    get_correction_factor=lambda: 0.981188105562,
                    get_correction_note=lambda: (
                        "Smits finite-square correction (natural cubic spline); "
                        "F=0.981188; d/s=19.685039"
                    ),
                    get_resistor_info=lambda: {
                        "label": "681 ohm",
                        "range": "1 kOhm/sq - 100 kOhm/sq",
                    },
                ),
            )

            P4PPApp._auto_save_csv(app)

            csv_path = next(Path(output_dir).glob("*.csv"))
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))

            settings_header = rows.index(["Setting", "Value", "Notes"])
            summary_header = rows.index(["Metric", "Value", "Notes"])
            self.assertEqual(
                rows[settings_header + 7][0:2],
                ["Smits Geometric Factor F", "0.981188"],
            )
            self.assertIn("d/s=19.685039", rows[settings_header + 7][2])
            self.assertTrue(all(len(row) == 3 for row in rows[summary_header + 1 :]))


if __name__ == "__main__":
    unittest.main()
