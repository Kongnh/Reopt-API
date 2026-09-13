import csv
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from proforma_vietnam.case_builder import DEFAULT_EXCHANGE_RATE_VND_PER_USD, build_vietnam_case
from proforma_vietnam.defaults import FINANCIAL_DEFAULTS
from proforma_vietnam.run_dppa_negotiation_sweep import (
    cash_flow_overrides_from_assumptions,
)


STUB_PV_SERIES = [0.25] * 8760
STUB_POA_SERIES = [800.0] * 8760


class VietnamCaseBuilderTests(TestCase):

    def setUp(self):
        patcher = patch(
            "proforma_vietnam.case_builder.pvwatts_client.fetch_pv_series",
            return_value={
                "production_factor": list(STUB_PV_SERIES),
                "poa_wm2": list(STUB_POA_SERIES),
            },
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
                        "replacement": {"enabled": True, "cost_per_kw": 1000000,
                                        "cost_per_kwh": 2000000},
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
            "offtaker_discount_rate_fraction": 0.12,
            "owner_tax_rate_fraction": 0.20,
            "offtaker_tax_rate_fraction": 0.20,
            "elec_cost_escalation_rate_fraction": FINANCIAL_DEFAULTS["evn_energy_escalation_rate"],
            "om_cost_escalation_rate_fraction": FINANCIAL_DEFAULTS["om_escalation_rate"],
        })
        self.assertEqual(payload["PV"], {
            "max_kw": 1000.0,
            "installed_cost_per_kw": 12000000,
            "om_cost_per_kw": 150000,
            "degradation_fraction": 0.005,
            "production_factor_series": list(STUB_PV_SERIES),
            "federal_itc_fraction": 0.0,
            "macrs_option_years": 0,
            "macrs_bonus_fraction": 0.0,
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
            "inverter_replacement_year": 10,
            "battery_replacement_year": 10,
            "can_grid_charge": True,
            "total_itc_fraction": 0.0,
            "macrs_option_years": 0,
            "macrs_bonus_fraction": 0.0,
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
                    "storage": {"max_kw": 100, "max_kwh": 200, "installed_cost_per_kw": 80,
                                "installed_cost_per_kwh": 120,
                                "replacement": {"enabled": True, "year": 11}},
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

    def test_assumptions_carry_evn_rate_vintage_disclosure(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2026, "path": str(load_csv_path)},
                "tariff": {"year": 2026, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        assumptions = case["assumptions"]
        self.assertEqual(assumptions["rate_vintage_year"], 2025)
        self.assertIn("1279/QD-BCT", assumptions["rate_vintage_source"])
        self.assertNotIn("rate_vintage_year", case["payload"]["ElectricTariff"])
        self.assertNotIn("rate_vintage_source", case["payload"]["ElectricTariff"])

    def test_storage_soc_bounds_pass_through_to_payload(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV", "currency": "vnd"},
                "technologies": {
                    "storage": {
                        "max_kw": 500.0,
                        "max_kwh": 2000.0,
                        "soc_min_fraction": 0.0,
                        "soc_init_fraction": 0.5,
                    },
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        storage = case["payload"]["ElectricStorage"]
        self.assertEqual(storage["soc_min_fraction"], 0.0)
        self.assertEqual(storage["soc_init_fraction"], 0.5)

    def test_business_tariff_category_passes_through_to_payload_and_assumptions(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {
                    "year": 2025,
                    "voltage_level": "22-110kV",
                    "currency": "vnd",
                    "tariff_category": "business",
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        # 2025-01-01 00:00 is off-peak; kinh doanh >=22kV off-peak is 1,609
        # VND/kWh (Decision 1279/QD-BCT) vs 1,190 for manufacturing.
        self.assertEqual(case["payload"]["ElectricTariff"]["tou_energy_rates_per_kwh"][0], 1609)
        self.assertEqual(case["assumptions"]["tariff_category"], "business")

    def test_tariff_category_defaults_to_manufacturing_in_assumptions(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV", "currency": "vnd"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertEqual(case["payload"]["ElectricTariff"]["tou_energy_rates_per_kwh"][0], 1190)
        self.assertEqual(case["assumptions"]["tariff_category"], "manufacturing")

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

    def test_two_component_eligibility_true_for_large_load_at_eligible_voltage(self):
        # 500 kW constant load -> 4,380,000 kWh/year -> 365,000 kWh/month average,
        # well above the 200,000 kWh/month pilot threshold; 22-110kV is an
        # eligible voltage tier.
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

        assumptions = case["assumptions"]
        self.assertEqual(assumptions["two_component_avg_monthly_kwh"], 365000.0)
        self.assertTrue(assumptions["two_component_eligible"])

    def test_two_component_eligibility_false_for_small_load(self):
        # 100 kW constant load -> 876,000 kWh/year -> 73,000 kWh/month average,
        # below the 200,000 kWh/month pilot threshold.
        load_csv_path = _write_load_csv([100.0] * 8760)

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

        assumptions = case["assumptions"]
        self.assertEqual(assumptions["two_component_avg_monthly_kwh"], 73000.0)
        self.assertFalse(assumptions["two_component_eligible"])

    def test_two_component_eligibility_keys_absent_when_toggle_off(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        assumptions = case["assumptions"]
        self.assertNotIn("two_component_avg_monthly_kwh", assumptions)
        self.assertNotIn("two_component_eligible", assumptions)

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

    def test_default_exchange_rate_matches_versioned_defaults(self):
        # The default contract FX planning rate lives in vietnam_defaults.json's
        # financial block. Refreshed to the June 2026 market reference (26,300
        # VND/USD; 2026 avg ~26,244) — see vietnam_market_context.md.
        self.assertEqual(DEFAULT_EXCHANGE_RATE_VND_PER_USD, 26300)
        self.assertEqual(
            DEFAULT_EXCHANGE_RATE_VND_PER_USD,
            FINANCIAL_DEFAULTS["exchange_rate_vnd_per_usd"],
        )

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

        self.assertIn("8760", str(context.exception))

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
        # POA irradiance rides assumptions (report-only), not the REopt payload.
        self.assertEqual(
            case["assumptions"]["pv_poa_irradiance_series"],
            list(STUB_POA_SERIES),
        )
        self.assertNotIn("pv_poa_irradiance_series", case["payload"]["PV"])

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
        # No PVWatts fetch means no irradiance is available for the report.
        self.assertNotIn("pv_poa_irradiance_series", case["assumptions"])

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

    def test_esco_only_case_does_not_carry_dppa_regulatory_vintage_keys(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        assumptions = case["assumptions"]
        self.assertNotIn("dppa_regulatory_vintage_year", assumptions)
        self.assertNotIn("dppa_regulatory_source", assumptions)

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

    def test_grid_dppa_cfd_assumptions_carry_regulatory_vintage_disclosure(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2026, "path": str(load_csv_path)},
                "tariff": {"year": 2026, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "dppa": {
                    "type": "grid_dppa_cfd",
                    "cfd_strike_per_kwh_vnd": 1700.0,
                    "cfd_contract_volume_kwh_per_hour": 80.0,
                },
            }
        )

        assumptions = case["assumptions"]
        self.assertEqual(assumptions["dppa_regulatory_vintage_year"], 2025)
        self.assertIn("NLDC/EVN", assumptions["dppa_regulatory_source"])

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

    def test_physical_private_wire_populates_dppa_block_and_round_trips(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "dppa": {
                    "type": "physical_private_wire",
                    "ppa_price_vnd_per_kwh": 1850.0,
                    "ppa_price_escalation_rate": 0.02,
                },
            }
        )

        dppa = case["assumptions"]["dppa"]
        self.assertEqual(dppa["type"], "physical_private_wire")
        self.assertEqual(dppa["ppa_price_vnd_per_kwh"], 1850.0)
        self.assertEqual(dppa["ppa_price_escalation_rate"], 0.02)
        # Private wire has no ND57 loss-factor / fee regulatory vintage.
        self.assertNotIn("dppa_regulatory_vintage_year", case["assumptions"])

    def test_physical_private_wire_requires_ppa_price(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "dppa": {"type": "physical_private_wire"},
                }
            )

        self.assertIn("ppa_price_vnd_per_kwh", str(context.exception))

    def test_physical_private_wire_accepts_any_voltage_level(self):
        # Grid CfD requires ≥22kV; the private wire has no such restriction.
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "<6kv"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "dppa": {
                    "type": "physical_private_wire",
                    "ppa_price_vnd_per_kwh": 1850.0,
                },
            }
        )

        self.assertEqual(case["assumptions"]["dppa"]["type"], "physical_private_wire")

    def test_physical_private_wire_rejects_grid_cfd_fields(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "dppa": {
                        "type": "physical_private_wire",
                        "ppa_price_vnd_per_kwh": 1850.0,
                        "cfd_strike_per_kwh_vnd": 1700.0,
                    },
                }
            )

        self.assertIn("cfd_strike_per_kwh_vnd", str(context.exception))

    def test_physical_private_wire_forces_can_grid_charge_false(self):
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
                    "type": "physical_private_wire",
                    "ppa_price_vnd_per_kwh": 1850.0,
                },
            }
        )

        self.assertEqual(case["payload"]["ElectricStorage"]["can_grid_charge"], False)

    def test_physical_private_wire_carries_nested_surplus_block(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "dppa": {
                    "type": "physical_private_wire",
                    "ppa_price_vnd_per_kwh": 1850.0,
                    "surplus_export": {"enabled": True, "region": "south"},
                },
            }
        )

        surplus = case["assumptions"]["dppa"]["surplus_export"]
        self.assertEqual(surplus["enabled"], True)
        self.assertEqual(surplus["region"], "south")

    def test_physical_private_wire_rejects_unknown_nested_surplus_region(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError):
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "dppa": {
                        "type": "physical_private_wire",
                        "ppa_price_vnd_per_kwh": 1850.0,
                        "surplus_export": {"enabled": True, "region": "east"},
                    },
                }
            )

    def test_surplus_export_block_absent_when_not_configured(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertNotIn("surplus_export", case["assumptions"])

    def test_surplus_export_block_round_trips_into_assumptions(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "surplus_export": {
                    "enabled": True,
                    "region": "south",
                    "cap_fraction": 0.5,
                    "price_escalation_rate": 0.03,
                },
            }
        )

        surplus = case["assumptions"]["surplus_export"]
        self.assertEqual(surplus["enabled"], True)
        self.assertEqual(surplus["region"], "south")
        self.assertEqual(surplus["cap_fraction"], 0.5)
        self.assertEqual(surplus["price_escalation_rate"], 0.03)

    def test_surplus_export_rejects_unknown_keys(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "surplus_export": {"enabled": True, "region": "south", "bogus": 1},
                }
            )

        self.assertIn("bogus", str(context.exception))

    def test_surplus_export_rejects_unknown_region(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "surplus_export": {"enabled": True, "region": "east"},
                }
            )

        self.assertIn("region", str(context.exception).lower())

    def test_surplus_export_requires_region_or_price_when_enabled(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError):
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "surplus_export": {"enabled": True},
                }
            )

    def test_surplus_export_rejects_non_positive_price_and_cap(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        for bad in ({"enabled": True, "price_vnd_per_kwh": 0.0},
                    {"enabled": True, "region": "south", "cap_fraction": -0.1}):
            with self.assertRaises(ValueError):
                build_vietnam_case(
                    {
                        "site": {"latitude": 10.8231, "longitude": 106.6297},
                        "load_profile": {"year": 2025, "path": str(load_csv_path)},
                        "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                        "esco_contract": {"esco_energy_discount_fraction": 0.9},
                        "surplus_export": bad,
                    }
                )

    def test_surplus_export_disabled_block_skips_region_validation(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        # A disabled block is carried through untouched for round-tripping.
        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "surplus_export": {"enabled": False},
            }
        )

        self.assertEqual(case["assumptions"]["surplus_export"], {"enabled": False})

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

    def test_direct_ownership_block_selects_structure_and_round_trips(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "direct_ownership": {"enabled": True},
            }
        )

        self.assertEqual(case["assumptions"]["direct_ownership"], {"enabled": True})
        # The rebuild path maps the block into the cash-flow override the
        # esco_pro_forma adapter pops to select the structure.
        overrides = cash_flow_overrides_from_assumptions(case["assumptions"])
        self.assertEqual(overrides["direct_ownership"], {"enabled": True})

    def test_construction_financing_inputs_round_trip(self):
        # Construction + grace travel the same path as the other financing
        # scalars (debt fraction / rate / term): into assumptions, not the
        # REopt payload, and back out through the rebuild override mapping.
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "financial": {
                    "construction_months": 12,
                    "principal_grace_years": 2,
                },
            }
        )

        self.assertEqual(case["assumptions"]["construction_months"], 12)
        self.assertEqual(case["assumptions"]["principal_grace_years"], 2)
        self.assertNotIn("construction_months", case["payload"]["Financial"])
        overrides = cash_flow_overrides_from_assumptions(case["assumptions"])
        self.assertEqual(overrides["construction_months"], 12)
        self.assertEqual(overrides["principal_grace_years"], 2)

    def test_debt_currency_round_trips_like_the_other_financing_scalars(self):
        # debt_currency travels the same allowlisted path as debt fraction /
        # rate / term: into assumptions (never the REopt payload) and back out
        # through the rebuild override mapping.
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "financial": {"debt_currency": "USD"},
            }
        )

        self.assertEqual(case["assumptions"]["debt_currency"], "USD")
        self.assertNotIn("debt_currency", case["payload"]["Financial"])
        overrides = cash_flow_overrides_from_assumptions(case["assumptions"])
        self.assertEqual(overrides["debt_currency"], "USD")

    def test_target_min_dscr_round_trips_like_the_other_financing_scalars(self):
        # target_min_dscr travels the same allowlisted path as the other
        # financing scalars: into assumptions (never the REopt payload) and back
        # out through the rebuild override mapping.
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "financial": {"target_min_dscr": 1.3},
            }
        )

        self.assertEqual(case["assumptions"]["target_min_dscr"], 1.3)
        self.assertNotIn("target_min_dscr", case["payload"]["Financial"])
        overrides = cash_flow_overrides_from_assumptions(case["assumptions"])
        self.assertEqual(overrides["target_min_dscr"], 1.3)

    def test_contract_tenor_is_allowlisted_into_assumptions_not_the_payload(self):
        # Task 4e contract_years / contract_residual_value_usd travel the same
        # allowlisted path as the other financing scalars: into assumptions
        # (never the REopt payload) and back out through the rebuild override
        # mapping (cash_flow_overrides_from_assumptions), shared by the
        # offline rebuild_report.py path.
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "financial": {
                    "contract_years": 15,
                    "contract_residual_value_usd": 250000.0,
                },
            }
        )

        self.assertEqual(case["assumptions"]["contract_years"], 15)
        self.assertEqual(case["assumptions"]["contract_residual_value_usd"], 250000.0)
        self.assertNotIn("contract_years", case["payload"]["Financial"])
        self.assertNotIn("contract_residual_value_usd", case["payload"]["Financial"])
        overrides = cash_flow_overrides_from_assumptions(case["assumptions"])
        self.assertEqual(overrides["contract_years"], 15)
        self.assertEqual(overrides["contract_residual_value_usd"], 250000.0)

    def test_vat_inputs_round_trip_like_the_other_scalars(self):
        # Task 4f vat_rate_fraction / vat_refund_year travel the same allowlisted
        # path as the other financing scalars: into assumptions (never the REopt
        # payload) and back out through the rebuild override mapping
        # (cash_flow_overrides_from_assumptions), shared by rebuild_report.py.
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "financial": {
                    "vat_rate_fraction": 0.1,
                    "vat_refund_year": 2,
                },
            }
        )

        self.assertEqual(case["assumptions"]["vat_rate_fraction"], 0.1)
        self.assertEqual(case["assumptions"]["vat_refund_year"], 2)
        self.assertNotIn("vat_rate_fraction", case["payload"]["Financial"])
        self.assertNotIn("vat_refund_year", case["payload"]["Financial"])
        overrides = cash_flow_overrides_from_assumptions(case["assumptions"])
        self.assertEqual(overrides["vat_rate_fraction"], 0.1)
        self.assertEqual(overrides["vat_refund_year"], 2)

    def test_vat_inputs_absent_by_default_leaves_no_assumption_keys(self):
        # Default OFF: no VAT keys in the case financial input means neither key
        # appears in assumptions or the override mapping (byte-identical).
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertNotIn("vat_rate_fraction", case["assumptions"])
        self.assertNotIn("vat_refund_year", case["assumptions"])

    def test_contract_tenor_absent_by_default_leaves_no_assumption_keys(self):
        # Default OFF: no contract keys in the case financial input means neither
        # key appears in assumptions or the override mapping (byte-identical).
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertNotIn("contract_years", case["assumptions"])
        self.assertNotIn("contract_residual_value_usd", case["assumptions"])

    def test_battery_replacement_treatment_round_trips_like_the_other_scalars(self):
        # battery_replacement_treatment travels the same allowlisted path as the
        # other financing scalars: into assumptions (never the REopt payload) and
        # back out through the rebuild override mapping.
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "financial": {"battery_replacement_treatment": "expense"},
            }
        )

        self.assertEqual(case["assumptions"]["battery_replacement_treatment"], "expense")
        self.assertNotIn("battery_replacement_treatment", case["payload"]["Financial"])
        overrides = cash_flow_overrides_from_assumptions(case["assumptions"])
        self.assertEqual(overrides["battery_replacement_treatment"], "expense")

    def test_direct_ownership_carries_options_into_assumptions(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "direct_ownership": {
                    "enabled": True,
                    "assume_profitable_host": False,
                    "cit_regime": "re_producer",
                },
            }
        )

        block = case["assumptions"]["direct_ownership"]
        self.assertEqual(block["assume_profitable_host"], False)
        self.assertEqual(block["cit_regime"], "re_producer")

    def test_direct_ownership_rejects_preferential_cit_regime_with_default_host(self):
        # The immediate profitable-host shield convention (default on) is only
        # defined for the flat standard regime; a preferential/holiday regime
        # needs assume_profitable_host: false (5-yr FIFO carryforward).
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "direct_ownership": {"enabled": True, "cit_regime": "re_producer"},
                }
            )

        self.assertIn("assume_profitable_host", str(context.exception))

    def test_direct_ownership_does_not_require_esco_discount_fraction(self):
        # The factory captures the whole avoided bill, so the ESCO discount is
        # unused; a case may omit it and still build (defaulted to 0, never used).
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "direct_ownership": {"enabled": True},
            }
        )

        self.assertEqual(case["assumptions"]["esco_energy_discount_fraction"], 0.0)
        self.assertEqual(case["assumptions"]["direct_ownership"], {"enabled": True})

    def test_direct_ownership_rejects_dppa_block(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "direct_ownership": {"enabled": True},
                    "dppa": {
                        "type": "physical_private_wire",
                        "ppa_price_vnd_per_kwh": 1850.0,
                    },
                }
            )

        self.assertIn("dppa", str(context.exception).lower())

    def test_direct_ownership_rejects_unknown_keys(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        with self.assertRaises(ValueError) as context:
            build_vietnam_case(
                {
                    "site": {"latitude": 10.8231, "longitude": 106.6297},
                    "load_profile": {"year": 2025, "path": str(load_csv_path)},
                    "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                    "esco_contract": {"esco_energy_discount_fraction": 0.9},
                    "direct_ownership": {"enabled": True, "bogus": 1},
                }
            )

        self.assertIn("bogus", str(context.exception))

    def test_direct_ownership_disabled_block_is_not_selected(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
                "direct_ownership": {"enabled": False},
            }
        )

        self.assertNotIn("direct_ownership", case["assumptions"])

    def test_direct_ownership_leaves_can_grid_charge_as_configured(self):
        # Unlike the DPPA co-located BESS (forced off), the factory owns
        # everything, so a configured grid-charge flag is preserved.
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
                "direct_ownership": {"enabled": True},
            }
        )

        self.assertEqual(case["payload"]["ElectricStorage"]["can_grid_charge"], True)


