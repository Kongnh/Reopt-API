import glob
import json
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.demand_charge import battery_demand_savings, demand_charge_from_series

ROOT = Path(__file__).resolve().parents[2]


def _results(case_dir):
    files = sorted(glob.glob(str(ROOT / case_dir / "results*.json")))
    assert files, case_dir
    return json.loads(Path(files[0]).read_text(encoding="utf-8"))


def _purchase(outputs):
    utility = outputs["ElectricUtility"]
    to_load = utility.get("electric_to_load_series_kw") or []
    to_storage = utility.get("electric_to_storage_series_kw") or [0.0] * len(to_load)
    return [a + b for a, b in zip(to_load, to_storage)]


class HandBuiltTests(TestCase):

    def test_coincident_peak_periods(self):
        tariff = {"coincident_peak_load_charge_per_kw": [10.0, 20.0],
                  "coincident_peak_load_active_time_steps": [[1, 2, 3], [4, 5]]}
        purchase = [5.0, 7.0, 6.0, 1.0, 3.0, 100.0]

        self.assertAlmostEqual(demand_charge_from_series(tariff, purchase), 10 * 7 + 20 * 3)

    def test_monthly_rates(self):
        tariff = {"monthly_demand_rates": [1.0] * 12}
        purchase = [1.0] * 8760
        purchase[24 * 31 + 5] = 50.0       # a February hour

        self.assertAlmostEqual(demand_charge_from_series(tariff, purchase), 11 * 1.0 + 50.0)

    def test_monthly_rates_at_quarter_hour_resolution(self):
        tariff = {"monthly_demand_rates": [1.0] * 12}
        purchase = [1.0] * 35040
        purchase[96 * 31 + 5] = 50.0       # a February quarter hour

        self.assertAlmostEqual(demand_charge_from_series(tariff, purchase, 4), 11 * 1.0 + 50.0)

    def test_unsupported_structures_return_none(self):
        self.assertIsNone(demand_charge_from_series({"urdb_label": "abc"}, [1.0] * 8760))
        self.assertIsNone(demand_charge_from_series(
            {"monthly_demand_rates": [1.0] * 12, "demand_lookback_percent": 0.5}, [1.0] * 8760))
        self.assertIsNone(demand_charge_from_series(
            {"tou_demand_rates": [1.0] * 8760}, [1.0] * 8760))

    def test_no_demand_structure_is_zero(self):
        self.assertEqual(demand_charge_from_series({"monthly_demand_rates": [0.0] * 12}, [1.0] * 8760), 0.0)
        self.assertEqual(demand_charge_from_series({}, [1.0] * 8760), 0.0)

    def test_battery_savings_is_counterfactual_minus_optimized(self):
        tariff = {"coincident_peak_load_charge_per_kw": [10.0],
                  "coincident_peak_load_active_time_steps": [[1, 2]]}
        load = [10.0, 10.0]
        pv = [4.0, 0.0]
        optimized = [2.0, 3.0]         # the battery shaved the second hour

        self.assertAlmostEqual(battery_demand_savings(tariff, load, pv, optimized), 10 * 10 - 10 * 3)
        self.assertEqual(battery_demand_savings(tariff, load, pv, [20.0, 20.0]), 0.0)
        self.assertIsNone(battery_demand_savings({"urdb_label": "x"}, load, pv, optimized))


class ReoptTieOutTests(TestCase):
    """The replica must reproduce REopt's own demand costs on the saved solves."""

    def test_thailand_coincident_peak_bau_and_optimized(self):
        results = _results("outputs/thailand_case/rofu_thailand/case_6")
        tariff = results["inputs"]["ElectricTariff"]
        outputs = results["outputs"]
        expected_bau = outputs["ElectricTariff"]["year_one_coincident_peak_cost_before_tax_bau"]
        expected_opt = outputs["ElectricTariff"]["year_one_coincident_peak_cost_before_tax"]
        load = outputs["ElectricLoad"]["load_series_kw"]

        self.assertAlmostEqual(demand_charge_from_series(tariff, load, 4), expected_bau, delta=0.5)
        self.assertAlmostEqual(
            demand_charge_from_series(tariff, _purchase(outputs), 4), expected_opt, delta=0.5)

    def test_vietnam_monthly_demand_bau_and_optimized(self):
        results = _results("outputs/vietnam_case/factory_a/case_3")
        tariff = results["inputs"]["ElectricTariff"]
        outputs = results["outputs"]
        expected_bau = outputs["ElectricTariff"]["year_one_demand_cost_before_tax_bau"]
        expected_opt = outputs["ElectricTariff"]["year_one_demand_cost_before_tax"]
        load = outputs["ElectricLoad"]["load_series_kw"]

        self.assertAlmostEqual(demand_charge_from_series(tariff, load, 1), expected_bau, delta=0.5)
        self.assertAlmostEqual(
            demand_charge_from_series(tariff, _purchase(outputs), 1), expected_opt, delta=0.5)
