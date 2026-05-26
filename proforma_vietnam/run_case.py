import argparse
import json
import os
import time
from pathlib import Path
from urllib import parse, request

from proforma_vietnam.case_builder import build_vietnam_case


DEFAULT_API_URL = "http://localhost:8000/v3/job/"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and run a Vietnam REopt case.")
    parser.add_argument("--case", required=True, help="Path to Vietnam case JSON.")
    parser.add_argument("--out", required=True, help="Output directory.")
    parser.add_argument("--api-url", default=os.environ.get("REOPT_API_URL", DEFAULT_API_URL))
    parser.add_argument("--dry-run", action="store_true", help="Write payload only; do not submit.")
    parser.add_argument("--poll-seconds", type=float, default=5)
    parser.add_argument("--max-polls", type=int, default=120)
    args = parser.parse_args(argv)

    case_config = json.loads(Path(args.case).read_text(encoding="utf-8"))
    vietnam_case = build_vietnam_case(case_config)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "payload.json", vietnam_case["payload"])
    _write_json(out_dir / "assumptions.json", vietnam_case["assumptions"])

    if args.dry_run:
        return 0

    run_uuid = _submit_payload(args.api_url, vietnam_case["payload"])
    results = _poll_results(args.api_url, run_uuid, args.poll_seconds, args.max_polls)
    _write_json(out_dir / "results.json", results)

    if results.get("status") == "optimal":
        workbook = _download_vietnam_report(
            args.api_url,
            run_uuid,
            vietnam_case["assumptions"].get("esco_energy_discount_fraction"),
        )
        (out_dir / f"vietnam_report_{run_uuid}.xlsx").write_bytes(workbook)

    return 0


def _submit_payload(api_url, payload):
    post_request = request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(post_request) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["run_uuid"]


def _poll_results(api_url, run_uuid, poll_seconds, max_polls):
    results_url = _results_url(api_url, run_uuid)
    for _ in range(max_polls):
        with request.urlopen(results_url) as response:
            body = json.loads(response.read().decode("utf-8"))
        if body.get("status") not in ["Optimizing...", "optimizing...", "queued"]:
            return body
        time.sleep(poll_seconds)
    raise TimeoutError(f"Timed out waiting for REopt results for {run_uuid}.")


def _download_vietnam_report(api_url, run_uuid, esco_energy_discount_fraction):
    query = parse.urlencode({
        "vietnam_proforma": "true",
        "esco_energy_discount_fraction": esco_energy_discount_fraction,
    })
    with request.urlopen(f"{_results_url(api_url, run_uuid)}?{query}") as response:
        return response.read()


def _results_url(api_url, run_uuid):
    return api_url.rstrip("/").rsplit("/", 1)[0] + f"/{run_uuid}/results"


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
