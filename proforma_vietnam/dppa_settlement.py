import json
from pathlib import Path


DPPA_TYPE_NONE = "none"
DPPA_TYPE_GRID_CFD = "grid_dppa_cfd"

DEFAULT_TRANSMISSION_LOSS_FACTOR_K = 1.026
DEFAULT_ALLOCATION_FRACTION_DELTA = 1.0
DEFAULT_C_DPPA_SERVICE_FEE_VND_PER_KWH = 360.0
DEFAULT_C_CL_SETTLEMENT_ADDER_VND_PER_KWH = 163.0
DEFAULT_CFD_STRIKE_ESCALATION_RATE = 0.0

DISTRIBUTION_LOSS_FACTOR_KPP_BY_VOLTAGE = {
    "110kv_and_above": 1.008525,
    "22_to_110kv": 1.027263,
}

# Non-leap year month boundaries for 8760-hour series.
MONTH_DAY_COUNTS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def load_fmp_series(path):
    """Read the 8760-hour FMP series (VND/kWh) from the reference JSON file."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    series = raw.get("fmp_vnd_per_kwh")
    if series is None:
        raise ValueError(f"{path} does not contain key 'fmp_vnd_per_kwh'.")
    return list(series)


def load_cfmp_series(path):
    """Read the 8760-hour CFMP series (VND/kWh) from the reference JSON file.

    CFMP is the customer-side spot price (FMP marked up by distribution losses)
    used in C_DN settlement per ND57 Art. 14-18 and the user's clarified
    formula: C_DN = Q_adj × CFMP × K_pp.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    series = raw.get("cfmp_vnd_per_kwh")
    if series is None:
        raise ValueError(f"{path} does not contain key 'cfmp_vnd_per_kwh'.")
    return list(series)


def settle_dppa_year_one(*, dppa_inputs, dispatch, evn_energy_rates_vnd_per_kwh):
    """Compute year-one DPPA settlement primitives per ND57 Điều 14-18.

    All cost / revenue components are returned as year-one totals (VND).
    Year-N escalation is applied downstream in cash_flow.py using the
    `escalation` rates carried alongside the year-one values.
    """
    dppa_type = dppa_inputs.get("type", DPPA_TYPE_NONE)
    if dppa_type != DPPA_TYPE_GRID_CFD:
        raise ValueError(
            f"settle_dppa_year_one only supports type='{DPPA_TYPE_GRID_CFD}', got '{dppa_type}'."
        )

    fmp = list(dppa_inputs["fmp_series_vnd_per_kwh"])
    cfmp = list(dppa_inputs.get("cfmp_series_vnd_per_kwh") or fmp)
    p_evn = list(evn_energy_rates_vnd_per_kwh)
    horizon = max(
        len(fmp),
        len(cfmp),
        len(p_evn),
        *(len(series) for series in dispatch.values()),
    )

    k = dppa_inputs.get("transmission_loss_factor_k", DEFAULT_TRANSMISSION_LOSS_FACTOR_K)
    kpp = dppa_inputs["distribution_loss_factor_kpp"]
    delta = dppa_inputs.get("allocation_fraction_delta", DEFAULT_ALLOCATION_FRACTION_DELTA)
    f_dppa = dppa_inputs.get(
        "c_dppa_service_fee_vnd_per_kwh",
        DEFAULT_C_DPPA_SERVICE_FEE_VND_PER_KWH,
    )
    f_cl = dppa_inputs.get(
        "c_cl_settlement_adder_vnd_per_kwh",
        DEFAULT_C_CL_SETTLEMENT_ADDER_VND_PER_KWH,
    )
    p_c = dppa_inputs["cfd_strike_per_kwh_vnd"]
    q_c = _broadcast_volume(dppa_inputs["cfd_contract_volume_kwh_per_hour"], horizon)

    load_kw = _pad(dispatch.get("load_kw", []), horizon)
    pv_to_load = _pad(dispatch.get("pv_to_load_kw", []), horizon)
    pv_to_grid = _pad(dispatch.get("pv_to_grid_kw", []), horizon)
    pv_curtailed = _pad(dispatch.get("pv_curtailed_kw", []), horizon)
    storage_to_load = _pad(dispatch.get("storage_to_load_kw", []), horizon)
    storage_to_grid = _pad(dispatch.get("storage_to_grid_kw", []), horizon)

    loss_divisor = k * kpp

    hourly_rows = []
    sums = {
        "c_dn_vnd": 0.0,
        "c_dppa_vnd": 0.0,
        "c_cl_vnd": 0.0,
        "c_bl_vnd": 0.0,
        "cfd_strike_revenue_vnd": 0.0,
        "cfd_fmp_offset_vnd": 0.0,
        "generator_fmp_revenue_vnd": 0.0,
        "q_re_meter_kwh": 0.0,
        "q_re_delivered_kwh": 0.0,
        "q_adj_kwh": 0.0,
        "q_pv_curtailed_kwh": 0.0,
        "q_pv_to_grid_effective_kwh": 0.0,
    }

    for h in range(horizon):
        # Under DPPA the generator owns the meter; surplus that would be
        # curtailed in a self-consumption REopt run flows to grid at FMP.
        # Include curtailed PV in pv_to_grid for settlement accounting even
        # when the upstream optimizer ran in self-consumption mode.
        pv_to_grid_effective = pv_to_grid[h] + pv_curtailed[h]
        q_re_meter = pv_to_load[h] + pv_to_grid_effective + storage_to_load[h] + storage_to_grid[h]
        q_re_delivered = pv_to_load[h] + storage_to_load[h]
        q_adj = q_re_meter / loss_divisor * delta
        fmp_h = fmp[h] if h < len(fmp) else 0.0
        cfmp_h = cfmp[h] if h < len(cfmp) else fmp_h
        p_evn_h = p_evn[h] if h < len(p_evn) else 0.0
        q_c_h = q_c[h]

        # Customer-side spot energy charge per the clarified ND57 formula:
        # C_DN = Q_KHhc × CFMP × K_pp, where Q_KHhc is the loss-adjusted
        # customer consumption (Q_adj) and CFMP is the buyer-side spot price.
        c_dn = q_adj * cfmp_h * kpp
        c_dppa = q_adj * f_dppa
        c_cl = q_adj * f_cl
        shortfall = max(load_kw[h] - q_adj, 0.0)
        c_bl = shortfall * p_evn_h
        cfd_strike_revenue = p_c * q_c_h
        cfd_fmp_offset = fmp_h * q_c_h
        cfd_net = cfd_strike_revenue - cfd_fmp_offset
        gen_fmp_revenue = q_re_meter * fmp_h

        sums["c_dn_vnd"] += c_dn
        sums["c_dppa_vnd"] += c_dppa
        sums["c_cl_vnd"] += c_cl
        sums["c_bl_vnd"] += c_bl
        sums["cfd_strike_revenue_vnd"] += cfd_strike_revenue
        sums["cfd_fmp_offset_vnd"] += cfd_fmp_offset
        sums["generator_fmp_revenue_vnd"] += gen_fmp_revenue
        sums["q_re_meter_kwh"] += q_re_meter
        sums["q_re_delivered_kwh"] += q_re_delivered
        sums["q_adj_kwh"] += q_adj
        sums["q_pv_curtailed_kwh"] += pv_curtailed[h]
        sums["q_pv_to_grid_effective_kwh"] += pv_to_grid_effective

        hourly_rows.append({
            "hour": h + 1,
            "load_kw": load_kw[h],
            "q_re_meter_kw": q_re_meter,
            "q_re_delivered_kw": q_re_delivered,
            "cfmp_vnd_per_kwh": cfmp_h,
            "q_adj_kw": q_adj,
            "fmp_vnd_per_kwh": fmp_h,
            "c_dn_vnd": c_dn,
            "c_dppa_vnd": c_dppa,
            "c_cl_vnd": c_cl,
            "c_bl_vnd": c_bl,
            "cfd_payment_vnd": cfd_net,
        })

    cfd_net_total = sums["cfd_strike_revenue_vnd"] - sums["cfd_fmp_offset_vnd"]
    generator_revenue = sums["generator_fmp_revenue_vnd"] + cfd_net_total
    offtaker_cost = (
        sums["c_dn_vnd"]
        + sums["c_dppa_vnd"]
        + sums["c_cl_vnd"]
        + sums["c_bl_vnd"]
        + cfd_net_total
    )

    year_one = {
        **sums,
        "cfd_net_vnd": cfd_net_total,
        "generator_revenue_vnd": generator_revenue,
        "offtaker_dppa_cost_vnd": offtaker_cost,
    }

    return {
        "type": dppa_type,
        "esco_energy_revenue_vnd": 0.0,
        "year_one": year_one,
        "escalation": {
            "fee_escalation_rate": dppa_inputs.get("fee_escalation_rate", 0.0),
            "cfd_strike_escalation_rate": dppa_inputs.get(
                "cfd_strike_escalation_rate",
                DEFAULT_CFD_STRIKE_ESCALATION_RATE,
            ),
        },
        "hourly_breakout": hourly_rows,
        "monthly_breakout": _monthly_breakout(hourly_rows),
    }


