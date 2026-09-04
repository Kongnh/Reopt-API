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
