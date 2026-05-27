from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill


SUMMARY_ROWS = [
    ("Total Capex (USD)", "total_capex_usd"),
    ("Debt Principal (USD)", "debt_principal_usd"),
    ("Equity Investment (USD)", "equity_investment_usd"),
    ("Project IRR", "project_irr_fraction"),
    ("Equity IRR", "equity_irr_fraction"),
    ("NPV (USD)", "npv_usd"),
    ("Average DSCR", "average_dscr"),
    ("Simple Payback (Years)", "simple_payback_years"),
    ("ROI", "roi_fraction"),
]

CASH_FLOW_COLUMNS = [
    ("Year", "year"),
    ("ESCO Energy Revenue (USD)", "esco_energy_revenue_usd"),
    ("ESCO Demand Revenue (USD)", "esco_demand_revenue_usd"),
    ("ESCO Grid Arbitrage Revenue (USD)", "esco_grid_arbitrage_revenue_usd"),
    ("ESCO Revenue (USD)", "esco_revenue_usd"),
    ("O&M (USD)", "annual_om_usd"),
    ("Replacement Cost (USD)", "replacement_cost_usd"),
    ("Depreciation (USD)", "depreciation_usd"),
    ("CIT (USD)", "cit_usd"),
    ("Cash Available For Debt Service (USD)", "cash_available_for_debt_service_usd"),
    ("Debt Service (USD)", "debt_service_usd"),
    ("Equity Cash Flow (USD)", "equity_cash_flow_usd"),
    ("Offtaker Savings (USD)", "offtaker_savings_usd"),
    ("Offtaker Savings Fraction", "offtaker_savings_fraction"),
    ("DSCR", "dscr"),
]

TAX_SCHEDULE_COLUMNS = [
    ("Year", "year"),
    ("Depreciation (USD)", "depreciation_usd"),
    ("CIT (USD)", "cit_usd"),
]

DEBT_SERVICE_COLUMNS = [
    ("Year", "year"),
    ("Interest (USD)", "interest_usd"),
    ("Principal (USD)", "principal_usd"),
    ("Debt Service (USD)", "debt_service_usd"),
    ("Ending Debt Balance (USD)", "ending_debt_balance_usd"),
]

SYSTEM_SIZING_ROWS = [
    ("PV Size (kW)", "pv_kw"),
    ("Battery Power (kW)", "battery_kw"),
    ("Battery Energy (kWh)", "battery_kwh"),
]

RESULTS_COMPARISON_ROWS = [
    ("BAU Utility Bill (USD)", "bau_utility_bill_usd"),
    ("Optimized Utility Bill (USD)", "optimized_utility_bill_usd"),
    ("Utility Bill Savings (USD)", "utility_bill_savings_usd"),
    ("BAU Demand Charge (USD)", "bau_demand_charge_usd"),
    ("Optimized Demand Charge (USD)", "optimized_demand_charge_usd"),
    ("Demand Charge Savings (USD)", "demand_charge_savings_usd"),
]

ANNUAL_PRODUCTION_ROWS = [
    ("PV to Load (kWh)", "pv_to_load_kwh"),
    ("PV to Storage (kWh)", "pv_to_storage_kwh"),
    ("Storage to Load (kWh)", "storage_to_load_kwh"),
    ("Grid to Load (kWh)", "grid_to_load_kwh"),
    ("PV Curtailed (kWh)", "pv_curtailed_kwh"),
    ("Grid to Storage (kWh)", "grid_to_storage_kwh"),
]

DISPATCH_COLUMNS = [
    ("Hour", "hour"),
    ("Load (kW)", "load_kw"),
    ("Grid to Load (kW)", "grid_to_load_kw"),
    ("PV to Load (kW)", "pv_to_load_kw"),
    ("Storage to Load (kW)", "storage_to_load_kw"),
    ("Storage Charge (kW)", "storage_charge_kw"),
]

LOAD_DURATION_COLUMNS = [
    ("Rank", "rank"),
    ("Load (kW)", "load_kw"),
    ("Net Load (kW)", "net_load_kw"),
]

DEVELOPER_FINANCIAL_ROWS = [
    ("Project IRR", "project_irr_fraction"),
    ("Equity IRR", "equity_irr_fraction"),
    ("NPV (USD)", "npv_usd"),
    ("Average DSCR", "average_dscr"),
    ("Simple Payback (Years)", "simple_payback_years"),
    ("ROI", "roi_fraction"),
]