def _broadcast_volume(value, horizon):
    if isinstance(value, (int, float)):
        return [float(value)] * horizon
    series = list(value)
    if len(series) < horizon:
        series = series + [0.0] * (horizon - len(series))
    return series


def _pad(series, horizon):
    series = list(series)
    if len(series) < horizon:
        series = series + [0.0] * (horizon - len(series))
    return series


def _monthly_breakout(hourly_rows):
    boundaries = _month_boundaries(len(hourly_rows))
    months = []
    for month_index, (start, end) in enumerate(boundaries, start=1):
        c_dn = sum(row["c_dn_vnd"] for row in hourly_rows[start:end])
        c_dppa = sum(row["c_dppa_vnd"] for row in hourly_rows[start:end])
        c_cl = sum(row["c_cl_vnd"] for row in hourly_rows[start:end])
        c_bl = sum(row["c_bl_vnd"] for row in hourly_rows[start:end])
        cfd_net = sum(row["cfd_payment_vnd"] for row in hourly_rows[start:end])
        generator_rev = sum(
            row["q_re_meter_kw"] * row["fmp_vnd_per_kwh"]
            for row in hourly_rows[start:end]
        ) + cfd_net
        customer_total = c_dn + c_dppa + c_cl + c_bl + cfd_net
        months.append({
            "month": month_index,
            "c_dn_vnd": c_dn,
            "c_dppa_vnd": c_dppa,
            "c_cl_vnd": c_cl,
            "c_bl_vnd": c_bl,
            "cfd_net_vnd": cfd_net,
            "generator_revenue_vnd": generator_rev,
            "customer_total_vnd": customer_total,
        })
    return months


def _month_boundaries(horizon):
    if horizon != 8760:
        return [(0, horizon)] + [(horizon, horizon)] * 11
    boundaries = []
    start = 0
    for days in MONTH_DAY_COUNTS:
        end = start + days * 24
        boundaries.append((start, end))
        start = end
    return boundaries
