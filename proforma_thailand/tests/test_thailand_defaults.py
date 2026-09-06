from unittest import TestCase

from proforma_thailand.defaults import (
    EMISSIONS_DEFAULTS,
    FINANCIAL_DEFAULTS,
    PLACEHOLDER_MARKER,
    SITE_DEFAULTS,
    TAX_DEFAULTS,
    TAX_DEFAULTS_RAW,
    ft_for_month,
    placeholder_keys,
    value_of,
)


class ThailandDefaultsTests(TestCase):

    def test_verified_tax_values(self):
        self.assertEqual(TAX_DEFAULTS["cit_standard_rate"], 0.20)
        self.assertEqual(TAX_DEFAULTS["cit_loss_carryforward_years"], 5)
        self.assertEqual(TAX_DEFAULTS["vat_rate_fraction"], 0.07)

    def test_conservative_roof_bound_is_the_default(self):
        # Five roofs at 24x108 m until Ou confirms the size split.
        self.assertEqual(value_of(SITE_DEFAULTS, "usable_roof_area_m2"), 12960 * 0.65)
        self.assertEqual(value_of(SITE_DEFAULTS, "pv_max_kw"), 1685.0)

    def test_every_unconfirmed_value_is_marked_as_a_placeholder(self):
        expected = {
            "bess_installed_cost_per_kw",
            "bess_installed_cost_per_kwh",
            "bess_replace_cost_per_kw",
            "bess_replace_cost_per_kwh",
            "debt_fraction",
            "debt_term_years",
            "insurance_rate_fraction",
            "grid_connection_cost",
            "permitting_and_eia_cost",
            "pea_tariff_escalation_rate",
            "discount_rate",
            "usable_roof_area_m2",
            "pv_max_kw",
            "power_factor_mitigation_cost",
            "inverter_replacement_year",
            "inverter_replacement_fraction_of_pv_capex",
            "bess_min_duration_hours",
            "bess_om_fraction_of_installed_cost",
            "pv_tilt_degrees",
        }

        self.assertEqual(placeholder_keys(), expected)

    def test_placeholder_entries_carry_the_marker_string(self):
        for key in placeholder_keys():
            for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW, EMISSIONS_DEFAULTS):
                if key in block:
                    self.assertEqual(
                        block[key]["source"], PLACEHOLDER_MARKER,
                        "{} is not marked as a placeholder".format(key),
                    )
                    break
            else:
                self.fail("{} is not present in any defaults block".format(key))

    def test_placeholder_entries_still_expose_a_usable_value(self):
        for key in placeholder_keys():
            for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW, EMISSIONS_DEFAULTS):
                if key in block:
                    self.assertIsNotNone(block[key]["value"])
                    break


class DepreciationCitationTests(TestCase):

    def test_depreciation_entries_are_cited_not_left_as_task_stubs(self):
        from proforma_thailand.defaults import TAX_DEFAULTS_RAW

        for key in ("pv_depreciation_years", "bess_depreciation_years"):
            source = TAX_DEFAULTS_RAW[key]["source"]
            self.assertNotIn("TO BE CITED", source)
            self.assertGreater(
                len(source), 20, "{} needs a real citation".format(key)
            )

    def test_depreciation_lives_are_plausible(self):
        from proforma_thailand.defaults import TAX_DEFAULTS

        for key in ("pv_depreciation_years", "bess_depreciation_years"):
            self.assertGreaterEqual(TAX_DEFAULTS[key], 3)
            self.assertLessEqual(TAX_DEFAULTS[key], 25)


class FtWindowTests(TestCase):

    def test_january_2025_uses_the_first_window(self):
        self.assertAlmostEqual(ft_for_month(2025, 1), 0.3672)

    def test_may_2025_uses_the_second_window(self):
        self.assertAlmostEqual(ft_for_month(2025, 5), 0.1972)

    def test_september_2025_uses_the_third_window(self):
        self.assertAlmostEqual(ft_for_month(2025, 9), 0.1572)

    def test_january_2026_uses_the_fourth_window(self):
        # Important 4: this class pinned only 2025-01/05/09 and never asserted
        # a modelled-year (2026) month, so ft_for_month silently falling back
        # to the stale 2025-09 window went undetected. Pin it directly so that
        # fallback can never silently reappear.
        self.assertAlmostEqual(ft_for_month(2026, 1), 0.0972)

    def test_may_2026_uses_the_fifth_window(self):
        self.assertAlmostEqual(ft_for_month(2026, 5), 0.1623)

    def test_a_month_before_any_window_raises(self):
        with self.assertRaises(ValueError):
            ft_for_month(2000, 1)


class BenchmarkedSourcesTests(TestCase):
    """Inputs researched in Task 15 must not still claim to be placeholders."""

    RESEARCHED = (
        "pv_installed_cost_per_kw",
        "annual_om_per_kw",
        "debt_interest_rate",
    )

    def test_researched_financial_inputs_cite_a_source(self):
        for key in self.RESEARCHED:
            with self.subTest(key=key):
                source = FINANCIAL_DEFAULTS[key]["source"]
                self.assertNotEqual(source, PLACEHOLDER_MARKER)
                self.assertGreater(len(source), 20)

    def test_grid_emission_factor_records_its_vintage(self):
        vintage = EMISSIONS_DEFAULTS["grid_emission_factor_vintage"]["value"]
        self.assertNotEqual(vintage, "pending")
