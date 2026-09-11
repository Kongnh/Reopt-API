import unicodedata
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
    "bess_depreciation_years": 5,
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

    def test_technical_results_labels_the_rows_as_year_one(self):
        # Important 8 / Ruling 23: REopt's year_one_bill_before_tax and
        # electric_to_load_series_kw are already levelized across the 25-year
        # horizon, not a true undegraded first year, so these Technical
        # These headers used to read "Levelized Annual" because the figures
        # under them carried REopt's escalation/discount/degradation weighting.
        # The de-levelization work of 2026-09-08/09 removed that weighting from
        # the dispatch series, the tariff comparison and the emissions basis, so
        # they are now a true first year and the old headers would misdescribe
        # them in the opposite direction. The assertion is inverted rather than
        # deleted: it still guards against a header that lies about its basis.
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)
        sheet = workbook["Technical Results"]

        titles = [
            value for row in sheet.iter_rows(values_only=True)
            for value in row if isinstance(value, str)
        ]

        self.assertIn("Annual Energy Balance (Year 1)", titles)
        self.assertIn("Year-1 Utility Bill Comparison", titles)
        self.assertNotIn("Annual Energy Balance (Levelized Annual)", titles)
        self.assertNotIn("Levelized Annual Utility Bill Comparison", titles)

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


def _results_with_replacements():
    """A results fixture that exercises every conditionally-gated Model Basis
    block (Critical 1, hole 2 in the provenance guard): the stock ``_results()``
    fixture leaves PV ``installed_cost_per_kw`` unset, so ``_pv_capex`` is 0.0,
    no inverter replacement is ever booked, ``derivation["battery_replacement"]``
    is falsy, and the entire capitalized-replacement disclosure -- the one
    citing the depreciation authority and BESS life -- never rendered under
    test. This fixture gives PV a real capex and a battery so both replacement
    paths (which merge additively, see esco_pro_forma._merge_replacement_costs)
    actually populate ``derivation["battery_replacement"]``.
    """
    results = _results()
    results["outputs"]["PV"]["installed_cost_per_kw"] = 1_000.0
    results["outputs"]["ElectricStorage"] = {
        "size_kw": 200.0,
        "size_kwh": 400.0,
        "can_grid_charge": False,
        "battery_replacement_year": 10,
        "replace_cost_per_kw": 100.0,
        "replace_cost_per_kwh": 80.0,
    }
    return results


# The shared replacement policy as case_builder.py records it (year 11, 10
# percent of PV capex); the shared core derives the cost from the fixture's
# own solved PV capex.
PROVENANCE_ASSUMPTIONS = dict(
    ASSUMPTIONS,
    pv_inverter_replacement_year=11,
    pv_inverter_replacement_fraction_of_pv_capex=0.10,
)


