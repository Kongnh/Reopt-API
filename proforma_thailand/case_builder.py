"""Build a REopt payload plus an assumptions block for a Thailand case.

Mirrors proforma_vietnam/case_builder.py but for PEA: 15-minute resolution,
coincident-peak demand rather than monthly demand rates, and no export.
Only DIRECT_OWNERSHIP is supported; ESCO/PPA is a later phase.
"""

import json
from datetime import date
from pathlib import Path

from proforma_thailand.defaults import (
    FINANCIAL_DEFAULTS,
    SITE_DEFAULTS,
    TAX_DEFAULTS,
    placeholder_keys,
    value_of,
)
from proforma_vietnam import pvwatts_client
from proforma_vietnam.case_builder import _read_load_csv
from proforma_vietnam.country_profile import THAILAND_PROFILE
from reoptjl.src.thailand.pea_tariff import build_pea_tariff

# The producer owns the audit-key list; importing it means adding a key to
# build_pea_tariff cannot silently leak into a REopt payload.
from reoptjl.src.thailand.pea_tariff import AUDIT_METADATA_KEYS, RATE_VINTAGE_KEYS

NON_PAYLOAD_TARIFF_KEYS = AUDIT_METADATA_KEYS


def build_thailand_case(case_config):
    profile = THAILAND_PROFILE
    site = case_config["site"]
    load_config = case_config["load_profile"]
    tariff_config = case_config.get("tariff", {})
    technologies = case_config.get("technologies", {})

    calendar_months = [
        (int(year), int(month))
        for year, month in load_config["calendar_year_months"]
    ]
    loads_kw = _read_load_csv(
        load_config["path"], time_steps_per_hour=profile.time_steps_per_hour
    )
    all_off_peak_dates = {
        date.fromisoformat(value)
        for value in json.loads(
            Path(load_config["all_off_peak_dates_path"]).read_text(encoding="utf-8")
        )
    }

    exchange_rate = tariff_config.get(
        "exchange_rate_thb_per_usd",
        value_of(FINANCIAL_DEFAULTS, "exchange_rate_thb_per_usd"),
    )
    tariff = build_pea_tariff(
        calendar_months,
        all_off_peak_dates,
        voltage_level=tariff_config.get("voltage_level", "22_33kv"),
        currency="usd",
        exchange_rate_thb_per_usd=exchange_rate,
        time_steps_per_hour=profile.time_steps_per_hour,
    )
    tariff_extras = {key: tariff.pop(key) for key in NON_PAYLOAD_TARIFF_KEYS}

    # fetch_pv_series returns the dict; fetch_production_factor_series
    # returns only the bare list. proforma_vietnam/case_builder.py:266
    # uses the same call for the same reason.
    production = pvwatts_client.fetch_pv_series(
        site["latitude"], site["longitude"]
    )

    pv_config = technologies.get("pv", {})
    storage_config = technologies.get("storage", {})
    pv_max_kw = pv_config.get("max_kw", value_of(SITE_DEFAULTS, "pv_max_kw"))

    payload = {
        "Settings": {"time_steps_per_hour": profile.time_steps_per_hour},
        "Site": {"latitude": site["latitude"], "longitude": site["longitude"]},
        # REopt rejects loads_kw without a year (core_electric_load.jl:137).
        # Take it from the synthetic calendar rather than hardcoding, so the
        # two cannot drift apart. Jan-Jun are tagged 2026, which is not a leap
        # year, matching the 365-day / 35040-interval series.
        "ElectricLoad": {
            "loads_kw": loads_kw,
            "year": calendar_months[0][0],
        },
        "ElectricTariff": tariff,
        # Every FinancialInputs field is null=True with no Django default, so
        # anything omitted here silently takes REopt.jl's US-centric default.
        # Send the Thai values we hold rather than inheriting those.
        "Financial": {
            "analysis_years": value_of(FINANCIAL_DEFAULTS, "project_years"),
            "elec_cost_escalation_rate_fraction": value_of(
                FINANCIAL_DEFAULTS, "pea_tariff_escalation_rate"
            ),
            "om_cost_escalation_rate_fraction": value_of(
                FINANCIAL_DEFAULTS, "om_escalation_rate"
            ),
            "offtaker_tax_rate_fraction": TAX_DEFAULTS["cit_standard_rate"],
            "offtaker_discount_rate_fraction": value_of(
                FINANCIAL_DEFAULTS, "discount_rate"
            ),
            # Direct ownership: the offtaker IS the owner, so both rates match.
            "owner_discount_rate_fraction": value_of(
                FINANCIAL_DEFAULTS, "discount_rate"
            ),
            "owner_tax_rate_fraction": TAX_DEFAULTS["cit_standard_rate"],
        },
    }

    # validators.py:226 only resamples production_factor_series when max_kw > 0,
    # so an 8760 series on a zero-PV case reaches Julia unresampled and fails
    # against the 35040 container. A case with no PV should not declare the
    # technology at all, the same way storage is handled below.
    if pv_max_kw:
        payload["PV"] = {
            "max_kw": pv_max_kw,
            "installed_cost_per_kw": pv_config.get(
                "installed_cost_per_kw",
                value_of(FINANCIAL_DEFAULTS, "pv_installed_cost_per_kw"),
            ),
            "production_factor_series": production["production_factor"],
            # PEA pays nothing for exported energy, so the system must curtail
            # rather than export. See spec section 3.
            "can_net_meter": False,
            "can_wholesale": False,
            "can_export_beyond_nem_limit": False,
            "can_curtail": True,
        }

    if storage_config.get("max_kw") or storage_config.get("max_kwh"):
        payload["ElectricStorage"] = {
            "max_kw": storage_config.get("max_kw", 0),
            "max_kwh": storage_config.get("max_kwh", 0),
            "installed_cost_per_kw": storage_config.get(
                "installed_cost_per_kw",
                value_of(FINANCIAL_DEFAULTS, "bess_installed_cost_per_kw"),
            ),
            "installed_cost_per_kwh": storage_config.get(
                "installed_cost_per_kwh",
                value_of(FINANCIAL_DEFAULTS, "bess_installed_cost_per_kwh"),
            ),
            "installed_cost_constant": storage_config.get(
                "installed_cost_constant", 0.0
            ),
            "can_grid_charge": storage_config.get("can_grid_charge", True),
        }

    assumptions = {
        "country": profile.country,
        "local_currency_code": profile.local_currency_code,
        "utility_label": profile.utility_label,
        "time_steps_per_hour": profile.time_steps_per_hour,
        "exchange_rate_thb_per_usd": exchange_rate,
        "calendar_year_months": [list(pair) for pair in calendar_months],
        "service_charge_per_month_thb": (
            tariff_extras["service_charge_per_month"] * exchange_rate
        ),
        "vat_rate_fraction": tariff_extras["vat_fraction"],
        "power_factor_charge_per_kvar_thb": (
            tariff_extras["power_factor_charge_per_kvar"] * exchange_rate
        ),
        "power_factor_allowance_fraction": tariff_extras[
            "power_factor_allowance_fraction"
        ],
        "ft_per_kwh_by_month_thb": [
            value * exchange_rate for value in tariff_extras["ft_per_kwh_by_month"]
        ],
        "cit_regime": "standard_flat",
        "cit_standard_rate": TAX_DEFAULTS["cit_standard_rate"],
        "pv_depreciation_years": TAX_DEFAULTS["pv_depreciation_years"],
        "direct_ownership": case_config.get("direct_ownership", {"enabled": True}),
        "placeholder_keys": sorted(placeholder_keys()),
        "pv_poa_irradiance_series": production.get("poa_wm2") or None,
    }
    for key in RATE_VINTAGE_KEYS:
        assumptions[key] = tariff_extras[key]

    return {"payload": payload, "assumptions": assumptions}
