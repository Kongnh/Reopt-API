from unittest import TestCase

from proforma_vietnam.tools.fade_sizing_probe import (
    align_vietnam_financials,
    degradation_block,
    pin_energy,
    restore_kwh_om,
)


class FadeSizingProbeTests(TestCase):
    """The pure pieces of the sizing check (the solves themselves need the
    research Julia server on port 8082)."""

    def test_degradation_block_cancels_reopts_hours_per_step_factor(self):
        hourly = degradation_block(1, 0.03)
        quarter = degradation_block(4, 0.03)
        self.assertAlmostEqual(hourly["cycle_fade_coefficient"][0], 0.2 / 8000)
        self.assertAlmostEqual(quarter["cycle_fade_coefficient"][0], 4 * 0.2 / 8000)
        self.assertAlmostEqual(quarter["calendar_fade_coefficient"], 4 * hourly["calendar_fade_coefficient"])
        self.assertEqual(hourly["maintenance_strategy"], "augmentation")
        self.assertEqual(hourly["installed_cost_per_kwh_declination_rate"], 0.03)

    def test_restore_kwh_om_puts_back_what_reopt_drops_under_degradation(self):
        results = {
            "inputs": {"ElectricStorage": {"model_degradation": True, "installed_cost_per_kwh": 120.0,
                                            "om_cost_fraction_of_installed_cost": 0.01}},
            "outputs": {"ElectricStorage": {"size_kwh": 4000.0},
                        "Financial": {"year_one_om_costs_before_tax": 20000.0}},
        }
        patched, restored = restore_kwh_om(results)
        self.assertAlmostEqual(restored, 4800.0)
        self.assertAlmostEqual(patched["outputs"]["Financial"]["year_one_om_costs_before_tax"], 24800.0)
        self.assertEqual(results["outputs"]["Financial"]["year_one_om_costs_before_tax"], 20000.0)
        blind = {"inputs": {"ElectricStorage": {}}, "outputs": results["outputs"]}
        self.assertEqual(restore_kwh_om(blind), (blind, 0.0))

    def test_align_vietnam_financials_removes_the_us_defaults(self):
        inputs = {
            "Financial": {"owner_discount_rate_fraction": 0.0624, "offtaker_discount_rate_fraction": 0.0624,
                          "owner_tax_rate_fraction": 0.26, "offtaker_tax_rate_fraction": 0.26,
                          "elec_cost_escalation_rate_fraction": 0.0166,
                          "om_cost_escalation_rate_fraction": 0.025},
            "PV": {"federal_itc_fraction": 0.3, "macrs_option_years": 5, "macrs_bonus_fraction": 1.0},
            "ElectricStorage": {"total_itc_fraction": 0.3, "macrs_option_years": 5, "macrs_bonus_fraction": 1.0},
        }
        changed = align_vietnam_financials(inputs, {"owner_discount_rate_fraction": 0.1,
                                                    "evn_energy_escalation_rate": 0.04})
        self.assertEqual(inputs["Financial"]["offtaker_discount_rate_fraction"], 0.1)
        self.assertEqual(inputs["Financial"]["owner_tax_rate_fraction"], 0.2)
        self.assertEqual(inputs["Financial"]["elec_cost_escalation_rate_fraction"], 0.04)
        self.assertEqual(inputs["PV"]["federal_itc_fraction"], 0)
        self.assertEqual(inputs["ElectricStorage"]["macrs_option_years"], 0)
        self.assertEqual(len(changed), 12)
        self.assertEqual(align_vietnam_financials(inputs, {"owner_discount_rate_fraction": 0.1,
                                                           "evn_energy_escalation_rate": 0.04}), {})

    def test_pin_energy_pins_kwh_only_and_zero_removes_the_battery(self):
        inputs = {"ElectricStorage": {"min_kw": 0.0, "max_kw": 5000.0, "min_kwh": 0.0, "max_kwh": 20000.0}}
        pin_energy(inputs, 4079.0)
        self.assertEqual((inputs["ElectricStorage"]["min_kwh"], inputs["ElectricStorage"]["max_kwh"]), (4079.0, 4079.0))
        self.assertEqual(inputs["ElectricStorage"]["max_kw"], 5000.0)
        pin_energy(inputs, 0.0)
        self.assertEqual(inputs["ElectricStorage"]["max_kw"], 0.0)
        self.assertEqual(inputs["ElectricStorage"]["max_kwh"], 0.0)
