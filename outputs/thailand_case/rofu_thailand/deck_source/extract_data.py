"""Deck data from the six Rofu cases on master: case table, curtailment,
monthly load, average weekday profile, case 6 typical-day dispatch, DSCR by
year for cases 5 and 6, cash-flow summaries. Writes deck_data.json."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/kongn/Pictures/CodeProject/Reopt API/REopt_API")
sys.path.insert(0, str(ROOT))
from proforma_vietnam.esco_pro_forma import calculate_esco_pro_forma_from_reopt_results
from proforma_thailand.report import (
    _pv_capex, _storage_capex, annual_opex_usd, cash_flow_overrides_from_assumptions,
    compute_power_factor_compensation,
)
from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of


def th_over(a, r):
    """The exact override block build_thailand_report applies (power factor,
    insurance in O&M), without building the workbook."""
    o = r.get("outputs") or {}; i = r.get("inputs") or {}
    pv_raw = o.get("PV"); pv_list = pv_raw if isinstance(pv_raw, list) else ([pv_raw] if pv_raw else [])
    overrides = cash_flow_overrides_from_assumptions(a)
    mitigation = compute_power_factor_compensation(a)["mitigation_cost_usd"]
    if mitigation:
        overrides["other_capex_vnd"] = (overrides.get("other_capex_vnd", 0.0) + mitigation)
    base_om = a.get("annual_om_usd")
    if base_om is None:
        base_om = (o.get("Financial") or {}).get("year_one_om_costs_before_tax") or 0.0
    overrides["annual_om_vnd"] = annual_opex_usd(
        _pv_capex(pv_list), _storage_capex(i.get("ElectricStorage") or {}, o.get("ElectricStorage") or {}),
        overrides.get("other_capex_vnd") or 0.0, base_om, value_of(FINANCIAL_DEFAULTS, "insurance_rate_fraction"))
    return overrides

OUT = ROOT / "tmp/presentations/rofu_feasibility/deck_data.json"
STEPS = 4
LABELS = {1: "Roof, low", 2: "Roof, mid", 3: "Roof, high", 4: "No roof limit",
          5: "Roof, low, with storage", 6: "No roof limit, with storage"}
data = {"cases": []}


def series(x):
    return list(x or [])


def pv_block(o):
    pv = o.get("PV")
    return (pv[0] if pv else {}) if isinstance(pv, list) else (pv or {})


for n in range(1, 7):
    d = ROOT / f"outputs/thailand_case/rofu_thailand/case_{n}"
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    a = json.loads((d / "assumptions.json").read_text(encoding="utf-8"))
    s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    cash = calculate_esco_pro_forma_from_reopt_results(r, esco_energy_discount_fraction=0.0, **th_over(a, r))
    rows = cash["annual_cash_flows"]; summ = cash["summary"]
    o = r["outputs"]; pv = pv_block(o); es = o.get("ElectricStorage") or {}
    produced = pv.get("annual_energy_produced_kwh") or 0.0   # levelized basis, as the memo
    curtailed = sum(series(pv.get("electric_curtailed_series_kw"))) / STEPS
    dscr = [row.get("dscr") for row in rows]
    case = {
        "n": n, "label": LABELS[n],
        "pv_kw": pv.get("size_kw", 0.0), "bess_kw": es.get("size_kw", 0.0), "bess_kwh": es.get("size_kwh", 0.0),
        "capex_usd": summ["total_capex_usd"], "year1_savings_usd": rows[0]["offtaker_savings_usd"],
        "grid_offset": s.get("grid_offset_fraction"), "tco2e": s.get("annual_avoided_tco2e"),
        "equity_irr": summ.get("equity_irr_fraction"), "npv_usd": summ["npv_usd"],
        "equity_usd": summ.get("equity_investment_usd"), "debt_usd": summ.get("debt_principal_usd"),
        "payback_years": summ.get("simple_payback_years"),
        "curtailed_fraction": (curtailed / produced) if produced else 0.0,
        "annual_pv_kwh": s.get("annual_pv_kwh"), "dscr_by_year": dscr,
        "avg_dscr": summ.get("average_dscr"), "min_dscr": min(x for x in dscr if x is not None),
        "replacement_by_year": [row.get("replacement_cost_usd", 0.0) for row in rows],
        "cfads_by_year": [row.get("cash_available_for_debt_service_usd") for row in rows],
        "debt_service_by_year": [row.get("debt_service_usd") for row in rows],
        "savings_by_year": [row.get("offtaker_savings_usd") for row in rows],
        "bau_bill_year1": rows[0]["bau_evn_bill_usd"],
    }
    data["cases"].append(case)
    if n == 1:
        load = series(o["ElectricLoad"]["load_series_kw"])
        # monthly energy (kWh) and average weekday profile (kW by hour)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        monthly = []
        idx = 0
        for dm in days_in_month:
            n_steps = dm * 24 * STEPS
            monthly.append(sum(load[idx:idx + n_steps]) / STEPS)
            idx += n_steps
        data["monthly_load_mwh"] = [m / 1000 for m in monthly]
        data["annual_load_kwh"] = sum(load) / STEPS
        by_hour = [0.0] * 24; counts = [0] * 24
        for i, kw in enumerate(load):
            h = (i // STEPS) % 24
            by_hour[h] += kw; counts[h] += 1
        data["avg_load_by_hour_kw"] = [by_hour[h] / counts[h] for h in range(24)]
        data["annual_load_kwh_summary"] = s.get("annual_load_kwh")
    if n == 6:
        # typical-day dispatch (annual average by hour): PV to load, PV to battery, battery to load, grid, curtailed
        def avg_by_hour(x):
            x = series(x); out = [0.0] * 24; c = [0] * 24
            for i, v in enumerate(x):
                h = (i // STEPS) % 24; out[h] += v; c[h] += 1
            return [out[h] / c[h] if c[h] else 0.0 for h in range(24)]
        data["case6_dispatch"] = {
            "pv_to_load": avg_by_hour(pv.get("electric_to_load_series_kw")),
            "pv_to_storage": avg_by_hour(pv.get("electric_to_storage_series_kw")),
            "pv_curtailed": avg_by_hour(pv.get("electric_curtailed_series_kw")),
            "storage_to_load": avg_by_hour(es.get("storage_to_load_series_kw")),
            "grid_to_load": avg_by_hour(o["ElectricUtility"]["electric_to_load_series_kw"]),
            "grid_to_storage": avg_by_hour(o["ElectricUtility"].get("electric_to_storage_series_kw")),
            "load": avg_by_hour(o["ElectricLoad"]["load_series_kw"]),
        }
        data["case6_assumptions"] = {k: a.get(k) for k in (
            "pv_installed_cost_per_kw", "bess_installed_cost_per_kw", "bess_installed_cost_per_kwh",
            "annual_om_usd", "debt_fraction", "debt_interest_rate_fraction", "debt_term_years",
            "exchange_rate_thb_per_usd", "pv_degradation_rate", "om_escalation_rate",
            "evn_energy_escalation_rate", "pv_depreciation_years", "battery_replacement_year",
            "bess_replace_cost_per_kw", "bess_replace_cost_per_kwh", "pv_inverter_replacement_year",
            "pv_inverter_replacement_fraction_of_pv_capex", "specific_yield_kwh_per_kwp",
            "performance_ratio", "poa_irradiation_kwh_per_m2", "emissions_factor_kg_per_kwh")}
        data["case6_assumption_keys"] = sorted(k for k in a.keys() if not isinstance(a[k], list))
OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
for c in data["cases"]:
    print(c["n"], c["label"], round(c["pv_kw"]), round(c["bess_kw"]), round(c["bess_kwh"]), round(c["capex_usd"]),
          round(c["year1_savings_usd"]), "%.1f%%" % (100 * c["grid_offset"]), round(c["tco2e"]),
          "%.1f%%" % (100 * c["equity_irr"]), round(c["npv_usd"]), "curt %.1f%%" % (100 * c["curtailed_fraction"]),
          "minDSCR %.2f" % c["min_dscr"], "payback %.1f" % (c["payback_years"] or 0))
print("monthly MWh", [round(m) for m in data["monthly_load_mwh"]])
print("annual load", round(data["annual_load_kwh"]), data["annual_load_kwh_summary"])
print("case6 assumptions", data["case6_assumptions"])
print("keys", data["case6_assumption_keys"])
