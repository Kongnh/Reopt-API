"""Cover the de-levelization of REopt's levelized dispatch.

REopt applies a levelization factor to PV production inside the optimisation,
so annual_energy_produced_kwh is an escalation/discount/degradation weighted
average and year_one_energy_produced_kwh is the raw first year. The dispatch
series and therefore year_one_bill_before_tax carry that weighting despite
their names. The proforma then applies (1 - deg)^y on its own axis, so
without this correction degradation is counted roughly twice.
"""
import unittest

from proforma_vietnam.esco_pro_forma import (
    _levelization_factor,
    calculate_esco_pro_forma_from_reopt_results,
)


class LevelizationFactorTests(unittest.TestCase):
    def test_factor_is_the_ratio_of_levelized_to_raw_production(self):
        pv_outputs = [{
            "year_one_energy_produced_kwh": 2524235.0,
            "annual_energy_produced_kwh": 2424811.22,
        }]

        self.assertAlmostEqual(_levelization_factor(pv_outputs), 0.960612, places=6)

    def test_multiple_arrays_are_summed_before_the_ratio(self):
        pv_outputs = [
            {"year_one_energy_produced_kwh": 1000.0, "annual_energy_produced_kwh": 950.0},
            {"year_one_energy_produced_kwh": 3000.0, "annual_energy_produced_kwh": 2850.0},
        ]

        self.assertAlmostEqual(_levelization_factor(pv_outputs), 0.95, places=9)

    def test_no_pv_yields_one_so_a_battery_only_case_is_untouched(self):
        self.assertEqual(_levelization_factor([]), 1.0)

    def test_zero_production_yields_one_rather_than_dividing_by_zero(self):
        pv_outputs = [{
            "year_one_energy_produced_kwh": 0.0,
            "annual_energy_produced_kwh": 0.0,
        }]

        self.assertEqual(_levelization_factor(pv_outputs), 1.0)

    def test_missing_fields_yield_one(self):
        self.assertEqual(_levelization_factor([{"size_kw": 100.0}]), 1.0)


class DeLevelizationApplicationTests(unittest.TestCase):
    """Only three quantities depend on PV production. BAU, capex and O&M
    must not move at all: that invariant is what catches scaling the wrong
    thing, which is the likely way to get this change wrong."""

    def _inputs(self):
        from proforma_vietnam.esco_pro_forma import _apply_de_levelization

        return _apply_de_levelization

    def test_served_energy_is_inflated_by_one_over_lambda(self):
        apply = self._inputs()
        cash_flow_inputs = {
            "project_served_pv_kwh": [100.0, 200.0],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 0.0,
            "optimized_demand_charge_vnd": 0.0,
        }

        apply(cash_flow_inputs, 0.8)

        self.assertEqual(cash_flow_inputs["project_served_pv_kwh"], [125.0, 250.0])

    def test_the_savings_delta_scales_not_the_bill(self):
        apply = self._inputs()
        cash_flow_inputs = {
            "project_served_pv_kwh": [],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 500.0,
            "optimized_demand_charge_vnd": 400.0,
        }

        apply(cash_flow_inputs, 0.8)

        # savings 200 / 0.8 = 250, so the bill lands at 1000 - 250 = 750.
        # A test asserting 800 / 0.8 = 1000 would be asserting the wrong rule.
        self.assertAlmostEqual(cash_flow_inputs["optimized_evn_bill_vnd"], 750.0)
        self.assertAlmostEqual(cash_flow_inputs["optimized_demand_charge_vnd"], 375.0)

    def test_bau_is_never_touched_because_it_has_no_pv(self):
        apply = self._inputs()
        cash_flow_inputs = {
            "project_served_pv_kwh": [],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 500.0,
            "optimized_demand_charge_vnd": 400.0,
        }

        apply(cash_flow_inputs, 0.8)

        self.assertEqual(cash_flow_inputs["bau_evn_bill_vnd"], 1000.0)
        self.assertEqual(cash_flow_inputs["bau_demand_charge_vnd"], 500.0)

    def test_lambda_of_one_is_a_no_op(self):
        apply = self._inputs()
        before = {
            "project_served_pv_kwh": [100.0],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 500.0,
            "optimized_demand_charge_vnd": 400.0,
        }
        after = dict(before, project_served_pv_kwh=list(before["project_served_pv_kwh"]))

        apply(after, 1.0)

        self.assertEqual(after, before)


