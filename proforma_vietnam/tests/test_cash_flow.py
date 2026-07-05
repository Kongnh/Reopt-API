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


class CurrencyFinalizationTests(TestCase):

    def _run(self, **overrides):
        inputs = dict(
            project_served_pv_kwh=[1000],
            evn_energy_rates_vnd_per_kwh=[0.12],
            bau_evn_bill_vnd=200000,
            optimized_evn_bill_vnd=120000,
            bau_demand_charge_vnd=40000,
            optimized_demand_charge_vnd=20000,
            pv_capex_vnd=1000000,
            bess_capex_vnd=400000,
            annual_om_vnd=10000,
            esco_energy_discount_fraction=0.9,
            project_years=3,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def test_without_exchange_rate_usd_aliases_equal_vnd_values(self):
        result = self._run()

        row = result["annual_cash_flows"][0]
        self.assertEqual(row["esco_revenue_usd"], row["esco_revenue_vnd"])
        summary = result["summary"]
        self.assertEqual(summary["npv_usd"], summary["npv_vnd"])

    def test_with_exchange_rate_vnd_keys_are_restated_at_fixed_rate(self):
        base = self._run()
        result = self._run(exchange_rate_vnd_per_usd=25000)

        base_row = base["annual_cash_flows"][0]
        row = result["annual_cash_flows"][0]
        # _usd keeps the computed (model-currency) value...
        self.assertEqual(row["esco_revenue_usd"], base_row["esco_revenue_vnd"])
        self.assertEqual(row["equity_cash_flow_usd"], base_row["equity_cash_flow_vnd"])
        # ...and _vnd is restated at the fixed contract rate.
        self.assertEqual(row["esco_revenue_vnd"], base_row["esco_revenue_vnd"] * 25000)
        self.assertEqual(
            result["summary"]["npv_vnd"], base["summary"]["npv_vnd"] * 25000
        )
        # Non-currency metrics are untouched.
        self.assertEqual(
            result["summary"]["equity_irr_fraction"],
            base["summary"]["equity_irr_fraction"],
        )
        self.assertEqual(
            result["summary"]["buyer_savings_10yr_fraction"],
            base["summary"]["buyer_savings_10yr_fraction"],
        )

    def test_derivation_block_echoes_inputs_and_year_one_bases(self):
        result = self._run(exchange_rate_vnd_per_usd=25000)

        derivation = result["derivation"]
        self.assertEqual(derivation["structure"], "esco")
        self.assertEqual(derivation["project_years"], 3)
        self.assertEqual(derivation["exchange_rate_vnd_per_usd"], 25000)
        self.assertEqual(derivation["pv_capex_usd"], 1000000)
        self.assertEqual(derivation["bess_capex_usd"], 400000)
        self.assertAlmostEqual(
            derivation["base_energy_revenue_usd"], 1000 * 0.12 * 0.9
        )
        self.assertAlmostEqual(derivation["base_demand_savings_usd"], 20000)
        self.assertEqual(derivation["cit"]["standard_rate"], 0.20)
        self.assertEqual(derivation["cit"]["holiday_years"], 4)


class CitRegimeTests(TestCase):

    def _esco_case(self, **overrides):
        inputs = dict(
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
            evn_energy_escalation_rate=0.0,
            debt_fraction=0,
            project_years=25,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def _dppa_settlement(self, generator_fmp=3000000.0):
        return {
            "type": "grid_dppa_cfd",
            "esco_energy_revenue_vnd": 0.0,
            "year_one": {
                "c_dn_vnd": 100.0,
                "c_dppa_vnd": 25.0,
                "c_cl_vnd": 10.0,
                "c_bl_vnd": 40.0,
                "cfd_strike_revenue_vnd": 0.0,
                "cfd_fmp_offset_vnd": 0.0,
                "generator_fmp_revenue_vnd": generator_fmp,
            },
            "escalation": {"fee_escalation_rate": 0.0, "cfd_strike_escalation_rate": 0.0},
            "hourly_breakout": [],
            "monthly_breakout": [],
        }

    def test_dppa_case_defaults_to_re_producer_with_lower_cit_from_year_five(self):
        default_dppa = self._esco_case(dppa_settlement=self._dppa_settlement())
        standard_dppa = self._esco_case(
            dppa_settlement=self._dppa_settlement(),
            cit_regime="standard_with_holiday",
        )

        self.assertEqual(default_dppa["derivation"]["cit"]["regime"], "re_producer")
        # Year 5 (index 4) is the first reduced-rate year: 5% under re_producer
        # (10% preferential × 50%) vs 10% under the standard-holiday regime.
        # taxable = 3,000,000 generator revenue − 100,000 O&M − 100,000 dep.
        self.assertAlmostEqual(default_dppa["annual_cash_flows"][4]["cit_vnd"], 2800000.0 * 0.05)
        self.assertAlmostEqual(standard_dppa["annual_cash_flows"][4]["cit_vnd"], 2800000.0 * 0.10)
        self.assertLess(
            default_dppa["annual_cash_flows"][4]["cit_vnd"],
            standard_dppa["annual_cash_flows"][4]["cit_vnd"],
        )

    def test_esco_case_defaults_to_standard_with_holiday(self):
        result = self._esco_case()

        self.assertEqual(result["derivation"]["cit"]["regime"], "standard_with_holiday")
        # taxable = 2,700,000 revenue − 100,000 O&M − 100,000 dep = 2,500,000;
        # year 5 taxed at 10% (standard-holiday reduced rate).
        self.assertAlmostEqual(result["annual_cash_flows"][4]["cit_vnd"], 2500000.0 * 0.10)

    def test_explicit_cit_regime_overrides_structure_default(self):
        result = self._esco_case(cit_regime="re_producer")

        self.assertEqual(result["derivation"]["cit"]["regime"], "re_producer")
        # ESCO forced to re_producer: year 5 at 5% instead of the default 10%.
        self.assertAlmostEqual(result["annual_cash_flows"][4]["cit_vnd"], 2500000.0 * 0.05)

    def test_invalid_cit_regime_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._esco_case(cit_regime="not_a_regime")

    def test_result_derivation_carries_regime_and_preferential_params(self):
        result = self._esco_case(cit_regime="re_producer")

        cit = result["derivation"]["cit"]
        self.assertEqual(cit["regime"], "re_producer")
        self.assertEqual(cit["preferential_rate"], 0.10)
        self.assertEqual(cit["preferential_years"], 15)


class SurplusExportTests(TestCase):
    """Decree 243/2026 rooftop surplus-export revenue line (ESCO only).

    cash_flow receives pre-resolved primitives (year-1 sold kWh, USD price,
    escalation rate); the cap and price resolution live in esco_pro_forma.
    """

    def _run(self, **overrides):
        inputs = dict(
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
            debt_fraction=0,
            project_years=2,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def test_disabled_surplus_export_leaves_outputs_byte_identical(self):
        base = self._run()
        # Passing the sentinel explicitly must be indistinguishable from omitting it.
        disabled = self._run(surplus_export_kwh_year1=None)

        self.assertEqual(base["annual_cash_flows"], disabled["annual_cash_flows"])
        self.assertEqual(base["summary"], disabled["summary"])
        self.assertEqual(base["derivation"], disabled["derivation"])
        # No surplus keys or derivation block leak when disabled.
        self.assertNotIn("surplus_export_kwh", base["annual_cash_flows"][0])
        self.assertNotIn("surplus_export_revenue_vnd", base["annual_cash_flows"][0])
        self.assertNotIn("surplus_export", base["derivation"])

    def test_surplus_revenue_added_to_esco_revenue_when_enabled(self):
        result = self._run(
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2.0,
        )

        row = result["annual_cash_flows"][0]
        self.assertEqual(row["surplus_export_kwh"], 1000)
        self.assertEqual(row["surplus_export_revenue_vnd"], 2000.0)
        # Surplus revenue accrues to the developer's ESCO revenue aggregate.
        self.assertEqual(row["esco_revenue_vnd"], 2000.0)

    def test_surplus_export_does_not_contaminate_offtaker_cost(self):
        without = self._run()
        with_surplus = self._run(
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2.0,
        )

        # Surplus goes to EVN, not the factory: offtaker cost/savings unchanged.
        self.assertEqual(
            with_surplus["annual_cash_flows"][0]["offtaker_post_project_cost_vnd"],
            without["annual_cash_flows"][0]["offtaker_post_project_cost_vnd"],
        )
        self.assertEqual(
            with_surplus["annual_cash_flows"][0]["offtaker_savings_vnd"],
            without["annual_cash_flows"][0]["offtaker_savings_vnd"],
        )

    def test_surplus_volume_degrades_with_pv_degradation(self):
        result = self._run(
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2.0,
            pv_degradation_rate=0.01,
        )

        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["surplus_export_kwh"], 1000.0)
        self.assertAlmostEqual(rows[1]["surplus_export_kwh"], 990.0)
        self.assertAlmostEqual(rows[1]["surplus_export_revenue_vnd"], 990.0 * 2.0)

    def test_surplus_price_escalates_at_given_rate(self):
        result = self._run(
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2.0,
            surplus_price_escalation_rate=0.04,
        )

        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["surplus_export_revenue_vnd"], 2000.0)
        self.assertAlmostEqual(rows[1]["surplus_export_revenue_vnd"], 2000.0 * 1.04)

    def test_surplus_price_escalation_defaults_to_evn_energy_escalation(self):
        result = self._run(
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2.0,
            evn_energy_escalation_rate=0.04,
        )

        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(rows[1]["surplus_export_revenue_vnd"], 2000.0 * 1.04)

    def test_surplus_revenue_flows_to_equity_cash_flow_and_cit(self):
        without = self._run(
            project_years=25,
            pv_capex_vnd=2000000,
            annual_om_vnd=100000,
        )
        with_surplus = self._run(
            project_years=25,
            pv_capex_vnd=2000000,
            annual_om_vnd=100000,
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2000.0,
        )

        # Extra developer revenue lifts CFADS, equity cash flow and, once out of
        # the holiday, CIT — proving surplus feeds the taxable base.
        base_row = without["annual_cash_flows"][14]
        surplus_row = with_surplus["annual_cash_flows"][14]
        self.assertGreater(
            surplus_row["cash_available_for_debt_service_vnd"],
            base_row["cash_available_for_debt_service_vnd"],
        )
        self.assertGreater(
            surplus_row["equity_cash_flow_vnd"], base_row["equity_cash_flow_vnd"]
        )
        self.assertGreater(surplus_row["cit_vnd"], base_row["cit_vnd"])

    def test_surplus_export_rejected_under_dppa(self):
        with self.assertRaises(ValueError):
            self._run(
                surplus_export_kwh_year1=1000,
                surplus_export_price_usd_per_kwh=2.0,
                dppa_settlement={
                    "type": "grid_dppa_cfd",
                    "esco_energy_revenue_vnd": 0.0,
                    "year_one": {
                        "c_dn_vnd": 100.0,
                        "c_dppa_vnd": 25.0,
                        "c_cl_vnd": 10.0,
                        "c_bl_vnd": 40.0,
                        "cfd_strike_revenue_vnd": 0.0,
                        "cfd_fmp_offset_vnd": 0.0,
                        "generator_fmp_revenue_vnd": 200.0,
                    },
                    "escalation": {"fee_escalation_rate": 0.0, "cfd_strike_escalation_rate": 0.0},
                    "hourly_breakout": [],
                    "monthly_breakout": [],
                },
            )

    def test_derivation_carries_surplus_block_when_enabled(self):
        result = self._run(
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2.0,
            surplus_price_escalation_rate=0.03,
            surplus_cap_fraction=0.5,
        )

        surplus = result["derivation"]["surplus_export"]
        self.assertEqual(surplus["sold_kwh_year1"], 1000)
        self.assertEqual(surplus["price_usd_per_kwh"], 2.0)
        self.assertEqual(surplus["price_escalation_rate"], 0.03)
        self.assertEqual(surplus["cap_fraction"], 0.5)

    def test_surplus_revenue_restated_to_vnd_with_exchange_rate(self):
        result = self._run(
            surplus_export_kwh_year1=1000,
            surplus_export_price_usd_per_kwh=2.0,
            exchange_rate_vnd_per_usd=25000,
        )

        row = result["annual_cash_flows"][0]
        # _usd holds the computed (model-currency) value, _vnd is restated at FX.
        self.assertEqual(row["surplus_export_revenue_usd"], 2000.0)
        self.assertEqual(row["surplus_export_revenue_vnd"], 2000.0 * 25000)


class PhysicalDppaTests(TestCase):
    """ND57 Điều 25 private-wire DPPA: matched energy paid at a freely
    negotiated PPA price, surplus to EVN, no grid-CfD settlement chain.

    cash_flow receives pre-resolved primitives (matched kWh year 1, USD price,
    escalation); esco_pro_forma extracts the series and converts the price.
    """

    def _run(self, physical_dppa=None, **overrides):
        physical = {
            "matched_kwh_year1": 1000.0,
            "ppa_price_usd_per_kwh": 2.0,
            "ppa_price_escalation_rate": 0.0,
        }
        if physical_dppa is not None:
            physical.update(physical_dppa)
        inputs = dict(
            project_served_pv_kwh=[100.0, 100.0],
            evn_energy_rates_vnd_per_kwh=[10.0, 10.0],
            bau_evn_bill_vnd=100000.0,
            optimized_evn_bill_vnd=60000.0,
            bau_demand_charge_vnd=0.0,
            optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=0.0,
            bess_capex_vnd=0.0,
            annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0,
            evn_capacity_escalation_rate=0.0,
            debt_fraction=0.0,
            project_years=2,
            physical_dppa=physical,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def test_resolve_structure_returns_physical_dppa(self):
        from proforma_vietnam.structures import PHYSICAL_DPPA, resolve_structure

        self.assertEqual(resolve_structure(physical_dppa={"x": 1}), PHYSICAL_DPPA)
        self.assertEqual(self._run()["derivation"]["structure"], PHYSICAL_DPPA)

    def test_mutual_exclusion_physical_and_cfd_raises(self):
        with self.assertRaises(ValueError):
            self._run(dppa_settlement={"year_one": {}, "escalation": {}})

    def test_developer_ppa_energy_revenue_is_matched_kwh_times_price(self):
        row = self._run()["annual_cash_flows"][0]
        self.assertAlmostEqual(row["ppa_matched_kwh"], 1000.0)
        self.assertAlmostEqual(row["ppa_energy_revenue_vnd"], 2000.0)
        # The PPA payment is the developer's energy line and its whole revenue
        # (no demand/arbitrage/surplus configured here).
        self.assertAlmostEqual(row["esco_energy_revenue_vnd"], 2000.0)
        self.assertAlmostEqual(row["esco_revenue_vnd"], 2000.0)

    def test_buyer_cost_adds_ppa_payment_to_residual_evn_bill(self):
        row = self._run()["annual_cash_flows"][0]
        # optimized residual EVN bill (60000) + PPA payment (2000); no demand.
        self.assertAlmostEqual(row["offtaker_post_project_cost_vnd"], 62000.0)
        self.assertAlmostEqual(row["offtaker_savings_vnd"], 100000.0 - 62000.0)

    def test_ppa_price_escalates_at_its_own_rate(self):
        rows = self._run(physical_dppa={"ppa_price_escalation_rate": 0.05})["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["ppa_energy_revenue_vnd"], 2000.0)
        self.assertAlmostEqual(rows[1]["ppa_energy_revenue_vnd"], 2000.0 * 1.05)

    def test_ppa_energy_ignores_evn_energy_escalation(self):
        # Flat PPA must NOT drift with the EVN tariff escalation — proves no
        # discount-to-EVN / CfD escalation leaks into the private-wire energy line.
        rows = self._run(evn_energy_escalation_rate=0.10)["annual_cash_flows"]
        self.assertAlmostEqual(rows[1]["ppa_energy_revenue_vnd"], 2000.0)

    def test_matched_energy_and_revenue_degrade_with_pv(self):
        rows = self._run(pv_degradation_rate=0.10)["annual_cash_flows"]
        self.assertAlmostEqual(rows[1]["ppa_matched_kwh"], 900.0)
        self.assertAlmostEqual(rows[1]["ppa_energy_revenue_vnd"], 1800.0)

    def test_degradation_repurchase_grows_buyer_residual_bill(self):
        # Energy lost to degradation is repurchased from EVN at retail, exactly
        # as the ESCO branch does. base served retail = 100*10 + 100*10 = 2000.
        rows = self._run(pv_degradation_rate=0.10)["annual_cash_flows"]
        self.assertAlmostEqual(rows[1]["optimized_evn_bill_vnd"], 60000.0 + 2000.0 * 0.10)

    def test_cit_regime_defaults_to_re_producer(self):
        cit = self._run()["derivation"]["cit"]
        self.assertEqual(cit["regime"], "re_producer")
        self.assertIn("preferential_rate", cit)

    def test_derivation_carries_physical_dppa_block(self):
        physical = self._run(physical_dppa={"ppa_price_escalation_rate": 0.03})["derivation"]["physical_dppa"]
        self.assertAlmostEqual(physical["matched_kwh_year1"], 1000.0)
        self.assertAlmostEqual(physical["ppa_price_usd_per_kwh"], 2.0)
        self.assertAlmostEqual(physical["ppa_price_escalation_rate"], 0.03)

    def test_surplus_leg_reuses_esco_machinery_without_double_counting(self):
        row = self._run(
            surplus_export_kwh_year1=500.0,
            surplus_export_price_usd_per_kwh=1.0,
        )["annual_cash_flows"][0]
        # Matched (PV/battery→load) and surplus (PV→grid + curtailed) are disjoint
        # series: developer revenue = PPA 2000 + surplus 500, no overlap.
        self.assertAlmostEqual(row["surplus_export_revenue_vnd"], 500.0)
        self.assertAlmostEqual(row["esco_revenue_vnd"], 2500.0)
        # Surplus goes to EVN, not the factory: buyer cost is unchanged.
        self.assertAlmostEqual(row["offtaker_post_project_cost_vnd"], 62000.0)

    def test_no_cfd_settlement_keys_leak_into_physical_rows(self):
        row = self._run()["annual_cash_flows"][0]
        for leaked in ("c_dn_vnd", "c_bl_vnd", "cfd_net_vnd",
                       "generator_revenue_vnd", "dppa_offtaker_cost_vnd"):
            self.assertNotIn(leaked, row)

    def test_physical_keys_absent_and_esco_unchanged_without_block(self):
        # An ESCO run (no physical_dppa) must not gain PPA keys or a derivation.
        esco = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[100.0, 100.0],
            evn_energy_rates_vnd_per_kwh=[10.0, 10.0],
            bau_evn_bill_vnd=100000.0,
            optimized_evn_bill_vnd=60000.0,
            bau_demand_charge_vnd=0.0,
            optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=0.0,
            bess_capex_vnd=0.0,
            annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            debt_fraction=0.0,
            project_years=2,
        )
        self.assertNotIn("ppa_energy_revenue_vnd", esco["annual_cash_flows"][0])
        self.assertNotIn("ppa_matched_kwh", esco["annual_cash_flows"][0])
        self.assertNotIn("physical_dppa", esco["derivation"])

    def test_ppa_revenue_restated_to_vnd_with_exchange_rate(self):
        row = self._run(exchange_rate_vnd_per_usd=25000)["annual_cash_flows"][0]
        self.assertAlmostEqual(row["ppa_energy_revenue_usd"], 2000.0)
        self.assertAlmostEqual(row["ppa_energy_revenue_vnd"], 2000.0 * 25000)


class DirectOwnershipTests(TestCase):
    """Factory self-invest benchmark: benefit is the FULL avoided EVN bill
    (energy + demand), no ESCO discount / 80/20 split; flat 20% CIT with the
    profitable-host shield by default."""

    def _run(self, direct_ownership=None, **overrides):
        inputs = dict(
            project_served_pv_kwh=[100.0, 100.0],
            evn_energy_rates_vnd_per_kwh=[10.0, 10.0],
            bau_evn_bill_vnd=100000.0,
            optimized_evn_bill_vnd=60000.0,
            bau_demand_charge_vnd=0.0,
            optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=0.0,
            bess_capex_vnd=0.0,
            annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0,
            evn_capacity_escalation_rate=0.0,
            debt_fraction=0.0,
            project_years=2,
            direct_ownership={} if direct_ownership is None else direct_ownership,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def test_resolve_structure_returns_direct_ownership(self):
        from proforma_vietnam.structures import DIRECT_OWNERSHIP, resolve_structure

        self.assertEqual(resolve_structure(direct_ownership={}), DIRECT_OWNERSHIP)
        self.assertEqual(self._run()["derivation"]["structure"], DIRECT_OWNERSHIP)

    def test_mutual_exclusion_with_cfd_settlement_raises(self):
        with self.assertRaises(ValueError):
            self._run(dppa_settlement={"year_one": {}, "escalation": {}})

    def test_mutual_exclusion_with_physical_dppa_raises(self):
        with self.assertRaises(ValueError):
            self._run(physical_dppa={
                "matched_kwh_year1": 1.0, "ppa_price_usd_per_kwh": 1.0,
            })

    def test_bill_savings_is_full_evn_bill_delta(self):
        row = self._run()["annual_cash_flows"][0]
        # BAU 100000 − optimized 60000 = 40000 (energy + demand, full delta).
        self.assertAlmostEqual(row["bill_savings_revenue_vnd"], 40000.0)
        # No ESCO discount / demand-split / arbitrage lines for the factory.
        self.assertAlmostEqual(row["esco_energy_revenue_vnd"], 0.0)
        self.assertAlmostEqual(row["esco_demand_revenue_vnd"], 0.0)
        self.assertAlmostEqual(row["esco_grid_arbitrage_revenue_vnd"], 0.0)
        # Total developer revenue is the full bill savings (no surplus here).
        self.assertAlmostEqual(row["esco_revenue_vnd"], 40000.0)

    def test_full_demand_delta_is_captured_without_80_20_split(self):
        # With a demand delta, the factory keeps 100% of it (it is inside the
        # total-bill delta), not the ESCO 80% share.
        row = self._run(
            bau_evn_bill_vnd=100000.0,
            optimized_evn_bill_vnd=60000.0,
            bau_demand_charge_vnd=30000.0,
            optimized_demand_charge_vnd=10000.0,
        )["annual_cash_flows"][0]
        # bill savings = total bau − total opt = 40000 (demand already inside).
        self.assertAlmostEqual(row["bill_savings_revenue_vnd"], 40000.0)
        self.assertAlmostEqual(row["esco_demand_revenue_vnd"], 0.0)

    def test_buyer_view_equals_developer_view(self):
        row = self._run()["annual_cash_flows"][0]
        # The factory IS the investor: residual cost is the optimized bill and
        # savings equal the bill-savings revenue line (no ESCO fee).
        self.assertAlmostEqual(row["offtaker_post_project_cost_vnd"], 60000.0)
        self.assertAlmostEqual(row["offtaker_savings_vnd"], 40000.0)
        self.assertAlmostEqual(
            row["offtaker_savings_vnd"], row["bill_savings_revenue_vnd"]
        )

    def test_default_regime_is_standard_flat_20_percent(self):
        result = self._run()
        cit = result["derivation"]["cit"]
        self.assertEqual(cit["regime"], "standard_flat")
        self.assertEqual(cit["holiday_years"], 0)
        self.assertEqual(cit["reduced_rate_years"], 0)
        self.assertNotIn("preferential_rate", cit)
        # Flat 20% every year on positive income: 40000 × 0.20 = 8000.
        for row in result["annual_cash_flows"]:
            self.assertAlmostEqual(row["cit_vnd"], 8000.0)

    def test_explicit_cit_regime_override_is_honored(self):
        result = self._run(
            direct_ownership={"assume_profitable_host": False},
            cit_regime="re_producer",
        )
        cit = result["derivation"]["cit"]
        self.assertEqual(cit["regime"], "re_producer")
        self.assertIn("preferential_rate", cit)

    def test_invalid_cit_regime_raises(self):
        with self.assertRaises(ValueError):
            self._run(cit_regime="not_a_regime")

    def test_negative_taxable_income_yields_negative_cit_shield(self):
        # Year-1 replacement expense drives EBT negative; the profitable host
        # takes an immediate shield (negative CIT), then pays on the year-2 profit.
        cit = [
            row["cit_vnd"]
            for row in self._run(replacement_costs_by_year=[80000.0])["annual_cash_flows"]
        ]
        self.assertAlmostEqual(cit[0], -8000.0)   # (40000 − 80000) × 0.20
        self.assertAlmostEqual(cit[1], 8000.0)    # 40000 × 0.20

    def test_carryforward_path_when_profitable_host_disabled(self):
        # Standalone treatment: the year-1 loss pays no CIT and carries forward
        # FIFO to zero out the year-2 profit (no immediate shield).
        cit = [
            row["cit_vnd"]
            for row in self._run(
                direct_ownership={"assume_profitable_host": False},
                replacement_costs_by_year=[80000.0],
            )["annual_cash_flows"]
        ]
        self.assertAlmostEqual(cit[0], 0.0)
        self.assertAlmostEqual(cit[1], 0.0)

    def test_profitable_host_with_preferential_regime_raises(self):
        # The immediate-shield convention is only defined for the flat
        # standard regime; layering it on the re_producer preferential/holiday
        # schedule is undefined economics (default host convention, explicit
        # regime override).
        with self.assertRaises(ValueError) as context:
            self._run(cit_regime="re_producer")
        self.assertIn("assume_profitable_host", str(context.exception))

    def test_preferential_regime_with_host_disabled_uses_carryforward(self):
        # host disabled routes to the FIFO carryforward branch
        # (immediate_loss_relief=False) with the re_producer preferential/
        # holiday schedule applied to the eventual taxed income.
        cit = [
            row["cit_vnd"]
            for row in self._run(
                direct_ownership={"assume_profitable_host": False},
                cit_regime="re_producer",
                replacement_costs_by_year=[0.0, 0.0, 80000.0, 0.0, 0.0],
                project_years=5,
            )["annual_cash_flows"]
        ]
        # Year 1 (index 0): within the 4-year holiday (clock starts at the
        # first profitable year, index 0).
        self.assertAlmostEqual(cit[0], 0.0)
        # Year 3 (index 2) loss: carried forward, not an immediate shield — CIT
        # is exactly 0, not the -4000 an immediate-relief path would give
        # (-40000 loss x 10% preferential rate).
        self.assertAlmostEqual(cit[2], 0.0)
        # Year 5 (index 4): past the holiday, in the 9-year reduced-rate
        # window, at the re_producer preferential 10% base rate:
        # 40000 x (0.10 x 0.50) = 2000.
        self.assertAlmostEqual(cit[4], 2000.0)

    def test_surplus_export_is_in_the_taxable_base_and_revenue(self):
        row = self._run(
            surplus_export_kwh_year1=500.0,
            surplus_export_price_usd_per_kwh=1.0,
        )["annual_cash_flows"][0]
        self.assertAlmostEqual(row["surplus_export_revenue_vnd"], 500.0)
        # revenue = bill savings 40000 + surplus 500; CIT taxes both.
        self.assertAlmostEqual(row["esco_revenue_vnd"], 40500.0)
        self.assertAlmostEqual(row["cit_vnd"], 40500.0 * 0.20)
        # Surplus goes to EVN, so the buyer's residual cost is unchanged.
        self.assertAlmostEqual(row["offtaker_post_project_cost_vnd"], 60000.0)

    def test_bill_savings_shrinks_with_degradation_repurchase(self):
        # base served retail = 100×10 + 100×10 = 2000; year-2 degradation grows
        # the residual bill by 2000 × 0.10 = 200, shrinking the savings.
        rows = self._run(pv_degradation_rate=0.10)["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["bill_savings_revenue_vnd"], 40000.0)
        self.assertAlmostEqual(rows[1]["bill_savings_revenue_vnd"], 40000.0 - 200.0)

    def test_developer_metrics_use_incremental_cash_flow(self):
        # CFADS = savings + surplus − opex − CIT; here 40000 − 8000 = 32000.
        row = self._run()["annual_cash_flows"][0]
        self.assertAlmostEqual(row["cash_available_for_debt_service_vnd"], 32000.0)
        self.assertAlmostEqual(row["equity_cash_flow_vnd"], 32000.0)

    def test_no_cfd_or_ppa_keys_leak_into_direct_rows(self):
        row = self._run()["annual_cash_flows"][0]
        for leaked in ("ppa_energy_revenue_vnd", "ppa_matched_kwh", "c_dn_vnd",
                       "cfd_net_vnd", "generator_revenue_vnd"):
            self.assertNotIn(leaked, row)

    def test_direct_keys_absent_and_esco_unchanged_without_block(self):
        esco = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[100.0, 100.0],
            evn_energy_rates_vnd_per_kwh=[10.0, 10.0],
            bau_evn_bill_vnd=100000.0,
            optimized_evn_bill_vnd=60000.0,
            bau_demand_charge_vnd=0.0,
            optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=0.0,
            bess_capex_vnd=0.0,
            annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            debt_fraction=0.0,
            project_years=2,
        )
        self.assertNotIn("bill_savings_revenue_vnd", esco["annual_cash_flows"][0])
        self.assertNotIn("direct_ownership", esco["derivation"])
        self.assertEqual(esco["derivation"]["cit"]["regime"], "standard_with_holiday")

    def test_bill_savings_restated_to_vnd_with_exchange_rate(self):
        row = self._run(exchange_rate_vnd_per_usd=25000)["annual_cash_flows"][0]
        self.assertAlmostEqual(row["bill_savings_revenue_usd"], 40000.0)
        self.assertAlmostEqual(row["bill_savings_revenue_vnd"], 40000.0 * 25000)


class ConstructionAndGraceTests(TestCase):
    """Construction period with capitalized IDC + principal grace (default OFF).

    Shared financing machinery for every structure. Hand-computed fixture:
    capex 1,000,000 (pv 700,000 + bess 300,000), 70% debt, 8.5%, 12 months →
    IDC = 700,000 × 0.085 × (12/12) / 2 = 29,750; COD debt = 729,750; equity
    unchanged at 300,000; depreciable base = 1,029,750 split pro-rata
    (pv 720,825 / bess 308,925).
    """

    def _run(self, **overrides):
        inputs = dict(
            project_served_pv_kwh=[100000.0],
            evn_energy_rates_vnd_per_kwh=[2.0],
            bau_evn_bill_vnd=400000.0,
            optimized_evn_bill_vnd=200000.0,
            bau_demand_charge_vnd=0.0,
            optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=700000.0,
            bess_capex_vnd=300000.0,
            annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0,
            evn_capacity_escalation_rate=0.0,
            debt_fraction=0.70,
            debt_interest_rate_fraction=0.085,
            debt_term_years=10,
            project_years=25,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def test_idc_hand_computed_fixture(self):
        result = self._run(construction_months=12)

        construction = result["derivation"]["construction"]
        self.assertEqual(construction["construction_months"], 12)
        self.assertEqual(construction["principal_grace_years"], 0)
        self.assertAlmostEqual(construction["idc_usd"], 29750.0)
        self.assertAlmostEqual(construction["cod_debt_balance_usd"], 729750.0)
        # IDC is debt-funded (rolled up): equity is unchanged.
        self.assertAlmostEqual(result["summary"]["equity_investment_vnd"], 300000.0)
        self.assertAlmostEqual(result["summary"]["debt_principal_vnd"], 700000.0)
        self.assertAlmostEqual(result["summary"]["idc_vnd"], 29750.0)
        self.assertAlmostEqual(result["summary"]["cod_debt_balance_vnd"], 729750.0)
        # Year-1 interest accrues on the full COD balance.
        self.assertAlmostEqual(
            result["annual_cash_flows"][0]["interest_vnd"], 729750.0 * 0.085
        )

    def test_depreciable_base_includes_idc_pro_rata_with_no_leakage(self):
        result = self._run(construction_months=12)

        # Year-1 per-class depreciation includes each class's pro-rata IDC
        # share on its existing schedule (pv 20y, bess 8y).
        self.assertAlmostEqual(
            result["annual_cash_flows"][0]["depreciation_vnd"],
            720825.0 / 20 + 308925.0 / 8,
        )
        # Total depreciation over the horizon equals the full base (no leakage).
        self.assertAlmostEqual(
            sum(row["depreciation_vnd"] for row in result["annual_cash_flows"]),
            1029750.0,
        )

    def test_grace_years_are_interest_only_then_principal_amortizes(self):
        result = self._run(principal_grace_years=3)

        rows = result["annual_cash_flows"]
        # Years 1..3: interest-only on the full COD balance (no IDC here).
        for row in rows[:3]:
            self.assertAlmostEqual(row["principal_vnd"], 0.0)
            self.assertAlmostEqual(row["interest_vnd"], 700000.0 * 0.085)
            self.assertAlmostEqual(row["debt_service_vnd"], 700000.0 * 0.085)
            self.assertAlmostEqual(row["ending_debt_balance_vnd"], 700000.0)
        # Principal starts in year g+1 and amortizes over the remaining 7 years.
        self.assertGreater(rows[3]["principal_vnd"], 0.0)
        self.assertAlmostEqual(
            sum(row["principal_vnd"] for row in rows), 700000.0
        )
        self.assertAlmostEqual(rows[9]["ending_debt_balance_vnd"], 0.0)
        # DSCR during grace reflects interest-only debt service (higher).
        self.assertGreater(rows[0]["dscr"], rows[3]["dscr"])

    def test_combined_construction_and_grace_fixture(self):
        result = self._run(construction_months=12, principal_grace_years=2)

        construction = result["derivation"]["construction"]
        self.assertAlmostEqual(construction["idc_usd"], 29750.0)
        self.assertAlmostEqual(construction["cod_debt_balance_usd"], 729750.0)
        rows = result["annual_cash_flows"]
        # Grace years are interest-only on the rolled-up COD balance.
        self.assertAlmostEqual(rows[0]["principal_vnd"], 0.0)
        self.assertAlmostEqual(rows[0]["interest_vnd"], 729750.0 * 0.085)
        self.assertAlmostEqual(rows[1]["ending_debt_balance_vnd"], 729750.0)
        # Sum of principal payments retires the full COD balance.
        self.assertAlmostEqual(
            sum(row["principal_vnd"] for row in rows), 729750.0
        )

    def test_idc_lowers_equity_irr_versus_overnight_build(self):
        overnight = self._run()
        construction = self._run(construction_months=12)

        # Same equity outlay, extra rolled-up debt to service: IRR must fall.
        self.assertLess(
            construction["summary"]["equity_irr_fraction"],
            overnight["summary"]["equity_irr_fraction"],
        )

    def test_validation_rejects_out_of_range_and_non_int_inputs(self):
        for bad_kwargs in (
            {"construction_months": 37},
            {"construction_months": -1},
            {"construction_months": 12.0},
            {"construction_months": "12"},
            {"construction_months": True},
            {"principal_grace_years": 10},   # == debt_term_years
            {"principal_grace_years": 11},   # > debt_term_years
            {"principal_grace_years": -1},
            {"principal_grace_years": 2.5},
            {"principal_grace_years": True},
        ):
            with self.assertRaises(ValueError, msg=bad_kwargs):
                self._run(**bad_kwargs)

    def test_disabled_defaults_leave_outputs_byte_identical(self):
        base = self._run()
        # Passing the defaults explicitly must be indistinguishable from
        # omitting them.
        disabled = self._run(construction_months=0, principal_grace_years=0)

        self.assertEqual(base["annual_cash_flows"], disabled["annual_cash_flows"])
        self.assertEqual(base["summary"], disabled["summary"])
        self.assertEqual(base["derivation"], disabled["derivation"])
        # No construction keys leak when disabled.
        self.assertNotIn("construction", base["derivation"])
        self.assertNotIn("idc_vnd", base["summary"])
        self.assertNotIn("idc_usd", base["summary"])
        self.assertNotIn("cod_debt_balance_vnd", base["summary"])

    def test_construction_and_grace_apply_under_direct_ownership(self):
        result = self._run(
            direct_ownership={},
            construction_months=12,
            principal_grace_years=2,
        )

        construction = result["derivation"]["construction"]
        self.assertAlmostEqual(construction["idc_usd"], 29750.0)
        row = result["annual_cash_flows"][0]
        self.assertAlmostEqual(row["principal_vnd"], 0.0)
        self.assertAlmostEqual(row["interest_vnd"], 729750.0 * 0.085)

    def test_construction_and_grace_apply_under_dppa(self):
        settlement = {
            "year_one": {
                "c_dn_vnd": 0.0, "c_dppa_vnd": 0.0, "c_cl_vnd": 0.0,
                "c_bl_vnd": 0.0, "cfd_strike_revenue_vnd": 0.0,
                "cfd_fmp_offset_vnd": 0.0,
                "generator_fmp_revenue_vnd": 200000.0,
            },
            "escalation": {},
        }
        result = self._run(
            dppa_settlement=settlement,
            construction_months=12,
            principal_grace_years=2,
        )

        construction = result["derivation"]["construction"]
        self.assertAlmostEqual(construction["idc_usd"], 29750.0)
        self.assertAlmostEqual(construction["cod_debt_balance_usd"], 729750.0)
        row = result["annual_cash_flows"][0]
        self.assertAlmostEqual(row["principal_vnd"], 0.0)
        self.assertAlmostEqual(row["interest_vnd"], 729750.0 * 0.085)

    def test_idc_restated_to_vnd_with_exchange_rate(self):
        result = self._run(construction_months=12, exchange_rate_vnd_per_usd=25000)

        self.assertAlmostEqual(result["summary"]["idc_usd"], 29750.0)
        self.assertAlmostEqual(
            result["summary"]["idc_vnd"], 29750.0 * 25000, delta=0.01
        )
        self.assertAlmostEqual(result["summary"]["cod_debt_balance_usd"], 729750.0)


class UsdDebtTests(TestCase):
    """USD-denominated debt option (default VND). The base case is mechanically
    identical to VND debt except the interest-rate default; the FX exposure is
    surfaced only on the FX-sensitivity block (see UsdDebtFxSensitivityTests).
    """

    def _run(self, **overrides):
        inputs = dict(
            project_served_pv_kwh=[100000.0],
            evn_energy_rates_vnd_per_kwh=[2.0],
            bau_evn_bill_vnd=400000.0,
            optimized_evn_bill_vnd=200000.0,
            bau_demand_charge_vnd=0.0,
            optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=700000.0,
            bess_capex_vnd=300000.0,
            annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0,
            evn_capacity_escalation_rate=0.0,
            debt_fraction=0.70,
            debt_term_years=10,
            project_years=25,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def test_equal_rate_usd_and_vnd_produce_identical_base_case(self):
        # Contract FX held flat: with an explicit identical rate the two
        # currencies must run the debt schedule / IDC / DSCR / tax deduction
        # byte-for-byte the same. Only the derivation carries the currency label.
        vnd = self._run(debt_currency="VND", debt_interest_rate_fraction=0.07)
        usd = self._run(debt_currency="USD", debt_interest_rate_fraction=0.07)

        self.assertEqual(vnd["annual_cash_flows"], usd["annual_cash_flows"])
        self.assertEqual(vnd["summary"], usd["summary"])
        # The only base-case difference is the disclosed currency label.
        self.assertNotIn("debt_currency", vnd["derivation"])
        self.assertEqual(usd["derivation"]["debt_currency"], "USD")

    def test_equal_rate_equivalence_holds_with_construction_and_grace(self):
        # Task 4a interaction: IDC + grace run in USD exactly as in VND when the
        # rate is pinned equal.
        common = dict(
            debt_interest_rate_fraction=0.07,
            construction_months=12,
            principal_grace_years=2,
        )
        vnd = self._run(debt_currency="VND", **common)
        usd = self._run(debt_currency="USD", **common)

        self.assertEqual(vnd["annual_cash_flows"], usd["annual_cash_flows"])
        self.assertEqual(vnd["summary"], usd["summary"])

    def test_usd_default_rate_resolves_to_versioned_default(self):
        from proforma_vietnam.defaults import FINANCIAL_DEFAULTS

        usd = self._run(debt_currency="USD")
        vnd = self._run(debt_currency="VND")

        self.assertEqual(
            usd["derivation"]["debt_interest_rate_fraction"],
            FINANCIAL_DEFAULTS["usd_debt_interest_rate"],
        )
        self.assertEqual(
            usd["derivation"]["debt_interest_rate_fraction"], 0.05
        )
        # VND is untouched at the existing 8.5% default.
        self.assertEqual(
            vnd["derivation"]["debt_interest_rate_fraction"],
            FINANCIAL_DEFAULTS["debt_interest_rate"],
        )

    def test_explicit_rate_override_wins_regardless_of_currency(self):
        usd = self._run(debt_currency="USD", debt_interest_rate_fraction=0.061)
        vnd = self._run(debt_currency="VND", debt_interest_rate_fraction=0.061)

        self.assertEqual(usd["derivation"]["debt_interest_rate_fraction"], 0.061)
        self.assertEqual(vnd["derivation"]["debt_interest_rate_fraction"], 0.061)

    def test_usd_idc_uses_resolved_usd_rate(self):
        # Task 4a interaction: with the default USD rate (5%) the IDC rolls into
        # the COD balance at that rate. capex 1,000,000 × 0.7 debt × 0.05 × 1yr /2.
        usd = self._run(debt_currency="USD", construction_months=12)

        construction = usd["derivation"]["construction"]
        self.assertAlmostEqual(construction["idc_usd"], 700000.0 * 0.05 * 0.5)
        self.assertAlmostEqual(
            construction["cod_debt_balance_usd"], 700000.0 + 17500.0
        )
        # Grace pattern intact at the USD rate on the rolled-up balance.
        usd_grace = self._run(
            debt_currency="USD", construction_months=12, principal_grace_years=2
        )
        rows = usd_grace["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["principal_vnd"], 0.0)
        self.assertAlmostEqual(rows[0]["interest_vnd"], 717500.0 * 0.05)
        self.assertAlmostEqual(rows[1]["ending_debt_balance_vnd"], 717500.0)

    def test_validation_rejects_unknown_or_non_str_currency(self):
        for bad in ("EUR", "usd", "vnd", "", 5, None, True):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self._run(debt_currency=bad)

    def test_default_currency_leaves_outputs_byte_identical(self):
        base = self._run()
        explicit = self._run(debt_currency="VND")

        self.assertEqual(base["annual_cash_flows"], explicit["annual_cash_flows"])
        self.assertEqual(base["summary"], explicit["summary"])
        self.assertEqual(base["derivation"], explicit["derivation"])
        # No currency key leaks on the default VND path.
        self.assertNotIn("debt_currency", base["derivation"])


class FxSensitivityTests(TestCase):

    def test_zero_depreciation_scenario_reproduces_base_metrics(self):
        from proforma_vietnam.cash_flow import calculate_fx_sensitivity

        result = calculate_vietnam_esco_cash_flow(
            project_served_pv_kwh=[100000],
            evn_energy_rates_vnd_per_kwh=[0.10],
            bau_evn_bill_vnd=20000,
            optimized_evn_bill_vnd=12000,
            bau_demand_charge_vnd=4000,
            optimized_demand_charge_vnd=2000,
            pv_capex_vnd=50000,
            bess_capex_vnd=20000,
            annual_om_vnd=1000,
            esco_energy_discount_fraction=0.9,
            project_years=25,
        )
        table = calculate_fx_sensitivity(result)

        self.assertEqual(table[0]["vnd_depreciation_rate"], 0.0)
        self.assertAlmostEqual(
            table[0]["equity_irr_fraction"],
            result["summary"]["equity_irr_fraction"],
            places=6,
        )
        self.assertAlmostEqual(
            table[0]["npv_usd"], result["summary"]["npv_usd"], places=4
        )
        # Faster VND depreciation strictly erodes the USD-reported return.
        irrs = [row["equity_irr_fraction"] for row in table]
        self.assertEqual(irrs, sorted(irrs, reverse=True))
        npvs = [row["npv_usd"] for row in table]
        self.assertEqual(npvs, sorted(npvs, reverse=True))


def _synthetic_fx_result(debt_currency):
    """Two-year fixture with hand-chosen CFADS / debt service per year so the
    FX decomposition and min-DSCR are verifiable by hand."""
    rows = [
        {
            "cash_available_for_debt_service_usd": 60.0,
            "debt_service_usd": 40.0,
            "equity_cash_flow_usd": 20.0,
            "dscr": 1.5,
        },
        {
            "cash_available_for_debt_service_usd": 88.0,
            "debt_service_usd": 40.0,
            "equity_cash_flow_usd": 48.0,
            "dscr": 2.2,
        },
    ]
    derivation = {"owner_discount_rate_fraction": 0.10}
    if debt_currency is not None:
        derivation["debt_currency"] = debt_currency
    return {
        "annual_cash_flows": rows,
        "summary": {"equity_investment_usd": 100.0},
        "derivation": derivation,
    }


class UsdDebtFxSensitivityTests(TestCase):
    """USD-debt FX exposure: revenue is VND-denominated and deflates by (1+d)^t,
    but USD debt service is fixed, so DSCR erodes with depreciation. VND debt
    keeps the whole-flow deflation and a depreciation-invariant DSCR.
    """

    def _engine(self, debt_currency, **overrides):
        inputs = dict(
            project_served_pv_kwh=[100000],
            evn_energy_rates_vnd_per_kwh=[0.10],
            bau_evn_bill_vnd=20000,
            optimized_evn_bill_vnd=12000,
            bau_demand_charge_vnd=4000,
            optimized_demand_charge_vnd=2000,
            pv_capex_vnd=50000,
            bess_capex_vnd=20000,
            annual_om_vnd=1000,
            esco_energy_discount_fraction=0.9,
            debt_interest_rate_fraction=0.05,
            project_years=25,
            debt_currency=debt_currency,
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    def test_zero_depreciation_row_equals_base_case_for_both_currencies(self):
        from proforma_vietnam.cash_flow import _irr, _npv, calculate_fx_sensitivity

        for currency in ("VND", "USD", None):
            result = _synthetic_fx_result(currency)
            table = calculate_fx_sensitivity(result, vnd_depreciation_rates=(0.0,))
            base = [-100.0, 20.0, 48.0]

            self.assertEqual(table[0]["vnd_depreciation_rate"], 0.0)
            self.assertAlmostEqual(table[0]["equity_irr_fraction"], _irr(base))
            self.assertAlmostEqual(table[0]["npv_usd"], _npv(0.10, base))
            # d=0 min DSCR is the base minimum for both currencies.
            self.assertAlmostEqual(table[0]["min_dscr"], 1.5)

    def test_usd_decomposition_and_min_dscr_hand_computed(self):
        from proforma_vietnam.cash_flow import _irr, _npv, calculate_fx_sensitivity

        result = _synthetic_fx_result("USD")
        table = calculate_fx_sensitivity(result, vnd_depreciation_rates=(0.0, 0.10))

        # USD debt service is fixed; VND revenue (CFADS) deflates by (1+d)^t.
        expected = [-100.0, 60.0 / 1.1 - 40.0, 88.0 / 1.21 - 40.0]
        self.assertAlmostEqual(table[1]["equity_irr_fraction"], _irr(expected))
        self.assertAlmostEqual(table[1]["npv_usd"], _npv(0.10, expected))
        # min DSCR = min over debt years of (CFADS_t/(1+d)^t)/debt_service_t.
        self.assertAlmostEqual(
            table[1]["min_dscr"],
            min((60.0 / 1.1) / 40.0, (88.0 / 1.21) / 40.0),
        )

    def test_vnd_decomposition_and_constant_min_dscr(self):
        from proforma_vietnam.cash_flow import _irr, _npv, calculate_fx_sensitivity

        result = _synthetic_fx_result("VND")
        table = calculate_fx_sensitivity(result, vnd_depreciation_rates=(0.0, 0.10))

        # VND debt: the whole equity flow deflates (legacy behaviour).
        expected = [-100.0, 20.0 / 1.1, 48.0 / 1.21]
        self.assertAlmostEqual(table[1]["equity_irr_fraction"], _irr(expected))
        self.assertAlmostEqual(table[1]["npv_usd"], _npv(0.10, expected))
        # DSCR is FX-neutral for VND debt: constant across depreciation.
        self.assertAlmostEqual(table[0]["min_dscr"], 1.5)
        self.assertAlmostEqual(table[1]["min_dscr"], 1.5)

    def test_absent_currency_defaults_to_vnd_behaviour(self):
        from proforma_vietnam.cash_flow import calculate_fx_sensitivity

        legacy = calculate_fx_sensitivity(_synthetic_fx_result(None))
        vnd = calculate_fx_sensitivity(_synthetic_fx_result("VND"))

        self.assertEqual(
            [row["equity_irr_fraction"] for row in legacy],
            [row["equity_irr_fraction"] for row in vnd],
        )
        self.assertEqual(
            [row["npv_usd"] for row in legacy],
            [row["npv_usd"] for row in vnd],
        )

    def test_usd_debt_irr_and_min_dscr_strictly_decrease_with_depreciation(self):
        from proforma_vietnam.cash_flow import calculate_fx_sensitivity

        table = calculate_fx_sensitivity(self._engine("USD"))
        irrs = [row["equity_irr_fraction"] for row in table]
        dscrs = [row["min_dscr"] for row in table]

        self.assertEqual(irrs, sorted(irrs, reverse=True))
        self.assertTrue(all(a > b for a, b in zip(irrs, irrs[1:])))
        self.assertEqual(dscrs, sorted(dscrs, reverse=True))
        self.assertTrue(all(a > b for a, b in zip(dscrs, dscrs[1:])))

    def test_vnd_debt_min_dscr_constant_and_irr_matches_legacy(self):
        from proforma_vietnam.cash_flow import _irr, calculate_fx_sensitivity

        result = self._engine("VND")
        table = calculate_fx_sensitivity(result)
        # min DSCR is depreciation-invariant for VND debt.
        dscrs = [row["min_dscr"] for row in table]
        self.assertTrue(all(abs(d - dscrs[0]) < 1e-12 for d in dscrs))
        # IRR trajectory reproduces the pre-4b whole-flow deflation exactly:
        # adjusted_t = equity_cf_t / (1+d)^t for every year (regression).
        equity = [-result["summary"]["equity_investment_usd"]] + [
            row["equity_cash_flow_usd"] for row in result["annual_cash_flows"]
        ]
        for row in table:
            d = row["vnd_depreciation_rate"]
            expected = [cf / (1 + d) ** i for i, cf in enumerate(equity)]
            self.assertAlmostEqual(row["equity_irr_fraction"], _irr(expected))
