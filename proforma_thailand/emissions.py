"""Scope 2 avoided emissions for the Thailand cases.

REopt's emissions outputs are all zero here because AVERT, Cambium and EASIUR
are US datasets with no Thailand coverage. They stay out of the workbook. This
is an Allotrope calculation from a cited Thai grid emission factor, and is
labelled as such so the two can never be confused.

The basis is avoided grid IMPORT, not PV generation. Curtailed energy displaces
nothing and must not be claimed, and any energy the battery draws from the grid
is grid energy. Avoided import is the same quantity the report already presents
as the grid offset, so the emissions figure and the offset figure cannot drift.
"""


def annual_avoided_tco2e(annual_load_kwh, annual_grid_kwh,
                         grid_emission_factor_kg_per_kwh,
                         levelization_factor=1.0):
    """Year-one avoided Scope 2 emissions in tonnes CO2e.

    ``levelization_factor`` undoes the weighting REopt applies inside the
    optimisation. Load is the customer's own and carries none, but the grid
    figure is load minus a levelized PV contribution, so their DIFFERENCE is
    levelized and must be divided back out. Without this the annual figure
    already carried degradation and lifetime_avoided_tco2e below then applied
    degradation again, understating avoided emissions by about 3.6 percent.
    """
    if not grid_emission_factor_kg_per_kwh:
        return 0.0
    avoided_kwh = max(0.0, (annual_load_kwh or 0.0) - (annual_grid_kwh or 0.0))
    if levelization_factor and levelization_factor != 1.0:
        avoided_kwh /= levelization_factor
    return avoided_kwh * grid_emission_factor_kg_per_kwh / 1000.0


def lifetime_avoided_tco2e(annual_tco2e, project_years, pv_degradation_rate):
    """Avoided emissions across the analysis period, degrading the array yearly.

    The emission factor is held constant. The Thai grid is expected to
    decarbonise under the PDP, which would reduce avoided emissions over time,
    so a constant factor is the optimistic end of the range and must be
    disclosed as an assumption.
    """
    total = 0.0
    for year in range(int(project_years or 0)):
        total += (annual_tco2e or 0.0) * (1.0 - (pv_degradation_rate or 0.0)) ** year
    return total
