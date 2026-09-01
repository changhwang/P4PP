import unittest

from src.p4pp.gui.components.measurement_settings_panel import (
    correction_factor,
    correction_factor_square,
)


class SmitsCorrectionFactorTests(unittest.TestCase):
    def test_square_table_value_at_d_over_s_10(self):
        self.assertAlmostEqual(correction_factor_square(10.0), 0.9313, places=7)

    def test_20_mm_square_with_40_mil_probe_spacing(self):
        factor = correction_factor(20.0, 20.0, 1.016)
        self.assertAlmostEqual(factor, 0.9812, delta=0.00005)
        relative_difference = abs(factor - 0.98138) / 0.98138
        self.assertLessEqual(relative_difference, 0.0002)

    def test_factor_remains_physical_for_large_samples(self):
        for d_over_s in (20.0, 40.0, 80.0, 1_000_000.0):
            factor = correction_factor_square(d_over_s)
            self.assertGreater(factor, 0.0)
            self.assertLessEqual(factor, 1.0)
        self.assertLess(correction_factor_square(80.0), 1.0)


if __name__ == "__main__":
    unittest.main()
