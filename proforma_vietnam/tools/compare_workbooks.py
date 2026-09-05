"""Cell-level workbook comparison, used as the Vietnam regression gate.

The report workbooks are deterministic apart from a "prepared <date>" cell on
the Cover and Executive Summary sheets, so a straight byte comparison is not
usable (and the zip container carries timestamps regardless). This compares
cell values and skips pairs where both sides contain an ignored substring.
"""

import re
from pathlib import Path

from openpyxl import load_workbook

# Nothing is ignored by substring. The precise DEFAULT_IGNORE_ROW_LABELS rule
# below covers the one genuinely volatile row, the prepared-on date. A
# substring of "prepared " also hid Cover and Executive Summary subtitles,
# which is how a Vietnam-titled Thailand workbook passed the gate.
DEFAULT_IGNORE_SUBSTRINGS = ()
# The Assumptions sheet splits the run date into a label cell and a value cell
# ("Report prepared" | "2026-09-05"), so the value carries no ignorable marker
# and the substring rule above cannot see it. Skip the whole row instead, and
# only when BOTH sides carry the label, so a renamed row still reports.
DEFAULT_IGNORE_ROW_LABELS = ("Report prepared",)

# The prepared-on date is metadata, not content, and it is interpolated
# mid-string into the Cover and Executive Summary subtitles. Neutralise
# exactly that token on both sides so every other character of those
# subtitles is still compared. Ignoring the whole row instead is what let a
# Vietnam-titled workbook reach a Thailand client.
_PREPARED_DATE = re.compile(r"(?<=prepared )\d{4}-\d{2}-\d{2}")

# Pinned so a rebuild and its baseline never differ by run date alone. The
# gate compares content; the prepared-on date is metadata, not content.
GATE_PREPARED_ON = "2026-01-01"


def compare_workbooks(path_a, path_b, ignore_substrings=DEFAULT_IGNORE_SUBSTRINGS,
                      ignore_row_labels=DEFAULT_IGNORE_ROW_LABELS):
    """Return a list of difference descriptions; empty means identical."""
    workbook_a = load_workbook(path_a)
    workbook_b = load_workbook(path_b)

    if workbook_a.sheetnames != workbook_b.sheetnames:
        return [
            "sheet names differ: {} != {}".format(
                workbook_a.sheetnames, workbook_b.sheetnames
            )
        ]

    differences = []
    for name in workbook_a.sheetnames:
        sheet_a = workbook_a[name]
        sheet_b = workbook_b[name]
        rows_a = list(sheet_a.iter_rows(values_only=True))
        rows_b = list(sheet_b.iter_rows(values_only=True))
        if len(rows_a) != len(rows_b):
            differences.append(
                "{}: row count differs: {} != {}".format(name, len(rows_a), len(rows_b))
            )
            continue
        for row_index, (row_a, row_b) in enumerate(zip(rows_a, rows_b), start=1):
            if len(row_a) != len(row_b):
                differences.append(
                    "{}: row {} column count differs: {} != {}".format(
                        name, row_index, len(row_a), len(row_b)
                    )
                )
                continue
            if (_row_ignored(row_a, ignore_row_labels)
                    and _row_ignored(row_b, ignore_row_labels)):
                continue
            for col_index, (value_a, value_b) in enumerate(zip(row_a, row_b), start=1):
                if value_a == value_b:
                    continue
                if _normalize_prepared_date(value_a) == _normalize_prepared_date(value_b):
                    continue
                if _both_ignored(value_a, value_b, ignore_substrings):
                    continue
                differences.append(
                    "{}: row {} col {}: {!r} != {!r}".format(
                        name, row_index, col_index, value_a, value_b
                    )
                )
    return differences


def _normalize_prepared_date(value):
    """Replace a "prepared <date>" token with a fixed placeholder.

    Only the ISO date immediately following "prepared " is touched, so a
    bare date cell with no such prefix (e.g. the Assumptions sheet's
    "Report prepared" value cell) is returned unchanged and still compared
    for real.
    """
    if not isinstance(value, str):
        return value
    return _PREPARED_DATE.sub("0000-00-00", value)


def _row_ignored(row, ignore_row_labels):
    """True when the row carries a label marking it as volatile by nature."""
    return any(
        isinstance(value, str) and any(label in value for label in ignore_row_labels)
        for value in row
    )


def _both_ignored(value_a, value_b, ignore_substrings):
    """True when both values are strings carrying the same ignored marker."""
    if not (isinstance(value_a, str) and isinstance(value_b, str)):
        return False
    return any(
        marker in value_a and marker in value_b for marker in ignore_substrings
    )


CASE_DIRS = [
    "outputs/vietnam_case/factory_a/case_1",
    "outputs/vietnam_case/factory_a/case_2",
    "outputs/vietnam_case/factory_a/case_3",
    "outputs/vietnam_case/factory_a/case_4",
    "outputs/vietnam_case/factory_a/case_5",
    "outputs/vietnam_case/factory_a/case_6",
    "outputs/vietnam_case/bess_arbitrage_5mw",
    "outputs/vietnam_case/bess_arbitrage_5mw_mfg",
]


def rebuild_all_cases(repo_root, out_dir, prepared_on=GATE_PREPARED_ON):
    """Rebuild every saved case into ``out_dir``; return {case name: path}.

    Copies each case's results/assumptions/case JSON into a scratch directory so
    rebuild_report writes there instead of over the tracked workbooks.
    """
    import shutil

    from proforma_vietnam.rebuild_report import rebuild_report

    repo_root = Path(repo_root)
    out_dir = Path(out_dir)
    built = {}
    for case_dir in CASE_DIRS:
        source = repo_root / case_dir
        name = "_".join(Path(case_dir).parts[-2:])
        target = out_dir / name
        target.mkdir(parents=True, exist_ok=True)
        for filename in ("results.json", "assumptions.json", "case.json"):
            candidate = source / filename
            if candidate.exists():
                shutil.copy2(candidate, target / filename)
        built[name] = rebuild_report(target, prepared_on=prepared_on)
    return built
