import csv
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from proforma_vietnam.run_case import _download_vietnam_report, main


class VietnamRunCaseTests(TestCase):

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
                "http://localhost:8000/v3/job/",
                "run-uuid",
                assumptions,
            )

        self.assertEqual(workbook, b"workbook")
        requested_url = urlopen.call_args.args[0]
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
