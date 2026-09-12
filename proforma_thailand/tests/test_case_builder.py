import json
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from proforma_thailand.case_builder import build_thailand_case
from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of
from proforma_vietnam import pvwatts_client

CALENDAR_MONTHS = [[2026, m] for m in range(1, 7)] + [[2025, m] for m in range(7, 13)]

# Real RTS case data, the same files proforma_thailand/cases/rts/case.json points
# at. Used as the default load/off-peak source so _case_config() is callable with
# no args; existing callers still pass their own tmp-dir fixtures positionally.
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DEFAULT_LOAD_CSV = _DATA_DIR / "rofu_load_15min.csv"
_DEFAULT_OFF_PEAK = _DATA_DIR / "rofu_all_off_peak_dates.json"


def _case_config(tmp=None, load_csv=None, off_peak_json=None, storage=None):
    return {
        "site": {"latitude": 15.209427, "longitude": 102.475687},
        "load_profile": {
            "path": str(load_csv or _DEFAULT_LOAD_CSV),
            "all_off_peak_dates_path": str(off_peak_json or _DEFAULT_OFF_PEAK),
            "calendar_year_months": CALENDAR_MONTHS,
        },
        "tariff": {"voltage_level": "22_33kv", "exchange_rate_thb_per_usd": 32.5},
        "technologies": {
            "pv": {"max_kw": 1685.0, "installed_cost_per_kw": 700.0},
            "storage": storage or {"max_kw": 0, "max_kwh": 0},
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

    def test_electric_load_declares_the_calendar_year(self):
        # REopt errors with "Must provide ElectricLoad.year when using loads_kw"
        # if this is absent, and the year must match the synthetic calendar.
        load = self._build()["payload"]["ElectricLoad"]

        self.assertEqual(load["year"], 2026)

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

    def test_a_zero_pv_case_omits_the_pv_block_entirely(self):
        # validators.py:226 skips production_factor_series resampling when
        # max_kw is 0, so declaring PV here ships an unresampled 8760 series
        # into a 35040 model and the solver dies on a DimensionMismatch.
        config = _case_config(self.tmp, self.load_csv, self.off_peak)
        config["technologies"]["pv"] = {"max_kw": 0}

        payload = build_thailand_case(config)["payload"]

        self.assertNotIn("PV", payload)

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

        # Was previously asserted equal to sorted(placeholder_keys()) - but
        # case_builder.py sets this key by calling that exact function, so
        # the comparison was tautological (true regardless of what the
        # function returns) and verified nothing. Checking presence and
        # shape is what is actually left to check without re-pinning a
        # literal key list, which breaks on every re-benchmark.
        self.assertIn("placeholder_keys", assumptions)
        self.assertIsInstance(assumptions["placeholder_keys"], list)

    def test_direct_ownership_block_is_passed_through(self):
        assumptions = self._build()["assumptions"]

        self.assertEqual(assumptions["direct_ownership"], {"enabled": True})

    def test_service_charge_and_vat_ride_assumptions(self):
        assumptions = self._build()["assumptions"]

        self.assertAlmostEqual(
            assumptions["service_charge_per_month_thb"], 312.24, places=2
        )
        self.assertEqual(assumptions["vat_rate_fraction"], 0.07)

    def test_storage_does_not_inherit_the_reopt_fixed_cost_default(self):
        config = _case_config(self.tmp, self.load_csv, self.off_peak)
        config["technologies"]["storage"] = {"max_kw": 500, "max_kwh": 1000}

        storage = build_thailand_case(config)["payload"]["ElectricStorage"]

        self.assertEqual(storage["installed_cost_constant"], 0.0)

    def test_financial_sends_thai_rates_not_reopt_defaults(self):
        financial = self._build()["payload"]["Financial"]

        self.assertEqual(financial["offtaker_tax_rate_fraction"], 0.20)
        self.assertEqual(financial["owner_tax_rate_fraction"], 0.20)
        self.assertEqual(financial["elec_cost_escalation_rate_fraction"], 0.03)
        self.assertEqual(
            financial["offtaker_discount_rate_fraction"],
            financial["owner_discount_rate_fraction"],
        )


class PayloadDefaultInheritanceTests(TestCase):
    """Fields REopt would otherwise silently default to non-Thai values."""

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
            "proforma_thailand.case_builder.pvwatts_client.fetch_pv_series",
            return_value={"production_factor": [0.5] * 8760, "poa_wm2": []},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _storage_case(self):
        config = _case_config(self.tmp, self.load_csv, self.off_peak)
        config["technologies"]["storage"] = {"max_kw": 500, "max_kwh": 1000}
        return config

    def test_default_storage_case_sends_zero_replacement_and_records_the_switch(self):
        # Policy 2026-09-12: no scheduled replacement. REopt defaults every
        # replace_cost to 0.0 anyway; sending it explicitly makes the payload
        # read as a decision rather than an omission.
        built = build_thailand_case(self._storage_case())
        storage = built["payload"]["ElectricStorage"]

        self.assertEqual(storage["replace_cost_per_kw"], 0.0)
        self.assertEqual(storage["replace_cost_per_kwh"], 0.0)
        self.assertNotIn("battery_replacement_year", storage)
        self.assertNotIn("inverter_replacement_year", storage)
        a = built["assumptions"]
        self.assertIs(a["bess_replacement_enabled"], False)
        self.assertEqual(a["bess_cycle_life_efc"], 8000)
        self.assertNotIn("battery_replacement_year", a)
        self.assertNotIn("bess_replace_cost_per_kw", a)
        self.assertEqual(a["pv_inverter_replacement_year"], 11)
        self.assertEqual(a["pv_inverter_replacement_fraction_of_pv_capex"], 0.10)
        self.assertNotIn("inverter_replacement_year", a)
        self.assertNotIn("inverter_replacement_cost_usd", a)

    def test_opt_in_replacement_prices_from_the_thai_install_defaults(self):
        config = self._storage_case()
        config["technologies"]["storage"]["replacement"] = {"enabled": True}

        built = build_thailand_case(config)
        storage = built["payload"]["ElectricStorage"]

        self.assertEqual(storage["replace_cost_per_kw"], 100.0)
        self.assertEqual(storage["replace_cost_per_kwh"], 150.0)
        self.assertEqual(storage["inverter_replacement_year"], 10)
        self.assertEqual(storage["battery_replacement_year"], 10)
        a = built["assumptions"]
        self.assertIs(a["bess_replacement_enabled"], True)
        self.assertEqual(a["battery_replacement_year"], 10)
        self.assertEqual(a["bess_replace_cost_per_kw"], 100.0)
        self.assertEqual(a["bess_replace_cost_per_kwh"], 150.0)

    def test_a_price_sensitivity_keeps_the_opt_in_rule(self):
        config = self._storage_case()
        config["technologies"]["storage"]["installed_cost_per_kwh"] = 200.0
        config["technologies"]["storage"]["replacement"] = {"enabled": True}

        storage = build_thailand_case(config)["payload"]["ElectricStorage"]

        self.assertEqual(storage["replace_cost_per_kwh"], 200.0)

    def test_raw_replacement_keys_are_refused(self):
        config = self._storage_case()
        config["technologies"]["storage"]["replace_cost_per_kw"] = 70.0

        with self.assertRaises(ValueError):
            build_thailand_case(config)

    def test_a_case_without_storage_records_no_battery_switch(self):
        a = build_thailand_case(
            _case_config(self.tmp, self.load_csv, self.off_peak)
        )["assumptions"]

        self.assertNotIn("battery_replacement_year", a)
        self.assertNotIn("bess_replace_cost_per_kw", a)
        self.assertNotIn("bess_replacement_enabled", a)
        self.assertNotIn("bess_cycle_life_efc", a)
        self.assertEqual(a["pv_inverter_replacement_year"], 11)

    def test_pv_om_cost_comes_from_the_thailand_defaults(self):
        pv = build_thailand_case(
            _case_config(self.tmp, self.load_csv, self.off_peak)
        )["payload"]["PV"]

        self.assertEqual(
            pv["om_cost_per_kw"], value_of(FINANCIAL_DEFAULTS, "annual_om_per_kw")
        )


class PvOmCostRoundingTests(TestCase):
    """Important 5 / Ruling 22: REopt.jl rounds PV cost parameters to whole
    dollars before it solves, so the SENT om_cost_per_kw is not what a
    committed run actually applies - see
    test_pv_om_cost_comes_from_the_thailand_defaults above, which only checks
    the SENT payload value and would stay green even if the rounding
    drifted. This reads what REopt RETURNED on a real, committed run
    (case_1's results.json on this branch), not a synthetic fixture, so it
    pins the solver's actual rounding behaviour rather than an assumption
    about it.

    The fixture has since been re-solved (2026-09-09) under the client's
    confirmed defaults, so `sent` is read live off FINANCIAL_DEFAULTS again
    rather than pinned to a historical literal. That is the stronger form:
    it fails if the committed results.json ever drifts from the defaults it
    was supposedly solved under, which a hardcoded pin cannot detect.
    """

    RESULTS_PATH = Path(
        "outputs/thailand_case/rofu_thailand/case_1/results.json"
    )

    @property
    def SENT_OM_PER_KW_AT_SOLVE_TIME(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of
        return value_of(FINANCIAL_DEFAULTS, "annual_om_per_kw")

    def setUp(self):
        self.results = json.loads(self.RESULTS_PATH.read_text(encoding="utf-8"))

    def _pv_outputs(self):
        pv = self.results["outputs"]["PV"]
        return pv[0] if isinstance(pv, list) else pv

    def test_reopt_rounds_the_sent_om_cost_up_to_a_whole_dollar(self):
        sent = self.SENT_OM_PER_KW_AT_SOLVE_TIME
        returned = self._pv_outputs()["om_cost_per_kw"]

        self.assertEqual(sent, 7.5)
        self.assertEqual(returned, 8.0)
        self.assertNotEqual(returned, sent)

    def test_year_one_om_cost_is_billed_at_the_rounded_rate_not_the_sent_rate(self):
        pv_size_kw = self._pv_outputs()["size_kw"]
        year_one_om = self.results["outputs"]["Financial"][
            "year_one_om_costs_before_tax"
        ]

        self.assertAlmostEqual(year_one_om, pv_size_kw * 8.0)
        self.assertNotAlmostEqual(
            year_one_om, pv_size_kw * self.SENT_OM_PER_KW_AT_SOLVE_TIME
        )


class UsIncentivesAreDisabledTests(TestCase):
    """REopt.jl defaults a 30% ITC and 5-year MACRS ON. Thailand has neither,
    and they cut the capital cost the optimizer sizes against."""

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
            "proforma_thailand.case_builder.pvwatts_client.fetch_pv_series",
            return_value={"production_factor": [0.5] * 8760, "poa_wm2": []},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_pv_carries_no_itc_or_macrs(self):
        pv = build_thailand_case(
            _case_config(self.tmp, self.load_csv, self.off_peak)
        )["payload"]["PV"]

        self.assertEqual(pv["federal_itc_fraction"], 0.0)
        self.assertEqual(pv["macrs_option_years"], 0)
        self.assertEqual(pv["macrs_bonus_fraction"], 0.0)

    def test_storage_carries_no_itc_or_macrs(self):
        config = _case_config(self.tmp, self.load_csv, self.off_peak)
        config["technologies"]["storage"] = {"max_kw": 500, "max_kwh": 1000}

        storage = build_thailand_case(config)["payload"]["ElectricStorage"]

        self.assertEqual(storage["total_itc_fraction"], 0.0)
        self.assertEqual(storage["macrs_option_years"], 0)
        self.assertEqual(storage["macrs_bonus_fraction"], 0.0)


class PayloadDefaultsTests(TestCase):
    """Fields REopt would otherwise silently default to US-centric values:
    a zero-duration battery, 2.5 percent storage O&M, and the Vietnam-tuned
    PVWatts tilt of 10 degrees."""

    def setUp(self):
        # test_storage_* below do not care about the PV series, but
        # build_thailand_case always calls fetch_pv_series, and the default
        # tilt override (15) does not match anything already cached on disk,
        # so an unmocked call would hit the live PVWatts API.
        patcher = mock.patch.object(
            pvwatts_client,
            "fetch_pv_series",
            return_value={"production_factor": [0.5] * 8760, "poa_wm2": []},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_storage_declares_a_minimum_duration(self):
        case = build_thailand_case(_case_config(storage={"max_kw": 500, "max_kwh": 1000}))
        self.assertEqual(
            case["payload"]["ElectricStorage"]["min_duration_hours"], 1.5
        )

    def test_storage_om_fraction_is_explicit(self):
        case = build_thailand_case(_case_config(storage={"max_kw": 500, "max_kwh": 1000}))
        # assertIn alone would also pass if the key held REopt's own 0.025
        # default by coincidence, so pin the actual Thailand value too.
        self.assertIn(
            "om_cost_fraction_of_installed_cost",
            case["payload"]["ElectricStorage"],
        )
        self.assertEqual(
            case["payload"]["ElectricStorage"]["om_cost_fraction_of_installed_cost"],
            0.01,
        )

    def test_case_can_override_min_duration_hours(self):
        storage = build_thailand_case(
            _case_config(
                storage={"max_kw": 500, "max_kwh": 1000, "min_duration_hours": 2.0}
            )
        )["payload"]["ElectricStorage"]
        self.assertEqual(storage["min_duration_hours"], 2.0)

    def test_case_can_override_om_cost_fraction(self):
        storage = build_thailand_case(
            _case_config(
                storage={
                    "max_kw": 500,
                    "max_kwh": 1000,
                    "om_cost_fraction_of_installed_cost": 0.02,
                }
            )
        )["payload"]["ElectricStorage"]
        self.assertEqual(storage["om_cost_fraction_of_installed_cost"], 0.02)

    def test_tilt_defaults_to_fifteen_degrees(self):
        captured = {}

        def _fake_fetch(latitude, longitude, overrides=None, api_key=None):
            captured["overrides"] = overrides
            return {"production_factor": [0.0] * 8760, "poa_wm2": [0.0] * 8760}

        with mock.patch.object(pvwatts_client, "fetch_pv_series", _fake_fetch):
            build_thailand_case(_case_config())
        self.assertEqual(captured["overrides"]["tilt"], 15)

    def test_case_can_override_tilt(self):
        captured = {}

        def _fake_fetch(latitude, longitude, overrides=None, api_key=None):
            captured["overrides"] = overrides
            return {"production_factor": [0.0] * 8760, "poa_wm2": [0.0] * 8760}

        config = _case_config()
        config["site"]["tilt"] = 7
        with mock.patch.object(pvwatts_client, "fetch_pv_series", _fake_fetch):
            build_thailand_case(config)
        self.assertEqual(captured["overrides"]["tilt"], 7)


class RofuCaseTreeTests(TestCase):
    """Every committed Rofu case.json declares the expected PV/storage shape.

    Reads the raw case.json files directly and does not call
    build_thailand_case, so this does not prove the cases actually build.
    """

    ROOT = Path("outputs/thailand_case/rofu_thailand")
    EXPECTED_PV_CAPS = {
        "case_1": 1685.0,
        "case_2": 1895.0,
        "case_3": 2106.0,
        "case_4": 3230.0,
        "case_5": 1685.0,
        "case_6": 3230.0,
    }

    def test_all_six_cases_declare_the_expected_pv_cap(self):
        for name, expected in self.EXPECTED_PV_CAPS.items():
            with self.subTest(case=name):
                config = json.loads(
                    (self.ROOT / name / "case.json").read_text(encoding="utf-8")
                )
                self.assertEqual(
                    config["technologies"]["pv"]["max_kw"], expected
                )

    def test_only_the_storage_cases_declare_storage(self):
        for name in ("case_1", "case_2", "case_3", "case_4"):
            with self.subTest(case=name):
                config = json.loads(
                    (self.ROOT / name / "case.json").read_text(encoding="utf-8")
                )
                storage = config["technologies"].get("storage", {})
                self.assertFalse(storage.get("max_kw"))
                self.assertFalse(storage.get("max_kwh"))
        for name in ("case_5", "case_6"):
            with self.subTest(case=name):
                config = json.loads(
                    (self.ROOT / name / "case.json").read_text(encoding="utf-8")
                )
                self.assertGreater(
                    config["technologies"]["storage"]["max_kw"], 0
                )
