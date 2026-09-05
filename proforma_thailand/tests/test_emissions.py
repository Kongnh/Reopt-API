"""Scope 2 avoided emissions, computed in-house from a cited Thai grid factor."""

from unittest import TestCase

from proforma_thailand.emissions import (
    annual_avoided_tco2e,
    lifetime_avoided_tco2e,
)


class AnnualAvoidedTests(TestCase):

    def test_avoided_energy_times_factor_in_tonnes(self):
        # 2,000,000 kWh avoided at 0.5 kg/kWh is 1,000,000 kg, so 1,000 tonnes.
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 5_000_000.0, 0.5), 1000.0
        )

    def test_no_offset_avoids_nothing(self):
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 7_000_000.0, 0.5), 0.0
        )

    def test_grid_above_load_cannot_produce_a_negative_claim(self):
        """Battery grid-charging can push grid import above load. Claim zero, never less."""
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 7_200_000.0, 0.5), 0.0
        )

    def test_missing_factor_yields_zero(self):
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 5_000_000.0, None), 0.0
        )


class LifetimeAvoidedTests(TestCase):

    def test_no_degradation_is_a_flat_multiple(self):
        self.assertAlmostEqual(lifetime_avoided_tco2e(100.0, 3, 0.0), 300.0)

    def test_degradation_reduces_later_years(self):
        # Year 1 = 100, year 2 = 99, year 3 = 98.01.
        self.assertAlmostEqual(
            lifetime_avoided_tco2e(100.0, 3, 0.01), 297.01, places=2
        )

    def test_zero_years_avoids_nothing(self):
        self.assertAlmostEqual(lifetime_avoided_tco2e(100.0, 0, 0.01), 0.0)
