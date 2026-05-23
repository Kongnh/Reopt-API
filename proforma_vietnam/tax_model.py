CIT_STANDARD_RATE = 0.20
CIT_HOLIDAY_YEARS = 4
CIT_REDUCED_RATE_YEARS = 9
CIT_REDUCED_RATE_FRACTION = 0.50
PV_DEPRECIATION_YEARS = 20
BESS_DEPRECIATION_YEARS = 8


def calculate_cit(
    taxable_income_by_year,
    standard_rate=CIT_STANDARD_RATE,
    holiday_years=CIT_HOLIDAY_YEARS,
    reduced_rate_years=CIT_REDUCED_RATE_YEARS,
    reduced_rate_fraction=CIT_REDUCED_RATE_FRACTION,
):
    cit_by_year = []

    for index, taxable_income in enumerate(taxable_income_by_year):
        taxable_income = max(taxable_income, 0)

        if index < holiday_years:
            rate = 0
        elif index < holiday_years + reduced_rate_years:
            rate = standard_rate * reduced_rate_fraction
        else:
            rate = standard_rate

        cit_by_year.append(taxable_income * rate)

    return cit_by_year


def straight_line_depreciation_schedule(capex, depreciation_years, project_years=25):
    annual_depreciation = capex / depreciation_years

    return [
        annual_depreciation if year < depreciation_years else 0
        for year in range(project_years)
    ]
