import argparse
import json
from pathlib import Path

from openpyxl import load_workbook

from proforma_vietnam.dppa_negotiation_sweep import run_dppa_negotiation_sweep
from proforma_vietnam.dppa_negotiation_workbook import (
    build_dppa_negotiation_summary,
    build_dppa_negotiation_workbook,
)
from proforma_vietnam.esco_pro_forma import calculate_esco_pro_forma_from_reopt_results


DEFAULT_FACTORY_A_DIR = Path("outputs/vietnam_case/factory_a")
DEFAULT_OUTPUT_DIR_NAME = "dppa_negotiation_study"
DEFAULT_REFERENCE_CASE = "case_5"
RECONCILIATION_TOLERANCE = 1e-6


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the fixed-system Factory A DPPA commercial negotiation sweep."
    )
    parser.add_argument("--factory-a-dir", default=str(DEFAULT_FACTORY_A_DIR))
    parser.add_argument("--reference-case", default=DEFAULT_REFERENCE_CASE)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    factory_dir = Path(args.factory_a_dir)
    out_dir = (
        Path(args.out)
        if args.out
        else factory_dir / default_output_dir_name(args.reference_case)
    )
    run_factory_a_negotiation_sweep(
        factory_dir=factory_dir,
        out_dir=out_dir,
        reference_case=args.reference_case,
    )
    return 0


def default_output_dir_name(reference_case):
    if reference_case == DEFAULT_REFERENCE_CASE:
        return DEFAULT_OUTPUT_DIR_NAME
    return f"{DEFAULT_OUTPUT_DIR_NAME}_{reference_case}"


def reference_case_paths(factory_dir, reference_case):
    case_dir = Path(factory_dir) / reference_case
    return {
        "results": case_dir / "results.json",
        "assumptions": case_dir / "assumptions.json",
    }


def run_factory_a_negotiation_sweep(
    *,
    factory_dir,
    out_dir,
    reference_case=DEFAULT_REFERENCE_CASE,
):
    case_2_results_path = factory_dir / "case_2" / "results.json"
    case_2_assumptions_path = factory_dir / "case_2" / "assumptions.json"
    reference_paths = reference_case_paths(factory_dir, reference_case)
    reference_results_path = reference_paths["results"]
    reference_assumptions_path = reference_paths["assumptions"]

    case_2_results = _read_json(case_2_results_path)
    case_2_assumptions = _read_json(case_2_assumptions_path)
    reference_results = _read_json(reference_results_path)
    reference_assumptions = _read_json(reference_assumptions_path)
    reference_dppa_inputs = reference_assumptions["dppa"]
    reference_workbook_path = (
        factory_dir
        / reference_case
        / f"vietnam_report_{reference_results['run_uuid']}.xlsx"
    )

    case_2_cash_flow = _calculate_cash_flow(case_2_results, case_2_assumptions)

    def evaluator(dppa_inputs):
        assumptions = dict(reference_assumptions)
        assumptions["dppa"] = dppa_inputs
        return _calculate_cash_flow(reference_results, assumptions)

    study = run_dppa_negotiation_sweep(
        reference_dppa_inputs=reference_dppa_inputs,
        evaluator=evaluator,
        non_dppa_case_2_cash_flow=case_2_cash_flow,
        baseline_sources={
            "fixed_technical_results": str(reference_results_path),
            "non_dppa_case_2_assumptions": str(case_2_assumptions_path),
            "reference_case": reference_case,
            "validated_dppa_inputs": str(reference_assumptions_path),
            "reference_case_results": str(reference_results_path),
            "reference_case_workbook": str(reference_workbook_path),
            "case_2_run_uuid": case_2_results.get("run_uuid"),
            "reference_case_run_uuid": reference_results.get("run_uuid"),
        },
    )

    sweep_reference_cash_flow = evaluator(reference_dppa_inputs)
    direct_reference_cash_flow = _calculate_cash_flow(
        reference_results,
        reference_assumptions,
    )
    study["reconciliation"] = reconcile_cash_flows(
        sweep_reference_cash_flow,
        direct_reference_cash_flow,
        tolerance=RECONCILIATION_TOLERANCE,
    )
    study["workbook_reconciliation"] = reconcile_reference_workbook(
        sweep_reference_cash_flow,
        reference_workbook_path,
        tolerance=RECONCILIATION_TOLERANCE,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "results.json", study)
    workbook = build_dppa_negotiation_workbook(study)
    workbook.save(out_dir / "Factory_A_DPPA_Negotiation_Sweep.xlsx")
    (out_dir / "NEGOTIATION_SUMMARY.md").write_text(
        build_dppa_negotiation_summary(study),
        encoding="utf-8",
    )
    return study


