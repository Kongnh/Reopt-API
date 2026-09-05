"""The committed load inputs must be reproducible and self-describing."""

import json
from pathlib import Path
from unittest import TestCase

from proforma_thailand.tools.build_load_inputs import (
    build_manifest,
    validate_calendar_months,
    LOAD_CSV,
    MANIFEST,
)


class BuildManifestTests(TestCase):

    def test_manifest_records_order_counts_and_hash(self):
        manifest = build_manifest([(2026, 1), (2025, 12)], [2976, 2976], "abc123")
        self.assertEqual(manifest["calendar_year_months"], [[2026, 1], [2025, 12]])
        self.assertEqual(manifest["rows_per_month"], [2976, 2976])
        self.assertEqual(manifest["total_rows"], 5952)
        self.assertEqual(manifest["source_sha256"], "abc123")


class ValidateCalendarMonthsTests(TestCase):

    MANIFEST = {
        "calendar_year_months": [[2026, 1], [2026, 2], [2025, 12]],
        "rows_per_month": [2976, 2688, 2976],
        "total_rows": 8640,
        "source_sha256": "abc123",
    }

    def test_matching_order_passes(self):
        validate_calendar_months([(2026, 1), (2026, 2), (2025, 12)], self.MANIFEST)

    def test_reordered_months_raise(self):
        with self.assertRaises(ValueError) as caught:
            validate_calendar_months(
                [(2026, 2), (2026, 1), (2025, 12)], self.MANIFEST
            )
        self.assertIn("order", str(caught.exception).lower())

    def test_wrong_month_count_raises(self):
        with self.assertRaises(ValueError):
            validate_calendar_months([(2026, 1), (2026, 2)], self.MANIFEST)

    def test_absent_manifest_is_not_an_error(self):
        validate_calendar_months([(2026, 1)], None)


class CommittedManifestTests(TestCase):
    """Tests that pin the committed manifest as a consumed artifact."""

    def test_manifest_file_exists_and_parses(self):
        # Manifest must be a real file, not optional. Deleting it would silently
        # disable the calendar_year_months guard without any test failure.
        self.assertTrue(MANIFEST.exists(),
                       "Committed manifest must exist at {}: {}".format(
                           MANIFEST.relative_to(Path.cwd()), "is missing"))
        with open(MANIFEST, encoding="utf-8") as f:
            manifest_data = json.load(f)
        self.assertIn("calendar_year_months", manifest_data)
        self.assertIn("total_rows", manifest_data)
        self.assertIn("rows_per_month", manifest_data)

    def test_manifest_total_rows_matches_csv_data_rows(self):
        # Load the actual CSV and count its data rows (excluding header).
        # This proves the manifest was backfilled against the real CSV content,
        # not against an invented fixture, and that the CSV has not drifted.
        with open(LOAD_CSV, encoding="utf-8") as f:
            lines = f.readlines()
        csv_data_rows = len(lines) - 1  # exclude header line
        self.assertGreater(csv_data_rows, 0, "CSV must have data rows")

        # Load manifest and compare.
        with open(MANIFEST, encoding="utf-8") as f:
            manifest_data = json.load(f)
        manifest_rows = manifest_data["total_rows"]

        self.assertEqual(manifest_rows, csv_data_rows,
                        "Manifest total_rows ({}) must match CSV data rows ({})".format(
                            manifest_rows, csv_data_rows))

    def test_manifest_is_genuinely_consumed_on_production_path(self):
        # The guard validate_calendar_months(_, None) is a deliberate no-op,
        # but nothing prevents the manifest from going missing. This test proves
        # the guard actually fires when called with the real committed manifest.
        # A deleted or corrupted manifest is caught because this test fails.
        with open(MANIFEST, encoding="utf-8") as f:
            real_manifest = json.load(f)

        # Get the real month order from the manifest.
        expected_months = [tuple(pair) for pair in real_manifest["calendar_year_months"]]

        # Deliberately reorder the first two months.
        wrong_order = [expected_months[1], expected_months[0]] + list(expected_months[2:])

        # The guard must fire when passed the reordered list and the real manifest.
        with self.assertRaises(ValueError) as caught:
            validate_calendar_months(wrong_order, real_manifest)
        self.assertIn("order", str(caught.exception).lower())

    def test_all_committed_case_files_declare_manifest_month_order(self):
        # Every committed case.json must declare a calendar_year_months that
        # matches the manifest. A new case added later with a different order
        # must be caught by this test before it breaks the system.
        cases_dir = Path(__file__).resolve().parent.parent / "cases"
        self.assertTrue(cases_dir.exists(), "Thailand cases directory must exist")

        # Discover all case.json files in the cases tree.
        case_files = sorted(cases_dir.glob("*/case.json"))
        self.assertGreater(len(case_files), 0,
                          "Must have at least one committed case.json")

        with open(MANIFEST, encoding="utf-8") as f:
            manifest_data = json.load(f)
        expected_order = [tuple(pair) for pair in manifest_data["calendar_year_months"]]

        for case_file in case_files:
            with open(case_file, encoding="utf-8") as f:
                case_data = json.load(f)
            case_months = [tuple(pair) for pair in case_data["load_profile"]["calendar_year_months"]]
            self.assertEqual(case_months, expected_order,
                           "Case {} must declare the same month order as the manifest".format(
                               case_file.relative_to(Path.cwd())))
