"""The committed load inputs must be reproducible and self-describing."""

from unittest import TestCase

from proforma_thailand.tools.build_load_inputs import (
    build_manifest,
    validate_calendar_months,
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
