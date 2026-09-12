"""Battery state of health from the solved year-1 dispatch.

Replicates the daily SOH recurrence of REopt.jl v0.57.0 (``add_degradation``
in src/constraints/battery_degradation.jl) with the hours-per-time-step
factor removed, so the same daily energy gives the same fade at 15 minute
and hourly resolution (ruling 2026-09-12). REopt's code applies the cycle
coefficient to the energy discharged, not the documented (E+ + E-)/2; the
code is followed. The optimiser never sees this curve; it derates the
proforma only (see esco_pro_forma and cash_flow).
"""

from proforma_vietnam.defaults import (
    BESS_CALENDAR_FADE_COEFFICIENT,
    BESS_CALENDAR_FADE_EXPONENT,
    BESS_CYCLE_LIFE_EFC,
    BESS_END_OF_LIFE_SOH,
)

DAYS_PER_YEAR = 365


def cycle_fade_coefficient_from_life(cycle_life_efc, end_of_life_soh=BESS_END_OF_LIFE_SOH):
    """kWh lost per kWh discharged so that ``cycle_life_efc`` full cycles reach end of life."""
    if not cycle_life_efc or cycle_life_efc <= 0:
        raise ValueError("cycle_life_efc must be a positive number of equivalent full cycles.")
    return (1.0 - end_of_life_soh) / cycle_life_efc


def _daily_energies(soc_series_fraction, discharge_series_kw, size_kwh, time_steps_per_hour):
    steps_per_day = 24 * time_steps_per_hour
    needed = DAYS_PER_YEAR * steps_per_day
    if len(soc_series_fraction) < needed or len(discharge_series_kw) < needed:
        raise ValueError(
            "state of health needs a full year of storage series ({} steps), got {} and {}.".format(
                needed, len(soc_series_fraction), len(discharge_series_kw)
            )
        )
    average_energy_kwh = []
    discharged_kwh = []
    for day in range(DAYS_PER_YEAR):
        block = slice(day * steps_per_day, (day + 1) * steps_per_day)
        soc = soc_series_fraction[block]
        average_energy_kwh.append(sum(soc) / len(soc) * size_kwh)
        discharged_kwh.append(sum(discharge_series_kw[block]) / time_steps_per_hour)
    return average_energy_kwh, discharged_kwh


def battery_state_of_health(*, size_kwh, soc_series_fraction, discharge_series_kw,
                            time_steps_per_hour, project_years,
                            cycle_life_efc=BESS_CYCLE_LIFE_EFC,
                            end_of_life_soh=BESS_END_OF_LIFE_SOH,
                            calendar_fade_coefficient=BESS_CALENDAR_FADE_COEFFICIENT,
                            calendar_fade_exponent=BESS_CALENDAR_FADE_EXPONENT,
                            cycle_fade_coefficient=None):
    """SOH by day and by year for a battery cycled like its solved first year.

    Returns None when there is no battery or no series. ``cycle_fade_coefficient``
    given explicitly wins over the one derived from ``cycle_life_efc`` (the
    REopt replication test passes NREL's).
    """
    if not size_kwh or size_kwh <= 0 or not soc_series_fraction or not discharge_series_kw:
        return None
    k_cyc = (
        cycle_fade_coefficient if cycle_fade_coefficient is not None
        else cycle_fade_coefficient_from_life(cycle_life_efc, end_of_life_soh)
    )
    k_cal = calendar_fade_coefficient
    alpha = calendar_fade_exponent
    average_energy_kwh, discharged_kwh = _daily_energies(
        soc_series_fraction, discharge_series_kw, size_kwh, time_steps_per_hour
    )
    total_days = DAYS_PER_YEAR * int(project_years)
    soh_kwh = [float(size_kwh)]
    calendar_by_day = [0.0]
    cycle_by_day = [0.0]
    for day in range(2, total_days + 1):
        # Day d - 1 of the horizon maps onto the repeated year-1 pattern.
        previous = (day - 2) % DAYS_PER_YEAR
        calendar = k_cal * alpha * average_energy_kwh[previous] * day ** (alpha - 1)
        cycle = k_cyc * discharged_kwh[previous]
        soh_kwh.append(soh_kwh[-1] - calendar - cycle)
        calendar_by_day.append(calendar)
        cycle_by_day.append(cycle)
    soh_fraction = [value / size_kwh for value in soh_kwh]

    efc_per_year = sum(discharged_kwh) / size_kwh
    years = []
    cumulative = 0.0
    first_below = None
    for year in range(1, int(project_years) + 1):
        block = slice((year - 1) * DAYS_PER_YEAR, year * DAYS_PER_YEAR)
        fractions = soh_fraction[block]
        cumulative += efc_per_year
        years.append({
            "year": year,
            "soh_end": fractions[-1],
            "soh_average": sum(fractions) / len(fractions),
            "usable_kwh_end": fractions[-1] * size_kwh,
            "efc_in_year": efc_per_year,
            "efc_cumulative": cumulative,
            "calendar_fade_kwh": sum(calendar_by_day[block]),
            "cycle_fade_kwh": sum(cycle_by_day[block]),
        })
        if first_below is None and any(value < end_of_life_soh for value in fractions):
            first_below = year
    return {
        "size_kwh": float(size_kwh),
        "project_years": int(project_years),
        "soh_fraction_by_day": soh_fraction,
        "years": years,
        "soh_average_by_year": [entry["soh_average"] for entry in years],
        "first_year_below_end_of_life": first_below,
        "coefficients": {
            "calendar_fade_coefficient": k_cal,
            "calendar_fade_exponent": alpha,
            "cycle_fade_coefficient": k_cyc,
            "cycle_life_efc": cycle_life_efc if cycle_fade_coefficient is None else None,
            "end_of_life_soh": end_of_life_soh,
        },
        "year_one_daily_average_soc_kwh": sum(average_energy_kwh) / DAYS_PER_YEAR,
        "year_one_daily_discharge_kwh": sum(discharged_kwh) / DAYS_PER_YEAR,
        "year_one_efc": efc_per_year,
    }
