"""Render the Thailand proforma workbook.

Drives the proforma_vietnam engine with THAILAND_PROFILE. Money keys keep their
historical ``_vnd`` suffix and carry THB (see the spec's section 2); only the
rendered labels change, and a test asserts no VND or EVN string survives.

Power factor is handled per spec section 4: compensation is sized once from the
post-PV billed demand and added to project capex, rather than carried as a
25-year penalty stream that competent engineering would avoid.
"""

from proforma_thailand.defaults import (
    EMISSIONS_DEFAULTS,
    FINANCIAL_DEFAULTS,
    PLACEHOLDER_MARKER,
    value_of,
)
from proforma_thailand.emissions import (
    annual_avoided_tco2e,
    lifetime_avoided_tco2e,
)
from proforma_vietnam.country_profile import THAILAND_PROFILE
from proforma_vietnam.esco_pro_forma import (
    _levelization_factor,
    calculate_esco_pro_forma_from_reopt_results,
    # Private-by-convention, imported anyway: esco_pro_forma.py already uses
    # _pv_capex to compute pv_capex_vnd, the depreciation basis. If Thailand
    # derived its own PV/BESS capex instead of reusing these, the insurance
    # base here and the depreciation base there could silently diverge on any
    # future change to either. Consistency beats the underscore convention.
    _pv_capex,
    _storage_capex,
)
from proforma_vietnam.report_data import build_vietnam_report_data
from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook

# Assumption keys that map straight onto cash-flow keyword arguments.
PASSTHROUGH_OVERRIDE_KEYS = (
    "debt_fraction",
    "debt_interest_rate_fraction",
    "debt_term_years",
    "project_years",
    "pv_depreciation_years",
    "cit_regime",
    "om_escalation_rate",
    "evn_energy_escalation_rate",
    "evn_capacity_escalation_rate",
    "time_steps_per_hour",
    "pv_degradation_rate",
    "battery_replacement_year",
    "bess_depreciation_years",
    "cit_standard_rate",
)


def cash_flow_overrides_from_assumptions(assumptions):
    """Translate a Thailand assumptions block into cash-flow keyword arguments.

    The engine's currency keyword is named for Vietnam; Thailand passes its
    THB-per-USD rate through the same argument, which is what makes the ``_vnd``
    presentation keys carry THB.
    """
    overrides = {}
    # The cash-flow engine keeps Vietnam's _vnd parameter names by explicit
    # decision: vietnam is the shared core and nothing was renamed. The suffix
    # is a legacy label, not a currency assertion - the engine is
    # currency-agnostic and this value is USD like the rest of the payload.
    if assumptions.get("annual_om_usd") is not None:
        overrides["annual_om_vnd"] = assumptions["annual_om_usd"]
    for key in PASSTHROUGH_OVERRIDE_KEYS:
        if assumptions.get(key) is not None:
            overrides[key] = assumptions[key]
    if assumptions.get("exchange_rate_thb_per_usd") is not None:
        overrides["exchange_rate_vnd_per_usd"] = assumptions[
            "exchange_rate_thb_per_usd"
        ]
    # The engine defaults to Vietnam's Circular 45 range of 7-20 years, which
    # would reject Thailand's 5. Royal Decree No. 145 caps machinery at 20
    # percent per year, so 5 is the fastest permitted life and 20 the
    # conservative bound if the array were ever classed as a building
    # improvement. See docs/superpowers/notes/2026-09-04-thai-depreciation.md.
    overrides["pv_depreciation_years_min"] = 5
    overrides["pv_depreciation_years_max"] = 20
    overrides["pv_depreciation_citation"] = (
        "Thai Revenue Code, Royal Decree No. 145"
    )
    if assumptions.get("direct_ownership") is not None:
        overrides["direct_ownership"] = assumptions["direct_ownership"]
    # REopt.jl models no PV inverter replacement, and neither did this proforma,
    # which overstates a 25-year case. Book it as its own replacement event so it
    # hits the year it actually falls in rather than being smeared into O&M.
    inverter_year = assumptions.get("inverter_replacement_year")
    inverter_cost = assumptions.get("inverter_replacement_cost_usd")
    if inverter_year and inverter_cost:
        series = [0.0] * int(inverter_year)
        series[int(inverter_year) - 1] = float(inverter_cost)
        overrides["extra_replacement_costs_by_year"] = series
    return overrides