class EndToEndDeLevelizationTests(unittest.TestCase):
    """Drive the real call site, not just the two helpers in isolation.

    The unit tests above pin ``_apply_de_levelization`` directly, but nothing
    pinned that ``calculate_esco_pro_forma_from_reopt_results`` (the function
    every rebuild path actually calls) still invokes it. Without this, the
    only thing protecting the fix was a gitignored local baseline that a
    fresh clone does not have.
    """

    def test_demand_savings_equal_the_levelized_savings_divided_by_lambda(self):
        reopt_results = {
            "inputs": {
                "ElectricTariff": {"tou_energy_rates_per_kwh": [1000, 2000]},
                "ElectricStorage": {"can_grid_charge": False},
                "Financial": {"owner_discount_rate_fraction": 0.11},
            },
            "outputs": {
                "PV": {
                    "size_kw": 100,
                    "installed_cost_per_kw": 1000,
                    "electric_to_load_series_kw": [1, 2],
                    # lambda = annual / year_one = 900 / 1000 = 0.9
                    "year_one_energy_produced_kwh": 1000.0,
                    "annual_energy_produced_kwh": 900.0,
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
                "Financial": {"year_one_om_costs_before_tax": 1000},
            },
        }

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=1,
        )

        # REopt's reported (levelized) demand savings: 8000 - 3000 = 5000.
        # De-levelized by lambda = 0.9: 5000 / 0.9 = 5555.555...
        levelized_savings = 8000 - 3000
        lam = 900.0 / 1000.0
        expected_savings = levelized_savings / lam

        annual = result["annual_cash_flows"][0]
        self.assertAlmostEqual(annual["demand_charge_savings_vnd"], expected_savings)

        # Capex is untouched by the de-levelization: PV capex depends only on
        # size_kw * installed_cost_per_kw, not on any production series.
        self.assertEqual(result["summary"]["total_capex_vnd"], 110000)


