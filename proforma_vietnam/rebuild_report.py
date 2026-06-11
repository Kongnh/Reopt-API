"""Rebuild the Vietnam report workbook offline from saved case outputs.

The workbook is pure post-processing of results.json + assumptions.json, so it
can be regenerated without Django or a REopt re-run:

    python -m proforma_vietnam.rebuild_report --case-dir outputs/vietnam_case/factory_a/case_5
"""
import argparse
import json
from pathlib import Path

from proforma_vietnam.esco_pro_forma import calculate_esco_pro_forma_from_reopt_results
from proforma_vietnam.report_data import build_vietnam_report_data
from proforma_vietnam.run_dppa_negotiation_sweep import cash_flow_overrides_from_assumptions
from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook


def rebuild_report(case_dir):
    case_dir = Path(case_dir)
    results = json.loads((case_dir / "results.json").read_text(encoding="utf-8"))
    assumptions = json.loads((case_dir / "assumptions.json").read_text(encoding="utf-8"))

    cash_flow_result = calculate_esco_pro_forma_from_reopt_results(
        results,
        esco_energy_discount_fraction=assumptions["esco_energy_discount_fraction"],
        **cash_flow_overrides_from_assumptions(assumptions),
    )
    report_data = build_vietnam_report_data(results, cash_flow_result)
    workbook = build_vietnam_esco_workbook(
        cash_flow_result,
        assumptions=assumptions,
        report_data=report_data,
    )
    out_path = case_dir / f"vietnam_report_{results['run_uuid']}.xlsx"
    workbook.save(out_path)
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rebuild a Vietnam report workbook offline.")
    parser.add_argument("--case-dir", required=True, help="Case directory with results.json + assumptions.json.")
    args = parser.parse_args(argv)
    print(rebuild_report(args.case_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
