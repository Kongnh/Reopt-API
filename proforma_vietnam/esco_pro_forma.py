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
    direct_ownership = cash_flow_overrides.pop("direct_ownership", None)
    battery_replacement_year = cash_flow_overrides.pop("battery_replacement_year", None)
    extra_replacement_costs = cash_flow_overrides.pop(
        "extra_replacement_costs_by_year", None
    )
    pv_inverter_year = cash_flow_overrides.pop("pv_inverter_replacement_year", None)
    pv_inverter_fraction = cash_flow_overrides.pop(
        "pv_inverter_replacement_fraction_of_pv_capex", None
    )
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

    # Every energy quantity below reads this first-year restatement of
    # REopt's levelized dispatch, never the raw series (see
    # _year_one_dispatch).
    year_one = _year_one_dispatch(reopt_results)
    project_served_pv_kwh = year_one["pv_to_load_kw"]

    if storage_inputs.get("can_grid_charge") is False:
        project_served_pv_kwh = _sum_series([
            project_served_pv_kwh,
            year_one["storage_to_load_kw"],
        ])

    tou_rates = tariff_inputs.get("tou_energy_rates_per_kwh", [])
    if not project_served_pv_kwh and tou_rates:
        # No PV tech in the run (battery-only case): an empty served series
        # would trip the cash flow's length check, so serve zeros over the
        # tariff horizon instead.
        project_served_pv_kwh = [0.0] * len(tou_rates)

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
            _value(tariff_outputs, "year_one_bill_before_tax")
            - year_one["avoided_energy_cost"],
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        # A coincident-peak demand structure (PEA's on-peak kW charge) is
        # booked by REopt under year_one_coincident_peak_cost_before_tax, not
        # year_one_demand_cost_before_tax (Important 7) -- every Vietnam
        # baseline case has that field at 0.0, so adding it in only changes
        # anything for a tariff actually billed on coincident peak.
        "bau_demand_charge_vnd": _money(
            _value(tariff_outputs, "year_one_demand_cost_before_tax_bau")
            + _value(tariff_outputs, "year_one_coincident_peak_cost_before_tax_bau"),
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        "optimized_demand_charge_vnd": _money(
            _value(tariff_outputs, "year_one_demand_cost_before_tax")
            + _value(tariff_outputs, "year_one_coincident_peak_cost_before_tax"),
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        ),
        "pv_capex_vnd": _pv_capex(pv_outputs),
        "bess_capex_vnd": _storage_capex(storage_inputs, storage_outputs),
        "annual_om_vnd": _value(financial_outputs, "year_one_om_costs_before_tax"),
        "esco_energy_discount_fraction": esco_energy_discount_fraction,
        "owner_discount_rate_fraction": financial_inputs.get("owner_discount_rate_fraction", 0.10),
    }

    pv_capacity_kw = sum(_value(pv, "size_kw") for pv in pv_outputs)
    if storage_inputs.get("can_grid_charge") is True and pv_capacity_kw == 0:
        # Battery-only grid-charging case: with no PV, every discharged kWh was
        # grid-charged, so the whole energy-bill delta IS the net grid-arbitrage
        # value (the demand-charge movement is booked on its own line and
        # excluded here). This sidesteps the PV-vs-grid attribution problem the
        # design doc defers; with PV present the value stays 0 unless an
        # explicit override provides it.
        cash_flow_inputs["net_grid_arbitrage_value_vnd"] = (
            cash_flow_inputs["bau_evn_bill_vnd"]
            - cash_flow_inputs["optimized_evn_bill_vnd"]
        ) - (
            cash_flow_inputs["bau_demand_charge_vnd"]
            - cash_flow_inputs["optimized_demand_charge_vnd"]
        )

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
    # Shared replacement policy: one PV inverter event at a fraction of the
    # SOLVED PV capex, derived here so both countries book it from one place.
    # Added, never assigned: a bare override would delete the BESS event.
    pv_inverter_replacement = _pv_inverter_replacement(
        pv_outputs, pv_inverter_year, pv_inverter_fraction
    )
    if pv_inverter_replacement is not None:
        cash_flow_inputs["replacement_costs_by_year"] = _merge_replacement_costs(
            cash_flow_inputs.get("replacement_costs_by_year"),
            _money_series(
                pv_inverter_replacement["series"],
                exchange_rate_vnd_per_usd,
                tariff_money_values_currency,
            ),
        )
    if extra_replacement_costs:
        # Added, not assigned: a bare override would silently delete the BESS
        # replacement derived above.
        cash_flow_inputs["replacement_costs_by_year"] = _merge_replacement_costs(
            cash_flow_inputs.get("replacement_costs_by_year"),
            _money_series(
                extra_replacement_costs,
                exchange_rate_vnd_per_usd,
                tariff_money_values_currency,
            ),
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
            cash_flow_inputs, dppa_inputs, year_one, exchange_rate_vnd_per_usd
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
            "pv_to_load_kw": year_one["pv_to_load_kw"],
            "pv_to_grid_kw": year_one["pv_to_grid_kw"],
            # Curtailed PV is treated as DPPA grid export per the design clarified
            # in case_5: optimizer runs self-consumption, the generator dumps any
            # surplus to grid at FMP rather than curtailing.
            "pv_curtailed_kw": year_one["pv_curtailed_kw"],
            "storage_to_load_kw": year_one["storage_to_load_kw"],
            "storage_to_grid_kw": year_one["storage_to_grid_kw"],
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

    direct_ownership_enabled = direct_ownership is not None and (
        not isinstance(direct_ownership, dict) or direct_ownership.get("enabled", True)
    )
    if direct_ownership_enabled:
        # Factory self-invest benchmark. Mutually exclusive with any DPPA block
        # (the factory owns the asset, there is no generator/offtaker split);
        # the top-level Decree 243 surplus_export IS allowed here (the factory is
        # the rooftop owner) and rides on the shared 3a machinery below.
        if dppa_inputs is not None and dppa_inputs.get("type", DPPA_TYPE_NONE) != DPPA_TYPE_NONE:
            raise ValueError(
                "direct_ownership (factory self-invest) cannot be combined with a "
                "DPPA block (grid CfD or private wire)."
            )
        _apply_direct_ownership(cash_flow_inputs, direct_ownership)

    if surplus_export is not None and surplus_export.get("enabled"):
        _apply_surplus_export(
            cash_flow_inputs, surplus_export, year_one, exchange_rate_vnd_per_usd
        )

    # The inputs above are normalized to USD; passing the FX rate through lets
    # the cash flow restate every _vnd key at the fixed contract rate instead
    # of aliasing USD values under VND labels.
    cash_flow_inputs.setdefault("exchange_rate_vnd_per_usd", exchange_rate_vnd_per_usd)

    result = calculate_vietnam_esco_cash_flow(**cash_flow_inputs)
    if pv_inverter_replacement is not None:
        result["derivation"]["pv_inverter_replacement"] = {
            "year": pv_inverter_replacement["year"],
            "fraction": pv_inverter_replacement["fraction"],
            "cost_usd": _money(
                pv_inverter_replacement["cost"],
                exchange_rate_vnd_per_usd,
                tariff_money_values_currency,
            ),
        }
    return result


def _levelization_factor(pv_outputs):
    """Ratio of REopt's levelized annual PV production to its raw first year.

    REopt applies this weighting to the PV production parameter inside the
    optimisation, so every dispatch series and the bill computed from them
    carry it, despite the "year_one" prefix on their names. Dividing by this
    factor recovers a true first year for the proforma to degrade on its own
    time axis. Returns 1.0 whenever there is no usable production, which
    leaves battery-only cases untouched.
    """
    raw = sum(_value(pv, "year_one_energy_produced_kwh") for pv in pv_outputs)
    levelized = sum(_value(pv, "annual_energy_produced_kwh") for pv in pv_outputs)
    if raw <= 0 or levelized <= 0:
        return 1.0
    return levelized / raw


def _year_one_dispatch(reopt_results):
    """REopt's solved dispatch restated on a true first-year PV basis.

    REopt solves on PV production weighted by _levelization_factor (lambda),
    so the first year produces 1 / lambda times what the dispatch shows. The
    extra energy is placed interval by interval: it first displaces grid
    import in the same interval and the rest is curtailed, while the battery
    keeps its solved schedule. The load balance therefore still closes.

    Until 2026-09-28 every PV and storage flow and the savings delta were
    divided by lambda instead. Against a REopt re-solve at lambda = 1 that
    overstated first-year savings by 2.8-3.9 percent (factory_a_v2, five
    cases): most of the extra PV lands in hours that already curtail, the
    battery is bounded by its own size, and the grid flow stayed levelized,
    so the first-year energy table summed to 9.58 GWh against a 9.34 GWh
    load. Holding the battery fixed lands 0-0.9 percent below the re-solve,
    the conservative side.

    Demand-side quantities (the demand charge, billed peaks) stay on the
    solved dispatch: extra PV can only lower a peak, so that is conservative
    too. Series are kW per interval; money is in REopt's own currency.
    """
    inputs = reopt_results.get("inputs", {})
    outputs = reopt_results.get("outputs", {})
    pv_outputs = _as_list(outputs.get("PV"))
    storage_outputs = outputs.get("ElectricStorage") or {}
    utility_outputs = outputs.get("ElectricUtility") or {}

    def pv_series(key):
        return _sum_series([_series(pv.get(key)) for pv in pv_outputs])

    dispatch = {
        "pv_to_load_kw": pv_series("electric_to_load_series_kw"),
        "pv_to_storage_kw": pv_series("electric_to_storage_series_kw"),
        "pv_to_grid_kw": pv_series("electric_to_grid_series_kw"),
        "pv_curtailed_kw": pv_series("electric_curtailed_series_kw"),
        "storage_to_load_kw": _series(storage_outputs.get("storage_to_load_series_kw")),
        "storage_to_grid_kw": _series(storage_outputs.get("storage_to_grid_series_kw")),
        "grid_to_load_kw": _series(utility_outputs.get("electric_to_load_series_kw")),
        "grid_to_storage_kw": _series(utility_outputs.get("electric_to_storage_series_kw")),
        "avoided_grid_kwh": 0.0,
        "avoided_energy_cost": 0.0,
    }
    levelization_factor = _levelization_factor(pv_outputs)
    if levelization_factor == 1.0:
        return dispatch

    pv_total = _sum_series([
        dispatch["pv_to_load_kw"],
        dispatch["pv_to_storage_kw"],
        dispatch["pv_to_grid_kw"],
        dispatch["pv_curtailed_kw"],
    ])
    grid_to_load = dispatch["grid_to_load_kw"]
    extra = [value * (1 / levelization_factor - 1) for value in pv_total]
    absorbed = [
        min(value, grid_to_load[index]) if index < len(grid_to_load) else 0.0
        for index, value in enumerate(extra)
    ]
    rates = _series(
        (inputs.get("ElectricTariff") or {}).get("tou_energy_rates_per_kwh")
    )
    if any(absorbed) and len(rates) != len(absorbed):
        raise ValueError(
            "Restating the dispatch on a first-year basis needs "
            "tou_energy_rates_per_kwh at the dispatch resolution "
            "({} rates for {} intervals).".format(len(rates), len(absorbed))
        )
    time_steps_per_hour = (inputs.get("Settings") or {}).get("time_steps_per_hour") or 1

    dispatch["pv_to_load_kw"] = _sum_series([dispatch["pv_to_load_kw"], absorbed])
    dispatch["pv_curtailed_kw"] = _sum_series([
        dispatch["pv_curtailed_kw"],
        [value - taken for value, taken in zip(extra, absorbed)],
    ])
    dispatch["grid_to_load_kw"] = [
        value - (absorbed[index] if index < len(absorbed) else 0.0)
        for index, value in enumerate(grid_to_load)
    ]
    dispatch["avoided_grid_kwh"] = sum(absorbed) / time_steps_per_hour
    dispatch["avoided_energy_cost"] = sum(
        taken * rate for taken, rate in zip(absorbed, rates)
    ) / time_steps_per_hour
    return dispatch


def _apply_physical_dppa(cash_flow_inputs, dppa_inputs, year_one, exchange_rate_vnd_per_usd):
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
            cash_flow_inputs, nested_surplus, year_one, exchange_rate_vnd_per_usd
        )