class NoVietnamProvenanceTests(TestCase):
    """A Thai client must not be told its tax is governed by Vietnamese law.

    The original label test banned only the title-case token "Vietnam", which
    is why a Pro Forma (Audit) section header reading "DEPRECIATION & VIETNAM
    CIT (USD)" (all caps) shipped past it. Matching is now case-insensitive
    (see the ``.lower()`` comparison below) so an all-caps or all-lowercase
    slip is caught the same as title case.
    """

    # Lowercase module paths like proforma_vietnam.cash_flow are accurate
    # engineering provenance (the engine IS that module) and are not a claim
    # about the client's country, so they are deliberately not banned.
    #
    # QĐ963 (U+0110 Đ) and Điều are the Unicode tokens the render actually
    # uses -- an ASCII "QD963" banned string never matches "QĐ963" and let a
    # Vietnamese TOU citation past the old guard on a Thai workbook. NĐ-CP and
    # VAS were both missing outright. Matching below is additionally done
    # after Unicode NFC normalisation (see _normalized), which is the more
    # durable fix the review asked us to weigh -- it catches an NFD-decomposed
    # rendering of any of these tokens without having to enumerate variants.
    BANNED = (
        "Vietnam", "vietnam_defaults", "VND", "EVN",
        "Circular 45", "Circular 78", "Law 67", "QH15",
        "Decree 320", "ND57", "Decision 988", "QD963", "DPPA",
        "QĐ963", "NĐ-CP", "VAS", "Điều",
        # PPA is a substring of DPPA, so it also catches every existing DPPA
        # match; the reason to ban it separately is a bare "PPA" (Important 6:
        # "Investment & PPA Negotiation Summary" on a direct-ownership title,
        # which has no DPPA anywhere near it). Every non-DPPA PPA mention in
        # proforma_vietnam is gated on the physical-DPPA structure, which a
        # Thailand DIRECT_OWNERSHIP case can never hit, so this is safe.
        "PPA",
    )

    # Case-insensitive matching also catches BANNED tokens embedded inside the
    # engineering-provenance strings the class docstring already exempts.
    # Each entry below was checked against the real Thailand workbook and
    # confirmed accurate, not a country leak:
    #  - "proforma_vietnam" is the shared engine's real, importable package
    #    name for both countries -- it appears in the cover-sheet credit
    #    line, the CLI "regenerate offline" command, and Assumptions-sheet
    #    "source" annotations that name the Python module which derived the
    #    value. Renaming the package per-country is out of scope here and
    #    would not change what a Thai client's numbers are actually worth.
    #  - "evn_energy_escalation_rate" / "evn_capacity_escalation_rate" are the
    #    literal case.json keys Thailand's own case_builder.py writes for a
    #    Thai case (proforma_thailand/case_builder.py:231-234) -- the shared
    #    engine never renamed these keys per country, so citing them by their
    #    real name is accurate provenance, not a Vietnam leak. (Contrast with
    #    the exchange-rate key, which Thailand's case.json genuinely calls
    #    exchange_rate_thb_per_usd -- that source annotation was hardcoded to
    #    the Vietnam name and has been fixed to use profile.local_currency_code.)
    ALLOWED_SUBSTRINGS = (
        "proforma_vietnam",
        "evn_energy_escalation_rate",
        "evn_capacity_escalation_rate",
    )

    def _cells(self, workbook):
        for worksheet in workbook.worksheets:
            for row in worksheet.iter_rows(values_only=True):
                for value in row:
                    if isinstance(value, str):
                        yield worksheet.title, value

    def _normalized(self, text):
        # NFC normalisation: the more durable half of the Critical 1 fix. A
        # BANNED token and the rendered cell could in principle each be a
        # different Unicode normal form (e.g. an NFD-decomposed "Đ" as "D" +
        # combining stroke) and still look identical on screen while failing
        # a naive substring match. Normalising both sides to NFC first means
        # that can never silently defeat the guard.
        return unicodedata.normalize("NFC", text).lower()

    def _unmasked(self, text):
        # Per-match masking (Critical 1, hole 2): the old check exempted the
        # WHOLE cell if an allowed substring appeared anywhere in it, so an
        # allowed phrase could hide an unrelated banned token elsewhere in the
        # same cell. Stripping only the allowed substrings out first means a
        # banned token elsewhere in the cell is still caught.
        stripped = text
        for allowed in self.ALLOWED_SUBSTRINGS:
            stripped = stripped.replace(allowed, "")
        return stripped

    def test_no_vietnam_specific_token_reaches_a_thailand_workbook(self):
        assumptions = dict(PROVENANCE_ASSUMPTIONS, cit_regime="standard_flat")
        workbook, _ = build_thailand_report(_results_with_replacements(), assumptions)

        cells = list(self._cells(workbook))
        all_text = " ".join(text for _, text in cells)

        # Prove the fixture actually exercises the previously-invisible blocks
        # rather than passing vacuously (the review's explicit ask): the
        # capitalized-replacement disclosure only renders when
        # derivation["battery_replacement"] is truthy, which requires a
        # nonzero PV capex driving an inverter replacement, a real battery, or
        # both -- exactly what _results_with_replacements() now provides.
        self.assertIn("CAPITALIZED, not expensed", all_text)

        # Critical 1 was a hardcoded "8-year BESS class life" citing Vietnamese
        # law on Thai workbooks; the fix drives the stated life from
        # derivation["bess_depreciation_years"], which PROVENANCE_ASSUMPTIONS
        # must set to Thailand's actual 5 (case_builder.py:241) for this to be
        # a real proof rather than a fixture that happens to dodge the number
        # entirely. Assert the rendered life directly so a regression back to
        # a hardcoded 8 fails the suite instead of passing silently.
        self.assertIn("5-year BESS class life", all_text)
        self.assertNotIn("8-year BESS class life", all_text)

        offenders = [
            (sheet, token, text[:70])
            for sheet, text in cells
            for token in self.BANNED
            if self._normalized(token) in self._normalized(self._unmasked(text))
        ]

        self.assertEqual(
            offenders, [],
            "Vietnam provenance leaked into the Thailand workbook: {}".format(
                offenders[:8]
            ),
        )


