"""Audit-grade workbook sheets: live Excel formulas + engine tie-out.

These sheets make the Vietnam proforma workbook self-auditable for a
third-party (investor, lender, or model auditor):

- ``Cover``            — contents, conventions, colour legend, overall status.
- ``Assumptions``      — every input grouped, with unit + source, as *named
                         cells* so the formula sheets read like the design doc.
- ``Model Basis``      — methodology, settlement math, simplifications register.
- ``Pro Forma (Audit)``— the full multi-year cash flow rebuilt with live Excel
                         formulas (SAM cash-flow convention: line items down,
                         years across). Only engine outputs that cannot be
                         derived in-sheet (year-1 dispatch/settlement bases,
                         the replacement schedule, tie-out rows) are hardcoded
                         and shaded as inputs. A Checks block compares every
                         Excel-computed metric against the Python engine and
                         shows PASS/REVIEW.
- ``FX Sensitivity``   — USD-reported equity returns under annual VND
                         depreciation, live formulas over the audit sheet.

The Excel formulas replicate ``cash_flow.py`` (and ``tax_model.py``) exactly —
including the CIT holiday clock and the FIFO 5-year tax-loss carryforward —
so an auditor can trace every published figure from named inputs to the
metric without leaving Excel.
"""

from datetime import date

from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

from proforma_vietnam.cash_flow import calculate_fx_sensitivity
from proforma_vietnam.structures import DPPA

NAVY = "1F3864"
ACCENT = "2E74B5"
INPUT_COLOR = "FFF2CC"   # hardcoded engine outputs / user inputs
CHECK_COLOR = "E2EFDA"   # tie-out block

TITLE_FILL = PatternFill("solid", fgColor=NAVY)
TITLE_FONT = Font(bold=True, color="FFFFFF", size=13)
SECTION_FILL = PatternFill("solid", fgColor=ACCENT)
SECTION_FONT = Font(bold=True, color="FFFFFF", size=10)
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
HEADER_FONT = Font(bold=True, color="FFFFFF")
INPUT_FILL = PatternFill("solid", fgColor=INPUT_COLOR)
CHECK_FILL = PatternFill("solid", fgColor=CHECK_COLOR)
NOTE_FONT = Font(italic=True, size=9, color="595959")
BOLD_FONT = Font(bold=True)

FMT_AMOUNT = "#,##0"
FMT_AMOUNT_2 = "#,##0.00"
FMT_PERCENT = "0.00%"
FMT_RATIO = "0.00"
FMT_FACTOR = "0.0000"
FMT_YEARS = "0.0"

PRO_FORMA_SHEET = "Pro Forma (Audit)"

# assumptions.json keys already rendered in a curated Assumptions section; the
# remainder is echoed raw at the bottom of the sheet so the file is complete.
CURATED_ASSUMPTION_KEYS = {
    "case_name", "run_uuid", "country", "tariff_year", "voltage_level",
    "tou_schedule", "exchange_rate_vnd_per_usd", "evn_energy_escalation_rate",
    "evn_capacity_escalation_rate", "esco_energy_discount_fraction",
    "demand_savings_esco_share", "grid_charging_enabled",
    "battery_replacement_year", "annual_om_usd", "pv_capex_usd",
    "bess_capex_usd", "om_escalation_rate", "pv_degradation_rate",
    "pv_depreciation_years", "debt_fraction", "debt_interest_rate_fraction",
    "debt_term_years", "owner_discount_rate_fraction", "analysis_years",
    "case_config", "dppa",
}

STORAGE_CASE_ROWS = [
    ("Storage minimum power", "min_kw", "kW"),
    ("Storage maximum power", "max_kw", "kW"),
    ("Storage minimum energy", "min_kwh", "kWh"),
    ("Storage maximum energy", "max_kwh", "kWh"),
    ("Storage cost per kW", "installed_cost_per_kw", "USD/kW"),
    ("Storage cost per kWh", "installed_cost_per_kwh", "USD/kWh"),
    ("Storage fixed cost", "installed_cost_constant", "USD"),
    ("Replacement cost per kW", "replace_cost_per_kw", "USD/kW"),
    ("Replacement cost per kWh", "replace_cost_per_kwh", "USD/kWh"),
    ("Replacement fixed cost", "replace_cost_constant", "USD"),
    ("Inverter replacement year", "inverter_replacement_year", "year"),
    ("Battery replacement year", "battery_replacement_year", "year"),
    ("Fixed-cost replacement year", "cost_constant_replacement_year", "year"),
    ("O&M (fraction of installed cost)", "om_cost_fraction_of_installed_cost", "per year"),
    ("Can charge from grid", "can_grid_charge", "yes/no"),
]

# Absolute tolerances for the tie-out checks. Excel and the engine execute the
# same double-precision arithmetic, so real deltas are ~1e-9; the tolerances
# only absorb IRR root-finding differences and display rounding.
TOL_AMOUNT = 1.0        # USD
TOL_RATE = 0.0005       # 5 bp on IRR / percent metrics
TOL_RATIO = 0.005       # DSCR
TOL_YEARS = 0.05        # payback


def _fmt_num(value):
    """Render a float for embedding inside an Excel formula string."""
    return repr(float(value))


def _define_name(workbook, name, sheet_title, cell):
    workbook.defined_names[name] = DefinedName(
        name, attr_text=f"'{sheet_title}'!${cell[0]}${cell[1]}"
    )


# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------

