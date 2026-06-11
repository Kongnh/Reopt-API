from unittest import TestCase

from proforma_vietnam.tax_model import (
    BESS_DEPRECIATION_YEARS,
    PV_DEPRECIATION_YEARS,
    calculate_cit,
    straight_line_depreciation_schedule,
)


class VietnamTaxModelTests(TestCase):

    def test_cit_schedule_applies_holiday_reduced_rate_and_standard_rate(self):
        taxable_income_by_year = [1000000] * 25

        cit_by_year = calculate_cit(taxable_income_by_year)

        self.assertEqual(cit_by_year[0:4], [0, 0, 0, 0])
        self.assertEqual(cit_by_year[4:13], [100000] * 9)
        self.assertEqual(cit_by_year[13:25], [200000] * 12)

    def test_cit_does_not_tax_negative_income(self):
        cit_by_year = calculate_cit([-1000000, -500000, -200000])

        self.assertEqual(cit_by_year, [0, 0, 0])

    def test_tax_holiday_starts_at_first_profitable_year(self):
        # Circular 78/2014 Art. 18: the exemption period counts from the first
        # year with taxable income, not from the first project year.
        incomes = [-1000000, 0] + [1000000] * 6

        cit_by_year = calculate_cit(incomes)

        # First taxable income in index 2 → holiday covers indices 2-5.
        self.assertEqual(cit_by_year[0:6], [0] * 6)
        # Index 6 is in the 50% reduced-rate window (loss already consumed).
        self.assertEqual(cit_by_year[6], 1000000 * 0.10)

    def test_holiday_clock_starts_no_later_than_year_four(self):
        # If there is no taxable income in the first 3 years, the incentive
        # clock starts in year 4 regardless.
        incomes = [-100.0] * 5 + [1000.0] * 20

        cit_by_year = calculate_cit(incomes)

        # Clock starts at index 3 → holiday indices 3-6.
        self.assertEqual(cit_by_year[5], 0.0)
        self.assertEqual(cit_by_year[6], 0.0)
        # Carried losses were consumed in index 5; index 7 taxed at 10%.
        self.assertAlmostEqual(cit_by_year[7], 1000.0 * 0.10)

    def test_loss_carryforward_offsets_future_taxable_income(self):
        cit_by_year = calculate_cit(
            [-1000.0, 600.0, 800.0],
            holiday_years=0,
            reduced_rate_years=0,
        )

        self.assertEqual(cit_by_year[0], 0.0)
        self.assertEqual(cit_by_year[1], 0.0)  # 600 fully offset, 400 carried
        self.assertAlmostEqual(cit_by_year[2], (800.0 - 400.0) * 0.20)

    def test_loss_carryforward_expires_after_five_years(self):
        incomes = [-1000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 500.0]

        cit_by_year = calculate_cit(incomes, holiday_years=0, reduced_rate_years=0)

        # The year-1 loss is usable only through year 6 (5 following years).
        self.assertAlmostEqual(cit_by_year[6], 500.0 * 0.20)

    def test_pv_uses_20_year_straight_line_depreciation(self):
        depreciation = straight_line_depreciation_schedule(20000000, PV_DEPRECIATION_YEARS, project_years=25)

        self.assertEqual(PV_DEPRECIATION_YEARS, 20)
        self.assertEqual(depreciation[0:20], [1000000] * 20)
        self.assertEqual(depreciation[20:25], [0] * 5)

    def test_bess_uses_8_year_straight_line_depreciation(self):
        depreciation = straight_line_depreciation_schedule(8000000, BESS_DEPRECIATION_YEARS, project_years=12)

        self.assertEqual(BESS_DEPRECIATION_YEARS, 8)
        self.assertEqual(depreciation[0:8], [1000000] * 8)
        self.assertEqual(depreciation[8:12], [0] * 4)
