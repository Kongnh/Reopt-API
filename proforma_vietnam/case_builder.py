import csv

from reoptjl.src.vietnam import build_evn_tariff


DEFAULT_COUNTRY = "Vietnam"
DEFAULT_ANALYSIS_YEARS = 25
DEFAULT_TOU_SCHEDULE = "current"
DEFAULT_DEMAND_SAVINGS_ESCO_SHARE = 0.8
DEFAULT_GRID_CHARGING_ENABLED = False


def build_vietnam_case(case_config):
    load_config = case_config.get("load_profile", {})
    tariff_config = case_config.get("tariff", {})
    technologies = case_config.get("technologies", {})
    financial = case_config.get("financial", {})
    esco_contract = case_config.get("esco_contract", {})

    year = load_config.get("year") or tariff_config.get("year")
    loads_kw = _read_8760_load_csv(load_config["path"])
    tariff = _build_tariff(tariff_config)

    payload = {
        "Meta": {
            "description": case_config.get("case", {}).get("name", "Vietnam REopt case"),
        },
        "Settings": {
            "time_steps_per_hour": 1,
        },
        "Site": {
            "latitude": case_config.get("site", {})["latitude"],
            "longitude": case_config.get("site", {})["longitude"],
        },
        "ElectricLoad": {
            "year": year,
            "loads_kw": loads_kw,
        },
        "ElectricTariff": tariff,
        "Financial": {
            "analysis_years": financial.get("analysis_years", DEFAULT_ANALYSIS_YEARS),
        },
        "PV": technologies.get("pv", {}).copy(),
        "ElectricStorage": _storage_inputs(technologies.get("storage", {})),
    }

    return {
        "payload": payload,
        "assumptions": _assumptions(case_config, esco_contract, tariff_config),
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
    )


def _storage_inputs(storage_config):
    storage = storage_config.copy()
    storage.setdefault("can_grid_charge", DEFAULT_GRID_CHARGING_ENABLED)
    return storage


def _assumptions(case_config, esco_contract, tariff_config):
    if esco_contract.get("esco_energy_discount_fraction") is None:
        raise ValueError("esco_contract.esco_energy_discount_fraction is required.")

    return {
        "case_name": case_config.get("case", {}).get("name", "Vietnam REopt case"),
        "country": DEFAULT_COUNTRY,
        "tariff_year": tariff_config.get("year"),
        "voltage_level": tariff_config.get("voltage_level"),
        "tou_schedule": tariff_config.get("tou_schedule", DEFAULT_TOU_SCHEDULE),
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
