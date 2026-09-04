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