def write_assumptions_sheet(worksheet, workbook, assumptions, derivation):
    """Grouped assumptions with units, sources and workbook-scope named cells.

    Returns True when the engine derivation block was available (i.e. the
    formula sheets can be built on top of these names).
    """
    derivation = derivation or {}
    dppa = assumptions.get("dppa") if assumptions else None
    is_dppa = derivation.get("structure") == DPPA or bool(
        dppa and dppa.get("type", "none") != "none"
    )

    worksheet.sheet_view.showGridLines = False
    worksheet.merge_cells("B1:E1")
    title = worksheet.cell(row=1, column=2, value="Assumptions & Model Inputs")
    title.fill = TITLE_FILL
    title.font = TITLE_FONT
    worksheet.row_dimensions[1].height = 24
    worksheet.cell(
        row=2, column=2,
        value="Shaded cells are hardcoded inputs (case file or engine output); "
              "named cells drive every formula on the Pro Forma (Audit) sheet.",
    ).font = NOTE_FONT

    state = {"row": 4}

    def section(label):
        row = state["row"]
        for column in range(2, 6):
            worksheet.cell(row=row, column=column).fill = SECTION_FILL
        cell = worksheet.cell(row=row, column=2, value=label)
        cell.font = SECTION_FONT
        state["row"] = row + 1

    def entry(label, value, unit="", source="", name=None, fmt=None, formula=None):
        row = state["row"]
        worksheet.cell(row=row, column=2, value=label)
        value_cell = worksheet.cell(row=row, column=3)
        if formula is not None:
            value_cell.value = formula
        else:
            value_cell.value = value
            value_cell.fill = INPUT_FILL
        if fmt:
            value_cell.number_format = fmt
        # Never write empty strings: openpyxl serialises them as an inlineStr
        # cell with no <is> child, which Excel rejects as a corrupt workbook.
        if unit:
            worksheet.cell(row=row, column=4, value=unit).font = NOTE_FONT
        if source:
            worksheet.cell(row=row, column=5, value=source).font = NOTE_FONT
        if name:
            _define_name(workbook, name, worksheet.title, ("C", row))
        state["row"] = row + 1

    d = derivation

    def get(key, alt=None):
        """Engine derivation is authoritative; fall back to the case assumptions."""
        value = d.get(key)
        if value is not None:
            return value
        return assumptions.get(alt or key)

    section("Project & Run")
    entry("Case name", assumptions.get("case_name", "Vietnam case"), source="case.json")
    entry("Financing structure",
          "Grid DPPA with CfD (ND57/2025)" if is_dppa else "ESCO discount-to-EVN (behind-the-meter)",
          source="proforma_vietnam.structures")
    if assumptions.get("run_uuid"):
        entry("REopt run UUID", assumptions["run_uuid"], source="REopt API")
    entry("Report prepared", date.today().isoformat())
    entry("Analysis period", d.get("project_years", assumptions.get("analysis_years", 25)),
          unit="years", source="case.json financial.analysis_years",
          name="PROJECT_YEARS", fmt="0")
    if assumptions.get("tariff_year"):
        entry("Tariff year", assumptions.get("tariff_year"), source="case.json tariff.year", fmt="0")
    if assumptions.get("voltage_level"):
        entry("Voltage level", str(assumptions.get("voltage_level")), source="case.json tariff.voltage_level")
    if assumptions.get("tou_schedule"):
        entry("TOU schedule", assumptions.get("tou_schedule"), source="case.json tariff.tou_schedule")

    case_config = assumptions.get("case_config") or {}
    _write_case_definition_sections(section, entry, case_config)

    section("Currency & FX")
    entry("Model currency", "USD",
          source="EVN tariff converted VND→USD before REopt; see Model Basis")
    entry("Contract exchange rate",
          d.get("exchange_rate_vnd_per_usd") or assumptions.get("exchange_rate_vnd_per_usd"),
          unit="VND per USD", source="case.json tariff.exchange_rate_vnd_per_usd",
          name="FX_VND_PER_USD", fmt=FMT_AMOUNT)
    entry("FX treatment", "Held flat over the analysis period",
          source="Simplification — see FX Sensitivity sheet")

    section("Capital Costs")
    entry("PV capex", get("pv_capex_usd"), unit="USD",
          source="REopt PV size_kw × installed_cost_per_kw",
          name="PV_CAPEX", fmt=FMT_AMOUNT)
    entry("BESS capex", get("bess_capex_usd"), unit="USD",
          source="REopt ElectricStorage initial_capital_cost",
          name="BESS_CAPEX", fmt=FMT_AMOUNT)
    entry("Other capex", d.get("other_capex_usd", 0), unit="USD",
          source="case.json (developer overrides)",
          name="OTHER_CAPEX", fmt=FMT_AMOUNT)
    entry("Total investment", None, unit="USD", source="Formula: PV + BESS + Other",
          name="TOTAL_CAPEX", fmt=FMT_AMOUNT,
          formula="=PV_CAPEX+BESS_CAPEX+OTHER_CAPEX")

    section("Operating Costs")
    entry("Year-1 O&M", get("annual_om_year1_usd", "annual_om_usd"), unit="USD/yr",
          source="REopt Financial.year_one_om_costs_before_tax",
          name="OM_YEAR1", fmt=FMT_AMOUNT)
    entry("O&M escalation", get("om_escalation_rate") or 0.0, unit="per year",
          source="case.json financial.om_escalation_rate",
          name="ESC_OM", fmt=FMT_PERCENT)
    if assumptions.get("battery_replacement_year"):
        entry("Battery replacement year", assumptions["battery_replacement_year"],
              unit="year", source="case.json technologies.storage.battery_replacement_year",
              fmt="0")

    section("Tariff & Escalation")
    entry("EVN energy escalation", get("evn_energy_escalation_rate"), unit="per year",
          source="case.json tariff.evn_energy_escalation_rate",
          name="ESC_ENERGY", fmt=FMT_PERCENT)
    entry("EVN capacity (demand) escalation", get("evn_capacity_escalation_rate"),
          unit="per year", source="case.json tariff.evn_capacity_escalation_rate",
          name="ESC_CAPACITY", fmt=FMT_PERCENT)
    entry("PV degradation", get("pv_degradation_rate") or 0.0, unit="per year",
          source="REopt PV.degradation_fraction",
          name="PV_DEGRADATION", fmt=FMT_PERCENT)
    tariff_config = case_config.get("tariff") or {}
    if tariff_config.get("currency"):
        entry("Tariff currency fed to REopt", str(tariff_config["currency"]).upper(),
              source="case.json tariff.currency")
    if tariff_config.get("two_component_pilot_enabled") is not None:
        entry("Two-component tariff pilot", tariff_config["two_component_pilot_enabled"],
              unit="yes/no", source="case.json tariff.two_component_pilot_enabled")

    section("Contract Terms")
    entry("ESCO energy price (fraction of EVN tariff)",
          get("esco_energy_discount_fraction"), unit="fraction",
          source="case.json esco_contract.esco_energy_discount_fraction",
          name="ESCO_DISCOUNT", fmt=FMT_PERCENT)
    entry("Demand savings share to ESCO",
          get("esco_demand_savings_share", "demand_savings_esco_share"),
          unit="fraction", source="case.json esco_contract.demand_savings_esco_share",
          name="DEMAND_SHARE", fmt=FMT_PERCENT)
    if assumptions.get("grid_charging_enabled") is not None:
        entry("Grid charging enabled", assumptions["grid_charging_enabled"],
              unit="yes/no", source="case.json esco_contract.grid_charging_enabled")
    if is_dppa and dppa:
        volume = dppa.get("cfd_contract_volume_kwh_per_hour")
        annual_volume = sum(volume) if isinstance(volume, list) else (volume or 0.0) * 8760
        entry("CfD strike price", dppa.get("cfd_strike_per_kwh_vnd"), unit="VND/kWh",
              source="case.json dppa.cfd_strike_per_kwh_vnd", fmt=FMT_AMOUNT)
        entry("CfD strike escalation",
              (d.get("dppa_escalation") or {}).get("cfd_strike_escalation_rate", 0.0),
              unit="per year", source="case.json dppa.cfd_strike_escalation_rate",
              name="ESC_STRIKE", fmt=FMT_PERCENT)
        entry("DPPA fee / FMP escalation",
              (d.get("dppa_escalation") or {}).get("fee_escalation_rate", 0.0),
              unit="per year", source="case.json dppa.fee_escalation_rate",
              name="ESC_FEE", fmt=FMT_PERCENT)
        entry("Annual CfD contract volume", annual_volume, unit="kWh/yr",
              source="case.json dppa.cfd_contract_volume_kwh_per_hour", fmt=FMT_AMOUNT)
        entry("Transmission loss factor k (price-only)",
              dppa.get("transmission_loss_factor_k"), unit="ratio",
              source="ND57; CFMP = FMP × k", fmt=FMT_FACTOR)
        entry("Distribution loss factor K_pp", dppa.get("distribution_loss_factor_kpp"),
              unit="ratio", source="ND57 by voltage; Q_adj = Q_meter / K_pp",
              fmt="0.000000")
        entry("DPPA system service fee", dppa.get("c_dppa_service_fee_vnd_per_kwh"),
              unit="VND/kWh", source="2025 EVN published fee", fmt=FMT_AMOUNT_2)
        entry("Settlement adder C_CL", dppa.get("c_cl_settlement_adder_vnd_per_kwh"),
              unit="VND/kWh", source="2025 EVN published adder", fmt=FMT_AMOUNT_2)
        entry("Allocation fraction δ", dppa.get("allocation_fraction_delta"),
              unit="fraction", source="case.json dppa.allocation_fraction_delta",
              fmt=FMT_RATIO)
        if dppa.get("fmp_series_path"):
            entry("FMP / CFMP price series", dppa.get("fmp_series_path"),
                  source="case.json dppa.fmp_series_path (8760-hour VND/kWh)")

    surplus = d.get("surplus_export")
    if surplus:
        # Decree 243/2026 rooftop surplus-export (ESCO only). Gated on the engine
        # derivation so disabled cases carry no surplus names or rows.
        section("Surplus Export (Decree 243/2026)")
        entry("Year-1 surplus sold to EVN", surplus.get("sold_kwh_year1"),
              unit="kWh/yr",
              source="min(PV grid export + curtailed, cap × PV output)",
              name="SURPLUS_KWH_Y1", fmt=FMT_AMOUNT)
        entry("Surplus export price", surplus.get("price_usd_per_kwh"),
              unit="USD/kWh",
              source="Decree 243 market price, capped at Decision 988 regional "
                     "ceiling, at contract FX",
              name="SURPLUS_PRICE", fmt="#,##0.00000")
        entry("Surplus price escalation", surplus.get("price_escalation_rate"),
              unit="per year",
              source="case.json surplus_export.price_escalation_rate "
                     "(default: EVN energy escalation)",
              name="SURPLUS_ESC", fmt=FMT_PERCENT)
        entry("Surplus export cap", surplus.get("cap_fraction"),
              unit="of PV output",
              source="Decree 243/2026 (50%; >50% negotiable to 2030)",
              name="SURPLUS_CAP", fmt=FMT_PERCENT)

    section("Financing")
    entry("Debt fraction", get("debt_fraction"), unit="of total capex",
          source="vietnam_defaults.json / case.json financial.debt_fraction",
          name="DEBT_FRACTION", fmt=FMT_PERCENT)
    entry("Debt interest rate", get("debt_interest_rate_fraction"), unit="per year",
          source="vietnam_defaults.json / case.json financial.debt_interest_rate_fraction",
          name="DEBT_RATE", fmt=FMT_PERCENT)
    entry("Debt term", get("debt_term_years"), unit="years",
          source="vietnam_defaults.json / case.json financial.debt_term_years",
          name="DEBT_TERM_YEARS", fmt="0")
    entry("Debt principal", None, unit="USD", source="Formula: total investment × debt fraction",
          name="DEBT_PRINCIPAL", fmt=FMT_AMOUNT,
          formula="=TOTAL_CAPEX*DEBT_FRACTION")
    entry("Equity investment", None, unit="USD", source="Formula: total investment − debt",
          name="EQUITY_INVESTMENT", fmt=FMT_AMOUNT,
          formula="=TOTAL_CAPEX-DEBT_PRINCIPAL")
    entry("Annual debt payment (level)", None, unit="USD/yr",
          source="Standard annuity over the debt term",
          name="DEBT_PAYMENT", fmt=FMT_AMOUNT,
          formula=(
              "=IF(OR(DEBT_PRINCIPAL<=0,DEBT_TERM_YEARS<=0),0,"
              "IF(DEBT_RATE=0,DEBT_PRINCIPAL/DEBT_TERM_YEARS,"
              "DEBT_PRINCIPAL*(DEBT_RATE*(1+DEBT_RATE)^DEBT_TERM_YEARS)"
              "/((1+DEBT_RATE)^DEBT_TERM_YEARS-1)))"
          ))
    entry("Owner discount rate", get("owner_discount_rate_fraction"), unit="per year",
          source="case.json financial.owner_discount_rate_fraction",
          name="DISC_RATE", fmt=FMT_PERCENT)

    section("Tax & Depreciation (Vietnam)")
    cit = d.get("cit", {})
    regime_label = {
        "re_producer": "RE producer — Law 67/2025 preferential (10% / 15y)",
        "standard_with_holiday": "Standard + holiday (conservative ESCO default)",
    }.get(cit.get("regime"), "Standard + holiday (conservative ESCO default)")
    entry("CIT regime", regime_label,
          source="proforma_vietnam.cash_flow (structure-dependent; explicit override wins)")
    entry("CIT standard rate", cit.get("standard_rate"), unit="of taxable income",
          source="Law 67/2025/QH15; vietnam_defaults.json",
          name="CIT_RATE", fmt=FMT_PERCENT)
    if cit.get("preferential_rate") is not None:
        entry("CIT preferential rate (RE producer)", cit.get("preferential_rate"),
              unit="of taxable income",
              source="Law 67/2025/QH15 + Decree 320/2025/NĐ-CP (first-15-year window)",
              name="CIT_PREF_RATE", fmt=FMT_PERCENT)
        entry("CIT preferential-rate period", cit.get("preferential_years"),
              unit="years (from year 1)", source="Law 67/2025/QH15",
              name="CIT_PREF_YEARS", fmt="0")
    entry("CIT holiday", cit.get("holiday_years"), unit="years",
          source="Law 67/2025 (from first profitable year); Circular 78/2014 Art. 18 shape",
          name="CIT_HOLIDAY_YEARS", fmt="0")
    entry("CIT reduced-rate period", cit.get("reduced_rate_years"), unit="years",
          source="Law 67/2025; Circular 78/2014 Art. 18 shape",
          name="CIT_REDUCED_YEARS", fmt="0")
    entry("CIT reduction during period", cit.get("reduced_rate_fraction"),
          unit="of applicable base rate", source="Law 67/2025 (50% of base rate)",
          name="CIT_REDUCED_FRACTION", fmt=FMT_PERCENT)
    entry("Tax-loss carryforward limit", cit.get("loss_carryforward_years"),
          unit="years", source="Law 67/2025; Circular 78/2014 Art. 9 shape",
          name="CIT_LOSS_CF_YEARS", fmt="0")
    entry("Incentive clock cap", (cit.get("incentive_start_cap_index") or 3) + 1,
          unit="year (latest start)", source="Law 67/2025; Circular 78/2014 Art. 18 shape",
          name="CIT_CLOCK_CAP_YEAR", fmt="0")
    entry("PV depreciation (straight-line)", d.get("pv_depreciation_years"),
          unit="years", source="Circular 45/2013/TT-BTC (7–20 yr band)",
          name="PV_DEP_YEARS", fmt="0")
    entry("BESS depreciation (straight-line)", d.get("bess_depreciation_years"),
          unit="years", source="Circular 45/2013/TT-BTC",
          name="BESS_DEP_YEARS", fmt="0")

    section("Year-1 Engine Outputs (hardcoded — dispatch × tariff, not derivable in-sheet)")
    entry("Year-1 BAU EVN bill", d.get("bau_evn_bill_year1_usd"), unit="USD",
          source="REopt ElectricTariff.year_one_bill_before_tax_bau",
          name="BAU_BILL_Y1", fmt=FMT_AMOUNT)
    entry("Year-1 optimized EVN bill", d.get("optimized_evn_bill_year1_usd"), unit="USD",
          source="REopt ElectricTariff.year_one_bill_before_tax",
          name="OPT_BILL_Y1", fmt=FMT_AMOUNT)
    entry("Year-1 BAU demand charge", d.get("bau_demand_charge_year1_usd"), unit="USD",
          source="REopt year_one_demand_cost_before_tax_bau",
          name="BAU_DEMAND_Y1", fmt=FMT_AMOUNT)
    entry("Year-1 optimized demand charge", d.get("optimized_demand_charge_year1_usd"),
          unit="USD", source="REopt year_one_demand_cost_before_tax",
          name="OPT_DEMAND_Y1", fmt=FMT_AMOUNT)
    entry("Year-1 demand savings base", d.get("base_demand_savings_usd"), unit="USD",
          source="max(BAU − optimized demand charge, 0)",
          name="BASE_DEMAND_SAVINGS", fmt=FMT_AMOUNT)
    entry("Year-1 served-energy retail value", d.get("base_served_retail_value_usd"),
          unit="USD", source="Σ project-served kWh × EVN TOU rate (8760 h)",
          name="BASE_SERVED_RETAIL", fmt=FMT_AMOUNT)
    if is_dppa:
        dp = d.get("dppa_year_one_usd", {})
        entry("Year-1 C_DN (spot energy)", dp.get("c_dn"), unit="USD",
              source="settle_dppa_year_one: Σ Q_Khc × CFMP × K_pp",
              name="DPPA_C_DN_Y1", fmt=FMT_AMOUNT)
        entry("Year-1 C_DPPA (system fee)", dp.get("c_dppa"), unit="USD",
              source="Σ Q_Khc × f_dppa", name="DPPA_C_DPPA_Y1", fmt=FMT_AMOUNT)
        entry("Year-1 C_CL (settlement adder)", dp.get("c_cl"), unit="USD",
              source="Σ Q_Khc × f_cl", name="DPPA_C_CL_Y1", fmt=FMT_AMOUNT)
        entry("Year-1 C_BL (retail shortfall)", dp.get("c_bl"), unit="USD",
              source="Σ shortfall × EVN TOU rate", name="DPPA_C_BL_Y1", fmt=FMT_AMOUNT)
        entry("Year-1 CfD strike leg", dp.get("cfd_strike_revenue"), unit="USD",
              source="Σ P_c × min(Q_c, Q_Khc)", name="DPPA_CFD_STRIKE_Y1", fmt=FMT_AMOUNT)
        entry("Year-1 CfD market offset", dp.get("cfd_fmp_offset"), unit="USD",
              source="Σ FMP × min(Q_c, Q_Khc)", name="DPPA_CFD_OFFSET_Y1", fmt=FMT_AMOUNT)
        entry("Year-1 generator FMP revenue", dp.get("generator_fmp_revenue"), unit="USD",
              source="Σ Q_re_meter × FMP", name="DPPA_FMP_REV_Y1", fmt=FMT_AMOUNT)
        entry("Year-1 matched-energy retail value", dp.get("matched_retail_value"),
              unit="USD", source="Σ Q_Khc × EVN TOU rate (degradation repurchase)",
              name="DPPA_MATCHED_RETAIL_Y1", fmt=FMT_AMOUNT)
    else:
        entry("Year-1 ESCO energy revenue base", d.get("base_energy_revenue_usd"),
              unit="USD", source="Σ served kWh × EVN TOU rate × ESCO discount",
              name="BASE_ENERGY_REV", fmt=FMT_AMOUNT)
        entry("Year-1 grid arbitrage base", d.get("base_grid_arbitrage_revenue_usd", 0),
              unit="USD", source="REopt net grid arbitrage × ESCO share",
              name="BASE_GRID_ARB", fmt=FMT_AMOUNT)

    # Completeness guarantee: any assumptions.json scalar not already shown in
    # a curated group above is echoed raw here, so nothing is silently dropped.
    leftover = {
        key: value
        for key, value in (assumptions or {}).items()
        if key not in CURATED_ASSUMPTION_KEYS
        and not isinstance(value, (dict, list))
        and value is not None
    }
    if leftover:
        section("Other Assumptions (assumptions.json echo)")
        for key in sorted(leftover):
            entry(key, leftover[key], source="assumptions.json")

    worksheet.column_dimensions["A"].width = 2
    worksheet.column_dimensions["B"].width = 44
    worksheet.column_dimensions["C"].width = 16
    worksheet.column_dimensions["D"].width = 16
    worksheet.column_dimensions["E"].width = 52
    worksheet.freeze_panes = "A4"
    return bool(derivation)


