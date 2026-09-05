"""Render the Thailand proforma workbook.

Drives the proforma_vietnam engine with THAILAND_PROFILE. Money keys keep their
historical ``_vnd`` suffix and carry THB (see the spec's section 2); only the
rendered labels change, and a test asserts no VND or EVN string survives.

Power factor is handled per spec section 4: compensation is sized once from the
post-PV billed demand and added to project capex, rather than carried as a
25-year penalty stream that competent engineering would avoid.
"""

from proforma_thailand.defaults import (
    FINANCIAL_DEFAULTS,
    PLACEHOLDER_MARKER,
    value_of,
)
from proforma_vietnam.country_profile import THAILAND_PROFILE
from proforma_vietnam.esco_pro_forma import (
    calculate_esco_pro_forma_from_reopt_results,
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
    "pv_degradation_rate",
    "battery_replacement_year",
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
    return overrides


def compute_power_factor_compensation(assumptions):
    """Return ``(required_kvar, mitigation_cost_usd)``.

    PV reduces billed kW but not kVAR, so the PEA allowance shrinks as demand
    falls. Anything above the allowance is compensated once with a capacitor
    bank rather than paid monthly.
    """
    kvar_max = assumptions.get("kvar_max")
    billed_kw = assumptions.get("billed_demand_kw")
    if not kvar_max or not billed_kw:
        return 0.0, 0.0
    allowance = assumptions["power_factor_allowance_fraction"] * billed_kw
    required = max(0.0, kvar_max - allowance)
    if required <= 0.0:
        return 0.0, 0.0
    cost_usd = value_of(FINANCIAL_DEFAULTS, "power_factor_mitigation_cost")
    return required, cost_usd


def billed_demand_kw_by_month(reopt_results):
    """On-peak billed demand per month, from the OPTIMIZED grid draw.

    PEA bills the on-peak maximum, so this is the max of the grid series over
    each month's coincident-peak timestep set. Those sets are 1-based, matching
    the Julia convention, hence the ``- 1``. Returns [] when either side is
    absent rather than inventing zeros.
    """
    tariff = (reopt_results.get("inputs") or {}).get("ElectricTariff") or {}
    utility = (reopt_results.get("outputs") or {}).get("ElectricUtility") or {}
    periods = tariff.get("coincident_peak_load_active_time_steps") or []
    series = utility.get("electric_to_load_series_kw") or []
    if not periods or not series:
        return []
    return [
        max((series[step - 1] for step in steps if 0 < step <= len(series)),
            default=0.0)
        for steps in periods
    ]


def build_thailand_report(reopt_results, assumptions):
    """Return ``(workbook, extras)`` for a Thailand DIRECT_OWNERSHIP run."""
    required_kvar, mitigation_cost = compute_power_factor_compensation(assumptions)

    overrides = cash_flow_overrides_from_assumptions(assumptions)
    if mitigation_cost:
        overrides["other_capex_vnd"] = (
            overrides.get("other_capex_vnd", 0.0) + mitigation_cost
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
    )

    workbook_assumptions = dict(assumptions)
    workbook_assumptions["placeholder_marker"] = PLACEHOLDER_MARKER
    workbook_assumptions["power_factor_compensation_kvar"] = required_kvar
    workbook_assumptions["power_factor_mitigation_cost_usd"] = mitigation_cost

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
    }
    return workbook, extras
