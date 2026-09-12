"""Fade-aware battery sizing probe (research line, 2026-09-12).

Sizes the battery of a kept case three ways and scores every candidate with
the same fade-derated pro forma, so the comparison is on the number the
workbook reports:

  blind  REopt as run today: no ageing in the objective, sizes free.
  deg    REopt with ``model_degradation`` on (augmentation strategy). The
         hours-per-step factor of REopt's SOH recurrence is cancelled by
         scaling the coefficients by 1/h, so the optimiser ages the battery
         exactly as ``battery_soh`` does at h = 1; k_cyc comes from the
         8,000 EFC ruling.
  grid   REopt without ageing at fixed energy capacities (fractions of the
         blind size, power free), the derated NPV read off each point. The
         deg size is also solved this way so it sits on the same curve.

Vietnam cases are additionally solved with the US incentives that REopt
defaults ON (30 percent ITC, 5-year MACRS with bonus) switched off and the
Financial block aligned to the pro forma (10 percent discount, 20 percent
CIT, EVN escalation): the kept Vietnam solves carry those defaults, so their
sizes are not comparable to an ageing-aware solve at full price. Thailand's
builder already zeroes them.

Solves go straight to the research Julia server on port 8082 (Django does
not accept ``model_degradation``, and the shared server's http.jl cannot type
the vector degradation inputs); the echoed inputs of the kept run are self-contained
(load, production factor and tariff series are inline). Each solve is saved
as a Django-shaped results file so the pro forma reads it unchanged. Nothing
under the case directory is touched.

Usage (from the repository root, research worktree):

    python -m proforma_vietnam.tools.fade_sizing_probe \
        --case-dir outputs/vietnam_case/factory_a/case_1 \
        --out outputs/research/fade_sizing/vn_case_1
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from proforma_vietnam.battery_soh import (
    battery_state_of_health,
    cycle_fade_coefficient_from_life,
)
from proforma_vietnam.defaults import (
    BESS_CALENDAR_FADE_COEFFICIENT,
    BESS_CALENDAR_FADE_EXPONENT,
    BESS_CYCLE_LIFE_EFC,
    BESS_END_OF_LIFE_SOH,
    FINANCIAL_DEFAULTS,
    TAX_DEFAULTS,
)
from proforma_vietnam.esco_pro_forma import (
    _as_list,
    _levelization_factor,
    _series,
    calculate_esco_pro_forma_from_reopt_results,
)
from proforma_vietnam.run_dppa_negotiation_sweep import (
    cash_flow_overrides_from_assumptions as vietnam_overrides,
)
from proforma_thailand.report import (
    cash_flow_overrides_from_assumptions as thailand_overrides,
)

# The research worktree runs its own Julia server (container julia_api_soh,
# port 8082) whose http.jl coerces the vector-valued degradation inputs;
# the shared server on 8081 rejects them (REopt.jl 0.57 typing).
JULIA_URL = "http://localhost:8082/reopt/"
DEFAULT_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25)
DEFAULT_DECLINATION = 0.03
DAYS_PER_YEAR = 365


def _strip(block):
    return {k: v for k, v in block.items() if v not in [None, [], {}, ""]}


def _pv_block(inputs):
    pv = inputs.get("PV")
    if isinstance(pv, list):
        return pv[0] if pv else None
    return pv


def _pv_output(outputs):
    pv = outputs.get("PV")
    if isinstance(pv, list):
        return pv[0] if pv else {}
    return pv or {}


def base_inputs(results):
    """The kept run's echoed inputs, stripped the way the Celery task strips them."""
    inputs = json.loads(json.dumps(results["inputs"]))
    inputs = {
        section: (_strip(block) if isinstance(block, dict) else block)
        for section, block in inputs.items()
    }
    inputs = _strip(inputs)
    settings = inputs.setdefault("Settings", {})
    settings.setdefault("timeout_seconds", 600)
    settings.setdefault("optimality_tolerance", 0.001)
    settings["run_bau"] = True
    settings["solver_name"] = "HiGHS"
    for key in ("replace_cost_per_kw", "replace_cost_per_kwh", "replace_cost_constant"):
        inputs["ElectricStorage"][key] = 0.0
    return inputs


