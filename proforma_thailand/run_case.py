"""Build, submit and report a Thailand REopt case.

Same submit/poll shape as proforma_vietnam/run_case.py, but the workbook is
built locally from the returned results rather than fetched from the Django
report endpoint - there is no Thailand equivalent of ?vietnam_proforma=true.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

from proforma_thailand.case_builder import build_thailand_case
from proforma_thailand.report import build_thailand_report

DEFAULT_API_URL = "http://localhost:8000/v3"
HEADLINE_LABELS = ("IRR", "NPV", "Payback")


def assert_placeholders_disclosed(workbook):
    """Refuse to ship a workbook that reports returns without disclosing provisionality.

    The validator checks that placeholders are MARKED, not that they are
    absent, so failing hard here does not block legitimate provisional inputs.
    It blocks a rendering regression that silently drops the markers.
    """
    from proforma_thailand.defaults import PLACEHOLDER_MARKER
    from proforma_vietnam.validate_workbook import validate_no_unmarked_placeholders

    failures = validate_no_unmarked_placeholders(
        workbook, PLACEHOLDER_MARKER, HEADLINE_LABELS
    )
    if failures:
        raise RuntimeError(
            "Refusing to write the workbook: {}".format(" ".join(failures))
        )


POLLING_STATUSES = ("Optimizing...", "optimizing...", "queued")
BODY_BEARING_ERROR_CODES = (400, 404, 500)


def summarize_results(results, extras):
    """Headline figures for the Keen update: sizing and grid offset."""
    outputs = results.get("outputs", {})
    pv = outputs.get("PV") or {}
    if isinstance(pv, list):
        pv = pv[0] if pv else {}
    storage = outputs.get("ElectricStorage") or {}
    load = outputs.get("ElectricLoad") or {}
    utility = outputs.get("ElectricUtility") or {}

    annual_load = float(load.get("annual_calculated_kwh") or 0.0)
    annual_grid = float(utility.get("annual_energy_supplied_kwh") or 0.0)
    grid_offset = 0.0 if annual_load <= 0 else 1.0 - annual_grid / annual_load

    return {
        "pv_kw": float(pv.get("size_kw") or 0.0),
        "bess_kw": float(storage.get("size_kw") or 0.0),
        "bess_kwh": float(storage.get("size_kwh") or 0.0),
        "annual_load_kwh": annual_load,
        # REopt levelizes annual_energy_produced_kwh across the project
        # lifetime inside the optimisation; year_one_energy_produced_kwh is
        # the true first-year value (see
        # proforma_vietnam.esco_pro_forma._levelization_factor). This feeds
        # summary.json and the client memo, so it must be on the same
        # first-year basis as the corrected workbook.
        "annual_pv_kwh": float(pv.get("year_one_energy_produced_kwh") or 0.0),
        "grid_offset_fraction": grid_offset,
        "power_factor_compensation_kvar": float(
            extras.get("power_factor_compensation_kvar") or 0.0
        ),
        "power_factor_mitigation_cost_usd": float(
            extras.get("power_factor_mitigation_cost_usd") or 0.0
        ),
        "billed_demand_kw_by_month": extras.get("billed_demand_kw_by_month", []),
        "annual_avoided_tco2e": float(extras.get("annual_avoided_tco2e") or 0.0),
        "lifetime_avoided_tco2e": float(extras.get("lifetime_avoided_tco2e") or 0.0),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and run a Thailand REopt case.")
    parser.add_argument("--case", required=True, help="Path to Thailand case JSON.")
    parser.add_argument("--out", default=None, help="Output directory.")
    parser.add_argument("--api-url", default=os.environ.get("REOPT_API_URL", DEFAULT_API_URL))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=5)
    parser.add_argument("--max-polls", type=int, default=240)
    args = parser.parse_args(argv)

    api_base = args.api_url.rstrip("/")
    if api_base.endswith("/job"):
        api_base = api_base[: -len("/job")]

    case_path = Path(args.case)
    case = build_thailand_case(json.loads(case_path.read_text(encoding="utf-8")))

    out_dir = Path(args.out) if args.out else case_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "payload.json", case["payload"])
    _write_json(out_dir / "assumptions.json", case["assumptions"])

    if args.dry_run:
        return 0

    run_uuid = _submit(api_base, case["payload"])
    results = _poll(api_base, run_uuid, args.poll_seconds, args.max_polls)
    _write_json(out_dir / "results.json", results)

    if results.get("status") != "optimal":
        print("Run {} ended with status {!r}.".format(run_uuid, results.get("status")),
              file=sys.stderr)
        for key, value in (results.get("messages", {}).get("errors") or {}).items():
            print("  {}: {}".format(key, value), file=sys.stderr)
        return 1

    assumptions = dict(case["assumptions"], run_uuid=run_uuid)
    workbook, extras = build_thailand_report(results, assumptions)
    assert_placeholders_disclosed(workbook)
    workbook.save(out_dir / "thailand_report_{}.xlsx".format(run_uuid))
    _write_json(out_dir / "summary.json", summarize_results(results, extras))
    return 0


def _submit(api_base, payload):
    post = request.Request(
        "{}/job/".format(api_base),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(post) as response:
        return json.loads(response.read().decode("utf-8"))["run_uuid"]


def _poll(api_base, run_uuid, poll_seconds, max_polls):
    url = "{}/job/{}/results".format(api_base, run_uuid)
    for _ in range(max_polls):
        body = _get(url)
        if body.get("status") not in POLLING_STATUSES and _is_complete(body):
            return body
        time.sleep(poll_seconds)
    raise TimeoutError("Timed out waiting for REopt results for {}.".format(run_uuid))


def _is_complete(body):
    """True when the results document is actually finished being written.

    A run can report status "optimal" while process_results is still populating
    outputs, which yields a document carrying only Financial and ElectricTariff
    and a summary of all zeros. Only an error is complete without outputs.
    """
    if body.get("status") != "optimal":
        return True
    return bool(body.get("outputs", {}).get("ElectricLoad"))


def _get(url):
    try:
        with request.urlopen(url) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code in BODY_BEARING_ERROR_CODES:
            try:
                return json.loads(error.read().decode("utf-8"))
            except (ValueError, OSError):
                raise error from None
        raise


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