class ReplacementSwitchInTheBuilderTests(TestCase):
    """technologies.storage.replacement is the one way to schedule a battery
    replacement; the policy default (2026-09-12) is none."""

    def _case(self, storage=None, financial=None):
        load_csv_path = _write_load_csv([500.0] * 8760)
        config = {
            "site": {"latitude": 10.8231, "longitude": 106.6297},
            "load_profile": {"year": 2025, "path": str(load_csv_path)},
            "tariff": {"year": 2025, "voltage_level": "22-110kV"},
            "esco_contract": {"esco_energy_discount_fraction": 0.9},
        }
        if storage is not None:
            config["technologies"] = {"storage": storage}
        if financial is not None:
            config["financial"] = financial
        return build_vietnam_case(config)

    def _storage(self, extra=None):
        storage = {"max_kw": 1000, "max_kwh": 4000,
                   "installed_cost_per_kw": 80, "installed_cost_per_kwh": 120}
        storage.update(extra or {})
        return storage

    def test_default_sends_a_zero_replacement_and_no_years(self):
        from proforma_vietnam.case_builder import apply_replacement_policy
        payload = {"max_kw": 100, "max_kwh": 200, "installed_cost_per_kw": 80,
                   "installed_cost_per_kwh": 120}

        record = apply_replacement_policy(self._storage(), payload)

        self.assertEqual(payload["replace_cost_per_kw"], 0.0)
        self.assertEqual(payload["replace_cost_per_kwh"], 0.0)
        self.assertNotIn("battery_replacement_year", payload)
        self.assertNotIn("inverter_replacement_year", payload)
        self.assertIs(record["bess_replacement_enabled"], False)
        self.assertNotIn("battery_replacement_year", record)
        self.assertEqual(record["bess_cycle_life_efc"], 8000)

    def test_enabled_block_prices_the_whole_system_in_one_year(self):
        from proforma_vietnam.case_builder import apply_replacement_policy
        payload = {"max_kw": 100, "max_kwh": 200, "installed_cost_per_kw": 80,
                   "installed_cost_per_kwh": 120}

        record = apply_replacement_policy(
            self._storage({"replacement": {"enabled": True}}), payload)

        self.assertEqual(payload["replace_cost_per_kw"], 80.0)
        self.assertEqual(payload["replace_cost_per_kwh"], 120.0)
        self.assertEqual(payload["battery_replacement_year"], 10)
        self.assertEqual(payload["inverter_replacement_year"], 10)
        self.assertIs(record["bess_replacement_enabled"], True)
        self.assertEqual(record["battery_replacement_year"], 10)
        self.assertEqual(record["bess_replace_cost_per_kw"], 80.0)
        self.assertEqual(record["bess_replace_cost_per_kwh"], 120.0)

    def test_enabled_block_accepts_year_fraction_and_absolute_costs(self):
        from proforma_vietnam.case_builder import apply_replacement_policy
        payload = {"installed_cost_per_kw": 80, "installed_cost_per_kwh": 120, "max_kwh": 1}
        apply_replacement_policy(
            self._storage({"replacement": {"enabled": True, "year": 8, "fraction_of_install": 0.5}}),
            payload)
        self.assertEqual((payload["replace_cost_per_kw"], payload["replace_cost_per_kwh"]), (40.0, 60.0))
        self.assertEqual(payload["battery_replacement_year"], 8)
        self.assertEqual(payload["inverter_replacement_year"], 8)

        payload = {"installed_cost_per_kw": 80, "installed_cost_per_kwh": 120, "max_kwh": 1}
        apply_replacement_policy(
            self._storage({"replacement": {"enabled": True, "cost_per_kw": 30, "cost_per_kwh": 45}}),
            payload)
        self.assertEqual((payload["replace_cost_per_kw"], payload["replace_cost_per_kwh"]), (30, 45))

    def test_fraction_and_absolute_costs_together_are_refused(self):
        from proforma_vietnam.case_builder import apply_replacement_policy
        with self.assertRaises(ValueError):
            apply_replacement_policy(
                self._storage({"replacement": {"enabled": True, "fraction_of_install": 1.0,
                                               "cost_per_kw": 30}}),
                {"installed_cost_per_kw": 80, "installed_cost_per_kwh": 120, "max_kwh": 1})

    def test_raw_reopt_replacement_keys_are_refused(self):
        from proforma_vietnam.case_builder import REPLACEMENT_RAW_KEYS, apply_replacement_policy
        self.assertEqual(len(REPLACEMENT_RAW_KEYS), 6)
        for key in REPLACEMENT_RAW_KEYS:
            with self.assertRaises(ValueError, msg=key):
                apply_replacement_policy(
                    self._storage({key: 1}), {"installed_cost_per_kw": 80, "max_kwh": 1})

    def test_cycle_life_override_is_recorded(self):
        from proforma_vietnam.case_builder import apply_replacement_policy
        record = apply_replacement_policy(
            self._storage({"cycle_life_efc": 6000}), {"installed_cost_per_kw": 80, "max_kwh": 1})
        self.assertEqual(record["bess_cycle_life_efc"], 6000)
        with self.assertRaises(ValueError):
            apply_replacement_policy(
                self._storage({"cycle_life_efc": 0}), {"installed_cost_per_kw": 80, "max_kwh": 1})

    def test_ageing_treatment_defaults_to_derate_and_is_recorded(self):
        from proforma_vietnam.case_builder import apply_replacement_policy
        record = apply_replacement_policy(self._storage(), {"installed_cost_per_kw": 80, "max_kwh": 1})
        self.assertEqual(record["battery_ageing_treatment"], "derate")
        self.assertEqual(record["bess_augmentation_price_declination_rate"], 0.03)
        record = apply_replacement_policy(
            self._storage({"ageing_treatment": "augment", "augmentation_price_declination_rate": 0.05}),
            {"installed_cost_per_kw": 80, "max_kwh": 1})
        self.assertEqual(record["battery_ageing_treatment"], "augment")
        self.assertEqual(record["bess_augmentation_price_declination_rate"], 0.05)
        with self.assertRaises(ValueError):
            apply_replacement_policy(
                self._storage({"ageing_treatment": "replace"}), {"installed_cost_per_kw": 80, "max_kwh": 1})
        with self.assertRaises(ValueError):
            apply_replacement_policy(
                self._storage({"augmentation_price_declination_rate": 1.5}),
                {"installed_cost_per_kw": 80, "max_kwh": 1})

    def test_built_case_records_the_ageing_treatment_in_assumptions(self):
        case = self._case(storage=self._storage({"ageing_treatment": "augment"}))
        self.assertEqual(case["assumptions"]["battery_ageing_treatment"], "augment")
        self.assertEqual(case["assumptions"]["bess_augmentation_price_declination_rate"], 0.03)
        pv_only = self._case(storage=None)
        self.assertNotIn("battery_ageing_treatment", pv_only["assumptions"])

    def test_no_storage_means_no_record(self):
        from proforma_vietnam.case_builder import apply_replacement_policy
        payload = {}
        self.assertEqual(apply_replacement_policy({}, payload), {})
        self.assertEqual(payload, {})

    def test_built_case_records_the_switch_in_assumptions(self):
        case = self._case(storage=self._storage())

        storage = case["payload"]["ElectricStorage"]
        self.assertEqual(storage["replace_cost_per_kw"], 0.0)
        self.assertEqual(storage["replace_cost_per_kwh"], 0.0)
        self.assertNotIn("battery_replacement_year", storage)
        self.assertNotIn("inverter_replacement_year", storage)
        assumptions = case["assumptions"]
        self.assertIs(assumptions["bess_replacement_enabled"], False)
        self.assertEqual(assumptions["bess_cycle_life_efc"], 8000)
        self.assertNotIn("battery_replacement_year", assumptions)
        self.assertNotIn("bess_replace_cost_per_kw", assumptions)
        self.assertEqual(assumptions["pv_inverter_replacement_year"], 11)
        self.assertEqual(assumptions["pv_inverter_replacement_fraction_of_pv_capex"], 0.10)

    def test_built_case_with_an_opt_in_records_the_event(self):
        case = self._case(storage=self._storage({"replacement": {"enabled": True, "year": 12}}))

        storage = case["payload"]["ElectricStorage"]
        self.assertEqual(storage["replace_cost_per_kwh"], 120.0)
        self.assertEqual(storage["battery_replacement_year"], 12)
        assumptions = case["assumptions"]
        self.assertIs(assumptions["bess_replacement_enabled"], True)
        self.assertEqual(assumptions["battery_replacement_year"], 12)
        self.assertEqual(assumptions["bess_replace_cost_per_kw"], 80.0)

    def test_a_raw_key_in_case_json_fails_the_build(self):
        with self.assertRaises(ValueError):
            self._case(storage=self._storage({"replace_cost_per_kwh": 60}))

    def test_analysis_years_defaults_to_the_policy_horizon(self):
        from proforma_vietnam.defaults import PROJECT_YEARS
        case = self._case()

        self.assertEqual(case["payload"]["Financial"]["analysis_years"], PROJECT_YEARS)
        self.assertEqual(case["payload"]["Financial"]["analysis_years"], 20)

    def test_an_explicit_analysis_years_still_wins(self):
        case = self._case(financial={"analysis_years": 25})

        self.assertEqual(case["payload"]["Financial"]["analysis_years"], 25)

    def test_no_storage_block_means_no_replacement_keys(self):
        case = self._case()

        self.assertNotIn("replace_cost_per_kw", case["payload"]["ElectricStorage"])
        self.assertNotIn("battery_replacement_year", case["payload"]["ElectricStorage"])
        self.assertNotIn("bess_replacement_enabled", case["assumptions"])
        self.assertNotIn("bess_cycle_life_efc", case["assumptions"])
        self.assertNotIn("battery_replacement_year", case["assumptions"])
        # The PV inverter policy is written regardless: it needs PV, not storage.
        self.assertEqual(case["assumptions"]["pv_inverter_replacement_year"], 11)


