from datetime import datetime
from unittest import TestCase

from reoptjl.src.vietnam import build_evn_tariff
from reoptjl.src.vietnam.example_submit import build_example_payload


class VietnamEvnTariffTests(TestCase):

    def test_builds_8760_standard_manufacturing_rates_for_voltage_level(self):
        tariff = build_evn_tariff(year=2025, voltage_level="22-110kV")

        self.assertEqual(len(tariff["tou_energy_rates_per_kwh"]), 8760)
        self.assertEqual(tariff["monthly_demand_rates"], [])
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][0], 1190)

        jan_5_2025_10am = datetime(2025, 1, 5, 10).timetuple().tm_yday - 1
        jan_5_2025_10am_index = jan_5_2025_10am * 24 + 10
        jan_6_2025_10am = datetime(2025, 1, 6, 10).timetuple().tm_yday - 1
        jan_6_2025_10am_index = jan_6_2025_10am * 24 + 10
        jan_6_2025_2am = datetime(2025, 1, 6, 2).timetuple().tm_yday - 1
        jan_6_2025_2am_index = jan_6_2025_2am * 24 + 2

        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_5_2025_10am_index], 1833)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 3398)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_2am_index], 1190)

    def test_converts_standard_rates_to_usd_when_requested(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level=">=110kV",
            currency="usd",
            exchange_rate_vnd_per_usd=25000
        )

        jan_6_2025_10am = datetime(2025, 1, 6, 10).timetuple().tm_yday - 1
        jan_6_2025_10am_index = jan_6_2025_10am * 24 + 10

        self.assertAlmostEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 3266 / 25000)

    def test_two_component_pilot_uses_ca_energy_and_cp_monthly_demand_rates(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level="6-22kV",
            two_component_pilot_enabled=True
        )

        jan_6_2025_10am = datetime(2025, 1, 6, 10).timetuple().tm_yday - 1
        jan_6_2025_10am_index = jan_6_2025_10am * 24 + 10

        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 2189)
        self.assertEqual(tariff["monthly_demand_rates"], [240050] * 12)

    def test_base_rate_override_applies_standard_tou_multipliers(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level="<6kV",
            base_rate_per_kwh=2000
        )

        jan_6_2025_10am = datetime(2025, 1, 6, 10).timetuple().tm_yday - 1
        jan_6_2025_10am_index = jan_6_2025_10am * 24 + 10
        jan_6_2025_2am = datetime(2025, 1, 6, 2).timetuple().tm_yday - 1
        jan_6_2025_2am_index = jan_6_2025_2am * 24 + 2

        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 3560)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_2am_index], 1040)

    def test_decision_963_tou_schedule_removes_morning_peak_and_moves_peak_later(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level="22-110kV",
            tou_schedule="decision_963"
        )

        jan_6_2025_5am_index = (datetime(2025, 1, 6, 5).timetuple().tm_yday - 1) * 24 + 5
        jan_6_2025_10am_index = (datetime(2025, 1, 6, 10).timetuple().tm_yday - 1) * 24 + 10
        jan_6_2025_17_index = (datetime(2025, 1, 6, 17).timetuple().tm_yday - 1) * 24 + 17
        jan_6_2025_18_index = (datetime(2025, 1, 6, 18).timetuple().tm_yday - 1) * 24 + 18
        jan_6_2025_22_index = (datetime(2025, 1, 6, 22).timetuple().tm_yday - 1) * 24 + 22
        jan_6_2025_23_index = (datetime(2025, 1, 6, 23).timetuple().tm_yday - 1) * 24 + 23

        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_5am_index], 1190)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 1833)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_17_index], 1833)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_18_index], 3398)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_22_index], 3398)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_23_index], 1833)

    def test_tou_schedule_can_compare_current_and_decision_963_cases(self):
        current_tariff = build_evn_tariff(
            year=2025,
            voltage_level="22-110kV",
            tou_schedule="current"
        )
        decision_963_tariff = build_evn_tariff(
            year=2025,
            voltage_level="22-110kV",
            tou_schedule="decision_963"
        )

        jan_6_2025_10am_index = (datetime(2025, 1, 6, 10).timetuple().tm_yday - 1) * 24 + 10
        jan_6_2025_21_index = (datetime(2025, 1, 6, 21).timetuple().tm_yday - 1) * 24 + 21
        jan_6_2025_23_index = (datetime(2025, 1, 6, 23).timetuple().tm_yday - 1) * 24 + 23

        self.assertEqual(current_tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 3398)
        self.assertEqual(decision_963_tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 1833)
        self.assertEqual(current_tariff["tou_energy_rates_per_kwh"][jan_6_2025_21_index], 1833)
        self.assertEqual(decision_963_tariff["tou_energy_rates_per_kwh"][jan_6_2025_21_index], 3398)
        self.assertEqual(current_tariff["tou_energy_rates_per_kwh"][jan_6_2025_23_index], 1190)
        self.assertEqual(decision_963_tariff["tou_energy_rates_per_kwh"][jan_6_2025_23_index], 1833)

    def test_example_payload_maps_builder_output_to_electric_tariff_inputs(self):
        payload = build_example_payload()

        self.assertEqual(len(payload["ElectricTariff"]["tou_energy_rates_per_kwh"]), 8760)
        self.assertEqual(payload["ElectricTariff"]["monthly_demand_rates"], [])
        self.assertEqual(payload["Settings"]["time_steps_per_hour"], 1)
        self.assertEqual(payload["ElectricLoad"]["year"], 2025)
        # Vintage disclosure is audit metadata, not a REopt.jl ElectricTariff
        # field — it must never reach a payload submitted to REopt.jl.
        self.assertNotIn("rate_vintage_year", payload["ElectricTariff"])
        self.assertNotIn("rate_vintage_source", payload["ElectricTariff"])

    def test_standard_rates_fall_back_to_latest_vintage_at_or_before_requested_year(self):
        tariff = build_evn_tariff(year=2026, voltage_level="22-110kV")

        jan_6_2025_10am = datetime(2025, 1, 6, 10).timetuple().tm_yday - 1
        jan_6_2025_10am_index = jan_6_2025_10am * 24 + 10

        self.assertEqual(tariff["rate_vintage_year"], 2025)
        self.assertIn("1279/QD-BCT", tariff["rate_vintage_source"])
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 3398)

    def test_standard_rates_raise_for_year_before_earliest_vintage(self):
        # 2019 (not 2020) is deliberately used here: 2020 is a leap year, which
        # would trip the unrelated 8760-hour leap-year guard before the vintage
        # lookup ever runs, and this test wants to isolate the vintage-fallback error.
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(year=2019, voltage_level="22-110kV")

        self.assertIn("2019", str(context.exception))

    def test_two_component_pilot_rates_fall_back_to_latest_vintage(self):
        tariff = build_evn_tariff(
            year=2026,
            voltage_level="6-22kV",
            two_component_pilot_enabled=True,
        )

        jan_6_2025_10am = datetime(2025, 1, 6, 10).timetuple().tm_yday - 1
        jan_6_2025_10am_index = jan_6_2025_10am * 24 + 10

        self.assertEqual(tariff["rate_vintage_year"], 2025)
        self.assertIn("official pilot billing from 2026-07", tariff["rate_vintage_source"])
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 2189)
        self.assertEqual(tariff["monthly_demand_rates"], [240050] * 12)

    def test_example_payload_accepts_decision_963_schedule_for_case_studies(self):
        payload = build_example_payload(tou_schedule="decision_963")

        jan_6_2025_10am_index = (datetime(2025, 1, 6, 10).timetuple().tm_yday - 1) * 24 + 10
        jan_6_2025_21_index = (datetime(2025, 1, 6, 21).timetuple().tm_yday - 1) * 24 + 21

        self.assertAlmostEqual(
            payload["ElectricTariff"]["tou_energy_rates_per_kwh"][jan_6_2025_10am_index],
            1833 / 25000
        )
        self.assertAlmostEqual(
            payload["ElectricTariff"]["tou_energy_rates_per_kwh"][jan_6_2025_21_index],
            3398 / 25000
        )

    def test_leap_year_is_rejected(self):
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(year=2028, voltage_level="22-110kV")

        self.assertIn("8760", str(context.exception))
        self.assertIn("non-leap", str(context.exception))

    def test_non_manufacturing_tariff_category_is_rejected(self):
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(year=2025, voltage_level="22-110kV", tariff_category="residential")

        self.assertIn("residential", str(context.exception))

    def test_unsupported_voltage_level_raises_with_message(self):
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(year=2025, voltage_level="500kV")

        self.assertIn("500kV", str(context.exception))

    def test_voltage_level_aliases_produce_identical_rates(self):
        spelled_out = build_evn_tariff(year=2025, voltage_level="6 kV to less than 22 kV")
        abbreviated = build_evn_tariff(year=2025, voltage_level="6-22kV")

        self.assertEqual(
            spelled_out["tou_energy_rates_per_kwh"],
            abbreviated["tou_energy_rates_per_kwh"]
        )

    def test_unsupported_tou_schedule_raises_with_message(self):
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(year=2025, voltage_level="22-110kV", tou_schedule="decision_9999")

        self.assertIn("decision_9999", str(context.exception))

    def test_unsupported_currency_raises(self):
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(year=2025, voltage_level="22-110kV", currency="eur")

        self.assertIn("Unsupported currency", str(context.exception))

    def test_usd_currency_without_exchange_rate_raises(self):
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(
                year=2025,
                voltage_level="22-110kV",
                currency="usd",
                exchange_rate_vnd_per_usd=None
            )

        self.assertIn("exchange_rate_vnd_per_usd is required", str(context.exception))

    def test_exact_vintage_match_echoes_metadata_for_requested_year(self):
        tariff = build_evn_tariff(year=2025, voltage_level="22-110kV")

        self.assertEqual(tariff["rate_vintage_year"], 2025)
        self.assertIn("1279/QD-BCT", tariff["rate_vintage_source"])

    def test_two_component_pilot_raises_for_year_before_earliest_vintage(self):
        # 2023 (not 2024) is deliberately used here: 2024 is a leap year, which
        # would trip the unrelated 8760-hour leap-year guard before the pilot
        # vintage lookup ever runs, and this test wants to isolate the
        # vintage-fallback error for the two-component pilot table.
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(
                year=2023,
                voltage_level="6-22kV",
                two_component_pilot_enabled=True
            )

        self.assertIn("2023", str(context.exception))
        self.assertIn("two-component pilot", str(context.exception))

    def test_base_rate_override_has_no_vintage_metadata(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level="<6kV",
            base_rate_per_kwh=2000
        )

        self.assertNotIn("rate_vintage_year", tariff)
        self.assertNotIn("rate_vintage_source", tariff)

    def test_two_component_pilot_usd_conversion_covers_capacity_rate(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level="6-22kV",
            two_component_pilot_enabled=True,
            currency="usd",
            exchange_rate_vnd_per_usd=25000
        )

        jan_6_2025_10am = datetime(2025, 1, 6, 10).timetuple().tm_yday - 1
        jan_6_2025_10am_index = jan_6_2025_10am * 24 + 10

        self.assertEqual(tariff["monthly_demand_rates"], [240050 / 25000] * 12)
        self.assertAlmostEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 2189 / 25000)

    def test_two_component_pilot_takes_precedence_over_base_rate_override(self):
        pilot_with_base_rate_override = build_evn_tariff(
            year=2025,
            voltage_level="6-22kV",
            two_component_pilot_enabled=True,
            base_rate_per_kwh=2000
        )
        pilot_only = build_evn_tariff(
            year=2025,
            voltage_level="6-22kV",
            two_component_pilot_enabled=True
        )

        # Documents current precedence: the pilot branch in _rates_for() returns
        # before the base_rate_per_kwh branch is reached, so base_rate_per_kwh
        # is silently ignored whenever the pilot is enabled.
        self.assertEqual(pilot_with_base_rate_override, pilot_only)

    def test_builds_business_category_rates_for_22kv_and_above(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level="22-110kV",
            tariff_category="business",
        )

        jan_5_2025_10am_index = (datetime(2025, 1, 5, 10).timetuple().tm_yday - 1) * 24 + 10
        jan_6_2025_10am_index = (datetime(2025, 1, 6, 10).timetuple().tm_yday - 1) * 24 + 10
        jan_6_2025_2am_index = (datetime(2025, 1, 6, 2).timetuple().tm_yday - 1) * 24 + 2

        # Sunday 10:00 normal / Monday 10:00 peak / Monday 02:00 off-peak,
        # kinh doanh >=22kV tier per Decision 1279/QD-BCT (2025-05-09).
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_5_2025_10am_index], 2887)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 5025)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_2am_index], 1609)
        self.assertEqual(tariff["rate_vintage_year"], 2025)
        self.assertIn("1279/QD-BCT", tariff["rate_vintage_source"])

    def test_business_category_maps_110kv_connections_to_22kv_and_above_tier(self):
        # The kinh doanh table has a single ">=22kV" tier, so both engine
        # voltage keys at or above 22kV resolve to the same rates.
        tariff_110 = build_evn_tariff(
            year=2025, voltage_level=">=110kV", tariff_category="business"
        )
        tariff_22 = build_evn_tariff(
            year=2025, voltage_level="22-110kV", tariff_category="business"
        )

        self.assertEqual(
            tariff_110["tou_energy_rates_per_kwh"],
            tariff_22["tou_energy_rates_per_kwh"],
        )

    def test_business_category_lower_voltage_tiers(self):
        jan_6_2025_2am_index = (datetime(2025, 1, 6, 2).timetuple().tm_yday - 1) * 24 + 2

        tariff_6_22 = build_evn_tariff(
            year=2025, voltage_level="6-22kV", tariff_category="business"
        )
        tariff_below_6 = build_evn_tariff(
            year=2025, voltage_level="<6kV", tariff_category="business"
        )

        self.assertEqual(tariff_6_22["tou_energy_rates_per_kwh"][jan_6_2025_2am_index], 1829)
        self.assertEqual(tariff_below_6["tou_energy_rates_per_kwh"][jan_6_2025_2am_index], 1918)

    def test_business_category_with_decision_963_schedule(self):
        tariff = build_evn_tariff(
            year=2025,
            voltage_level="22-110kV",
            tariff_category="business",
            tou_schedule="decision_963",
        )

        jan_6_2025_5am_index = (datetime(2025, 1, 6, 5).timetuple().tm_yday - 1) * 24 + 5
        jan_6_2025_10am_index = (datetime(2025, 1, 6, 10).timetuple().tm_yday - 1) * 24 + 10
        jan_6_2025_18_index = (datetime(2025, 1, 6, 18).timetuple().tm_yday - 1) * 24 + 18

        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_5am_index], 1609)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_10am_index], 2887)
        self.assertEqual(tariff["tou_energy_rates_per_kwh"][jan_6_2025_18_index], 5025)

    def test_two_component_pilot_rejects_business_category(self):
        # The two-component pilot is defined for production (manufacturing)
        # customers; combining it with the kinh doanh table would silently
        # ignore the category, so it raises instead.
        with self.assertRaises(ValueError) as context:
            build_evn_tariff(
                year=2025,
                voltage_level="22-110kV",
                tariff_category="business",
                two_component_pilot_enabled=True,
            )

        self.assertIn("two-component", str(context.exception))