def compute_power_factor_compensation(assumptions):
    """Return a dict with ``status``, ``compensation_kvar`` and
    ``mitigation_cost_usd``.

    PV reduces billed kW but not kVAR, so the PEA allowance shrinks as demand
    falls. Anything above the allowance would be compensated once with a
    capacitor bank rather than paid monthly - but Keen has directed that this
    cost stay excluded from project capex, and the site kVAR maximum was
    never requested. That is a client choice, not a technical finding that no
    mitigation is needed, so the status says exactly that rather than
    reading as "none required". In production kvar_max is never supplied
    (see case_builder.py), so this status is what every real Thailand case
    discloses; the branches below exist only so the underlying kVAR math
    stays covered by tests that inject kvar_max directly.
    """
    status = "Excluded from capex at client direction; site kVAR data not requested"
    kvar_max = assumptions.get("kvar_max")
    billed_kw = assumptions.get("billed_demand_kw")
    if not kvar_max or not billed_kw:
        return {
            "status": status,
            "compensation_kvar": 0.0,
            "mitigation_cost_usd": 0.0,
        }
    allowance = assumptions["power_factor_allowance_fraction"] * billed_kw
    required = max(0.0, kvar_max - allowance)
    if required <= 0.0:
        return {
            "status": status,
            "compensation_kvar": 0.0,
            "mitigation_cost_usd": 0.0,
        }
    cost_usd = value_of(FINANCIAL_DEFAULTS, "power_factor_mitigation_cost")
    return {
        "status": status,
        "compensation_kvar": required,
        "mitigation_cost_usd": cost_usd,
    }


def billed_demand_kw_by_month(reopt_results):
    """On-peak billed demand per month, from the OPTIMIZED total grid draw.

    PEA bills the on-peak maximum of what the meter sees, which is grid-to-load
    PLUS grid-to-storage. REopt's own coincident-peak constraint applies to
    total grid purchase, so reading only the to-load series under-reports what
    the model already billed. Those step sets are 1-based, matching the Julia
    convention, hence the ``- 1``. Returns [] when either side is absent rather
    than inventing zeros.
    """
    tariff = (reopt_results.get("inputs") or {}).get("ElectricTariff") or {}
    utility = (reopt_results.get("outputs") or {}).get("ElectricUtility") or {}
    periods = tariff.get("coincident_peak_load_active_time_steps") or []
    to_load = utility.get("electric_to_load_series_kw") or []
    to_storage = utility.get("electric_to_storage_series_kw") or []
    if not periods or not to_load:
        return []

    def _draw(step):
        index = step - 1
        charging = to_storage[index] if index < len(to_storage) else 0.0
        return to_load[index] + charging

    return [
        max((_draw(step) for step in steps if 0 < step <= len(to_load)),
            default=0.0)
        for steps in periods
    ]


def annual_opex_usd(pv_capex_usd, bess_capex_usd, other_capex_usd,
                    annual_om_usd, insurance_rate_fraction):
    """Year-one operating cost including insurance.

    Insurance was costed nowhere. It is a real annual expense on an owned
    asset, so it belongs in opex where it escalates with O&M and is deducted
    for CIT. The base is total installed capex, which is how underwriters quote
    an all-risk premium.
    """
    total_capex = (pv_capex_usd or 0.0) + (bess_capex_usd or 0.0) + (other_capex_usd or 0.0)
    return (annual_om_usd or 0.0) + total_capex * (insurance_rate_fraction or 0.0)


