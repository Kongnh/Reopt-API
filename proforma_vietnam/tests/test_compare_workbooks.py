from unittest import TestCase

from openpyxl import Workbook

from proforma_vietnam.tools.compare_workbooks import compare_workbooks


def _write(tmp_path, name, rows, sheet="Sheet1"):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet
    for row in rows:
        worksheet.append(row)
    path = tmp_path / name
    workbook.save(path)
    return path


class CompareWorkbooksTests(TestCase):

    def setUp(self):
        import tempfile
        from pathlib import Path
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def test_identical_workbooks_report_no_differences(self):
        a = _write(self.tmp, "a.xlsx", [["x", 1], ["y", 2]])
        b = _write(self.tmp, "b.xlsx", [["x", 1], ["y", 2]])

        self.assertEqual(compare_workbooks(a, b), [])

    def test_differing_cell_is_reported_with_sheet_and_coordinates(self):
        a = _write(self.tmp, "a.xlsx", [["x", 1]])
        b = _write(self.tmp, "b.xlsx", [["x", 2]])

        differences = compare_workbooks(a, b)

        self.assertEqual(len(differences), 1)
        self.assertIn("Sheet1", differences[0])
        self.assertIn("row 1", differences[0])
        self.assertIn("col 2", differences[0])

    def test_ignored_substring_suppresses_the_difference(self):
        a = _write(self.tmp, "a.xlsx", [["prepared 2026-07-07"]])
        b = _write(self.tmp, "b.xlsx", [["prepared 2026-09-04"]])

        self.assertEqual(compare_workbooks(a, b), [])

    def test_ignored_substring_must_match_both_sides(self):
        a = _write(self.tmp, "a.xlsx", [["prepared 2026-07-07"]])
        b = _write(self.tmp, "b.xlsx", [["something else"]])

        self.assertEqual(len(compare_workbooks(a, b)), 1)

    def test_sheet_name_mismatch_is_reported(self):
        a = _write(self.tmp, "a.xlsx", [["x"]], sheet="Alpha")
        b = _write(self.tmp, "b.xlsx", [["x"]], sheet="Beta")

        differences = compare_workbooks(a, b)

        self.assertEqual(len(differences), 1)
        self.assertIn("sheet names differ", differences[0])
