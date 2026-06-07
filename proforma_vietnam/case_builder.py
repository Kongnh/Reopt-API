import csv
from pathlib import Path

from proforma_vietnam import pvwatts_client
from proforma_vietnam.dppa_settlement import (
    DEFAULT_ALLOCATION_FRACTION_DELTA,
    DEFAULT_CFD_STRIKE_ESCALATION_RATE,
    DEFAULT_C_CL_SETTLEMENT_ADDER_VND_PER_KWH,
    DEFAULT_C_DPPA_SERVICE_FEE_VND_PER_KWH,
    DEFAULT_TRANSMISSION_LOSS_FACTOR_K,
    DISTRIBUTION_LOSS_FACTOR_KPP_BY_VOLTAGE,
    DPPA_TYPE_GRID_CFD,
    DPPA_TYPE_NONE,
    load_cfmp_series,
    load_fmp_series,
)
from reoptjl.src.vietnam import build_evn_tariff
from reoptjl.src.vietnam.evn_tariff import _normalize_voltage_level


DEFAULT_COUNTRY = "Vietnam"
DEFAULT_ANALYSIS_YEARS = 25
DEFAULT_TOU_SCHEDULE = "current"
DEFAULT_DEMAND_SAVINGS_ESCO_SHARE = 0.8
DEFAULT_GRID_CHARGING_ENABLED = False

DPPA_VOLTAGE_ELIGIBLE_GRID_CFD = {"110kv_and_above", "22_to_110kv"}
DEFAULT_FMP_SERIES_PATH = "DPPA DOC/fmp_cfmp_vn.json"

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
    voltage_key = _normalize_voltage_level(tariff_config["voltage_level"])
    dppa_inputs = _dppa_inputs(case_config.get("dppa"), voltage_key, tariff_config)

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
            dppa_inputs,
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
            dppa_inputs,
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


def _storage_inputs(storage_config, esco_contract, dppa_inputs):
    storage = _allowlisted(storage_config, STORAGE_PAYLOAD_KEYS)
    if dppa_inputs is not None and dppa_inputs["type"] != DPPA_TYPE_NONE:
        # Co-located BESS only under DPPA: charges from PV, not from the grid.
        storage["can_grid_charge"] = False
        return storage
    if "can_grid_charge" not in storage:
        storage["can_grid_charge"] = esco_contract.get(
            "grid_charging_enabled",
            DEFAULT_GRID_CHARGING_ENABLED,
        )
    storage.setdefault("can_grid_charge", DEFAULT_GRID_CHARGING_ENABLED)
    return storage


