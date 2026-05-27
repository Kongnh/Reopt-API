from unittest import TestCase
from copy import deepcopy

from proforma_vietnam.esco_pro_forma import calculate_esco_pro_forma_from_reopt_results


class VietnamEscoProFormaAdapterTests(TestCase):

    def test_maps_v3_results_into_cash_flow_inputs(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
        )

        annual = result["annual_cash_flows"][0]
        summary = result["summary"]

        self.assertEqual(annual["esco_energy_revenue_vnd"], 14400)
        self.assertEqual(annual["demand_charge_savings_vnd"], 5000)
        self.assertEqual(annual["esco_demand_revenue_vnd"], 4000)
        self.assertEqual(annual["annual_om_vnd"], 1000)
        self.assertEqual(summary["total_capex_vnd"], 110000)

    def test_excludes_storage_discharge_when_grid_charging_is_enabled(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=True),
            esco_energy_discount_fraction=0.9,
            project_years=1,
        )

        annual = result["annual_cash_flows"][0]

        self.assertEqual(annual["esco_energy_revenue_vnd"], 4500)
        self.assertEqual(annual["esco_grid_arbitrage_revenue_vnd"], 0)

    def test_converts_vnd_tariff_inputs_to_usd_report_values_when_exchange_rate_is_provided(self):
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        reopt_results["inputs"]["ElectricTariff"]["tou_energy_rates_per_kwh"] = [1000, 2000]
        reopt_results["outputs"]["ElectricTariff"] = {
            "year_one_bill_before_tax_bau": 50000,
            "year_one_bill_before_tax": 30000,
            "year_one_demand_cost_before_tax_bau": 8000,
            "year_one_demand_cost_before_tax": 3000,
        }
        reopt_results["outputs"]["Financial"]["year_one_om_costs_before_tax"] = 1000

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            exchange_rate_vnd_per_usd=25000,
            reopt_money_values_currency="vnd",
            project_years=1,
        )

        annual = result["annual_cash_flows"][0]
        summary = result["summary"]

        self.assertAlmostEqual(annual["esco_energy_revenue_usd"], 0.576)
        self.assertEqual(annual["demand_charge_savings_usd"], 0.2)
        self.assertEqual(annual["annual_om_usd"], 1000)
        self.assertEqual(summary["total_capex_usd"], 110000)


def _fake_reopt_results(can_grid_charge):
    return {
        "inputs": {
            "ElectricTariff": {
                "tou_energy_rates_per_kwh": [1000, 2000],
            },
            "ElectricStorage": {
                "can_grid_charge": can_grid_charge,
            },
            "Financial": {
                "owner_discount_rate_fraction": 0.11,
            },
        },
        "outputs": {
            "PV": {
                "size_kw": 100,
                "installed_cost_per_kw": 1000,
                "electric_to_load_series_kw": [1, 2],
            },
            "ElectricStorage": {
                "initial_capital_cost": 10000,
                "storage_to_load_series_kw": [3, 4],
            },
            "ElectricTariff": {
                "year_one_bill_before_tax_bau": 50000,
                "year_one_bill_before_tax": 30000,
                "year_one_demand_cost_before_tax_bau": 8000,
                "year_one_demand_cost_before_tax": 3000,
            },
            "Financial": {
                "year_one_om_costs_before_tax": 1000,
            },
        },
    }
