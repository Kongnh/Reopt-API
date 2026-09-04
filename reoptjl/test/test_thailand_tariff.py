from datetime import date
from unittest import TestCase

from reoptjl.src.thailand.pea_tariff import AUDIT_METADATA_KEYS, build_pea_tariff

# Synthetic calendar year used by the Rofu case: Jan-Jun from 2026,
# Jul-Dec from 2025. See the plan's Global Constraints.
CALENDAR_MONTHS = [(2026, m) for m in range(1, 7)] + [(2025, m) for m in range(7, 13)]

# The real REopt.jl ElectricTariffInputs fields build_pea_tariff() produces.
REOPT_PAYLOAD_KEYS = {
    "tou_energy_rates_per_kwh",
    "coincident_peak_load_charge_per_kw",
    "coincident_peak_load_active_time_steps",
}


class PeaTariffTests(TestCase):

    def test_energy_array_is_35040_long(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertEqual(len(tariff["tou_energy_rates_per_kwh"]), 35040)

    def test_first_interval_of_january_is_off_peak_plus_ft(self):
        # Interval 0 ends at 00:15 on 1 Jan, which is off-peak. January maps to
        # 2026-01, whose Ft falls back to the Sep-Dec 2025 window (0.1572).
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][0], 2.6037 + 0.1572, places=6
        )

    def test_interval_ending_0915_on_a_weekday_is_peak(self):
        # 1 Jan is index 0; slot 37 ends at 09:30. Peak is 09:00 < t <= 22:00.
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][37], 4.1839 + 0.1572, places=6
        )

    def test_interval_ending_exactly_0900_is_off_peak(self):
        # Slot 35 ends at 09:00, which is NOT in (09:00, 22:00].
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][35], 2.6037 + 0.1572, places=6
        )

    def test_interval_ending_exactly_2200_is_peak(self):
        # Slot 87 ends at 22:00, which IS in (09:00, 22:00].
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][87], 4.1839 + 0.1572, places=6
        )

    def test_all_off_peak_date_has_no_peak_intervals(self):
        tariff = build_pea_tariff(
            CALENDAR_MONTHS, all_off_peak_dates={date(2026, 1, 1)}
        )
        first_day = tariff["tou_energy_rates_per_kwh"][:96]

        self.assertTrue(
            all(abs(rate - (2.6037 + 0.1572)) < 1e-6 for rate in first_day)
        )

    def test_coincident_peak_has_twelve_periods_at_the_demand_rate(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertEqual(len(tariff["coincident_peak_load_charge_per_kw"]), 12)
        self.assertEqual(len(tariff["coincident_peak_load_active_time_steps"]), 12)
        self.assertTrue(
            all(rate == 132.93 for rate in tariff["coincident_peak_load_charge_per_kw"])
        )

    def test_coincident_peak_time_steps_are_one_based_and_disjoint(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())
        sets = tariff["coincident_peak_load_active_time_steps"]
        flat = [ts for group in sets for ts in group]

        self.assertEqual(len(flat), len(set(flat)))
        self.assertGreaterEqual(min(flat), 1)
        self.assertLessEqual(max(flat), 35040)

    def test_coincident_peak_indices_align_with_peak_energy_rates(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())
        rates = tariff["tou_energy_rates_per_kwh"]
        january = tariff["coincident_peak_load_active_time_steps"][0]

        for timestep in january:
            self.assertGreater(rates[timestep - 1], 4.0)

    def test_usd_conversion_divides_every_money_field(self):
        thb_tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())
        tariff = build_pea_tariff(
            CALENDAR_MONTHS,
            all_off_peak_dates=set(),
            currency="usd",
            exchange_rate_thb_per_usd=32.5,
        )

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][0], (2.6037 + 0.1572) / 32.5, places=8
        )
        self.assertAlmostEqual(
            tariff["coincident_peak_load_charge_per_kw"][0], 132.93 / 32.5, places=8
        )
        self.assertAlmostEqual(
            tariff["service_charge_per_month"],
            thb_tariff["service_charge_per_month"] / 32.5,
            places=8,
        )
        self.assertAlmostEqual(
            tariff["power_factor_charge_per_kvar"],
            thb_tariff["power_factor_charge_per_kvar"] / 32.5,
            places=8,
        )
        self.assertAlmostEqual(
            tariff["ft_per_kwh_by_month"][0],
            thb_tariff["ft_per_kwh_by_month"][0] / 32.5,
            places=8,
        )

    def test_usd_without_an_exchange_rate_raises(self):
        with self.assertRaises(ValueError):
            build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set(), currency="usd")

    def test_rate_vintage_is_disclosed(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertEqual(tariff["rate_vintage_year"], 2025)
        self.assertIn("4224", tariff["rate_vintage_source"])

    def test_calendar_months_must_be_twelve(self):
        with self.assertRaises(ValueError):
            build_pea_tariff(CALENDAR_MONTHS[:11], all_off_peak_dates=set())

    def test_returned_keys_are_exactly_payload_plus_audit_metadata(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertEqual(
            set(tariff.keys()), REOPT_PAYLOAD_KEYS | set(AUDIT_METADATA_KEYS)
        )
