import csv
import tempfile
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.case_builder import build_vietnam_case


class VietnamCaseBuilderTests(TestCase):

    def test_builds_reopt_payload_from_8760_load_csv_and_defaults(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "case": {"name": "Factory A"},
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {
                    "year": 2025,
                    "voltage_level": "22-110kV",
                    "currency": "usd",
                    "exchange_rate_vnd_per_usd": 25000,
                    "tou_schedule": "current",
                },
                "technologies": {
                    "pv": {"max_kw": 1000.0},
                    "storage": {"max_kw": 500.0, "max_kwh": 2000.0},
                },
                "financial": {"analysis_years": 25},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        payload = case["payload"]
        assumptions = case["assumptions"]

        self.assertEqual(payload["Meta"]["description"], "Factory A")
        self.assertEqual(payload["Site"]["latitude"], 10.8231)
        self.assertEqual(payload["ElectricLoad"]["year"], 2025)
        self.assertEqual(len(payload["ElectricLoad"]["loads_kw"]), 8760)
        self.assertEqual(len(payload["ElectricTariff"]["tou_energy_rates_per_kwh"]), 8760)
        self.assertEqual(payload["PV"]["max_kw"], 1000.0)
        self.assertEqual(payload["ElectricStorage"]["can_grid_charge"], False)
        self.assertEqual(payload["Financial"]["analysis_years"], 25)
        self.assertEqual(assumptions["country"], "Vietnam")
        self.assertEqual(assumptions["esco_energy_discount_fraction"], 0.9)
        self.assertEqual(assumptions["demand_savings_esco_share"], 0.8)

    def test_rejects_load_csv_that_is_not_8760_rows(self):
        load_csv_path = _write_load_csv([500.0] * 24)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                }
            )

        self.assertIn("8760 hourly load values", str(context.exception))

    def test_requires_esco_energy_discount_for_report_download(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                }
            )

        self.assertIn("esco_energy_discount_fraction", str(context.exception))


def _write_load_csv(values):
    temp_dir = Path(tempfile.mkdtemp())
    path = temp_dir / "load.csv"
    with path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["load_kw"])
        for value in values:
            writer.writerow([value])
    return path