def _write_case_definition_sections(section, entry, case_config):
    """Site, load-profile, PV and storage definitions straight from case.json."""
    if not case_config:
        return
    site = case_config.get("site") or {}
    load_profile = case_config.get("load_profile") or {}
    if site or load_profile:
        section("Site & Load Profile (case.json)")
        entry("Latitude", site.get("latitude"), unit="deg",
              source="case.json site.latitude", fmt="0.0000")
        entry("Longitude", site.get("longitude"), unit="deg",
              source="case.json site.longitude", fmt="0.0000")
        if load_profile.get("path"):
            entry("Load profile file", load_profile["path"],
                  source="case.json load_profile.path (8760 hourly kW)")
        if load_profile.get("year"):
            entry("Load year", load_profile["year"], fmt="0",
                  source="case.json load_profile.year")

    technologies = case_config.get("technologies") or {}
    pv = technologies.get("pv") or {}
    if pv:
        section("PV Technology (case.json)")
        entry("PV minimum size", pv.get("min_kw"), unit="kW",
              source="case.json technologies.pv.min_kw", fmt=FMT_AMOUNT)
        entry("PV maximum size", pv.get("max_kw"), unit="kW",
              source="case.json technologies.pv.max_kw", fmt=FMT_AMOUNT)
        entry("PV installed cost", pv.get("installed_cost_per_kw"), unit="USD/kW",
              source="case.json technologies.pv.installed_cost_per_kw", fmt=FMT_AMOUNT)
        entry("PV O&M cost", pv.get("om_cost_per_kw"), unit="USD/kW/yr",
              source="case.json technologies.pv.om_cost_per_kw", fmt=FMT_AMOUNT_2)
        entry("PV degradation (case input)", pv.get("degradation_fraction"),
              unit="per year", source="case.json technologies.pv.degradation_fraction",
              fmt=FMT_PERCENT)
        for key, value in (pv.get("pvwatts") or {}).items():
            entry(f"PVWatts {key}", value,
                  source="case.json technologies.pv.pvwatts (production factor inputs)")

    storage = technologies.get("storage") or {}
    if storage:
        section("Storage Technology (case.json)")
        for label, key, unit in STORAGE_CASE_ROWS:
            if storage.get(key) is None:
                continue
            fmt = FMT_PERCENT if key == "om_cost_fraction_of_installed_cost" else FMT_AMOUNT
            entry(label, storage[key], unit=unit,
                  source=f"case.json technologies.storage.{key}", fmt=fmt)


