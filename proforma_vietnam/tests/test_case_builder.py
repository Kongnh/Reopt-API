import csv
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from proforma_vietnam.case_builder import build_vietnam_case


STUB_PV_SERIES = [0.25] * 8760


class VietnamCaseBuilderTests(TestCase):

    def setUp(self):
        patcher = patch(
            "proforma_vietnam.case_builder.pvwatts_client.fetch_production_factor_series",
            return_value=list(STUB_PV_SERIES),
        )
        self.fetch_pv = patcher.start()
        self.addCleanup(patcher.stop)

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
            "production_factor_series": list(STUB_PV_SERIES),
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

    def test_pv_depreciation_and_battery_replacement_pass_through_assumptions(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "financial": {"pv_depreciation_years": 15},
                "technologies": {
                    "storage": {"battery_replacement_year": 11},
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertEqual(case["assumptions"]["pv_depreciation_years"], 15)
        self.assertEqual(case["assumptions"]["battery_replacement_year"], 11)
        self.assertEqual(
            case["payload"]["ElectricStorage"]["battery_replacement_year"], 11
        )

    def test_om_escalation_and_pv_degradation_pass_through_assumptions(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "financial": {
                    "om_escalation_rate": 0.03,
                    "pv_degradation_rate": 0.006,
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertEqual(case["assumptions"]["om_escalation_rate"], 0.03)
        self.assertEqual(case["assumptions"]["pv_degradation_rate"], 0.006)

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

    def test_bess_capex_omitted_when_storage_size_is_optimizer_chosen(self):
        # Regression: when storage sizes are not preset (optimizer chooses),
        # case_builder previously wrote bess_capex_usd=0 because installed_cost_constant
        # was present (even at 0). That zero then overrode the REopt-derived capex
        # downstream, deflating total project cost by the true BESS capex.
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
                },
                "technologies": {
                    "pv": {"max_kw": 5000.0, "installed_cost_per_kw": 480},
                    "storage": {
                        # No size_kw / size_kwh — optimizer chooses
                        "max_kw": 5000.0,
                        "max_kwh": 20000.0,
                        "installed_cost_per_kw": 80,
                        "installed_cost_per_kwh": 120,
                        "installed_cost_constant": 0,
                    },
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        assumptions = case["assumptions"]
        # Neither size preset → no zero override should be written. esco_pro_forma
        # will derive bess_capex from REopt outputs at report time.
        self.assertNotIn("bess_capex_usd", assumptions)

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

    def test_auto_fetches_pv_production_series_when_missing(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "technologies": {"pv": {"max_kw": 1000.0}},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.fetch_pv.assert_called_once_with(
            latitude=10.8231,
            longitude=106.6297,
            overrides=None,
        )
        self.assertEqual(
            case["payload"]["PV"]["production_factor_series"],
            list(STUB_PV_SERIES),
        )

    def test_passes_pvwatts_overrides_and_drops_pvwatts_key_from_payload(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "technologies": {
                    "pv": {
                        "max_kw": 1000.0,
                        "pvwatts": {"tilt": 15, "azimuth": 170, "losses": 12},
                    },
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.fetch_pv.assert_called_once_with(
            latitude=10.8231,
            longitude=106.6297,
            overrides={"tilt": 15, "azimuth": 170, "losses": 12},
        )
        self.assertNotIn("pvwatts", case["payload"]["PV"])

    def test_skips_pv_fetch_when_production_factor_series_provided(self):
        load_csv_path = _write_load_csv([500.0] * 8760)
        user_series = [0.5] * 8760

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "technologies": {
                    "pv": {
                        "max_kw": 1000.0,
                        "production_factor_series": user_series,
                    },
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.fetch_pv.assert_not_called()
        self.assertEqual(
            case["payload"]["PV"]["production_factor_series"],
            user_series,
        )

    def test_dppa_block_is_omitted_when_dppa_type_is_none_or_missing(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertNotIn("dppa", case["assumptions"])

    def test_grid_dppa_cfd_populates_assumptions_dppa_block_with_defaults_and_fmp_series(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "dppa": {
                    "type": "grid_dppa_cfd",
                    "cfd_strike_per_kwh_vnd": 1700.0,
                    "cfd_contract_volume_kwh_per_hour": 80.0,
                },
            }
        )

        dppa = case["assumptions"]["dppa"]
        self.assertEqual(dppa["type"], "grid_dppa_cfd")
        self.assertEqual(dppa["cfd_strike_per_kwh_vnd"], 1700.0)
        self.assertEqual(dppa["cfd_contract_volume_kwh_per_hour"], 80.0)
        self.assertAlmostEqual(dppa["distribution_loss_factor_kpp"], 1.027263)
        self.assertAlmostEqual(dppa["transmission_loss_factor_k"], 1.026)
        self.assertAlmostEqual(dppa["allocation_fraction_delta"], 1.0)
        self.assertEqual(dppa["c_dppa_service_fee_vnd_per_kwh"], 360.0)
        self.assertEqual(dppa["c_cl_settlement_adder_vnd_per_kwh"], 163.3)
        self.assertEqual(dppa["cfd_strike_escalation_rate"], 0.04)
        self.assertEqual(len(dppa["fmp_series_vnd_per_kwh"]), 8760)

    def test_grid_dppa_cfd_preserves_explicit_strike_escalation_override(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "dppa": {
                    "type": "grid_dppa_cfd",
                    "cfd_strike_per_kwh_vnd": 1700.0,
                    "cfd_strike_escalation_rate": 0.02,
                    "cfd_contract_volume_kwh_per_hour": 80.0,
                },
            }
        )

        self.assertEqual(case["assumptions"]["dppa"]["cfd_strike_escalation_rate"], 0.02)

    def test_grid_dppa_cfd_forces_can_grid_charge_false(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {
                    "esco_energy_discount_fraction": 0.9,
                    "grid_charging_enabled": True,
                },
                "technologies": {
                    "storage": {"max_kw": 500.0, "max_kwh": 2000.0, "can_grid_charge": True},
                },
                "dppa": {
                    "type": "grid_dppa_cfd",
                    "cfd_strike_per_kwh_vnd": 1700.0,
                    "cfd_contract_volume_kwh_per_hour": 80.0,
                },
            }
        )

        self.assertEqual(case["payload"]["ElectricStorage"]["can_grid_charge"], False)

    def test_grid_dppa_cfd_rejects_ineligible_voltage_level(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "6-22kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "dppa": {
                        "type": "grid_dppa_cfd",
                        "cfd_strike_per_kwh_vnd": 1700.0,
                        "cfd_contract_volume_kwh_per_hour": 80.0,
                    },
                }
            )

        self.assertIn("grid_dppa_cfd", str(context.exception))
        self.assertIn("voltage", str(context.exception).lower())

    def test_grid_dppa_cfd_requires_cfd_strike_and_volume(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "dppa": {"type": "grid_dppa_cfd"},
                }
            )

        self.assertIn("cfd_strike_per_kwh_vnd", str(context.exception))

    def test_rejects_unknown_dppa_type(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "dppa": {"type": "private_wire"},
                }
            )

        self.assertIn("dppa.type", str(context.exception))

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
