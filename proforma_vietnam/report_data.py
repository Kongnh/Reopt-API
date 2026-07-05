def build_vietnam_report_data(reopt_results, cash_flow_result=None):
    cash_flow_result = cash_flow_result or {}
    inputs = reopt_results.get("inputs", {})
    outputs = reopt_results.get("outputs", {})

    pv_outputs = _as_list(outputs.get("PV"))
    storage_outputs = outputs.get("ElectricStorage") or {}
    utility_outputs = outputs.get("ElectricUtility") or {}
    load_inputs = inputs.get("ElectricLoad") or {}
    load_outputs = outputs.get("ElectricLoad") or {}
    tariff_outputs = outputs.get("ElectricTariff") or {}

    load_series = _series(load_outputs.get("load_series_kw")) or _series(load_inputs.get("loads_kw"))
    pv_to_load = _sum_series([pv.get("electric_to_load_series_kw", []) for pv in pv_outputs])
    pv_to_storage = _sum_series([pv.get("electric_to_storage_series_kw", []) for pv in pv_outputs])
    pv_curtailed = _sum_series([pv.get("electric_curtailed_series_kw", []) for pv in pv_outputs])
    pv_to_grid = _sum_series([pv.get("electric_to_grid_series_kw", []) for pv in pv_outputs])
    grid_to_load = _series(utility_outputs.get("electric_to_load_series_kw"))
    grid_to_storage = _series(utility_outputs.get("electric_to_storage_series_kw"))
    storage_to_load = _series(storage_outputs.get("storage_to_load_series_kw"))
    # Original PV generation before any dispatch split (load/storage/grid/curtailment).
    pv_total = _sum_series([pv_to_load, pv_to_storage, pv_to_grid, pv_curtailed])
    # Hourly solar resource signal: the PVWatts-derived production factor
    # (kWh per kW installed). REopt does not persist raw irradiance, so this
    # per-kW series is the irradiation proxy shown on the Dispatch sheet.
    production_factor = _production_factor_series(pv_outputs, _as_list(inputs.get("PV")))

    return {
        "system_sizing": {
            "pv_kw": sum(_value(pv, "size_kw") for pv in pv_outputs),
            "battery_kw": _value(storage_outputs, "size_kw"),
            "battery_kwh": _value(storage_outputs, "size_kwh"),
        },
        "dispatch_profile": _dispatch_rows(
            load_series=load_series,
            production_factor=production_factor,
            pv_total=pv_total,
            pv_to_load=pv_to_load,
            pv_to_storage=pv_to_storage,
            pv_to_grid=pv_to_grid,
            pv_curtailed=pv_curtailed,
            grid_to_load=grid_to_load,
            grid_to_storage=grid_to_storage,
            storage_to_load=storage_to_load,
        ),
        "annual_production": {
            "grid_to_load_kwh": sum(grid_to_load),
            "pv_to_load_kwh": sum(pv_to_load),
            "pv_to_storage_kwh": sum(pv_to_storage),
            "storage_to_load_kwh": sum(storage_to_load),
            "pv_curtailed_kwh": sum(pv_curtailed),
            "pv_to_grid_kwh": sum(pv_to_grid),
            # Effective grid export under DPPA = optimizer-determined export + would-be
            # curtailed surplus (the generator dumps everything at FMP, no curtailment).
            "pv_to_grid_effective_kwh": sum(pv_to_grid) + sum(pv_curtailed),
            "grid_to_storage_kwh": sum(grid_to_storage),
        },
        "results_comparison": _results_comparison(tariff_outputs),
        "load_duration": _load_duration(load_series, grid_to_load),
        "developer_financial_performance": cash_flow_result.get("summary", {}),
        "dppa_hourly_breakout": cash_flow_result.get("dppa_hourly_breakout", []),
        "dppa_monthly_breakout": cash_flow_result.get("dppa_monthly_breakout", []),
    }


def _dispatch_rows(*, load_series, production_factor, pv_total, pv_to_load,
                   pv_to_storage, pv_to_grid, pv_curtailed, grid_to_load,
                   grid_to_storage, storage_to_load):
    series = (load_series, production_factor, pv_total, pv_to_load,
              pv_to_storage, pv_to_grid, pv_curtailed, grid_to_load,
              grid_to_storage, storage_to_load)
    row_count = max((len(values) for values in series), default=0)
    rows = []
    for index in range(row_count):
        rows.append({
            "hour": index + 1,
            "load_kw": _at(load_series, index),
            "pv_production_factor": _at(production_factor, index),
            "pv_total_kw": _at(pv_total, index),
            "pv_to_load_kw": _at(pv_to_load, index),
            "pv_to_storage_kw": _at(pv_to_storage, index),
            "pv_to_grid_kw": _at(pv_to_grid, index),
            "pv_curtailed_kw": _at(pv_curtailed, index),
            "grid_to_load_kw": _at(grid_to_load, index),
            "grid_to_storage_kw": _at(grid_to_storage, index),
            "storage_to_load_kw": _at(storage_to_load, index),
        })
    return rows


def _production_factor_series(pv_outputs, pv_inputs):
    """First non-empty PVWatts production-factor series (kWh per kW installed)."""
    for pv in list(pv_outputs) + list(pv_inputs):
        series = _series((pv or {}).get("production_factor_series"))
        if series:
            return series
    return []


def _results_comparison(tariff_outputs):
    bau_bill = _value(tariff_outputs, "year_one_bill_before_tax_bau")
    optimized_bill = _value(tariff_outputs, "year_one_bill_before_tax")
    bau_demand = _value(tariff_outputs, "year_one_demand_cost_before_tax_bau")
    optimized_demand = _value(tariff_outputs, "year_one_demand_cost_before_tax")
    # REopt money outputs are USD (the EVN tariff is converted VND->USD at the
    # contract rate before the optimizer runs), so these keys carry the _usd
    # suffix — they are not VND amounts.
    return {
        "bau_utility_bill_usd": bau_bill,
        "optimized_utility_bill_usd": optimized_bill,
        "utility_bill_savings_usd": bau_bill - optimized_bill,
        "bau_demand_charge_usd": bau_demand,
        "optimized_demand_charge_usd": optimized_demand,
        "demand_charge_savings_usd": max(bau_demand - optimized_demand, 0),
    }


def _load_duration(load_series, grid_to_load):
    net_load = grid_to_load if grid_to_load else load_series
    rows = []
    for index, value in enumerate(sorted(load_series, reverse=True)):
        rows.append({
            "rank": index + 1,
            "load_kw": value,
            "net_load_kw": sorted(net_load, reverse=True)[index] if index < len(net_load) else 0,
        })
    return rows


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _sum_series(series_list):
    max_length = max((len(_series(series)) for series in series_list), default=0)
    totals = [0] * max_length
    for series in series_list:
        for index, value in enumerate(_series(series)):
            totals[index] += value
    return totals


def _series(value):
    return value if isinstance(value, list) else []


def _at(series, index):
    return series[index] if index < len(series) else 0


def _value(data, key):
    value = data.get(key)
    return value if value is not None else 0
