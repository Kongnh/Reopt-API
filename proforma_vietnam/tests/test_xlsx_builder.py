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
                "Cash Flow",
                "Tax Schedule",
                "Debt Service",
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

        self.assertEqual(values_by_label["Total Capex (VND)"], 1000000)
        self.assertEqual(values_by_label["Debt Principal (VND)"], 700000)
        self.assertEqual(values_by_label["Equity Investment (VND)"], 300000)
        self.assertEqual(values_by_label["NPV (VND)"], 123456)
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
