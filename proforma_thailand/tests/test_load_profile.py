from datetime import date
from unittest import TestCase

from proforma_thailand.load_profile import build_calendar_year

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
