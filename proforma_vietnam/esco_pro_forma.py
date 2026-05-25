from proforma_vietnam.cash_flow import calculate_vietnam_esco_cash_flow


def calculate_esco_pro_forma_from_reopt_results(
    reopt_results,
    esco_energy_discount_fraction,
    **cash_flow_overrides
):
    inputs = reopt_results.get("inputs", {})
    outputs = reopt_results.get("outputs", {})

    pv_outputs = _as_list(outputs.get("PV"))
    storage_inputs = inputs.get("ElectricStorage") or {}
    storage_outputs = outputs.get("ElectricStorage") or {}
    tariff_inputs = inputs.get("ElectricTariff") or {}
    tariff_outputs = outputs.get("ElectricTariff") or {}
    financial_inputs = inputs.get("Financial") or {}
    financial_outputs = outputs.get("Financial") or {}

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
        "evn_energy_rates_vnd_per_kwh": tariff_inputs.get("tou_energy_rates_per_kwh", []),
        "bau_evn_bill_vnd": _value(tariff_outputs, "year_one_bill_before_tax_bau"),
        "optimized_evn_bill_vnd": _value(tariff_outputs, "year_one_bill_before_tax"),
        "bau_demand_charge_vnd": _value(tariff_outputs, "year_one_demand_cost_before_tax_bau"),
        "optimized_demand_charge_vnd": _value(tariff_outputs, "year_one_demand_cost_before_tax"),
        "pv_capex_vnd": _pv_capex(pv_outputs),
        "bess_capex_vnd": _storage_capex(storage_inputs, storage_outputs),
        "annual_om_vnd": _value(financial_outputs, "year_one_om_costs_before_tax"),
        "esco_energy_discount_fraction": esco_energy_discount_fraction,
        "owner_discount_rate_fraction": financial_inputs.get("owner_discount_rate_fraction", 0.10),
    }
    cash_flow_inputs.update(cash_flow_overrides)

    return calculate_vietnam_esco_cash_flow(**cash_flow_inputs)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


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
