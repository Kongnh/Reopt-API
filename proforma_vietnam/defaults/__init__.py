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