class DirectOwnershipLabelTests(TestCase):
    """Positive assertions for the label fixes in Critical 2 and Important 6/9,
    complementing NoVietnamProvenanceTests' negative (banned-token) checks.
    """

    def test_sheet_is_named_owner_returns_not_developer_returns(self):
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)
        self.assertIn("Owner Returns", workbook.sheetnames)
        self.assertNotIn("Developer Returns", workbook.sheetnames)

    def test_executive_summary_title_has_no_ppa_negotiation_language(self):
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)
        title = workbook["Executive Summary"]["B1"].value
        self.assertIn("Investment Summary", title)
        self.assertNotIn("PPA", title)

    def test_replacement_row_is_not_labelled_a_battery(self):
        # case_1-shaped: PV capex + inverter replacement, ZERO battery -- the
        # exact scenario Critical 2 found labelled "Battery replacement".
        results = _results()
        results["outputs"]["PV"]["installed_cost_per_kw"] = 1_000.0
        assumptions = dict(
            ASSUMPTIONS,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )
        workbook, _ = build_thailand_report(results, assumptions)
        sheet = workbook["Pro Forma (Audit)"]

        labels = [
            value for row in sheet.iter_rows(values_only=True)
            for value in row if isinstance(value, str)
        ]
        self.assertIn("Equipment replacement (engine schedule)", labels)
        self.assertNotIn("Battery replacement (engine schedule)", labels)

    def test_year1_om_row_discloses_the_insurance_component(self):
        results = _results()
        results["outputs"]["PV"]["installed_cost_per_kw"] = 1_000.0
        results["outputs"]["Financial"] = {"year_one_om_costs_before_tax": 20_000.0}
        workbook, _ = build_thailand_report(results, ASSUMPTIONS)
        sheet = workbook["Assumptions"]

        labels = [
            value for row in sheet.iter_rows(values_only=True)
            for value in row if isinstance(value, str)
        ]
        self.assertIn("Year-1 operating cost (O&M + insurance)", labels)
        self.assertNotIn("Year-1 O&M", labels)

    def test_npv_and_payback_are_labelled_as_equity_figures(self):
        # Important 3: both figures are computed off the equity cash flows,
        # not the Total Investment row three lines above them.
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)
        for sheet_name in ("Executive Summary", "Owner Returns"):
            labels = [
                value for row in workbook[sheet_name].iter_rows(values_only=True)
                for value in row if isinstance(value, str)
            ]
            self.assertIn("Equity NPV (USD)", labels)
            self.assertIn("Simple Equity Payback (Years)", labels)
            self.assertNotIn("NPV (USD)", labels)
            self.assertNotIn("Simple Payback (Years)", labels)


class NoEscoLanguageTests(TestCase):

    def test_direct_ownership_workbook_has_no_esco_contract_rows(self):
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for value in row:
                    if isinstance(value, str):
                        self.assertNotIn("ESCO Energy Price", value)
                        self.assertNotIn("Demand Savings Share to ESCO", value)
                        self.assertNotIn("Developer (Seller) Returns", value)


