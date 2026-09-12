"""Versioned Vietnam proforma defaults.

Loads ``vietnam_defaults.json`` once at import. Modules expose the public
``DEFAULT_*`` / regulatory constants from these values, so the single
externally-editable file is the source of the numbers while the code keeps the
regulatory provenance in comments. Mirrors SAM's ``deploy/runtime/defaults``.
"""

import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "vietnam_defaults.json")

with open(_PATH, encoding="utf-8") as _f:
    _DEFAULTS = json.load(_f)

VERSION = _DEFAULTS["version"]
FINANCIAL_DEFAULTS = _DEFAULTS["financial"]
TAX_DEFAULTS = _DEFAULTS["tax"]
SURPLUS_EXPORT_DEFAULTS = _DEFAULTS["surplus_export"]

# Equipment replacement and battery ageing policy shared by every country
# branch (rulings of 2026-09-11 and 2026-09-12). A country's JSON carries its
# own prices and provenance, but its horizon and schedule must agree with
# these or its defaults module refuses to import; that is what keeps the two
# branches from drifting.
PROJECT_YEARS = 20
# 2026-09-12: no scheduled battery replacement inside the horizon. A case may
# opt in through technologies.storage.replacement; the year and fraction below
# are then the defaults it inherits (whole system, storage inverter and pack).
BESS_REPLACEMENT_ENABLED = False
BESS_REPLACEMENT_YEAR = 10
BESS_REPLACE_FRACTION_OF_INSTALL = 1.0
PV_INVERTER_REPLACEMENT_YEAR = 11
PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX = 0.10
# Battery ageing is carried by a state-of-health curve instead (battery_soh.py).
# Cycle life in the style of an LFP datasheet: equivalent full cycles to end of
# life. Calendar fade keeps the NREL coefficients REopt.jl v0.57.0 ships.
BESS_CYCLE_LIFE_EFC = 8000
BESS_END_OF_LIFE_SOH = 0.80
BESS_CALENDAR_FADE_COEFFICIENT = 1.16e-3
BESS_CALENDAR_FADE_EXPONENT = 0.428

def _assert_policy_holds():
    if FINANCIAL_DEFAULTS["project_years"] != PROJECT_YEARS:
        raise ValueError(
            "vietnam_defaults.json financial.project_years is {} but the shared "
            "replacement policy is {} years. Change the policy for both countries "
            "or re-derive the JSON.".format(
                FINANCIAL_DEFAULTS["project_years"], PROJECT_YEARS
            )
        )


_assert_policy_holds()

_EVN_TARIFF_PATH = os.path.join(os.path.dirname(__file__), "evn_tariff_rates.json")

with open(_EVN_TARIFF_PATH, encoding="utf-8") as _evn_tariff_f:
    EVN_TARIFF_RATES = json.load(_evn_tariff_f)

_DPPA_REGULATORY_PATH = os.path.join(os.path.dirname(__file__), "dppa_regulatory.json")

with open(_DPPA_REGULATORY_PATH, encoding="utf-8") as _dppa_regulatory_f:
    DPPA_REGULATORY = json.load(_dppa_regulatory_f)


def dppa_regulatory_for_year(year):
    """Resolve ``year`` to the latest configured DPPA regulatory vintage <= year.

    Mirrors evn_tariff.py's rate-vintage fallback: DPPA regulatory constants
    (loss factors, settlement fee adders) only change when NLDC/EVN issues new
    guidance, so a requested year with no exact vintage falls back to the
    newest vintage on or before it. Raises only when ``year`` predates every
    configured vintage.

    Returns ``(vintage_year, values)`` where ``values`` is the vintage's dict
    from dppa_regulatory.json (source, transmission_loss_factor_k, etc.).
    """
    vintages = DPPA_REGULATORY["vintages"]
    eligible_years = [int(vintage_year) for vintage_year in vintages if int(vintage_year) <= year]
    if not eligible_years:
        raise ValueError(
            "No DPPA regulatory constants configured for year {} or earlier.".format(year)
        )
    vintage_year = max(eligible_years)
    return vintage_year, vintages[str(vintage_year)]


def surplus_export_price_vnd_per_kwh(region):
    """Rooftop surplus-export price for ``region`` under Decree 243/2026.

    Returns the lesser of the prior-year average electricity market price and
    the region's Decision 988/QD-BCT ground-mounted-solar (no storage)
    ceiling, per SURPLUS_EXPORT_DEFAULTS. ``region`` is matched
    case-insensitively against "north", "central", "south".
    """
    ceilings = SURPLUS_EXPORT_DEFAULTS["price_ceiling_vnd_per_kwh_by_region"]
    region_key = region.lower()
    if region_key not in ceilings:
        raise ValueError(
            "Unknown surplus-export region '{}'; expected one of {}.".format(
                region, sorted(ceilings)
            )
        )
    prior_year_avg = SURPLUS_EXPORT_DEFAULTS["prior_year_avg_market_price_vnd_per_kwh"]
    return min(prior_year_avg, ceilings[region_key])
