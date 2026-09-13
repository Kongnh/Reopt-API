import json
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.battery_soh import (
    augmentation_cost_by_year,
    battery_state_of_health,
    cycle_fade_coefficient_from_life,
)

FIXTURE = Path(__file__).parent / "fixtures" / "soh_probe_bess_arbitrage_5mw.json"


class CycleFadeCoefficientTests(TestCase):

    def test_eight_thousand_cycles_to_eighty_percent(self):
        self.assertAlmostEqual(cycle_fade_coefficient_from_life(8000), 2.5e-5)

    def test_rejects_a_non_positive_life(self):
        with self.assertRaises(ValueError):
            cycle_fade_coefficient_from_life(0)
        with self.assertRaises(ValueError):
            cycle_fade_coefficient_from_life(-1)


class ReoptReplicationTests(TestCase):
    """The replica must reproduce REopt's own state_of_health on the probe
    solve (hourly, so REopt's h factor is 1 and the two recurrences agree)."""

    def test_matches_reopt_state_of_health_day_by_day(self):
        probe = json.loads(FIXTURE.read_text(encoding="utf-8"))

        result = battery_state_of_health(
            size_kwh=probe["size_kwh"],
            soc_series_fraction=probe["soc_series_fraction"],
            discharge_series_kw=probe["storage_to_load_series_kw"],
            time_steps_per_hour=probe["time_steps_per_hour"],
            project_years=probe["analysis_years"],
            calendar_fade_coefficient=probe["calendar_fade_coefficient"],
            calendar_fade_exponent=probe["time_exponent"],
            cycle_fade_coefficient=probe["cycle_fade_coefficient"],
        )

        expected = probe["state_of_health"]
        self.assertEqual(len(result["soh_fraction_by_day"]), len(expected))
        worst = max(abs(a - b) for a, b in zip(result["soh_fraction_by_day"], expected))
        # REopt rounds the SOC series to three decimals before returning it.
        self.assertLess(worst, 2e-3)
        self.assertAlmostEqual(result["soh_fraction_by_day"][-1], expected[-1], delta=1e-3)
        self.assertIsNone(result["first_year_below_end_of_life"])
        self.assertIsNone(result["coefficients"]["cycle_life_efc"])


