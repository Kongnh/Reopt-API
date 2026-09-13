import unittest
from unittest import TestCase
from copy import deepcopy

from proforma_vietnam.esco_pro_forma import (
    calculate_esco_pro_forma_from_reopt_results,
    _merge_replacement_costs,
)


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

    def test_contract_tenor_kwargs_pass_through_to_the_cash_flow(self):
        # Task 4e: contract_years / contract_residual_value_usd are plain cash
        # flow kwargs, so esco_pro_forma's generic **cash_flow_overrides carries
        # them straight into calculate_vietnam_esco_cash_flow (no schema-specific
        # handling needed, unlike surplus/dppa/direct blocks).
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=25,
            debt_term_years=10,
            contract_years=12,
            contract_residual_value_usd=40000.0,
        )

        block = result["derivation"]["contract_term"]
        self.assertEqual(block["contract_years"], 12)
        self.assertAlmostEqual(block["residual_value_usd"], 40000.0)
        # Transfer proceeds land in the year-12 row; operations truncate after.
        self.assertAlmostEqual(
            result["annual_cash_flows"][11]["asset_transfer_proceeds_vnd"], 40000.0
        )
        self.assertEqual(result["annual_cash_flows"][12]["esco_revenue_vnd"], 0.0)

    def test_excludes_storage_discharge_when_grid_charging_is_enabled(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=True),
            esco_energy_discount_fraction=0.9,
            project_years=1,
        )

        annual = result["annual_cash_flows"][0]

        self.assertEqual(annual["esco_energy_revenue_vnd"], 4500)
        self.assertEqual(annual["esco_grid_arbitrage_revenue_vnd"], 0)

    def test_battery_only_grid_charging_wires_net_arbitrage_from_bill_delta(self):
        # With no PV, every discharged kWh was grid-charged, so the whole
        # energy-bill delta IS the net grid-arbitrage value:
        # (50000 - 30000) - (8000 - 3000) demand delta = 15000, ESCO share 1.0.
        result = calculate_esco_pro_forma_from_reopt_results(
            _battery_only_reopt_results(),
            esco_energy_discount_fraction=0.0,
            grid_charging_enabled=True,
            project_years=1,
        )

        annual = result["annual_cash_flows"][0]

        self.assertEqual(annual["esco_grid_arbitrage_revenue_vnd"], 15000)
        self.assertEqual(annual["esco_energy_revenue_vnd"], 0)

    def test_battery_only_arbitrage_stays_zero_without_grid_charging_flag(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _battery_only_reopt_results(),
            esco_energy_discount_fraction=0.0,
            project_years=1,
        )

        self.assertEqual(
            result["annual_cash_flows"][0]["esco_grid_arbitrage_revenue_vnd"], 0
        )

    def test_pv_case_keeps_arbitrage_unwired_even_with_grid_charging_flag(self):
        # With PV present the grid-charged share of discharge cannot be
        # attributed from available REopt outputs (per the design doc), so the
        # bill-delta wiring must not fire.
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=True),
            esco_energy_discount_fraction=0.9,
            grid_charging_enabled=True,
            project_years=1,
        )

        self.assertEqual(
            result["annual_cash_flows"][0]["esco_grid_arbitrage_revenue_vnd"], 0
        )

    def test_explicit_net_arbitrage_override_wins_over_battery_only_wiring(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _battery_only_reopt_results(),
            esco_energy_discount_fraction=0.0,
            grid_charging_enabled=True,
            net_grid_arbitrage_value_vnd=1234.0,
            project_years=1,
        )

        self.assertEqual(
            result["annual_cash_flows"][0]["esco_grid_arbitrage_revenue_vnd"], 1234.0
        )

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


    def test_dppa_year_one_primitives_are_converted_to_cash_flow_currency(self):
        # DPPA settlement produces VND-magnitude values from FMP × kWh. When the
        # cash flow runs in USD (REopt money values are USD), the DPPA primitives
        # must be divided by the exchange rate before they flow into annual rows,
        # or the offtaker savings calculation mixes currencies.
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        # Zero out the tariff so c_bl drops out of the comparison; the c_dn /
        # cfd / generator_revenue terms are sufficient to prove conversion.
        reopt_results["inputs"]["ElectricTariff"]["tou_energy_rates_per_kwh"] = [0.0, 0.0]
        reopt_results["outputs"]["ElectricLoad"] = {"load_series_kw": [10, 10]}
        reopt_results["outputs"]["ElectricUtility"] = {
            "electric_to_load_series_kw": [6, 6],
            "electric_to_storage_series_kw": [0, 0],
        }

        dppa_inputs = {
            "type": "grid_dppa_cfd",
            "fmp_series_vnd_per_kwh": [1500.0, 1500.0],
            "cfd_strike_per_kwh_vnd": 1700.0,
            "cfd_contract_volume_kwh_per_hour": 1.0,
            "transmission_loss_factor_k": 1.026,
            "distribution_loss_factor_kpp": 1.027263,
            "allocation_fraction_delta": 1.0,
            "c_dppa_service_fee_vnd_per_kwh": 360.0,
            "c_cl_settlement_adder_vnd_per_kwh": 163.0,
            "cfd_strike_escalation_rate": 0.0,
            "fee_escalation_rate": 0.0,
        }

        with_rate = calculate_esco_pro_forma_from_reopt_results(
            deepcopy(reopt_results),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            dppa_inputs=dppa_inputs,
            exchange_rate_vnd_per_usd=25000,
        )
        without_rate = calculate_esco_pro_forma_from_reopt_results(
            deepcopy(reopt_results),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            dppa_inputs=dppa_inputs,
        )

        annual_with = with_rate["annual_cash_flows"][0]
        annual_without = without_rate["annual_cash_flows"][0]

        # With an exchange rate the pair is real: _usd carries the converted
        # cash-flow-currency value and _vnd is restated back to true VND (so
        # it matches the unconverted run's native-VND value).
        for key in ("c_dn", "c_dppa", "c_cl", "cfd_net",
                    "generator_revenue", "dppa_offtaker_cost"):
            self.assertAlmostEqual(
                annual_with[f"{key}_usd"], annual_without[f"{key}_vnd"] / 25000,
                places=6,
                msg=f"{key}_usd not converted by exchange rate",
            )
            self.assertAlmostEqual(
                annual_with[f"{key}_vnd"], annual_without[f"{key}_vnd"], places=4,
                msg=f"{key}_vnd not restated to true VND",
            )

    def test_dppa_hourly_and_monthly_breakouts_stay_in_vnd_when_exchange_rate_is_provided(self):
        # The Hourly/Monthly Settlement workbook sheets display VND-native
        # per-hour amounts. Their breakouts must NOT be converted, even when
        # the cash flow's year-one primitives are.
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        reopt_results["outputs"]["ElectricLoad"] = {"load_series_kw": [10, 10]}

        dppa_inputs = {
            "type": "grid_dppa_cfd",
            "fmp_series_vnd_per_kwh": [1500.0, 1500.0],
            "cfd_strike_per_kwh_vnd": 1700.0,
            "cfd_contract_volume_kwh_per_hour": 1.0,
            "transmission_loss_factor_k": 1.026,
            "distribution_loss_factor_kpp": 1.027263,
            "allocation_fraction_delta": 1.0,
            "c_dppa_service_fee_vnd_per_kwh": 360.0,
            "c_cl_settlement_adder_vnd_per_kwh": 163.0,
            "cfd_strike_escalation_rate": 0.0,
            "fee_escalation_rate": 0.0,
        }

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=1,
            dppa_inputs=dppa_inputs,
            exchange_rate_vnd_per_usd=25000,
        )

        hourly = result["dppa_hourly_breakout"]
        # FMP entries echo back the input series in VND, untouched by conversion.
        self.assertEqual(hourly[0]["fmp_vnd_per_kwh"], 1500.0)
        # C_DN per hour = Q_adj × FMP — still VND-magnitude (hundreds-of-thousands here).
        self.assertGreater(hourly[0]["c_dn_vnd"], 1000)

    def test_dppa_inputs_drive_grid_dppa_cfd_branch_of_cash_flow(self):
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        reopt_results["outputs"]["ElectricLoad"] = {"load_series_kw": [10, 10]}
        reopt_results["outputs"]["ElectricUtility"] = {
            "electric_to_load_series_kw": [6, 6],
            "electric_to_storage_series_kw": [0, 0],
        }

        dppa_inputs = {
            "type": "grid_dppa_cfd",
            "fmp_series_vnd_per_kwh": [1500.0, 1500.0],
            "cfd_strike_per_kwh_vnd": 1700.0,
            "cfd_contract_volume_kwh_per_hour": 1.0,
            "transmission_loss_factor_k": 1.026,
            "distribution_loss_factor_kpp": 1.027263,
            "allocation_fraction_delta": 1.0,
            "c_dppa_service_fee_vnd_per_kwh": 360.0,
            "c_cl_settlement_adder_vnd_per_kwh": 163.0,
            "cfd_strike_escalation_rate": 0.0,
            "fee_escalation_rate": 0.0,
        }

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=1,
            dppa_inputs=dppa_inputs,
        )

        annual = result["annual_cash_flows"][0]
        # Generator-side: Q_re_meter (PV-to-load + storage-to-load with can_grid_charge=False
        # absorbed into co-located injection) × FMP, plus CfD net.
        self.assertGreater(annual["generator_revenue_vnd"], 0)
        self.assertIn("c_dn_vnd", annual)
        self.assertIn("c_bl_vnd", annual)
        self.assertIn("cfd_net_vnd", annual)
        # ESCO energy revenue under DPPA is replaced by generator revenue.
        self.assertEqual(
            annual["esco_energy_revenue_vnd"], annual["generator_revenue_vnd"]
        )


    def test_bess_replacement_cost_derived_from_reopt_replacement_inputs(self):
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        reopt_results["inputs"]["ElectricStorage"].update({
            "replace_cost_per_kw": 80.0,
            "replace_cost_per_kwh": 100.0,
            "battery_replacement_year": 10,
        })
        reopt_results["outputs"]["ElectricStorage"].update({
            "size_kw": 10.0,
            "size_kwh": 20.0,
        })

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=12,
        )

        rows = result["annual_cash_flows"]
        self.assertEqual(rows[0]["replacement_cost_vnd"], 0)
        # Replacement lands in year 10 (index 9): 10×80 + 20×100 = 2,800.
        self.assertAlmostEqual(rows[9]["replacement_cost_vnd"], 2800.0)
        self.assertEqual(rows[10]["replacement_cost_vnd"], 0)

    def test_battery_replacement_year_override_beats_reopt_inputs(self):
        # Saved results.json may echo battery_replacement_year=10 from the
        # original REopt run; an explicit override (e.g. year 11 from updated
        # assumptions) must win so the schedule can change without a re-run.
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        reopt_results["inputs"]["ElectricStorage"].update({
            "replace_cost_per_kw": 80.0,
            "replace_cost_per_kwh": 100.0,
            "battery_replacement_year": 10,
        })
        reopt_results["outputs"]["ElectricStorage"].update({
            "size_kw": 10.0,
            "size_kwh": 20.0,
        })

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=12,
            battery_replacement_year=11,
        )

        rows = result["annual_cash_flows"]
        self.assertEqual(rows[9]["replacement_cost_vnd"], 0)
        # Replacement lands in year 11 (index 10): 10×80 + 20×100 = 2,800.
        self.assertAlmostEqual(rows[10]["replacement_cost_vnd"], 2800.0)
        self.assertEqual(rows[11]["replacement_cost_vnd"], 0)

    def test_pv_degradation_rate_derived_from_reopt_pv_inputs(self):
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        reopt_results["inputs"]["PV"] = {"degradation_fraction": 0.01}

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            evn_energy_escalation_rate=0.0,
            project_years=2,
        )

        rows = result["annual_cash_flows"]
        self.assertAlmostEqual(
            rows[1]["esco_energy_revenue_vnd"],
            rows[0]["esco_energy_revenue_vnd"] * 0.99,
        )

    def test_extra_replacement_costs_add_to_the_bess_replacement(self):
        # Verifies that extra_replacement_costs_by_year sums element-wise with
        # the base BESS replacement costs through the public entry point, not just
        # in unit tests of the private helper. This guards against regressions like
        # moving the merge block below cash_flow_inputs.update(cash_flow_overrides).
        reopt_results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        reopt_results["inputs"]["ElectricStorage"].update({
            "replace_cost_per_kw": 80.0,
            "replace_cost_per_kwh": 100.0,
            "battery_replacement_year": 10,
        })
        reopt_results["outputs"]["ElectricStorage"].update({
            "size_kw": 10.0,
            "size_kwh": 20.0,
        })

        # Case 1: With extra replacement costs (e.g., PV inverter in year 10).
        result_with_extra = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=12,
            extra_replacement_costs_by_year=[0]*9 + [1000],
        )

        # Case 2: Base BESS replacement only.
        result_base_only = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=12,
        )

        rows_with_extra = result_with_extra["annual_cash_flows"]
        rows_base_only = result_base_only["annual_cash_flows"]

        # Assertion 1: Merged year-10 value is the SUM (3800.0), not either alone.
        self.assertAlmostEqual(rows_with_extra[9]["replacement_cost_vnd"], 3800.0)

        # Assertion 2: Base-only case is still 2800.0 (so extra genuinely added).
        self.assertAlmostEqual(rows_base_only[9]["replacement_cost_vnd"], 2800.0)

        # Assertion 3: Year with no replacement stays 0.0 (merge did not smear).
        self.assertEqual(rows_with_extra[0]["replacement_cost_vnd"], 0)


