from unittest import TestCase

from proforma_vietnam.report_data import build_vietnam_report_data, _upsample_series


class VietnamReportDataTests(TestCase):

    def test_normalizes_reopt_results_for_report_sheets(self):
        report = build_vietnam_report_data(
            _fake_reopt_results(),
            _cash_flow_result(),
            poa_irradiance_series=[100.0, 200.0],
        )

        self.assertEqual(
            report["system_sizing"],
            {
                "pv_kw": 100,
                "battery_kw": 50,
                "battery_kwh": 200,
            },
        )
        self.assertEqual(
            report["dispatch_profile"][0],
            {
                "hour": 1,
                "load_kw": 10,
                "pv_irradiance": 100.0,
                "pv_total_kw": 4,       # to_load 3 + to_storage 1 + curtailed 0
                "pv_to_load_kw": 3,
                "pv_to_storage_kw": 1,
                "pv_to_grid_kw": 0,
                "pv_curtailed_kw": 0,
                "grid_to_load_kw": 7,
                "grid_to_storage_kw": 0,
                "storage_to_load_kw": 0,
            },
        )
        self.assertEqual(report["dispatch_profile"][1]["pv_irradiance"], 200.0)
        self.assertEqual(report["dispatch_profile"][1]["pv_total_kw"], 7)
        self.assertEqual(report["dispatch_profile"][1]["grid_to_storage_kw"], 1)
        self.assertEqual(report["annual_production"]["pv_to_load_kwh"], 7)
        self.assertEqual(report["annual_production"]["grid_to_load_kwh"], 15)
        self.assertEqual(report["annual_production"]["storage_to_load_kwh"], 1)
        # Annual POA insolation = (100 + 200) / 1000; PR = specific yield
        # (0.2 + 0.5) / reference yield (0.3).
        self.assertAlmostEqual(
            report["solar_resource"]["annual_poa_irradiation_kwh_per_m2"], 0.3
        )
        self.assertAlmostEqual(
            report["solar_resource"]["performance_ratio"], 0.7 / 0.3
        )
        self.assertEqual(report["results_comparison"]["bau_utility_bill_usd"], 100000)
        self.assertEqual(report["results_comparison"]["optimized_utility_bill_usd"], 70000)
        self.assertEqual(report["developer_financial_performance"]["equity_irr_fraction"], 0.14)
        self.assertEqual(report["load_duration"][0]["load_kw"], 20)
        self.assertEqual(report["load_duration"][0]["net_load_kw"], 8)

    def test_solar_resource_degrades_without_irradiance(self):
        report = build_vietnam_report_data(_fake_reopt_results(), _cash_flow_result())

        self.assertIsNone(report["solar_resource"]["performance_ratio"])
        self.assertEqual(
            report["solar_resource"]["annual_poa_irradiation_kwh_per_m2"], 0.0
        )
        self.assertEqual(report["dispatch_profile"][0]["pv_irradiance"], 0)


class UpsampleSeriesTests(TestCase):

    def test_factor_of_one_returns_the_same_values(self):
        self.assertEqual(_upsample_series([1.0, 2.0], 1), [1.0, 2.0])

    def test_each_value_repeats_factor_times(self):
        self.assertEqual(
            _upsample_series([1.0, 2.0], 4),
            [1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0],
        )

    def test_empty_series_stays_empty(self):
        self.assertEqual(_upsample_series([], 4), [])

    def test_hourly_poa_becomes_quarter_hourly(self):
        self.assertEqual(len(_upsample_series([0.5] * 8760, 4)), 35040)


class DispatchIrradianceResolutionTests(TestCase):
    """Locks in the Task 8 split: _dispatch_rows must see irradiance
    up-sampled to the model's resolution, while _solar_resource must keep
    the original hourly series. Feeding the up-sampled series into
    _solar_resource instead would 4x annual_poa_irradiation_kwh_per_m2 -
    silently, since the dispatch row count and length checks alone would
    still pass.
    """

    def test_dispatch_rows_are_upsampled_while_solar_resource_stays_hourly(self):
        poa_series = [100.0] * 8760
        poa_series[0] = 500.0  # distinct first hour, so four equal values at
        # the start of the dispatch column can only come from the hour being
        # repeated, not from reading the raw hourly array by row index.

        report = build_vietnam_report_data(
            _fake_reopt_results(),
            _cash_flow_result(),
            poa_irradiance_series=poa_series,
            time_steps_per_hour=4,
        )

        rows = report["dispatch_profile"]
        self.assertEqual(len(rows), 35040)
        self.assertEqual(
            [row["pv_irradiance"] for row in rows[:4]],
            [500.0, 500.0, 500.0, 500.0],
        )

        # annual_poa_irradiation_kwh_per_m2 = sum(original 8760 series) / 1000
        # = (500.0 + 100.0 * 8759) / 1000 = 876.4. If _solar_resource were fed
        # the up-sampled 35040-row series instead, this would come out 4x too
        # high (3505.6) - the same bug class as this branch's founding
        # Critical (a Performance Ratio above 1.0, which is impossible).
        self.assertAlmostEqual(
            report["solar_resource"]["annual_poa_irradiation_kwh_per_m2"], 876.4
        )


