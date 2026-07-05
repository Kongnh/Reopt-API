from unittest import TestCase

from openpyxl import Workbook

from proforma_vietnam import audit_sheets
from proforma_vietnam.cash_flow import (
    calculate_fx_sensitivity,
    calculate_vietnam_esco_cash_flow,
)
from proforma_vietnam.dppa_settlement import settle_dppa_year_one
from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook


def _esco_result(**overrides):
    inputs = dict(
        project_served_pv_kwh=[1000.0] * 8760,
        evn_energy_rates_vnd_per_kwh=[0.08] * 8760,
        bau_evn_bill_vnd=900000,
        optimized_evn_bill_vnd=630000,
        bau_demand_charge_vnd=180000,
        optimized_demand_charge_vnd=120000,
        pv_capex_vnd=2100000,
        bess_capex_vnd=900000,
        annual_om_vnd=45000,
        esco_energy_discount_fraction=0.9,
        pv_degradation_rate=0.005,
        om_escalation_rate=0.02,
        replacement_costs_by_year=[0.0] * 10 + [250000.0],
        exchange_rate_vnd_per_usd=25000,
    )
    inputs.update(overrides)
    return calculate_vietnam_esco_cash_flow(**inputs)


def _dppa_result():
    dppa_inputs = {
        "type": "grid_dppa_cfd",
        "fmp_series_vnd_per_kwh": [1500.0] * 24,
        "cfmp_series_vnd_per_kwh": [1539.0] * 24,
        "cfd_strike_per_kwh_vnd": 1700.0,
        "cfd_strike_escalation_rate": 0.02,
        "cfd_contract_volume_kwh_per_hour": 500.0,
        "transmission_loss_factor_k": 1.026,
        "distribution_loss_factor_kpp": 1.027263,
        "allocation_fraction_delta": 1.0,
        "c_dppa_service_fee_vnd_per_kwh": 360.0,
        "c_cl_settlement_adder_vnd_per_kwh": 163.3,
        "fee_escalation_rate": 0.04,
    }
    dispatch = {
        "load_kw": [800.0] * 24,
        "pv_to_load_kw": [600.0] * 24,
        "pv_to_grid_kw": [100.0] * 24,
        "pv_curtailed_kw": [50.0] * 24,
        "storage_to_load_kw": [0.0] * 24,
        "storage_to_grid_kw": [0.0] * 24,
    }
    settlement = settle_dppa_year_one(
        dppa_inputs=dppa_inputs,
        dispatch=dispatch,
        evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
    )
    # convert year-one primitives to USD as esco_pro_forma does
    year_one = {
        key: (value / 25000 if key.endswith("_vnd") else value)
        for key, value in settlement["year_one"].items()
    }
    settlement = {**settlement, "year_one": year_one}
    return calculate_vietnam_esco_cash_flow(
        project_served_pv_kwh=[600.0] * 24,
        evn_energy_rates_vnd_per_kwh=[0.08] * 24,
        bau_evn_bill_vnd=900000,
        optimized_evn_bill_vnd=630000,
        bau_demand_charge_vnd=180000,
        optimized_demand_charge_vnd=120000,
        pv_capex_vnd=2100000,
        bess_capex_vnd=900000,
        annual_om_vnd=45000,
        esco_energy_discount_fraction=0.9,
        dppa_settlement=settlement,
        exchange_rate_vnd_per_usd=25000,
    ), dppa_inputs


ESCO_ASSUMPTIONS = {
    "case_name": "Audit Test",
    "exchange_rate_vnd_per_usd": 25000,
    "run_uuid": "test-uuid",
}


class AssumptionsSheetTests(TestCase):

    def test_defines_named_cells_for_every_formula_input(self):
        result = _esco_result()
        workbook = build_vietnam_esco_workbook(result, assumptions=ESCO_ASSUMPTIONS)

        for name in (
            "PROJECT_YEARS", "FX_VND_PER_USD", "PV_CAPEX", "BESS_CAPEX",
            "TOTAL_CAPEX", "OM_YEAR1", "ESC_ENERGY", "ESC_CAPACITY",
            "PV_DEGRADATION", "DEBT_FRACTION", "DEBT_RATE", "DEBT_TERM_YEARS",
            "DEBT_PRINCIPAL", "EQUITY_INVESTMENT", "DEBT_PAYMENT", "DISC_RATE",
            "CIT_RATE", "CIT_HOLIDAY_YEARS", "PV_DEP_YEARS", "BESS_DEP_YEARS",
            "BASE_ENERGY_REV", "BASE_DEMAND_SAVINGS", "BASE_SERVED_RETAIL",
            "BAU_BILL_Y1", "OPT_BILL_Y1",
        ):
            self.assertIn(name, workbook.defined_names, name)

    def test_no_cell_holds_an_empty_string_or_accidental_formula(self):
        # Empty-string cells serialise as corrupt inlineStr XML; label/source
        # strings starting with "=" become invalid formulas. Both have broken
        # Excel loads before — guard every sheet.
        result = _esco_result()
        workbook = build_vietnam_esco_workbook(result, assumptions=ESCO_ASSUMPTIONS)

        for worksheet in workbook.worksheets:
            for row in worksheet.iter_rows():
                for cell in row:
                    if not isinstance(cell.value, str):
                        continue
                    self.assertNotEqual(
                        cell.value, "",
                        f"{worksheet.title}!{cell.coordinate} is an empty string",
                    )
                    if cell.value.startswith("="):
                        self.assertNotIn(
                            " − ", cell.value,
                            f"{worksheet.title}!{cell.coordinate} looks like prose "
                            "stored as a formula",
                        )


