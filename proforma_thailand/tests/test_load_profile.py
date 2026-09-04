import tempfile
from datetime import date, datetime, time
from pathlib import Path
from unittest import TestCase

from openpyxl import Workbook

from proforma_thailand.load_profile import (
    SHEET_NAME,
    build_calendar_year,
    extract_intervals,
)

CALENDAR_MONTHS = [(2026, m) for m in range(1, 7)] + [(2025, m) for m in range(7, 13)]


def _intervals_for(year, month, days_in_month, kwh=100.0, day_type="Weekday"):
    rows = []
    for day in range(1, days_in_month + 1):
        for slot in range(96):
            rows.append(
                {
                    "date": date(year, month, day),
                    "end_minute": (slot + 1) * 15,
                    "day_type": day_type,
                    "kwh": kwh,
                }
            )
    return rows


DAYS = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


def _full_year():
    rows = []
    for year, month in CALENDAR_MONTHS:
        rows.extend(_intervals_for(year, month, DAYS[month]))
    return rows


class BuildCalendarYearTests(TestCase):

    def test_produces_35040_values(self):
        loads, _, _ = build_calendar_year(_full_year(), CALENDAR_MONTHS)

        self.assertEqual(len(loads), 35040)

    def test_kwh_is_converted_to_kw(self):
        loads, _, _ = build_calendar_year(_full_year(), CALENDAR_MONTHS)

        self.assertAlmostEqual(loads[0], 400.0, places=6)

    def test_holiday_day_types_become_all_off_peak_dates(self):
        rows = _full_year()
        for row in rows:
            if row["date"] == date(2026, 1, 5):
                row["day_type"] = "Holiday"

        _, off_peak, _ = build_calendar_year(rows, CALENDAR_MONTHS)

        self.assertIn(date(2026, 1, 5), off_peak)

    def test_qa_reports_totals_and_peak(self):
        _, _, qa = build_calendar_year(_full_year(), CALENDAR_MONTHS)

        self.assertEqual(qa["days"], 365)
        self.assertEqual(qa["missing_days"], [])
        self.assertAlmostEqual(qa["total_kwh"], 35040 * 100.0, places=3)
        self.assertAlmostEqual(qa["peak_kw"], 400.0, places=6)

    def test_a_missing_day_is_reported_not_silently_padded(self):
        rows = [row for row in _full_year() if row["date"] != date(2026, 3, 15)]

        with self.assertRaises(ValueError) as caught:
            build_calendar_year(rows, CALENDAR_MONTHS)

        self.assertIn("2026-03-15", str(caught.exception))

    def test_a_day_with_wrong_interval_count_is_rejected(self):
        rows = _full_year()
        rows = [
            row for row in rows
            if not (row["date"] == date(2026, 4, 2) and row["end_minute"] == 1440)
        ]

        with self.assertRaises(ValueError) as caught:
            build_calendar_year(rows, CALENDAR_MONTHS)

        self.assertIn("2026-04-02", str(caught.exception))
        self.assertIn("95", str(caught.exception))


def _write_workbook(tmp_path, name, kwh_value):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = SHEET_NAME
    worksheet.append(
        ["Timestamp", None, "Time", None, "DayType", None, None, None, None, "kWh"]
    )
    row = [None] * 10
    row[0] = datetime(2026, 1, 1)
    row[2] = time(0, 15)
    row[4] = "Weekday"
    row[9] = kwh_value
    worksheet.append(row)
    path = tmp_path / name
    workbook.save(path)
    return path


class ExtractIntervalsTests(TestCase):

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def test_a_missing_kwh_cell_raises(self):
        path = _write_workbook(self.tmp, "missing.xlsx", None)

        with self.assertRaises(ValueError) as caught:
            extract_intervals(path)

        self.assertIn("2026-01-01", str(caught.exception))

    def test_a_legitimate_zero_kwh_reading_is_accepted(self):
        path = _write_workbook(self.tmp, "zero.xlsx", 0.0)

        rows = extract_intervals(path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kwh"], 0.0)
