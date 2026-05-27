import csv
import io
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError

from proforma_vietnam.run_case import (
    _api_base,
    _download_vietnam_report,
    _poll_results,
    _results_url,
    _submit_url,
    main,
)


STUB_PV_SERIES = [0.25] * 8760


class VietnamRunCaseTests(TestCase):

    def setUp(self):
        patcher = patch(
            "proforma_vietnam.case_builder.pvwatts_client.fetch_production_factor_series",
            return_value=list(STUB_PV_SERIES),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_dry_run_writes_payload_and_assumptions_without_api_call(self):
        temp_dir = Path(tempfile.mkdtemp())
        load_path = temp_dir / "load.csv"
        case_path = temp_dir / "case.json"
        out_dir = temp_dir / "outputs"

        _write_load_csv(load_path)
        case_path.write_text(json.dumps(_case_config(load_path)), encoding="utf-8")

        exit_code = main([
            "--case",
            str(case_path),
            "--out",
            str(out_dir),
            "--dry-run",
        ])

        self.assertEqual(exit_code, 0)
        payload = json.loads((out_dir / "payload.json").read_text(encoding="utf-8"))
        assumptions = json.loads((out_dir / "assumptions.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["Meta"]["description"], "Factory A")
        self.assertEqual(len(payload["ElectricLoad"]["loads_kw"]), 8760)
        self.assertEqual(assumptions["country"], "Vietnam")

    def test_dry_run_writes_financial_report_assumptions(self):
        temp_dir = Path(tempfile.mkdtemp())
        load_path = temp_dir / "load.csv"
        case_path = temp_dir / "case.json"
        out_dir = temp_dir / "outputs"

        case_config = _case_config(load_path)
        case_config["financial"] = {
            "owner_discount_rate_fraction": 0.12,
            "debt_fraction": 0.65,
            "debt_interest_rate_fraction": 0.09,
            "debt_term_years": 12,
            "annual_om_usd": 4000,
        }
        _write_load_csv(load_path)
        case_path.write_text(json.dumps(case_config), encoding="utf-8")

        exit_code = main([
            "--case",
            str(case_path),
            "--out",
            str(out_dir),
            "--dry-run",
        ])

        self.assertEqual(exit_code, 0)
        assumptions = json.loads((out_dir / "assumptions.json").read_text(encoding="utf-8"))
        self.assertEqual(assumptions["owner_discount_rate_fraction"], 0.12)
        self.assertEqual(assumptions["debt_fraction"], 0.65)
        self.assertEqual(assumptions["debt_interest_rate_fraction"], 0.09)
        self.assertEqual(assumptions["debt_term_years"], 12)
        self.assertEqual(assumptions["annual_om_usd"], 4000)

    def test_download_report_uses_allowlisted_assumption_query_params(self):
        assumptions = {
            "esco_energy_discount_fraction": 0.9,
            "owner_discount_rate_fraction": 0.12,
            "debt_fraction": 0.65,
            "debt_interest_rate_fraction": 0.09,
            "debt_term_years": 12,
            "annual_om_usd": 4000,
            "pv_capex_usd": 480000,
            "bess_capex_usd": 430000,
            "exchange_rate_vnd_per_usd": 25000,
            "evn_energy_escalation_rate": 0.04,
            "evn_capacity_escalation_rate": 0.03,
            "demand_savings_esco_share": 0.75,
            "grid_charging_enabled": True,
            "unsupported": "ignored",
        }

        with patch("proforma_vietnam.run_case.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b"workbook"

            workbook = _download_vietnam_report(
                "http://localhost:8000/v3",
                "11111111-2222-3333-4444-555555555555",
                assumptions,
            )

        self.assertEqual(workbook, b"workbook")
        requested_url = urlopen.call_args.args[0]
        self.assertTrue(
            requested_url.startswith(
                "http://localhost:8000/v3/job/11111111-2222-3333-4444-555555555555/results?"
            ),
            requested_url,
        )
        self.assertIn("vietnam_proforma=true", requested_url)
        self.assertIn("esco_energy_discount_fraction=0.9", requested_url)
        self.assertIn("owner_discount_rate_fraction=0.12", requested_url)
        self.assertIn("debt_fraction=0.65", requested_url)
        self.assertIn("debt_interest_rate_fraction=0.09", requested_url)
        self.assertIn("debt_term_years=12", requested_url)
        self.assertIn("annual_om_usd=4000", requested_url)
        self.assertIn("pv_capex_usd=480000", requested_url)
        self.assertIn("bess_capex_usd=430000", requested_url)
        self.assertIn("exchange_rate_vnd_per_usd=25000", requested_url)
        self.assertIn("evn_energy_escalation_rate=0.04", requested_url)
        self.assertIn("evn_capacity_escalation_rate=0.03", requested_url)
        self.assertIn("demand_savings_esco_share=0.75", requested_url)
        self.assertIn("grid_charging_enabled=True", requested_url)
        self.assertNotIn("unsupported", requested_url)


class VietnamRunCaseUrlTests(TestCase):

    def test_api_base_accepts_base_or_job_suffixed_url(self):
        self.assertEqual(_api_base("http://localhost:8000/v3"), "http://localhost:8000/v3")
        self.assertEqual(_api_base("http://localhost:8000/v3/"), "http://localhost:8000/v3")
        self.assertEqual(_api_base("http://localhost:8000/v3/job/"), "http://localhost:8000/v3")
        self.assertEqual(_api_base("http://localhost:8000/v3/job"), "http://localhost:8000/v3")

    def test_submit_url_targets_job_endpoint(self):
        self.assertEqual(
            _submit_url("http://localhost:8000/v3"),
            "http://localhost:8000/v3/job/",
        )

    def test_results_url_keeps_job_segment(self):
        self.assertEqual(
            _results_url("http://localhost:8000/v3", "abc"),
            "http://localhost:8000/v3/job/abc/results",
        )


class VietnamRunCasePollTests(TestCase):

    def test_poll_returns_error_body_when_results_endpoint_returns_400(self):
        error_body = {
            "status": "error",
            "messages": {"errors": {"core_utils.jl_450": ["solar timeout"]}},
        }
        error = HTTPError(
            url="http://localhost:8000/v3/job/run-uuid/results",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(json.dumps(error_body).encode("utf-8")),
        )

        with patch("proforma_vietnam.run_case.request.urlopen", side_effect=error):
            body = _poll_results("http://localhost:8000/v3", "run-uuid", 0, 1)

        self.assertEqual(body, error_body)

    def test_poll_raises_for_unexpected_http_error_codes(self):
        error = HTTPError(
            url="http://localhost:8000/v3/job/run-uuid/results",
            code=502,
            msg="Bad Gateway",
            hdrs=None,
            fp=io.BytesIO(b""),
        )

        with patch("proforma_vietnam.run_case.request.urlopen", side_effect=error):
            with self.assertRaises(HTTPError):
                _poll_results("http://localhost:8000/v3", "run-uuid", 0, 1)


def _write_load_csv(path):
    with path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["load_kw"])
        for _ in range(8760):
            writer.writerow([500.0])


def _case_config(load_path):
    return {
        "case": {"name": "Factory A"},
        "site": {"latitude": 10.8231, "longitude": 106.6297},
        "load_profile": {"year": 2025, "path": str(load_path)},
        "tariff": {
            "year": 2025,
            "voltage_level": "22-110kV",
            "currency": "usd",
            "exchange_rate_vnd_per_usd": 25000,
        },
        "esco_contract": {"esco_energy_discount_fraction": 0.9},
    }
