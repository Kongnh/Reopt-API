import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import parse, request
from urllib.error import HTTPError

from proforma_vietnam.case_builder import build_vietnam_case


DEFAULT_API_URL = "http://localhost:8000/v3"
TERMINAL_STATUSES_NON_OPTIMAL_BODY_CODES = (400, 404, 500)
POLLING_STATUSES = ("Optimizing...", "optimizing...", "queued")
VIETNAM_REPORT_QUERY_KEYS = [
    "esco_energy_discount_fraction",
    "owner_discount_rate_fraction",
    "debt_fraction",
    "debt_interest_rate_fraction",
    "debt_term_years",
    "annual_om_usd",
    "pv_capex_usd",
    "bess_capex_usd",
    "annual_om_vnd",
    "pv_capex_vnd",
    "bess_capex_vnd",
    "exchange_rate_vnd_per_usd",
    "evn_energy_escalation_rate",
    "evn_capacity_escalation_rate",
    "demand_savings_esco_share",
    "grid_charging_enabled",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and run a Vietnam REopt case.")
    parser.add_argument("--case", required=True, help="Path to Vietnam case JSON.")
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory. Defaults to the directory containing --case.",
    )
    parser.add_argument("--api-url", default=os.environ.get("REOPT_API_URL", DEFAULT_API_URL))
    parser.add_argument("--dry-run", action="store_true", help="Write payload only; do not submit.")
    parser.add_argument("--poll-seconds", type=float, default=5)
    parser.add_argument("--max-polls", type=int, default=120)
    args = parser.parse_args(argv)

    api_base = _api_base(args.api_url)
    case_path = Path(args.case)
    case_config = json.loads(case_path.read_text(encoding="utf-8"))
    vietnam_case = build_vietnam_case(case_config)

    out_dir = Path(args.out) if args.out else case_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "payload.json", vietnam_case["payload"])
    _write_json(out_dir / "assumptions.json", vietnam_case["assumptions"])

    if args.dry_run:
        return 0

    run_uuid = _submit_payload(api_base, vietnam_case["payload"])
    results = _poll_results(api_base, run_uuid, args.poll_seconds, args.max_polls)
    _write_json(out_dir / "results.json", results)

    status = results.get("status")
    if status != "optimal":
        _print_run_failure(run_uuid, results)
        return 1

    workbook = _download_vietnam_report(
        api_base,
        run_uuid,
        vietnam_case["assumptions"],
    )
    (out_dir / f"vietnam_report_{run_uuid}.xlsx").write_bytes(workbook)
    return 0


def _api_base(api_url):
    """Strip any trailing ``/job`` segment so callers may pass either shape."""
    stripped = api_url.rstrip("/")
    if stripped.endswith("/job"):
        stripped = stripped[: -len("/job")]
    return stripped


def _submit_url(api_base):
    return f"{api_base}/job/"


def _results_url(api_base, run_uuid):
    return f"{api_base}/job/{run_uuid}/results"


def _submit_payload(api_base, payload):
    post_request = request.Request(
        _submit_url(api_base),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(post_request) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["run_uuid"]


def _poll_results(api_base, run_uuid, poll_seconds, max_polls):
    results_url = _results_url(api_base, run_uuid)
    for _ in range(max_polls):
        body = _get_results_body(results_url)
        if body.get("status") not in POLLING_STATUSES:
            return body
        time.sleep(poll_seconds)
    raise TimeoutError(f"Timed out waiting for REopt results for {run_uuid}.")


def _get_results_body(url):
    """Read the results endpoint, returning the JSON body even on 4xx/5xx.

    REopt returns 400 with a populated ``messages.errors`` body when a run
    errors out. Without catching ``HTTPError`` here the caller crashes with a
    bare traceback instead of surfacing the optimizer's error message.
    """
    try:
        with request.urlopen(url) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code in TERMINAL_STATUSES_NON_OPTIMAL_BODY_CODES:
            try:
                return json.loads(error.read().decode("utf-8"))
            except (ValueError, OSError):
                raise error from None
        raise


def _print_run_failure(run_uuid, results):
    status = results.get("status")
    print(f"REopt run {run_uuid} ended with status {status!r}.", file=sys.stderr)
    errors = results.get("messages", {}).get("errors") or {}
    for key, value in errors.items():
        print(f"  {key}: {value}", file=sys.stderr)


def _download_vietnam_report(api_base, run_uuid, assumptions):
    query = parse.urlencode(_vietnam_report_query_params(assumptions))
    with request.urlopen(f"{_results_url(api_base, run_uuid)}?{query}") as response:
        return response.read()


def _vietnam_report_query_params(assumptions):
    query = {"vietnam_proforma": "true"}
    for key in VIETNAM_REPORT_QUERY_KEYS:
        value = assumptions.get(key)
        if value is not None:
            query[key] = value
    return query


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