class DepreciationAndInverterReplacementTests(TestCase):

    def test_bess_life_is_passed_through(self):
        overrides = cash_flow_overrides_from_assumptions(
            dict(ASSUMPTIONS, bess_depreciation_years=5)
        )
        self.assertEqual(overrides["bess_depreciation_years"], 5)

    def test_pv_inverter_policy_is_passed_to_the_core(self):
        overrides = cash_flow_overrides_from_assumptions(dict(
            ASSUMPTIONS,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        ))
        self.assertEqual(overrides["pv_inverter_replacement_year"], 11)
        self.assertEqual(overrides["pv_inverter_replacement_fraction_of_pv_capex"], 0.10)
        # The report layer no longer builds the series itself.
        self.assertNotIn("extra_replacement_costs_by_year", overrides)

    def test_no_pv_inverter_policy_emits_no_keys(self):
        overrides = cash_flow_overrides_from_assumptions(dict(ASSUMPTIONS))
        self.assertNotIn("pv_inverter_replacement_year", overrides)
        self.assertNotIn("pv_inverter_replacement_fraction_of_pv_capex", overrides)
        self.assertNotIn("extra_replacement_costs_by_year", overrides)

    def test_cit_rate_is_passed_through(self):
        overrides = cash_flow_overrides_from_assumptions(
            dict(ASSUMPTIONS, cit_standard_rate=0.20)
        )
        self.assertAlmostEqual(overrides["cit_standard_rate"], 0.20)

    def test_inverter_replacement_does_not_displace_a_battery_replacement(self):
        # The PV inverter event is merged ADDITIVELY onto the battery schedule
        # (proforma_vietnam/esco_pro_forma.py:_merge_replacement_costs). A
        # wholesale override would silently zero out the battery cost, so this
        # checks the full merged series rather than just the inverter value.
        from proforma_vietnam.esco_pro_forma import (
            calculate_esco_pro_forma_from_reopt_results,
        )

        results = _results()
        # 1000 kW x 1180 USD/kW x 0.10 = 118,000 for the PV inverter.
        results["outputs"]["PV"]["installed_cost_per_kw"] = 1180.0
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
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
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


class NoReoptEmissionsOutputTests(TestCase):
    """Task 14 Finding 4: Scope 2 is computed in-house in emissions.py because
    REopt's own AVERT/Cambium/EASIUR emissions figures are US datasets, always
    zero outside the US, and must never be quoted to the client. Nothing
    before this test asserted those figures stay out of the workbook.
    """

    BANNED_DATASET_NAMES = ("AVERT", "Cambium", "EASIUR")
    REOPT_EMISSIONS_SENTINEL = 918273.0

    def test_no_reopt_emissions_dataset_name_or_value_reaches_the_workbook(self):
        results = _results()
        # A distinctive non-zero sentinel: the real case's own AVERT/Cambium
        # output fields are all 0.0 (a US-only dataset outside the US), so
        # asserting "0.0 does not appear" would pass vacuously. This proves
        # the wiring never reads these fields at all, not merely that they
        # happen to be zero today.
        results["outputs"]["Site"] = dict(
            results["outputs"].get("Site") or {},
            annual_emissions_tonnes_CO2=self.REOPT_EMISSIONS_SENTINEL,
            lifecycle_emissions_tonnes_CO2=self.REOPT_EMISSIONS_SENTINEL,
        )
        results["outputs"]["ElectricUtility"]["annual_emissions_tonnes_CO2"] = (
            self.REOPT_EMISSIONS_SENTINEL
        )

        workbook, _ = build_thailand_report(results, ASSUMPTIONS)

        texts = []
        numbers = []
        for worksheet in workbook.worksheets:
            for row in worksheet.iter_rows(values_only=True):
                for value in row:
                    if isinstance(value, str):
                        texts.append(value)
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        numbers.append(value)

        for banned in self.BANNED_DATASET_NAMES:
            self.assertFalse(
                any(banned.lower() in text.lower() for text in texts),
                "{} leaked into the Thailand workbook".format(banned),
            )
        self.assertNotIn(self.REOPT_EMISSIONS_SENTINEL, numbers)


class ScopeTwoAvoidedEmissionsAuditRowTests(TestCase):
    """Task 14 Finding 5: the emissions rows reaching the workbook, and the
    CURATED_ASSUMPTION_KEYS fix that stopped them double-rendering into the
    "Other Assumptions" echo, were previously verified only by one-off
    scripts against the real RTS case. Locks both down as a committed test,
    reusing the row-finding idiom from proforma_vietnam/tests/test_audit_sheets.py.
    """

    def _rows_with_label(self, sheet, label):
        return [
            row for row in range(1, sheet.max_row + 1)
            if sheet.cell(row=row, column=2).value == label
        ]

    def test_avoided_emissions_rows_render_exactly_once_each(self):
        workbook, extras = build_thailand_report(_results(), ASSUMPTIONS)
        sheet = workbook["Assumptions"]

        for label in (
            "Grid emission factor",
            "Grid emission factor vintage",
            "Avoided emissions, year 1",
        ):
            rows = self._rows_with_label(sheet, label)
            self.assertEqual(
                len(rows), 1,
                "expected exactly one {!r} row, found {}".format(label, len(rows)),
            )

        row = self._rows_with_label(sheet, "Avoided emissions, year 1")[0]
        self.assertAlmostEqual(
            sheet.cell(row=row, column=3).value, extras["annual_avoided_tco2e"],
        )


