"""Tests for proforma_vietnam.validate_workbook.

The recalc tests drive a real Excel instance via COM and are gated: they
require Windows, pywin32 (win32com) and an installed Excel. The availability
probe runs once at module import and is cached, so on machines without Excel
the whole class skips cleanly and the suite stays green.
"""

import os
import sys
import tempfile
import unittest

from proforma_vietnam.tests.test_audit_sheets import (
    ESCO_ASSUMPTIONS,
    _dppa_result,
    _esco_result,
    _esco_surplus_result,
)
from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook


def _probe_excel():
    """True iff a real Excel instance can be created via COM (cached below)."""
    if sys.platform != "win32":
        return False
    try:
        import win32com.client
    except ImportError:
        return False
    excel = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.DisplayAlerts = False
        return True
    except Exception:
        return False
    finally:
        if excel is not None:
            try:
                excel.Quit()
            except Exception:
                pass


EXCEL_AVAILABLE = _probe_excel()

requires_excel = unittest.skipUnless(
    EXCEL_AVAILABLE, "requires Windows + Microsoft Excel + pywin32"
)


def _engine_tie_out_row(sheet):
    """Row index of the hardcoded 'Equity cash flow (engine)' tie-out line."""
    for row in range(1, sheet.max_row + 1):
        if sheet.cell(row=row, column=1).value == "Equity cash flow (engine)":
            return row
    raise AssertionError("no 'Equity cash flow (engine)' row on the audit sheet")


@requires_excel
class ExcelRecalcValidationTests(unittest.TestCase):
    """End-to-end: build workbook -> recalc in Excel -> read PASS/REVIEW."""

    def _validate_saved(self, workbook, name):
        from proforma_vietnam.validate_workbook import validate_workbook

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, name)
            workbook.save(path)
            return validate_workbook(path)

    def test_corrupted_engine_tie_out_is_detected(self):
        # Load-bearing negative test: +1000 on ONE hardcoded engine tie-out
        # cell must flip at least one check to REVIEW and break the Cover
        # aggregate — proving the recalc actually detects divergence.
        workbook = build_vietnam_esco_workbook(
            _esco_result(), assumptions=ESCO_ASSUMPTIONS
        )
        sheet = workbook["Pro Forma (Audit)"]
        cell = sheet.cell(row=_engine_tie_out_row(sheet), column=4)  # year 1
        self.assertIsInstance(cell.value, (int, float))
        cell.value = cell.value + 1000.0

        result = self._validate_saved(workbook, "corrupted.xlsx")

        self.assertFalse(result["ok"])
        self.assertGreaterEqual(result["review_count"], 1)
        self.assertEqual(result["cover_status"], "REVIEW REQUIRED")

    def test_esco_fixture_workbook_passes(self):
        workbook = build_vietnam_esco_workbook(
            _esco_result(), assumptions=ESCO_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "esco.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")
        self.assertTrue(result["file"].endswith("esco.xlsx"))

    def test_surplus_export_esco_fixture_workbook_passes(self):
        # Decree 243/2026 surplus-export line must tie out in Excel: the live
        # surplus revenue formula has to reproduce the engine's number so the
        # per-year CFADS/equity/CIT checks stay PASS.
        workbook = build_vietnam_esco_workbook(
            _esco_surplus_result(), assumptions=ESCO_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "esco_surplus.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")

    def test_dppa_fixture_workbook_passes(self):
        cash_flow_result, dppa_inputs = _dppa_result()
        workbook = build_vietnam_esco_workbook(
            cash_flow_result,
            assumptions={**ESCO_ASSUMPTIONS, "dppa": dppa_inputs},
        )
        result = self._validate_saved(workbook, "dppa.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")


class ResolvePathsTests(unittest.TestCase):
    """CLI path resolution needs no Excel — runs everywhere."""

    def test_xlsx_paths_pass_through(self):
        from proforma_vietnam.validate_workbook import _resolve_paths

        self.assertEqual(_resolve_paths(["a.xlsx", "b.xlsx"]), ["a.xlsx", "b.xlsx"])

    def test_case_directory_resolves_to_its_single_report(self):
        from proforma_vietnam.validate_workbook import _resolve_paths

        with tempfile.TemporaryDirectory() as tmp:
            report = os.path.join(tmp, "vietnam_report_abc123.xlsx")
            open(report, "wb").close()
            self.assertEqual(_resolve_paths([tmp]), [report])

    def test_directory_without_report_errors(self):
        from proforma_vietnam.validate_workbook import _resolve_paths

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                _resolve_paths([tmp])

    def test_directory_with_multiple_reports_errors(self):
        from proforma_vietnam.validate_workbook import _resolve_paths

        with tempfile.TemporaryDirectory() as tmp:
            for name in ("vietnam_report_a.xlsx", "vietnam_report_b.xlsx"):
                open(os.path.join(tmp, name), "wb").close()
            with self.assertRaises(SystemExit):
                _resolve_paths([tmp])


if __name__ == "__main__":
    unittest.main()
