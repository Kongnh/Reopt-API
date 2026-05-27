import csv

from proforma_vietnam import pvwatts_client
from reoptjl.src.vietnam import build_evn_tariff


DEFAULT_COUNTRY = "Vietnam"
DEFAULT_ANALYSIS_YEARS = 25
DEFAULT_TOU_SCHEDULE = "current"
DEFAULT_DEMAND_SAVINGS_ESCO_SHARE = 0.8
DEFAULT_GRID_CHARGING_ENABLED = False

FINANCIAL_PAYLOAD_KEYS = [
    "analysis_years",
    "owner_discount_rate_fraction",
]
FINANCIAL_ASSUMPTION_KEYS = [
    "owner_discount_rate_fraction",
    "debt_fraction",
    "debt_interest_rate_fraction",
    "debt_term_years",
    "annual_om_usd",
    "annual_om_vnd",
]
PV_PAYLOAD_KEYS = [
    "min_kw",
    "max_kw",
    "installed_cost_per_kw",
    "om_cost_per_kw",
    "degradation_fraction",
    "production_factor_series",
]
STORAGE_PAYLOAD_KEYS = [
    "min_kw",
    "max_kw",
    "min_kwh",
    "max_kwh",
    "installed_cost_per_kw",
    "installed_cost_per_kwh",
    "installed_cost_constant",
    "replace_cost_per_kw",
    "replace_cost_per_kwh",
    "replace_cost_constant",
    "inverter_replacement_year",
    "battery_replacement_year",
    "cost_constant_replacement_year",
    "om_cost_fraction_of_installed_cost",
    "can_grid_charge",
]


def build_vietnam_case(case_config):
    load_config = case_config.get("load_profile", {})
    tariff_config = case_config.get("tariff", {})
    technologies = case_config.get("technologies", {})
    financial = case_config.get("financial", {})
    esco_contract = case_config.get("esco_contract", {})

    year = load_config.get("year") or tariff_config.get("year")
    loads_kw = _read_8760_load_csv(load_config["path"])
    tariff = _build_tariff(tariff_config)
    site = case_config.get("site", {})
    pv_inputs = _pv_inputs(technologies.get("pv", {}), site)

    payload = {
        "Meta": {
            "description": case_config.get("case", {}).get("name", "Vietnam REopt case"),
        },
        "Settings": {
            "time_steps_per_hour": 1,
        },
        "Site": {
            "latitude": site["latitude"],
            "longitude": site["longitude"],
        },
        "ElectricLoad": {
            "year": year,
            "loads_kw": loads_kw,
        },
        "ElectricTariff": tariff,
        "Financial": _financial_inputs(financial),
        "PV": pv_inputs,
        "ElectricStorage": _storage_inputs(
            technologies.get("storage", {}),
            esco_contract,
        ),
    }

    return {
        "payload": payload,
        "assumptions": _assumptions(
            case_config,
            financial,
            technologies,
            esco_contract,
            tariff_config,
        ),
    }


def _read_8760_load_csv(path):
    values = []
    with open(path, newline="") as csv_file:
        for row in csv.reader(csv_file):
            if not row:
                continue
            try:
                value = float(row[0])
            except ValueError:
                continue
            if value < 0:
                raise ValueError("Load profile cannot contain negative values.")
            values.append(value)

    if len(values) != 8760:
        raise ValueError("Vietnam case builder requires exactly 8760 hourly load values.")

    return values


def _build_tariff(tariff_config):
    return build_evn_tariff(
        year=tariff_config["year"],
        voltage_level=tariff_config["voltage_level"],
        currency=tariff_config.get("currency", "usd"),
        exchange_rate_vnd_per_usd=tariff_config.get("exchange_rate_vnd_per_usd", 25000),
        tou_schedule=tariff_config.get("tou_schedule", DEFAULT_TOU_SCHEDULE),
        two_component_pilot_enabled=tariff_config.get("two_component_pilot_enabled", False),
    )


def _financial_inputs(financial):
    inputs = {
        "analysis_years": financial.get("analysis_years", DEFAULT_ANALYSIS_YEARS),
    }
    for key in FINANCIAL_PAYLOAD_KEYS:
        if key in financial:
            inputs[key] = financial[key]
    return inputs