class ObjectiveAlignmentTests(TestCase):
    """The REopt objective prices what the pro forma books (2026-09-13).

    REopt.jl defaults the Financial block and the PV / storage incentives to
    US values: a 6.24 percent offtaker discount rate that also replaces the
    owner rate when third_party_ownership is false, 26 percent tax, 1.66
    percent electricity escalation, 2.5 percent O&M escalation, and a 30
    percent ITC with 5-year MACRS bonus depreciation on both technologies.
    None of that is booked by the pro forma, so the builder sends the pro
    forma's own values and zero incentives, as the Thailand builder does.
    """

    def setUp(self):
        patcher = patch(
            "proforma_vietnam.case_builder.pvwatts_client.fetch_pv_series",
            return_value={"production_factor": list(STUB_PV_SERIES), "poa_wm2": None},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _case(self, financial=None, tariff=None, pv=None, storage=None):
        load_csv_path = _write_load_csv([500.0] * 8760)
        tariff_block = {"year": 2025, "voltage_level": "22-110kV"}
        tariff_block.update(tariff or {})
        config = {
            "site": {"latitude": 10.8231, "longitude": 106.6297},
            "load_profile": {"year": 2025, "path": str(load_csv_path)},
            "tariff": tariff_block,
            "technologies": {
                "pv": {"max_kw": 1000.0} if pv is None else pv,
                "storage": {"max_kw": 500.0, "max_kwh": 2000.0} if storage is None else storage,
            },
            "esco_contract": {"esco_energy_discount_fraction": 0.9},
        }
        if financial is not None:
            config["financial"] = financial
        return build_vietnam_case(config)["payload"]

    def test_financial_block_defaults_to_the_pro_forma_values(self):
        payload = self._case()
        self.assertEqual(payload["Financial"], {
            "analysis_years": FINANCIAL_DEFAULTS["project_years"],
            "owner_discount_rate_fraction": 0.10,
            "offtaker_discount_rate_fraction": 0.10,
            "owner_tax_rate_fraction": 0.20,
            "offtaker_tax_rate_fraction": 0.20,
            "elec_cost_escalation_rate_fraction": FINANCIAL_DEFAULTS["evn_energy_escalation_rate"],
            "om_cost_escalation_rate_fraction": FINANCIAL_DEFAULTS["om_escalation_rate"],
        })

    def test_financial_block_follows_the_case(self):
        payload = self._case(
            financial={"owner_discount_rate_fraction": 0.12, "om_escalation_rate": 0.05},
            tariff={"evn_energy_escalation_rate": 0.06},
        )
        fin = payload["Financial"]
        self.assertEqual(fin["owner_discount_rate_fraction"], 0.12)
        self.assertEqual(fin["offtaker_discount_rate_fraction"], 0.12)
        self.assertEqual(fin["elec_cost_escalation_rate_fraction"], 0.06)
        self.assertEqual(fin["om_cost_escalation_rate_fraction"], 0.05)

    def test_incentives_are_zero_unless_the_case_says_otherwise(self):
        payload = self._case()
        for key in ("federal_itc_fraction", "macrs_bonus_fraction"):
            self.assertEqual(payload["PV"][key], 0.0)
        self.assertEqual(payload["PV"]["macrs_option_years"], 0)
        for key in ("total_itc_fraction", "macrs_bonus_fraction"):
            self.assertEqual(payload["ElectricStorage"][key], 0.0)
        self.assertEqual(payload["ElectricStorage"]["macrs_option_years"], 0)

        payload = self._case(
            pv={"max_kw": 1000.0, "federal_itc_fraction": 0.1},
            storage={"max_kw": 500.0, "max_kwh": 2000.0, "macrs_option_years": 7},
        )
        self.assertEqual(payload["PV"]["federal_itc_fraction"], 0.1)
        self.assertEqual(payload["ElectricStorage"]["macrs_option_years"], 7)

    def test_pv_only_case_still_zeroes_the_pv_incentives(self):
        payload = self._case(storage={})
        self.assertEqual(payload["PV"]["federal_itc_fraction"], 0.0)
        self.assertEqual(payload["ElectricStorage"], {"can_grid_charge": False})


def _write_load_csv(values):
    temp_dir = Path(tempfile.mkdtemp())
    path = temp_dir / "load.csv"
    with path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["load_kw"])
        for value in values:
            writer.writerow([value])
    return path


