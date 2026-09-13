from proforma_vietnam.battery_soh import (
    DAYS_PER_YEAR,
    augmentation_cost_by_year,
    battery_state_of_health,
)
from proforma_vietnam.cash_flow import DEFAULT_PROJECT_YEARS, calculate_vietnam_esco_cash_flow
from proforma_vietnam.defaults import (
    BATTERY_AGEING_TREATMENT,
    BATTERY_AGEING_TREATMENTS,
    BESS_AUGMENTATION_PRICE_DECLINATION_RATE,
    BESS_CYCLE_LIFE_EFC,
    SURPLUS_EXPORT_DEFAULTS,
    surplus_export_price_vnd_per_kwh,
)
from proforma_vietnam.demand_charge import battery_demand_savings
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
    bess_cycle_life_efc = cash_flow_overrides.pop("bess_cycle_life_efc", BESS_CYCLE_LIFE_EFC)
    battery_ageing_treatment = cash_flow_overrides.pop(
        "battery_ageing_treatment", BATTERY_AGEING_TREATMENT
    )
    if battery_ageing_treatment not in BATTERY_AGEING_TREATMENTS:
        raise ValueError(
            "battery_ageing_treatment must be one of {}.".format(", ".join(BATTERY_AGEING_TREATMENTS))
        )
    augmentation_price_declination_rate = cash_flow_overrides.pop(
        "bess_augmentation_price_declination_rate", BESS_AUGMENTATION_PRICE_DECLINATION_RATE
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

    project_served_pv_kwh = _sum_series([
        pv.get("electric_to_load_series_kw", [])
        for pv in pv_outputs
    ])

    if storage_inputs.get("can_grid_charge") is False:
        project_served_pv_kwh = _sum_series([
            project_served_pv_kwh,
            storage_outputs.get("storage_to_load_series_kw", []),
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
            _value(tariff_outputs, "year_one_bill_before_tax"),
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

    # REopt returns levelized dispatch, so year_one_bill_before_tax and every
    # dispatch series already carry degradation. The cash flow then applies
    # (1 - deg)^y on its own axis, which counted degradation roughly twice
    # and understated savings by 4.10 percent (Thailand) / 4.95 percent
    # (Vietnam). Undo the levelization here so the cash flow's own degradation
    # is the only one applied.
    _apply_de_levelization(cash_flow_inputs, _levelization_factor(pv_outputs))

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
        # The settlement basis above is built straight from raw REopt dispatch
        # series, bypassing cash_flow_inputs and therefore _apply_de_levelization
        # above -- so it carries the same levelization as project_served_pv_kwh
        # and needs the same correction. load_kw is the customer's actual load,
        # not PV production, and is left alone.
        _apply_de_levelization_to_dispatch(dispatch, _levelization_factor(pv_outputs))
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
            cash_flow_inputs, surplus_export, pv_outputs, exchange_rate_vnd_per_usd
        )

    # Battery capacity fade (2026-09-12): the state-of-health curve replayed
    # from the solved dispatch and the year-1 battery quantities it derates.
    # Absent when the solve has no battery, which leaves the cash flow as it was.
    battery_fade = _battery_fade_inputs(
        storage_inputs=storage_inputs,
        storage_outputs=storage_outputs,
        utility_outputs=utility_outputs,
        pv_outputs=pv_outputs,
        load_series=_series(load_outputs.get("load_series_kw"))
            or _series(load_inputs.get("loads_kw")),
        tariff_inputs=tariff_inputs,
        rates=cash_flow_inputs["evn_energy_rates_vnd_per_kwh"],
        served_kwh=cash_flow_inputs["project_served_pv_kwh"],
        storage_in_served=storage_inputs.get("can_grid_charge") is False,
        direct_ownership_enabled=direct_ownership_enabled,
        battery_only=pv_capacity_kw == 0,
        esco_energy_discount_fraction=esco_energy_discount_fraction,
        levelization_factor=_levelization_factor(pv_outputs),
        time_steps_per_hour=cash_flow_inputs.get("time_steps_per_hour", 1),
        project_years=cash_flow_inputs.get("project_years", DEFAULT_PROJECT_YEARS),
        cycle_life_efc=bess_cycle_life_efc,
        ageing_treatment=battery_ageing_treatment,
        augmentation_price_declination_rate=augmentation_price_declination_rate,
        exchange_rate_vnd_per_usd=exchange_rate_vnd_per_usd,
        reopt_money_values_currency=tariff_money_values_currency,
    )
    if battery_fade is not None:
        cash_flow_inputs["battery_fade"] = battery_fade

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


def _apply_de_levelization(cash_flow_inputs, levelization_factor):
    """Undo REopt's levelization on the three quantities that carry it.

    ``project_served_pv_kwh`` is PV production, so it scales directly. The
    bills do not: BAU carries no PV and is a true first year, so it is the
    SAVINGS DELTA that is levelized. Scaling the optimized bill by
    1 / lambda would inflate the whole bill including the part PV never
    touched. Capex, debt and O&M are absent here on purpose; none of them
    depends on production.
    """
    if levelization_factor == 1.0:
        return

    served = cash_flow_inputs.get("project_served_pv_kwh")
    if served:
        cash_flow_inputs["project_served_pv_kwh"] = [
            value / levelization_factor for value in served
        ]

    for optimized_key, bau_key in (
        ("optimized_evn_bill_vnd", "bau_evn_bill_vnd"),
        ("optimized_demand_charge_vnd", "bau_demand_charge_vnd"),
    ):
        bau = cash_flow_inputs[bau_key]
        savings = bau - cash_flow_inputs[optimized_key]
        cash_flow_inputs[optimized_key] = bau - savings / levelization_factor


def _apply_de_levelization_to_dispatch(dispatch, levelization_factor):
    """Undo REopt's levelization on the grid-CfD DPPA settlement's raw dispatch.

    Unlike project_served_pv_kwh, this dispatch dict never passes through
    cash_flow_inputs, so _apply_de_levelization above never sees it. All five
    series come from the same levelized REopt solve, so all five need the
    same lambda division -- including the two storage series: the merged
    project_served_pv_kwh already folds storage_to_load in when the battery
    cannot grid-charge and de-levelizes the merge, so leaving storage out here
    would be inconsistent with that.
    """
    if levelization_factor == 1.0:
        return

    for key in (
        "pv_to_load_kw",
        "pv_to_grid_kw",
        "pv_curtailed_kw",
        "storage_to_load_kw",
        "storage_to_grid_kw",
    ):
        series = dispatch.get(key)
        if series:
            dispatch[key] = [value / levelization_factor for value in series]


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

    # Like the grid-CfD dispatch dict, these four series are read straight from
    # the levelized REopt outputs and never pass through cash_flow_inputs, so
    # _apply_de_levelization does not reach them. Both surplus_kwh and
    # annual_pv_output_kwh below derive from them, so without this the export
    # revenue would carry the same double count the rest of this module now
    # corrects. No current case enables surplus export, so this is a latent
    # path, but a latent read of a levelized series is how the other three
    # instances of this defect survived.
    levelization_factor = _levelization_factor(pv_outputs)

    def _raw(key):
        series = _sum_series([pv.get(key, []) for pv in pv_outputs])
        if levelization_factor == 1.0:
            return series
        return [value / levelization_factor for value in series]

    pv_to_load = _raw("electric_to_load_series_kw")
    pv_to_grid = _raw("electric_to_grid_series_kw")
    pv_to_storage = _raw("electric_to_storage_series_kw")
    pv_curtailed = _raw("electric_curtailed_series_kw")

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


def _battery_fade_inputs(*, storage_inputs, storage_outputs, utility_outputs, pv_outputs,
                         load_series, tariff_inputs, rates, served_kwh, storage_in_served,
                         direct_ownership_enabled, battery_only, esco_energy_discount_fraction,
                         levelization_factor, time_steps_per_hour, project_years,
                         cycle_life_efc, ageing_treatment, augmentation_price_declination_rate,
                         exchange_rate_vnd_per_usd, reopt_money_values_currency):
    """Year-1 battery quantities the cash flow derates by state of health.

    Storage series are de-levelized like project_served_pv_kwh; grid charging
    is a grid quantity and is left alone, as report_data does. Which quantity
    carries the battery's energy follows the structure's own accounting:
    inside the served series when the battery is PV-charged (ESCO revenue and
    the retail repurchase), as a net value when the solve books the whole bill
    delta (direct ownership, battery-only arbitrage), and not at all when an
    ESCO case has grid-charged storage beside PV (that value is not booked
    today either). ``rates`` are already in cash-flow currency; the demand
    counterfactual is in REopt money and is converted here. None when the
    solve has no battery or less than a year of storage series.
    """
    size_kwh = _value(storage_outputs, "size_kwh")
    discharge_raw = _series(storage_outputs.get("storage_to_load_series_kw"))
    soc = _series(storage_outputs.get("soc_series_fraction"))
    needed = DAYS_PER_YEAR * 24 * time_steps_per_hour
    if size_kwh <= 0 or len(discharge_raw) < needed or len(soc) < needed:
        return None
    discharge = [value / levelization_factor for value in discharge_raw]
    soh = battery_state_of_health(
        size_kwh=size_kwh,
        soc_series_fraction=soc,
        discharge_series_kw=discharge,
        time_steps_per_hour=time_steps_per_hour,
        project_years=project_years,
        cycle_life_efc=cycle_life_efc,
    )
    if soh is None:
        return None
    discharge_value = sum(kw * rate for kw, rate in zip(discharge, rates)) / time_steps_per_hour
    grid_to_storage = _series(utility_outputs.get("electric_to_storage_series_kw"))
    charge_cost = sum(kw * rate for kw, rate in zip(grid_to_storage, rates)) / time_steps_per_hour
    # Augmentation price path (2026-09-13): the installed USD/kWh declining a
    # fixed rate a year, REopt's own; the series is booked under "augment"
    # and reported under "derate".
    augmentation_price = _money(
        _value(storage_inputs, "installed_cost_per_kwh"),
        exchange_rate_vnd_per_usd, reopt_money_values_currency,
    )
    fade = {
        "soh_by_year": soh["soh_average_by_year"],
        "treatment": ageing_treatment,
        "augmentation_price_per_kwh_vnd": augmentation_price,
        "augmentation_price_declination_rate": augmentation_price_declination_rate,
        "augmentation_cost_by_year_vnd": augmentation_cost_by_year(
            soh["soh_fraction_by_day"], size_kwh, augmentation_price,
            augmentation_price_declination_rate, project_years,
        ),
        "energy_revenue_vnd": 0.0,
        "served_retail_value_vnd": 0.0,
        "unserved_energy_value_vnd": 0.0,
        "matched_energy_share": 0.0,
        "energy_attribution": "",
        "soh": {key: value for key, value in soh.items() if key != "soh_fraction_by_day"},
    }
    if storage_in_served:
        fade["energy_revenue_vnd"] = discharge_value * esco_energy_discount_fraction
        fade["served_retail_value_vnd"] = discharge_value
        total_served = sum(served_kwh)
        fade["matched_energy_share"] = sum(discharge) / total_served if total_served else 0.0
        fade["energy_attribution"] = "inside the served series (PV-charged storage)"
    elif direct_ownership_enabled or battery_only:
        fade["unserved_energy_value_vnd"] = max(discharge_value - charge_cost, 0.0)
        fade["energy_attribution"] = (
            "net retail value of battery energy (discharge at retail minus grid charging)"
        )
    else:
        fade["energy_attribution"] = (
            "not booked: grid-charged storage beside PV under an ESCO structure "
            "carries no attributed energy value in this model"
        )
    pv_available = _sum_series([
        _sum_series([
            _series(pv.get("electric_to_load_series_kw")),
            _series(pv.get("electric_to_storage_series_kw")),
            _series(pv.get("electric_curtailed_series_kw")),
            _series(pv.get("electric_to_grid_series_kw")),
        ])
        for pv in pv_outputs
    ]) or [0.0] * len(load_series)
    optimized_purchase = _sum_series([
        _series(utility_outputs.get("electric_to_load_series_kw")),
        grid_to_storage,
    ])
    demand = None
    if load_series and optimized_purchase:
        demand = battery_demand_savings(
            tariff_inputs, load_series, pv_available, optimized_purchase, time_steps_per_hour
        )
    if demand is None:
        fade["demand_savings_vnd"] = 0.0
        fade["demand_attribution"] = "none: unsupported tariff demand structure"
    else:
        fade["demand_savings_vnd"] = _money(
            demand / levelization_factor, exchange_rate_vnd_per_usd, reopt_money_values_currency
        )
        fade["demand_attribution"] = "counterfactual"
    return fade


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
