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
        cfmp = 1500.0 * k  # no cfmp_series → falls back to CFMP = FMP × k
        q_adj_solar = 80.0 / kpp  # quantity conversion uses Kpp only (CD7)
        # C_DN per ND57 / CD7: Q_Khc × CFMP × K_pp.
        c_dn_solar = q_adj_solar * cfmp * kpp
        c_dppa_solar = q_adj_solar * 360.0
        c_cl_solar = q_adj_solar * 163.0
        c_bl_solar = (100.0 - q_adj_solar) * 2000.0
        c_bl_night = 100.0 * 2000.0
        # CfD settles on min(Q_c, Q_Khc): contract 80 vs received 80/kpp.
        q_cfd_solar = min(80.0, q_adj_solar)

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
            12 * 1700.0 * q_cfd_solar,
            delta=0.01,
        )
        self.assertAlmostEqual(
            year_one["cfd_fmp_offset_vnd"],
            12 * 1500.0 * q_cfd_solar,
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

        # Flat 50 kWh contracted volume, but CfD only settles on received
        # volume: solar hours Q_Khc = 80/kpp > 50 → 50; night hours Q_Khc = 0.
        self.assertAlmostEqual(
            result["year_one"]["cfd_strike_revenue_vnd"],
            12 * 1700.0 * 50.0,
            delta=0.01,
        )

    def test_buyer_charges_settle_on_matched_consumption_q_khc(self):
        # ND57 / vietnam_market_context.md: Q_Khc = min(load, Q_adj). The buyer
        # pays C_DN/C_DPPA/C_CL only on matched consumption; excess generation
        # stays with the generator as spot revenue and must not be billed to
        # the buyer.
        dispatch = _known_day_dispatch()
        dispatch["load_kw"] = [50.0] * 24
        dispatch["pv_to_load_kw"] = [50.0 if 6 <= h < 18 else 0.0 for h in range(24)]
        dispatch["pv_to_grid_kw"] = [100.0 if 6 <= h < 18 else 0.0 for h in range(24)]

        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=dispatch,
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        k, kpp = 1.026, 1.027263
        q_adj_solar = 150.0 / kpp
        self.assertGreater(q_adj_solar, 50.0)  # generation exceeds load
        q_khc = 50.0

        y1 = result["year_one"]
        # CFMP fallback = FMP × k.
        self.assertAlmostEqual(y1["c_dn_vnd"], 12 * q_khc * 1500.0 * k * kpp, delta=0.01)
        self.assertAlmostEqual(y1["c_dppa_vnd"], 12 * q_khc * 360.0, delta=0.01)
        self.assertAlmostEqual(y1["c_cl_vnd"], 12 * q_khc * 163.0, delta=0.01)
        # Solar hours fully matched (no shortfall); night hours buy 50 kWh retail.
        self.assertAlmostEqual(y1["c_bl_vnd"], 12 * 50.0 * 2000.0, delta=0.01)
        self.assertAlmostEqual(y1["q_khc_kwh"], 12 * 50.0, delta=0.001)
        # The generator still sells its full injection at FMP.
        self.assertAlmostEqual(
            y1["generator_fmp_revenue_vnd"], 12 * 150.0 * 1500.0, delta=0.01,
        )

    def test_matched_retail_value_reported_for_degradation_adjustment(self):
        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        kpp = 1.027263
        q_khc_solar = 80.0 / kpp  # below the 100 kW load, fully matched
        self.assertAlmostEqual(
            result["year_one"]["matched_retail_value_vnd"],
            12 * q_khc_solar * 2000.0,
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
        q_adj_solar = 80.0 / kpp
        expected_c_dn_solar = q_adj_solar * 1550.0 * kpp
        self.assertAlmostEqual(
            result["year_one"]["c_dn_vnd"], 12 * expected_c_dn_solar, delta=0.01,
        )


class CD7AlignmentTests(TestCase):
    """Align settlement with the official NSMO CD7 simulation deck (05/9/2025).

    CD7 settles every example with C_DN = Q_khhc × FMP × k × Kpp where k and
    Kpp mark up the *price*; quantity conversion generator meter → customer
    uses Kpp only (Ví dụ 1: Qm 6,048,000 kWh ↔ Q_khhc 6,000,000 = ÷1.008).
    """

    def test_cd7_example_1_reproduces_official_totals(self):
        # CD7 Ví dụ 1: Q_khhc = 6,000,000 kWh, Qm = 6,048,000 kWh, FMP = 1,200,
        # k = 1.026, Kpp = 1.008, Pc = 1,300, Qc = 6,000,000.
        dppa_inputs = {
            "type": "grid_dppa_cfd",
            "fmp_series_vnd_per_kwh": [1200.0],
            "cfd_strike_per_kwh_vnd": 1300.0,
            "cfd_contract_volume_kwh_per_hour": [6_000_000.0],
            "transmission_loss_factor_k": 1.026,
            "distribution_loss_factor_kpp": 1.008,
            "allocation_fraction_delta": 1.0,
            "c_dppa_service_fee_vnd_per_kwh": 360.0,
            "c_cl_settlement_adder_vnd_per_kwh": 163.3,
        }
        dispatch = {
            "load_kw": [6_000_000.0],
            "pv_to_load_kw": [6_048_000.0],
            "pv_to_grid_kw": [0.0],
            "storage_to_load_kw": [0.0],
            "storage_to_grid_kw": [0.0],
        }

        result = settle_dppa_year_one(
            dppa_inputs=dppa_inputs,
            dispatch=dispatch,
            evn_energy_rates_vnd_per_kwh=[2204.0],
        )

        y1 = result["year_one"]
        self.assertAlmostEqual(y1["q_khc_kwh"], 6_000_000.0, delta=0.5)
        self.assertAlmostEqual(y1["c_dn_vnd"], 7_446_297_600.0, delta=1.0)
        self.assertAlmostEqual(y1["c_dppa_vnd"], 2_160_000_000.0, delta=1.0)
        self.assertAlmostEqual(y1["c_cl_vnd"], 979_800_000.0, delta=1.0)
        self.assertAlmostEqual(y1["c_bl_vnd"], 0.0, delta=0.5)
        self.assertAlmostEqual(y1["cfd_net_vnd"], 600_000_000.0, delta=1.0)
        # C_KH = C_EVN + C_CfD = 10,586,097,600 + 600,000,000.
        self.assertAlmostEqual(y1["offtaker_dppa_cost_vnd"], 11_186_097_600.0, delta=2.0)
        # Generator: Qm × FMP + CfD = 7,257,600,000 + 600,000,000.
        self.assertAlmostEqual(y1["generator_revenue_vnd"], 7_857_600_000.0, delta=2.0)

    def test_quantity_conversion_uses_kpp_only_not_k(self):
        # k adjusts the market price the customer pays, never the delivered
        # quantity (CFMP = FMP × k). Volume conversion uses Kpp only.
        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        kpp = 1.027263
        self.assertAlmostEqual(
            result["year_one"]["q_adj_kwh"], 12 * 80.0 / kpp, delta=0.001,
        )

    def test_cfmp_fallback_is_fmp_times_k_when_series_missing(self):
        # _known_day_dppa_inputs has no cfmp series: C_DN must fall back to
        # CFMP = FMP × k, i.e. C_DN = Q_khc × FMP × k × Kpp per CD7.
        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        k, kpp = 1.026, 1.027263
        q_khc = 80.0 / kpp  # below the 100 kW load, fully matched
        self.assertAlmostEqual(
            result["year_one"]["c_dn_vnd"],
            12 * q_khc * 1500.0 * k * kpp,
            delta=0.01,
        )

    def test_default_c_cl_adder_is_163_3(self):
        inputs = _known_day_dppa_inputs()
        del inputs["c_cl_settlement_adder_vnd_per_kwh"]

        result = settle_dppa_year_one(
            dppa_inputs=inputs,
            dispatch=_known_day_dispatch(),
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        kpp = 1.027263
        q_khc = 80.0 / kpp
        self.assertAlmostEqual(
            result["year_one"]["c_cl_vnd"], 12 * q_khc * 163.3, delta=0.01,
        )

    def test_cfd_settles_on_received_volume_capped_by_contract(self):
        # CD7 Ví dụ 4: CfD revenue is computed only on the DPPA volume the
        # customer actually receives — min(Q_c, Q_Khc) — never on contracted
        # volume the buyer did not absorb.
        dispatch = _known_day_dispatch()
        dispatch["load_kw"] = [50.0] * 24
        dispatch["pv_to_load_kw"] = [50.0 if 6 <= h < 18 else 0.0 for h in range(24)]
        dispatch["pv_to_grid_kw"] = [100.0 if 6 <= h < 18 else 0.0 for h in range(24)]

        result = settle_dppa_year_one(
            dppa_inputs=_known_day_dppa_inputs(),
            dispatch=dispatch,
            evn_energy_rates_vnd_per_kwh=[2000.0] * 24,
        )

        # Contract volume is 80 kWh in solar hours but Q_Khc = 50 kWh.
        y1 = result["year_one"]
        self.assertAlmostEqual(y1["q_cfd_kwh"], 12 * 50.0, delta=0.001)
        self.assertAlmostEqual(y1["cfd_strike_revenue_vnd"], 12 * 1700.0 * 50.0, delta=0.01)
        self.assertAlmostEqual(y1["cfd_fmp_offset_vnd"], 12 * 1500.0 * 50.0, delta=0.01)


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
