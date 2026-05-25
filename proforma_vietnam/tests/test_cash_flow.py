from unittest import TestCase

from proforma_vietnam.cash_flow import calculate_vietnam_esco_cash_flow


class VietnamCashFlowTests(TestCase):

    def test_esco_energy_revenue_uses_discounted_time_specific_evn_rates(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[10, 20],
            evn_energy_rates_vnd_per_kwh=[1000, 2000],
            bau_evn_bill_vnd=1000000,
            optimized_evn_bill_vnd=700000,
            bau_demand_charge_vnd=0,
            optimized_demand_charge_vnd=0,
            pv_capex_vnd=0,
            bess_capex_vnd=0,
            annual_om_vnd=0,
            esco_energy_discount_fraction=0.9,
            debt_fraction=0,
            project_years=2,
        )

        self.assertEqual(result["annual_cash_flows"][0]["esco_energy_revenue_vnd"], 45000)
        self.assertEqual(result["annual_cash_flows"][1]["esco_energy_revenue_vnd"], 46800)

    def test_demand_charge_savings_are_split_80_percent_to_esco_by_default(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[],
            evn_energy_rates_vnd_per_kwh=[],
            bau_evn_bill_vnd=1000000,
            optimized_evn_bill_vnd=700000,
            bau_demand_charge_vnd=300000,
            optimized_demand_charge_vnd=100000,
            pv_capex_vnd=0,
            bess_capex_vnd=0,
            annual_om_vnd=0,
            esco_energy_discount_fraction=0.9,
            debt_fraction=0,
            project_years=1,
        )

        annual = result["annual_cash_flows"][0]
        self.assertEqual(annual["demand_charge_savings_vnd"], 200000)
        self.assertEqual(annual["esco_demand_revenue_vnd"], 160000)
        self.assertEqual(annual["offtaker_demand_savings_vnd"], 40000)

    def test_base_case_disables_grid_charging_arbitrage(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[],
            evn_energy_rates_vnd_per_kwh=[],
            bau_evn_bill_vnd=1000000,
            optimized_evn_bill_vnd=700000,
            bau_demand_charge_vnd=0,
            optimized_demand_charge_vnd=0,
            pv_capex_vnd=0,
            bess_capex_vnd=0,
            annual_om_vnd=0,
            esco_energy_discount_fraction=0.9,
            net_grid_arbitrage_value_vnd=500000,
            debt_fraction=0,
            project_years=1,
        )

        self.assertEqual(result["annual_cash_flows"][0]["esco_grid_arbitrage_revenue_vnd"], 0)

    def test_optional_grid_charging_assigns_net_positive_arbitrage_to_esco(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[],
            evn_energy_rates_vnd_per_kwh=[],
            bau_evn_bill_vnd=1000000,
            optimized_evn_bill_vnd=700000,
            bau_demand_charge_vnd=0,
            optimized_demand_charge_vnd=0,
            pv_capex_vnd=0,
            bess_capex_vnd=0,
            annual_om_vnd=0,
            esco_energy_discount_fraction=0.9,
            grid_charging_enabled=True,
            net_grid_arbitrage_value_vnd=500000,
            debt_fraction=0,
            project_years=1,
        )

        self.assertEqual(result["annual_cash_flows"][0]["esco_grid_arbitrage_revenue_vnd"], 500000)

    def test_outputs_investor_metrics_and_uses_vietnam_tax_depreciation(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[1000],
            evn_energy_rates_vnd_per_kwh=[3000],
            bau_evn_bill_vnd=5000000,
            optimized_evn_bill_vnd=3000000,
            bau_demand_charge_vnd=1000000,
            optimized_demand_charge_vnd=500000,
            pv_capex_vnd=2000000,
            bess_capex_vnd=800000,
            annual_om_vnd=100000,
            esco_energy_discount_fraction=0.9,
            owner_discount_rate_fraction=0.1,
            debt_fraction=0,
            project_years=25,
        )

        summary = result["summary"]
        annual = result["annual_cash_flows"][0]
        self.assertEqual(annual["depreciation_vnd"], 200000)
        self.assertEqual(annual["cit_vnd"], 0)
        self.assertIn("project_irr_fraction", summary)
        self.assertIn("equity_irr_fraction", summary)
        self.assertIn("npv_vnd", summary)
        self.assertIn("average_dscr", summary)
        self.assertIn("simple_payback_years", summary)
