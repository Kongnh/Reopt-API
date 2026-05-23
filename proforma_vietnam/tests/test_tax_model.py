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
        cit_by_year = calculate_cit([-1000000, 0, 1000000, 1000000, 1000000])

        self.assertEqual(cit_by_year, [0, 0, 0, 0, 100000])

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
