import json
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from proforma_thailand.case_builder import build_thailand_case

CALENDAR_MONTHS = [[2026, m] for m in range(1, 7)] + [[2025, m] for m in range(7, 13)]


def _case_config(tmp, load_csv, off_peak_json):
    return {
        "site": {"latitude": 15.209427, "longitude": 102.475687},
        "load_profile": {
            "path": str(load_csv),
            "all_off_peak_dates_path": str(off_peak_json),
            "calendar_year_months": CALENDAR_MONTHS,
        },
        "tariff": {"voltage_level": "22_33kv", "exchange_rate_thb_per_usd": 32.5},
        "technologies": {
            "pv": {"max_kw": 1685.0, "installed_cost_per_kw": 700.0},
            "storage": {"max_kw": 0, "max_kwh": 0},
        },
        "direct_ownership": {"enabled": True},
    }


class ThailandCaseBuilderTests(TestCase):

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)
        self.load_csv = self.tmp / "load.csv"
        self.load_csv.write_text(
            "load_kw\n" + "\n".join("500.0" for _ in range(35040)), encoding="utf-8"
        )
        self.off_peak = self.tmp / "off_peak.json"
        self.off_peak.write_text(json.dumps(["2026-01-04"]), encoding="utf-8")
        patcher = mock.patch(
            "proforma_thailand.case_builder.pvwatts_client."
            "fetch_pv_series",
            return_value={"production_factor": [0.5] * 8760, "poa_wm2": []},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _build(self):
        return build_thailand_case(
            _case_config(self.tmp, self.load_csv, self.off_peak)
        )

    def test_settings_request_15_minute_resolution(self):
        case = self._build()

        self.assertEqual(case["payload"]["Settings"]["time_steps_per_hour"], 4)

    def test_load_is_35040_long(self):
        case = self._build()

        self.assertEqual(
            len(case["payload"]["ElectricLoad"]["loads_kw"]), 35040
        )

    def test_tariff_uses_coincident_peak_not_monthly_demand(self):
        tariff = self._build()["payload"]["ElectricTariff"]

        self.assertEqual(len(tariff["coincident_peak_load_charge_per_kw"]), 12)
        self.assertEqual(len(tariff["coincident_peak_load_active_time_steps"]), 12)
        self.assertNotIn("monthly_demand_rates", tariff)

    def test_export_is_fully_disabled_with_curtailment_allowed(self):
        pv = self._build()["payload"]["PV"]

        self.assertFalse(pv["can_net_meter"])
        self.assertFalse(pv["can_wholesale"])
        self.assertFalse(pv["can_export_beyond_nem_limit"])
        self.assertTrue(pv["can_curtail"])

    def test_rate_vintage_is_routed_to_assumptions_not_the_payload(self):
        case = self._build()

        self.assertNotIn("rate_vintage_year", case["payload"]["ElectricTariff"])
        self.assertEqual(case["assumptions"]["rate_vintage_year"], 2025)

    def test_assumptions_record_the_country_and_currency(self):
        assumptions = self._build()["assumptions"]

        self.assertEqual(assumptions["country"], "Thailand")
        self.assertEqual(assumptions["local_currency_code"], "THB")

    def test_assumptions_list_the_active_placeholders(self):
        assumptions = self._build()["assumptions"]

        self.assertIn("placeholder_keys", assumptions)
        self.assertIn("debt_interest_rate", assumptions["placeholder_keys"])

    def test_direct_ownership_block_is_passed_through(self):
        assumptions = self._build()["assumptions"]

        self.assertEqual(assumptions["direct_ownership"], {"enabled": True})

    def test_service_charge_and_vat_ride_assumptions(self):
        assumptions = self._build()["assumptions"]

        self.assertAlmostEqual(
            assumptions["service_charge_per_month_thb"], 312.24, places=2
        )
        self.assertEqual(assumptions["vat_rate_fraction"], 0.07)
