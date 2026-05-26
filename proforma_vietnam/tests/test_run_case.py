import csv
import json
import tempfile
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.run_case import main


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
