from proforma_vietnam.cash_flow import calculate_vietnam_esco_cash_flow
from proforma_vietnam.dppa_settlement import (
    DPPA_TYPE_GRID_CFD,
    DPPA_TYPE_NONE,
    settle_dppa_year_one,
)


def calculate_esco_pro_forma_from_reopt_results(
    reopt_results,
    esco_energy_discount_fraction,
    **cash_flow_overrides
):
    exchange_rate_vnd_per_usd = cash_flow_overrides.pop("exchange_rate_vnd_per_usd", None)
    tariff_money_values_currency = cash_flow_overrides.pop("tariff_money_values_currency", "usd")
    tariff_money_values_currency = cash_flow_overrides.pop(
        "reopt_money_values_currency",
        tariff_money_values_currency,
    )
    dppa_inputs = cash_flow_overrides.pop("dppa_inputs", None)
    inputs = reopt_results.get("inputs", {})
    outputs = reopt_results.get("outputs", {})

    pv_outputs = _as_list(outputs.get("PV"))
    storage_inputs = inputs.get("ElectricStorage") or {}
    storage_outputs = outputs.get("ElectricStorage") or {}
    tariff_inputs = inputs.get("ElectricTariff") or {}
    tariff_outputs = outputs.get("ElectricTariff") or {}
    financial_inputs = inputs.get("Financial") or {}
    financial_outputs = outputs.get("Financial") or {}
    utility_outputs = outputs.get("ElectricUtility") or {}
    load_outputs = outputs.get("ElectricLoad") or {}
    load_inputs = inputs.get("ElectricLoad") or {}

    project_served_pv_kwh = _sum_series([
        pv.get("electric_to_load_series_kw", [])
        for pv in pv_outputs
    ])

    if storage_inputs.get("can_grid_charge") is False:
        project_served_pv_kwh = _sum_series([
            project_served_pv_kwh,
            storage_outputs.get("storage_to_load_series_kw", []),
        ])

    cash_flow_inputs = {
        "project_served_pv_kwh": project_served_pv_kwh,
        "evn_energy_rates_vnd_per_kwh": _money_series(
            tariff_inputs.get("tou_energy_rates_per_kwh", []),
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        "bau_evn_bill_vnd": _money(
            _value(tariff_outputs, "year_one_bill_before_tax_bau"),
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        "optimized_evn_bill_vnd": _money(
            _value(tariff_outputs, "year_one_bill_before_tax"),
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        "bau_demand_charge_vnd": _money(
            _value(tariff_outputs, "year_one_demand_cost_before_tax_bau"),
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        "optimized_demand_charge_vnd": _money(
            _value(tariff_outputs, "year_one_demand_cost_before_tax"),
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        "pv_capex_vnd": _pv_capex(pv_outputs),
        "bess_capex_vnd": _storage_capex(storage_inputs, storage_outputs),
        "annual_om_vnd": _value(financial_outputs, "year_one_om_costs_before_tax"),
        "esco_energy_discount_fraction": esco_energy_discount_fraction,
        "owner_discount_rate_fraction": financial_inputs.get("owner_discount_rate_fraction", 0.10),
    }
    cash_flow_inputs.update(cash_flow_overrides)

    if dppa_inputs is not None and dppa_inputs.get("type", DPPA_TYPE_NONE) == DPPA_TYPE_GRID_CFD:
        evn_rates_vnd = _money_series(
            tariff_inputs.get("tou_energy_rates_per_kwh", []),
            exchange_rate_vnd_per_usd,
            "vnd",
        ) if tariff_money_values_currency == "vnd" else [
            value * (exchange_rate_vnd_per_usd or 1.0)
            for value in tariff_inputs.get("tou_energy_rates_per_kwh", [])
        ]
        dispatch = {
            "load_kw": _series(load_outputs.get("load_series_kw"))
                or _series(load_inputs.get("loads_kw")),
            "pv_to_load_kw": _sum_series([
                pv.get("electric_to_load_series_kw", []) for pv in pv_outputs
            ]),
            "pv_to_grid_kw": _sum_series([
                pv.get("electric_to_grid_series_kw", []) for pv in pv_outputs
            ]),
            # Curtailed PV is treated as DPPA grid export per the design clarified
            # in case_5: optimizer runs self-consumption, the generator dumps any
            # surplus to grid at FMP rather than curtailing.
            "pv_curtailed_kw": _sum_series([
                pv.get("electric_curtailed_series_kw", []) for pv in pv_outputs
            ]),
            "storage_to_load_kw": _series(storage_outputs.get("storage_to_load_series_kw")),
            "storage_to_grid_kw": _series(storage_outputs.get("storage_to_grid_series_kw")),
        }
        dppa_settlement = settle_dppa_year_one(
            dppa_inputs=dppa_inputs,
            dispatch=dispatch,
            evn_energy_rates_vnd_per_kwh=evn_rates_vnd,
        )
        if exchange_rate_vnd_per_usd:
            dppa_settlement = _convert_dppa_year_one_to_cash_flow_currency(
                dppa_settlement, exchange_rate_vnd_per_usd
            )
        cash_flow_inputs["dppa_settlement"] = dppa_settlement

    return calculate_vietnam_esco_cash_flow(**cash_flow_inputs)


def _convert_dppa_year_one_to_cash_flow_currency(dppa_settlement, exchange_rate_vnd_per_usd):
    # DPPA primitives come from FMP (VND/kWh) × kWh and are intrinsically VND.
    # The surrounding cash flow runs in the same currency as Phase 2 (USD after
    # _money() normalization), so the year-one totals must be divided before
    # they flow into _dppa_year_terms — otherwise offtaker_savings mixes units.
    # Hourly/monthly breakouts are display-only for the VND-labelled workbook
    # sheets and stay in VND.
    converted = dict(dppa_settlement)
    converted["esco_energy_revenue_vnd"] = (
        dppa_settlement.get("esco_energy_revenue_vnd", 0.0) / exchange_rate_vnd_per_usd
    )
    year_one = dict(dppa_settlement["year_one"])
    for key, value in list(year_one.items()):
        if key.endswith("_vnd"):
            year_one[key] = value / exchange_rate_vnd_per_usd
    converted["year_one"] = year_one
    return converted


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _series(value):
    return value if isinstance(value, list) else []


def _sum_series(series_list):
    max_length = max((len(series) for series in series_list), default=0)
    totals = [0] * max_length

    for series in series_list:
        for index, value in enumerate(series):
            totals[index] += value

    return totals


def _pv_capex(pv_outputs):
    return sum(
        _value(pv, "size_kw") * _value(pv, "installed_cost_per_kw")
        for pv in pv_outputs
    )


def _storage_capex(storage_inputs, storage_outputs):
    if storage_outputs.get("initial_capital_cost") is not None:
        return storage_outputs["initial_capital_cost"]

    size_kw = _value(storage_outputs, "size_kw")
    size_kwh = _value(storage_outputs, "size_kwh")
    return (
        size_kw * _value(storage_inputs, "installed_cost_per_kw")
        + size_kwh * _value(storage_inputs, "installed_cost_per_kwh")
        + _value(storage_inputs, "installed_cost_constant")
    )


def _value(data, key):
    value = data.get(key)
    return value if value is not None else 0


def _money(value, exchange_rate_vnd_per_usd, reopt_money_values_currency):
    if reopt_money_values_currency == "usd":
        return value
    if reopt_money_values_currency == "vnd":
        if not exchange_rate_vnd_per_usd:
            raise ValueError("exchange_rate_vnd_per_usd is required when REopt money values are VND.")
        return value / exchange_rate_vnd_per_usd
    raise ValueError("tariff_money_values_currency must be 'usd' or 'vnd'.")


def _money_series(values, exchange_rate_vnd_per_usd, reopt_money_values_currency):
    return [
        _money(value, exchange_rate_vnd_per_usd, reopt_money_values_currency)
        for value in values
    ]