class GridCfdDppaDispatchDeLevelizationTests(unittest.TestCase):
    """The grid-CfD DPPA settlement basis bypasses cash_flow_inputs entirely.

    esco_pro_forma.py assembles a ``dispatch`` dict straight from raw REopt
    series (electric_to_load/to_grid/curtailed, storage_to_load/to_grid) and
    hands it to settle_dppa_year_one. _apply_de_levelization above only
    touches cash_flow_inputs, so it never sees this dict -- without a
    separate correction, the whole DPPA revenue basis stays levelized while
    cash_flow.py still applies (1 - deg)^y on top, double counting
    degradation. This drives the real call site (not the helper in
    isolation) and checks it against an independently computed reference.
    """

    def test_dppa_settlement_uses_de_levelized_dispatch_not_raw_series(self):
        from proforma_vietnam.dppa_settlement import settle_dppa_year_one

        year_one_kwh = 1000.0
        annual_kwh = 900.0
        lam = annual_kwh / year_one_kwh  # 0.9

        pv_to_load = [10.0, 20.0]
        pv_to_grid = [5.0, 6.0]
        pv_curtailed = [1.0, 2.0]
        storage_to_load = [3.0, 4.0]
        storage_to_grid = [1.0, 1.0]
        load_kw = [10.0, 10.0]
        tou_rates = [1000.0, 2000.0]

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

        reopt_results = {
            "inputs": {
                "ElectricTariff": {"tou_energy_rates_per_kwh": tou_rates},
                "ElectricStorage": {"can_grid_charge": False},
                "Financial": {"owner_discount_rate_fraction": 0.11},
            },
            "outputs": {
                "PV": {
                    "size_kw": 100,
                    "installed_cost_per_kw": 1000,
                    "electric_to_load_series_kw": pv_to_load,
                    "electric_to_grid_series_kw": pv_to_grid,
                    "electric_curtailed_series_kw": pv_curtailed,
                    # lambda = annual / year_one = 900 / 1000 = 0.9
                    "year_one_energy_produced_kwh": year_one_kwh,
                    "annual_energy_produced_kwh": annual_kwh,
                },
                "ElectricStorage": {
                    "initial_capital_cost": 10000,
                    "storage_to_load_series_kw": storage_to_load,
                    "storage_to_grid_series_kw": storage_to_grid,
                },
                "ElectricLoad": {"load_series_kw": load_kw},
                "ElectricTariff": {
                    "year_one_bill_before_tax_bau": 50000,
                    "year_one_bill_before_tax": 30000,
                    "year_one_demand_cost_before_tax_bau": 8000,
                    "year_one_demand_cost_before_tax": 3000,
                },
                "Financial": {"year_one_om_costs_before_tax": 1000},
            },
        }

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=1,
            dppa_inputs=dppa_inputs,
        )
        annual = result["annual_cash_flows"][0]

        # Reference: de-levelize the same five series by hand (divide by
        # lambda, same direction the fix uses) and settle directly. load_kw
        # is the customer's actual load, not PV production, and is NOT
        # divided.
        expected_dispatch = {
            "load_kw": load_kw,
            "pv_to_load_kw": [v / lam for v in pv_to_load],
            "pv_to_grid_kw": [v / lam for v in pv_to_grid],
            "pv_curtailed_kw": [v / lam for v in pv_curtailed],
            "storage_to_load_kw": [v / lam for v in storage_to_load],
            "storage_to_grid_kw": [v / lam for v in storage_to_grid],
        }
        expected_year_one = settle_dppa_year_one(
            dppa_inputs=dppa_inputs,
            dispatch=expected_dispatch,
            evn_energy_rates_vnd_per_kwh=tou_rates,
        )["year_one"]

        # Year 1 (index 0): every escalation/degradation multiplier is 1, so
        # the annual row's DPPA keys equal the year_one settlement exactly.
        for key in (
            "generator_revenue_vnd", "c_dn_vnd", "c_dppa_vnd", "c_cl_vnd",
            "c_bl_vnd", "cfd_net_vnd",
        ):
            self.assertAlmostEqual(annual[key], expected_year_one[key], places=6, msg=key)
        # cash_flow.py's dppa_offtaker_cost_vnd recomputes the sum rather than
        # echoing year_one's offtaker_dppa_cost_vnd key, so check it directly.
        self.assertAlmostEqual(
            annual["dppa_offtaker_cost_vnd"],
            expected_year_one["c_dn_vnd"] + expected_year_one["c_dppa_vnd"]
            + expected_year_one["c_cl_vnd"] + expected_year_one["c_bl_vnd"]
            + expected_year_one["cfd_net_vnd"],
            places=6,
        )

        # Guard the guard: the de-levelized reference must actually differ
        # from what raw (still-levelized) series would produce, or this test
        # could pass whether or not the fix is present.
        raw_dispatch = {
            "load_kw": load_kw,
            "pv_to_load_kw": pv_to_load,
            "pv_to_grid_kw": pv_to_grid,
            "pv_curtailed_kw": pv_curtailed,
            "storage_to_load_kw": storage_to_load,
            "storage_to_grid_kw": storage_to_grid,
        }
        raw_year_one = settle_dppa_year_one(
            dppa_inputs=dppa_inputs,
            dispatch=raw_dispatch,
            evn_energy_rates_vnd_per_kwh=tou_rates,
        )["year_one"]
        self.assertNotAlmostEqual(
            expected_year_one["generator_revenue_vnd"],
            raw_year_one["generator_revenue_vnd"],
            places=2,
        )


if __name__ == "__main__":
    unittest.main()


