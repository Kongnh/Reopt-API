"""Rebuild the Thailand report workbook offline from saved case outputs.

The workbook is pure post-processing of results.json + assumptions.json, so it
can be regenerated without Django or a REopt re-run:

    python -m proforma_thailand.rebuild_report --case-dir outputs/thailand_case/rofu_thailand/case_1

Mirrors proforma_vietnam/rebuild_report.py. The Thailand report builder takes
assumptions directly rather than going through a sweep-override helper, so
there is no cash_flow_overrides_from_assumptions call here.
"""
import argparse
import json
from pathlib import Path

from proforma_thailand.report import build_thailand_report


def rebuild_report(case_dir, prepared_on=None):
    case_dir = Path(case_dir)
    results = json.loads((case_dir / "results.json").read_text(encoding="utf-8"))
    assumptions = json.loads((case_dir / "assumptions.json").read_text(encoding="utf-8"))
    if prepared_on is not None:
        assumptions["prepared_on"] = prepared_on
    case_path = case_dir / "case.json"
    if case_path.exists():
        assumptions["case_config"] = json.loads(case_path.read_text(encoding="utf-8"))

    workbook, _extras = build_thailand_report(
        results, dict(assumptions, run_uuid=results.get("run_uuid"))
    )
    out_path = case_dir / "thailand_report_{}.xlsx".format(results["run_uuid"])
    workbook.save(out_path)
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rebuild a Thailand report workbook offline."
    )
    parser.add_argument(
        "--case-dir", required=True,
        help="Case directory with results.json + assumptions.json.",
    )
    args = parser.parse_args(argv)
    print(rebuild_report(args.case_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