class DispatchDisplayDeLevelizationTests(TestCase):
    """DISPLAYED dispatch and annual-production figures must divide by the
    same levelization factor the corrected cash flow already divides by
    (esco_pro_forma._levelization_factor). Before this, the workbook's
    Dispatch Profile sheet stayed levelized after the cash-flow fix landed
    (b7d7cf05, 72b6cdbe), so two sheets built from the same REopt solve
    showed the same physical quantity ~4-5 percent apart.
    """

    def _reopt_results(self, year_one_kwh=1000.0, annual_kwh=800.0):
        # lambda = annual_kwh / year_one_kwh = 800 / 1000 = 0.8 by default.
        return {
            "inputs": {
                "ElectricLoad": {"loads_kw": [10, 20]},
            },
            "outputs": {
                "PV": {
                    "size_kw": 100,
                    "electric_to_load_series_kw": [3, 4],
                    "electric_to_storage_series_kw": [1, 2],
                    "electric_curtailed_series_kw": [0, 1],
                    "electric_to_grid_series_kw": [2, 0],
                    "production_factor_series": [0.2, 0.5],
                    "year_one_energy_produced_kwh": year_one_kwh,
                    "annual_energy_produced_kwh": annual_kwh,
                },
                "ElectricStorage": {
                    "size_kw": 50,
                    "size_kwh": 200,
                    "storage_to_load_series_kw": [0, 1],
                },
                "ElectricUtility": {
                    "electric_to_load_series_kw": [7, 8],
                    "electric_to_storage_series_kw": [0, 1],
                },
                "ElectricTariff": {
                    "year_one_bill_before_tax_bau": 100000,
                    "year_one_bill_before_tax": 70000,
                    "year_one_demand_cost_before_tax_bau": 20000,
                    "year_one_demand_cost_before_tax": 12000,
                },
            },
        }

    def test_pv_and_storage_dispatch_series_divide_by_lambda(self):
        lam = 0.8
        report = build_vietnam_report_data(
            self._reopt_results(), _cash_flow_result(),
            poa_irradiance_series=[100.0, 200.0],
        )

        row0 = report["dispatch_profile"][0]
        self.assertAlmostEqual(row0["pv_to_load_kw"], 3 / lam)
        self.assertAlmostEqual(row0["pv_to_storage_kw"], 1 / lam)
        self.assertAlmostEqual(row0["pv_curtailed_kw"], 0 / lam)
        self.assertAlmostEqual(row0["pv_to_grid_kw"], 2 / lam)
        self.assertAlmostEqual(row0["storage_to_load_kw"], 0 / lam)
        # pv_total is built from the already de-levelized components above.
        self.assertAlmostEqual(row0["pv_total_kw"], (3 + 1 + 2 + 0) / lam)

        row1 = report["dispatch_profile"][1]
        self.assertAlmostEqual(row1["pv_to_load_kw"], 4 / lam)
        self.assertAlmostEqual(row1["pv_to_storage_kw"], 2 / lam)
        self.assertAlmostEqual(row1["pv_curtailed_kw"], 1 / lam)
        self.assertAlmostEqual(row1["storage_to_load_kw"], 1 / lam)

    def test_grid_and_customer_load_series_are_not_divided(self):
        report = build_vietnam_report_data(
            self._reopt_results(), _cash_flow_result(),
            poa_irradiance_series=[100.0, 200.0],
        )

        row0 = report["dispatch_profile"][0]
        row1 = report["dispatch_profile"][1]
        self.assertEqual(row0["load_kw"], 10)
        self.assertEqual(row1["load_kw"], 20)
        self.assertEqual(row0["grid_to_load_kw"], 7)
        self.assertEqual(row1["grid_to_load_kw"], 8)
        self.assertEqual(row1["grid_to_storage_kw"], 1)

    def test_annual_production_totals_divide_by_lambda(self):
        lam = 0.8
        report = build_vietnam_report_data(self._reopt_results(), _cash_flow_result())

        annual = report["annual_production"]
        self.assertAlmostEqual(annual["pv_to_load_kwh"], (3 + 4) / lam)
        self.assertAlmostEqual(annual["pv_to_storage_kwh"], (1 + 2) / lam)
        self.assertAlmostEqual(annual["storage_to_load_kwh"], (0 + 1) / lam)
        self.assertAlmostEqual(annual["pv_curtailed_kwh"], (0 + 1) / lam)
        self.assertAlmostEqual(annual["pv_to_grid_kwh"], (2 + 0) / lam)
        # Grid-sourced flows carry no PV levelization and must not move.
        self.assertEqual(annual["grid_to_load_kwh"], 15)
        self.assertEqual(annual["grid_to_storage_kwh"], 1)

    def test_no_pv_energy_fields_is_a_no_op(self):
        # No year_one_energy_produced_kwh / annual_energy_produced_kwh means
        # _levelization_factor returns 1.0, so dividing must be a no-op -
        # this is what keeps every pre-existing fixture in this file (none
        # of which set those two fields) byte-identical.
        report = build_vietnam_report_data(
            self._reopt_results(year_one_kwh=0.0, annual_kwh=0.0),
            _cash_flow_result(),
        )

        row0 = report["dispatch_profile"][0]
        self.assertEqual(row0["pv_to_load_kw"], 3)
        self.assertEqual(row0["pv_to_storage_kw"], 1)

    def test_performance_ratio_and_poa_irradiation_are_unchanged_by_de_levelization(self):
        """The regression most likely to slip through: production_factor_series
        is ALREADY a true first-year series (it equals
        year_one_energy_produced_kwh / size_kw for real REopt output), so
        dividing it again by lambda would silently change the Performance
        Ratio in a client-facing workbook. It must be identical whether or
        not the PV output carries a levelization factor != 1.
        """
        with_levelization = build_vietnam_report_data(
            self._reopt_results(year_one_kwh=1000.0, annual_kwh=800.0),
            _cash_flow_result(),
            poa_irradiance_series=[100.0, 200.0],
        )
        without_levelization = build_vietnam_report_data(
            self._reopt_results(year_one_kwh=0.0, annual_kwh=0.0),
            _cash_flow_result(),
            poa_irradiance_series=[100.0, 200.0],
        )

        self.assertAlmostEqual(
            with_levelization["solar_resource"]["performance_ratio"],
            without_levelization["solar_resource"]["performance_ratio"],
        )
        self.assertAlmostEqual(
            with_levelization["solar_resource"]["annual_poa_irradiation_kwh_per_m2"],
            without_levelization["solar_resource"]["annual_poa_irradiation_kwh_per_m2"],
        )
        # Pinned against the current value so a future change to either
        # series is caught here too, not just the equality above.
        self.assertAlmostEqual(
            with_levelization["solar_resource"]["performance_ratio"], 0.7 / 0.3
        )