def _apply_direct_ownership(cash_flow_inputs, direct_ownership):
    """Flag a factory self-invest (DIRECT_OWNERSHIP) run for the cash flow.

    The benefit is the full avoided EVN bill (bau − optimized), so the ESCO
    bau/optimized bill, O&M and replacement extraction above are reused
    unchanged — only the structure flag, the flat-CIT default and the
    profitable-host convention differ. The ESCO discount fraction / demand-split
    inputs, if present, are ignored (the factory captures the whole bill).
    An optional ``assume_profitable_host`` and ``cit_regime`` override ride in
    the block; the cash flow defaults the host convention on and the regime to
    ``standard_flat``.
    """
    config = direct_ownership if isinstance(direct_ownership, dict) else {}
    block = {}
    if config.get("assume_profitable_host") is not None:
        block["assume_profitable_host"] = config["assume_profitable_host"]
    cash_flow_inputs["direct_ownership"] = block
    if config.get("cit_regime") is not None:
        cash_flow_inputs["cit_regime"] = config["cit_regime"]


def _apply_surplus_export(cash_flow_inputs, surplus_export, year_one, exchange_rate_vnd_per_usd):
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

    # The first-year dispatch (_year_one_dispatch), never the raw levelized
    # series: both surplus_kwh and annual_pv_output_kwh derive from it. No
    # current case enables surplus export, so this is a latent path, but a
    # latent read of a levelized series is how earlier instances of this
    # defect survived.
    pv_to_load = year_one["pv_to_load_kw"]
    pv_to_grid = year_one["pv_to_grid_kw"]
    pv_to_storage = year_one["pv_to_storage_kw"]
    pv_curtailed = year_one["pv_curtailed_kw"]

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


def _pv_inverter_replacement(pv_outputs, year, fraction):
    """One PV inverter event at ``fraction`` of the solved PV capex in ``year``.

    Returns None when either policy value is unset or the run has no PV, so a
    battery-only case books nothing and a caller that never adopted the policy
    is unchanged. Money is in REopt's own currency here; the caller converts.
    """
    if not year or not fraction:
        return None
    cost = _pv_capex(pv_outputs) * fraction
    if cost <= 0:
        return None
    series = [0.0] * int(year)
    series[int(year) - 1] = cost
    return {"year": int(year), "fraction": fraction, "cost": cost, "series": series}


def _merge_replacement_costs(base, extra):
    """Element-wise sum of two replacement-cost series, either of which may be None.

    Overriding replacement_costs_by_year wholesale would drop the BESS
    replacement derived from the REopt inputs. Thailand books an inverter
    replacement alongside it, so the two must add rather than compete.
    """
    base = list(base or [])
    extra = list(extra or [])
    length = max(len(base), len(extra))
    return [
        (base[i] if i < len(base) else 0.0) + (extra[i] if i < len(extra) else 0.0)
        for i in range(length)
    ]


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