class RecurrencePropertyTests(TestCase):

    def _one_cycle_per_day(self, time_steps_per_hour):
        steps = 24 * time_steps_per_hour
        soc = ([1.0] * (steps // 2) + [0.0] * (steps // 2)) * 365
        # 12 h at 2 kW is 24 kWh a day at any resolution.
        discharge = ([0.0] * (steps // 2) + [2.0] * (steps // 2)) * 365
        return soc, discharge

    def test_same_daily_energy_gives_the_same_curve_at_any_resolution(self):
        hourly = self._one_cycle_per_day(1)
        quarter = self._one_cycle_per_day(4)

        a = battery_state_of_health(
            size_kwh=24.0, soc_series_fraction=hourly[0], discharge_series_kw=hourly[1],
            time_steps_per_hour=1, project_years=2)
        b = battery_state_of_health(
            size_kwh=24.0, soc_series_fraction=quarter[0], discharge_series_kw=quarter[1],
            time_steps_per_hour=4, project_years=2)

        for x, y in zip(a["soh_fraction_by_day"], b["soh_fraction_by_day"]):
            self.assertAlmostEqual(x, y, places=12)
        self.assertAlmostEqual(a["year_one_efc"], 365.0)

    def test_full_cycle_every_day_without_calendar_fade_hits_eol_on_day_8001(self):
        soc = [0.5] * 8760
        discharge = [1.0] * 8760      # 24 kWh a day on a 24 kWh battery: one EFC a day

        result = battery_state_of_health(
            size_kwh=24.0, soc_series_fraction=soc, discharge_series_kw=discharge,
            time_steps_per_hour=1, project_years=23, calendar_fade_coefficient=0.0)

        self.assertAlmostEqual(result["soh_fraction_by_day"][8000], 0.80, places=9)
        self.assertEqual(result["first_year_below_end_of_life"], 22)
        self.assertAlmostEqual(result["year_one_efc"], 365.0)
        self.assertAlmostEqual(result["years"][0]["efc_in_year"], 365.0)
        self.assertEqual(result["coefficients"]["cycle_life_efc"], 8000)
        self.assertAlmostEqual(result["coefficients"]["cycle_fade_coefficient"], 2.5e-5)

    def test_year_table_is_consistent(self):
        soc = [0.6] * 8760
        discharge = [0.5] * 8760

        result = battery_state_of_health(
            size_kwh=100.0, soc_series_fraction=soc, discharge_series_kw=discharge,
            time_steps_per_hour=1, project_years=3)

        years = result["years"]
        self.assertEqual([y["year"] for y in years], [1, 2, 3])
        start = 1.0
        for y in years:
            self.assertLessEqual(y["soh_end"], y["soh_average"])
            self.assertLessEqual(y["soh_average"], start)
            start = y["soh_end"]
        self.assertAlmostEqual(years[2]["efc_cumulative"], 3 * years[0]["efc_in_year"])
        self.assertEqual(result["soh_average_by_year"], [y["soh_average"] for y in years])
        self.assertAlmostEqual(
            years[0]["calendar_fade_kwh"] + years[0]["cycle_fade_kwh"],
            (1.0 - years[0]["soh_end"]) * 100.0, places=6)
        self.assertAlmostEqual(result["year_one_daily_average_soc_kwh"], 60.0)
        self.assertAlmostEqual(result["year_one_daily_discharge_kwh"], 12.0)

    def test_no_battery_returns_none(self):
        self.assertIsNone(battery_state_of_health(
            size_kwh=0, soc_series_fraction=[1.0] * 8760, discharge_series_kw=[0.0] * 8760,
            time_steps_per_hour=1, project_years=20))
        self.assertIsNone(battery_state_of_health(
            size_kwh=10, soc_series_fraction=[], discharge_series_kw=[],
            time_steps_per_hour=1, project_years=20))

    def test_a_short_series_is_refused(self):
        with self.assertRaises(ValueError):
            battery_state_of_health(
                size_kwh=10, soc_series_fraction=[0.5] * 24, discharge_series_kw=[1.0] * 24,
                time_steps_per_hour=1, project_years=1)


class AugmentationCostTests(TestCase):
    """Nominal cost of topping the capacity up, year by year, REopt's price path."""

    def test_zero_fade_costs_nothing(self):
        cost = augmentation_cost_by_year([1.0] * (2 * 365), 1000.0, 120.0, 0.03, 2)
        self.assertEqual(cost, [0.0, 0.0])

    def test_constant_daily_fade_is_priced_at_the_declining_installed_price(self):
        days = 2 * 365
        soh = [1.0 - 0.0001 * d for d in range(days)]   # 0.1 kWh a day on 1,000 kWh
        cost = augmentation_cost_by_year(soh, 1000.0, 120.0, 0.03, 2)
        # Day d (1-based, from 2) loses 0.1 kWh priced at 120 * 0.97 ** ((d - 1) / 365).
        expected_year_1 = sum(0.1 * 120.0 * 0.97 ** ((d - 1) / 365) for d in range(2, 366))
        expected_year_2 = sum(0.1 * 120.0 * 0.97 ** ((d - 1) / 365) for d in range(366, days + 1))
        self.assertAlmostEqual(cost[0], expected_year_1, places=6)
        self.assertAlmostEqual(cost[1], expected_year_2, places=6)
        self.assertLess(cost[1], cost[0])

    def test_series_length_follows_project_years(self):
        cost = augmentation_cost_by_year([1.0] * (3 * 365), 500.0, 150.0, 0.0, 3)
        self.assertEqual(len(cost), 3)
