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
