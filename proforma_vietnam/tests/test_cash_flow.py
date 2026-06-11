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

    def test_dppa_settlement_replaces_esco_energy_revenue_with_generator_revenue(self):
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
            project_years=1,
            dppa_settlement={
                "type": "grid_dppa_cfd",
                "esco_energy_revenue_vnd": 0.0,
                "year_one": {
                    "c_dn_vnd": 100.0,
                    "c_dppa_vnd": 25.0,
                    "c_cl_vnd": 10.0,
                    "c_bl_vnd": 40.0,
                    "cfd_strike_revenue_vnd": 170.0,
                    "cfd_fmp_offset_vnd": 150.0,
                    "generator_fmp_revenue_vnd": 200.0,
                },
                "escalation": {"fee_escalation_rate": 0.0, "cfd_strike_escalation_rate": 0.0},
                "hourly_breakout": [],
                "monthly_breakout": [],
            },
        )

        annual = result["annual_cash_flows"][0]
        self.assertEqual(annual["esco_energy_revenue_vnd"], 220.0)  # 200 FMP + (170-150) CfD
        self.assertEqual(annual["c_dn_vnd"], 100.0)
        self.assertEqual(annual["c_bl_vnd"], 40.0)
        self.assertEqual(annual["cfd_net_vnd"], 20.0)
        self.assertEqual(annual["generator_revenue_vnd"], 220.0)

    def test_dppa_settlement_replaces_offtaker_post_project_cost_with_dppa_chain(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[],
            evn_energy_rates_vnd_per_kwh=[],
            bau_evn_bill_vnd=1000000,
            optimized_evn_bill_vnd=9999999,  # ignored under DPPA
            bau_demand_charge_vnd=300000,
            optimized_demand_charge_vnd=100000,
            pv_capex_vnd=0,
            bess_capex_vnd=0,
            annual_om_vnd=0,
            esco_energy_discount_fraction=0.9,
            debt_fraction=0,
            project_years=1,
            dppa_settlement={
                "type": "grid_dppa_cfd",
                "esco_energy_revenue_vnd": 0.0,
                "year_one": {
                    "c_dn_vnd": 500000.0,
                    "c_dppa_vnd": 100000.0,
                    "c_cl_vnd": 50000.0,
                    "c_bl_vnd": 200000.0,
                    "cfd_strike_revenue_vnd": 0.0,
                    "cfd_fmp_offset_vnd": 0.0,
                    "generator_fmp_revenue_vnd": 500000.0,
                },
                "escalation": {"fee_escalation_rate": 0.0, "cfd_strike_escalation_rate": 0.0},
                "hourly_breakout": [],
                "monthly_breakout": [],
            },
        )

        annual = result["annual_cash_flows"][0]
        # offtaker = (C_DN + C_DPPA + C_CL + C_BL + CfD net) + optimized_demand + esco_demand_revenue
        # = (500k + 100k + 50k + 200k + 0) + 100k + (200k * 0.8) = 850k + 100k + 160k = 1,110,000
        self.assertEqual(annual["offtaker_post_project_cost_vnd"], 1110000.0)

    def test_dppa_strike_revenue_compounds_four_percent_in_year_two(self):
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
            debt_fraction=0,
            project_years=2,
            dppa_settlement={
                "type": "grid_dppa_cfd",
                "esco_energy_revenue_vnd": 0.0,
                "year_one": {
                    "c_dn_vnd": 0.0,
                    "c_dppa_vnd": 0.0,
                    "c_cl_vnd": 0.0,
                    "c_bl_vnd": 0.0,
                    "cfd_strike_revenue_vnd": 100.0,
                    "cfd_fmp_offset_vnd": 0.0,
                    "generator_fmp_revenue_vnd": 0.0,
                },
                "escalation": {
                    "fee_escalation_rate": 0.0,
                    "cfd_strike_escalation_rate": 0.04,
                },
                "hourly_breakout": [],
                "monthly_breakout": [],
            },
        )

        self.assertEqual(result["annual_cash_flows"][0]["cfd_strike_revenue_vnd"], 100.0)
        self.assertEqual(result["annual_cash_flows"][1]["cfd_strike_revenue_vnd"], 104.0)

    def test_non_dppa_demand_charge_rows_escalate_from_year_one(self):
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
            evn_capacity_escalation_rate=0.05,
            debt_fraction=0,
            project_years=3,
        )

        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["bau_demand_charge_vnd"], 300000.0)
        self.assertAlmostEqual(rows[0]["optimized_demand_charge_vnd"], 100000.0)
        self.assertAlmostEqual(rows[1]["bau_demand_charge_vnd"], 315000.0)
        self.assertAlmostEqual(rows[2]["optimized_demand_charge_vnd"], 110250.0)

    def test_pv_degradation_reduces_revenue_and_raises_offtaker_residual_bill(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[1000],
            evn_energy_rates_vnd_per_kwh=[2000],
            bau_evn_bill_vnd=10000000,
            optimized_evn_bill_vnd=4000000,
            bau_demand_charge_vnd=0,
            optimized_demand_charge_vnd=0,
            pv_capex_vnd=0,
            bess_capex_vnd=0,
            annual_om_vnd=0,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0,
            pv_degradation_rate=0.01,
            debt_fraction=0,
            project_years=2,
        )

        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["esco_energy_revenue_vnd"], 1800000.0)
        self.assertAlmostEqual(rows[1]["esco_energy_revenue_vnd"], 1800000.0 * 0.99)
        # Energy lost to degradation is repurchased from EVN at retail value.
        served_retail_value = 1000 * 2000.0
        self.assertAlmostEqual(
            rows[1]["offtaker_post_project_cost_vnd"],
            4000000.0 + served_retail_value * 0.01 + 1800000.0 * 0.99,
        )

    def test_pv_degradation_applies_to_dppa_generation_linked_terms(self):
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
            evn_energy_escalation_rate=0.0,
            pv_degradation_rate=0.01,
            debt_fraction=0,
            project_years=2,
            dppa_settlement={
                "type": "grid_dppa_cfd",
                "esco_energy_revenue_vnd": 0.0,
                "year_one": {
                    "c_dn_vnd": 1000.0,
                    "c_dppa_vnd": 100.0,
                    "c_cl_vnd": 50.0,
                    "c_bl_vnd": 400.0,
                    "cfd_strike_revenue_vnd": 170.0,
                    "cfd_fmp_offset_vnd": 150.0,
                    "generator_fmp_revenue_vnd": 2000.0,
                    "matched_retail_value_vnd": 3000.0,
                },
                "escalation": {"fee_escalation_rate": 0.0, "cfd_strike_escalation_rate": 0.0},
                "hourly_breakout": [],
                "monthly_breakout": [],
            },
        )

        y2 = result["annual_cash_flows"][1]
        self.assertAlmostEqual(y2["c_dn_vnd"], 1000.0 * 0.99)
        self.assertAlmostEqual(y2["c_dppa_vnd"], 100.0 * 0.99)
        self.assertAlmostEqual(y2["c_cl_vnd"], 50.0 * 0.99)
        self.assertAlmostEqual(y2["generator_fmp_revenue_vnd"], 2000.0 * 0.99)
        # Lost matched energy is repurchased from EVN at retail inside C_BL.
        self.assertAlmostEqual(y2["c_bl_vnd"], 400.0 + 3000.0 * 0.01)
        # The CfD settles on the contracted volume and does not degrade.
        self.assertAlmostEqual(y2["cfd_net_vnd"], 20.0)

    def test_om_escalation_rate_compounds_annual_om(self):
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[],
            evn_energy_rates_vnd_per_kwh=[],
            bau_evn_bill_vnd=1000000,
            optimized_evn_bill_vnd=700000,
            bau_demand_charge_vnd=0,
            optimized_demand_charge_vnd=0,
            pv_capex_vnd=0,
            bess_capex_vnd=0,
            annual_om_vnd=100000,
            esco_energy_discount_fraction=0.9,
            om_escalation_rate=0.03,
            debt_fraction=0,
            project_years=2,
        )

        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["annual_om_vnd"], 100000.0)
        self.assertAlmostEqual(rows[1]["annual_om_vnd"], 103000.0)

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

    def test_pv_depreciation_years_is_configurable(self):
        # Circular 45/2013/TT-BTC permits 7-20 years for generating equipment;
        # the default stays 20 but the schedule must be configurable.
        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[1000],
            evn_energy_rates_vnd_per_kwh=[3000],
            bau_evn_bill_vnd=5000000,
            optimized_evn_bill_vnd=3000000,
            bau_demand_charge_vnd=0,
            optimized_demand_charge_vnd=0,
            pv_capex_vnd=2000000,
            bess_capex_vnd=0,
            annual_om_vnd=100000,
            esco_energy_discount_fraction=0.9,
            debt_fraction=0,
            project_years=25,
            pv_depreciation_years=10,
        )

        rows = result["annual_cash_flows"]
        self.assertEqual(rows[0]["depreciation_vnd"], 200000)  # 2,000,000 / 10
        self.assertEqual(rows[9]["depreciation_vnd"], 200000)
        self.assertEqual(rows[10]["depreciation_vnd"], 0)

    def test_pv_depreciation_years_outside_circular_45_range_raises(self):
        for invalid_years in (6, 21):
            with self.assertRaises(ValueError):
                calculate_vietnam_esco_cash_flow(
                    project_served_pv_kwh=[],
                    evn_energy_rates_vnd_per_kwh=[],
                    bau_evn_bill_vnd=1000000,
                    optimized_evn_bill_vnd=700000,
                    bau_demand_charge_vnd=0,
                    optimized_demand_charge_vnd=0,
                    pv_capex_vnd=1000000,
                    bess_capex_vnd=0,
                    annual_om_vnd=0,
                    esco_energy_discount_fraction=0.9,
                    debt_fraction=0,
                    project_years=5,
                    pv_depreciation_years=invalid_years,
                )

    def test_summary_reports_10_year_and_lifetime_buyer_savings(self):
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
            debt_fraction=0,
            project_years=25,
        )

        rows = result["annual_cash_flows"]
        summary = result["summary"]
        savings_10yr = sum(row["offtaker_savings_vnd"] for row in rows[:10])
        bau_10yr = sum(row["bau_evn_bill_vnd"] for row in rows[:10])
        savings_lifetime = sum(row["offtaker_savings_vnd"] for row in rows)
        bau_lifetime = sum(row["bau_evn_bill_vnd"] for row in rows)

        self.assertAlmostEqual(summary["buyer_savings_10yr_vnd"], savings_10yr)
        self.assertAlmostEqual(
            summary["buyer_savings_10yr_fraction"], savings_10yr / bau_10yr
        )
        self.assertAlmostEqual(summary["buyer_savings_lifetime_vnd"], savings_lifetime)
        self.assertAlmostEqual(
            summary["buyer_savings_lifetime_fraction"], savings_lifetime / bau_lifetime
        )
        self.assertAlmostEqual(summary["buyer_savings_10yr_usd"], savings_10yr)
