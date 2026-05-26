from unittest import TestCase

from proforma_vietnam.report_data import build_vietnam_report_data


class VietnamReportDataTests(TestCase):

    def test_normalizes_reopt_results_for_report_sheets(self):
        report = build_vietnam_report_data(_fake_reopt_results(), _cash_flow_result())

        self.assertEqual(
            report["system_sizing"],
            {
                "pv_kw": 100,
                "battery_kw": 50,
                "battery_kwh": 200,
            },
        )
        self.assertEqual(
            report["dispatch_profile"][0],
            {
                "hour": 1,
                "load_kw": 10,
                "grid_to_load_kw": 7,
                "pv_to_load_kw": 3,
                "storage_to_load_kw": 0,
                "storage_charge_kw": 1,
            },
        )
        self.assertEqual(report["annual_production"]["pv_to_load_kwh"], 7)
        self.assertEqual(report["annual_production"]["grid_to_load_kwh"], 15)
        self.assertEqual(report["annual_production"]["storage_to_load_kwh"], 1)
        self.assertEqual(report["results_comparison"]["bau_utility_bill_vnd"], 100000)
        self.assertEqual(report["results_comparison"]["optimized_utility_bill_vnd"], 70000)
        self.assertEqual(report["developer_financial_performance"]["equity_irr_fraction"], 0.14)
        self.assertEqual(report["load_duration"][0]["load_kw"], 20)
        self.assertEqual(report["load_duration"][0]["net_load_kw"], 8)


def _fake_reopt_results():
    return {
        "inputs": {
            "ElectricLoad": {"loads_kw": [10, 20]},
        },
        "outputs": {
            "PV": {
                "size_kw": 100,
                "electric_to_load_series_kw": [3, 4],
                "electric_to_storage_series_kw": [1, 2],
                "electric_curtailed_series_kw": [0, 1],
            },
            "ElectricStorage": {
                "size_kw": 50,
                "size_kwh": 200,
                "storage_to_load_series_kw": [0, 1],
            },
            "ElectricUtility": {
                "electric_to_load_series_kw": [7, 8],
                "electric_to_storage_series_kw": [0, 1],
            },
            "ElectricTariff": {
                "year_one_bill_before_tax_bau": 100000,
                "year_one_bill_before_tax": 70000,
                "year_one_demand_cost_before_tax_bau": 20000,
                "year_one_demand_cost_before_tax": 12000,
            },
        },
    }


def _cash_flow_result():
    return {
        "summary": {
            "project_irr_fraction": 0.12,
            "equity_irr_fraction": 0.14,
            "npv_vnd": 123456,
            "average_dscr": 1.3,
            "simple_payback_years": 7.5,
            "roi_fraction": 1.8,
        }
    }
