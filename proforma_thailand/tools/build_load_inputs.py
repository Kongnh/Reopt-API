"""Regenerate the committed Thailand load inputs from the source workbook.

The load CSV is a bare load_kw column with no timestamps, so nothing in the
repo could previously prove which months it holds or in what order. This script
regenerates the CSV and the holiday list, and writes a manifest recording the
month order, the row count per month and the SHA-256 of the source workbook, so
a case.json can be checked against the data it claims to describe.

Usage:
    python -m proforma_thailand.tools.build_load_inputs \\
        --source "<path to ROFU Thailand 15-Minute Interval Data.xlsm>" \\
        --calendar-months 2026-01,2026-02,2026-03,2026-04,2026-05,2026-06,\\
2025-07,2025-08,2025-09,2025-10,2025-11,2025-12
"""

import argparse
import hashlib
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOAD_CSV = DATA_DIR / "rofu_load_15min.csv"
HOLIDAYS_JSON = DATA_DIR / "rofu_all_off_peak_dates.json"
MANIFEST = DATA_DIR / "load_manifest.json"
INTERVALS_PER_DAY = 96


def build_manifest(calendar_year_months, rows_per_month, source_sha256):
    """Self-describing record of what the committed CSV actually contains."""
    return {
        "calendar_year_months": [list(pair) for pair in calendar_year_months],
        "rows_per_month": list(rows_per_month),
        "total_rows": sum(rows_per_month),
        "source_sha256": source_sha256,
    }


def validate_calendar_months(calendar_months, manifest):
    """Raise when a case claims a month order the committed data does not have.

    Only the row count was checked before, so swapping two months left the load
    silently misaligned against the tariff with no error anywhere.
    """
    if not manifest:
        return
    expected = [tuple(pair) for pair in manifest["calendar_year_months"]]
    actual = [tuple(pair) for pair in calendar_months]
    if actual != expected:
        raise ValueError(
            "calendar_year_months does not match the committed load data. "
            "The CSV is in the order {}, the case asks for {}. Month order "
            "determines which tariff month each interval is billed under.".format(
                expected, actual
            )
        )


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True,
                        help="Path to the ROFU 15-minute interval .xlsm.")
    parser.add_argument("--calendar-months", required=True,
                        help="Comma-separated YYYY-MM in the order the year is assembled.")
    args = parser.parse_args(argv)

    from proforma_thailand.load_profile import build_calendar_year, extract_intervals

    calendar_months = [
        (int(token.split("-")[0]), int(token.split("-")[1]))
        for token in args.calendar_months.split(",")
        if token.strip()
    ]

    from proforma_thailand.load_profile import _days_in_month

    intervals = extract_intervals(args.source)
    # build_calendar_year returns THREE values, and it already derives the
    # all-off-peak (holiday) dates, so this script writes that file too rather
    # than leaving a second committed input with no producer.
    loads, all_off_peak_dates, qa = build_calendar_year(intervals, calendar_months)

    # _days_in_month returns a LIST OF DATES, not a count.
    rows_per_month = [
        len(_days_in_month(year, month)) * INTERVALS_PER_DAY
        for year, month in calendar_months
    ]

    LOAD_CSV.write_text(
        "load_kw\n" + "\n".join("{:g}".format(value) for value in loads) + "\n",
        encoding="utf-8",
    )
    HOLIDAYS_JSON.write_text(
        json.dumps(sorted(day.isoformat() for day in all_off_peak_dates), indent=2)
        + "\n",
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps(
            build_manifest(calendar_months, rows_per_month, sha256_of(args.source)),
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print("Wrote {} rows to {}".format(len(loads), LOAD_CSV))
    print("Wrote {} all-off-peak dates to {}".format(
        len(all_off_peak_dates), HOLIDAYS_JSON))
    print("Wrote manifest to {}".format(MANIFEST))
    print("QA: {}".format(qa))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
