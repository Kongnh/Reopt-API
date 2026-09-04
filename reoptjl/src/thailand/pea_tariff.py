"""PEA Schedule 4.2 (Large General Service, TOU) tariff builder.

Verified against the Rofu (Thailand) invoice for 06/2568 (rate code 4224,
22-33 kV): peak energy 4.1839 THB/kWh, off-peak and holiday energy billed as a
single bucket at 2.6037, demand billed on the on-peak maximum only at 132.93
THB/kW, plus a per-kWh Ft adder that is revised every four months.

Two mappings matter for REopt:

- Demand is NOT a monthly all-hours maximum, so it uses
  coincident_peak_load_charge_per_kw with one period per month rather than
  monthly_demand_rates. The Julia constraint compares power to power and omits
  TimeStepScaling (julia_src/reopt_model.jl:1049), so it is correct at
  sub-hourly resolution.
- The service charge has no V3 input field and is identical in the BAU and
  optimized cases, so it is returned for the proforma to display and is not
  part of the REopt payload.

Intervals are labelled by their END time, matching the meter data: interval 0
covers 00:00-00:15 and is labelled 00:15. On-peak is 09:00 < t <= 22:00.
"""

from datetime import date, timedelta

from proforma_thailand.defaults import ft_for_month, pea_rates_for_year

PEAK_START_MINUTE = 9 * 60
PEAK_END_MINUTE = 22 * 60
DEFAULT_VOLTAGE_LEVEL = "22_33kv"
MONEY_KEYS_PER_MONTH = ("coincident_peak_load_charge_per_kw",)


def build_pea_tariff(calendar_year_months, all_off_peak_dates,
                     voltage_level=DEFAULT_VOLTAGE_LEVEL, currency="thb",
                     exchange_rate_thb_per_usd=None, time_steps_per_hour=4):
    if len(calendar_year_months) != 12:
        raise ValueError(
            "calendar_year_months must hold exactly 12 (year, month) pairs in "
            "January-to-December order; got {}.".format(len(calendar_year_months))
        )

    vintage_year, values = pea_rates_for_year(
        max(year for year, _ in calendar_year_months)
    )
    schedule = values["schedule_4_2"]
    if voltage_level not in schedule:
        raise ValueError(
            "Unsupported PEA voltage level {!r}; configured: {}.".format(
                voltage_level, sorted(schedule)
            )
        )
    rates = schedule[voltage_level]

    steps_per_day = 24 * time_steps_per_hour
    minutes_per_step = 60 // time_steps_per_hour

    ft_by_month = [ft_for_month(year, month) for year, month in calendar_year_months]

    energy_rates = []
    coincident_steps = [[] for _ in range(12)]
    timestep = 0
    for month_index, (year, month) in enumerate(calendar_year_months):
        for day in _days_in_month(year, month):
            is_all_off_peak = day in all_off_peak_dates or day.weekday() >= 5
            for slot in range(steps_per_day):
                timestep += 1
                end_minute = (slot + 1) * minutes_per_step
                on_peak = (
                    not is_all_off_peak
                    and PEAK_START_MINUTE < end_minute <= PEAK_END_MINUTE
                )
                base = (
                    rates["peak_energy_per_kwh"] if on_peak
                    else rates["off_peak_energy_per_kwh"]
                )
                energy_rates.append(base + ft_by_month[month_index])
                if on_peak:
                    coincident_steps[month_index].append(timestep)

    demand_rates = [rates["on_peak_demand_per_kw"]] * 12

    result = {
        "tou_energy_rates_per_kwh": [
            _convert(rate, currency, exchange_rate_thb_per_usd) for rate in energy_rates
        ],
        "coincident_peak_load_charge_per_kw": [
            _convert(rate, currency, exchange_rate_thb_per_usd) for rate in demand_rates
        ],
        "coincident_peak_load_active_time_steps": coincident_steps,
        "rate_vintage_year": vintage_year,
        "rate_vintage_source": values["source"],
        "service_charge_per_month": _convert(
            values["service_charge_per_month"], currency, exchange_rate_thb_per_usd
        ),
        "vat_fraction": values["vat_fraction"],
        "power_factor_charge_per_kvar": _convert(
            values["power_factor_charge_per_kvar"], currency, exchange_rate_thb_per_usd
        ),
        "power_factor_allowance_fraction": values["power_factor_allowance_fraction"],
        "ft_per_kwh_by_month": ft_by_month,
    }
    return result


def _days_in_month(year, month):
    """Yield every date in the given month."""
    current = date(year, month, 1)
    while current.month == month:
        yield current
        current += timedelta(days=1)


def _convert(value, currency, exchange_rate_thb_per_usd):
    if currency == "thb":
        return value
    if currency == "usd":
        if not exchange_rate_thb_per_usd:
            raise ValueError(
                "exchange_rate_thb_per_usd is required when currency='usd'."
            )
        return value / exchange_rate_thb_per_usd
    raise ValueError("Unsupported currency: {}".format(currency))
