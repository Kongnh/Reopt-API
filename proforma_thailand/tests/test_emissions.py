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


class LevelizationIsUndoneBeforeDegradingTests(TestCase):
    """The sixth site of the levelization defect, and the one that reached the
    client memo as a headline number.

    annual_avoided_tco2e was computed from load minus grid supply. Load carries
    no levelization but the grid figure is load minus a levelized PV
    contribution, so the DIFFERENCE was levelized. lifetime_avoided_tco2e then
    applied (1 - deg)^y on top of it, counting degradation twice and
    understating avoided emissions by about 3.6 percent.

    Reconstructing the shipped figure proved it: 1058.02 tCO2e annual over 20
    years came to exactly 20184.85, which matches a 0.005 degradation series to
    the decimal and cannot be reached without the double count.
    """

    def test_the_avoided_energy_is_de_levelized(self):
        # 1,000,000 kWh avoided on a levelized basis, lambda 0.95, factor 0.5
        # kg/kWh, so the true first year is 1e6/0.95 kWh and 526.32 tonnes.
        result = annual_avoided_tco2e(
            annual_load_kwh=3_000_000.0,
            annual_grid_kwh=2_000_000.0,
            grid_emission_factor_kg_per_kwh=0.5,
            levelization_factor=0.95,
        )

        self.assertAlmostEqual(result, (1_000_000.0 / 0.95) * 0.5 / 1000.0, places=6)

    def test_a_factor_of_one_changes_nothing(self):
        without = annual_avoided_tco2e(3_000_000.0, 2_000_000.0, 0.5)
        with_one = annual_avoided_tco2e(3_000_000.0, 2_000_000.0, 0.5, 1.0)

        self.assertEqual(without, with_one)
        self.assertAlmostEqual(without, 500.0, places=6)

    def test_lifetime_no_longer_double_counts(self):
        """Annual is now a true first year, so applying degradation across the
        term is correct rather than a second application of it."""
        annual = annual_avoided_tco2e(
            3_000_000.0, 2_000_000.0, 0.5, levelization_factor=0.95
        )
        lifetime = lifetime_avoided_tco2e(annual, 20, 0.005)

        expected = sum(annual * (1 - 0.005) ** y for y in range(20))
        self.assertAlmostEqual(lifetime, expected, places=6)
        self.assertGreater(lifetime, 20 * annual * 0.94)
