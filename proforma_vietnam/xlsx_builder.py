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

DPPA_CASH_FLOW_EXTRA_COLUMNS = [
    ("Generator Revenue (USD)", "generator_revenue_usd"),
    ("CfD Net (USD)", "cfd_net_usd"),
    ("DPPA Offtaker Cost (USD)", "dppa_offtaker_cost_usd"),
]

DPPA_CONFIG_ROWS = [
    ("DPPA Type", "type"),
    ("CfD Strike (VND/kWh)", "cfd_strike_per_kwh_vnd"),
    ("CfD Strike Escalation Rate", "cfd_strike_escalation_rate"),
    ("Transmission Loss Factor k", "transmission_loss_factor_k"),
    ("Distribution Loss Factor K_pp", "distribution_loss_factor_kpp"),
    ("Allocation Fraction delta", "allocation_fraction_delta"),
    ("System Service Fee (VND/kWh)", "c_dppa_service_fee_vnd_per_kwh"),
    ("Delta Settlement Adder (VND/kWh)", "c_cl_settlement_adder_vnd_per_kwh"),
    ("Fee Escalation Rate", "fee_escalation_rate"),
    ("FMP Series Path", "fmp_series_path"),
]

DPPA_HOURLY_COLUMNS = [
    ("Hour", "hour"),
    ("Load (kW)", "load_kw"),
    ("Q_re_meter (kW)", "q_re_meter_kw"),
    ("Q_re_delivered (kW)", "q_re_delivered_kw"),
    ("Q_adj (kW)", "q_adj_kw"),
    ("FMP (VND/kWh)", "fmp_vnd_per_kwh"),
    ("C_DN (VND)", "c_dn_vnd"),
    ("C_DPPA (VND)", "c_dppa_vnd"),
    ("C_CL (VND)", "c_cl_vnd"),
    ("C_BL (VND)", "c_bl_vnd"),
    ("CfD Payment (VND)", "cfd_payment_vnd"),
]

DPPA_MONTHLY_COLUMNS = [
    ("Month", "month"),
    ("C_DN (VND)", "c_dn_vnd"),
    ("C_DPPA (VND)", "c_dppa_vnd"),
    ("C_CL (VND)", "c_cl_vnd"),
    ("C_BL (VND)", "c_bl_vnd"),
    ("CfD Net (VND)", "cfd_net_vnd"),
    ("Generator Revenue (VND)", "generator_revenue_vnd"),
    ("Customer Total (VND)", "customer_total_vnd"),
]

DPPA_ANNUAL_COLUMNS = [
    ("Year", "year"),
    ("C_DN (USD)", "c_dn_usd"),
    ("C_DPPA (USD)", "c_dppa_usd"),
    ("C_CL (USD)", "c_cl_usd"),
    ("C_BL (USD)", "c_bl_usd"),
    ("CfD Net (USD)", "cfd_net_usd"),
    ("Generator Revenue (USD)", "generator_revenue_usd"),
    ("DPPA Offtaker Cost (USD)", "dppa_offtaker_cost_usd"),
]

