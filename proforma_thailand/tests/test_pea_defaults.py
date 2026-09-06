from unittest import TestCase

from proforma_thailand.defaults import ft_for_month, pea_rates_for_year


class PeaDefaultsTests(TestCase):

    def test_2025_schedule_42_rates(self):
        _, values = pea_rates_for_year(2025)
        rates = values["schedule_4_2"]["22_33kv"]

        self.assertEqual(rates["peak_energy_per_kwh"], 4.1839)
        self.assertEqual(rates["off_peak_energy_per_kwh"], 2.6037)
        self.assertEqual(rates["on_peak_demand_per_kw"], 132.93)
        self.assertEqual(values["service_charge_per_month"], 312.24)
        self.assertEqual(values["vat_fraction"], 0.07)
        self.assertEqual(values["power_factor_charge_per_kvar"], 56.07)
        self.assertEqual(values["power_factor_allowance_fraction"], 0.6197)

    def test_year_without_a_vintage_falls_back_to_the_latest_earlier_one(self):
        vintage_year, _ = pea_rates_for_year(2026)

        self.assertEqual(vintage_year, 2025)

    def test_year_before_every_vintage_raises(self):
        with self.assertRaises(ValueError):
            pea_rates_for_year(2019)

    def test_ft_windows_across_2025(self):
        self.assertEqual(ft_for_month(2025, 3), 0.3672)
        self.assertEqual(ft_for_month(2025, 4), 0.3672)
        self.assertEqual(ft_for_month(2025, 5), 0.1972)
        self.assertEqual(ft_for_month(2025, 8), 0.1972)
        self.assertEqual(ft_for_month(2025, 9), 0.1572)
        self.assertEqual(ft_for_month(2025, 12), 0.1572)

    def test_ft_windows_across_2026(self):
        # Pins the modelled-year months so a stale fallback (Critical/Important 4)
        # can never silently reappear: Jan-Apr 2026 was cut to 9.72 satang/kWh and
        # May-Aug 2026 rose to 16.23 satang/kWh - both published by PEA, not the
        # 2025-09 invoice window this used to fall back to.
        self.assertEqual(ft_for_month(2026, 1), 0.0972)
        self.assertEqual(ft_for_month(2026, 4), 0.0972)
        self.assertEqual(ft_for_month(2026, 5), 0.1623)
        self.assertEqual(ft_for_month(2026, 6), 0.1623)
        self.assertEqual(ft_for_month(2026, 8), 0.1623)

    def test_ft_falls_back_to_the_latest_known_window(self):
        # No window is configured past 2026-05, so a month after that still
        # falls back - this is the intended fallback behaviour, exercised on
        # a month beyond every known window rather than inside the modelled year.
        self.assertEqual(ft_for_month(2027, 1), 0.1623)

    def test_ft_rejects_a_month_before_the_first_window(self):
        with self.assertRaises(ValueError):
            ft_for_month(2019, 1)
