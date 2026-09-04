"""PEA Schedule 4.2 monthly bill reconstruction.

Used both as the tie-out test against real invoices and as the BAU bill in the
proforma. Off-peak and holiday energy share one bucket at the off-peak rate;
demand is billed on the on-peak maximum only; Ft applies to total kWh; VAT
applies to base plus Ft.
"""

from proforma_thailand.defaults import ft_for_month, pea_rates_for_year

DEFAULT_VOLTAGE_LEVEL = "22_33kv"


def compute_monthly_bill(peak_kwh, off_peak_kwh, holiday_kwh, on_peak_kw,
                         year, month, voltage_level=DEFAULT_VOLTAGE_LEVEL):
    _, values = pea_rates_for_year(year)
    rates = values["schedule_4_2"][voltage_level]

    demand_charge = on_peak_kw * rates["on_peak_demand_per_kw"]
    peak_energy = peak_kwh * rates["peak_energy_per_kwh"]
    off_peak_energy = (off_peak_kwh + holiday_kwh) * rates["off_peak_energy_per_kwh"]
    service_charge = values["service_charge_per_month"]
    base_total = demand_charge + peak_energy + off_peak_energy + service_charge

    total_kwh = peak_kwh + off_peak_kwh + holiday_kwh
    ft_charge = total_kwh * ft_for_month(year, month)

    subtotal = base_total + ft_charge
    vat = subtotal * values["vat_fraction"]

    return {
        "demand_charge": demand_charge,
        "peak_energy": peak_energy,
        "off_peak_energy": off_peak_energy,
        "service_charge": service_charge,
        "base_total": base_total,
        "ft_charge": ft_charge,
        "subtotal": subtotal,
        "vat": vat,
        "total": subtotal + vat,
    }