# ---------------------------------------------------------------------------
# Pro Forma (Audit)
# ---------------------------------------------------------------------------

class _ProFormaWriter:
    """Row-oriented writer: line items down, Year 0..N across (SAM layout)."""

    def __init__(self, worksheet, years):
        self.ws = worksheet
        self.years = years          # analysis years (N); columns C..C+N are Year 0..N
        self.row = 1
        self.rows = {}              # key -> row index

    def col(self, year):
        return get_column_letter(3 + year)

    @property
    def first_col(self):
        return self.col(0)

    @property
    def last_col(self):
        return self.col(self.years)

    def year_range(self, row, start=1, end=None):
        end = self.years if end is None else end
        return f"{self.col(start)}{row}:{self.col(end)}{row}"

    def full_range(self, row):
        return f"{self.col(0)}{row}:{self.col(self.years)}{row}"

    def skip(self, count=1):
        self.row += count

    def section(self, label):
        row = self.row
        for year in range(-2, self.years + 1):
            self.ws.cell(row=row, column=3 + year).fill = SECTION_FILL
        cell = self.ws.cell(row=row, column=1, value=label)
        cell.font = SECTION_FONT
        cell.fill = SECTION_FILL
        self.row += 1
        return row

    def line(self, key, label, unit, *, y0=None, formula=None, values=None,
             fmt=FMT_AMOUNT, fill=None, bold=False, start=1):
        """Write one line item.

        ``formula(year, col)`` returns the formula for each year >= ``start``;
        ``values`` hardcodes a list indexed by year 0..N; ``y0`` sets Year 0
        explicitly (value or formula string).
        """
        row = self.row
        self.rows[key] = row
        label_cell = self.ws.cell(row=row, column=1, value=label)
        if unit:  # empty strings serialise as corrupt inlineStr cells
            self.ws.cell(row=row, column=2, value=unit).font = NOTE_FONT
        if bold:
            label_cell.font = BOLD_FONT
        if y0 is not None:
            cell = self.ws.cell(row=row, column=3, value=y0)
            cell.number_format = fmt
            if fill:
                cell.fill = fill
            if bold:
                cell.font = BOLD_FONT
        for year in range(start, self.years + 1):
            cell = self.ws.cell(row=row, column=3 + year)
            if values is not None:
                cell.value = values[year] if year < len(values) else 0
            elif formula is not None:
                cell.value = formula(year, self.col(year))
            cell.number_format = fmt
            if fill:
                cell.fill = fill
            if bold:
                cell.font = BOLD_FONT
        self.row += 1
        return row

    def metric(self, key, label, formula_or_value, fmt, note="", fill=None):
        row = self.row
        self.rows[key] = row
        self.ws.cell(row=row, column=1, value=label)
        cell = self.ws.cell(row=row, column=3, value=formula_or_value)
        cell.number_format = fmt
        cell.font = BOLD_FONT
        if fill:
            cell.fill = fill
        if note:
            self.ws.cell(row=row, column=4, value=note).font = NOTE_FONT
        self.row += 1
        return row


