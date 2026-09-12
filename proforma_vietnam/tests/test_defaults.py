from unittest import TestCase

from proforma_vietnam.defaults import (
    SURPLUS_EXPORT_DEFAULTS,
    dppa_regulatory_for_year,
    surplus_export_price_vnd_per_kwh,
)


class DppaRegulatoryForYearTests(TestCase):

    def test_resolves_year_after_latest_vintage_to_latest_vintage(self):
        vintage_year, values = dppa_regulatory_for_year(2026)

        self.assertEqual(vintage_year, 2025)
        self.assertEqual(values["transmission_loss_factor_k"], 1.026)
        self.assertEqual(
            values["distribution_loss_factor_kpp_by_voltage"],
            {"110kv_and_above": 1.008525, "22_to_110kv": 1.027263},
        )
        self.assertEqual(values["c_dppa_service_fee_vnd_per_kwh"], 360.0)
        self.assertEqual(values["c_cl_settlement_adder_vnd_per_kwh"], 163.3)

    def test_raises_for_year_before_earliest_vintage(self):
        with self.assertRaises(ValueError) as context:
            dppa_regulatory_for_year(2024)

        self.assertIn("2024", str(context.exception))


class SurplusExportDefaultsTests(TestCase):

    def test_cap_fraction_of_output(self):
        self.assertEqual(SURPLUS_EXPORT_DEFAULTS["cap_fraction_of_output"], 0.50)

    def test_regional_price_ceilings(self):
        self.assertEqual(
            SURPLUS_EXPORT_DEFAULTS["price_ceiling_vnd_per_kwh_by_region"],
            {"north": 1382.7, "central": 1107.1, "south": 1012.0},
        )


class SurplusExportPriceVndPerKwhTests(TestCase):

    def test_south_ceiling_binds(self):
        self.assertEqual(surplus_export_price_vnd_per_kwh("south"), 1012.0)

    def test_north_ceiling_binds(self):
        self.assertEqual(surplus_export_price_vnd_per_kwh("north"), 1382.7)

    def test_region_lookup_is_case_insensitive(self):
        self.assertEqual(surplus_export_price_vnd_per_kwh("SOUTH"), 1012.0)
        self.assertEqual(surplus_export_price_vnd_per_kwh("North"), 1382.7)

    def test_unknown_region_raises(self):
        with self.assertRaises(ValueError) as context:
            surplus_export_price_vnd_per_kwh("east")

        self.assertIn("east", str(context.exception))


class ReplacementPolicyTests(TestCase):
    """The rule both countries book. Numbers here are the 2026-09-11 rulings;
    a change to any of them is a change to both countries' deliverables."""

    def test_policy_constants(self):
        from proforma_vietnam import defaults

        self.assertEqual(defaults.PROJECT_YEARS, 20)
        # 2026-09-12: replacement is an opt-in; the schedule survives for cases that opt in.
        self.assertFalse(defaults.BESS_REPLACEMENT_ENABLED)
        self.assertEqual(defaults.BESS_REPLACEMENT_YEAR, 10)
        self.assertEqual(defaults.BESS_REPLACE_FRACTION_OF_INSTALL, 1.0)
        self.assertEqual(defaults.PV_INVERTER_REPLACEMENT_YEAR, 11)
        self.assertEqual(defaults.PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX, 0.10)

    def test_battery_ageing_constants(self):
        from proforma_vietnam import defaults

        self.assertEqual(defaults.BESS_CYCLE_LIFE_EFC, 8000)
        self.assertEqual(defaults.BESS_END_OF_LIFE_SOH, 0.80)
        self.assertAlmostEqual(defaults.BESS_CALENDAR_FADE_COEFFICIENT, 1.16e-3)
        self.assertAlmostEqual(defaults.BESS_CALENDAR_FADE_EXPONENT, 0.428)

    def test_vietnam_horizon_matches_the_policy(self):
        from proforma_vietnam.defaults import FINANCIAL_DEFAULTS, PROJECT_YEARS

        self.assertEqual(FINANCIAL_DEFAULTS["project_years"], PROJECT_YEARS)

    def test_a_desynced_horizon_fails_at_import(self):
        from proforma_vietnam import defaults

        original = defaults.FINANCIAL_DEFAULTS["project_years"]
        defaults.FINANCIAL_DEFAULTS["project_years"] = 25
        try:
            with self.assertRaises(ValueError):
                defaults._assert_policy_holds()
        finally:
            defaults.FINANCIAL_DEFAULTS["project_years"] = original
