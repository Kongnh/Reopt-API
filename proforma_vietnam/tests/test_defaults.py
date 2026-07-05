from unittest import TestCase

from proforma_vietnam.defaults import dppa_regulatory_for_year


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
