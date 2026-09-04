from unittest import TestCase

from proforma_thailand.defaults import (
    FINANCIAL_DEFAULTS,
    PLACEHOLDER_MARKER,
    SITE_DEFAULTS,
    TAX_DEFAULTS,
    TAX_DEFAULTS_RAW,
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
            "pv_installed_cost_per_kw",
            "bess_installed_cost_per_kw",
            "bess_installed_cost_per_kwh",
            "annual_om_per_kw",
            "debt_fraction",
            "debt_interest_rate",
            "debt_term_years",
            "discount_rate",
            "insurance_rate_fraction",
            "grid_connection_cost",
            "permitting_and_eia_cost",
            "pea_tariff_escalation_rate",
            "ft_forecast_per_kwh",
            "usable_roof_area_m2",
            "pv_max_kw",
            "power_factor_mitigation_cost",
        }

        self.assertEqual(placeholder_keys(), expected)

    def test_placeholder_entries_carry_the_marker_string(self):
        for key in placeholder_keys():
            for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW):
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
            for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW):
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
