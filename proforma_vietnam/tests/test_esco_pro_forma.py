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