class ProFormaAuditSheetTests(TestCase):

    def test_white_cells_are_formulas_and_engine_rows_are_hardcoded(self):
        result = _esco_result()
        workbook = build_vietnam_esco_workbook(result, assumptions=ESCO_ASSUMPTIONS)
        sheet = workbook["Pro Forma (Audit)"]

        labels = {
            sheet.cell(row=row, column=1).value: row
            for row in range(1, sheet.max_row + 1)
            if sheet.cell(row=row, column=1).value
        }
        # formula rows reference named assumption cells
        revenue_row = labels["ESCO energy revenue (discount-to-EVN)"]
        year1 = sheet.cell(row=revenue_row, column=4).value
        self.assertTrue(str(year1).startswith("=BASE_ENERGY_REV"))
        # the engine tie-out row is hardcoded to the engine's numbers
        engine_row = labels["Equity cash flow (engine)"]
        engine_year1 = sheet.cell(row=engine_row, column=4).value
        self.assertAlmostEqual(
            engine_year1,
            result["annual_cash_flows"][0]["equity_cash_flow_usd"],
        )
        # year 0 equity = -equity investment
        engine_year0 = sheet.cell(row=engine_row, column=3).value
        self.assertAlmostEqual(
            engine_year0, -result["summary"]["equity_investment_usd"]
        )

    def test_check_block_carries_engine_metrics_and_pass_formulas(self):
        result = _esco_result()
        workbook = build_vietnam_esco_workbook(result, assumptions=ESCO_ASSUMPTIONS)
        sheet = workbook["Pro Forma (Audit)"]

        checks = {}
        for row in range(1, sheet.max_row + 1):
            status = sheet.cell(row=row, column=6).value
            if isinstance(status, str) and status.startswith("=IF(ABS"):
                checks[sheet.cell(row=row, column=1).value] = row

        self.assertIn("Equity IRR", checks)
        self.assertIn("Equity NPV", checks)
        self.assertIn("Simple equity payback", checks)
        irr_row = checks["Equity IRR"]
        self.assertAlmostEqual(
            sheet.cell(row=irr_row, column=4).value,
            result["summary"]["equity_irr_fraction"],
        )
        self.assertTrue(
            str(sheet.cell(row=irr_row, column=3).value).startswith("=")
        )

    def test_dppa_structure_gets_settlement_rows_and_names(self):
        result, dppa_inputs = _dppa_result()
        assumptions = {**ESCO_ASSUMPTIONS, "dppa": dppa_inputs}
        workbook = build_vietnam_esco_workbook(result, assumptions=assumptions)

        for name in ("DPPA_C_DN_Y1", "DPPA_C_BL_Y1", "DPPA_CFD_STRIKE_Y1",
                     "DPPA_FMP_REV_Y1", "ESC_FEE", "ESC_STRIKE"):
            self.assertIn(name, workbook.defined_names, name)

        sheet = workbook["Pro Forma (Audit)"]
        labels = [
            sheet.cell(row=row, column=1).value
            for row in range(1, sheet.max_row + 1)
        ]
        self.assertIn("Generator FMP market revenue", labels)
        self.assertIn("CfD net settlement (to generator)", labels)
        self.assertIn("C_BL retail shortfall (incl. degradation repurchase)", labels)
        self.assertNotIn("ESCO energy revenue (discount-to-EVN)", labels)


class FxSensitivitySheetTests(TestCase):

    def test_table_carries_engine_scenarios_and_live_irr_formulas(self):
        result = _esco_result()
        workbook = build_vietnam_esco_workbook(result, assumptions=ESCO_ASSUMPTIONS)
        sheet = workbook["FX Sensitivity"]
        engine = calculate_fx_sensitivity(result)

        for index, scenario in enumerate(engine):
            row = 5 + index
            self.assertAlmostEqual(
                sheet.cell(row=row, column=1).value,
                scenario["vnd_depreciation_rate"],
            )
            self.assertTrue(str(sheet.cell(row=row, column=2).value).startswith("=IRR("))
            self.assertAlmostEqual(
                sheet.cell(row=row, column=4).value,
                scenario["equity_irr_fraction"],
            )
            self.assertAlmostEqual(
                sheet.cell(row=row, column=5).value, scenario["npv_usd"]
            )


class CoverSheetTests(TestCase):

    def test_cover_aggregates_check_statuses_when_audit_sheets_exist(self):
        result = _esco_result()
        workbook = build_vietnam_esco_workbook(result, assumptions=ESCO_ASSUMPTIONS)
        cover = workbook["Cover"]

        status_formula = None
        for row in range(1, cover.max_row + 1):
            value = cover.cell(row=row, column=3).value
            if isinstance(value, str) and value.startswith("=IF(COUNTIF"):
                status_formula = value
        self.assertIsNotNone(status_formula)
        self.assertIn("Pro Forma (Audit)", status_formula)
        self.assertIn("FX Sensitivity", status_formula)

    def test_cover_omits_status_row_without_derivation(self):
        workbook = build_vietnam_esco_workbook(
            {"summary": {}, "annual_cash_flows": []},
            assumptions={"esco_energy_discount_fraction": 0.9},
        )
        cover = workbook["Cover"]
        for row in range(1, cover.max_row + 1):
            value = cover.cell(row=row, column=3).value
            if isinstance(value, str):
                self.assertFalse(value.startswith("=IF(COUNTIF"))
