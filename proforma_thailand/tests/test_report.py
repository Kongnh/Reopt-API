from unittest import TestCase

from proforma_thailand.report import (
    annual_opex_usd,
    build_thailand_report,
    cash_flow_overrides_from_assumptions,
)

ASSUMPTIONS = {
    # build_thailand_case sets these; the fixture must match production
    # or the provenance test passes or fails for the wrong reason.
    "case_name": "Thailand DIRECT_OWNERSHIP Case",
    "cit_regime": "standard_flat",
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
    "annual_om_usd": None,
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


class BilledDemandTests(TestCase):

    def _results(self, periods, series):
        return {
            "inputs": {"ElectricTariff": {
                "coincident_peak_load_active_time_steps": periods}},
            "outputs": {"ElectricUtility": {"electric_to_load_series_kw": series}},
        }

    def test_peak_is_taken_over_each_periods_one_based_steps(self):
        from proforma_thailand.report import billed_demand_kw_by_month

        # step 2 -> series[1] = 50.0; step 4 -> series[3] = 90.0
        result = billed_demand_kw_by_month(
            self._results([[1, 2], [3, 4]], [10.0, 50.0, 20.0, 90.0])
        )

        self.assertEqual(result, [50.0, 90.0])

    def test_missing_series_yields_no_months_rather_than_zeros(self):
        from proforma_thailand.report import billed_demand_kw_by_month

        self.assertEqual(billed_demand_kw_by_month(self._results([[1]], [])), [])

    def _results_with_storage(self, periods, to_load, to_storage):
        return {
            "inputs": {"ElectricTariff": {
                "coincident_peak_load_active_time_steps": periods}},
            "outputs": {"ElectricUtility": {
                "electric_to_load_series_kw": to_load,
                "electric_to_storage_series_kw": to_storage,
            }},
        }

    def test_grid_charging_raises_only_its_own_month(self):
        from proforma_thailand.report import billed_demand_kw_by_month

        # Month 1 (steps 1-2): grid charging in step 1 raises peak to 500.
        # Month 2 (steps 3-4): no charging, peak is 250, unaffected by month 1.
        # Proves the summation is scoped per month, not leaked across boundaries.
        results = self._results_with_storage(
            [[1, 2], [3, 4]],
            [100.0, 120.0, 200.0, 250.0],
            [400.0, 0.0, 0.0, 0.0]
        )
        self.assertEqual(billed_demand_kw_by_month(results), [500.0, 250.0])

    def test_grid_charging_can_set_the_peak(self):
        from proforma_thailand.report import billed_demand_kw_by_month

        results = self._results_with_storage(
            [[1, 2]], [100.0, 120.0], [400.0, 0.0]
        )
        self.assertEqual(billed_demand_kw_by_month(results), [500.0])

    def test_absent_storage_series_is_treated_as_zeros(self):
        from proforma_thailand.report import billed_demand_kw_by_month

        results = self._results_with_storage([[1, 2]], [100.0, 120.0], [])
        self.assertEqual(billed_demand_kw_by_month(results), [120.0])

    def test_short_storage_series_degrades_to_zero_for_trailing_steps(self):
        from proforma_thailand.report import billed_demand_kw_by_month

        # Storage series shorter than load series: trailing steps default to zero.
        # Step 1: load 100 + storage 50 = 150. Step 2: load 120 + storage 0 = 120.
        # Peak is 150. Verifies no IndexError and earlier steps still add correctly.
        results = self._results_with_storage([[1, 2, 3]], [100.0, 120.0, 150.0], [50.0])
        self.assertEqual(billed_demand_kw_by_month(results), [150.0])


class NoVietnamProvenanceTests(TestCase):
    """A Thai client must not be told its tax is governed by Vietnamese law.

    The existing label test only bans the uppercase tokens VND and EVN, which
    is why a workbook titled "Vietnam ESCO / DPPA Case" citing Circular
    45/2013/TT-BTC shipped past it.
    """

    # Lowercase module paths like proforma_vietnam.cash_flow are accurate
    # engineering provenance (the engine IS that module) and are not a claim
    # about the client's country, so they are deliberately not banned.
    BANNED = (
        "Vietnam", "vietnam_defaults", "VND", "EVN",
        "Circular 45", "Circular 78", "Law 67", "QH15",
        "Decree 320", "ND57", "Decision 988", "QD963", "DPPA",
    )

    def _cells(self, workbook):
        for worksheet in workbook.worksheets:
            for row in worksheet.iter_rows(values_only=True):
                for value in row:
                    if isinstance(value, str):
                        yield worksheet.title, value

    def test_no_vietnam_specific_token_reaches_a_thailand_workbook(self):
        assumptions = dict(ASSUMPTIONS, cit_regime="standard_flat")
        workbook, _ = build_thailand_report(_results(), assumptions)

        offenders = [
            (sheet, token, text[:70])
            for sheet, text in self._cells(workbook)
            for token in self.BANNED
            if token in text
        ]

        self.assertEqual(
            offenders, [],
            "Vietnam provenance leaked into the Thailand workbook: {}".format(
                offenders[:8]
            ),
        )


class DepreciationAndInverterReplacementTests(TestCase):

    def test_bess_life_is_passed_through(self):
        overrides = cash_flow_overrides_from_assumptions(
            dict(ASSUMPTIONS, bess_depreciation_years=5)
        )
        self.assertEqual(overrides["bess_depreciation_years"], 5)

    def test_inverter_replacement_lands_in_the_right_year(self):
        overrides = cash_flow_overrides_from_assumptions(dict(
            ASSUMPTIONS,
            inverter_replacement_year=11,
            inverter_replacement_cost_usd=118_000.0,
        ))
        series = overrides["extra_replacement_costs_by_year"]
        self.assertEqual(len(series), 11)
        self.assertEqual(series[10], 118_000.0)
        self.assertEqual(sum(series[:10]), 0.0)

    def test_no_inverter_replacement_emits_no_series(self):
        overrides = cash_flow_overrides_from_assumptions(dict(ASSUMPTIONS))
        self.assertNotIn("extra_replacement_costs_by_year", overrides)

    def test_cit_rate_is_passed_through(self):
        overrides = cash_flow_overrides_from_assumptions(
            dict(ASSUMPTIONS, cit_standard_rate=0.20)
        )
        self.assertAlmostEqual(overrides["cit_standard_rate"], 0.20)

    def test_inverter_replacement_does_not_displace_a_battery_replacement(self):
        # extra_replacement_costs_by_year is merged ADDITIVELY onto the battery
        # schedule (proforma_vietnam/esco_pro_forma.py:_merge_replacement_costs).
        # A wholesale override would silently zero out the battery cost, so this
        # checks the full merged series rather than just the inverter value.
        from proforma_vietnam.esco_pro_forma import (
            calculate_esco_pro_forma_from_reopt_results,
        )

        results = _results()
        results["inputs"]["ElectricStorage"] = {
            "can_grid_charge": False,
            "battery_replacement_year": 10,
            "replace_cost_per_kw": 100.0,
            "replace_cost_per_kwh": 80.0,
        }
        results["outputs"]["ElectricStorage"] = {"size_kw": 200.0, "size_kwh": 400.0}
        # battery replacement cost = 200*100 + 400*80 = 52,000

        assumptions = dict(
            ASSUMPTIONS,
            inverter_replacement_year=11,
            inverter_replacement_cost_usd=118_000.0,
        )
        overrides = cash_flow_overrides_from_assumptions(assumptions)

        cash_flow_result = calculate_esco_pro_forma_from_reopt_results(
            results,
            esco_energy_discount_fraction=0.0,
            **overrides
        )

        series = cash_flow_result["derivation"]["replacement_costs_by_year_usd"]
        self.assertEqual(series[9], 52_000.0)
        self.assertEqual(series[10], 118_000.0)


class InsuranceTests(TestCase):

    def test_insurance_is_a_fraction_of_total_installed_capex(self):
        # 0.5 percent of 1,200,000 is 6,000, on top of 20,000 of O&M.
        self.assertAlmostEqual(
            annual_opex_usd(1_000_000.0, 150_000.0, 50_000.0, 20_000.0, 0.005),
            26_000.0,
        )

    def test_zero_rate_leaves_om_untouched(self):
        self.assertAlmostEqual(
            annual_opex_usd(1_000_000.0, 0.0, 0.0, 20_000.0, 0.0),
            20_000.0,
        )

    def test_none_rate_is_treated_as_zero(self):
        self.assertAlmostEqual(
            annual_opex_usd(1_000_000.0, 0.0, 0.0, 20_000.0, None),
            20_000.0,
        )


class InsuranceReachesTheEngineTests(TestCase):
    """Task 4 Finding 1: production never sets annual_om_usd (case_builder.py
    always leaves it None), so annual_opex_usd() passing in isolation proves
    nothing about whether the premium actually reaches the cash-flow engine.
    This drives the real build_thailand_report entry point at that exact
    production shape and reads the number the engine derived, off the
    workbook's OM_YEAR1 named cell (audit_sheets.write_assumptions_sheet
    sources it from cash_flow_result["derivation"]["annual_om_year1_usd"]).
    """

    def _results_with_capex(self):
        # PV/BESS capex and REopt's own year-one O&M: the inputs
        # annual_opex_usd's insurance base and the fallback O&M read from.
        # PVOutputs has no initial_capital_cost field in production (a field
        # that name only exists on ElectricStorageOutputs), so the fixture
        # mirrors the real shape: size_kw * installed_cost_per_kw = capex,
        # not a fabricated initial_capital_cost key on PV. ElectricStorage
        # genuinely carries initial_capital_cost, so that one stays as-is.
        results = _results()
        results["outputs"]["PV"]["installed_cost_per_kw"] = 1_000.0
        results["outputs"]["ElectricStorage"]["initial_capital_cost"] = 150_000.0
        results["outputs"]["Financial"] = {"year_one_om_costs_before_tax": 20_000.0}
        return results

    def _om_year1_from_workbook(self, workbook):
        defined_name = workbook.defined_names["OM_YEAR1"]
        sheet_title, coordinate = next(iter(defined_name.destinations))
        return workbook[sheet_title][coordinate].value

    def test_insurance_premium_reaches_the_engine_when_annual_om_usd_is_unset(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of

        self.assertIsNone(ASSUMPTIONS["annual_om_usd"])  # the production shape
        workbook, _ = build_thailand_report(self._results_with_capex(), ASSUMPTIONS)

        insurance_rate = value_of(FINANCIAL_DEFAULTS, "insurance_rate_fraction")
        expected = annual_opex_usd(
            1_000_000.0, 150_000.0, 0.0, 20_000.0, insurance_rate,
        )
        # Exact, not >=: proves the premium landed, not merely that O&M is
        # nonzero (which the pre-fix REopt fallback alone would also give).
        self.assertAlmostEqual(self._om_year1_from_workbook(workbook), expected)
        self.assertNotAlmostEqual(expected, 20_000.0)