def _dppa_inputs(dppa_config, voltage_key, tariff_config):
    if not dppa_config:
        return None

    dppa_type = dppa_config.get("type", DPPA_TYPE_NONE)
    if dppa_type == DPPA_TYPE_NONE:
        return {"type": DPPA_TYPE_NONE}
    if dppa_type != DPPA_TYPE_GRID_CFD:
        raise ValueError(
            f"dppa.type must be one of {{'none', '{DPPA_TYPE_GRID_CFD}'}}, got '{dppa_type}'."
        )

    if voltage_key not in DPPA_VOLTAGE_ELIGIBLE_GRID_CFD:
        raise ValueError(
            f"dppa.type='{DPPA_TYPE_GRID_CFD}' requires a voltage_level in "
            f"{sorted(DPPA_VOLTAGE_ELIGIBLE_GRID_CFD)} per ND57 Art. 16; got '{voltage_key}'."
        )

    for required in ("cfd_strike_per_kwh_vnd", "cfd_contract_volume_kwh_per_hour"):
        if dppa_config.get(required) is None:
            raise ValueError(
                f"dppa.{required} is required when dppa.type='{DPPA_TYPE_GRID_CFD}'."
            )

    fmp_path = dppa_config.get("fmp_series_path", DEFAULT_FMP_SERIES_PATH)
    fmp_resolved = _resolve_fmp_path(fmp_path)
    fmp_series = list(load_fmp_series(fmp_resolved))
    try:
        cfmp_series = list(load_cfmp_series(fmp_resolved))
    except ValueError:
        # Older FMP files may not carry the CFMP column; fall back to FMP for C_DN.
        cfmp_series = list(fmp_series)

    kpp = dppa_config.get("distribution_loss_factor_kpp")
    if kpp is None:
        kpp = DISTRIBUTION_LOSS_FACTOR_KPP_BY_VOLTAGE[voltage_key]

    return {
        "type": DPPA_TYPE_GRID_CFD,
        "cfd_strike_per_kwh_vnd": dppa_config["cfd_strike_per_kwh_vnd"],
        "cfd_strike_escalation_rate": dppa_config.get(
            "cfd_strike_escalation_rate",
            DEFAULT_CFD_STRIKE_ESCALATION_RATE,
        ),
        "cfd_contract_volume_kwh_per_hour": dppa_config["cfd_contract_volume_kwh_per_hour"],
        "transmission_loss_factor_k": dppa_config.get(
            "transmission_loss_factor_k",
            DEFAULT_TRANSMISSION_LOSS_FACTOR_K,
        ),
        "distribution_loss_factor_kpp": kpp,
        "allocation_fraction_delta": dppa_config.get(
            "allocation_fraction_delta",
            DEFAULT_ALLOCATION_FRACTION_DELTA,
        ),
        "c_dppa_service_fee_vnd_per_kwh": dppa_config.get(
            "c_dppa_service_fee_vnd_per_kwh",
            DEFAULT_C_DPPA_SERVICE_FEE_VND_PER_KWH,
        ),
        "c_cl_settlement_adder_vnd_per_kwh": dppa_config.get(
            "c_cl_settlement_adder_vnd_per_kwh",
            DEFAULT_C_CL_SETTLEMENT_ADDER_VND_PER_KWH,
        ),
        "fee_escalation_rate": dppa_config.get(
            "fee_escalation_rate",
            tariff_config.get("evn_energy_escalation_rate", 0.0),
        ),
        "fmp_series_path": fmp_path,
        "fmp_series_vnd_per_kwh": fmp_series,
        "cfmp_series_vnd_per_kwh": cfmp_series,
    }


def _resolve_fmp_path(fmp_path):
    path = Path(fmp_path)
    if path.is_absolute():
        return str(path)
    repo_root = Path(__file__).resolve().parents[1]
    return str(repo_root / fmp_path)


def _assumptions(case_config, financial, technologies, esco_contract, tariff_config, dppa_inputs):
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
    if dppa_inputs is not None and dppa_inputs["type"] != DPPA_TYPE_NONE:
        assumptions["dppa"] = dppa_inputs
    return assumptions


def _capex_assumptions(technologies, exchange_rate):
    assumptions = {}
    pv = technologies.get("pv", {})
    storage = technologies.get("storage", {})

    if pv.get("size_kw") is not None and pv.get("installed_cost_per_kw") is not None:
        assumptions["pv_capex_usd"] = pv["size_kw"] * pv["installed_cost_per_kw"]

    # bess_capex_usd is only emitted when storage size is preset in case.json
    # (i.e. the user is forcing a fixed system). When the optimizer chooses
    # size, esco_pro_forma derives capex from REopt outputs at report time —
    # writing a stale or zero value here would silently override the truth.
    storage_capex = 0
    size_preset = (
        storage.get("size_kw") is not None
        or storage.get("size_kwh") is not None
    )
    if storage.get("size_kw") is not None and storage.get("installed_cost_per_kw") is not None:
        storage_capex += storage["size_kw"] * storage["installed_cost_per_kw"]
    if storage.get("size_kwh") is not None and storage.get("installed_cost_per_kwh") is not None:
        storage_capex += storage["size_kwh"] * storage["installed_cost_per_kwh"]
    if storage.get("installed_cost_constant") is not None:
        storage_capex += storage["installed_cost_constant"]
    if size_preset and storage_capex > 0:
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
