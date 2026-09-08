"""Versioned Thailand proforma defaults.

Mirrors proforma_vietnam/defaults: the JSON files are the editable source of the
numbers, and provenance lives in each entry's "source" field. Rate resolution
follows the same rule as the EVN tables - a requested year falls back to the
newest vintage on or before it.
"""

import json
import os

_DIR = os.path.dirname(__file__)

with open(os.path.join(_DIR, "pea_tariff_rates.json"), encoding="utf-8") as _f:
    PEA_TARIFF_RATES = json.load(_f)


def pea_rates_for_year(year):
    """Return ``(vintage_year, values)`` for the latest vintage <= ``year``."""
    vintages = PEA_TARIFF_RATES["vintages"]
    eligible = [int(y) for y in vintages if int(y) <= year]
    if not eligible:
        raise ValueError(
            "No PEA rates configured for year {} or earlier.".format(year)
        )
    vintage_year = max(eligible)
    return vintage_year, vintages[str(vintage_year)]


def ft_for_month(year, month):
    """Return the Ft adder (THB/kWh) in force for ``year``/``month``.

    Ft is revised every four months. Windows are declared by their start
    (year, month) and run until the next one begins.
    """
    key = (year, month)
    eligible = [
        window
        for window in PEA_TARIFF_RATES["ft_windows"]
        if (window["from_year"], window["from_month"]) <= key
    ]
    if not eligible:
        raise ValueError(
            "No Ft window configured for {}-{:02d} or earlier.".format(year, month)
        )
    latest = max(eligible, key=lambda w: (w["from_year"], w["from_month"]))
    return latest["ft_per_kwh"]


with open(os.path.join(_DIR, "thailand_defaults.json"), encoding="utf-8") as _f:
    THAILAND_DEFAULTS = json.load(_f)

PLACEHOLDER_MARKER = THAILAND_DEFAULTS["placeholder_marker"]
FINANCIAL_DEFAULTS = THAILAND_DEFAULTS["financial"]
TAX_DEFAULTS_RAW = THAILAND_DEFAULTS["tax"]
SITE_DEFAULTS = THAILAND_DEFAULTS["site"]
EMISSIONS_DEFAULTS = THAILAND_DEFAULTS["emissions"]

# Tax values are consumed as plain numbers by the cash flow engine, so expose a
# flattened view alongside the annotated one.
TAX_DEFAULTS = {key: entry["value"] for key, entry in TAX_DEFAULTS_RAW.items()}

# The coupling each derived default must satisfy: (derived, base, fraction).
# Kept as an assertion rather than a computation so the JSON stays the single
# readable source of every number, while a price change that desyncs a coupled
# value fails at import instead of silently shipping.
_DERIVED_COUPLINGS = (
    ("annual_om_per_kw", "pv_installed_cost_per_kw", 0.015),
    ("bess_replace_cost_per_kw", "bess_installed_cost_per_kw", 0.70),
    ("bess_replace_cost_per_kwh", "bess_installed_cost_per_kwh", 0.70),
)


def _assert_couplings_hold():
    for derived_key, base_key, fraction in _DERIVED_COUPLINGS:
        derived = FINANCIAL_DEFAULTS[derived_key]["value"]
        expected = FINANCIAL_DEFAULTS[base_key]["value"] * fraction
        if abs(derived - expected) > 1e-9:
            raise ValueError(
                "{} is {} but is defined as {} of {}, which is {}. "
                "Re-derive it or change the coupling.".format(
                    derived_key, derived, fraction, base_key, expected
                )
            )


_assert_couplings_hold()


def placeholder_keys():
    """Names of every default still awaiting confirmation from Keen."""
    found = set()
    for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW, EMISSIONS_DEFAULTS):
        for key, entry in block.items():
            if entry.get("source") == PLACEHOLDER_MARKER:
                found.add(key)
    return found


def value_of(block, key):
    """Read a default's numeric value, ignoring its provenance wrapper."""
    return block[key]["value"]
