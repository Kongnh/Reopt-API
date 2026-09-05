from unittest import TestCase

from proforma_vietnam.country_profile import (
    DEFAULT_PROFILE,
    THAILAND_PROFILE,
    VIETNAM_PROFILE,
    CountryProfile,
    profile_for,
)


class CountryProfileTests(TestCase):

    def test_vietnam_profile_values(self):
        self.assertEqual(VIETNAM_PROFILE.country, "Vietnam")
        self.assertEqual(VIETNAM_PROFILE.local_currency_code, "VND")
        self.assertEqual(VIETNAM_PROFILE.utility_label, "EVN")
        self.assertEqual(VIETNAM_PROFILE.time_steps_per_hour, 1)

    def test_thailand_profile_values(self):
        self.assertEqual(THAILAND_PROFILE.country, "Thailand")
        self.assertEqual(THAILAND_PROFILE.local_currency_code, "THB")
        self.assertEqual(THAILAND_PROFILE.utility_label, "PEA")
        self.assertEqual(THAILAND_PROFILE.time_steps_per_hour, 4)

    def test_default_profile_is_vietnam(self):
        self.assertIs(DEFAULT_PROFILE, VIETNAM_PROFILE)

    def test_profile_for_is_case_insensitive(self):
        self.assertIs(profile_for("thailand"), THAILAND_PROFILE)
        self.assertIs(profile_for("VIETNAM"), VIETNAM_PROFILE)

    def test_profile_for_rejects_unknown_country(self):
        with self.assertRaises(ValueError) as caught:
            profile_for("Malaysia")
        self.assertIn("Malaysia", str(caught.exception))

    def test_profile_is_frozen(self):
        with self.assertRaises(Exception):
            VIETNAM_PROFILE.local_currency_code = "USD"

    def test_time_steps_per_hour_must_be_supported(self):
        with self.assertRaises(ValueError):
            CountryProfile(
                country="Nowhere",
                local_currency_code="XXX",
                utility_label="XX",
                time_steps_per_hour=3,
            )


class DirectOwnershipPresentationTests(TestCase):

    def test_vietnam_keeps_the_esco_presentation(self):
        self.assertTrue(VIETNAM_PROFILE.shows_esco_contract_terms)
        self.assertEqual(
            VIETNAM_PROFILE.returns_section_label, "Developer (Seller) Returns"
        )
        self.assertEqual(VIETNAM_PROFILE.dispatch_row_label, "Hour")

    def test_thailand_presents_as_direct_ownership(self):
        self.assertFalse(THAILAND_PROFILE.shows_esco_contract_terms)
        self.assertEqual(THAILAND_PROFILE.returns_section_label, "Owner Returns")
        self.assertEqual(THAILAND_PROFILE.dispatch_row_label, "Interval")