def write_pro_forma_audit_sheet(worksheet, cash_flow_result, assumptions):
    """Rebuild the cash flow with live Excel formulas + engine tie-out.

    Returns a refs dict used by the FX Sensitivity sheet and the Cover status:
    ``{"equity_cf_row", "year_row", "years", "status_cells": [...]}``.
    """
    d = cash_flow_result["derivation"]
    summary = cash_flow_result["summary"]
    annual = cash_flow_result["annual_cash_flows"]
    years = d["project_years"]
    is_dppa = d["structure"] == DPPA
    w = _ProFormaWriter(worksheet, years)

    worksheet.sheet_view.showGridLines = False
    title = worksheet.cell(
        row=1, column=1,
        value="Pro Forma (Audit) — every white cell is a live Excel formula",
    )
    title.font = Font(bold=True, size=13, color=NAVY)
    worksheet.cell(
        row=2, column=1,
        value="Shaded cells are hardcoded engine outputs (REopt dispatch / 8760-h "
              "settlement / tie-out reference). All other cells derive from the "
              "named cells on the Assumptions sheet. Currency: USD at the fixed "
              "contract FX rate.",
    ).font = NOTE_FONT
    w.row = 4

    # --- timeline -----------------------------------------------------------
    w.section("TIMELINE & INDEXATION")
    r_year = w.line("year", "Year", "index", y0=0,
                    formula=lambda y, c: y, fmt="0", bold=True)

    def year_ref(col):
        return f"{col}${r_year}"

    r_fac_energy = w.line(
        "fac_energy", "EVN energy escalation factor", "index",
        formula=lambda y, c: f"=(1+ESC_ENERGY)^({year_ref(c)}-1)", fmt=FMT_FACTOR)
    r_fac_capacity = w.line(
        "fac_capacity", "EVN capacity escalation factor", "index",
        formula=lambda y, c: f"=(1+ESC_CAPACITY)^({year_ref(c)}-1)", fmt=FMT_FACTOR)
    r_fac_om = w.line(
        "fac_om", "O&M escalation factor", "index",
        formula=lambda y, c: f"=(1+ESC_OM)^({year_ref(c)}-1)", fmt=FMT_FACTOR)
    r_fac_deg = w.line(
        "fac_deg", "PV degradation factor", "index",
        formula=lambda y, c: f"=(1-PV_DEGRADATION)^({year_ref(c)}-1)", fmt=FMT_FACTOR)
    if is_dppa:
        r_fac_fee = w.line(
            "fac_fee", "DPPA fee / FMP escalation factor", "index",
            formula=lambda y, c: f"=(1+ESC_FEE)^({year_ref(c)}-1)", fmt=FMT_FACTOR)
        r_fac_strike = w.line(
            "fac_strike", "CfD strike escalation factor", "index",
            formula=lambda y, c: f"=(1+ESC_STRIKE)^({year_ref(c)}-1)", fmt=FMT_FACTOR)
    w.skip()

    # --- revenue ------------------------------------------------------------
    w.section("REVENUE (USD)")
    if is_dppa:
        r_fmp_rev = w.line(
            "fmp_rev", "Generator FMP market revenue", "USD",
            formula=lambda y, c: f"=DPPA_FMP_REV_Y1*{c}{r_fac_fee}*{c}{r_fac_deg}")
        r_cfd_strike = w.line(
            "cfd_strike", "CfD strike leg (P_c × Q_cfd)", "USD",
            formula=lambda y, c: f"=DPPA_CFD_STRIKE_Y1*{c}{r_fac_strike}")
        r_cfd_offset = w.line(
            "cfd_offset", "CfD market offset (FMP × Q_cfd)", "USD",
            formula=lambda y, c: f"=DPPA_CFD_OFFSET_Y1*{c}{r_fac_fee}")
        r_cfd_net = w.line(
            "cfd_net", "CfD net settlement (to generator)", "USD",
            formula=lambda y, c: f"={c}{r_cfd_strike}-{c}{r_cfd_offset}")
        r_energy_rev = w.line(
            "energy_rev", "Generator revenue (FMP + CfD net)", "USD",
            formula=lambda y, c: f"={c}{r_fmp_rev}+{c}{r_cfd_net}", bold=True)
    else:
        r_energy_rev = w.line(
            "energy_rev", "ESCO energy revenue (discount-to-EVN)", "USD",
            formula=lambda y, c: f"=BASE_ENERGY_REV*{c}{r_fac_energy}*{c}{r_fac_deg}")
    r_dem_savings = w.line(
        "dem_savings", "Demand charge savings (total)", "USD",
        formula=lambda y, c: f"=BASE_DEMAND_SAVINGS*{c}{r_fac_capacity}")
    r_dem_rev = w.line(
        "dem_rev", "ESCO share of demand savings", "USD",
        formula=lambda y, c: f"={c}{r_dem_savings}*DEMAND_SHARE")
    if is_dppa:
        r_arb_rev = None
        r_revenue = w.line(
            "revenue", "Total developer revenue", "USD",
            formula=lambda y, c: f"={c}{r_energy_rev}+{c}{r_dem_rev}", bold=True)
    else:
        r_arb_rev = w.line(
            "arb_rev", "Grid arbitrage revenue", "USD",
            formula=lambda y, c: f"=BASE_GRID_ARB*{c}{r_fac_energy}")
        surplus = d.get("surplus_export")
        if surplus:
            # Volume degrades with PV output (r_fac_deg); the price escalates
            # independently (annual market re-set proxy). Matches the engine's
            # surplus_export_revenue exactly so the tie-out holds.
            r_surplus = w.line(
                "surplus_rev", "Surplus export revenue (Decree 243)", "USD",
                formula=lambda y, c:
                    f"=SURPLUS_KWH_Y1*{c}{r_fac_deg}*SURPLUS_PRICE"
                    f"*(1+SURPLUS_ESC)^({year_ref(c)}-1)")
            r_revenue = w.line(
                "revenue", "Total developer revenue", "USD",
                formula=lambda y, c:
                    f"={c}{r_energy_rev}+{c}{r_dem_rev}+{c}{r_arb_rev}+{c}{r_surplus}",
                bold=True)
        else:
            r_revenue = w.line(
                "revenue", "Total developer revenue", "USD",
                formula=lambda y, c: f"={c}{r_energy_rev}+{c}{r_dem_rev}+{c}{r_arb_rev}",
                bold=True)
    w.skip()

    # --- operating costs ----------------------------------------------------
    w.section("OPERATING COSTS (USD)")
    r_om = w.line(
        "om", "O&M", "USD",
        formula=lambda y, c: f"=OM_YEAR1*{c}{r_fac_om}")
    replacement = list(d.get("replacement_costs_by_year_usd") or [])
    replacement_by_year = [0.0] + replacement + [0.0] * years
    r_repl = w.line(
        "repl", "Battery replacement (engine schedule)", "USD",
        values=replacement_by_year[:years + 1], fill=INPUT_FILL)
    r_ebitda = w.line(
        "ebitda", "EBITDA", "USD",
        formula=lambda y, c: f"={c}{r_revenue}-{c}{r_om}-{c}{r_repl}", bold=True)
    w.skip()

    # --- debt ---------------------------------------------------------------
    w.section("DEBT SCHEDULE (USD)")
    # Years >= 2 reference the closing-balance row, which is not written yet;
    # they are filled in right after r_close is known.
    r_open = w.line(
        "debt_open", "Opening debt balance", "USD",
        formula=lambda y, c: "=DEBT_PRINCIPAL" if y == 1 else None)
    r_interest = w.line(
        "interest", "Interest", "USD",
        formula=lambda y, c:
            f"=IF({year_ref(c)}<=DEBT_TERM_YEARS,{c}{r_open}*DEBT_RATE,0)")
    r_principal = w.line(
        "principal", "Principal repayment", "USD",
        formula=lambda y, c:
            f"=IF({year_ref(c)}<=DEBT_TERM_YEARS,"
            f"MIN(MAX(DEBT_PAYMENT-{c}{r_interest},0),{c}{r_open}),0)")
    r_ds = w.line(
        "debt_service", "Debt service", "USD",
        formula=lambda y, c: f"={c}{r_interest}+{c}{r_principal}", bold=True)
    r_close = w.line(
        "debt_close", "Closing debt balance", "USD",
        formula=lambda y, c: f"={c}{r_open}-{c}{r_principal}")
    # fix the opening-balance back-reference now that r_close is known
    for year in range(2, years + 1):
        worksheet.cell(
            row=r_open, column=3 + year,
            value=f"={w.col(year - 1)}{r_close}",
        )
    w.skip()

    # --- depreciation & tax --------------------------------------------------
    w.section("DEPRECIATION & VIETNAM CIT (USD)")
    r_dep_pv = w.line(
        "dep_pv", "PV depreciation (straight-line)", "USD",
        formula=lambda y, c:
            f"=IF({year_ref(c)}<=PV_DEP_YEARS,PV_CAPEX/PV_DEP_YEARS,0)")
    r_dep_bess = w.line(
        "dep_bess", "BESS depreciation (straight-line)", "USD",
        formula=lambda y, c:
            f"=IF({year_ref(c)}<=BESS_DEP_YEARS,BESS_CAPEX/BESS_DEP_YEARS,0)")
    r_dep = w.line(
        "dep", "Total depreciation", "USD",
        formula=lambda y, c: f"={c}{r_dep_pv}+{c}{r_dep_bess}")
    r_ebt = w.line(
        "ebt", "Taxable income before loss relief (EBT)", "USD",
        formula=lambda y, c: f"={c}{r_ebitda}-{c}{r_dep}-{c}{r_interest}", bold=True)
    r_newloss = w.line(
        "newloss", "New tax loss arising", "USD",
        formula=lambda y, c: f"=MAX(-{c}{r_ebt},0)")
    r_income_pos = w.line(
        "income_pos", "Assessable income (pre-relief)", "USD",
        formula=lambda y, c: f"=MAX({c}{r_ebt},0)")

    # FIFO tax-loss carryforward with 5-year expiry (Circular 78/2014 Art. 9):
    # avail[j] = unused loss aged j years; usage consumes oldest vintages first.
    r_avail = {}
    r_used = {}
    for age in range(1, 6):
        r_avail[age] = w.line(
            f"loss_avail_{age}", f"Loss vintage aged {age}y — available", "USD",
            formula=None)
    oldest_first = [5, 4, 3, 2, 1]
    for age in oldest_first:
        def used_formula(y, c, age=age):
            older_terms = "".join(
                f"-{c}{r_used[a]}" for a in oldest_first[:oldest_first.index(age)]
            )
            return (f"=MIN({c}{r_avail[age]},"
                    f"MAX({c}{r_income_pos}{older_terms},0))")
        r_used[age] = w.line(
            f"loss_used_{age}", f"Loss vintage aged {age}y — utilised", "USD",
            formula=used_formula)
    # availability recursion (needs r_used, so filled after)
    for age in range(1, 6):
        for year in range(1, years + 1):
            cell = worksheet.cell(row=r_avail[age], column=3 + year)
            prev = w.col(year - 1)
            if age == 1:
                cell.value = 0 if year == 1 else f"={prev}{r_newloss}"
            else:
                cell.value = (
                    0 if year == 1
                    else f"=MAX({prev}{r_avail[age - 1]}-{prev}{r_used[age - 1]},0)"
                )
            cell.number_format = FMT_AMOUNT
    r_relief = w.line(
        "relief", "Loss relief utilised (FIFO, ≤5y old)", "USD",
        formula=lambda y, c: "=" + "+".join(f"{c}{r_used[a]}" for a in oldest_first))
    r_taxbase = w.line(
        "taxbase", "Taxable income after loss relief", "USD",
        formula=lambda y, c: f"={c}{r_income_pos}-{c}{r_relief}", bold=True)
    r_flag = w.line(
        "profit_flag", "Profitable-to-date flag (starts CIT clock)", "0/1",
        formula=lambda y, c: (
            f"=IF({c}{r_ebt}>0,1,0)" if y == 1
            else f"=IF(OR({w.col(y - 1)}{w.rows['profit_flag']}=1,{c}{r_ebt}>0),1,0)"
        ), fmt="0")
    r_clock = w.metric(
        "cit_clock", "CIT clock start year (first profit, capped)",
        f"=MIN(IFERROR(MATCH(1,{w.year_range(r_flag)},0),CIT_CLOCK_CAP_YEAR),"
        "CIT_CLOCK_CAP_YEAR)",
        "0", note="Circular 78/2014 Art. 18")
    clock_ref = f"$C${r_clock}"
    cit = d.get("cit", {})
    if cit.get("preferential_rate") is not None:
        # Law 67/2025 re_producer: the applicable base rate is the preferential
        # rate for the first CIT_PREF_YEARS years (counted from year 1), then
        # the standard rate. The 50% reduction multiplies whichever base rate
        # applies. The standard regime keeps CIT_RATE as the base throughout
        # (formula below collapses to the legacy expression, bit-for-bit).
        r_cit_base = w.line(
            "cit_base_rate", "Applicable base CIT rate (preferential window)", "%",
            formula=lambda y, c:
                f"=IF({year_ref(c)}<=CIT_PREF_YEARS,CIT_PREF_RATE,CIT_RATE)",
            fmt=FMT_PERCENT)

        def base_ref(c):
            return f"{c}{r_cit_base}"
    else:
        def base_ref(c):
            return "CIT_RATE"
    r_cit_rate = w.line(
        "cit_rate", "Applicable CIT rate", "%",
        formula=lambda y, c: (
            f"=IF({year_ref(c)}<{clock_ref}+CIT_HOLIDAY_YEARS,0,"
            f"IF({year_ref(c)}<{clock_ref}+CIT_HOLIDAY_YEARS+CIT_REDUCED_YEARS,"
            f"{base_ref(c)}*CIT_REDUCED_FRACTION,{base_ref(c)}))"
        ), fmt=FMT_PERCENT)
    r_cit = w.line(
        "cit", "CIT payable", "USD",
        formula=lambda y, c: f"={c}{r_taxbase}*{c}{r_cit_rate}", bold=True)
    w.skip()

    # --- cash flows -----------------------------------------------------------
    w.section("CASH FLOW & COVERAGE (USD)")
    r_cfads = w.line(
        "cfads", "Cash available for debt service (CFADS)", "USD",
        formula=lambda y, c: f"={c}{r_ebitda}-{c}{r_cit}", bold=True)
    r_proj = w.line(
        "project_cf", "Project cash flow (unlevered, post-tax)", "USD",
        y0="=-TOTAL_CAPEX",
        formula=lambda y, c: f"={c}{r_cfads}")
    r_eq = w.line(
        "equity_cf", "Equity cash flow", "USD",
        y0="=-EQUITY_INVESTMENT",
        formula=lambda y, c: f"={c}{r_cfads}-{c}{r_ds}", bold=True)
    r_cum = w.line(
        "cum_equity", "Cumulative equity cash flow", "USD",
        y0=f"={w.col(0)}{r_eq}",
        formula=lambda y, c: f"={w.col(y - 1)}{w.rows['cum_equity']}+{c}{w.rows['equity_cf']}")
    r_dscr = w.line(
        "dscr", "DSCR (debt years)", "x",
        formula=lambda y, c: f"=IF({c}{r_ds}>0,{c}{r_cfads}/{c}{r_ds},\"\")",
        fmt=FMT_RATIO)
    w.skip()

    # --- offtaker -------------------------------------------------------------
    w.section("OFFTAKER (BUYER) POSITION (USD)")
    r_bau = w.line(
        "bau_bill", "BAU EVN bill (energy + demand)", "USD",
        formula=lambda y, c: f"=BAU_BILL_Y1*{c}{r_fac_energy}")
    if is_dppa:
        r_c_dn = w.line(
            "c_dn", "C_DN spot energy (Q_Khc × CFMP × K_pp)", "USD",
            formula=lambda y, c: f"=DPPA_C_DN_Y1*{c}{r_fac_fee}*{c}{r_fac_deg}")
        r_c_dppa = w.line(
            "c_dppa", "C_DPPA system service fee", "USD",
            formula=lambda y, c: f"=DPPA_C_DPPA_Y1*{c}{r_fac_fee}*{c}{r_fac_deg}")
        r_c_cl = w.line(
            "c_cl", "C_CL settlement adder", "USD",
            formula=lambda y, c: f"=DPPA_C_CL_Y1*{c}{r_fac_fee}*{c}{r_fac_deg}")
        r_c_bl = w.line(
            "c_bl", "C_BL retail shortfall (incl. degradation repurchase)", "USD",
            formula=lambda y, c:
                f"=(DPPA_C_BL_Y1+DPPA_MATCHED_RETAIL_Y1*(1-{c}{r_fac_deg}))"
                f"*{c}{r_fac_energy}")
        r_post = w.line(
            "post_cost", "Buyer cost with project", "USD",
            formula=lambda y, c:
                f"={c}{r_c_dn}+{c}{r_c_dppa}+{c}{r_c_cl}+{c}{r_c_bl}"
                f"+{c}{w.rows['cfd_net']}+OPT_DEMAND_Y1*{c}{r_fac_capacity}"
                f"+{c}{r_dem_rev}",
            bold=True)
    else:
        r_post = w.line(
            "post_cost", "Buyer cost with project", "USD",
            formula=lambda y, c:
                f"=(OPT_BILL_Y1+BASE_SERVED_RETAIL*(1-{c}{r_fac_deg}))"
                f"*{c}{r_fac_energy}"
                f"+{c}{r_energy_rev}+{c}{r_dem_rev}+{c}{r_arb_rev}",
            bold=True)
    r_savings = w.line(
        "savings", "Buyer savings vs BAU", "USD",
        formula=lambda y, c: f"={c}{r_bau}-{c}{r_post}", bold=True)
    w.line(
        "savings_pct", "Buyer savings (% of BAU)", "%",
        formula=lambda y, c: f"=IF({c}{r_bau}=0,\"\",{c}{r_savings}/{c}{r_bau})",
        fmt=FMT_PERCENT)
    w.skip()

    # --- return metrics ---------------------------------------------------------
    w.section("RETURN METRICS (Excel formulas)")
    ten = min(10, years)
    r_irr_eq = w.metric(
        "m_equity_irr", "Equity IRR", f"=IRR({w.full_range(r_eq)})", FMT_PERCENT)
    r_irr_proj = w.metric(
        "m_project_irr", "Project IRR (unlevered)",
        f"=IRR({w.full_range(r_proj)})", FMT_PERCENT)
    r_npv = w.metric(
        "m_npv", "Equity NPV @ owner discount rate",
        f"=NPV(DISC_RATE,{w.year_range(r_eq)})+{w.col(0)}{r_eq}", FMT_AMOUNT)
    r_min_dscr = w.metric(
        "m_min_dscr", "Minimum DSCR (debt years)",
        f"=MIN({w.year_range(r_dscr)})", FMT_RATIO,
        note="MIN ignores the blank non-debt years")
    r_avg_dscr = w.metric(
        "m_avg_dscr", "Average DSCR (debt years)",
        f"=AVERAGE({w.year_range(r_dscr)})", FMT_RATIO)
    r_pay_match = w.metric(
        "m_payback_year", "First year cumulative equity CF ≥ 0",
        f"=MATCH(TRUE,INDEX({w.year_range(r_cum)}>=0,0),0)", "0")
    r_payback = w.metric(
        "m_payback", "Simple equity payback",
        f"=IF(ISNA($C${r_pay_match}),\"n/a\",$C${r_pay_match}-1"
        f"+IFERROR(-INDEX({w.col(0)}{r_cum}:{w.last_col}{r_cum},$C${r_pay_match})"
        f"/INDEX({w.year_range(r_eq)},$C${r_pay_match}),0))",
        FMT_YEARS, note="years")
    r_roi = w.metric(
        "m_roi", "ROI (cumulative equity CF / equity)",
        f"=SUM({w.year_range(r_eq)})/EQUITY_INVESTMENT", FMT_PERCENT)
    r_sav10 = w.metric(
        "m_savings_10yr", "Buyer savings, years 1-10 (% of BAU)",
        f"=SUM({w.year_range(r_savings, 1, ten)})/SUM({w.year_range(r_bau, 1, ten)})",
        FMT_PERCENT)
    w.skip()

    # --- engine tie-out ----------------------------------------------------------
    w.section("CHECKS — EXCEL vs ENGINE (per-year tie-out)")
    eq_engine = [-summary["equity_investment_usd"]] + [
        row["equity_cash_flow_usd"] for row in annual
    ]
    cfads_engine = [None] + [
        row["cash_available_for_debt_service_usd"] for row in annual
    ]
    cit_engine = [None] + [row["cit_usd"] for row in annual]
    r_eq_engine = w.line(
        "eq_engine", "Equity cash flow (engine)", "USD",
        y0=eq_engine[0], values=eq_engine, fill=INPUT_FILL)
    r_cfads_engine = w.line(
        "cfads_engine", "CFADS (engine)", "USD",
        values=cfads_engine, fill=INPUT_FILL)
    r_cit_engine = w.line(
        "cit_engine", "CIT (engine)", "USD",
        values=cit_engine, fill=INPUT_FILL)
    r_delta = w.line(
        "delta", "Max |Excel − engine| this year", "USD",
        y0=f"=ABS({w.col(0)}{r_eq}-{w.col(0)}{r_eq_engine})",
        formula=lambda y, c: (
            f"=MAX(ABS({c}{r_eq}-{c}{r_eq_engine}),"
            f"ABS({c}{r_cfads}-{c}{r_cfads_engine}),"
            f"ABS({c}{r_cit}-{c}{r_cit_engine}))"
        ), fmt="0.0000")
    w.skip()

    header_row = w.row
    for column, header in enumerate(
            ("Check", None, "Excel", "Engine", "Delta", "Status"), start=1):
        cell = worksheet.cell(row=header_row, column=column)
        if header:
            cell.value = header
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
    w.row += 1

    status_cells = []

    def check(label, excel_ref, engine_value, tolerance, fmt):
        row = w.row
        worksheet.cell(row=row, column=1, value=label)
        excel_cell = worksheet.cell(row=row, column=3, value=f"={excel_ref}")
        excel_cell.number_format = fmt
        engine_cell = worksheet.cell(row=row, column=4, value=engine_value)
        engine_cell.number_format = fmt
        engine_cell.fill = INPUT_FILL
        delta = worksheet.cell(row=row, column=5, value=f"=ABS(C{row}-D{row})")
        delta.number_format = "0.000000"
        status = worksheet.cell(
            row=row, column=6,
            value=f"=IF(ABS(C{row}-D{row})<={_fmt_num(tolerance)},\"PASS\",\"REVIEW\")",
        )
        status.fill = CHECK_FILL
        status.font = BOLD_FONT
        status_cells.append(f"F{row}")
        w.row += 1

    min_dscr_engine = _minimum_dscr(annual)
    check("Per-year cash flow tie-out (max delta, all years)",
          f"MAX({w.full_range(r_delta)})", 0.0, TOL_AMOUNT, "0.0000")
    if summary.get("equity_irr_fraction") is not None:
        check("Equity IRR", f"$C${r_irr_eq}", summary["equity_irr_fraction"],
              TOL_RATE, FMT_PERCENT)
    if summary.get("project_irr_fraction") is not None:
        check("Project IRR", f"$C${r_irr_proj}", summary["project_irr_fraction"],
              TOL_RATE, FMT_PERCENT)
    check("Equity NPV", f"$C${r_npv}", summary["npv_usd"], TOL_AMOUNT, FMT_AMOUNT)
    if min_dscr_engine is not None:
        check("Minimum DSCR", f"$C${r_min_dscr}", min_dscr_engine, TOL_RATIO, FMT_RATIO)
    if summary.get("average_dscr") is not None:
        check("Average DSCR", f"$C${r_avg_dscr}", summary["average_dscr"],
              TOL_RATIO, FMT_RATIO)
    if summary.get("simple_payback_years") is not None:
        check("Simple equity payback", f"$C${r_payback}",
              summary["simple_payback_years"], TOL_YEARS, FMT_YEARS)
    if summary.get("roi_fraction") is not None:
        check("ROI", f"$C${r_roi}", summary["roi_fraction"], TOL_RATE, FMT_PERCENT)
    if summary.get("buyer_savings_10yr_fraction") is not None:
        check("Buyer savings, years 1-10 (% of BAU)", f"$C${r_sav10}",
              summary["buyer_savings_10yr_fraction"], TOL_RATE, FMT_PERCENT)

    # highlight REVIEW statuses in red
    status_range = f"F{header_row + 1}:F{w.row - 1}"
    worksheet.conditional_formatting.add(
        status_range,
        CellIsRule(operator="equal", formula=['"REVIEW"'],
                   font=Font(bold=True, color="9C0006"),
                   fill=PatternFill("solid", fgColor="FFC7CE")),
    )

    worksheet.column_dimensions["A"].width = 48
    worksheet.column_dimensions["B"].width = 8
    for year in range(0, years + 1):
        worksheet.column_dimensions[w.col(year)].width = 13
    worksheet.freeze_panes = f"C{r_year + 1}"

    return {
        "sheet": worksheet.title,
        "years": years,
        "year_row": r_year,
        "equity_cf_row": r_eq,
        "status_cells": status_cells,
        "status_range": status_range,
    }


