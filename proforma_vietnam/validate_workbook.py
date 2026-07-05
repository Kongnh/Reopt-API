"""Recalculate an audit workbook in real Excel and read back its checks.

The workbook built by ``xlsx_builder``/``audit_sheets`` carries live Excel
formulas, per-check PASS/REVIEW cells on the Pro Forma (Audit) sheet, and an
aggregate status on the Cover sheet. openpyxl writes those formulas but cannot
evaluate them, so the tie-out is normally verified by opening the file in
Excel by hand. This module automates that step: it opens the workbook
read-only in an invisible Excel instance via COM, forces a full calculation
rebuild, waits for calculation to settle, and reads the evaluated Cover
status plus every check cell. It is used to validate re-baselined
deliverables before they are published.

Requirements: Windows, Microsoft Excel, and pywin32 (``win32com``).

Command line::

    python -m proforma_vietnam.validate_workbook <path> [<path> ...]

Each path is either an ``.xlsx`` file or a case directory containing exactly
one ``vietnam_report_*.xlsx``. One Excel instance is reused across all files.
Exit code 0 iff every workbook shows "ALL CHECKS PASS" and no REVIEW cells.
"""

import gc
import glob
import os
import sys
import time

try:
    import pywintypes
    import win32com.client
except ImportError:  # non-Windows or pywin32 missing; validate_workbook() raises
    pywintypes = None
    win32com = None

from proforma_vietnam.audit_sheets import PRO_FORMA_SHEET

COVER_SHEET = "Cover"
# Strings written by audit_sheets.write_cover_sheet / write_pro_forma_audit_sheet.
# The validator anchors on these labels, not on cell coordinates, so layout
# tweaks (added rows/columns) do not silently break it.
COVER_STATUS_LABEL = "Model validation status"
ALL_CHECKS_PASS = "ALL CHECKS PASS"
CHECKS_HEADER_FIRST = "Check"
CHECKS_HEADER_STATUS = "Status"

CALCULATION_TIMEOUT_S = 60.0
_XL_CALCULATION_DONE = 0  # XlCalculationState.xlDone


def validate_workbook(xlsx_path):
    """Recalculate one workbook in Excel and summarise its check statuses.

    Returns ``{"file", "cover_status", "pass_count", "review_count", "ok"}``
    where ``ok`` means the Cover aggregate reads "ALL CHECKS PASS" and no
    check cell on the Pro Forma (Audit) sheet evaluated to REVIEW.
    """
    excel = _open_excel()
    try:
        return _validate_one(excel, xlsx_path)
    finally:
        _quit_excel(excel)


def _open_excel():
    if win32com is None:
        raise RuntimeError(
            "validate_workbook requires Windows with Microsoft Excel and "
            "pywin32 (win32com is not importable)"
        )
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    return excel


def _quit_excel(excel):
    try:
        excel.Quit()
    except Exception:
        pass  # best-effort teardown; never mask the original error
    # Release COM references so the dedicated EXCEL.EXE started by DispatchEx
    # actually exits once the caller's binding goes away.
    del excel
    gc.collect()


def _validate_one(excel, xlsx_path):
    path = os.path.abspath(xlsx_path)
    if not os.path.isfile(path):
        raise RuntimeError(f"workbook not found: {path}")
    workbook = None
    try:
        try:
            # Positional args: Filename, UpdateLinks=0, ReadOnly=True
            workbook = excel.Workbooks.Open(path, 0, True)
            excel.CalculateFullRebuild()
            _wait_for_calculation(excel, path)
            cover_status = _read_cover_status(workbook, path)
            pass_count, review_count = _read_check_statuses(workbook, path)
        except pywintypes.com_error as error:
            raise RuntimeError(
                f"Excel COM error while validating {path}: {error}"
            ) from error
    finally:
        if workbook is not None:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass  # Quit() tears the instance down regardless
    return {
        "file": path,
        "cover_status": cover_status,
        "pass_count": pass_count,
        "review_count": review_count,
        "ok": cover_status == ALL_CHECKS_PASS and review_count == 0,
    }


