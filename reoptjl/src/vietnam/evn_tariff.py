from calendar import isleap
from datetime import datetime

from reoptjl.src.vietnam.evn_rates import (
    STANDARD_BUSINESS_RATES,
    STANDARD_MANUFACTURING_RATES,
    STANDARD_TOU_MULTIPLIERS,
    TWO_COMPONENT_PILOT_RATES,
)


TOU_SCHEDULES = {
    "current": {
        "off_peak_hours": set([0, 1, 2, 3, 22, 23]),
        "peak_hours": set([10, 11, 17, 18, 19]),
        "sunday_has_peak": False,
    },
    "decision_963": {
        "off_peak_hours": set([0, 1, 2, 3, 4, 5]),
        "peak_hours": set([18, 19, 20, 21, 22]),
        "sunday_has_peak": False,
    },
}

# Vintage-disclosure keys carried on build_evn_tariff()'s output. They are audit
# metadata, not REopt.jl ElectricTariff scenario fields — callers that submit the
# tariff dict to REopt.jl must strip these keys from the payload first.
RATE_VINTAGE_KEYS = ("rate_vintage_year", "rate_vintage_source")

SUPPORTED_TARIFF_CATEGORIES = ("manufacturing", "business")

# The kinh doanh (business) table has a single ">=22kV" tier where the
# manufacturing table splits 110kV+ from 22-110kV, so both normalized keys
# resolve to the same business tier.
BUSINESS_VOLTAGE_TIER_BY_KEY = {
    "110kv_and_above": "22kv_and_above",
    "22_to_110kv": "22kv_and_above",
    "6_to_22kv": "6_to_22kv",
    "below_6kv": "below_6kv",
}

VOLTAGE_LEVEL_ALIASES = {
    ">=110kv": "110kv_and_above",
    "110kv_and_above": "110kv_and_above",
    "110kv and above": "110kv_and_above",
    "u>=110kv": "110kv_and_above",
    "22-110kv": "22_to_110kv",
    "22_to_110kv": "22_to_110kv",
    "22kv_to_110kv": "22_to_110kv",
    "22 kv to less than 110 kv": "22_to_110kv",
    "6-22kv": "6_to_22kv",
    "6_to_22kv": "6_to_22kv",
    "6kv_to_22kv": "6_to_22kv",
    "6 kv to less than 22 kv": "6_to_22kv",
    "<6kv": "below_6kv",
    "below_6kv": "below_6kv",
    "less than 6kv": "below_6kv",
    "less than 6 kv": "below_6kv",
}


def build_evn_tariff(year, voltage_level, tariff_category="manufacturing",
                     base_rate_per_kwh=None, two_component_pilot_enabled=False,
                     currency="vnd", exchange_rate_vnd_per_usd=None,
                     tou_schedule="current"):
    if tariff_category not in SUPPORTED_TARIFF_CATEGORIES:
        raise ValueError(
            "Unsupported EVN tariff category: {}. Supported: {}.".format(
                tariff_category, ", ".join(repr(c) for c in SUPPORTED_TARIFF_CATEGORIES)
            )
        )
    if tariff_category == "business" and two_component_pilot_enabled:
        raise ValueError(
            "The two-component pilot applies to manufacturing (production) "
            "customers; it cannot be combined with the business (kinh doanh) "
            "tariff category."
        )
    if isleap(year):
        raise ValueError("EVN tariff builder currently produces 8760-hour non-leap-year arrays.")

    voltage_key = _normalize_voltage_level(voltage_level)
    schedule = _tou_schedule(tou_schedule)
    rates, rate_vintage_year, rate_vintage_source = _rates_for(
        year, voltage_key, base_rate_per_kwh, two_component_pilot_enabled, tariff_category
    )
    tou_rates = [_convert_currency(rates[_period_for(year, hour_index, schedule)], currency, exchange_rate_vnd_per_usd)
                 for hour_index in range(8760)]

    monthly_demand_rates = []
    if two_component_pilot_enabled:
        cp_rate = TWO_COMPONENT_PILOT_RATES[rate_vintage_year]["rates"][voltage_key]["capacity_per_kw_month"]
        monthly_demand_rates = [_convert_currency(cp_rate, currency, exchange_rate_vnd_per_usd)] * 12

    result = {
        "tou_energy_rates_per_kwh": tou_rates,
        "monthly_demand_rates": monthly_demand_rates,
    }
    if rate_vintage_year is not None:
        result["rate_vintage_year"] = rate_vintage_year
        result["rate_vintage_source"] = rate_vintage_source
    return result