class VietnamSurplusExportAdapterTests(TestCase):
    """Decree 243/2026 surplus-export extraction, cap and price resolution."""

    def _results_with_surplus(self):
        # PV: 1000 to load, 400 to grid, 200 curtailed, 400 to storage per hour
        # over 2 hours -> total output 2000/h; surplus (grid + curtailed) 600/h.
        results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        results["outputs"]["PV"] = {
            "size_kw": 100,
            "installed_cost_per_kw": 1000,
            "electric_to_load_series_kw": [1000, 1000],
            "electric_to_grid_series_kw": [400, 400],
            "electric_curtailed_series_kw": [200, 200],
            "electric_to_storage_series_kw": [400, 400],
        }
        return results

    def test_surplus_not_extracted_when_config_absent(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results_with_surplus(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
        )
        self.assertNotIn("surplus_export_kwh", result["annual_cash_flows"][0])
        self.assertNotIn("surplus_export", result["derivation"])

    def test_surplus_not_extracted_when_disabled(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results_with_surplus(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            surplus_export={"enabled": False, "region": "south"},
        )
        self.assertNotIn("surplus_export_kwh", result["annual_cash_flows"][0])

    def test_surplus_cap_does_not_bind_below_fifty_percent(self):
        # Surplus 1200 kWh vs 50% of 4000 total output = 2000 cap -> uncapped.
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results_with_surplus(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            surplus_export={"enabled": True, "region": "south"},
        )
        self.assertAlmostEqual(
            result["derivation"]["surplus_export"]["sold_kwh_year1"], 1200.0
        )

    def test_surplus_cap_binds_at_fifty_percent_of_output(self):
        # Make surplus exceed the 50% cap: grid 900 + curtailed 900 per hour ->
        # surplus 3600; total output = 1000(load)+900+900 = 2800/h -> 5600 total;
        # cap = 0.5 * 5600 = 2800 < 3600 surplus -> sold capped to 2800.
        results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        results["outputs"]["PV"] = {
            "size_kw": 100,
            "installed_cost_per_kw": 1000,
            "electric_to_load_series_kw": [1000, 1000],
            "electric_to_grid_series_kw": [900, 900],
            "electric_curtailed_series_kw": [900, 900],
        }
        result = calculate_esco_pro_forma_from_reopt_results(
            results,
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            surplus_export={"enabled": True, "region": "south"},
        )
        self.assertAlmostEqual(
            result["derivation"]["surplus_export"]["sold_kwh_year1"], 2800.0
        )

    def test_custom_cap_fraction_is_applied(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results_with_surplus(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            surplus_export={"enabled": True, "region": "south", "cap_fraction": 0.25},
        )
        # cap = 0.25 * 4000 = 1000 < surplus 1200 -> sold capped to 1000.
        self.assertAlmostEqual(
            result["derivation"]["surplus_export"]["sold_kwh_year1"], 1000.0
        )

    def test_price_resolved_from_region_default_and_converted_to_usd(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results_with_surplus(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            surplus_export={"enabled": True, "region": "south"},
        )
        # South ceiling 1012.0 VND/kWh < prior-year avg 1426.6 -> price 1012.0 VND.
        self.assertAlmostEqual(
            result["derivation"]["surplus_export"]["price_usd_per_kwh"],
            1012.0 / 25000,
        )

    def test_explicit_price_overrides_region_default(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results_with_surplus(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            surplus_export={"enabled": True, "price_vnd_per_kwh": 1300.0},
        )
        self.assertAlmostEqual(
            result["derivation"]["surplus_export"]["price_usd_per_kwh"],
            1300.0 / 25000,
        )

    def test_region_required_when_price_not_explicit(self):
        with self.assertRaises(ValueError):
            calculate_esco_pro_forma_from_reopt_results(
                self._results_with_surplus(),
                esco_energy_discount_fraction=0.9,
                project_years=1,
                exchange_rate_vnd_per_usd=25000,
                surplus_export={"enabled": True},
            )

    def test_surplus_revenue_appears_in_annual_rows(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results_with_surplus(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            surplus_export={"enabled": True, "region": "south"},
        )
        row = result["annual_cash_flows"][0]
        self.assertAlmostEqual(row["surplus_export_kwh"], 1200.0)
        self.assertAlmostEqual(
            row["surplus_export_revenue_usd"], 1200.0 * (1012.0 / 25000)
        )

    def test_enabled_surplus_rejected_under_dppa(self):
        results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        results["outputs"]["ElectricLoad"] = {"load_series_kw": [10, 10]}
        results["outputs"]["PV"] = {
            "size_kw": 100,
            "installed_cost_per_kw": 1000,
            "electric_to_load_series_kw": [6, 6],
            "electric_to_grid_series_kw": [1, 1],
            "electric_curtailed_series_kw": [0, 0],
        }
        dppa_inputs = {
            "type": "grid_dppa_cfd",
            "fmp_series_vnd_per_kwh": [1500.0, 1500.0],
            "cfd_strike_per_kwh_vnd": 1700.0,
            "cfd_contract_volume_kwh_per_hour": 1.0,
            "transmission_loss_factor_k": 1.026,
            "distribution_loss_factor_kpp": 1.027263,
            "allocation_fraction_delta": 1.0,
            "c_dppa_service_fee_vnd_per_kwh": 360.0,
            "c_cl_settlement_adder_vnd_per_kwh": 163.0,
            "cfd_strike_escalation_rate": 0.0,
            "fee_escalation_rate": 0.0,
        }
        with self.assertRaises(ValueError):
            calculate_esco_pro_forma_from_reopt_results(
                results,
                esco_energy_discount_fraction=0.9,
                project_years=1,
                exchange_rate_vnd_per_usd=25000,
                dppa_inputs=dppa_inputs,
                surplus_export={"enabled": True, "region": "south"},
            )


class VietnamPhysicalDppaAdapterTests(TestCase):
    """ND57 Điều 25 private-wire DPPA config resolution: matched-energy series,
    VND→USD PPA price, nested surplus, and the top-level-surplus rejection."""

    def _physical_results(self):
        # PV: 1000 to load, 400 to grid, 200 curtailed, 400 to storage per hour
        # over 2 hours; storage_to_load [3, 4] from the fake results.
        results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        results["outputs"]["PV"] = {
            "size_kw": 100,
            "installed_cost_per_kw": 1000,
            "electric_to_load_series_kw": [1000, 1000],
            "electric_to_grid_series_kw": [400, 400],
            "electric_curtailed_series_kw": [200, 200],
            "electric_to_storage_series_kw": [400, 400],
        }
        return results

    def _physical_inputs(self, **overrides):
        inputs = {"type": "physical_private_wire", "ppa_price_vnd_per_kwh": 2500.0}
        inputs.update(overrides)
        return inputs

    def test_matched_energy_is_project_served_series(self):
        # PV→load [1,2] + battery→load [3,4] (can_grid_charge False) -> 10 kWh.
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            dppa_inputs=self._physical_inputs(),
        )
        self.assertEqual(result["derivation"]["structure"], "physical_dppa")
        physical = result["derivation"]["physical_dppa"]
        self.assertAlmostEqual(physical["matched_kwh_year1"], 10.0)

    def test_ppa_price_converted_vnd_to_usd_at_contract_fx(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            dppa_inputs=self._physical_inputs(),
        )
        physical = result["derivation"]["physical_dppa"]
        self.assertAlmostEqual(physical["ppa_price_usd_per_kwh"], 2500.0 / 25000)
        # matched 10 kWh × 0.1 USD/kWh = 1.0 USD PPA revenue in year 1.
        self.assertAlmostEqual(
            result["annual_cash_flows"][0]["ppa_energy_revenue_usd"], 1.0
        )

    def test_ppa_price_required(self):
        with self.assertRaises(ValueError):
            calculate_esco_pro_forma_from_reopt_results(
                _fake_reopt_results(can_grid_charge=False),
                esco_energy_discount_fraction=0.9,
                project_years=1,
                exchange_rate_vnd_per_usd=25000,
                dppa_inputs={"type": "physical_private_wire"},
            )

    def test_escalation_carried_through(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            dppa_inputs=self._physical_inputs(ppa_price_escalation_rate=0.03),
        )
        self.assertAlmostEqual(
            result["derivation"]["physical_dppa"]["ppa_price_escalation_rate"], 0.03
        )

    def test_nested_surplus_resolves_and_monetizes(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._physical_results(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            dppa_inputs=self._physical_inputs(
                surplus_export={"enabled": True, "region": "south"}
            ),
        )
        # surplus = grid 800 + curtailed 400 = 1200; cap 0.5 × 4000 output = 2000
        # -> uncapped, sold 1200.
        self.assertAlmostEqual(
            result["derivation"]["surplus_export"]["sold_kwh_year1"], 1200.0
        )
        self.assertIn("surplus_export_revenue_usd", result["annual_cash_flows"][0])

    def test_disabled_nested_surplus_not_monetized(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._physical_results(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            dppa_inputs=self._physical_inputs(
                surplus_export={"enabled": False, "region": "south"}
            ),
        )
        self.assertNotIn("surplus_export", result["derivation"])

    def test_top_level_surplus_config_rejected_with_physical(self):
        with self.assertRaises(ValueError):
            calculate_esco_pro_forma_from_reopt_results(
                self._physical_results(),
                esco_energy_discount_fraction=0.9,
                project_years=1,
                exchange_rate_vnd_per_usd=25000,
                dppa_inputs=self._physical_inputs(),
                surplus_export={"enabled": True, "region": "south"},
            )


class VietnamDirectOwnershipAdapterTests(TestCase):
    """Factory self-invest (DIRECT_OWNERSHIP) config resolution: reuses the ESCO
    bill extraction, flags the structure, allows the top-level surplus leg, and
    is mutually exclusive with any DPPA block."""

    def _direct_results(self):
        results = deepcopy(_fake_reopt_results(can_grid_charge=False))
        results["outputs"]["PV"] = {
            "size_kw": 100,
            "installed_cost_per_kw": 1000,
            "electric_to_load_series_kw": [1, 2],
            "electric_to_grid_series_kw": [400, 400],
            "electric_curtailed_series_kw": [200, 200],
            "electric_to_storage_series_kw": [0, 0],
        }
        return results

    def test_selects_structure_and_captures_full_avoided_bill(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            direct_ownership={"enabled": True},
        )
        self.assertEqual(result["derivation"]["structure"], "direct_ownership")
        row = result["annual_cash_flows"][0]
        # bill savings = bau 50000 − optimized 30000 (full delta, energy + demand).
        self.assertAlmostEqual(row["bill_savings_revenue_vnd"], 20000.0)
        self.assertAlmostEqual(row["esco_energy_revenue_vnd"], 0.0)

    def test_defaults_to_standard_flat_and_profitable_host(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            direct_ownership={"enabled": True},
        )
        self.assertEqual(result["derivation"]["cit"]["regime"], "standard_flat")
        self.assertTrue(
            result["derivation"]["direct_ownership"]["assume_profitable_host"]
        )

    def test_assume_profitable_host_false_carries_through(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            direct_ownership={"enabled": True, "assume_profitable_host": False},
        )
        self.assertFalse(
            result["derivation"]["direct_ownership"]["assume_profitable_host"]
        )

    def test_cit_regime_override_carried_through(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            direct_ownership={
                "enabled": True,
                "cit_regime": "re_producer",
                "assume_profitable_host": False,
            },
        )
        self.assertEqual(result["derivation"]["cit"]["regime"], "re_producer")

    def test_top_level_surplus_export_allowed_with_direct_ownership(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._direct_results(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            exchange_rate_vnd_per_usd=25000,
            direct_ownership={"enabled": True},
            surplus_export={"enabled": True, "region": "south"},
        )
        self.assertEqual(result["derivation"]["structure"], "direct_ownership")
        self.assertIn("surplus_export", result["derivation"])
        self.assertIn(
            "surplus_export_revenue_usd", result["annual_cash_flows"][0]
        )

    def test_physical_dppa_block_rejected_with_direct_ownership(self):
        with self.assertRaises(ValueError):
            calculate_esco_pro_forma_from_reopt_results(
                _fake_reopt_results(can_grid_charge=False),
                esco_energy_discount_fraction=0.9,
                project_years=1,
                exchange_rate_vnd_per_usd=25000,
                direct_ownership={"enabled": True},
                dppa_inputs={"type": "physical_private_wire",
                             "ppa_price_vnd_per_kwh": 2500.0},
            )

    def test_disabled_block_does_not_select_direct_ownership(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            direct_ownership={"enabled": False},
        )
        self.assertEqual(result["derivation"]["structure"], "esco")
        self.assertNotIn("direct_ownership", result["derivation"])


class ConstructionFinancingAdapterTests(TestCase):
    """Construction + grace ride the shared financing-override path (like debt
    fraction / rate / term) straight through to the cash flow."""

    def test_construction_and_grace_inputs_flow_to_cash_flow(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            construction_months=12,
            principal_grace_years=2,
        )

        construction = result["derivation"]["construction"]
        self.assertEqual(construction["construction_months"], 12)
        self.assertEqual(construction["principal_grace_years"], 2)
        # capex 110,000 (PV 100,000 + BESS 10,000) × 0.7 debt × 8.5% × 0.5.
        self.assertAlmostEqual(construction["idc_usd"], 3272.5)
        self.assertAlmostEqual(construction["cod_debt_balance_usd"], 80272.5)

    def test_defaults_leave_derivation_without_construction_block(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
        )

        self.assertNotIn("construction", result["derivation"])


class UsdDebtAdapterTests(TestCase):
    """debt_currency rides the shared financing-override path straight through
    to the cash flow, and defaults to VND (no derivation label)."""

    def test_usd_debt_currency_flows_to_cash_flow_and_resolves_default_rate(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
            debt_currency="USD",
        )

        self.assertEqual(result["derivation"]["debt_currency"], "USD")
        self.assertAlmostEqual(
            result["derivation"]["debt_interest_rate_fraction"], 0.05
        )

    def test_defaults_leave_derivation_without_debt_currency_label(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False),
            esco_energy_discount_fraction=0.9,
            project_years=1,
        )

        self.assertNotIn("debt_currency", result["derivation"])


def _battery_only_reopt_results():
    # A grid-charging BESS with no PV tech at all: REopt omits (or zeroes) the
    # PV output block, so the project-served series is empty.
    results = deepcopy(_fake_reopt_results(can_grid_charge=True))
    del results["outputs"]["PV"]
    return results


class ExtraReplacementCostsTests(unittest.TestCase):
    """Thailand books an inverter replacement without losing the BESS one."""

    def test_extra_costs_add_to_the_existing_series(self):
        merged = _merge_replacement_costs([0.0, 0.0, 100.0], [0.0, 50.0, 25.0])
        self.assertEqual(merged, [0.0, 50.0, 125.0])

    def test_longer_extra_series_extends_the_result(self):
        merged = _merge_replacement_costs([0.0, 100.0], [0.0, 0.0, 0.0, 70.0])
        self.assertEqual(merged, [0.0, 100.0, 0.0, 70.0])

    def test_missing_base_series_is_treated_as_zeros(self):
        merged = _merge_replacement_costs(None, [0.0, 40.0])
        self.assertEqual(merged, [0.0, 40.0])

    def test_missing_extra_series_leaves_the_base_untouched(self):
        merged = _merge_replacement_costs([0.0, 100.0], None)
        self.assertEqual(merged, [0.0, 100.0])


class PvInverterReplacementTests(TestCase):
    """The shared core books the PV inverter event for both countries:
    fraction x SOLVED PV capex in the policy year, added to the BESS event."""

    def _results(self, pv_kw=100, bess=False):
        results = deepcopy(_fake_reopt_results(can_grid_charge=True))
        results["outputs"]["PV"]["size_kw"] = pv_kw
        if bess:
            results["inputs"]["ElectricStorage"].update(
                {"replace_cost_per_kw": 100.0, "replace_cost_per_kwh": 150.0,
                 "battery_replacement_year": 10}
            )
            results["outputs"]["ElectricStorage"].update({"size_kw": 10, "size_kwh": 20})
        return results

    def test_the_event_lands_at_fraction_of_solved_pv_capex_in_the_policy_year(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=100),
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )
        series = result["derivation"]["replacement_costs_by_year_usd"]
        self.assertEqual(len(series), 11)
        self.assertAlmostEqual(series[10], 10000.0)      # 100 kW x 1000 x 0.10, year 11
        self.assertEqual(sum(series[:10]), 0.0)
        self.assertEqual(
            result["derivation"]["pv_inverter_replacement"],
            {"year": 11, "fraction": 0.10, "cost_usd": 10000.0},
        )

    def test_the_event_adds_to_the_bess_event_rather_than_replacing_it(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=100, bess=True),
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )
        series = result["derivation"]["replacement_costs_by_year_usd"]
        self.assertAlmostEqual(series[9], 10 * 100.0 + 20 * 150.0)   # BESS, year 10
        self.assertAlmostEqual(series[10], 10000.0)                   # PV inverter, year 11

    def test_the_event_adds_to_an_explicit_extra_series_too(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=100),
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
            extra_replacement_costs_by_year=[0.0] * 10 + [1.0],
        )
        self.assertAlmostEqual(
            result["derivation"]["replacement_costs_by_year_usd"][10], 10001.0
        )

    def test_no_pv_means_no_event_and_no_block(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=0, bess=True),
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )
        series = result["derivation"]["replacement_costs_by_year_usd"]
        self.assertEqual(len(series), 10)
        self.assertNotIn("pv_inverter_replacement", result["derivation"])

    def test_omitting_the_policy_keys_books_nothing(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=100),
            esco_energy_discount_fraction=0.9,
        )
        self.assertEqual(result["derivation"].get("replacement_costs_by_year_usd"), [])
        self.assertNotIn("pv_inverter_replacement", result["derivation"])


class BatteryFadeInputsTests(TestCase):
    """The battery quantities the cash flow derates by state of health, on a
    full-year fake so the SOH engine has a year to replay."""

    HOURS = 8760

    def _results(self, can_grid_charge, pv_kw=100.0, demand=False):
        hours = self.HOURS
        results = {
            "inputs": {
                "ElectricTariff": {"tou_energy_rates_per_kwh": [0.1] * hours},
                "ElectricStorage": {"can_grid_charge": can_grid_charge},
                "Financial": {"owner_discount_rate_fraction": 0.11},
            },
            "outputs": {
                "PV": {
                    "size_kw": pv_kw,
                    "installed_cost_per_kw": 1000,
                    "electric_to_load_series_kw": [2.0 if pv_kw else 0.0] * hours,
                    "electric_to_storage_series_kw": [1.0 if pv_kw else 0.0] * hours,
                    "electric_curtailed_series_kw": [0.0] * hours,
                },
                "ElectricStorage": {
                    "size_kw": 10.0,
                    "size_kwh": 20.0,
                    "initial_capital_cost": 10000,
                    "soc_series_fraction": [0.5] * hours,
                    "storage_to_load_series_kw": [1.0] * hours,
                },
                "ElectricUtility": {
                    "electric_to_load_series_kw": [4.0] * hours,
                    "electric_to_storage_series_kw": [1.2 if can_grid_charge else 0.0] * hours,
                },
                "ElectricLoad": {"load_series_kw": [10.0] * hours},
                "ElectricTariff": {
                    "year_one_bill_before_tax_bau": 50000,
                    "year_one_bill_before_tax": 30000,
                    "year_one_demand_cost_before_tax_bau": 8000,
                    "year_one_demand_cost_before_tax": 3000,
                },
                "Financial": {"year_one_om_costs_before_tax": 1000},
            },
        }
        if demand:
            results["inputs"]["ElectricTariff"]["monthly_demand_rates"] = [1.0] * 12
        return results

    def test_pv_charged_storage_splits_served_value_and_share(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=False), esco_energy_discount_fraction=0.9,
            project_years=2)

        fade = result["derivation"]["battery_fade"]
        # 8760 h x 1 kW x 0.1 USD/kWh through the battery; served = 2 + 1 kW.
        self.assertAlmostEqual(fade["served_retail_value_usd"], 876.0)
        self.assertAlmostEqual(fade["energy_revenue_usd"], 876.0 * 0.9)
        self.assertEqual(fade["unserved_energy_value_usd"], 0.0)
        self.assertAlmostEqual(fade["matched_energy_share"], 1.0 / 3.0)
        self.assertEqual(len(fade["soh_by_year"]), 2)
        self.assertLess(fade["soh_by_year"][1], fade["soh_by_year"][0])
        self.assertIn("served series", fade["energy_attribution"])
        self.assertEqual(fade["demand_attribution"], "counterfactual")
        self.assertEqual(fade["demand_savings_usd"], 0.0)   # no demand structure: 0 either way
        self.assertNotIn("soh_fraction_by_day", fade["soh"])
        self.assertEqual(fade["soh"]["coefficients"]["cycle_life_efc"], 8000)

    def test_grid_charged_storage_beside_pv_books_no_energy_derate_under_esco(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=True), esco_energy_discount_fraction=0.9,
            project_years=2)

        fade = result["derivation"]["battery_fade"]
        self.assertEqual(fade["energy_revenue_usd"], 0.0)
        self.assertEqual(fade["served_retail_value_usd"], 0.0)
        self.assertEqual(fade["unserved_energy_value_usd"], 0.0)
        self.assertEqual(fade["matched_energy_share"], 0.0)
        self.assertIn("not booked", fade["energy_attribution"])

    def test_battery_only_case_uses_the_net_arbitrage_value(self):
        results = self._results(can_grid_charge=True, pv_kw=0.0)
        results["outputs"]["ElectricUtility"]["electric_to_storage_series_kw"] = [0.4] * self.HOURS

        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=2)

        fade = result["derivation"]["battery_fade"]
        # discharge 876 at retail minus grid charging 0.4 kW x 8760 x 0.1 = 350.4
        self.assertAlmostEqual(fade["unserved_energy_value_usd"], 876.0 - 350.4)
        self.assertEqual(fade["energy_revenue_usd"], 0.0)
        self.assertIn("net retail value", fade["energy_attribution"])

    def test_direct_ownership_with_grid_charging_books_the_net_value(self):
        results = self._results(can_grid_charge=True)
        results["outputs"]["ElectricUtility"]["electric_to_storage_series_kw"] = [0.4] * self.HOURS

        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.0, project_years=2,
            direct_ownership={"enabled": True})

        fade = result["derivation"]["battery_fade"]
        self.assertAlmostEqual(fade["unserved_energy_value_usd"], 876.0 - 350.4)
        self.assertEqual(fade["served_retail_value_usd"], 0.0)

    def test_net_energy_value_is_floored_at_zero(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=True, pv_kw=0.0), esco_energy_discount_fraction=0.9,
            project_years=2)

        # charging 1.2 kW costs more than the 1 kW discharged returns at a flat rate
        self.assertEqual(result["derivation"]["battery_fade"]["unserved_energy_value_usd"], 0.0)

    def test_demand_attribution_uses_the_counterfactual(self):
        results = self._results(can_grid_charge=False, demand=True)
        # load 10, PV available 3 (2 to load + 1 to storage): counterfactual
        # purchase 7 every hour; the solved purchase is 4. Twelve months at 1/kW.
        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=1)

        fade = result["derivation"]["battery_fade"]
        self.assertAlmostEqual(fade["demand_savings_usd"], 12 * (7.0 - 4.0))
        self.assertEqual(fade["demand_attribution"], "counterfactual")

    def test_unsupported_demand_structure_is_reported_not_guessed(self):
        results = self._results(can_grid_charge=False)
        results["inputs"]["ElectricTariff"]["urdb_label"] = "abc"

        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=1)

        fade = result["derivation"]["battery_fade"]
        self.assertEqual(fade["demand_savings_usd"], 0.0)
        self.assertIn("unsupported", fade["demand_attribution"])

    def test_cycle_life_override_reaches_the_curve(self):
        a = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=False), esco_energy_discount_fraction=0.9,
            project_years=2)
        b = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=False), esco_energy_discount_fraction=0.9,
            project_years=2, bess_cycle_life_efc=2000)

        self.assertLess(b["derivation"]["battery_fade"]["soh_by_year"][1],
                        a["derivation"]["battery_fade"]["soh_by_year"][1])
        self.assertEqual(b["derivation"]["battery_fade"]["soh"]["coefficients"]["cycle_life_efc"], 2000)

    def test_levelized_storage_series_are_put_back_on_a_first_year_basis(self):
        results = self._results(can_grid_charge=False)
        # lambda = 0.5: REopt's series carry half the true first-year production
        results["outputs"]["PV"]["year_one_energy_produced_kwh"] = 1000.0
        results["outputs"]["PV"]["annual_energy_produced_kwh"] = 500.0

        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=1)

        fade = result["derivation"]["battery_fade"]
        self.assertAlmostEqual(fade["served_retail_value_usd"], 876.0 / 0.5)
        self.assertAlmostEqual(fade["matched_energy_share"], 1.0 / 3.0)

    def test_augment_treatment_books_the_augmentation_and_does_not_derate(self):
        results = self._results(can_grid_charge=False)
        results["inputs"]["ElectricStorage"]["installed_cost_per_kwh"] = 150.0
        derate = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=2)
        augment = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=2,
            battery_ageing_treatment="augment",
            bess_augmentation_price_declination_rate=0.05)

        fade = augment["derivation"]["battery_fade"]
        self.assertEqual(fade["treatment"], "augment")
        self.assertEqual(fade["augmentation_price_per_kwh_usd"], 150.0)
        self.assertEqual(fade["augmentation_price_declination_rate"], 0.05)
        self.assertEqual(len(fade["augmentation_cost_by_year_usd"]), 2)
        self.assertGreater(fade["augmentation_cost_by_year_usd"][0], 0.0)
        rows = augment["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["battery_augmentation_cost_usd"],
                               fade["augmentation_cost_by_year_usd"][0])
        # savings are not derated in year 2
        self.assertAlmostEqual(rows[1]["esco_energy_revenue_usd"],
                               derate["annual_cash_flows"][1]["esco_energy_revenue_usd"]
                               + derate["annual_cash_flows"][1]["battery_fade_loss_usd"] * 0.9)
        # the derate run carries the figure for information and no row
        d_fade = derate["derivation"]["battery_fade"]
        self.assertEqual(d_fade["treatment"], "derate")
        self.assertGreater(d_fade["augmentation_cost_by_year_usd"][0], 0.0)
        self.assertNotIn("battery_augmentation_cost_usd", derate["annual_cash_flows"][0])

    def test_unknown_treatment_is_refused(self):
        with self.assertRaises(ValueError):
            calculate_esco_pro_forma_from_reopt_results(
                self._results(can_grid_charge=False), esco_energy_discount_fraction=0.9,
                project_years=2, battery_ageing_treatment="replace")

    def test_no_battery_means_no_fade_block(self):
        results = self._results(can_grid_charge=False)
        results["outputs"]["ElectricStorage"] = {"size_kw": 0.0, "size_kwh": 0.0}

        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=1)

        self.assertNotIn("battery_fade", result["derivation"])

    def test_a_short_storage_series_means_no_fade_block(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            _fake_reopt_results(can_grid_charge=False), esco_energy_discount_fraction=0.9,
            project_years=1)

        self.assertNotIn("battery_fade", result["derivation"])


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