def _wait_for_calculation(excel, path):
    deadline = time.monotonic() + CALCULATION_TIMEOUT_S
    while excel.CalculationState != _XL_CALCULATION_DONE:
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Excel calculation did not settle within "
                f"{CALCULATION_TIMEOUT_S:.0f}s for {path}"
            )
        time.sleep(0.1)


def _used_rows(worksheet):
    """UsedRange values as a list of row tuples (normalises COM shapes)."""
    values = worksheet.UsedRange.Value
    if values is None:
        return []
    if not isinstance(values, tuple):  # single cell
        return [(values,)]
    if values and not isinstance(values[0], tuple):  # single row
        return [values]
    return list(values)


def _read_cover_status(workbook, path):
    """Evaluated aggregate status next to the Cover 'Model validation status'."""
    for row in _used_rows(workbook.Worksheets(COVER_SHEET)):
        for index, value in enumerate(row):
            if value == COVER_STATUS_LABEL and index + 1 < len(row):
                status = row[index + 1]
                if isinstance(status, str) and status:
                    return status
    raise RuntimeError(
        f"{path}: no '{COVER_STATUS_LABEL}' status found on the Cover sheet "
        "(is this an audit workbook with a derivation block?)"
    )


def _read_check_statuses(workbook, path):
    """(pass_count, review_count) from the Pro Forma (Audit) checks block."""
    rows = _used_rows(workbook.Worksheets(PRO_FORMA_SHEET))
    header_index = status_column = None
    for index, row in enumerate(rows):
        if CHECKS_HEADER_FIRST in row and CHECKS_HEADER_STATUS in row:
            header_index = index
            status_column = row.index(CHECKS_HEADER_STATUS)
            break
    if header_index is None:
        raise RuntimeError(
            f"{path}: no checks block header "
            f"('{CHECKS_HEADER_FIRST}'/'{CHECKS_HEADER_STATUS}') found on "
            f"the {PRO_FORMA_SHEET!r} sheet"
        )
    pass_count = review_count = 0
    for row in rows[header_index + 1:]:
        value = row[status_column] if status_column < len(row) else None
        if value == "PASS":
            pass_count += 1
        elif value == "REVIEW":
            review_count += 1
    if pass_count + review_count == 0:
        raise RuntimeError(
            f"{path}: checks block header found but no evaluated PASS/REVIEW "
            "cells below it"
        )
    return pass_count, review_count


def _resolve_paths(arguments):
    """Map CLI arguments (xlsx files or case directories) to workbook paths."""
    paths = []
    for argument in arguments:
        if os.path.isdir(argument):
            matches = sorted(
                glob.glob(os.path.join(argument, "vietnam_report_*.xlsx"))
            )
            if not matches:
                raise SystemExit(
                    f"error: no vietnam_report_*.xlsx found in {argument}"
                )
            if len(matches) > 1:
                names = ", ".join(os.path.basename(match) for match in matches)
                raise SystemExit(
                    f"error: multiple vietnam_report_*.xlsx in {argument}: {names}"
                )
            paths.append(matches[0])
        else:
            paths.append(argument)
    return paths


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else list(argv)
    if not arguments:
        print(
            "usage: python -m proforma_vietnam.validate_workbook "
            "<xlsx-or-case-dir> [<xlsx-or-case-dir> ...]",
            file=sys.stderr,
        )
        return 2
    paths = _resolve_paths(arguments)
    excel = _open_excel()  # one instance reused across all files
    all_ok = True
    try:
        for path in paths:
            result = _validate_one(excel, path)
            total = result["pass_count"] + result["review_count"]
            if result["ok"]:
                print(f"PASS  {result['file']}  ({total} checks)")
            else:
                all_ok = False
                print(
                    f"REVIEW {result['file']}  "
                    f"({result['review_count']} of {total} checks failed)"
                )
    finally:
        _quit_excel(excel)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
