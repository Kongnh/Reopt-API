from proforma_vietnam.cash_flow import calculate_vietnam_esco_cash_flow
from proforma_vietnam.defaults import (
    SURPLUS_EXPORT_DEFAULTS,
    surplus_export_price_vnd_per_kwh,
)
from proforma_vietnam.dppa_settlement import (
    DPPA_TYPE_GRID_CFD,
    DPPA_TYPE_NONE,
    DPPA_TYPE_PHYSICAL_PRIVATE_WIRE,
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
    surplus_export = cash_flow_overrides.pop("surplus_export", None)
    battery_replacement_year = cash_flow_overrides.pop("battery_replacement_year", None)
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

    pv_input_list = _as_list(inputs.get("PV"))
    degradation_rates = [
        pv.get("degradation_fraction")
        for pv in pv_input_list
        if pv.get("degradation_fraction")
    ]
    if degradation_rates:
        cash_flow_inputs["pv_degradation_rate"] = max(degradation_rates)

    replacement_costs = _bess_replacement_costs(
        storage_inputs, storage_outputs, battery_replacement_year
    )
    if replacement_costs is not None:
        cash_flow_inputs["replacement_costs_by_year"] = _money_series(
            replacement_costs,
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        )

    cash_flow_inputs.update(cash_flow_overrides)

    is_physical = (
        dppa_inputs is not None
        and dppa_inputs.get("type") == DPPA_TYPE_PHYSICAL_PRIVATE_WIRE
    )
    if is_physical:
        # ND57 Điều 25 private wire: no grid-CfD settlement. The surplus leg is
        # nested inside the physical block, so the standalone 3a top-level
        # surplus_export config is not accepted here (it stays ESCO-only).
        if surplus_export is not None:
            raise ValueError(
                "top-level surplus_export config is ESCO-only; under a physical "
                "private-wire DPPA the surplus rides inside the physical_dppa block."
            )
        _apply_physical_dppa(
            cash_flow_inputs, dppa_inputs, pv_outputs, exchange_rate_vnd_per_usd
        )
    elif dppa_inputs is not None and dppa_inputs.get("type", DPPA_TYPE_NONE) == DPPA_TYPE_GRID_CFD:
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

    if surplus_export is not None and surplus_export.get("enabled"):
        _apply_surplus_export(
            cash_flow_inputs, surplus_export, pv_outputs, exchange_rate_vnd_per_usd
        )

    # The inputs above are normalized to USD; passing the FX rate through lets
    # the cash flow restate every _vnd key at the fixed contract rate instead
    # of aliasing USD values under VND labels.
    cash_flow_inputs.setdefault("exchange_rate_vnd_per_usd", exchange_rate_vnd_per_usd)

    return calculate_vietnam_esco_cash_flow(**cash_flow_inputs)


def _apply_physical_dppa(cash_flow_inputs, dppa_inputs, pv_outputs, exchange_rate_vnd_per_usd):
    """Resolve ND57 Điều 25 private-wire DPPA primitives into the cash flow.

    Matched energy is the project-served series REopt already produced
    (PV→load, plus battery→load when the battery cannot grid-charge — the same
    basis as the ESCO energy stream); the buyer pays it at the freely negotiated
    PPA price (Decree 243/2026 removed the ceiling), converted VND→USD at the
    contract FX. A nested, optional ``surplus_export`` sub-block monetizes the
    export leg with Task 3a's cap/pricing machinery.
    """
    ppa_price_vnd = dppa_inputs.get("ppa_price_vnd_per_kwh")
    if ppa_price_vnd is None:
        raise ValueError(
            "physical_private_wire DPPA requires 'ppa_price_vnd_per_kwh'."
        )
    # The PPA price is a VND/kWh contract quantity; the cash flow runs in the
    # contract-FX model currency, so convert like every other VND money input.
    ppa_price_usd = (
        ppa_price_vnd / exchange_rate_vnd_per_usd
        if exchange_rate_vnd_per_usd
        else ppa_price_vnd
    )
    matched_kwh_year1 = sum(cash_flow_inputs["project_served_pv_kwh"])
    cash_flow_inputs["physical_dppa"] = {
        "matched_kwh_year1": matched_kwh_year1,
        "ppa_price_usd_per_kwh": ppa_price_usd,
        "ppa_price_escalation_rate": dppa_inputs.get("ppa_price_escalation_rate", 0.0),
    }

    nested_surplus = dppa_inputs.get("surplus_export")
    if nested_surplus is not None and nested_surplus.get("enabled"):
        _apply_surplus_export(
            cash_flow_inputs, nested_surplus, pv_outputs, exchange_rate_vnd_per_usd
        )


def _apply_surplus_export(cash_flow_inputs, surplus_export, pv_outputs, exchange_rate_vnd_per_usd):
    """Resolve Decree 243/2026 surplus-export primitives into the cash flow.

    Surplus = PV grid export + would-be-curtailed energy (the ESCO sells it to
    EVN, mirroring the DPPA branch's pv_to_grid_effective treatment). The sold
    quantity is capped at ``cap_fraction`` of total PV output; the price is the
    explicit VND/kWh or the region's Decree 243 ceiling-capped market price,
    converted to the model currency at the contract FX.
    """
    if "dppa_settlement" in cash_flow_inputs:
        # Under DPPA the export energy is already monetized at FMP; a surplus
        # line would double-count it.
        raise ValueError(
            "surplus export cannot be combined with a DPPA settlement "
            "(export energy is already monetized at FMP)."
        )

    pv_to_load = _sum_series([pv.get("electric_to_load_series_kw", []) for pv in pv_outputs])
    pv_to_grid = _sum_series([pv.get("electric_to_grid_series_kw", []) for pv in pv_outputs])
    pv_to_storage = _sum_series([pv.get("electric_to_storage_series_kw", []) for pv in pv_outputs])
    pv_curtailed = _sum_series([pv.get("electric_curtailed_series_kw", []) for pv in pv_outputs])

    surplus_kwh = sum(pv_to_grid) + sum(pv_curtailed)
    annual_pv_output_kwh = (
        sum(pv_to_load) + sum(pv_to_grid) + sum(pv_to_storage) + sum(pv_curtailed)
    )

    cap_fraction = surplus_export.get("cap_fraction")
    if cap_fraction is None:
        cap_fraction = SURPLUS_EXPORT_DEFAULTS["cap_fraction_of_output"]
    sold_kwh = min(surplus_kwh, cap_fraction * annual_pv_output_kwh)

    price_vnd = surplus_export.get("price_vnd_per_kwh")
    if price_vnd is None:
        region = surplus_export.get("region")
        if not region:
            raise ValueError(
                "surplus_export requires 'region' when 'price_vnd_per_kwh' is not given."
            )
        price_vnd = surplus_export_price_vnd_per_kwh(region)
    # The price is a VND/kWh regulatory quantity; the cash flow runs in the
    # contract-FX model currency, so convert like every other VND money input.
    price_usd = (
        price_vnd / exchange_rate_vnd_per_usd if exchange_rate_vnd_per_usd else price_vnd
    )

    cash_flow_inputs["surplus_export_kwh_year1"] = sold_kwh
    cash_flow_inputs["surplus_export_price_usd_per_kwh"] = price_usd
    cash_flow_inputs["surplus_price_escalation_rate"] = surplus_export.get("price_escalation_rate")
    cash_flow_inputs["surplus_cap_fraction"] = cap_fraction


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


def _bess_replacement_costs(storage_inputs, storage_outputs, replacement_year_override=None):
    """Battery replacement schedule derived from REopt replacement inputs.

    REopt carries replace_cost_per_kw / replace_cost_per_kwh and
    battery_replacement_year on ElectricStorage inputs; the proforma books the
    replacement as an expense in that year. An explicit override wins over the
    year echoed in saved results so the schedule can change without a re-run.
    """
    replacement_year = (
        replacement_year_override
        if replacement_year_override is not None
        else storage_inputs.get("battery_replacement_year")
    )
    if not replacement_year or replacement_year < 1:
        return None

    cost = (
        _value(storage_outputs, "size_kw") * _value(storage_inputs, "replace_cost_per_kw")
        + _value(storage_outputs, "size_kwh") * _value(storage_inputs, "replace_cost_per_kwh")
        + _value(storage_inputs, "replace_cost_constant")
    )
    if cost <= 0:
        return None

    costs = [0.0] * int(replacement_year)
    costs[int(replacement_year) - 1] = cost
    return costs


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