def _minimum_dscr(annual_rows):
    values = [
        row["dscr"] for row in annual_rows
        if row.get("debt_service_usd") and row.get("dscr") is not None
    ]
    return min(values) if values else None


# ---------------------------------------------------------------------------
# FX Sensitivity
# ---------------------------------------------------------------------------

def write_fx_sensitivity_sheet(worksheet, cash_flow_result, proforma_refs):
    """USD equity returns under annual VND depreciation — live formulas."""
    engine_rows = calculate_fx_sensitivity(cash_flow_result)
    years = proforma_refs["years"]
    eq_row = proforma_refs["equity_cf_row"]
    sheet_ref = f"'{proforma_refs['sheet']}'"

    worksheet.sheet_view.showGridLines = False
    worksheet.merge_cells("A1:F1")
    title = worksheet.cell(row=1, column=1, value="FX Sensitivity — VND depreciation vs USD returns")
    title.fill = TITLE_FILL
    title.font = TITLE_FONT
    worksheet.row_dimensions[1].height = 24
    worksheet.cell(
        row=2, column=1,
        value="Cash flows are VND-denominated (EVN tariff / DPPA settlement) but reported in USD "
              "at the fixed contract rate. Each scenario deflates the year-t USD equity cash flow "
              "by (1+d)^t. Debt is assumed VND-denominated, so DSCR is unchanged. The rate cells "
              "are editable; engine columns validate the default scenarios.",
    ).font = NOTE_FONT

    header_row = 4
    headers = ("VND depreciation (per year)", "Equity IRR (USD)", "Equity NPV (USD)",
               "Equity IRR (engine)", "Equity NPV (engine)", "Status")
    for column, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=header_row, column=column, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    helper_start = header_row + len(engine_rows) + 3
    worksheet.cell(
        row=helper_start - 1, column=1,
        value="Helper — FX-adjusted equity cash flow per scenario (USD): "
              "CF_t / (1 + d)^t",
    ).font = NOTE_FONT
    year_header_row = helper_start
    for year in range(0, years + 1):
        col = get_column_letter(2 + year)
        cell = worksheet.cell(row=year_header_row, column=2 + year, value=year)
        cell.font = BOLD_FONT
        cell.number_format = "0"

    status_cells = []
    for index, engine in enumerate(engine_rows):
        table_row = header_row + 1 + index
        helper_row = year_header_row + 1 + index
        rate_cell = worksheet.cell(row=table_row, column=1, value=engine["vnd_depreciation_rate"])
        rate_cell.number_format = FMT_PERCENT
        rate_cell.fill = INPUT_FILL

        worksheet.cell(row=helper_row, column=1, value=f"=A{table_row}").number_format = FMT_PERCENT
        for year in range(0, years + 1):
            col = get_column_letter(2 + year)
            worksheet.cell(
                row=helper_row, column=2 + year,
                value=(
                    f"={sheet_ref}!{get_column_letter(3 + year)}{eq_row}"
                    f"/(1+$A{table_row})^{col}${year_header_row}"
                ),
            ).number_format = FMT_AMOUNT
        helper_range = f"B{helper_row}:{get_column_letter(2 + years)}{helper_row}"
        first_year_range = f"C{helper_row}:{get_column_letter(2 + years)}{helper_row}"

        irr_cell = worksheet.cell(row=table_row, column=2, value=f"=IRR({helper_range})")
        irr_cell.number_format = FMT_PERCENT
        npv_cell = worksheet.cell(
            row=table_row, column=3,
            value=f"=NPV(DISC_RATE,{first_year_range})+B{helper_row}",
        )
        npv_cell.number_format = FMT_AMOUNT
        engine_irr = worksheet.cell(row=table_row, column=4, value=engine["equity_irr_fraction"])
        engine_irr.number_format = FMT_PERCENT
        engine_irr.fill = INPUT_FILL
        engine_npv = worksheet.cell(row=table_row, column=5, value=engine["npv_usd"])
        engine_npv.number_format = FMT_AMOUNT
        engine_npv.fill = INPUT_FILL
        status = worksheet.cell(
            row=table_row, column=6,
            value=(
                f"=IF(AND(ABS(B{table_row}-D{table_row})<={_fmt_num(TOL_RATE)},"
                f"ABS(C{table_row}-E{table_row})<={_fmt_num(TOL_AMOUNT)}),"
                f"\"PASS\",\"REVIEW\")"
            ),
        )
        status.fill = CHECK_FILL
        status.font = BOLD_FONT
        status_cells.append(f"F{table_row}")

    status_range = f"F{header_row + 1}:F{header_row + len(engine_rows)}"
    worksheet.conditional_formatting.add(
        status_range,
        CellIsRule(operator="equal", formula=['"REVIEW"'],
                   font=Font(bold=True, color="9C0006"),
                   fill=PatternFill("solid", fgColor="FFC7CE")),
    )

    worksheet.column_dimensions["A"].width = 28
    for letter in ("B", "C", "D", "E", "F"):
        worksheet.column_dimensions[letter].width = 20

    return {"sheet": worksheet.title, "status_range": status_range}


