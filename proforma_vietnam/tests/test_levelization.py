"""Cover the restatement of REopt's levelized dispatch on a true first year.

REopt applies a levelization factor to PV production inside the optimisation,
so annual_energy_produced_kwh is an escalation/discount/degradation weighted
average and year_one_energy_produced_kwh is the raw first year. The dispatch
series and therefore year_one_bill_before_tax carry that weighting despite
their names. The proforma then applies (1 - deg)^y on its own axis, so the
dispatch has to be put back on a first-year basis first.

Until 2026-09-28 that was done by dividing every PV and storage flow, and the
savings delta, by lambda. That overstated year one by 2.8-3.9 percent against
a REopt re-solve at lambda = 1 (factory_a_v2, five cases): the extra first-year
PV lands mostly in hours that are already curtailing, the battery is bounded
by its own size, and the grid flow was left levelized, so the first-year
energy table summed to 9.58 GWh against a 9.34 GWh load. The restatement is
now hourly: the extra PV first displaces grid import in the same hour, the
rest is curtailed, and the battery keeps its solved dispatch.
"""
import unittest

from proforma_vietnam.esco_pro_forma import (
    _levelization_factor,
    _year_one_dispatch,
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


def _reopt_results(time_steps_per_hour=1, year_one_kwh=1000.0, annual_kwh=800.0):
    """Two intervals, lambda = 0.8 by default, so the extra PV is 25 percent.

    Interval 0: PV 4 all to load, grid 6, load 10. Extra PV 1 is fully
    absorbed by the grid import.
    Interval 1: PV 12 (6 load, 2 storage, 4 curtailed), battery 3 to load,
    grid 1, load 10. Extra PV 3: 1 displaces the grid, 2 is curtailed.
    """
    return {
        "inputs": {
            "Settings": {"time_steps_per_hour": time_steps_per_hour},
            "ElectricTariff": {"tou_energy_rates_per_kwh": [100.0, 200.0]},
            "ElectricStorage": {"can_grid_charge": False},
            "Financial": {"owner_discount_rate_fraction": 0.11},
        },
        "outputs": {
            "PV": {
                "size_kw": 100,
                "installed_cost_per_kw": 1000,
                "electric_to_load_series_kw": [4.0, 6.0],
                "electric_to_storage_series_kw": [0.0, 2.0],
                "electric_to_grid_series_kw": [0.0, 0.0],
                "electric_curtailed_series_kw": [0.0, 4.0],
                "year_one_energy_produced_kwh": year_one_kwh,
                "annual_energy_produced_kwh": annual_kwh,
            },
            "ElectricStorage": {
                "initial_capital_cost": 10000,
                "storage_to_load_series_kw": [0.0, 3.0],
                "storage_to_grid_series_kw": [0.0, 0.0],
            },
            "ElectricUtility": {
                "electric_to_load_series_kw": [6.0, 1.0],
                "electric_to_storage_series_kw": [0.0, 0.0],
            },
            "ElectricLoad": {"load_series_kw": [10.0, 10.0]},
            "ElectricTariff": {
                "year_one_bill_before_tax_bau": 50000,
                "year_one_bill_before_tax": 30000,
                "year_one_demand_cost_before_tax_bau": 8000,
                "year_one_demand_cost_before_tax": 3000,
            },
            "Financial": {"year_one_om_costs_before_tax": 1000},
        },
    }


class YearOneDispatchTests(unittest.TestCase):
    def test_extra_pv_displaces_grid_import_first_and_the_rest_is_curtailed(self):
        dispatch = _year_one_dispatch(_reopt_results())

        self.assertEqual(dispatch["pv_to_load_kw"], [5.0, 7.0])
        self.assertEqual(dispatch["grid_to_load_kw"], [5.0, 0.0])
        self.assertEqual(dispatch["pv_curtailed_kw"], [0.0, 6.0])

    def test_the_battery_keeps_its_solved_dispatch(self):
        dispatch = _year_one_dispatch(_reopt_results())

        self.assertEqual(dispatch["pv_to_storage_kw"], [0.0, 2.0])
        self.assertEqual(dispatch["storage_to_load_kw"], [0.0, 3.0])
        self.assertEqual(dispatch["storage_to_grid_kw"], [0.0, 0.0])
        self.assertEqual(dispatch["grid_to_storage_kw"], [0.0, 0.0])

    def test_the_load_balance_closes_every_interval(self):
        """The invariant the 1 / lambda scaling broke: PV to load + battery to
        load + grid to load must equal the load, hour by hour."""
        dispatch = _year_one_dispatch(_reopt_results())

        for index, load in enumerate([10.0, 10.0]):
            self.assertAlmostEqual(
                dispatch["pv_to_load_kw"][index]
                + dispatch["storage_to_load_kw"][index]
                + dispatch["grid_to_load_kw"][index],
                load,
            )

    def test_total_pv_is_the_true_first_year_production(self):
        dispatch = _year_one_dispatch(_reopt_results())
        pv_total = sum(
            sum(dispatch[key])
            for key in ("pv_to_load_kw", "pv_to_storage_kw", "pv_to_grid_kw", "pv_curtailed_kw")
        )

        self.assertAlmostEqual(pv_total, (4.0 + 12.0) / 0.8)

    def test_avoided_grid_energy_is_valued_at_the_hours_own_rate(self):
        dispatch = _year_one_dispatch(_reopt_results())

        self.assertAlmostEqual(dispatch["avoided_grid_kwh"], 2.0)
        self.assertAlmostEqual(dispatch["avoided_energy_cost"], 1.0 * 100.0 + 1.0 * 200.0)

    def test_sub_hourly_intervals_convert_kw_to_kwh(self):
        dispatch = _year_one_dispatch(_reopt_results(time_steps_per_hour=2))

        self.assertAlmostEqual(dispatch["avoided_grid_kwh"], 1.0)
        self.assertAlmostEqual(dispatch["avoided_energy_cost"], 150.0)

    def test_lambda_of_one_returns_the_solved_dispatch(self):
        dispatch = _year_one_dispatch(_reopt_results(annual_kwh=1000.0))

        self.assertEqual(dispatch["pv_to_load_kw"], [4.0, 6.0])
        self.assertEqual(dispatch["grid_to_load_kw"], [6.0, 1.0])
        self.assertEqual(dispatch["pv_curtailed_kw"], [0.0, 4.0])
        self.assertEqual(dispatch["avoided_energy_cost"], 0.0)
        self.assertEqual(dispatch["avoided_grid_kwh"], 0.0)

    def test_no_pv_production_fields_is_a_no_op(self):
        dispatch = _year_one_dispatch(_reopt_results(year_one_kwh=0.0, annual_kwh=0.0))

        self.assertEqual(dispatch["pv_to_load_kw"], [4.0, 6.0])
        self.assertEqual(dispatch["avoided_energy_cost"], 0.0)


class CashFlowUsesTheYearOneDispatchTests(unittest.TestCase):
    """Drive the real call site every rebuild path uses."""

    def _result(self):
        return calculate_esco_pro_forma_from_reopt_results(
            _reopt_results(),
            esco_energy_discount_fraction=0.9,
            project_years=1,
        )

    def test_served_energy_adds_only_the_absorbed_pv(self):
        derivation = self._result()["derivation"]

        # PV to load [5, 7] + battery to load [0, 3], valued at [100, 200].
        self.assertAlmostEqual(
            derivation["base_served_retail_value_usd"], 5 * 100 + 10 * 200
        )

    def test_energy_savings_grow_by_the_avoided_grid_cost_only(self):
        derivation = self._result()["derivation"]

        # 30000 - (100 + 200); the old rule gave 50000 - 20000 / 0.8 = 25000.
        self.assertAlmostEqual(derivation["optimized_evn_bill_year1_usd"], 29700.0)
        self.assertEqual(derivation["bau_evn_bill_year1_usd"], 50000)

    def test_demand_savings_keep_the_solved_value(self):
        """Extra PV can only lower a monthly peak, so keeping REopt's demand
        charge is the conservative side; scaling it by 1 / lambda was not."""
        annual = self._result()["annual_cash_flows"][0]

        self.assertAlmostEqual(annual["demand_charge_savings_vnd"], 8000 - 3000)

    def test_capex_is_untouched(self):
        self.assertEqual(self._result()["summary"]["total_capex_vnd"], 110000)


class GridCfdDppaDispatchTests(unittest.TestCase):
    """The grid-CfD DPPA settlement reads its own dispatch dict, which must be
    the same first-year dispatch the cash flow uses."""

    def test_dppa_settlement_uses_the_year_one_dispatch(self):
        from proforma_vietnam.dppa_settlement import settle_dppa_year_one

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
        reopt_results = _reopt_results()

        result = calculate_esco_pro_forma_from_reopt_results(
            reopt_results,
            esco_energy_discount_fraction=0.9,
            project_years=1,
            dppa_inputs=dppa_inputs,
        )
        annual = result["annual_cash_flows"][0]

        expected_dispatch = {
            "load_kw": [10.0, 10.0],
            "pv_to_load_kw": [5.0, 7.0],
            "pv_to_grid_kw": [0.0, 0.0],
            "pv_curtailed_kw": [0.0, 6.0],
            "storage_to_load_kw": [0.0, 3.0],
            "storage_to_grid_kw": [0.0, 0.0],
        }
        expected_year_one = settle_dppa_year_one(
            dppa_inputs=dppa_inputs,
            dispatch=expected_dispatch,
            evn_energy_rates_vnd_per_kwh=[100.0, 200.0],
        )["year_one"]

        for key in (
            "generator_revenue_vnd", "c_dn_vnd", "c_dppa_vnd", "c_cl_vnd",
            "c_bl_vnd", "cfd_net_vnd",
        ):
            self.assertAlmostEqual(annual[key], expected_year_one[key], places=6, msg=key)


class SurplusExportTests(unittest.TestCase):
    """_apply_surplus_export builds the surplus volume and the output cap from
    the same first-year dispatch."""

    def test_sold_energy_uses_the_year_one_curtailment(self):
        from proforma_vietnam.esco_pro_forma import _apply_surplus_export

        cash_flow_inputs = {}
        _apply_surplus_export(
            cash_flow_inputs,
            {"enabled": True, "price_vnd_per_kwh": 1000.0, "cap_fraction": 1.0},
            _year_one_dispatch(_reopt_results()),
            25000.0,
        )

        # Grid 0 + curtailed [0, 6]; cap_fraction 1.0 never binds.
        self.assertAlmostEqual(cash_flow_inputs["surplus_export_kwh_year1"], 6.0, places=6)

    def test_the_cap_is_a_share_of_the_year_one_output(self):
        from proforma_vietnam.esco_pro_forma import _apply_surplus_export

        cash_flow_inputs = {}
        _apply_surplus_export(
            cash_flow_inputs,
            {"enabled": True, "price_vnd_per_kwh": 1000.0, "cap_fraction": 0.1},
            _year_one_dispatch(_reopt_results()),
            25000.0,
        )

        self.assertAlmostEqual(
            cash_flow_inputs["surplus_export_kwh_year1"], 0.1 * 16.0 / 0.8, places=6
        )


class TechnicalResultsSavingsMatchTheCashFlowTests(unittest.TestCase):
    """report_data._results_comparison reads REopt's tariff outputs directly.
    The invariant this pins is "Technical Results and the cash flow agree",
    which is what caught every earlier instance of the levelization defect."""

    def _tariff(self):
        return {
            "year_one_bill_before_tax_bau": 1000.0,
            "year_one_bill_before_tax": 800.0,
            "year_one_demand_cost_before_tax_bau": 500.0,
            "year_one_demand_cost_before_tax": 400.0,
            "year_one_coincident_peak_cost_before_tax_bau": 0.0,
            "year_one_coincident_peak_cost_before_tax": 0.0,
        }

    def test_energy_savings_add_the_avoided_grid_cost(self):
        from proforma_vietnam.report_data import _results_comparison

        out = _results_comparison(self._tariff(), avoided_energy_cost=30.0)

        self.assertAlmostEqual(out["utility_bill_savings_usd"], 230.0)
        self.assertAlmostEqual(out["optimized_utility_bill_usd"], 770.0)
        self.assertAlmostEqual(out["demand_charge_savings_usd"], 100.0)

    def test_bau_is_untouched(self):
        from proforma_vietnam.report_data import _results_comparison

        out = _results_comparison(self._tariff(), avoided_energy_cost=30.0)

        self.assertEqual(out["bau_utility_bill_usd"], 1000.0)
        self.assertEqual(out["bau_demand_charge_usd"], 500.0)

    def test_the_sheet_agrees_with_the_cash_flow(self):
        from proforma_vietnam.report_data import build_vietnam_report_data

        reopt_results = _reopt_results()
        cash_flow = calculate_esco_pro_forma_from_reopt_results(
            reopt_results, esco_energy_discount_fraction=0.9, project_years=1,
        )
        report = build_vietnam_report_data(reopt_results, cash_flow)
        derivation = cash_flow["derivation"]

        self.assertAlmostEqual(
            report["results_comparison"]["optimized_utility_bill_usd"],
            derivation["optimized_evn_bill_year1_usd"],
        )


if __name__ == "__main__":
    unittest.main()