class SurplusExportDeLevelizationTests(unittest.TestCase):
    """The fourth site reading raw levelized series.

    _apply_surplus_export builds both the surplus volume and the output cap
    from four REopt series that never pass through cash_flow_inputs, so
    _apply_de_levelization never sees them. No current case enables surplus
    export, which is exactly why this one survived three earlier passes.
    """

    def _pv_outputs(self):
        # lambda = 950 / 1000 = 0.95, so 1 / lambda is a clean 1.0526...
        return [{
            "year_one_energy_produced_kwh": 1000.0,
            "annual_energy_produced_kwh": 950.0,
            "electric_to_load_series_kw": [600.0],
            "electric_to_grid_series_kw": [200.0],
            "electric_to_storage_series_kw": [0.0],
            "electric_curtailed_series_kw": [150.0],
        }]

    def test_sold_energy_is_de_levelized(self):
        from proforma_vietnam.esco_pro_forma import _apply_surplus_export

        cash_flow_inputs = {}
        _apply_surplus_export(
            cash_flow_inputs,
            {"enabled": True, "price_vnd_per_kwh": 1000.0, "cap_fraction": 1.0},
            self._pv_outputs(),
            25000.0,
        )

        # Surplus = grid 200 + curtailed 150 = 350 levelized, / 0.95 = 368.42.
        # cap_fraction 1.0 means the cap never binds, so sold == surplus.
        self.assertAlmostEqual(
            cash_flow_inputs["surplus_export_kwh_year1"], 350.0 / 0.95, places=6
        )

    def test_no_pv_production_leaves_the_series_untouched(self):
        from proforma_vietnam.esco_pro_forma import _apply_surplus_export

        pv_outputs = [{
            "electric_to_grid_series_kw": [200.0],
            "electric_curtailed_series_kw": [150.0],
        }]
        cash_flow_inputs = {}
        _apply_surplus_export(
            cash_flow_inputs,
            {"enabled": True, "price_vnd_per_kwh": 1000.0, "cap_fraction": 1.0},
            pv_outputs,
            25000.0,
        )

        self.assertAlmostEqual(
            cash_flow_inputs["surplus_export_kwh_year1"], 350.0, places=6
        )


class TechnicalResultsSavingsMatchTheCashFlowTests(unittest.TestCase):
    """The fifth site of the levelization defect, and the one that reached a
    client-facing sheet.

    report_data._results_comparison reads REopt's tariff outputs directly,
    bypassing the correction esco_pro_forma applies. Before the fix, one
    workbook reported 263279 as "Utility Bill Savings" on Technical Results
    and 272717 as "Year 1 Buyer Savings" on Executive Summary: the same
    quantity, two numbers, differing by exactly the levelization factor.

    The invariant this pins is not "the number is 272717" but "the two
    sheets agree", which is what actually caught every instance of this
    defect. Tests and the regression gate stayed green through all five.
    """

    def _tariff(self):
        return {
            "year_one_bill_before_tax_bau": 1000.0,
            "year_one_bill_before_tax": 800.0,
            "year_one_demand_cost_before_tax_bau": 500.0,
            "year_one_demand_cost_before_tax": 400.0,
            "year_one_coincident_peak_cost_before_tax_bau": 0.0,
            "year_one_coincident_peak_cost_before_tax": 0.0,
        }

    def _pv(self):
        # lambda = 0.95
        return [{
            "year_one_energy_produced_kwh": 1000.0,
            "annual_energy_produced_kwh": 950.0,
        }]

    def test_savings_are_de_levelized_like_the_cash_flow(self):
        from proforma_vietnam.report_data import _results_comparison

        out = _results_comparison(self._tariff(), self._pv())

        # Levelized savings 200 / 0.95 = 210.526..., so the optimized bill
        # lands at 1000 - 210.526 and NOT at 800 / 0.95.
        self.assertAlmostEqual(out["utility_bill_savings_usd"], 200.0 / 0.95, places=9)
        self.assertAlmostEqual(out["demand_charge_savings_usd"], 100.0 / 0.95, places=9)

    def test_bau_is_untouched(self):
        from proforma_vietnam.report_data import _results_comparison

        out = _results_comparison(self._tariff(), self._pv())

        self.assertEqual(out["bau_utility_bill_usd"], 1000.0)
        self.assertEqual(out["bau_demand_charge_usd"], 500.0)

    def test_no_pv_is_a_no_op(self):
        from proforma_vietnam.report_data import _results_comparison

        out = _results_comparison(self._tariff(), [])

        self.assertEqual(out["utility_bill_savings_usd"], 200.0)
        self.assertEqual(out["demand_charge_savings_usd"], 100.0)
