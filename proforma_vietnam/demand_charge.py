"""Year-1 demand charge recomputed from a grid purchase series.

Supports the two demand structures the cases use: REopt's coincident-peak
periods (PEA's on-peak kW charge) and monthly demand rates (EVN's capacity
charge). Anything else (URDB, TOU demand tiers, ratchets, lookback) returns
None so the caller can say the battery's demand relief was not attributed
rather than guess. The PV-only counterfactual needs no optimiser: with no
battery, PV serves load first and the grid covers the rest.
"""

DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

_UNSUPPORTED_KEYS = (
    "urdb_label",
    "urdb_response",
    "urdb_utility_name",
    "urdb_rate_name",
    "tou_demand_rates",
    "blended_annual_demand_rate",
    "monthly_demand_ratchet",
)


def demand_charge_from_series(tariff_inputs, grid_purchase_kw, time_steps_per_hour=1):
    """Demand cost of ``grid_purchase_kw`` under the tariff, or None if unsupported."""
    tariff_inputs = tariff_inputs or {}
    for key in _UNSUPPORTED_KEYS:
        if tariff_inputs.get(key):
            return None
    if tariff_inputs.get("demand_lookback_percent"):
        return None
    cost = 0.0
    rates = tariff_inputs.get("coincident_peak_load_charge_per_kw") or []
    periods = tariff_inputs.get("coincident_peak_load_active_time_steps") or []
    for rate, steps in zip(rates, periods):
        if steps:
            # REopt time steps are 1-based.
            cost += rate * max(grid_purchase_kw[step - 1] for step in steps)
    monthly = tariff_inputs.get("monthly_demand_rates") or []
    if any(monthly):
        steps_per_day = 24 * time_steps_per_hour
        start = 0
        for days, rate in zip(DAYS_IN_MONTH, monthly):
            end = start + days * steps_per_day
            window = grid_purchase_kw[start:end]
            if window:
                cost += rate * max(window)
            start = end
    return cost


def battery_demand_savings(tariff_inputs, load_kw, pv_available_kw, optimized_purchase_kw,
                           time_steps_per_hour=1):
    """Demand cost the battery removed: PV-only counterfactual minus the solved purchase.

    Floored at zero; None when the tariff's demand structure is not supported.
    """
    counterfactual = [max(load - pv, 0.0) for load, pv in zip(load_kw, pv_available_kw)]
    without = demand_charge_from_series(tariff_inputs, counterfactual, time_steps_per_hour)
    with_battery = demand_charge_from_series(
        tariff_inputs, optimized_purchase_kw, time_steps_per_hour
    )
    if without is None or with_battery is None:
        return None
    return max(without - with_battery, 0.0)
