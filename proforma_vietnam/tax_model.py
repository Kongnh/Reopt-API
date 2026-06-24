from proforma_vietnam.defaults import TAX_DEFAULTS

# Values sourced from defaults/vietnam_defaults.json (versioned); regulatory
# provenance kept inline below.
CIT_STANDARD_RATE = TAX_DEFAULTS["cit_standard_rate"]
CIT_HOLIDAY_YEARS = TAX_DEFAULTS["cit_holiday_years"]
CIT_REDUCED_RATE_YEARS = TAX_DEFAULTS["cit_reduced_rate_years"]
CIT_REDUCED_RATE_FRACTION = TAX_DEFAULTS["cit_reduced_rate_fraction"]
# Vietnam CIT law: losses may be carried forward for at most 5 consecutive
# years following the loss year (Circular 78/2014 Art. 9).
CIT_LOSS_CARRYFORWARD_YEARS = TAX_DEFAULTS["cit_loss_carryforward_years"]
# Circular 78/2014 Art. 18: the exemption/reduction period counts from the
# first year with taxable income; if there is none within the first 3 years,
# the clock starts in year 4 (index 3).
CIT_INCENTIVE_START_CAP_INDEX = TAX_DEFAULTS["cit_incentive_start_cap_index"]
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
):
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

        if index < clock_start + holiday_years:
            rate = 0
        elif index < clock_start + holiday_years + reduced_rate_years:
            rate = standard_rate * reduced_rate_fraction
        else:
            rate = standard_rate

        cit_by_year.append(taxable_base * rate)

    return cit_by_year


def straight_line_depreciation_schedule(capex, depreciation_years, project_years=25):
    annual_depreciation = capex / depreciation_years

    return [
        annual_depreciation if year < depreciation_years else 0
        for year in range(project_years)
    ]
