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
    DIRECT_ASSUMPTIONS,
    ESCO_ASSUMPTIONS,
    PHYSICAL_ASSUMPTIONS,
    _construction_result,
    _direct_result,
    _dppa_result,
    _dscr_sized_result,
    _esco_contract_term_result,
    _esco_result,
    _esco_surplus_result,
    _physical_result,
    _usd_debt_result,
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

    def test_expense_mode_esco_fixture_workbook_passes(self):
        # Legacy expense treatment (Circular 45 opt-out): the year-11 replacement
        # is fully deducted in-year, so the workbook keeps the two-class
        # depreciation / EBT formulas. Under real Excel recalc that legacy path
        # must still tie out to the engine so every check stays PASS — the
        # byte-identical guarantee holds end-to-end, not just structurally.
        workbook = build_vietnam_esco_workbook(
            _esco_result(battery_replacement_treatment="expense"),
            assumptions=ESCO_ASSUMPTIONS,
        )
        result = self._validate_saved(workbook, "esco_expense.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")

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

    def test_physical_dppa_fixture_workbook_passes(self):
        # ND57 Điều 25 private wire: the live PPA revenue formula (matched ×
        # price × PPA escalation × degradation) plus the nested surplus line must
        # reproduce the engine so the per-year CFADS/equity/CIT checks stay PASS.
        workbook = build_vietnam_esco_workbook(
            _physical_result(), assumptions=PHYSICAL_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "physical_dppa.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")

    def test_direct_ownership_fixture_workbook_passes(self):
        # Factory self-invest: the live bill-savings formula (BAU − optimized,
        # degradation repurchase) plus the flat-20% profitable-host CIT row (a
        # negative CIT in the year-11 replacement loss) must reproduce the engine
        # so the per-year CFADS/equity/CIT checks stay PASS.
        workbook = build_vietnam_esco_workbook(
            _direct_result(), assumptions=DIRECT_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "direct_ownership.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")

    def test_construction_grace_fixture_workbook_passes(self):
        # Construction + grace financing: the live debt schedule must reproduce
        # the interest-only grace rows on the rolled-up COD balance (principal
        # starting year g+1) and the depreciation rows must carry the pro-rata
        # IDC so the per-year CFADS/equity/CIT checks stay PASS.
        workbook = build_vietnam_esco_workbook(
            _construction_result(), assumptions=ESCO_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "construction_grace.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")

    def test_usd_debt_fixture_workbook_passes(self):
        # USD-denominated debt: the FX Sensitivity sheet's live min-DSCR column
        # must reproduce the engine's decomposition ((CFADS_t/(1+d)^t)/DS_t) so
        # the DSCR-vs-depreciation status stays PASS, and the base-case pro forma
        # tie-out (identical to VND at the resolved rate) must stay PASS.
        workbook = build_vietnam_esco_workbook(
            _usd_debt_result(), assumptions=ESCO_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "usd_debt.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")

    def test_dscr_sized_fixture_workbook_passes(self):
        # DSCR-sized debt (binding 2.5x covenant): DEBT_PRINCIPAL is the live
        # MIN(FRACTION_DEBT, SUPPORTED_DEBT), so the whole debt schedule / IDC /
        # depreciation / DSCR chain rides the sized loan. Under real Excel recalc
        # the base pro-forma tie-out and the fixed-point property row (MIN DSCR =
        # covenant when binding) must both stay PASS.
        workbook = build_vietnam_esco_workbook(
            _dscr_sized_result(), assumptions=ESCO_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "dscr_sized.xlsx")

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)
        self.assertGreaterEqual(result["pass_count"], 1)
        self.assertEqual(result["cover_status"], "ALL CHECKS PASS")

    def test_contract_term_fixture_workbook_passes(self):
        # Task 4e ESCO contract tenor (T=12) + residual buyout: operations
        # truncate at year 12, the year-12 equity CF carries the residual, and
        # the year-12 taxable income carries the NBV-based disposal gain. Under
        # real Excel recalc the truncated per-year CFADS/equity/CIT tie-out, the
        # live NBV disposal formula and the transfer-proceeds row must all
        # reproduce the engine so every check stays PASS.
        workbook = build_vietnam_esco_workbook(
            _esco_contract_term_result(), assumptions=ESCO_ASSUMPTIONS
        )
        result = self._validate_saved(workbook, "contract_term.xlsx")

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