class ReadLoadCsvResolutionTests(TestCase):

    def setUp(self):
        import tempfile
        from pathlib import Path
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def _write_csv(self, name, count):
        path = self.tmp / name
        path.write_text(
            "load_kw\n" + "\n".join(str(float(i % 100)) for i in range(count)),
            encoding="utf-8",
        )
        return path

    def test_hourly_csv_reads_at_default_resolution(self):
        from proforma_vietnam.case_builder import _read_load_csv

        values = _read_load_csv(self._write_csv("hourly.csv", 8760))

        self.assertEqual(len(values), 8760)

    def test_fifteen_minute_csv_reads_at_four_steps_per_hour(self):
        from proforma_vietnam.case_builder import _read_load_csv

        values = _read_load_csv(
            self._write_csv("quarter.csv", 35040), time_steps_per_hour=4
        )

        self.assertEqual(len(values), 35040)

    def test_wrong_length_names_the_expected_count(self):
        from proforma_vietnam.case_builder import _read_load_csv

        with self.assertRaises(ValueError) as caught:
            _read_load_csv(self._write_csv("short.csv", 8760), time_steps_per_hour=4)

        self.assertIn("35040", str(caught.exception))

    def test_legacy_wrapper_still_enforces_8760(self):
        from proforma_vietnam.case_builder import _read_8760_load_csv

        with self.assertRaises(ValueError):
            _read_8760_load_csv(self._write_csv("quarter.csv", 35040))