def cash_flow_overrides_from_assumptions(assumptions):
    mapping = {
        "owner_discount_rate_fraction": "owner_discount_rate_fraction",
        "debt_fraction": "debt_fraction",
        "debt_interest_rate_fraction": "debt_interest_rate_fraction",
        "debt_term_years": "debt_term_years",
        "annual_om_usd": "annual_om_vnd",
        "pv_capex_usd": "pv_capex_vnd",
        "bess_capex_usd": "bess_capex_vnd",
        "exchange_rate_vnd_per_usd": "exchange_rate_vnd_per_usd",
        "evn_energy_escalation_rate": "evn_energy_escalation_rate",
        "evn_capacity_escalation_rate": "evn_capacity_escalation_rate",
        "om_escalation_rate": "om_escalation_rate",
        "pv_degradation_rate": "pv_degradation_rate",
        "pv_depreciation_years": "pv_depreciation_years",
        "battery_replacement_year": "battery_replacement_year",
        "demand_savings_esco_share": "esco_demand_savings_share",
        "grid_charging_enabled": "grid_charging_enabled",
        "dppa": "dppa_inputs",
    }
    return {
        target: assumptions[source]
        for source, target in mapping.items()
        if assumptions.get(source) is not None
    }


def reconcile_cash_flows(actual, reference, tolerance=RECONCILIATION_TOLERANCE):
    actual_year_one = actual["annual_cash_flows"][0]
    reference_year_one = reference["annual_cash_flows"][0]
    actual_summary = actual["summary"]
    reference_summary = reference["summary"]
    metrics = {}

    for key in (
        "c_dn_usd",
        "c_dppa_usd",
        "c_cl_usd",
        "c_bl_usd",
        "cfd_net_usd",
        "generator_revenue_usd",
        "dppa_offtaker_cost_usd",
    ):
        metrics[key] = _comparison(actual_year_one[key], reference_year_one[key], tolerance)

    for key in ("equity_irr_fraction", "npv_usd", "average_dscr"):
        metrics[key] = _comparison(actual_summary[key], reference_summary[key], tolerance)

    metrics["minimum_dscr"] = _comparison(
        _minimum_debt_service_dscr(actual),
        _minimum_debt_service_dscr(reference),
        tolerance,
    )
    return {
        "tolerance": tolerance,
        "passed": all(metric["passed"] for metric in metrics.values()),
        "metrics": metrics,
    }


def reconcile_reference_workbook(cash_flow, workbook_path, tolerance=RECONCILIATION_TOLERANCE):
    workbook = load_workbook(workbook_path, data_only=True, read_only=True)
    summary = dict(workbook["Summary"].values)
    year_one = {
        label: value
        for label, value, _ in workbook["Year 1 BAU vs DPPA"].values
        if label and value is not None
    }
    cash_flow_rows = list(workbook["Cash Flow"].values)
    headers = list(cash_flow_rows[0])
    dscr_column = headers.index("DSCR")
    debt_service_column = headers.index("Debt Service (USD)")
    workbook_minimum_dscr = min(
        row[dscr_column]
        for row in cash_flow_rows[1:]
        if row[debt_service_column] and row[dscr_column] is not None
    )
    actual_year_one = cash_flow["annual_cash_flows"][0]
    actual_summary = cash_flow["summary"]
    workbook_values = {
        "c_dn_usd": year_one["C_DN spot energy (Q_Khc × CFMP × K_pp)"],
        "c_dppa_usd": year_one["C_DPPA system service fee"],
        "c_cl_usd": year_one["C_CL settlement adder"],
        "c_bl_usd": year_one["C_BL retail shortfall (P_evn × shortfall)"],
        "cfd_net_usd": year_one["CfD payment to ESCO (positive = pay)"],
        "generator_revenue_usd": year_one["Total ESCO / generator revenue"],
        "dppa_offtaker_cost_usd": year_one["Total buyer outflow"],
        "equity_irr_fraction": summary["Equity IRR"],
        "npv_usd": summary["NPV (USD)"],
        "minimum_dscr": workbook_minimum_dscr,
        "average_dscr": summary["Average DSCR"],
    }
    actual_values = {
        **{key: actual_year_one[key] for key in (
            "c_dn_usd", "c_dppa_usd", "c_cl_usd", "c_bl_usd", "cfd_net_usd",
            "generator_revenue_usd", "dppa_offtaker_cost_usd",
        )},
        "equity_irr_fraction": actual_summary["equity_irr_fraction"],
        "npv_usd": actual_summary["npv_usd"],
        "minimum_dscr": _minimum_debt_service_dscr(cash_flow),
        "average_dscr": actual_summary["average_dscr"],
    }
    metrics = {
        key: _comparison(actual_values[key], workbook_values[key], tolerance)
        for key in workbook_values
    }
    return {
        "reference_workbook": str(workbook_path),
        "tolerance": tolerance,
        "passed": all(metric["passed"] for metric in metrics.values()),
        "metrics": metrics,
    }


def _calculate_cash_flow(results, assumptions):
    return calculate_esco_pro_forma_from_reopt_results(
        results,
        esco_energy_discount_fraction=assumptions["esco_energy_discount_fraction"],
        **cash_flow_overrides_from_assumptions(assumptions),
    )


def _minimum_debt_service_dscr(cash_flow):
    return min(
        row["dscr"]
        for row in cash_flow["annual_cash_flows"]
        if row.get("debt_service_usd") and row.get("dscr") is not None
    )


def _comparison(actual, reference, tolerance):
    delta = actual - reference
    relative_delta = abs(delta) / max(abs(reference), 1.0)
    return {
        "actual": actual,
        "reference": reference,
        "delta": delta,
        "relative_delta": relative_delta,
        "passed": relative_delta <= tolerance,
    }


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
