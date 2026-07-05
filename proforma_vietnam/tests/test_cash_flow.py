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