HEADER_FILL = PatternFill("solid", fgColor="D9EAF7")
HEADER_FONT = Font(bold=True)


def build_vietnam_esco_workbook(cash_flow_result, assumptions=None, report_data=None):
    report_data = report_data or {}
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"

    _write_summary_sheet(summary_sheet, cash_flow_result.get("summary", {}))
    _write_key_value_sheet(
        workbook.create_sheet("System Sizing"),
        SYSTEM_SIZING_ROWS,
        report_data.get("system_sizing", {}),
    )
    _write_key_value_sheet(
        workbook.create_sheet("Results Comparison"),
        RESULTS_COMPARISON_ROWS,
        report_data.get("results_comparison", {}),
    )
    _write_key_value_sheet(
        workbook.create_sheet("Annual Production"),
        ANNUAL_PRODUCTION_ROWS,
        report_data.get("annual_production", {}),
        chart_title="Annual Electricity Production Breakdown",
    )
    _write_table_sheet(
        workbook.create_sheet("Dispatch Profile"),
        DISPATCH_COLUMNS,
        report_data.get("dispatch_profile", []),
        chart_title="Dispatch Profile",
    )
    _write_table_sheet(
        workbook.create_sheet("Load Duration"),
        LOAD_DURATION_COLUMNS,
        report_data.get("load_duration", []),
        chart_title="Load Duration Curve",
    )
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
    _write_key_value_sheet(
        workbook.create_sheet("Developer Financials"),
        DEVELOPER_FINANCIAL_ROWS,
        report_data.get("developer_financial_performance", cash_flow_result.get("summary", {})),
        chart_title="Developer Financial Performance",
    )
    _write_assumptions_sheet(workbook.create_sheet("Assumptions"), assumptions or {})

    for worksheet in workbook.worksheets:
        _autosize_columns(worksheet)

    return workbook


def _write_summary_sheet(worksheet, summary):
    for row_index, (label, key) in enumerate(SUMMARY_ROWS, start=1):
        worksheet.cell(row=row_index, column=1, value=label)
        worksheet.cell(row=row_index, column=2, value=_lookup(summary, key))

    worksheet.column_dimensions["A"].width = 28
    worksheet.column_dimensions["B"].width = 18


def _write_key_value_sheet(worksheet, rows, values, chart_title=None):
    worksheet.cell(row=1, column=1, value="Metric").font = HEADER_FONT
    worksheet.cell(row=1, column=2, value="Value").font = HEADER_FONT
    worksheet.cell(row=1, column=1).fill = HEADER_FILL
    worksheet.cell(row=1, column=2).fill = HEADER_FILL

    for row_index, (label, key) in enumerate(rows, start=2):
        worksheet.cell(row=row_index, column=1, value=label)
        worksheet.cell(row=row_index, column=2, value=_lookup(values, key))

    worksheet.freeze_panes = "A2"
    worksheet.column_dimensions["A"].width = 34
    worksheet.column_dimensions["B"].width = 18

    if chart_title and rows:
        _add_bar_chart(worksheet, chart_title, 2, len(rows) + 1)


def _write_table_sheet(worksheet, columns, rows, chart_title=None):
    for column_index, (header, _key) in enumerate(columns, start=1):
        cell = worksheet.cell(row=1, column=column_index, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    for row_index, row in enumerate(rows, start=2):
        for column_index, (_header, key) in enumerate(columns, start=1):
            worksheet.cell(row=row_index, column=column_index, value=_lookup(row, key))

    worksheet.freeze_panes = "A2"
    if chart_title and rows:
        _add_line_chart(worksheet, chart_title, len(columns), len(rows) + 1)


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


def _lookup(values, key):
    if key in values:
        return values.get(key)
    if key.endswith("_usd"):
        return values.get(f"{key[:-4]}_vnd")
    return values.get(key)


def _add_bar_chart(worksheet, title, first_row, last_row):
    chart = BarChart()
    chart.title = title
    data = Reference(worksheet, min_col=2, min_row=1, max_row=last_row)
    categories = Reference(worksheet, min_col=1, min_row=first_row, max_row=last_row)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.height = 7
    chart.width = 14
    worksheet.add_chart(chart, "D2")


def _add_line_chart(worksheet, title, max_col, last_row):
    chart = LineChart()
    chart.title = title
    data = Reference(worksheet, min_col=2, max_col=max_col, min_row=1, max_row=last_row)
    categories = Reference(worksheet, min_col=1, min_row=2, max_row=last_row)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.height = 7
    chart.width = 16
    worksheet.add_chart(chart, "H2")