def _normalize_voltage_level(voltage_level):
    normalized = str(voltage_level).strip().lower().replace(" ", "")
    if normalized in VOLTAGE_LEVEL_ALIASES:
        return VOLTAGE_LEVEL_ALIASES[normalized]

    normalized_with_spaces = str(voltage_level).strip().lower()
    if normalized_with_spaces in VOLTAGE_LEVEL_ALIASES:
        return VOLTAGE_LEVEL_ALIASES[normalized_with_spaces]

    raise ValueError("Unsupported EVN voltage level: {}".format(voltage_level))


def _tou_schedule(tou_schedule):
    schedule_key = str(tou_schedule).strip().lower().replace("-", "_")
    if schedule_key in TOU_SCHEDULES:
        return TOU_SCHEDULES[schedule_key]
    raise ValueError("Unsupported EVN TOU schedule: {}".format(tou_schedule))


def _rates_for(year, voltage_key, base_rate_per_kwh, two_component_pilot_enabled,
               tariff_category="manufacturing"):
    if two_component_pilot_enabled:
        vintage_year = _latest_vintage_year(TWO_COMPONENT_PILOT_RATES, year, "two-component pilot")
        vintage = TWO_COMPONENT_PILOT_RATES[vintage_year]
        return vintage["rates"][voltage_key]["energy_per_kwh"], vintage_year, vintage["source"]

    if base_rate_per_kwh is not None:
        rates = {
            period: base_rate_per_kwh * multiplier
            for period, multiplier in STANDARD_TOU_MULTIPLIERS.items()
        }
        return rates, None, None

    if tariff_category == "business":
        vintage_year = _latest_vintage_year(STANDARD_BUSINESS_RATES, year, "standard business")
        vintage = STANDARD_BUSINESS_RATES[vintage_year]
        business_tier = BUSINESS_VOLTAGE_TIER_BY_KEY[voltage_key]
        return vintage["rates_per_kwh"][business_tier], vintage_year, vintage["source"]

    vintage_year = _latest_vintage_year(STANDARD_MANUFACTURING_RATES, year, "standard manufacturing")
    vintage = STANDARD_MANUFACTURING_RATES[vintage_year]
    return vintage["rates_per_kwh"][voltage_key], vintage_year, vintage["source"]


def _latest_vintage_year(rates_by_year, year, label):
    """Resolve ``year`` to the latest configured vintage year <= ``year``.

    Rate tables only carry the years a tariff decision actually changed;
    a requested year with no exact entry falls back to the newest vintage
    on or before it (e.g. 2026 resolves to a 2025 vintage). Raises only
    when ``year`` predates every configured vintage.
    """
    eligible_years = [vintage_year for vintage_year in rates_by_year if vintage_year <= year]
    if not eligible_years:
        raise ValueError(
            "No EVN {} rates configured for year {} or earlier.".format(label, year)
        )
    return max(eligible_years)


def _period_for(year, hour_index, schedule):
    hour = hour_index % 24
    day_of_year = hour_index // 24 + 1
    timestamp = datetime.strptime("{} {}".format(year, day_of_year), "%Y %j")

    if timestamp.weekday() == 6 and not schedule["sunday_has_peak"]:
        return "normal"
    if hour in schedule["off_peak_hours"]:
        return "off_peak"
    if hour in schedule["peak_hours"]:
        return "peak"
    return "normal"


def _convert_currency(value, currency, exchange_rate_vnd_per_usd):
    if currency == "vnd":
        return value
    if currency == "usd":
        if not exchange_rate_vnd_per_usd:
            raise ValueError("exchange_rate_vnd_per_usd is required when currency='usd'.")
        return value / exchange_rate_vnd_per_usd
    raise ValueError("Unsupported currency: {}".format(currency))
