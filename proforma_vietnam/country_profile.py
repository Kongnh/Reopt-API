"""Per-country display and resolution settings.

The proforma engine is country-neutral project finance; only two things vary
between markets in a way the presentation layer must know about: what the local
contract currency is called, and what the utility is called. A third setting,
the dispatch resolution, varies because PEA bills demand on a 15-minute maximum
while EVN bills hourly.

This profile deliberately does NOT rename compute keys. Money keys inside
cash_flow.py keep their historical ``_vnd`` suffix and carry the local contract
currency, which is VND for Vietnam runs and THB for Thailand runs. See
docs/superpowers/specs/2026-09-04-thailand-adaptation-design.md section 2.
"""

from dataclasses import dataclass

SUPPORTED_TIME_STEPS_PER_HOUR = (1, 2, 4)


@dataclass(frozen=True)
class CountryProfile:
    country: str
    local_currency_code: str
    utility_label: str
    time_steps_per_hour: int
    # Statutory authorities cited on the Assumptions sheet. These are country
    # law, so a Thailand workbook must not cite Vietnamese decrees at a Thai
    # client. Defaults reproduce Vietnam's existing strings byte-for-byte.
    cit_rate_source: str = "Law 67/2025/QH15; vietnam_defaults.json"
    cit_holiday_source: str = (
        "Law 67/2025 (from first profitable year); Circular 78/2014 Art. 18 shape"
    )
    cit_reduced_source: str = "Law 67/2025; Circular 78/2014 Art. 18 shape"
    cit_reduced_rate_source: str = "Law 67/2025 (50% of base rate)"
    cit_loss_source: str = "Law 67/2025; Circular 78/2014 Art. 9 shape"
    depreciation_band_source: str = "Circular 45/2013/TT-BTC (7–20 yr band)"
    depreciation_source: str = "Circular 45/2013/TT-BTC"
    depreciation_authority: str = "Circular 45/2013/TT-BTC"
    depreciation_range_text: str = "permits 7-20 years for generating equipment"
    case_label: str = "ESCO / DPPA Case"
    defaults_file: str = "vietnam_defaults.json"
    depreciation_band_phrase: str = "the 7-20y band of Circular 45/2013/TT-BTC"
    revenue_source_phrase: str = "tariff / DPPA settlement"

    def __post_init__(self):
        if self.time_steps_per_hour not in SUPPORTED_TIME_STEPS_PER_HOUR:
            raise ValueError(
                "Unsupported time_steps_per_hour {}; REopt supports {}.".format(
                    self.time_steps_per_hour, SUPPORTED_TIME_STEPS_PER_HOUR
                )
            )


VIETNAM_PROFILE = CountryProfile(
    country="Vietnam",
    local_currency_code="VND",
    utility_label="EVN",
    time_steps_per_hour=1,

)

THAILAND_PROFILE = CountryProfile(
    country="Thailand",
    local_currency_code="THB",
    utility_label="PEA",
    time_steps_per_hour=4,
    cit_rate_source="Thai Revenue Code; thailand_defaults.json",
    cit_holiday_source="Thai Revenue Code (standard flat regime, no holiday)",
    cit_reduced_source="Thai Revenue Code (standard flat regime, no reduction)",
    cit_reduced_rate_source="Thai Revenue Code (standard flat regime)",
    cit_loss_source="Thai Revenue Code (5-year loss carryforward)",
    depreciation_band_source=(
        "Thai Revenue Code, Royal Decree No. 145 (20%/yr machinery cap)"
    ),
    depreciation_source="Thai Revenue Code, Royal Decree No. 145",
    depreciation_authority="Thai Revenue Code, Royal Decree No. 145",
    depreciation_range_text=(
        "caps machinery at 20 percent per year, a 5-year life"
    ),
    case_label="DIRECT_OWNERSHIP Case",
    defaults_file="thailand_defaults.json",
    depreciation_band_phrase=(
        "the 20 percent per year machinery cap of Royal Decree No. 145"
    ),
    revenue_source_phrase="tariff",
)

DEFAULT_PROFILE = VIETNAM_PROFILE

_BY_COUNTRY = {
    profile.country.lower(): profile
    for profile in (VIETNAM_PROFILE, THAILAND_PROFILE)
}


def profile_for(country):
    key = str(country).strip().lower()
    if key not in _BY_COUNTRY:
        raise ValueError(
            "No country profile for {!r}; known: {}.".format(
                country, sorted(_BY_COUNTRY)
            )
        )
    return _BY_COUNTRY[key]