def _as_pv_list(pv_outputs):
    """REopt returns PV as a dict for one array and a list for several."""
    if not pv_outputs:
        return []
    return pv_outputs if isinstance(pv_outputs, list) else [pv_outputs]


def build_thailand_report(reopt_results, assumptions):
    """Return ``(workbook, extras)`` for a Thailand DIRECT_OWNERSHIP run."""
    power_factor = compute_power_factor_compensation(assumptions)
    required_kvar = power_factor["compensation_kvar"]
    mitigation_cost = power_factor["mitigation_cost_usd"]

    # Capex comes from the solved results, not the roof-area cap handed to
    # REopt, so the inverter replacement (below) and insurance (further down)
    # are both derived here rather than in the case builder, which does not
    # yet know the optimized sizes.
    outputs = reopt_results.get("outputs") or {}
    inputs = reopt_results.get("inputs") or {}
    # PVOutputs carries no initial_capital_cost field (that only exists on
    # ElectricStorageOutputs), so reading it here always evaluated to 0.0 on
    # real runs. _pv_capex sums size_kw * installed_cost_per_kw instead, the
    # same figure esco_pro_forma.py uses as the depreciation basis, and wants
    # the PV output list rather than a single dict.
    pv_outputs_raw = outputs.get("PV")
    pv_outputs_list = (
        pv_outputs_raw if isinstance(pv_outputs_raw, list)
        else ([pv_outputs_raw] if pv_outputs_raw else [])
    )
    storage_inputs = inputs.get("ElectricStorage") or {}
    storage_outputs = outputs.get("ElectricStorage") or {}
    financial_outputs = outputs.get("Financial") or {}
    pv_capex = _pv_capex(pv_outputs_list)

    # Copy so the caller's assumptions dict is untouched; the derived cost
    # only needs to reach cash_flow_overrides_from_assumptions below.
    assumptions = dict(assumptions)
    assumptions["inverter_replacement_cost_usd"] = pv_capex * value_of(
        FINANCIAL_DEFAULTS, "inverter_replacement_fraction_of_pv_capex"
    )

    overrides = cash_flow_overrides_from_assumptions(assumptions)
    if mitigation_cost:
        overrides["other_capex_vnd"] = (
            overrides.get("other_capex_vnd", 0.0) + mitigation_cost
        )

    # Insurance is a real annual expense on an owned asset, so it belongs in
    # opex where it escalates with O&M and is deducted for CIT. This must run
    # unconditionally: a case that leaves annual_om_usd unset (the production
    # default) never puts annual_om_vnd in overrides, and the engine falls
    # back to its own outputs.Financial.year_one_om_costs_before_tax with no
    # premium added. Base O&M is the case's own figure when it supplied one,
    # otherwise that same REopt fallback, read here so the override always
    # carries the insured total.
    insurance_rate = value_of(FINANCIAL_DEFAULTS, "insurance_rate_fraction")
    base_om = assumptions.get("annual_om_usd")
    if base_om is None:
        base_om = financial_outputs.get("year_one_om_costs_before_tax") or 0.0
    overrides["annual_om_vnd"] = annual_opex_usd(
        pv_capex,
        _storage_capex(storage_inputs, storage_outputs),
        overrides.get("other_capex_vnd") or 0.0,
        base_om,
        insurance_rate,
    )

    cash_flow_result = calculate_esco_pro_forma_from_reopt_results(
        reopt_results,
        # DIRECT_OWNERSHIP captures the whole avoided bill, so there is no
        # discount to apply; the engine ignores this under that structure.
        esco_energy_discount_fraction=0.0,
        **overrides
    )
    report_data = build_vietnam_report_data(
        reopt_results,
        cash_flow_result,
        poa_irradiance_series=assumptions.get("pv_poa_irradiance_series"),
        time_steps_per_hour=assumptions.get("time_steps_per_hour", 1),
    )

    # Scope 2 avoided emissions: an Allotrope calculation from a cited Thai
    # grid factor, not a REopt output (see proforma_thailand/emissions.py).
    # The basis is avoided grid import, the same quantity already reported as
    # the grid offset, so the two figures cannot drift apart.
    load_outputs = outputs.get("ElectricLoad") or {}
    utility_outputs = outputs.get("ElectricUtility") or {}
    emission_factor = value_of(
        EMISSIONS_DEFAULTS, "grid_emission_factor_kg_co2e_per_kwh"
    )
    annual_tco2e = annual_avoided_tco2e(
        load_outputs.get("annual_calculated_kwh"),
        utility_outputs.get("annual_energy_supplied_kwh"),
        emission_factor,
        levelization_factor=_levelization_factor(_as_pv_list(outputs.get("PV"))),
    )

    workbook_assumptions = dict(assumptions)
    workbook_assumptions["placeholder_marker"] = PLACEHOLDER_MARKER
    workbook_assumptions["power_factor_compensation_kvar"] = required_kvar
    workbook_assumptions["power_factor_mitigation_cost_usd"] = mitigation_cost
    workbook_assumptions["insurance_rate_fraction"] = insurance_rate
    workbook_assumptions["annual_avoided_tco2e"] = annual_tco2e
    workbook_assumptions["grid_emission_factor_kg_co2e_per_kwh"] = emission_factor
    workbook_assumptions["grid_emission_factor_source"] = EMISSIONS_DEFAULTS[
        "grid_emission_factor_kg_co2e_per_kwh"
    ]["source"]
    workbook_assumptions["grid_emission_factor_vintage"] = value_of(
        EMISSIONS_DEFAULTS, "grid_emission_factor_vintage"
    )

    # PV O&M unit-rate rounding disclosure (Important 5 / Ruling 22): the
    # sourced and sent rate (7.5 USD/kWp-yr) is not what REopt actually
    # applied, because REopt.jl rounds PV cost parameters to whole dollars
    # before it solves. Read the applied rate back from the solved PV
    # outputs rather than assuming it equals the sent value. Only Thailand
    # builds this dict, so Vietnam workbooks never set these keys.
    workbook_assumptions["pv_om_cost_sourced_usd_per_kw"] = value_of(
        FINANCIAL_DEFAULTS, "annual_om_per_kw"
    )
    workbook_assumptions["pv_om_cost_sent_usd_per_kw"] = value_of(
        FINANCIAL_DEFAULTS, "annual_om_per_kw"
    )
    workbook_assumptions["pv_om_cost_applied_usd_per_kw"] = (
        pv_outputs_list[0].get("om_cost_per_kw") if pv_outputs_list else None
    )

    workbook = build_vietnam_esco_workbook(
        cash_flow_result,
        assumptions=workbook_assumptions,
        report_data=report_data,
        profile=THAILAND_PROFILE,
    )

    # A bare 0.0 here would read as "no compensation needed" when it actually
    # means "kvar_max was never supplied". Say which, so the report cannot
    # quietly present an uncomputed number as a finding.
    extras = {
        "power_factor_compensation_kvar": required_kvar,
        "power_factor_mitigation_cost_usd": mitigation_cost,
        "power_factor_status": (
            "computed" if assumptions.get("kvar_max")
            else "not computed - site kVAR maximum not supplied"
        ),
        "billed_demand_kw_by_month": (
            assumptions.get("billed_demand_kw_by_month")
            or billed_demand_kw_by_month(reopt_results)
        ),
        "annual_avoided_tco2e": annual_tco2e,
        "lifetime_avoided_tco2e": lifetime_avoided_tco2e(
            annual_tco2e,
            assumptions.get("project_years") or 25,
            (cash_flow_result.get("derivation") or {}).get("pv_degradation_rate")
            or assumptions.get("pv_degradation_rate")
            or 0.0,
        ),
        "grid_emission_factor_kg_co2e_per_kwh": emission_factor,
    }
    return workbook, extras
