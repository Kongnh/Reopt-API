from unittest import TestCase

from proforma_thailand.report import (
    build_thailand_report,
    cash_flow_overrides_from_assumptions,
)

ASSUMPTIONS = {
    "country": "Thailand",
    "local_currency_code": "THB",
    "utility_label": "PEA",
    "time_steps_per_hour": 4,
    "exchange_rate_thb_per_usd": 32.5,
    "vat_rate_fraction": 0.07,
    "power_factor_charge_per_kvar_thb": 56.07,
    "power_factor_allowance_fraction": 0.6197,
    "kvar_max": 664.0,
    "cit_regime": "standard_flat",
    "pv_depreciation_years": 5,
    "direct_ownership": {"enabled": True},
    "placeholder_keys": ["debt_interest_rate"],
    "annual_om_usd": 20000.0,
    "debt_fraction": 0.7,
    "debt_interest_rate_fraction": 0.06,
    "debt_term_years": 10,
}


def _results():
    horizon = 8
    return {
        "inputs": {
            "ElectricTariff": {"tou_energy_rates_per_kwh": [0.1] * horizon},
            "ElectricStorage": {"can_grid_charge": False},
            "Financial": {"analysis_years": 25},
            "ElectricLoad": {},
        },
        "outputs": {
            "PV": {
                "size_kw": 1000.0,
                "annual_energy_produced_kwh": 1_500_000.0,
                "electric_to_load_series_kw": [100.0] * horizon,
            },
            "ElectricStorage": {"size_kw": 0.0, "size_kwh": 0.0},
            "ElectricTariff": {
                "year_one_bill_before_tax": 400000.0,
                "year_one_bill_before_tax_bau": 500000.0,
                "year_one_demand_cost_before_tax": 60000.0,
                "year_one_demand_cost_before_tax_bau": 80000.0,
            },
            "ElectricUtility": {"annual_energy_supplied_kwh": 5_000_000.0},
            "ElectricLoad": {"annual_calculated_kwh": 6_500_000.0},
            "Financial": {},
        },
    }


class ThailandReportTests(TestCase):

    def test_overrides_map_thb_exchange_rate_onto_the_engine_key(self):
        overrides = cash_flow_overrides_from_assumptions(ASSUMPTIONS)

        self.assertEqual(overrides["exchange_rate_vnd_per_usd"], 32.5)

    def test_overrides_carry_the_direct_ownership_block(self):
        overrides = cash_flow_overrides_from_assumptions(ASSUMPTIONS)

        self.assertEqual(overrides["direct_ownership"], {"enabled": True})

    def test_overrides_never_carry_an_esco_discount(self):
        overrides = cash_flow_overrides_from_assumptions(ASSUMPTIONS)

        self.assertNotIn("esco_energy_discount_fraction", overrides)

    def test_workbook_renders_with_thailand_labels(self):
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)

        texts = [
            value
            for worksheet in workbook.worksheets
            for row in worksheet.iter_rows(values_only=True)
            for value in row
            if isinstance(value, str)
        ]

        self.assertTrue(any("THB" in text for text in texts))
        self.assertFalse(any("VND" in text or "EVN" in text for text in texts))

    def test_power_factor_compensation_is_computed_from_billed_demand(self):
        assumptions = dict(ASSUMPTIONS, billed_demand_kw=800.0)

        _, extras = build_thailand_report(_results(), assumptions)

        self.assertAlmostEqual(
            extras["power_factor_compensation_kvar"],
            664.0 - 0.6197 * 800.0,
            places=3,
        )

    def test_no_compensation_needed_when_demand_stays_high(self):
        assumptions = dict(ASSUMPTIONS, billed_demand_kw=1368.0)

        _, extras = build_thailand_report(_results(), assumptions)

        self.assertEqual(extras["power_factor_compensation_kvar"], 0.0)
        self.assertEqual(extras["power_factor_mitigation_cost_usd"], 0.0)

    def test_placeholder_guard_passes_because_markers_are_rendered(self):
        from proforma_vietnam.validate_workbook import (
            validate_no_unmarked_placeholders,
        )
        from proforma_thailand.defaults import PLACEHOLDER_MARKER

        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)

        self.assertEqual(
            validate_no_unmarked_placeholders(
                workbook, PLACEHOLDER_MARKER, ("IRR", "NPV", "Payback")
            ),
            [],
        )
