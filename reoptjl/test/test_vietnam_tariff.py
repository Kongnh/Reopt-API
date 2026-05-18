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
