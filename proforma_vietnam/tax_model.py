from proforma_vietnam.defaults import TAX_DEFAULTS

# Values sourced from defaults/vietnam_defaults.json (versioned); regulatory
# provenance kept inline below. CIT regime schedules follow Law 67/2025/QH15
# (effective 2025-10-01, from tax year 2025) + Decree 320/2025/NĐ-CP, which
# supersede the Circular 78/2014 framework for new projects. The
# ``standard_with_holiday`` regime reproduces the legacy Circular 78/2014 shape
# and stays the conservative default for service ESCOs (grandfathered projects
# also keep old-law incentives).
CIT_STANDARD_RATE = TAX_DEFAULTS["cit_standard_rate"]
# Law 67/2025: renewable-energy producers get a 10% preferential base rate for
# the first 15 years counted from the first revenue-generating year, then the
# standard rate. Applied only under the ``re_producer`` regime.
CIT_PREFERENTIAL_RATE = TAX_DEFAULTS["cit_preferential_rate"]
CIT_PREFERENTIAL_RATE_YEARS = TAX_DEFAULTS["cit_preferential_rate_years"]
CIT_HOLIDAY_YEARS = TAX_DEFAULTS["cit_holiday_years"]
CIT_REDUCED_RATE_YEARS = TAX_DEFAULTS["cit_reduced_rate_years"]
# The reduction applies 50% of the then-applicable base rate (standard, or the
# preferential rate while its window is active).
CIT_REDUCED_RATE_FRACTION = TAX_DEFAULTS["cit_reduced_rate_fraction"]
# Vietnam CIT law: losses may be carried forward for at most 5 consecutive
# years following the loss year (Law 67/2025; Circular 78/2014 Art. 9 shape).
CIT_LOSS_CARRYFORWARD_YEARS = TAX_DEFAULTS["cit_loss_carryforward_years"]
# The exemption/reduction period counts from the first year with taxable
# income; if there is none within the first 3 years, the clock starts in year 4
# (index 3). (Law 67/2025; Circular 78/2014 Art. 18 shape.)
CIT_INCENTIVE_START_CAP_INDEX = TAX_DEFAULTS["cit_incentive_start_cap_index"]

# CIT regimes. The regime is structure/case-dependent (not a JSON default):
# ``standard_with_holiday`` is the conservative ESCO default (legacy shape);
# ``re_producer`` is the Law 67/2025 renewable-energy producer incentive.
CIT_REGIME_STANDARD_WITH_HOLIDAY = "standard_with_holiday"
CIT_REGIME_RE_PRODUCER = "re_producer"
CIT_REGIMES = (CIT_REGIME_STANDARD_WITH_HOLIDAY, CIT_REGIME_RE_PRODUCER)
# Circular 45/2013/TT-BTC: power generating equipment may be depreciated
# straight-line over 7-20 years; 20 is this model's explicit default.
PV_DEPRECIATION_YEARS = TAX_DEFAULTS["pv_depreciation_years"]
PV_DEPRECIATION_YEARS_MIN = TAX_DEFAULTS["pv_depreciation_years_min"]
PV_DEPRECIATION_YEARS_MAX = TAX_DEFAULTS["pv_depreciation_years_max"]
BESS_DEPRECIATION_YEARS = TAX_DEFAULTS["bess_depreciation_years"]


def validate_pv_depreciation_years(years):
    if not PV_DEPRECIATION_YEARS_MIN <= years <= PV_DEPRECIATION_YEARS_MAX:
        raise ValueError(
            "pv_depreciation_years must be within "
            f"{PV_DEPRECIATION_YEARS_MIN}-{PV_DEPRECIATION_YEARS_MAX} years "
            f"per Circular 45/2013/TT-BTC, got {years}."
        )
    return years


def calculate_cit(
    taxable_income_by_year,
    standard_rate=CIT_STANDARD_RATE,
    holiday_years=CIT_HOLIDAY_YEARS,
    reduced_rate_years=CIT_REDUCED_RATE_YEARS,
    reduced_rate_fraction=CIT_REDUCED_RATE_FRACTION,
    loss_carryforward_years=CIT_LOSS_CARRYFORWARD_YEARS,
    preferential_rate=None,
    preferential_years=None,
):
    """CIT schedule with a first-profit exemption/reduction holiday.

    When ``preferential_rate``/``preferential_years`` are given (the Law 67/2025
    ``re_producer`` regime), the applicable base rate is the preferential rate
    for the first ``preferential_years`` years (counted from year 1) and the
    standard rate afterwards; the 50% reduction multiplies whichever base rate
    applies that year. Left unset, the base rate is always ``standard_rate`` —
    the legacy ``standard_with_holiday`` behaviour, bit-for-bit.
    """
    clock_start = next(
        (
            index
            for index, income in enumerate(taxable_income_by_year)
            if income > 0
        ),
        CIT_INCENTIVE_START_CAP_INDEX,
    )
    clock_start = min(clock_start, CIT_INCENTIVE_START_CAP_INDEX)

    cit_by_year = []
    carried_losses = []  # [loss_year_index, remaining_loss]

    for index, taxable_income in enumerate(taxable_income_by_year):
        if taxable_income < 0:
            carried_losses.append([index, -taxable_income])
            cit_by_year.append(0.0)
            continue

        taxable_base = taxable_income
        for entry in carried_losses:
            if entry[1] <= 0 or index - entry[0] > loss_carryforward_years:
                continue
            offset = min(entry[1], taxable_base)
            entry[1] -= offset
            taxable_base -= offset
            if taxable_base <= 0:
                break

        if preferential_rate is not None and index < preferential_years:
            base_rate = preferential_rate
        else:
            base_rate = standard_rate

        if index < clock_start + holiday_years:
            rate = 0
        elif index < clock_start + holiday_years + reduced_rate_years:
            rate = base_rate * reduced_rate_fraction
        else:
            rate = base_rate

        cit_by_year.append(taxable_base * rate)

    return cit_by_year


def straight_line_depreciation_schedule(capex, depreciation_years, project_years=25):
    annual_depreciation = capex / depreciation_years

    return [
        annual_depreciation if year < depreciation_years else 0
        for year in range(project_years)
    ]