# ---------------------------------------------------------------------------
# Model Basis
# ---------------------------------------------------------------------------

def write_model_basis_sheet(worksheet, assumptions, derivation):
    derivation = derivation or {}
    is_dppa = derivation.get("structure") == DPPA
    fx = derivation.get("exchange_rate_vnd_per_usd") or assumptions.get("exchange_rate_vnd_per_usd")

    if derivation.get("cit", {}).get("regime") == "re_producer":
        cit_regime_text = (
            "CIT regime: renewable-energy producer (Law 67/2025/QH15 + Decree "
            "320/2025/NĐ-CP) — 10% preferential base rate for the first 15 years "
            "counted from the first revenue-generating year, then 20%."
        )
    else:
        cit_regime_text = (
            "CIT regime: standard rate with holiday (Law 67/2025; legacy Circular "
            "78/2014 shape) — 20% base rate throughout. Conservative default for a "
            "service ESCO, whose RE-producer status is a legal question; "
            "grandfathered projects keep old-law incentives."
        )

    worksheet.sheet_view.showGridLines = False
    worksheet.merge_cells("B1:C1")
    title = worksheet.cell(row=1, column=2, value="Model Basis, Conventions & Simplifications")
    title.fill = TITLE_FILL
    title.font = TITLE_FONT
    worksheet.row_dimensions[1].height = 24

    sections = [
        ("1. Model architecture", [
            "REopt (NLR optimization engine) selects PV/BESS sizing and hourly dispatch against the "
            "EVN time-of-use tariff over an 8760-hour year.",
            "proforma_vietnam post-processes the REopt run: an hourly ND57/2025 DPPA settlement layer "
            "(when applicable) and a 25-year developer cash flow with Vietnam tax and debt.",
            "This workbook is generated from that engine. The Pro Forma (Audit) sheet re-derives the "
            "full cash flow with live Excel formulas from the named inputs on the Assumptions sheet; "
            "the Checks block ties every metric back to the engine (PASS/REVIEW).",
        ]),
        ("2. Currency & FX", [
            f"All money flows are computed in USD at the fixed contract rate ({fx:,.0f} VND/USD)."
            if fx else
            "All money flows are computed in USD at the fixed contract exchange rate.",
            "Underlying revenue is VND-denominated (EVN tariff, FMP market, DPPA fees). Holding FX flat "
            "for the analysis period is a simplification: the FX Sensitivity sheet quantifies USD-reported "
            "returns under 0-3%/yr VND depreciation.",
            "Sheets that show VND amounts (Hourly/Monthly Settlement, DPPA fee inputs) are VND-native "
            "regulatory quantities, not conversions.",
            "Debt is assumed VND-denominated (local bank), so DSCR is FX-neutral.",
        ]),
        ("3. Settlement math" + (" — ND57/2025 grid DPPA with CfD" if is_dppa else " — ESCO discount-to-EVN"), (
            [
                "Q_adj[h] = Q_re_meter[h] / K_pp × delta — quantity conversion generator→customer uses "
                "K_pp only (CD7 Ví dụ 1); k is price-only.",
                "Q_Khc[h] = min(load[h], Q_adj[h]) — the buyer settles only matched consumption; surplus "
                "stays with the generator at FMP and is never billed to the buyer.",
                "C_DN = Q_Khc × CFMP × K_pp with CFMP = FMP × k;  C_DPPA = Q_Khc × f_dppa;  C_CL = Q_Khc × f_cl;  "
                "C_BL = shortfall × EVN TOU retail.",
                "CfD settles on min(Q_c, Q_Khc) per CD7 Ví dụ 4: CfD[h] = (P_c − FMP[h]) × Q_cfd[h]. The strike "
                "leg escalates at the contracted strike escalation; the market legs at the fee escalation.",
                "Curtailed PV from the self-consumption REopt run is credited as grid export at FMP (the "
                "generator does not curtail under DPPA).",
                "Year-1 settlement is computed hourly; later years scale the year-1 totals by the escalation "
                "and degradation factors shown on the Pro Forma (Audit) sheet.",
            ] if is_dppa else [
                "The ESCO is paid a contracted fraction of the time-specific EVN tariff for project-served "
                "energy (PV→load, plus battery→load when the battery cannot grid-charge).",
                "Demand-charge savings vs BAU are split between ESCO and offtaker at the contracted share.",
                "Year-1 revenue is computed from the 8760-hour REopt dispatch × TOU rates; later years scale "
                "by EVN escalation and PV degradation factors shown on the Pro Forma (Audit) sheet.",
            ]
        )),
        ("4. Multi-year mechanics", [
            "PV degradation compounds on generation-linked terms; energy lost to degradation is repurchased "
            "from EVN at retail (added to the buyer's residual bill / C_BL).",
            "O&M escalates at its own rate; battery replacement is booked in the configured year at REopt "
            "replacement unit costs.",
            "Debt: level-payment annuity over the debt term (interest + principal split per the Debt "
            "Schedule block).",
            cit_regime_text + " The 4-year exemption and 9-year 50%-reduction periods count from the first "
            "profitable year, no later than year 4; the 50% reduction applies to the then-applicable base "
            "rate. Tax losses carry forward at most 5 consecutive years, consumed FIFO — the carryforward "
            "schedule is fully visible on the Pro Forma sheet.",
            "Straight-line depreciation: PV over the configured life within the 7-20y band of Circular "
            "45/2013/TT-BTC; BESS over its own life.",
        ]),
        ("5. Simplifications register (disclosed for audit)", [
            "Fixed FX over the analysis period — quantified on the FX Sensitivity sheet.",
            "Battery replacement is expensed in the replacement year, not capitalized and re-depreciated.",
            "VAT is out of scope (pass-through assumed for both parties).",
            "No working-capital, DSRA, or terminal/residual value is modelled.",
            "A single dispatch year (8760 h) is escalated; no re-dispatch in later years.",
            "REopt sizing is optimizer output and can vary slightly between solver versions; the financial "
            "post-processing is deterministic given results.json.",
        ]),
        ("6. How to validate this workbook", [
            "1) Assumptions sheet: confirm every shaded input against the case file / contract term sheet.",
            "2) Pro Forma (Audit): trace any line — formulas reference named cells (e.g. ESC_ENERGY, "
            "DEBT_RATE) and prior rows only.",
            "3) Checks block: every metric shows Excel vs engine with PASS/REVIEW at stated tolerances "
            "(amounts $1, rates 5 bp, DSCR 0.005, payback 0.05 yr).",
            "4) FX Sensitivity: rate cells are editable; Excel recomputes IRR/NPV live.",
            "5) Technical sheets (Technical Results, Dispatch Profile, Load Duration, Settlement) are "
            "engine output for record. The Dispatch sheet's PV production factor (kWh/kW, PVWatts-derived) "
            "is the hourly solar-resource signal — REopt does not persist raw irradiance.",
        ]),
        ("7. Key references", [
            "ND57/2025 (DPPA decree) Art. 14-18 — settlement chain and eligibility.",
            "NSMO/CD7 simulation examples — k price-only conversion (Ví dụ 1), CfD cap on matched volume (Ví dụ 4).",
            "Law 67/2025/QH15 + Decree 320/2025/NĐ-CP — CIT rates, RE-producer preferential incentive, "
            "holiday & loss carryforward (legacy Circular 78/2014 Art. 9, 18 shape kept for the standard regime).",
            "Circular 45/2013/TT-BTC — fixed-asset depreciation bands.",
            "EVN retail tariff (current & QĐ963 TOU structures) as configured in the case file.",
        ]),
    ]

    row = 3
    for heading, bullets in sections:
        cell = worksheet.cell(row=row, column=2, value=heading)
        cell.font = Font(bold=True, size=11, color=NAVY)
        row += 1
        for bullet in bullets:
            bullet_cell = worksheet.cell(row=row, column=2, value="•  " + bullet)
            bullet_cell.alignment = Alignment(wrap_text=True, vertical="top")
            worksheet.row_dimensions[row].height = max(
                14, 13 * (1 + len(bullet) // 105)
            )
            row += 1
        row += 1

    worksheet.column_dimensions["A"].width = 2
    worksheet.column_dimensions["B"].width = 110


# ---------------------------------------------------------------------------
# Cover
# ---------------------------------------------------------------------------

def write_cover_sheet(worksheet, workbook, assumptions, derivation,
                      check_ranges=None):
    derivation = derivation or {}
    is_dppa = derivation.get("structure") == DPPA
    case_name = (assumptions or {}).get("case_name", "Vietnam ESCO / DPPA Case")

    worksheet.sheet_view.showGridLines = False
    worksheet.merge_cells("B2:E2")
    title = worksheet.cell(row=2, column=2, value=f"Investment Case Workbook — {case_name}")
    title.fill = TITLE_FILL
    title.font = Font(bold=True, color="FFFFFF", size=15)
    worksheet.row_dimensions[2].height = 30

    subtitle = (
        "Grid-connected DPPA with CfD (ND57/2025)" if is_dppa
        else "ESCO discount-to-EVN tariff (behind-the-meter)"
    )
    worksheet.cell(
        row=3, column=2,
        value=f"{subtitle}  ·  prepared {date.today().isoformat()}  ·  "
              "REopt dispatch + proforma_vietnam financial engine",
    ).font = NOTE_FONT
    if (assumptions or {}).get("run_uuid"):
        worksheet.cell(
            row=4, column=2, value=f"REopt run UUID: {assumptions['run_uuid']}"
        ).font = NOTE_FONT

    row = 6
    if check_ranges:
        worksheet.cell(row=row, column=2, value="Model validation status").font = BOLD_FONT
        countifs = "+".join(
            f"COUNTIF('{sheet}'!{rng},\"REVIEW\")" for sheet, rng in check_ranges
        )
        status = worksheet.cell(
            row=row, column=3,
            value=f"=IF({countifs}=0,\"ALL CHECKS PASS\",\"REVIEW REQUIRED\")",
        )
        status.font = Font(bold=True, size=12, color=NAVY)
        worksheet.cell(
            row=row, column=4,
            value="Live tie-out of every Excel-derived metric against the engine",
        ).font = NOTE_FONT
        row += 2

    worksheet.cell(row=row, column=2, value="Colour legend").font = BOLD_FONT
    row += 1
    legend_input = worksheet.cell(row=row, column=2, value="Hardcoded input / engine output")
    legend_input.fill = INPUT_FILL
    worksheet.cell(
        row=row, column=3,
        value="Case file terms, REopt dispatch results, 8760-h settlement totals, tie-out references",
    ).font = NOTE_FONT
    row += 1
    worksheet.cell(row=row, column=2, value="Live Excel formula (white)")
    worksheet.cell(
        row=row, column=3,
        value="Everything derivable is a formula — trace with Excel's formula auditing tools",
    ).font = NOTE_FONT
    row += 1
    legend_check = worksheet.cell(row=row, column=2, value="PASS / REVIEW check cell")
    legend_check.fill = CHECK_FILL
    worksheet.cell(
        row=row, column=3, value="Excel-vs-engine tie-out at stated tolerances"
    ).font = NOTE_FONT
    row += 2

    worksheet.cell(row=row, column=2, value="Contents").font = BOLD_FONT
    row += 1
    guide = [
        ("Executive Summary", "Headline KPIs for both counterparties"),
        ("Assumptions", "Every case input & contract term with unit, source and named cell"),
        ("Model Basis", "Methodology, settlement math, simplifications register"),
        (PRO_FORMA_SHEET, "Full cash flow rebuilt with live formulas + engine tie-out"),
        ("FX Sensitivity", "USD returns under VND depreciation (editable)"),
        ("Buyer Analysis", "Offtaker savings vs business-as-usual"),
        ("Developer Returns", "Sources & uses, coverage, equity cash flow"),
        ("Technical Results", "System sizing, year-1 energy balance, bill comparison"),
        ("Dispatch Profile", "8760-h dispatch incl. original PV generation; chart shows the peak-load week"),
        ("Load Duration", "Load and net-load duration curves"),
    ]
    if is_dppa:
        guide.append(("Year 1 BAU vs DPPA", "Side-by-side year-1 buyer/seller position"))
        guide.append(("Monthly / Hourly Settlement",
                      "ND57 fee chain, VND-native (full configuration on Assumptions)"))
    for sheet_name, description in guide:
        worksheet.cell(row=row, column=2, value=sheet_name).font = BOLD_FONT
        worksheet.cell(row=row, column=3, value=description).font = NOTE_FONT
        row += 1

    row += 1
    for note in (
        "Prepared for investment and lending review. Figures are model outputs, not offers; "
        "REopt sizing is optimizer output and may shift with solver versions.",
        "Regenerate offline anytime: python -m proforma_vietnam.rebuild_report --case-dir <case>.",
    ):
        worksheet.cell(row=row, column=2, value=note).font = NOTE_FONT
        row += 1

    worksheet.column_dimensions["A"].width = 2
    worksheet.column_dimensions["B"].width = 46
    worksheet.column_dimensions["C"].width = 30
    worksheet.column_dimensions["D"].width = 60
    worksheet.column_dimensions["E"].width = 14