def align_vietnam_financials(inputs, assumptions):
    """Take the US incentive defaults out of the objective and align the
    Financial block with the pro forma. Returns the fields changed."""
    changed = {}
    fin = inputs["Financial"]
    rate = assumptions.get("owner_discount_rate_fraction", 0.10)
    escalation = assumptions.get(
        "evn_energy_escalation_rate", FINANCIAL_DEFAULTS["evn_energy_escalation_rate"]
    )
    targets = {
        "owner_discount_rate_fraction": rate,
        "offtaker_discount_rate_fraction": rate,
        "owner_tax_rate_fraction": TAX_DEFAULTS["cit_standard_rate"],
        "offtaker_tax_rate_fraction": TAX_DEFAULTS["cit_standard_rate"],
        "elec_cost_escalation_rate_fraction": escalation,
        "om_cost_escalation_rate_fraction": FINANCIAL_DEFAULTS["om_escalation_rate"],
    }
    for key, value in targets.items():
        if fin.get(key) != value:
            changed["Financial." + key] = (fin.get(key), value)
            fin[key] = value
    pv = _pv_block(inputs)
    if pv is not None:
        for key in ("federal_itc_fraction", "macrs_option_years", "macrs_bonus_fraction"):
            if pv.get(key) not in (0, 0.0):
                changed["PV." + key] = (pv.get(key), 0)
                pv[key] = 0
    es = inputs["ElectricStorage"]
    for key in ("total_itc_fraction", "macrs_option_years", "macrs_bonus_fraction"):
        if es.get(key) not in (0, 0.0):
            changed["ElectricStorage." + key] = (es.get(key), 0)
            es[key] = 0
    return changed


def degradation_block(time_steps_per_hour, declination, cycle_life_efc=BESS_CYCLE_LIFE_EFC):
    """REopt degradation inputs that reproduce the h = 1 recurrence of
    ``battery_soh`` at this resolution (coefficients scaled by 1/h)."""
    h = 1.0 / time_steps_per_hour
    k_cyc = cycle_fade_coefficient_from_life(cycle_life_efc, BESS_END_OF_LIFE_SOH)
    return {
        "calendar_fade_coefficient": BESS_CALENDAR_FADE_COEFFICIENT / h,
        "cycle_fade_coefficient": [k_cyc / h],
        "cycle_fade_fraction": [1.0],
        "time_exponent": BESS_CALENDAR_FADE_EXPONENT,
        "installed_cost_per_kwh_declination_rate": declination,
        "maintenance_strategy": "augmentation",
    }


def pin_energy(inputs, kwh):
    es = inputs["ElectricStorage"]
    if kwh <= 0:
        es["min_kw"] = es["max_kw"] = 0.0
        es["min_kwh"] = es["max_kwh"] = 0.0
    else:
        es["min_kwh"] = es["max_kwh"] = float(kwh)


def solve(inputs, tag, solves_dir, julia_url=JULIA_URL):
    """POST to the Julia server; cache the Django-shaped result under solves_dir."""
    path = solves_dir / (tag + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    req = urllib.request.Request(
        julia_url,
        data=json.dumps(inputs).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=4000) as resp:
            raw = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        (solves_dir / (tag + ".error.txt")).write_text(body, encoding="utf-8")
        raise RuntimeError("Julia returned HTTP %s for %s: %s" % (exc.code, tag, body[:500]))
    outputs = raw.get("results", raw)
    results = {
        "run_uuid": "probe-" + tag,
        "status": outputs.get("status"),
        "solve_seconds": round(time.time() - started, 1),
        "inputs": inputs,
        "outputs": outputs,
    }
    path.write_text(json.dumps(results), encoding="utf-8")
    return results


def _cash_flow(results, assumptions, country):
    if country == "thailand":
        return calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.0, **thailand_overrides(assumptions)
        )
    return calculate_esco_pro_forma_from_reopt_results(
        results,
        esco_energy_discount_fraction=assumptions["esco_energy_discount_fraction"],
        **vietnam_overrides(assumptions)
    )