def _pv_inputs(pv_config, site):
    pv = _allowlisted(pv_config, PV_PAYLOAD_KEYS)
    if "production_factor_series" not in pv:
        pv["production_factor_series"] = pvwatts_client.fetch_production_factor_series(
            latitude=site["latitude"],
            longitude=site["longitude"],
            overrides=pv_config.get("pvwatts"),
        )
    return pv


def _storage_inputs(storage_config, esco_contract):
    storage = _allowlisted(storage_config, STORAGE_PAYLOAD_KEYS)
    if "can_grid_charge" not in storage:
        storage["can_grid_charge"] = esco_contract.get(
            "grid_charging_enabled",
            DEFAULT_GRID_CHARGING_ENABLED,
        )
    storage.setdefault("can_grid_charge", DEFAULT_GRID_CHARGING_ENABLED)
    return storage


def _assumptions(case_config, financial, technologies, esco_contract, tariff_config):
    if esco_contract.get("esco_energy_discount_fraction") is None:
        raise ValueError("esco_contract.esco_energy_discount_fraction is required.")

    assumptions = {
        "case_name": case_config.get("case", {}).get("name", "Vietnam REopt case"),
        "country": DEFAULT_COUNTRY,
        "tariff_year": tariff_config.get("year"),
        "voltage_level": tariff_config.get("voltage_level"),
        "tou_schedule": tariff_config.get("tou_schedule", DEFAULT_TOU_SCHEDULE),
        "exchange_rate_vnd_per_usd": tariff_config.get("exchange_rate_vnd_per_usd"),
        "evn_energy_escalation_rate": tariff_config.get("evn_energy_escalation_rate"),
        "evn_capacity_escalation_rate": tariff_config.get("evn_capacity_escalation_rate"),
        "esco_energy_discount_fraction": esco_contract.get("esco_energy_discount_fraction"),
        "demand_savings_esco_share": esco_contract.get(
            "demand_savings_esco_share",
            DEFAULT_DEMAND_SAVINGS_ESCO_SHARE,
        ),
        "grid_charging_enabled": esco_contract.get(
            "grid_charging_enabled",
            DEFAULT_GRID_CHARGING_ENABLED,
        ),
    }
    assumptions.update(_allowlisted(financial, FINANCIAL_ASSUMPTION_KEYS))
    exchange_rate = tariff_config.get("exchange_rate_vnd_per_usd")
    if financial.get("annual_om_vnd") is not None:
        assumptions["annual_om_usd"] = _vnd_to_usd(financial["annual_om_vnd"], exchange_rate)
        assumptions.pop("annual_om_vnd", None)
    assumptions.update(_capex_assumptions(technologies, exchange_rate))
    assumptions = {
        key: value
        for key, value in assumptions.items()
        if value is not None
    }
    return assumptions


def _capex_assumptions(technologies, exchange_rate):
    assumptions = {}
    pv = technologies.get("pv", {})
    storage = technologies.get("storage", {})

    if pv.get("size_kw") is not None and pv.get("installed_cost_per_kw") is not None:
        assumptions["pv_capex_usd"] = pv["size_kw"] * pv["installed_cost_per_kw"]

    storage_capex = 0
    has_storage_capex = False
    if storage.get("size_kw") is not None and storage.get("installed_cost_per_kw") is not None:
        storage_capex += storage["size_kw"] * storage["installed_cost_per_kw"]
        has_storage_capex = True
    if storage.get("size_kwh") is not None and storage.get("installed_cost_per_kwh") is not None:
        storage_capex += storage["size_kwh"] * storage["installed_cost_per_kwh"]
        has_storage_capex = True
    if storage.get("installed_cost_constant") is not None:
        storage_capex += storage["installed_cost_constant"]
        has_storage_capex = True
    if has_storage_capex:
        assumptions["bess_capex_usd"] = storage_capex

    return assumptions


def _vnd_to_usd(value, exchange_rate):
    if exchange_rate is None:
        return value
    return value / exchange_rate


def _allowlisted(source, keys):
    return {
        key: source[key]
        for key in keys
        if key in source
    }
