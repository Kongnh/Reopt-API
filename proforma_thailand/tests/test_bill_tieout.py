from unittest import TestCase

from proforma_thailand.bill import compute_monthly_bill

# Actual PEA invoice totals for KTH2, from 02_Bills_2025/ and the meter
# workbook's Summary sheet. Only Jun-Nov 2025 overlap the interval data.
INVOICE_TOTALS = {
    (2025, 6): 2576311.21,
    (2025, 7): 2624222.45,
    (2025, 8): 2417188.28,
    (2025, 9): 2528702.23,
    (2025, 10): 2458569.72,
    (2025, 11): 2375516.43,
}

INVOICE_ON_PEAK_KW = {
    (2025, 6): 1368.0,
    (2025, 7): 1376.0,
    (2025, 8): 1320.0,
    (2025, 9): 1296.0,
    (2025, 10): 1328.0,
    (2025, 11): 1360.0,
}


class BillTieOutTests(TestCase):

    def test_june_2025_reconstructs_line_by_line(self):
        bill = compute_monthly_bill(
            peak_kwh=288960.0,
            off_peak_kwh=164380.0,
            holiday_kwh=178240.0,
            on_peak_kw=1368.0,
            year=2025,
            month=6,
        )

        self.assertAlmostEqual(bill["demand_charge"], 181848.24, places=2)
        self.assertAlmostEqual(bill["peak_energy"], 1208979.74, places=2)
        self.assertAlmostEqual(bill["off_peak_energy"], 892079.69, places=2)
        self.assertAlmostEqual(bill["base_total"], 2283219.91, places=1)
        self.assertAlmostEqual(bill["ft_charge"], 124547.58, places=2)
        self.assertAlmostEqual(bill["vat"], 168543.72, places=2)
        self.assertAlmostEqual(bill["total"], 2576311.21, places=1)

    def test_november_2025_uses_the_september_ft_window(self):
        bill = compute_monthly_bill(
            peak_kwh=266920.0,
            off_peak_kwh=148920.0,
            holiday_kwh=169920.0,
            on_peak_kw=1360.0,
            year=2025,
            month=11,
        )

        # 585,760 kWh at the Sep-Dec Ft of 0.1572
        self.assertAlmostEqual(bill["ft_charge"], 92081.47, places=2)
        self.assertAlmostEqual(bill["base_total"], 2128027.34, places=1)

    def test_holiday_energy_is_billed_at_the_off_peak_rate(self):
        with_holiday = compute_monthly_bill(
            peak_kwh=0.0, off_peak_kwh=0.0, holiday_kwh=1000.0,
            on_peak_kw=0.0, year=2025, month=6,
        )
        as_off_peak = compute_monthly_bill(
            peak_kwh=0.0, off_peak_kwh=1000.0, holiday_kwh=0.0,
            on_peak_kw=0.0, year=2025, month=6,
        )

        self.assertAlmostEqual(
            with_holiday["off_peak_energy"], as_off_peak["off_peak_energy"], places=6
        )

    def test_all_six_overlap_months_tie_out_within_one_percent(self):
        from proforma_thailand.load_profile import (
            build_month_buckets,
            extract_intervals,
        )

        XLSM = (
            r"C:/Users/kongn/OneDrive/Máy tính/Allotrope/2026/"
            r"13. Keen Project/01_Load_Data/"
            r"ROFU Thailand 15-Minute Interval Data.xlsm"
        )
        buckets = build_month_buckets(extract_intervals(XLSM))

        for key, invoice_total in INVOICE_TOTALS.items():
            year, month = key
            bucket = buckets[key]
            bill = compute_monthly_bill(
                peak_kwh=bucket["peak_kwh"],
                off_peak_kwh=bucket["off_peak_kwh"],
                holiday_kwh=bucket["holiday_kwh"],
                on_peak_kw=INVOICE_ON_PEAK_KW[key],
                year=year,
                month=month,
            )
            error = abs(bill["total"] - invoice_total) / invoice_total
            self.assertLess(
                error, 0.01,
                "{}-{:02d}: modelled {:.2f} vs invoice {:.2f} ({:.3%})".format(
                    year, month, bill["total"], invoice_total, error
                ),
            )
