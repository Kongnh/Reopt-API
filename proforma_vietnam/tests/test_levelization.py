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


if __name__ == "__main__":
    unittest.main()