class PvOmCostRoundingDisclosureTests(TestCase):
    """Ruling 22 / final review R3: the memo discloses that PV O&M was sourced
    at 7.5 USD/kWp-yr, sent as 7.5, and applied by REopt as 8.00 (REopt.jl
    rounds PV cost parameters to whole dollars) -- but the workbook itself
    carried no such row. These lock the disclosure onto the Assumptions
    sheet. Gated on a key only proforma_thailand.report sets, so the default
    ``_results()`` fixture (no PV.om_cost_per_kw) renders nothing here.
    """

    def _rows_with_label(self, sheet, label):
        return [
            row for row in range(1, sheet.max_row + 1)
            if sheet.cell(row=row, column=2).value == label
        ]

    def test_all_three_values_render_on_the_assumptions_sheet(self):
        results = _results()
        results["outputs"]["PV"]["om_cost_per_kw"] = 8.0
        workbook, _ = build_thailand_report(results, ASSUMPTIONS)
        sheet = workbook["Assumptions"]

        for label, expected in (
            ("PV O&M cost, sourced", 7.5),
            ("PV O&M cost, sent to REopt", 7.5),
            ("PV O&M cost, applied by REopt", 8.0),
        ):
            rows = self._rows_with_label(sheet, label)
            self.assertEqual(len(rows), 1, "expected exactly one {!r} row".format(label))
            self.assertEqual(sheet.cell(row=rows[0], column=3).value, expected)

    def test_no_row_when_reopt_never_returned_an_om_cost(self):
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)
        sheet = workbook["Assumptions"]

        self.assertEqual(self._rows_with_label(sheet, "PV O&M cost, applied by REopt"), [])


class DemandChargeCitationTests(TestCase):
    """Final review R4: the PEA on-peak demand charge is booked by REopt
    under year_one_coincident_peak_cost_before_tax, not
    year_one_demand_cost_before_tax alone (Important 7). The two Year-1 BAU/
    optimized demand charge rows on the Assumptions sheet render the SUM of
    both fields but, before this fix, cited only the demand-cost field --
    an auditor tracing the number to the cited field would not reconcile.
    """

    def _rows_with_label(self, sheet, label):
        return [
            row for row in range(1, sheet.max_row + 1)
            if sheet.cell(row=row, column=2).value == label
        ]

    def test_demand_charge_citation_names_the_coincident_peak_field(self):
        results = _results()
        results["outputs"]["ElectricTariff"]["year_one_coincident_peak_cost_before_tax_bau"] = 90_000.0
        results["outputs"]["ElectricTariff"]["year_one_coincident_peak_cost_before_tax"] = 70_000.0
        workbook, _ = build_thailand_report(results, ASSUMPTIONS)
        sheet = workbook["Assumptions"]

        bau_row = self._rows_with_label(sheet, "Year-1 BAU demand charge")[0]
        opt_row = self._rows_with_label(sheet, "Year-1 optimized demand charge")[0]

        self.assertEqual(
            sheet.cell(row=bau_row, column=3).value, 80_000.0 + 90_000.0
        )
        self.assertIn(
            "year_one_coincident_peak_cost_before_tax_bau",
            sheet.cell(row=bau_row, column=5).value,
        )
        self.assertEqual(
            sheet.cell(row=opt_row, column=3).value, 60_000.0 + 70_000.0
        )
        self.assertIn(
            "year_one_coincident_peak_cost_before_tax",
            sheet.cell(row=opt_row, column=5).value,
        )


