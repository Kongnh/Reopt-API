from calendar import isleap
from datetime import datetime

from reoptjl.src.vietnam.evn_rates import (
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
    if tariff_category != "manufacturing":
        raise ValueError("Only manufacturing EVN tariffs are available.")
    if isleap(year):
        raise ValueError("EVN tariff builder currently produces 8760-hour non-leap-year arrays.")

    voltage_key = _normalize_voltage_level(voltage_level)
    schedule = _tou_schedule(tou_schedule)
    rates = _rates_for(year, voltage_key, base_rate_per_kwh, two_component_pilot_enabled)
    tou_rates = [_convert_currency(rates[_period_for(year, hour_index, schedule)], currency, exchange_rate_vnd_per_usd)
                 for hour_index in range(8760)]

    monthly_demand_rates = []
    if two_component_pilot_enabled:
        cp_rate = TWO_COMPONENT_PILOT_RATES[year]["rates"][voltage_key]["capacity_per_kw_month"]
        monthly_demand_rates = [_convert_currency(cp_rate, currency, exchange_rate_vnd_per_usd)] * 12

    return {
        "tou_energy_rates_per_kwh": tou_rates,
        "monthly_demand_rates": monthly_demand_rates,
    }


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


def _rates_for(year, voltage_key, base_rate_per_kwh, two_component_pilot_enabled):
    if two_component_pilot_enabled:
        if year not in TWO_COMPONENT_PILOT_RATES:
            raise ValueError("No EVN two-component pilot rates configured for year {}.".format(year))
        return TWO_COMPONENT_PILOT_RATES[year]["rates"][voltage_key]["energy_per_kwh"]

    if base_rate_per_kwh is not None:
        return {
            period: base_rate_per_kwh * multiplier
            for period, multiplier in STANDARD_TOU_MULTIPLIERS.items()
        }

    if year not in STANDARD_MANUFACTURING_RATES:
        raise ValueError("No EVN standard manufacturing rates configured for year {}.".format(year))
    return STANDARD_MANUFACTURING_RATES[year]["rates_per_kwh"][voltage_key]


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