def _present_value(values_by_year, rate):
    return sum(v / (1.0 + rate) ** y for y, v in enumerate(values_by_year, start=1))


def augmentation_cost(results, soh_by_day, declination, rate):
    """Present value of topping the capacity up daily at REopt's declining
    price, computed on the replica's SOH curve (REopt's own formula)."""
    es_in = results["inputs"]["ElectricStorage"]
    size_kwh = results["outputs"]["ElectricStorage"]["size_kwh"]
    price = es_in["installed_cost_per_kwh"]
    total = 0.0
    by_year = [0.0] * (len(soh_by_day) // DAYS_PER_YEAR)
    for day in range(2, len(soh_by_day) + 1):
        lost_kwh = (soh_by_day[day - 2] - soh_by_day[day - 1]) * size_kwh
        exponent = (day - 1) / DAYS_PER_YEAR
        total += price * (1 - declination) ** exponent / (1 + rate) ** exponent * lost_kwh
        by_year[(day - 1) // DAYS_PER_YEAR] += price * (1 - declination) ** exponent * lost_kwh
    return total, by_year


def daily_soh(results, cycle_life_efc=BESS_CYCLE_LIFE_EFC, de_levelize=True):
    """The pro forma's SOH curve (h = 1) on this solve's dispatch; with
    de_levelize False the raw REopt series is used, which is what REopt's own
    recurrence sees."""
    outputs = results["outputs"]
    es = outputs.get("ElectricStorage") or {}
    size_kwh = es.get("size_kwh") or 0.0
    steps = results["inputs"]["Settings"].get("time_steps_per_hour", 1)
    years = results["inputs"]["Financial"].get("analysis_years", 20)
    factor = _levelization_factor(_as_list(outputs.get("PV"))) if de_levelize else 1.0
    discharge = [v / factor for v in _series(es.get("storage_to_load_series_kw"))]
    soc = _series(es.get("soc_series_fraction"))
    if size_kwh <= 0 or len(discharge) < DAYS_PER_YEAR * 24 * steps:
        return None
    soh = battery_state_of_health(
        size_kwh=size_kwh, soc_series_fraction=soc, discharge_series_kw=discharge,
        time_steps_per_hour=steps, project_years=years, cycle_life_efc=cycle_life_efc)
    return None if soh is None else soh["soh_fraction_by_day"]


def evaluate(results, assumptions, country, declination):
    outputs = results["outputs"]
    es = outputs.get("ElectricStorage") or {}
    financial = outputs.get("Financial") or {}
    cash = _cash_flow(results, assumptions, country)
    rows = cash["annual_cash_flows"]
    summary = cash["summary"]
    dscr = [row["dscr"] for row in rows if row.get("dscr") is not None]
    rate = assumptions.get("owner_discount_rate_fraction", 0.10)
    metrics = {
        "status": results.get("status") or outputs.get("status"),
        "solve_seconds": results.get("solve_seconds"),
        "pv_kw": _pv_output(outputs).get("size_kw", 0.0),
        "bess_kw": es.get("size_kw", 0.0),
        "bess_kwh": es.get("size_kwh", 0.0),
        "capex_usd": financial.get("initial_capital_costs"),
        "reopt_capex_after_incentives_usd": financial.get("initial_capital_costs_after_incentives"),
        "reopt_npv_usd": (financial.get("lcc_bau") or 0.0) - (financial.get("lcc") or 0.0),
        "npv_usd": summary["npv_usd"],
        "equity_irr": summary.get("equity_irr_fraction"),
        "project_irr": summary.get("project_irr_fraction"),
        "min_dscr": min(dscr) if dscr else None,
        "year1_revenue_usd": rows[0].get("esco_revenue_usd"),
        "year1_offtaker_savings_usd": rows[0].get("offtaker_savings_usd"),
        "fade_loss_total_usd": sum(row.get("battery_fade_loss_usd", 0.0) or 0.0 for row in rows),
        "fade_loss_pv_usd": _present_value(
            [row.get("battery_fade_loss_usd", 0.0) or 0.0 for row in rows], rate
        ),
    }
    fade = cash["derivation"].get("battery_fade")
    if fade:
        years = {y["year"]: y for y in fade["soh"]["years"]}
        soh_by_day = daily_soh(results)
        metrics.update({
            "soh_y10": years[10]["soh_end"] if 10 in years else None,
            "soh_y20": years[max(years)]["soh_end"],
            "efc_y1": fade["soh"]["year_one_efc"],
            "battery_energy_value_y1_usd": (
                fade.get("served_retail_value_usd", 0.0) + fade.get("unserved_energy_value_usd", 0.0)
            ),
            "battery_demand_savings_y1_usd": fade.get("demand_savings_usd", 0.0),
        })
        aug_pv, aug_by_year = augmentation_cost(results, soh_by_day, declination, rate)
        metrics["augmentation_pv_usd"] = aug_pv
        metrics["augmentation_year1_usd"] = aug_by_year[0] if aug_by_year else None
        reopt_soh = es.get("state_of_health")
        if reopt_soh:
            raw_replica = daily_soh(results, de_levelize=False)
            n = min(len(reopt_soh), len(raw_replica))
            metrics["reopt_soh_end"] = reopt_soh[-1]
            metrics["reopt_vs_replica_soh_max_abs_diff"] = max(
                abs(reopt_soh[i] - raw_replica[i]) for i in range(n)
            )
        if es.get("maintenance_cost") is not None:
            metrics["reopt_maintenance_cost_pv_usd"] = es["maintenance_cost"]
    return metrics


def run_probe(case_dir, out_dir, fractions, declination, deg_grid, julia_url, log=print):
    case_dir = Path(case_dir)
    out_dir = Path(out_dir)
    solves_dir = out_dir / "solves"
    solves_dir.mkdir(parents=True, exist_ok=True)
    country = "thailand" if "thailand" in str(case_dir).replace("\\", "/") else "vietnam"
    kept = json.loads((case_dir / "results.json").read_text(encoding="utf-8"))
    assumptions = json.loads((case_dir / "assumptions.json").read_text(encoding="utf-8"))
    steps_per_hour = kept["inputs"]["Settings"].get("time_steps_per_hour", 1)

    variants = {}

    def record(tag, kind, results, note=""):
        metrics = evaluate(results, assumptions, country, declination)
        metrics.update({"tag": tag, "kind": kind, "note": note})
        variants[tag] = metrics
        log("%-14s %-10s PV %8.0f kW  BESS %7.0f kW / %8.0f kWh  NPV %12s  minDSCR %s  SOH20 %s  %ss" % (
            tag, kind, metrics["pv_kw"], metrics["bess_kw"], metrics["bess_kwh"], "{:,.0f}".format(metrics["npv_usd"]),
            "%.2f" % metrics["min_dscr"] if metrics["min_dscr"] is not None else "-",
            "%.3f" % metrics["soh_y20"] if metrics.get("soh_y20") is not None else "-",
            metrics.get("solve_seconds")))
        (out_dir / "summary.json").write_text(json.dumps({
            "case_dir": str(case_dir), "country": country, "time_steps_per_hour": steps_per_hour,
            "declination": declination, "fractions": list(fractions), "variants": variants,
        }, indent=1), encoding="utf-8")
        return metrics

    record("kept", "blind", kept, "the kept solve, as run through Django")

    inputs = base_inputs(kept)
    changed = {}
    if country == "vietnam":
        changed = align_vietnam_financials(inputs, assumptions)
        log("aligned Vietnam objective: %s" % json.dumps(changed))
    (out_dir / "aligned_fields.json").write_text(json.dumps(changed, indent=1), encoding="utf-8")

    blind = record("blind", "blind", solve(inputs, "blind", solves_dir, julia_url),
                   "no ageing in the objective, sizes free" + (", incentives off" if changed else ""))
    blind_kwh = blind["bess_kwh"]

    deg_inputs = json.loads(json.dumps(inputs))
    deg_inputs["ElectricStorage"]["model_degradation"] = True
    deg_inputs["ElectricStorage"]["degradation"] = degradation_block(steps_per_hour, declination)
    deg = record("deg", "deg", solve(deg_inputs, "deg", solves_dir, julia_url),
                 "model_degradation on, augmentation, coefficients / h, sizes free")

    def grid_point(fraction, kwh, tag=None):
        tag = tag or ("grid_%.3f" % fraction)
        point = json.loads(json.dumps(inputs))
        pin_energy(point, kwh)
        metrics = record(tag, "grid", solve(point, tag, solves_dir, julia_url),
                         "blind dispatch at %.0f kWh (%.3f of blind)" % (kwh, fraction))
        metrics["fraction"] = fraction
        if deg_grid and kwh > 0:
            dpoint = json.loads(json.dumps(deg_inputs))
            pin_energy(dpoint, kwh)
            dm = record(tag + "_deg", "grid_deg", solve(dpoint, tag + "_deg", solves_dir, julia_url),
                        "fade-aware dispatch at %.0f kWh" % kwh)
            dm["fraction"] = fraction
        return metrics

    for fraction in fractions:
        grid_point(fraction, fraction * blind_kwh)
    if deg["bess_kwh"] > 0:
        grid_point(deg["bess_kwh"] / blind_kwh if blind_kwh else 0.0, deg["bess_kwh"], tag="grid_at_deg")

    # One refinement round around the best coarse point.
    grid = sorted((m["fraction"], m["npv_usd"]) for m in variants.values() if m["kind"] == "grid")
    if len(grid) >= 3:
        best_index = max(range(len(grid)), key=lambda i: grid[i][1])
        step = min(abs(grid[i + 1][0] - grid[i][0]) for i in range(len(grid) - 1)) / 2.0
        for fraction in (grid[best_index][0] - step, grid[best_index][0] + step):
            if fraction > 0 and all(abs(fraction - f) > 1e-6 for f, _ in grid):
                grid_point(fraction, fraction * blind_kwh)

    (out_dir / "summary.md").write_text(render_summary(out_dir / "summary.json"), encoding="utf-8")
    return variants


def render_summary(summary_path):
    data = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    rows = sorted(data["variants"].values(), key=lambda m: (m["kind"] != "blind", m["kind"], m["bess_kwh"]))
    lines = [
        "# %s (%s, %d steps/h)" % (data["case_dir"], data["country"], data["time_steps_per_hour"]),
        "",
        "| variant | kind | PV kW | BESS kW | BESS kWh | capex USD | REopt NPV | proforma NPV | equity IRR | min DSCR | SOH y20 | EFC y1 | fade loss PV | augmentation PV | REopt maint PV | solve s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            m["tag"], m["kind"], _f(m["pv_kw"]), _f(m["bess_kw"]), _f(m["bess_kwh"]), _f(m["capex_usd"]),
            _f(m["reopt_npv_usd"]), _f(m["npv_usd"]), _p(m["equity_irr"]),
            "-" if m["min_dscr"] is None else "%.2f" % m["min_dscr"],
            _p(m.get("soh_y20")), _f(m.get("efc_y1")), _f(m.get("fade_loss_pv_usd")),
            _f(m.get("augmentation_pv_usd")), _f(m.get("reopt_maintenance_cost_pv_usd")),
            m.get("solve_seconds") or "-"))
    return "\n".join(lines) + "\n"


def _f(v):
    return "-" if v is None else "{:,.0f}".format(v)


def _p(v):
    return "-" if v is None else "{:.1%}".format(v)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fractions", default=",".join(str(f) for f in DEFAULT_FRACTIONS))
    parser.add_argument("--declination", type=float, default=DEFAULT_DECLINATION)
    parser.add_argument("--deg-grid", action="store_true",
                        help="also solve every grid point with degradation on (fade-aware dispatch)")
    parser.add_argument("--julia-url", default=JULIA_URL)
    args = parser.parse_args(argv)
    fractions = tuple(float(f) for f in args.fractions.split(","))
    run_probe(args.case_dir, args.out, fractions, args.declination, args.deg_grid, args.julia_url,
              log=lambda s: print(s, flush=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