class ExcludedInputsAreDisclosedAsChoicesTests(TestCase):
    """"Not required" is a technical conclusion this analysis does not
    support. "Excluded at client direction" is what actually happened, and
    a reader is entitled to tell the two apart."""

    def test_power_factor_status_names_the_client_direction(self):
        from proforma_thailand.report import compute_power_factor_compensation

        result = compute_power_factor_compensation({})

        self.assertIn("client", result["status"].lower())
        self.assertNotIn("none required", result["status"].lower())
        self.assertEqual(result["compensation_kvar"], 0.0)
        self.assertEqual(result["mitigation_cost_usd"], 0.0)


class InverterCostIsDerivedFromSolvedCapexTests(TestCase):
    """The one path no existing test covers: cost taken from the solved PV
    capex rather than injected. Reading a field that does not exist on PV
    outputs made this inert once already."""

    def _results_with_solved_pv(self, size_kw, cost_per_kw):
        results = _results()
        results["outputs"]["PV"]["size_kw"] = size_kw
        results["outputs"]["PV"]["installed_cost_per_kw"] = cost_per_kw
        return results

    def _assumptions_without_explicit_inverter_cost(self):
        # Only the policy year and fraction are recorded; the shared core's
        # derivation from solved PV capex is the sole source of the cost.
        return dict(
            ASSUMPTIONS,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )

    def _replacement_row_value_at_year(self, workbook, year):
        # The Pro Forma (Audit) sheet's replacement row is written from
        # ``values=`` (audit_sheets.py), i.e. the raw per-year figures out of
        # cash_flow_result["derivation"]["replacement_costs_by_year_usd"]
        # copied verbatim, not a discounted or NPV'd figure. With zero battery
        # in this fixture that series equals extra_replacement_costs_by_year
        # exactly, so this is the value handed to the derivation this test
        # guards, not a recomputed expectation.
        sheet = workbook["Pro Forma (Audit)"]
        for row in range(1, sheet.max_row + 1):
            label = sheet.cell(row=row, column=1).value
            if isinstance(label, str) and "replacement (engine schedule)" in label.lower():
                return sheet.cell(row=row, column=3 + year).value
        return None

    def test_inverter_replacement_is_nonzero_when_only_solved_capex_is_present(self):
        from proforma_thailand.report import build_thailand_report

        results = self._results_with_solved_pv(size_kw=1000.0, cost_per_kw=400.0)
        assumptions = self._assumptions_without_explicit_inverter_cost()

        workbook, _extras = build_thailand_report(results, assumptions)

        # 10 percent of 1000 kW x 400 USD/kW = 40,000, booked as a raw
        # replacement-year cash outflow in year 11. The 400 is deliberately
        # NOT the production pv_installed_cost_per_kw: this test covers the
        # derivation mechanism, so tying it to a default would make it track
        # price changes instead of guarding the arithmetic.
        value_at_year_11 = self._replacement_row_value_at_year(workbook, 11)
        self.assertIsNotNone(value_at_year_11, "no replacement row rendered at all")
        self.assertAlmostEqual(
            value_at_year_11, 40000.0, delta=1.0,
            msg="inverter cost was not derived from solved PV capex",
        )

    def test_the_row_is_not_labelled_as_a_battery_replacement(self):
        """It rendered as "Battery replacement (engine schedule)" in case_1,
        which has no battery. That reached the client.

        Matches the exact row-label string, the same way
        test_replacement_row_is_not_labelled_a_battery above does, rather
        than a bare "Battery replacement" substring: the Model Basis sheet
        carries pre-existing, unconditional methodology bullets ("Battery
        replacement is CAPITALIZED, not expensed...") describing how ANY
        replacement-cost series is taxed under Circular 45 / Royal Decree
        No. 145, in shared proforma_vietnam/cash_flow.py and audit_sheets.py.
        That wording is not case-specific and is out of this task's scope
        (touching it risks the Vietnam byte-identity gate); a bare substring
        match trips on it and would fail for the wrong reason.
        """
        from proforma_thailand.report import build_thailand_report

        results = self._results_with_solved_pv(size_kw=1000.0, cost_per_kw=400.0)
        workbook, _extras = build_thailand_report(
            results, self._assumptions_without_explicit_inverter_cost()
        )

        labels = [
            value
            for sheet in workbook.worksheets
            for row in sheet.iter_rows(values_only=True)
            for value in row
            if isinstance(value, str)
        ]
        self.assertNotIn("Battery replacement (engine schedule)", labels)
