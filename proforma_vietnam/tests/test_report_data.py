from unittest import TestCase

from proforma_vietnam.report_data import build_vietnam_report_data


class VietnamReportDataTests(TestCase):

    def test_normalizes_reopt_results_for_report_sheets(self):
        report = build_vietnam_report_data(
            _fake_reopt_results(),
            _cash_flow_result(),
            poa_irradiance_series=[100.0, 200.0],
        )

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
                "pv_irradiance": 100.0,
                "pv_total_kw": 4,       # to_load 3 + to_storage 1 + curtailed 0
                "pv_to_load_kw": 3,
                "pv_to_storage_kw": 1,
                "pv_to_grid_kw": 0,
                "pv_curtailed_kw": 0,
                "grid_to_load_kw": 7,
                "grid_to_storage_kw": 0,
                "storage_to_load_kw": 0,
            },
        )
        self.assertEqual(report["dispatch_profile"][1]["pv_irradiance"], 200.0)
        self.assertEqual(report["dispatch_profile"][1]["pv_total_kw"], 7)
        self.assertEqual(report["dispatch_profile"][1]["grid_to_storage_kw"], 1)
        self.assertEqual(report["annual_production"]["pv_to_load_kwh"], 7)
        self.assertEqual(report["annual_production"]["grid_to_load_kwh"], 15)
        self.assertEqual(report["annual_production"]["storage_to_load_kwh"], 1)
        # Annual POA insolation = (100 + 200) / 1000; PR = specific yield
        # (0.2 + 0.5) / reference yield (0.3).
        self.assertAlmostEqual(
            report["solar_resource"]["annual_poa_irradiation_kwh_per_m2"], 0.3
        )
        self.assertAlmostEqual(
            report["solar_resource"]["performance_ratio"], 0.7 / 0.3
        )
        self.assertEqual(report["results_comparison"]["bau_utility_bill_usd"], 100000)
        self.assertEqual(report["results_comparison"]["optimized_utility_bill_usd"], 70000)
        self.assertEqual(report["developer_financial_performance"]["equity_irr_fraction"], 0.14)
        self.assertEqual(report["load_duration"][0]["load_kw"], 20)
        self.assertEqual(report["load_duration"][0]["net_load_kw"], 8)

    def test_solar_resource_degrades_without_irradiance(self):
        report = build_vietnam_report_data(_fake_reopt_results(), _cash_flow_result())

        self.assertIsNone(report["solar_resource"]["performance_ratio"])
        self.assertEqual(
            report["solar_resource"]["annual_poa_irradiation_kwh_per_m2"], 0.0
        )
        self.assertEqual(report["dispatch_profile"][0]["pv_irradiance"], 0)


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
                "production_factor_series": [0.2, 0.5],
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
