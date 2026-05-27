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

    def test_maps_allowlisted_financial_and_cost_assumptions(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "case": {"name": "Factory A"},
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "financial": {
                    "analysis_years": 20,
                    "owner_discount_rate_fraction": 0.12,
                    "debt_fraction": 0.65,
                    "debt_interest_rate_fraction": 0.09,
                    "debt_term_years": 12,
                    "annual_om_usd": 4000,
                    "unsupported_financial_key": 999,
                },
                "technologies": {
                    "pv": {
                        "max_kw": 1000.0,
                        "installed_cost_per_kw": 12000000,
                        "om_cost_per_kw": 150000,
                        "degradation_fraction": 0.005,
                        "unsupported_pv_key": 1,
                    },
                    "storage": {
                        "max_kw": 500.0,
                        "max_kwh": 2000.0,
                        "installed_cost_per_kw": 3000000,
                        "installed_cost_per_kwh": 4500000,
                        "installed_cost_constant": 250000000,
                        "om_cost_fraction_of_installed_cost": 0.02,
                        "replace_cost_per_kw": 1000000,
                        "replace_cost_per_kwh": 2000000,
                        "replace_cost_constant": 50000000,
                        "inverter_replacement_year": 10,
                        "battery_replacement_year": 10,
                        "cost_constant_replacement_year": 10,
                        "unsupported_storage_key": 1,
                    },
                },
                "esco_contract": {
                    "esco_energy_discount_fraction": 0.9,
                    "demand_savings_esco_share": 0.75,
                    "grid_charging_enabled": True,
                    "unsupported_esco_key": 1,
                },
            }
        )

        payload = case["payload"]
        assumptions = case["assumptions"]

        self.assertEqual(payload["Financial"], {
            "analysis_years": 20,
            "owner_discount_rate_fraction": 0.12,
        })
        self.assertEqual(payload["PV"], {
            "max_kw": 1000.0,
            "installed_cost_per_kw": 12000000,
            "om_cost_per_kw": 150000,
            "degradation_fraction": 0.005,
        })
        self.assertEqual(payload["ElectricStorage"], {
            "max_kw": 500.0,
            "max_kwh": 2000.0,
            "installed_cost_per_kw": 3000000,
            "installed_cost_per_kwh": 4500000,
            "installed_cost_constant": 250000000,
            "om_cost_fraction_of_installed_cost": 0.02,
            "replace_cost_per_kw": 1000000,
            "replace_cost_per_kwh": 2000000,
            "replace_cost_constant": 50000000,
            "inverter_replacement_year": 10,
            "battery_replacement_year": 10,
            "cost_constant_replacement_year": 10,
            "can_grid_charge": True,
        })
        self.assertEqual(assumptions["owner_discount_rate_fraction"], 0.12)
        self.assertEqual(assumptions["debt_fraction"], 0.65)
        self.assertEqual(assumptions["debt_interest_rate_fraction"], 0.09)
        self.assertEqual(assumptions["debt_term_years"], 12)
        self.assertEqual(assumptions["annual_om_usd"], 4000)
        self.assertEqual(assumptions["demand_savings_esco_share"], 0.75)
        self.assertEqual(assumptions["grid_charging_enabled"], True)
        self.assertNotIn("unsupported_financial_key", assumptions)
        self.assertNotIn("unsupported_esco_key", assumptions)

    def test_builds_two_component_pilot_tariff_when_enabled(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {
                    "year": 2025,
                    "voltage_level": "22-110kV",
                    "two_component_pilot_enabled": True,
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertEqual(len(case["payload"]["ElectricTariff"]["monthly_demand_rates"]), 12)

    def test_keeps_usd_report_assumptions_in_usd_with_exchange_rate(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {
                    "year": 2025,
                    "voltage_level": "22-110kV",
                    "currency": "usd",
                    "exchange_rate_vnd_per_usd": 25000,
                    "evn_energy_escalation_rate": 0.04,
                    "evn_capacity_escalation_rate": 0.03,
                },
                "financial": {
                    "annual_om_usd": 4000,
                },
                "technologies": {
                    "pv": {
                        "size_kw": 1000,
                        "installed_cost_per_kw": 480,
                    },
                    "storage": {
                        "size_kw": 500,
                        "size_kwh": 2000,
                        "installed_cost_per_kw": 120,
                        "installed_cost_per_kwh": 180,
                        "installed_cost_constant": 1000,
                    },
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        payload = case["payload"]
        assumptions = case["assumptions"]

        self.assertEqual(payload["PV"]["installed_cost_per_kw"], 480)
        self.assertEqual(payload["ElectricStorage"]["installed_cost_per_kwh"], 180)
        self.assertEqual(assumptions["exchange_rate_vnd_per_usd"], 25000)
        self.assertEqual(assumptions["annual_om_usd"], 4000)
        self.assertEqual(assumptions["pv_capex_usd"], 480000)
        self.assertEqual(assumptions["bess_capex_usd"], 421000)
        self.assertEqual(assumptions["evn_energy_escalation_rate"], 0.04)
        self.assertEqual(assumptions["evn_capacity_escalation_rate"], 0.03)

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
