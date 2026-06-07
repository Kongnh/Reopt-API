import json
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.dppa_settlement import (
    load_cfmp_series,
    load_fmp_series,
    settle_dppa_year_one,
)


class SettleDppaYearOneTests(TestCase):

    def test_known_24_hour_fixture_matches_hand_computed_values(self):
        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        k = 1.026
        kpp = 1.027263
        cfmp = 1500.0  # _known_day_dppa_inputs has no cfmp_series → falls back to fmp
        q_adj_solar = 80.0 / (k * kpp)
        # C_DN per the clarified ND57 formula: Q_adj × CFMP × K_pp.
        c_dn_solar = q_adj_solar * cfmp * kpp
        c_dppa_solar = q_adj_solar * 360.0
        c_cl_solar = q_adj_solar * 163.0
        c_bl_solar = (100.0 - q_adj_solar) * 2000.0
        c_bl_night = 100.0 * 2000.0
        cfd_solar = (1700.0 - 1500.0) * 80.0

        year_one = result["year_one"]
        self.assertAlmostEqual(year_one["c_dn_vnd"], 12 * c_dn_solar, delta=0.01)
        self.assertAlmostEqual(year_one["c_dppa_vnd"], 12 * c_dppa_solar, delta=0.01)
        self.assertAlmostEqual(year_one["c_cl_vnd"], 12 * c_cl_solar, delta=0.01)
        self.assertAlmostEqual(
            year_one["c_bl_vnd"],
            12 * c_bl_solar + 12 * c_bl_night,
            delta=0.01,
        )
        self.assertAlmostEqual(
            year_one["cfd_strike_revenue_vnd"],
            12 * 1700.0 * 80.0,
            delta=0.01,
        )
        self.assertAlmostEqual(
            year_one["cfd_fmp_offset_vnd"],
            12 * 1500.0 * 80.0,
            delta=0.01,
        )
        self.assertAlmostEqual(
            year_one["generator_fmp_revenue_vnd"],
            12 * 80.0 * 1500.0,
            delta=0.01,
        )
        self.assertAlmostEqual(
            year_one["q_re_meter_kwh"],
            12 * 80.0,
            delta=0.001,
        )

    def test_offtaker_dppa_cost_equals_sum_of_components(self):
        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        y1 = result["year_one"]
        cfd_net = y1["cfd_strike_revenue_vnd"] - y1["cfd_fmp_offset_vnd"]
        expected = y1["c_dn_vnd"] + y1["c_dppa_vnd"] + y1["c_cl_vnd"] + y1["c_bl_vnd"] + cfd_net

        self.assertAlmostEqual(y1["offtaker_dppa_cost_vnd"], expected, delta=0.01)

    def test_generator_revenue_equals_fmp_injection_plus_cfd_net(self):
        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        y1 = result["year_one"]
        cfd_net = y1["cfd_strike_revenue_vnd"] - y1["cfd_fmp_offset_vnd"]

        self.assertAlmostEqual(
            y1["generator_revenue_vnd"],
            y1["generator_fmp_revenue_vnd"] + cfd_net,
            delta=0.01,
        )

    def test_esco_energy_revenue_is_zero(self):
        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        self.assertEqual(result["esco_energy_revenue_vnd"], 0.0)

    def test_zero_cfd_volume_reduces_to_pure_spot_settlement(self):
        inputs = _known_day_dppa_inputs()
        inputs["cfd_contract_volume_kwh_per_hour"] = [0.0] * 24

        result = settle_dppa_year_one(
            dppa_inputs=inputs,
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        y1 = result["year_one"]
        self.assertEqual(y1["cfd_strike_revenue_vnd"], 0.0)
        self.assertEqual(y1["cfd_fmp_offset_vnd"], 0.0)
        self.assertAlmostEqual(
            y1["generator_revenue_vnd"],
            y1["generator_fmp_revenue_vnd"],
            delta=0.01,
        )

    def test_storage_discharge_counts_toward_generator_meter_injection(self):
        # Co-located BESS sits upstream of the offtaker meter, so storage-to-load
        # crosses the generator POC.
        dispatch = _known_day_dispatch()
        dispatch["storage_to_load_kw"] = [10.0 if 18 <= h < 20 else 0.0 for h in range(24)]

        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=dispatch,
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        # 12h * 80kW (solar PV-to-load) + 2h * 10kW (storage-to-load) = 980 kWh injected
        self.assertAlmostEqual(result["year_one"]["q_re_meter_kwh"], 980.0, delta=0.001)

    def test_scalar_cfd_volume_broadcasts_to_8760_during_contracted_hours(self):
        inputs = _known_day_dppa_inputs()
        inputs["cfd_contract_volume_kwh_per_hour"] = 50.0

        result = settle_dppa_year_one(
            dppa_inputs=inputs,
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        # 24 hours at flat 50 kWh contracted volume
        self.assertAlmostEqual(
            result["year_one"]["cfd_strike_revenue_vnd"],
            24 * 1700.0 * 50.0,
            delta=0.01,
        )

    def test_returns_monthly_breakout_with_twelve_entries(self):
        # Run the settlement against a full-year fixture so all 12 months populate.
        dppa_inputs = _known_day_dppa_inputs()
        dppa_inputs["fmp_series_vnd_per_kwh"] = [1500.0] * 8760
        dppa_inputs["cfd_contract_volume_kwh_per_hour"] = 80.0

        dispatch = {key: [0.0] * 8760 for key in _known_day_dispatch()}
        dispatch["load_kw"] = [100.0] * 8760
        dispatch["pv_to_load_kw"] = [80.0] * 8760

        result = settle_dppa_year_one(
            dppa_inputs=dppa_inputs,
            dispatch=dispatch,
            evn_energy_rates_vnd_per_kwh=[2000.0] * 8760,
        )

        self.assertEqual(len(result["monthly_breakout"]), 12)
        # First month has 31 days (Jan); year-one cost components are positive.
        january = result["monthly_breakout"][0]
        self.assertEqual(january["month"], 1)
        self.assertGreater(january["c_dn_vnd"], 0)
        self.assertGreater(january["c_bl_vnd"], 0)


class LoadFmpSeriesTests(TestCase):

    def test_load_fmp_series_reads_8760_values(self):
        series = load_fmp_series(_fmp_json_path())

        self.assertEqual(len(series), 8760)
        self.assertTrue(all(isinstance(value, (int, float)) for value in series))

    def test_load_fmp_series_returns_fmp_not_cfmp(self):
        series = load_fmp_series(_fmp_json_path())
        raw = json.loads(Path(_fmp_json_path()).read_text(encoding="utf-8"))

        self.assertEqual(series[0], raw["fmp_vnd_per_kwh"][0])

    def test_load_cfmp_series_returns_cfmp_not_fmp(self):
        cfmp = load_cfmp_series(_fmp_json_path())
        raw = json.loads(Path(_fmp_json_path()).read_text(encoding="utf-8"))

        self.assertEqual(len(cfmp), 8760)
        self.assertEqual(cfmp[0], raw["cfmp_vnd_per_kwh"][0])
        # CFMP is FMP marked up by distribution losses, so it's strictly larger.
        self.assertGreater(cfmp[0], raw["fmp_vnd_per_kwh"][0])


class DispatchExtensionsTests(TestCase):

    def test_curtailed_pv_is_credited_as_grid_export_in_q_re_meter(self):
        # Under DPPA the generator owns the meter; surplus that a self-consumption
        # optimizer would curtail flows to grid at FMP instead.
        dispatch = _known_day_dispatch()
        dispatch["pv_curtailed_kw"] = [50.0 if 10 <= h < 14 else 0.0 for h in range(24)]

        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=dispatch,
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        # 12h × 80kW solar + 4h × 50kW curtailed = 960 + 200 = 1160 kWh injected
        self.assertAlmostEqual(result["year_one"]["q_re_meter_kwh"], 1160.0, delta=0.001)
        self.assertAlmostEqual(result["year_one"]["q_pv_curtailed_kwh"], 200.0, delta=0.001)
        # Generator FMP revenue scales accordingly (1160 kWh × 1500 VND/kWh).
        self.assertAlmostEqual(
            result["year_one"]["generator_fmp_revenue_vnd"],
            1160.0 * 1500.0,
            delta=0.01,
        )

    def test_cfmp_series_drives_c_dn_when_provided(self):
        inputs = _known_day_dppa_inputs()
        inputs["cfmp_series_vnd_per_kwh"] = [1550.0] * 24  # CFMP > FMP (1500)

        result = settle_dppa_year_one(
            dppa_inputs=inputs,
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        kpp = 1.027263
        q_adj_solar = 80.0 / (1.026 * kpp)
        expected_c_dn_solar = q_adj_solar * 1550.0 * kpp
        self.assertAlmostEqual(
            result["year_one"]["c_dn_vnd"], 12 * expected_c_dn_solar, delta=0.01,
        )


def _known_day_dppa_inputs():
    return {
        "type": "grid_dppa_cfd",
        "fmp_series_vnd_per_kwh": [1500.0] * 24,
        "cfd_strike_per_kwh_vnd": 1700.0,
        "cfd_contract_volume_kwh_per_hour": [80.0 if 6 <= h < 18 else 0.0 for h in range(24)],
        "transmission_loss_factor_k": 1.026,
        "distribution_loss_factor_kpp": 1.027263,
        "allocation_fraction_delta": 1.0,
        "c_dppa_service_fee_vnd_per_kwh": 360.0,
        "c_cl_settlement_adder_vnd_per_kwh": 163.0,
        "fee_escalation_rate": 0.04,
        "cfd_strike_escalation_rate": 0.0,
    }


def _known_day_dispatch():
    return {
        "load_kw": [100.0] * 24,
        "pv_to_load_kw": [80.0 if 6 <= h < 18 else 0.0 for h in range(24)],
        "pv_to_grid_kw": [0.0] * 24,
        "storage_to_load_kw": [0.0] * 24,
        "storage_to_grid_kw": [0.0] * 24,
    }


def _fmp_json_path():
    return str(
        Path(__file__).resolve().parents[2]
        / "DPPA DOC"
        / "fmp_cfmp_vn.json"
    )