# Year-1 BAU vs DPPA comparison sheet. Each row pulls from the year-1 cash-flow
# row + assumptions; ("section", None, None) renders as a section header.
BAU_VS_DPPA_ROWS = [
    ("section", "Buyer (Factory) — Year 1 Outflow (USD)", None),
    ("BAU EVN energy + demand bill", "bau_evn_bill_usd", "bau"),
    ("C_DN spot energy (Q_adj × CFMP × K_pp)", "c_dn_usd", "dppa"),
    ("C_DPPA system service fee", "c_dppa_usd", "dppa"),
    ("C_CL settlement adder", "c_cl_usd", "dppa"),
    ("C_BL retail shortfall (P_evn × shortfall)", "c_bl_usd", "dppa"),
    ("CfD payment to ESCO (positive = pay)", "cfd_net_usd", "dppa"),
    ("Optimized demand charge (kept by EVN)", "optimized_demand_charge_year_usd", "dppa"),
    ("ESCO demand savings share charged back", "esco_demand_revenue_usd", "dppa"),
    ("Total buyer outflow", "total_buyer_outflow_usd", "both"),
    ("Buyer savings vs BAU", "buyer_savings_vs_bau_usd", "delta"),
    ("Buyer savings as % of BAU", "buyer_savings_fraction", "delta_fraction"),
    ("section", "Seller (ESCO / Generator) — Year 1 Revenue (USD)", None),
    ("Discount-to-EVN energy revenue (Phase 2)", "esco_phase2_energy_revenue_usd", "bau_esco"),
    ("FMP market revenue (Q_re_meter × FMP)", "generator_fmp_revenue_usd", "dppa"),
    ("CfD net (from buyer)", "cfd_net_usd", "dppa"),
    ("Demand savings share (80%)", "esco_demand_revenue_usd", "both_esco"),
    ("ESCO grid arbitrage revenue", "esco_grid_arbitrage_revenue_usd", "both_esco"),
    ("Total ESCO / generator revenue", "total_seller_revenue_usd", "both_esco"),
    ("section", "System Energy Flows (kWh / yr)", None),
    ("PV → load", "pv_to_load_kwh", "flow"),
    ("PV → storage", "pv_to_storage_kwh", "flow"),
    ("PV → grid (export at FMP)", "pv_to_grid_effective_kwh", "flow"),
    ("Storage → load", "storage_to_load_kwh", "flow"),
    ("Q_re_meter (total generator injection)", "q_re_meter_kwh", "flow"),
    ("Q_adj (loss-adjusted customer-side)", "q_adj_kwh", "flow"),
    ("EVN retail shortfall", "shortfall_kwh", "flow"),
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
    assumptions = assumptions or {}
    dppa_config = _active_dppa_config(assumptions)
    cash_flow_columns = (
        CASH_FLOW_COLUMNS + DPPA_CASH_FLOW_EXTRA_COLUMNS
        if dppa_config is not None
        else CASH_FLOW_COLUMNS
    )

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
        cash_flow_columns,
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
    _write_assumptions_sheet(workbook.create_sheet("Assumptions"), assumptions)

    if dppa_config is not None:
        _write_key_value_sheet(
            workbook.create_sheet("DPPA Configuration"),
            DPPA_CONFIG_ROWS,
            dppa_config,
        )
        _write_table_sheet(
            workbook.create_sheet("Hourly Settlement"),
            DPPA_HOURLY_COLUMNS,
            report_data.get("dppa_hourly_breakout", []),
        )
        _write_table_sheet(
            workbook.create_sheet("Monthly Settlement"),
            DPPA_MONTHLY_COLUMNS,
            report_data.get("dppa_monthly_breakout", []),
        )
        _write_table_sheet(
            workbook.create_sheet("DPPA Annual Summary"),
            DPPA_ANNUAL_COLUMNS,
            cash_flow_result.get("annual_cash_flows", []),
        )
        _write_bau_vs_dppa_sheet(
            workbook.create_sheet("Year 1 BAU vs DPPA"),
            cash_flow_result,
            report_data,
            assumptions,
        )

    for worksheet in workbook.worksheets:
        _autosize_columns(worksheet)

    return workbook


def _write_bau_vs_dppa_sheet(worksheet, cash_flow_result, report_data, assumptions):
    annual_rows = cash_flow_result.get("annual_cash_flows", []) or [{}]
    year_one = annual_rows[0]
    hourly = report_data.get("dppa_hourly_breakout", []) or []
    annual_production = report_data.get("annual_production") or {}

    def g(key):
        return year_one.get(key, 0.0) or 0.0

    bau_evn_bill_usd = g("bau_evn_bill_usd")
    c_dn_usd = g("c_dn_usd")
    c_dppa_usd = g("c_dppa_usd")
    c_cl_usd = g("c_cl_usd")
    c_bl_usd = g("c_bl_usd")
    cfd_net_usd = g("cfd_net_usd")
    esco_demand_revenue_usd = g("esco_demand_revenue_usd")
    esco_grid_arb_usd = g("esco_grid_arbitrage_revenue_usd")
    gen_fmp_usd = g("generator_fmp_revenue_usd")
    offtaker_post_cost_usd = g("offtaker_post_project_cost_usd")
    optimized_demand_charge_year_usd = g("optimized_demand_charge_usd")

    buyer_savings_usd = bau_evn_bill_usd - offtaker_post_cost_usd
    buyer_savings_fraction = (
        buyer_savings_usd / bau_evn_bill_usd if bau_evn_bill_usd else None
    )

    total_seller_revenue_usd = gen_fmp_usd + cfd_net_usd + esco_demand_revenue_usd + esco_grid_arb_usd

    # Energy flows from annual_production (if present) else sum from hourly.
    def _sum_hourly(key):
        return sum(row.get(key, 0.0) or 0.0 for row in hourly)

    pv_to_load_kwh = annual_production.get("pv_to_load_kwh") or 0.0
    pv_to_storage_kwh = annual_production.get("pv_to_storage_kwh") or 0.0
    storage_to_load_kwh = annual_production.get("storage_to_load_kwh") or 0.0
    pv_to_grid_effective_kwh = annual_production.get("pv_to_grid_effective_kwh") or 0.0
    q_re_meter_kwh = _sum_hourly("q_re_meter_kw")
    q_adj_kwh = sum((row.get("q_adj_kw") or row.get("q_re_meter_kw", 0.0) / (1.026 * 1.027263)) for row in hourly)
    shortfall_kwh = sum(max((row.get("load_kw", 0.0) or 0.0) - (row.get("q_adj_kw", 0.0) or 0.0), 0.0) for row in hourly)

    values = {
        "bau_evn_bill_usd": bau_evn_bill_usd,
        "c_dn_usd": c_dn_usd,
        "c_dppa_usd": c_dppa_usd,
        "c_cl_usd": c_cl_usd,
        "c_bl_usd": c_bl_usd,
        "cfd_net_usd": cfd_net_usd,
        "optimized_demand_charge_year_usd": optimized_demand_charge_year_usd,
        "esco_demand_revenue_usd": esco_demand_revenue_usd,
        "total_buyer_outflow_usd": offtaker_post_cost_usd,
        "buyer_savings_vs_bau_usd": buyer_savings_usd,
        "buyer_savings_fraction": buyer_savings_fraction,
        "esco_phase2_energy_revenue_usd": 0.0,  # zeroed under DPPA per design doc
        "generator_fmp_revenue_usd": gen_fmp_usd,
        "esco_grid_arbitrage_revenue_usd": esco_grid_arb_usd,
        "total_seller_revenue_usd": total_seller_revenue_usd,
        "pv_to_load_kwh": pv_to_load_kwh,
        "pv_to_storage_kwh": pv_to_storage_kwh,
        "pv_to_grid_effective_kwh": pv_to_grid_effective_kwh,
        "storage_to_load_kwh": storage_to_load_kwh,
        "q_re_meter_kwh": q_re_meter_kwh,
        "q_adj_kwh": q_adj_kwh,
        "shortfall_kwh": shortfall_kwh,
    }

    worksheet.cell(row=1, column=1, value="Line Item").font = HEADER_FONT
    worksheet.cell(row=1, column=2, value="Year 1 (USD)").font = HEADER_FONT
    worksheet.cell(row=1, column=3, value="Side").font = HEADER_FONT

    row_index = 2
    for label, key, side in BAU_VS_DPPA_ROWS:
        if label == "section":
            worksheet.cell(row=row_index, column=1, value=key).font = HEADER_FONT
            worksheet.cell(row=row_index, column=1).fill = HEADER_FILL
            row_index += 1
            continue
        worksheet.cell(row=row_index, column=1, value=label)
        worksheet.cell(row=row_index, column=2, value=values.get(key))
        worksheet.cell(row=row_index, column=3, value=side)
        row_index += 1

    worksheet.column_dimensions["A"].width = 48
    worksheet.column_dimensions["B"].width = 20
    worksheet.column_dimensions["C"].width = 14


def _active_dppa_config(assumptions):
    dppa = assumptions.get("dppa") if assumptions else None
    if not dppa or dppa.get("type", "none") == "none":
        return None
    return dppa


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

    flat = {
        key: value
        for key, value in assumptions.items()
        if not isinstance(value, (dict, list))
    }
    for row_index, (key, value) in enumerate(flat.items(), start=2):
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
