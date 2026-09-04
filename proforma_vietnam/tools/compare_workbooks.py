"""Cell-level workbook comparison, used as the Vietnam regression gate.

The report workbooks are deterministic apart from a "prepared <date>" cell on
the Cover and Executive Summary sheets, so a straight byte comparison is not
usable (and the zip container carries timestamps regardless). This compares
cell values and skips pairs where both sides contain an ignored substring.
"""

from pathlib import Path

from openpyxl import load_workbook

DEFAULT_IGNORE_SUBSTRINGS = ("prepared ",)


def compare_workbooks(path_a, path_b, ignore_substrings=DEFAULT_IGNORE_SUBSTRINGS):
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
            for col_index, (value_a, value_b) in enumerate(zip(row_a, row_b), start=1):
                if value_a == value_b:
                    continue
                if _both_ignored(value_a, value_b, ignore_substrings):
                    continue
                differences.append(
                    "{}: row {} col {}: {!r} != {!r}".format(
                        name, row_index, col_index, value_a, value_b
                    )
                )
    return differences


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


def rebuild_all_cases(repo_root, out_dir):
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
        built[name] = rebuild_report(target)
    return built
