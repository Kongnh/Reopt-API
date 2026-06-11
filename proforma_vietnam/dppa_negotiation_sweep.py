from copy import deepcopy


DEFAULT_STRIKES_VND_PER_KWH = tuple(range(1400, 2201, 100))
DEFAULT_VOLUME_FRACTIONS = (0.70, 0.80, 0.90, 1.00)
# Buyer gate evaluates the first 10 years AND the full project lifetime
# (cumulative savings vs BAU); Year 1 is reported as context only.
DEFAULT_THRESHOLDS = {
    "buyer_savings_10yr_fraction": 0.0,
    "buyer_savings_lifetime_fraction": 0.0,
    "equity_irr_fraction": 0.12,
    "minimum_dscr": 1.20,
}


def run_dppa_negotiation_sweep(
    *,
    reference_dppa_inputs,
    evaluator,
    non_dppa_case_2_cash_flow,
    strikes_vnd_per_kwh=DEFAULT_STRIKES_VND_PER_KWH,
    volume_fractions=DEFAULT_VOLUME_FRACTIONS,
    thresholds=None,
    baseline_sources=None,
):
    thresholds = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    reference_volume = list(reference_dppa_inputs["cfd_contract_volume_kwh_per_hour"])
    case_2_year_one = non_dppa_case_2_cash_flow["annual_cash_flows"][0]
    case_2_outflow = case_2_year_one["offtaker_post_project_cost_usd"]
    scenarios = []

    for strike in strikes_vnd_per_kwh:
        for fraction in volume_fractions:
            dppa_inputs = deepcopy(reference_dppa_inputs)
            dppa_inputs["cfd_strike_per_kwh_vnd"] = float(strike)
            dppa_inputs["volume_fraction"] = float(fraction)
            dppa_inputs["cfd_contract_volume_kwh_per_hour"] = [
                value * fraction for value in reference_volume
            ]
            cash_flow = evaluator(dppa_inputs)
            scenarios.append(
                _scenario_row(strike, fraction, dppa_inputs, cash_flow, case_2_outflow)
            )

    classify_balanced_deals(scenarios, thresholds)
    mark_pareto_frontier(scenarios)
    balanced = [row for row in scenarios if row["balanced_deal"]]
    frontier = [row for row in scenarios if row["pareto_frontier"]]
    recommended = [
        row for row in frontier
        if row["equity_irr_fraction"] >= thresholds["equity_irr_fraction"] + 0.01
        and row["minimum_dscr"] >= thresholds["minimum_dscr"] + 0.05
    ] or frontier

    return {
        "configuration": {
            "strikes_vnd_per_kwh": list(strikes_vnd_per_kwh),
            "volume_fractions": list(volume_fractions),
            "thresholds": thresholds,
        },
        "baseline_sources": baseline_sources or {},
        "scenarios": scenarios,
        "balanced_deals": balanced,
        "negotiation_frontier": frontier,
        "recommended_negotiation_range": recommended,
    }


def classify_balanced_deals(rows, thresholds=None):
    thresholds = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    for row in rows:
        dscr_values = [
            value for value in row.get("annual_dscr", [])
            if value is not None
        ]
        if "minimum_dscr" not in row:
            row["minimum_dscr"] = min(dscr_values) if dscr_values else None
        reasons = []
        if row["buyer_savings_10yr_fraction"] < thresholds["buyer_savings_10yr_fraction"]:
            reasons.append("buyer_10yr_savings_below_0_percent")
        if row["buyer_savings_lifetime_fraction"] < thresholds["buyer_savings_lifetime_fraction"]:
            reasons.append("buyer_lifetime_savings_below_0_percent")
        if row["equity_irr_fraction"] < thresholds["equity_irr_fraction"]:
            reasons.append("equity_irr_below_12_percent")
        if row["minimum_dscr"] is None or row["minimum_dscr"] < thresholds["minimum_dscr"]:
            reasons.append("minimum_dscr_below_1_20x")
        row["failed_qualification_reasons"] = reasons
        row["balanced_deal"] = not reasons
    return rows


def mark_pareto_frontier(rows):
    balanced = [row for row in rows if row.get("balanced_deal")]
    for row in rows:
        row["pareto_frontier"] = False
    for candidate in balanced:
        candidate["pareto_frontier"] = not any(
            other is not candidate
            and other["buyer_savings_lifetime_fraction"]
                >= candidate["buyer_savings_lifetime_fraction"]
            and other["equity_irr_fraction"] >= candidate["equity_irr_fraction"]
            and (
                other["buyer_savings_lifetime_fraction"]
                    > candidate["buyer_savings_lifetime_fraction"]
                or other["equity_irr_fraction"] > candidate["equity_irr_fraction"]
            )
            for other in balanced
        )
    return rows


def _scenario_row(strike, fraction, dppa_inputs, cash_flow, case_2_outflow):
    annual = cash_flow["annual_cash_flows"]
    year_one = annual[0]
    summary = cash_flow["summary"]
    bau = year_one["bau_evn_bill_usd"]
    outflow = year_one["offtaker_post_project_cost_usd"]
    savings_vs_bau = bau - outflow
    savings_vs_case_2 = case_2_outflow - outflow
    cfd_net = year_one["cfd_net_usd"]
    annual_dscr = [
        row["dscr"] if row.get("debt_service_usd") else None
        for row in annual
    ]
    return {
        "scenario_id": f"strike_{int(strike)}_volume_{int(round(fraction * 100))}",
        "strike_vnd_per_kwh": float(strike),
        "volume_fraction": float(fraction),
        "annual_contracted_kwh": sum(dppa_inputs["cfd_contract_volume_kwh_per_hour"]),
        "factory_savings_vs_bau_usd": savings_vs_bau,
        "factory_savings_vs_bau_fraction": savings_vs_bau / bau if bau else None,
        "buyer_savings_10yr_usd": summary["buyer_savings_10yr_usd"],
        "buyer_savings_10yr_fraction": summary["buyer_savings_10yr_fraction"],
        "buyer_savings_lifetime_usd": summary["buyer_savings_lifetime_usd"],
        "buyer_savings_lifetime_fraction": summary["buyer_savings_lifetime_fraction"],
        "factory_savings_vs_case_2_usd": savings_vs_case_2,
        "factory_savings_vs_case_2_fraction": (
            savings_vs_case_2 / case_2_outflow if case_2_outflow else None
        ),
        "factory_year_one_outflow_usd": outflow,
        "equity_irr_fraction": summary["equity_irr_fraction"],
        "npv_usd": summary["npv_usd"],
        "minimum_dscr": min(value for value in annual_dscr if value is not None),
        "average_dscr": summary["average_dscr"],
        "annual_dscr": annual_dscr,
        "generator_year_one_revenue_usd": year_one["generator_revenue_usd"],
        "cfd_year_one_net_usd": cfd_net,
        "cfd_transfer_direction": (
            "buyer_to_seller" if cfd_net > 0
            else "seller_to_buyer" if cfd_net < 0
            else "zero"
        ),
    }
