from unittest import TestCase

from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook


class VietnamXlsxBuilderTests(TestCase):

    def test_builds_required_workbook_sheets(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={"esco_energy_discount_fraction": 0.9},
        )

        self.assertEqual(
            workbook.sheetnames,
            [
                "Summary",
                "System Sizing",
                "Results Comparison",
                "Annual Production",
                "Dispatch Profile",
                "Load Duration",
                "Cash Flow",
                "Tax Schedule",
                "Debt Service",
                "Developer Financials",
                "Assumptions",
            ],
        )

    def test_writes_key_summary_values(self):
        workbook = build_vietnam_esco_workbook(_cash_flow_result())
        summary = workbook["Summary"]

        values_by_label = {
            summary.cell(row=row, column=1).value: summary.cell(row=row, column=2).value
            for row in range(1, summary.max_row + 1)
        }

        self.assertEqual(values_by_label["Total Capex (USD)"], 1000000)
        self.assertEqual(values_by_label["Debt Principal (USD)"], 700000)
        self.assertEqual(values_by_label["Equity Investment (USD)"], 300000)
        self.assertEqual(values_by_label["NPV (USD)"], 123456)
        self.assertEqual(values_by_label["Equity IRR"], 0.14)

    def test_writes_annual_cash_flow_tax_and_debt_rows(self):
        workbook = build_vietnam_esco_workbook(_cash_flow_result())

        cash_flow = workbook["Cash Flow"]
        self.assertEqual(cash_flow.cell(row=1, column=1).value, "Year")
        self.assertEqual(cash_flow.cell(row=2, column=1).value, 1)
        self.assertEqual(cash_flow.cell(row=2, column=2).value, 200000)
        self.assertEqual(cash_flow.cell(row=2, column=10).value, 250000)
        self.assertEqual(cash_flow.cell(row=2, column=13).value, 50000)

        tax_schedule = workbook["Tax Schedule"]
        self.assertEqual(tax_schedule.cell(row=1, column=1).value, "Year")
        self.assertEqual(tax_schedule.cell(row=2, column=2).value, 40000)
        self.assertEqual(tax_schedule.cell(row=2, column=3).value, 0)

        debt_service = workbook["Debt Service"]
        self.assertEqual(debt_service.cell(row=1, column=1).value, "Year")
        self.assertEqual(debt_service.cell(row=2, column=2).value, 60000)
        self.assertEqual(debt_service.cell(row=2, column=5).value, 640000)

    def test_writes_assumptions(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={
                "esco_energy_discount_fraction": 0.9,
                "evn_energy_escalation_rate": 0.04,
            },
        )

        assumptions = workbook["Assumptions"]
        values_by_label = {
            assumptions.cell(row=row, column=1).value: assumptions.cell(row=row, column=2).value
            for row in range(1, assumptions.max_row + 1)
        }

        self.assertEqual(values_by_label["esco_energy_discount_fraction"], 0.9)
        self.assertEqual(values_by_label["evn_energy_escalation_rate"], 0.04)

    def test_writes_report_sheets_and_charts(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            report_data=_report_data(),
        )

        self.assertEqual(workbook["System Sizing"]["A1"].value, "Metric")
        self.assertEqual(workbook["System Sizing"]["B2"].value, 100)
        self.assertEqual(workbook["Annual Production"]["A2"].value, "PV to Load (kWh)")
        self.assertEqual(workbook["Dispatch Profile"]["A2"].value, 1)
        self.assertEqual(workbook["Load Duration"]["B2"].value, 20)
        self.assertEqual(workbook["Developer Financials"]["A2"].value, "Project IRR")
        self.assertGreater(len(workbook["Annual Production"]._charts), 0)
        self.assertGreater(len(workbook["Dispatch Profile"]._charts), 0)
        self.assertGreater(len(workbook["Load Duration"]._charts), 0)
        self.assertGreater(len(workbook["Developer Financials"]._charts), 0)


def _cash_flow_result():
    return {
        "summary": {
            "total_capex_vnd": 1000000,
            "debt_principal_vnd": 700000,
            "equity_investment_vnd": 300000,
            "project_irr_fraction": 0.12,
            "equity_irr_fraction": 0.14,
            "npv_vnd": 123456,
            "average_dscr": 1.3,
            "simple_payback_years": 7.5,
            "roi_fraction": 1.8,
        },
        "annual_cash_flows": [
            {
                "year": 1,
                "esco_energy_revenue_vnd": 200000,
                "esco_demand_revenue_vnd": 80000,
                "esco_grid_arbitrage_revenue_vnd": 0,
                "esco_revenue_vnd": 280000,
                "annual_om_vnd": 30000,
                "replacement_cost_vnd": 0,
                "depreciation_vnd": 40000,
                "cit_vnd": 0,
                "cash_available_for_debt_service_vnd": 250000,
                "debt_service_vnd": 110000,
                "principal_vnd": 50000,
                "interest_vnd": 60000,
                "ending_debt_balance_vnd": 640000,
                "equity_cash_flow_vnd": 140000,
                "offtaker_savings_vnd": 50000,
                "offtaker_savings_fraction": 0.05,
                "dscr": 2.27,
            }
        ],
    }


def _report_data():
    return {
        "system_sizing": {
            "pv_kw": 100,
            "battery_kw": 50,
            "battery_kwh": 200,
        },
        "results_comparison": {
            "bau_utility_bill_vnd": 100000,
            "optimized_utility_bill_vnd": 70000,
            "utility_bill_savings_vnd": 30000,
            "demand_charge_savings_vnd": 8000,
        },
        "annual_production": {
            "grid_to_load_kwh": 100,
            "pv_to_load_kwh": 80,
            "pv_to_storage_kwh": 20,
            "storage_to_load_kwh": 15,
            "pv_curtailed_kwh": 5,
            "grid_to_storage_kwh": 0,
        },
        "dispatch_profile": [
            {
                "hour": 1,
                "load_kw": 10,
                "grid_to_load_kw": 7,
                "pv_to_load_kw": 3,
                "storage_to_load_kw": 0,
                "storage_charge_kw": 1,
            },
            {
                "hour": 2,
                "load_kw": 20,
                "grid_to_load_kw": 8,
                "pv_to_load_kw": 4,
                "storage_to_load_kw": 1,
                "storage_charge_kw": 2,
            },
        ],
        "load_duration": [
            {"rank": 1, "load_kw": 20, "net_load_kw": 8},
            {"rank": 2, "load_kw": 10, "net_load_kw": 7},
        ],
        "developer_financial_performance": {
            "project_irr_fraction": 0.12,
            "equity_irr_fraction": 0.14,
            "npv_vnd": 123456,
            "average_dscr": 1.3,
            "simple_payback_years": 7.5,
            "roi_fraction": 1.8,
        },
    }
