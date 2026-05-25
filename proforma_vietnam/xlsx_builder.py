from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


SUMMARY_ROWS = [
    ("Total Capex (VND)", "total_capex_vnd"),
    ("Debt Principal (VND)", "debt_principal_vnd"),
    ("Equity Investment (VND)", "equity_investment_vnd"),
    ("Project IRR", "project_irr_fraction"),
    ("Equity IRR", "equity_irr_fraction"),
    ("NPV (VND)", "npv_vnd"),
    ("Average DSCR", "average_dscr"),
    ("Simple Payback (Years)", "simple_payback_years"),
    ("ROI", "roi_fraction"),
]

CASH_FLOW_COLUMNS = [
    ("Year", "year"),
    ("ESCO Energy Revenue (VND)", "esco_energy_revenue_vnd"),
    ("ESCO Demand Revenue (VND)", "esco_demand_revenue_vnd"),
    ("ESCO Grid Arbitrage Revenue (VND)", "esco_grid_arbitrage_revenue_vnd"),
    ("ESCO Revenue (VND)", "esco_revenue_vnd"),
    ("O&M (VND)", "annual_om_vnd"),
    ("Replacement Cost (VND)", "replacement_cost_vnd"),
    ("Depreciation (VND)", "depreciation_vnd"),
    ("CIT (VND)", "cit_vnd"),
    ("Cash Available For Debt Service (VND)", "cash_available_for_debt_service_vnd"),
    ("Debt Service (VND)", "debt_service_vnd"),
    ("Equity Cash Flow (VND)", "equity_cash_flow_vnd"),
    ("Offtaker Savings (VND)", "offtaker_savings_vnd"),
    ("Offtaker Savings Fraction", "offtaker_savings_fraction"),
    ("DSCR", "dscr"),
]

TAX_SCHEDULE_COLUMNS = [
    ("Year", "year"),
    ("Depreciation (VND)", "depreciation_vnd"),
    ("CIT (VND)", "cit_vnd"),
]

DEBT_SERVICE_COLUMNS = [
    ("Year", "year"),
    ("Interest (VND)", "interest_vnd"),
    ("Principal (VND)", "principal_vnd"),
    ("Debt Service (VND)", "debt_service_vnd"),
    ("Ending Debt Balance (VND)", "ending_debt_balance_vnd"),
]

HEADER_FILL = PatternFill("solid", fgColor="D9EAF7")
HEADER_FONT = Font(bold=True)


def build_vietnam_esco_workbook(cash_flow_result, assumptions=None):
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"

    _write_summary_sheet(summary_sheet, cash_flow_result.get("summary", {}))
    _write_table_sheet(
        workbook.create_sheet("Cash Flow"),
        CASH_FLOW_COLUMNS,
        cash_flow_result.get("annual_cash_flows", []),
    )
    _write_table_sheet(
        workbook.create_sheet("Tax Schedule"),
        TAX_SCHEDULE_COLUMNS,
        cash_flow_result.get("annual_cash_flows", []),
    )
    _write_table_sheet(
        workbook.create_sheet("Debt Service"),
        DEBT_SERVICE_COLUMNS,
        cash_flow_result.get("annual_cash_flows", []),
    )
    _write_assumptions_sheet(workbook.create_sheet("Assumptions"), assumptions or {})

    for worksheet in workbook.worksheets:
        _autosize_columns(worksheet)

    return workbook


def _write_summary_sheet(worksheet, summary):
    for row_index, (label, key) in enumerate(SUMMARY_ROWS, start=1):
        worksheet.cell(row=row_index, column=1, value=label)
        worksheet.cell(row=row_index, column=2, value=summary.get(key))

    worksheet.column_dimensions["A"].width = 28
    worksheet.column_dimensions["B"].width = 18


def _write_table_sheet(worksheet, columns, rows):
    for column_index, (header, _key) in enumerate(columns, start=1):
        cell = worksheet.cell(row=1, column=column_index, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    for row_index, row in enumerate(rows, start=2):
        for column_index, (_header, key) in enumerate(columns, start=1):
            worksheet.cell(row=row_index, column=column_index, value=row.get(key))

    worksheet.freeze_panes = "A2"


def _write_assumptions_sheet(worksheet, assumptions):
    worksheet.cell(row=1, column=1, value="Assumption").font = HEADER_FONT
    worksheet.cell(row=1, column=2, value="Value").font = HEADER_FONT
    worksheet.cell(row=1, column=1).fill = HEADER_FILL
    worksheet.cell(row=1, column=2).fill = HEADER_FILL

    for row_index, (key, value) in enumerate(assumptions.items(), start=2):
        worksheet.cell(row=row_index, column=1, value=key)
        worksheet.cell(row=row_index, column=2, value=value)

    worksheet.freeze_panes = "A2"


def _autosize_columns(worksheet):
    for column_cells in worksheet.columns:
        width = max(
            len(str(cell.value))
            for cell in column_cells
            if cell.value is not None
        )
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(width + 2, 40)