def _fake_reopt_results():
    return {
        "inputs": {
            "ElectricLoad": {"loads_kw": [10, 20]},
        },
        "outputs": {
            "PV": {
                "size_kw": 100,
                "electric_to_load_series_kw": [3, 4],
                "electric_to_storage_series_kw": [1, 2],
                "electric_curtailed_series_kw": [0, 1],
                "production_factor_series": [0.2, 0.5],
            },
            "ElectricStorage": {
                "size_kw": 50,
                "size_kwh": 200,
                "storage_to_load_series_kw": [0, 1],
            },
            "ElectricUtility": {
                "electric_to_load_series_kw": [7, 8],
                "electric_to_storage_series_kw": [0, 1],
            },
            "ElectricTariff": {
                "year_one_bill_before_tax_bau": 100000,
                "year_one_bill_before_tax": 70000,
                "year_one_demand_cost_before_tax_bau": 20000,
                "year_one_demand_cost_before_tax": 12000,
            },
        },
    }


def _cash_flow_result():
    return {
        "summary": {
            "project_irr_fraction": 0.12,
            "equity_irr_fraction": 0.14,
            "npv_vnd": 123456,
            "average_dscr": 1.3,
            "simple_payback_years": 7.5,
            "roi_fraction": 1.8,
        }
    }
