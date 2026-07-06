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
        # Pinned to the legacy expense treatment: this fixture uses the full
        # in-year replacement deduction as the lever for the CIT-shield path.
        cit = [
            row["cit_vnd"]
            for row in self._run(
                replacement_costs_by_year=[80000.0],
                battery_replacement_treatment="expense",
            )["annual_cash_flows"]
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
                battery_replacement_treatment="expense",
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
                battery_replacement_treatment="expense",
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


class DscrDebtSizingTests(TestCase):
    """Optional DSCR-driven debt sizing (default OFF). When target_min_dscr is
    set the loan is sized as min(fraction-based, DSCR-supported) via a fixed-
    point iteration; equity absorbs the gap. When it binds the converged case
    hits min_dscr == target; when it does not, outputs match the same case run
    without the input.
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

    @staticmethod
    def _min_dscr(result):
        dscrs = [
            row["dscr"] for row in result["annual_cash_flows"]
            if row["debt_service_vnd"] and row["dscr"] is not None
        ]
        return min(dscrs) if dscrs else None

    def test_binding_case_converges_to_target_and_sizes_debt_down(self):
        # Fraction-based debt violates the covenant, so DSCR limits the loan.
        target = 2.0
        result = self._run(target_min_dscr=target)
        fraction_debt = 1_000_000.0 * 0.70

        sizing = result["derivation"]["debt_sizing"]
        self.assertEqual(sizing["binding_constraint"], "dscr")
        self.assertAlmostEqual(sizing["target_min_dscr"], target)
        self.assertAlmostEqual(sizing["fraction_based_principal_usd"], fraction_debt)
        # Converged min DSCR equals the covenant (the fixed-point tie-out).
        self.assertAlmostEqual(self._min_dscr(result), target, places=6)
        self.assertAlmostEqual(sizing["achieved_min_dscr"], target, places=6)
        # Sized debt is below the fraction-based principal.
        sized = result["summary"]["debt_principal_vnd"]
        self.assertLess(sized, fraction_debt)
        self.assertAlmostEqual(sizing["sized_principal_usd"], sized)
        # Equity absorbs the gap: equity = capex − sized debt.
        self.assertAlmostEqual(
            result["summary"]["equity_investment_vnd"], 1_000_000.0 - sized
        )
        # Debt-service rows are consistent with the sized principal (no
        # construction, so the COD balance equals the sized principal).
        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["interest_vnd"], sized * 0.085)
        self.assertAlmostEqual(
            sum(row["principal_vnd"] for row in rows), sized
        )
        # Gated summary keys surface the sized principal and binding flag.
        self.assertAlmostEqual(result["summary"]["sized_debt_principal_vnd"], sized)
        self.assertTrue(result["summary"]["debt_sizing_binding"])

    def test_non_binding_case_matches_case_without_the_input(self):
        # A low covenant the fraction-based debt already clears: outputs must be
        # identical (annual_cash_flows + summary) to omitting the input.
        target = 1.05
        baseline = self._run()
        sized = self._run(target_min_dscr=target)

        self.assertEqual(sized["derivation"]["debt_sizing"]["binding_constraint"],
                         "fraction")
        self.assertGreaterEqual(self._min_dscr(sized), target)
        self.assertEqual(sized["annual_cash_flows"], baseline["annual_cash_flows"])
        self.assertEqual(sized["summary"], baseline["summary"])
        # Non-binding leaves the summary byte-identical: no gated summary keys.
        self.assertNotIn("sized_debt_principal_vnd", sized["summary"])
        self.assertNotIn("debt_sizing_binding", sized["summary"])
        # The self-describing derivation block is still present (input was set).
        self.assertIn("debt_sizing", sized["derivation"])

    def test_raising_the_target_weakly_lowers_the_sized_principal(self):
        principals = [
            self._run(target_min_dscr=target)["summary"]["debt_principal_vnd"]
            for target in (1.0, 1.5, 2.0, 2.5, 3.0)
        ]
        for lower, higher in zip(principals, principals[1:]):
            self.assertLessEqual(higher, lower + 1e-6)

    def test_sizing_with_construction_puts_idc_on_the_sized_principal(self):
        target = 2.0
        result = self._run(target_min_dscr=target, construction_months=12)

        sizing = result["derivation"]["debt_sizing"]
        self.assertEqual(sizing["binding_constraint"], "dscr")
        sized = sizing["sized_principal_usd"]
        # IDC is computed on the SIZED principal (Task 4a formula).
        construction = result["derivation"]["construction"]
        self.assertAlmostEqual(construction["idc_usd"], sized * 0.085 * 0.5)
        self.assertAlmostEqual(
            construction["cod_debt_balance_usd"], sized + sized * 0.085 * 0.5
        )
        # Covenant is still hit at convergence.
        self.assertAlmostEqual(self._min_dscr(result), target, places=6)

    def test_sizing_with_grace_respects_the_covenant_in_interest_only_years(self):
        target = 2.0
        result = self._run(target_min_dscr=target, principal_grace_years=3)

        rows = result["annual_cash_flows"]
        # Grace years are interest-only but still carry debt service, so the
        # covenant must hold there too.
        for row in rows[:3]:
            self.assertAlmostEqual(row["principal_vnd"], 0.0)
            self.assertGreaterEqual(row["dscr"], target - 1e-6)
        self.assertAlmostEqual(self._min_dscr(result), target, places=6)

    def test_sizing_with_usd_debt_uses_resolved_usd_rate(self):
        # USD debt resolves the 5% default; the covenant sizing runs on it.
        target = 2.0
        result = self._run(
            target_min_dscr=target,
            debt_interest_rate_fraction=None,
            debt_currency="USD",
        )
        self.assertEqual(
            result["derivation"]["debt_interest_rate_fraction"], 0.05
        )
        sized = result["summary"]["debt_principal_vnd"]
        self.assertAlmostEqual(result["annual_cash_flows"][0]["interest_vnd"],
                               sized * 0.05)
        self.assertAlmostEqual(self._min_dscr(result), target, places=6)

    def test_degenerate_non_positive_cfads_sizes_debt_to_zero_all_equity(self):
        # Operating costs exceed revenue, so CFADS <= 0 in the debt years: the
        # supported debt collapses to zero — all-equity, zero debt schedule, no
        # exception.
        result = self._run(target_min_dscr=1.5, annual_om_vnd=300000.0)

        self.assertAlmostEqual(result["summary"]["debt_principal_vnd"], 0.0)
        self.assertAlmostEqual(
            result["summary"]["equity_investment_vnd"], 1_000_000.0
        )
        for row in result["annual_cash_flows"]:
            self.assertAlmostEqual(row["debt_service_vnd"], 0.0)
            self.assertIsNone(row["dscr"])
        sizing = result["derivation"]["debt_sizing"]
        self.assertAlmostEqual(sizing["sized_principal_usd"], 0.0)
        self.assertEqual(sizing["binding_constraint"], "dscr")

    def test_validation_rejects_below_one_zero_negative_bool_and_string(self):
        for bad in (0.9, 0, -1.0, True, False, "1.5"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self._run(target_min_dscr=bad)

    def test_none_leaves_outputs_byte_identical_and_leaks_no_keys(self):
        base = self._run()
        disabled = self._run(target_min_dscr=None)

        self.assertEqual(base["annual_cash_flows"], disabled["annual_cash_flows"])
        self.assertEqual(base["summary"], disabled["summary"])
        self.assertEqual(base["derivation"], disabled["derivation"])
        self.assertNotIn("debt_sizing", base["derivation"])
        self.assertNotIn("sized_debt_principal_vnd", base["summary"])
        self.assertNotIn("debt_sizing_binding", base["summary"])

    def test_derivation_block_carries_the_full_self_describing_record(self):
        result = self._run(target_min_dscr=2.0)
        sizing = result["derivation"]["debt_sizing"]
        for key in (
            "target_min_dscr", "fraction_based_principal_usd",
            "supported_principal_usd", "sized_principal_usd",
            "binding_constraint", "iterations", "achieved_min_dscr",
        ):
            self.assertIn(key, sizing)
        self.assertGreaterEqual(sizing["iterations"], 1)

    def test_sizing_applies_under_direct_ownership(self):
        result = self._run(target_min_dscr=2.0, direct_ownership={})
        self.assertEqual(
            result["derivation"]["debt_sizing"]["binding_constraint"], "dscr"
        )
        self.assertAlmostEqual(self._min_dscr(result), 2.0, places=6)


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


class BatteryReplacementCapitalizationTests(TestCase):
    """Circular 45 battery-replacement capitalization (default). Each replacement
    year spawns a BESS-class fixed asset depreciated straight-line over its
    8-year life from the in-service year, truncated at the horizon; the CIT
    deduction is the replacement depreciation, not the in-year expense. Cash is
    unchanged in both modes; the legacy ``"expense"`` flag restores the full
    in-year deduction and leaks no derivation block.

    The fixture is a factory self-invest (DIRECT_OWNERSHIP) case with flat 20%
    CIT and the profitable-host shield on, so CIT == taxable income x 20% every
    year (positive or negative) and totals reduce to 0.20 x total taxable income
    — hand-computable timing shifts.
    """

    RATE = 0.20
    SAVINGS = 40000.0  # bau 100000 - optimized 60000, flat (no escalation/degradation)

    def _run(self, **overrides):
        inputs = dict(
            project_served_pv_kwh=[100.0],
            evn_energy_rates_vnd_per_kwh=[10.0],
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
            project_years=15,
            direct_ownership={},  # standard_flat + profitable host -> flat 20%/yr
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    @staticmethod
    def _cit(result):
        return [row["cit_vnd"] for row in result["annual_cash_flows"]]

    def test_capitalize_spreads_replacement_over_the_bess_life(self):
        cost = 80000.0
        capitalize = self._run(replacement_costs_by_year=[0.0, 0.0, cost])
        expense = self._run(
            replacement_costs_by_year=[0.0, 0.0, cost],
            battery_replacement_treatment="expense",
        )

        block = capitalize["derivation"]["battery_replacement"]
        self.assertEqual(block["treatment"], "capitalize")
        self.assertEqual(len(block["schedules"]), 1)
        schedule = block["schedules"][0]
        self.assertEqual(schedule["in_service_year"], 3)
        self.assertAlmostEqual(schedule["cost_usd"], cost)
        self.assertEqual(schedule["life_years"], 8)
        self.assertAlmostEqual(schedule["annual_charge_usd"], cost / 8)
        # In-service year 3 -> depreciation years 3..10 (8 charges, full life).
        self.assertEqual(schedule["depreciation_years"], [3, 4, 5, 6, 7, 8, 9, 10])

        cap_cit, exp_cit = self._cit(capitalize), self._cit(expense)
        # Depreciation cost/8 in years 3..10: taxable there is savings - cost/8.
        for index in range(2, 10):
            self.assertAlmostEqual(cap_cit[index], (self.SAVINGS - cost / 8) * self.RATE)
        # Year-R taxable income is higher by cost - cost/8 than in expense mode.
        self.assertAlmostEqual((cap_cit[2] - exp_cit[2]) / self.RATE, cost - cost / 8)
        # Timing shift only: full 8-year life fits the horizon, so the total
        # deduction (and hence total CIT) is identical to expensing.
        self.assertAlmostEqual(sum(cap_cit), sum(exp_cit))

    def test_cash_lines_are_unchanged_between_modes(self):
        cost = 80000.0
        capitalize = self._run(replacement_costs_by_year=[0.0, 0.0, cost])
        expense = self._run(
            replacement_costs_by_year=[0.0, 0.0, cost],
            battery_replacement_treatment="expense",
        )
        # The replacement cash outflow and pre-tax operating lines are booked
        # identically; only CIT (and the CFADS/equity it nets) differ.
        for cap, exp in zip(capitalize["annual_cash_flows"], expense["annual_cash_flows"]):
            self.assertAlmostEqual(cap["replacement_cost_vnd"], exp["replacement_cost_vnd"])
            self.assertAlmostEqual(cap["esco_revenue_vnd"], exp["esco_revenue_vnd"])
            self.assertAlmostEqual(cap["annual_om_vnd"], exp["annual_om_vnd"])
        self.assertAlmostEqual(
            capitalize["annual_cash_flows"][2]["replacement_cost_vnd"], cost
        )

    def test_truncation_at_horizon_takes_only_in_horizon_charges(self):
        cost = 80000.0
        # Replacement in year 20, horizon 25: charges years 20..25 only (6), the
        # undepreciated remainder (2 x cost/8) is NOT written off.
        capitalize = self._run(
            replacement_costs_by_year=[0.0] * 19 + [cost], project_years=25
        )
        schedule = capitalize["derivation"]["battery_replacement"]["schedules"][0]
        self.assertEqual(schedule["in_service_year"], 20)
        self.assertEqual(schedule["depreciation_years"], [20, 21, 22, 23, 24, 25])
        self.assertAlmostEqual(schedule["annual_charge_usd"], cost / 8)
        total_taken = schedule["annual_charge_usd"] * len(schedule["depreciation_years"])
        self.assertAlmostEqual(total_taken, 6 * cost / 8)

        # Capitalize deducts only 6 x cost/8 vs expensing the full cost, so total
        # taxable (and total CIT) is higher by 0.20 x (cost - 6 x cost/8).
        expense = self._run(
            replacement_costs_by_year=[0.0] * 19 + [cost], project_years=25,
            battery_replacement_treatment="expense",
        )
        self.assertAlmostEqual(
            sum(self._cit(capitalize)) - sum(self._cit(expense)),
            self.RATE * (cost - 6 * cost / 8),
        )

    def test_multiple_replacement_years_get_independent_overlapping_schedules(self):
        cost = 80000.0
        capitalize = self._run(
            replacement_costs_by_year=[0.0, 0.0, cost, 0.0, 0.0, cost],
            project_years=20,
        )
        schedules = capitalize["derivation"]["battery_replacement"]["schedules"]
        self.assertEqual(len(schedules), 2)
        self.assertEqual(schedules[0]["in_service_year"], 3)
        self.assertEqual(schedules[0]["depreciation_years"], [3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(schedules[1]["in_service_year"], 6)
        self.assertEqual(schedules[1]["depreciation_years"], [6, 7, 8, 9, 10, 11, 12, 13])
        # Overlap years 6..10 carry both schedules: taxable = savings - 2 x cost/8.
        self.assertAlmostEqual(
            self._cit(capitalize)[5], (self.SAVINGS - 2 * cost / 8) * self.RATE
        )
        # Both lives fit the horizon -> total deduction = 2 x cost = expensing,
        # so total CIT matches (pure timing shift).
        expense = self._run(
            replacement_costs_by_year=[0.0, 0.0, cost, 0.0, 0.0, cost],
            project_years=20, battery_replacement_treatment="expense",
        )
        self.assertAlmostEqual(sum(self._cit(capitalize)), sum(self._cit(expense)))

    def test_no_replacement_capitalize_default_is_byte_identical_to_expense(self):
        base = self._run()  # capitalize default, no replacement
        expense = self._run(battery_replacement_treatment="expense")
        self.assertEqual(base["annual_cash_flows"], expense["annual_cash_flows"])
        self.assertEqual(base["summary"], expense["summary"])
        self.assertEqual(base["derivation"], expense["derivation"])
        self.assertNotIn("battery_replacement", base["derivation"])

    def test_legacy_expense_flag_leaks_no_block_and_deducts_full_cost_in_year(self):
        cost = 80000.0
        expense = self._run(
            replacement_costs_by_year=[0.0, 0.0, cost],
            battery_replacement_treatment="expense",
        )
        self.assertNotIn("battery_replacement", expense["derivation"])
        # Full in-year deduction: year-3 taxable = savings - cost (negative) ->
        # immediate CIT shield of (savings - cost) x 20%.
        self.assertAlmostEqual(
            expense["annual_cash_flows"][2]["cit_vnd"], (self.SAVINGS - cost) * self.RATE
        )

    def test_invalid_treatment_raises_value_error(self):
        for bad in ("Capitalize", "amortize", "", 0, 1, True, None, ["expense"]):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self._run(battery_replacement_treatment=bad)

    def test_capitalize_interacts_with_dscr_debt_sizing(self):
        # DSCR sizing consumes the capitalize-adjusted CFADS timing (the year-6
        # replacement cash year drags the DSCR) and still converges to the
        # covenant; both self-describing blocks coexist.
        result = self._run(
            bau_evn_bill_vnd=1_000_000.0, optimized_evn_bill_vnd=600_000.0,
            replacement_costs_by_year=[0.0] * 5 + [200000.0],
            pv_capex_vnd=700_000.0, bess_capex_vnd=300_000.0,
            debt_fraction=0.70, debt_interest_rate_fraction=0.085, debt_term_years=10,
            target_min_dscr=1.5, project_years=25,
        )
        self.assertIn("battery_replacement", result["derivation"])
        self.assertIn("debt_sizing", result["derivation"])
        dscrs = [
            row["dscr"] for row in result["annual_cash_flows"]
            if row["debt_service_vnd"] and row["dscr"] is not None
        ]
        self.assertGreaterEqual(min(dscrs), 1.5 - 1e-6)

    def test_capitalize_interacts_with_re_producer_holiday_regime(self):
        # re_producer holiday/reduced-rate schedule: the replacement depreciation
        # rides the same CIT machinery (no special-casing). Deductions falling in
        # the first-profit holiday years (0% rate) are worth nothing, so the total
        # CIT need NOT match expense mode — but the schedule is present and shaped.
        cost = 80000.0
        base = dict(
            project_served_pv_kwh=[100.0], evn_energy_rates_vnd_per_kwh=[10.0],
            bau_evn_bill_vnd=100000.0, optimized_evn_bill_vnd=60000.0,
            bau_demand_charge_vnd=0.0, optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=0.0, bess_capex_vnd=0.0, annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0, evn_capacity_escalation_rate=0.0,
            debt_fraction=0.0, project_years=20, cit_regime="re_producer",
            replacement_costs_by_year=[0.0, 0.0, cost],
        )
        capitalize = calculate_vietnam_esco_cash_flow(**base)
        expense = calculate_vietnam_esco_cash_flow(
            **{**base, "battery_replacement_treatment": "expense"}
        )
        self.assertEqual(
            capitalize["derivation"]["battery_replacement"]["treatment"], "capitalize"
        )
        self.assertNotIn("battery_replacement", expense["derivation"])
        schedule = capitalize["derivation"]["battery_replacement"]["schedules"][0]
        self.assertEqual(schedule["depreciation_years"], [3, 4, 5, 6, 7, 8, 9, 10])
        # The holiday years suppress CIT regardless of the deduction timing.
        self.assertAlmostEqual(capitalize["annual_cash_flows"][0]["cit_vnd"], 0.0)


class ContractTenorTests(TestCase):
    """Task 4e: ESCO contract tenor with end-of-term asset transfer at a
    residual/buyout value. Default OFF (``contract_years=None``).

    The fixture is a strongly profitable, no-debt, flat (no escalation /
    degradation) ESCO case under the flat-20% standard regime, so taxable income
    is positive every year, no losses carry forward, and CIT == taxable income x
    20% — the year-T disposal gain's tax effect is hand-computable. With
    ``pv_capex=2,000,000`` over a 20-year life, the year-1..12 depreciation is
    100,000/yr and revenue is a flat 900,000/yr (100,000 kWh x 10 x 0.9).
    """

    RATE = 0.20

    def _run(self, **overrides):
        inputs = dict(
            project_served_pv_kwh=[100000.0],
            evn_energy_rates_vnd_per_kwh=[10.0],
            bau_evn_bill_vnd=2_000_000.0,
            optimized_evn_bill_vnd=1_400_000.0,
            bau_demand_charge_vnd=0.0,
            optimized_demand_charge_vnd=0.0,
            pv_capex_vnd=2_000_000.0,
            bess_capex_vnd=0.0,
            annual_om_vnd=0.0,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0,
            evn_capacity_escalation_rate=0.0,
            debt_fraction=0.0,
            project_years=25,
            cit_regime="standard_flat",
        )
        inputs.update(overrides)
        return calculate_vietnam_esco_cash_flow(**inputs)

    # --- default OFF / byte-identical guard --------------------------------

    def test_disabled_by_default_leaks_no_block_or_row_key(self):
        result = self._run()
        self.assertNotIn("contract_term", result["derivation"])
        for row in result["annual_cash_flows"]:
            self.assertNotIn("asset_transfer_proceeds_usd", row)
            self.assertNotIn("asset_transfer_proceeds_vnd", row)

    def test_explicit_none_defaults_are_byte_identical_to_omitting(self):
        omitted = self._run()
        explicit = self._run(contract_years=None, contract_residual_value_usd=0.0)
        self.assertEqual(explicit["annual_cash_flows"], omitted["annual_cash_flows"])
        self.assertEqual(explicit["summary"], omitted["summary"])
        self.assertEqual(explicit["derivation"], omitted["derivation"])

    # --- hand-computed PV-only fixture (T=12) ------------------------------

    def test_pv_only_nbv_gain_truncation_and_transfer(self):
        result = self._run(contract_years=12, contract_residual_value_usd=1_000_000.0)
        block = result["derivation"]["contract_term"]
        rows = result["annual_cash_flows"]

        # NBV = capitalized cost - straight-line depreciation through T:
        # 2,000,000 x (20 - 12)/20 = 800,000 (BESS capex is 0 here).
        self.assertAlmostEqual(block["net_book_value_at_transfer_usd"], 800_000.0)
        self.assertAlmostEqual(block["disposal_gain_usd"], 200_000.0)  # 1,000,000 - 800,000
        # Gain is taxed at the year-12 regime rate (flat 20%).
        self.assertAlmostEqual(block["disposal_tax_usd"], 200_000.0 * self.RATE)

        # Operations stop at T: every ESCO-side line is zero for years 13..25.
        for row in rows[12:]:
            self.assertEqual(row["esco_revenue_usd"], 0.0)
            self.assertEqual(row["annual_om_usd"], 0.0)
            self.assertEqual(row["depreciation_usd"], 0.0)
            self.assertEqual(row["cit_usd"], 0.0)
            self.assertEqual(row["equity_cash_flow_usd"], 0.0)

        # Transfer proceeds are their own line, present only in year T.
        self.assertAlmostEqual(rows[11]["asset_transfer_proceeds_usd"], 1_000_000.0)
        self.assertEqual(rows[10]["asset_transfer_proceeds_usd"], 0.0)
        self.assertEqual(rows[12]["asset_transfer_proceeds_usd"], 0.0)

        # Year-12 equity = CFADS (900,000 - CIT 200,000) + residual 1,000,000.
        self.assertAlmostEqual(rows[11]["equity_cash_flow_usd"], 700_000.0 + 1_000_000.0)
        # Year-12 CIT carries the disposal gain: (800,000 + 200,000) x 20%.
        self.assertAlmostEqual(rows[11]["cit_usd"], 200_000.0)

    def test_zero_residual_books_a_disposal_loss_of_negative_nbv(self):
        result = self._run(contract_years=12, contract_residual_value_usd=0.0)
        block = result["derivation"]["contract_term"]
        rows = result["annual_cash_flows"]
        # Transfer row is present at 0.0 (a set tenor, no buyout).
        self.assertEqual(rows[11]["asset_transfer_proceeds_usd"], 0.0)
        # Disposal LOSS = 0 - NBV = -800,000, which reduces year-12 taxable income.
        self.assertAlmostEqual(block["disposal_gain_usd"], -800_000.0)
        self.assertAlmostEqual(block["disposal_tax_usd"], -800_000.0 * self.RATE)

    # --- asset-class coverage ----------------------------------------------

    def test_bess_fully_depreciated_at_transfer_is_excluded_from_nbv(self):
        # T=10 > BESS 8-year life, no replacement: BESS NBV is zero, PV remains.
        result = self._run(
            bess_capex_vnd=800_000.0, contract_years=10,
            contract_residual_value_usd=0.0,
        )
        by_asset = {
            item["asset"]: item
            for item in result["derivation"]["contract_term"]["net_book_value_by_asset_usd"]
        }
        self.assertAlmostEqual(by_asset["initial_bess"]["net_book_value_usd"], 0.0)
        # PV: 2,000,000 x (20 - 10)/20 = 1,000,000.
        self.assertAlmostEqual(by_asset["initial_pv"]["net_book_value_usd"], 1_000_000.0)
        self.assertAlmostEqual(
            result["derivation"]["contract_term"]["net_book_value_at_transfer_usd"],
            1_000_000.0,
        )

    def test_replacement_before_T_in_nbv_and_after_T_not_incurred(self):
        # Replacement in year 11 (before T=12) and year 20 (after T). Only the
        # year-11 asset exists; the year-20 replacement is never incurred.
        result = self._run(
            bess_capex_vnd=800_000.0, contract_years=12,
            contract_residual_value_usd=0.0,
            replacement_costs_by_year=[0.0] * 10 + [240_000.0] + [0.0] * 8 + [500_000.0],
        )
        schedules = result["derivation"]["battery_replacement"]["schedules"]
        self.assertEqual([s["in_service_year"] for s in schedules], [11])
        rows = result["annual_cash_flows"]
        self.assertEqual(rows[10]["replacement_cost_usd"], 240_000.0)
        self.assertEqual(rows[19]["replacement_cost_usd"], 0.0)  # year-20 not incurred
        by_asset = {
            (item["asset"], item.get("in_service_year")): item
            for item in result["derivation"]["contract_term"]["net_book_value_by_asset_usd"]
        }
        # Year-11 asset: cost 240,000, life 8, charges in years 11 & 12 (2 taken
        # through T): NBV = 240,000 - 240,000/8 x 2 = 180,000.
        self.assertAlmostEqual(
            by_asset[("replacement", 11)]["net_book_value_usd"], 180_000.0
        )

    def test_transfer_at_horizon_end_has_no_truncation(self):
        # contract_years == project_years: operations run the full horizon, the
        # transfer lands in the final year.
        result = self._run(contract_years=25, contract_residual_value_usd=500_000.0)
        rows = result["annual_cash_flows"]
        # No truncation: year-20 (still within PV life) revenue is the flat value.
        self.assertAlmostEqual(rows[19]["esco_revenue_usd"], 900_000.0)
        self.assertAlmostEqual(rows[24]["asset_transfer_proceeds_usd"], 500_000.0)
        for row in rows[:24]:
            self.assertEqual(row["asset_transfer_proceeds_usd"], 0.0)
        # PV fully depreciated by year 20 (< 25), so NBV at T=25 is 0.
        self.assertAlmostEqual(
            result["derivation"]["contract_term"]["net_book_value_at_transfer_usd"], 0.0
        )

    # --- interactions with earlier tasks -----------------------------------

    def test_construction_idc_rides_into_the_disposal_nbv(self):
        # Capitalized IDC (Task 4a) joins the PV/BESS bases pro-rata, so the NBV
        # at transfer is higher than the bare-capex NBV by the undepreciated IDC.
        result = self._run(
            contract_years=12, contract_residual_value_usd=0.0,
            construction_months=12, debt_fraction=0.5,
        )
        idc = result["derivation"]["construction"]["idc_usd"]
        pv_nbv = result["derivation"]["contract_term"][
            "net_book_value_by_asset_usd"][0]["net_book_value_usd"]
        # PV basis = 2,000,000 + IDC (all IDC to PV since BESS capex is 0);
        # NBV = basis x (20 - 12)/20.
        self.assertAlmostEqual(pv_nbv, (2_000_000.0 + idc) * (20 - 12) / 20)

    def test_tenor_with_dscr_sizing_converges_with_year_T_tax_effect(self):
        # DSCR sizing (Task 4c) re-runs the derivation against the truncated
        # CFADS incl. the year-T disposal tax; both blocks must be present and
        # the sized loan must not exceed the fraction-based loan.
        result = self._run(
            debt_fraction=0.6, debt_term_years=10, target_min_dscr=1.5,
            contract_years=12, contract_residual_value_usd=1_000_000.0,
        )
        self.assertIn("debt_sizing", result["derivation"])
        self.assertIn("contract_term", result["derivation"])
        self.assertLessEqual(
            result["summary"]["debt_principal_usd"],
            result["summary"]["total_capex_usd"] * 0.6 + 1e-6,
        )

    def test_tenor_with_usd_debt_still_transfers(self):
        result = self._run(
            debt_fraction=0.5, debt_term_years=10, debt_currency="USD",
            contract_years=12, contract_residual_value_usd=1_000_000.0,
        )
        self.assertEqual(result["derivation"]["debt_currency"], "USD")
        self.assertAlmostEqual(
            result["annual_cash_flows"][11]["asset_transfer_proceeds_usd"], 1_000_000.0
        )

    # --- validation --------------------------------------------------------

    def test_residual_without_tenor_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(contract_residual_value_usd=500_000.0)

    def test_negative_residual_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(contract_years=12, contract_residual_value_usd=-1.0)

    def test_zero_tenor_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(contract_years=0)

    def test_negative_tenor_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(contract_years=-5)

    def test_tenor_beyond_horizon_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(contract_years=26)  # project_years is 25

    def test_non_integer_tenor_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(contract_years=12.0)

    def test_boolean_tenor_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(contract_years=True)

    def test_tenor_shorter_than_debt_term_is_rejected(self):
        with self.assertRaises(ValueError):
            self._run(debt_fraction=0.5, debt_term_years=15, contract_years=12)

    def test_tenor_on_non_esco_structure_is_rejected(self):
        # DIRECT_OWNERSHIP (and any non-ESCO structure) rejects a tenor.
        with self.assertRaises(ValueError):
            self._run(direct_ownership={}, contract_years=12)
