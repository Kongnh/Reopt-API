from proforma_vietnam.defaults import EVN_TARIFF_RATES

STANDARD_TOU_MULTIPLIERS = {
    "off_peak": 0.52,
    "normal": 1.0,
    "peak": 1.78,
}


# STANDARD_MANUFACTURING_RATES and TWO_COMPONENT_PILOT_RATES are rebuilt here from the
# versioned JSON at proforma_vietnam/defaults/evn_tariff_rates.json (year string -> vintage
# object), keeping the dict shapes evn_tariff.py already expects: int year keys, and the
# original "rates_per_kwh" / "rates" sub-keys for the standard and two-component tables
# respectively. Regulatory provenance ("source") is carried through unchanged from the JSON.

STANDARD_MANUFACTURING_RATES = {
    int(year): {
        "source": vintage["source"],
        "currency": vintage["currency"],
        "rates_per_kwh": vintage["rates"],
    }
    for year, vintage in EVN_TARIFF_RATES["standard_manufacturing"].items()
}


TWO_COMPONENT_PILOT_RATES = {
    int(year): {
        "source": vintage["source"],
        "currency": vintage["currency"],
        "rates": vintage["rates"],
    }
    for year, vintage in EVN_TARIFF_RATES["two_component"].items()
}
