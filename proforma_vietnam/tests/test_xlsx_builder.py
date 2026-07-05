from unittest import TestCase

from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook


class VietnamXlsxBuilderTests(TestCase):

    def test_builds_required_workbook_sheets(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={"esco_energy_discount_fraction": 0.9},
        )

        self.assertEqual(
            workbook.sheetnames,
            [
                "Cover",
                "Executive Summary",
                "Assumptions",
                "Model Basis",
                "Buyer Analysis",
                "Developer Returns",
                "Technical Results",
                "Dispatch Profile",
                "Load Duration",
            ],
        )

    def test_adds_audit_and_fx_sheets_when_derivation_present(self):
        cash_flow = _cash_flow_result_with_derivation()
        workbook = build_vietnam_esco_workbook(
            cash_flow,
            assumptions={"esco_energy_discount_fraction": 0.9},
        )

        self.assertIn("Pro Forma (Audit)", workbook.sheetnames)
        self.assertIn("FX Sensitivity", workbook.sheetnames)
        # audit sheets come right after Model Basis in the reading flow
        self.assertLess(
            workbook.sheetnames.index("Model Basis"),
            workbook.sheetnames.index("Pro Forma (Audit)"),
        )

    def test_technical_results_consolidates_sizing_production_and_bills(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(), report_data=_report_data()
        )
        sheet = workbook["Technical Results"]

        values_by_label = {
            sheet.cell(row=row, column=1).value: sheet.cell(row=row, column=2).value
            for row in range(1, sheet.max_row + 1)
            if sheet.cell(row=row, column=1).value
        }

        self.assertIn("System Sizing", values_by_label)
        self.assertIn("Annual Energy Balance (Year 1)", values_by_label)
        self.assertIn("Year-1 Utility Bill Comparison", values_by_label)
        self.assertEqual(values_by_label["PV Size (kW)"], 100)
        self.assertEqual(values_by_label["Battery Energy (kWh)"], 200)
        self.assertEqual(values_by_label["PV to Load (kWh)"], 80)
        self.assertEqual(values_by_label["BAU Utility Bill (USD)"], 100000)
        self.assertGreater(len(sheet._charts), 0)

    def test_writes_assumptions(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={
                "esco_energy_discount_fraction": 0.9,
                "evn_energy_escalation_rate": 0.04,
            },
        )

        assumptions = workbook["Assumptions"]
        values_by_label = {
            assumptions.cell(row=row, column=2).value: assumptions.cell(row=row, column=3).value
            for row in range(1, assumptions.max_row + 1)
        }

        self.assertEqual(
            values_by_label["ESCO energy price (fraction of EVN tariff)"], 0.9
        )
        self.assertEqual(values_by_label["EVN energy escalation"], 0.04)

    def test_dispatch_sheet_has_generation_split_and_peak_week_chart(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            report_data=_report_data(),
        )

        dispatch = workbook["Dispatch Profile"]
        headers = [
            dispatch.cell(row=1, column=col).value
            for col in range(1, dispatch.max_column + 1)
        ]
        self.assertIn("PV Generation Total (kW)", headers)
        self.assertIn("PV Production Factor (kWh/kW) — irradiation proxy", headers)
        self.assertIn("PV to Storage (kW)", headers)
        self.assertIn("Grid to Storage (kW)", headers)
        self.assertEqual(dispatch["A2"].value, 1)

        self.assertEqual(len(dispatch._charts), 1)
        chart = dispatch._charts[0]
        self.assertIn("Peak-Load Week", chart.title.tx.rich.p[0].r[0].t)
        # chart spans at most one week of rows, not the whole series
        values_ref = chart.series[0].val.numRef.ref
        first, last = values_ref.split("!")[1].split(":")
        span = int("".join(ch for ch in last if ch.isdigit())) - int(
            "".join(ch for ch in first if ch.isdigit())
        ) + 1
        self.assertLessEqual(span, 168)

        self.assertEqual(workbook["Load Duration"]["B2"].value, 20)
        self.assertGreater(len(workbook["Load Duration"]._charts), 0)


    def test_executive_summary_presents_both_sides_kpis(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={"esco_energy_discount_fraction": 0.9},
            report_data=_report_data(),
        )

        sheet = workbook["Executive Summary"]
        labels = {
            sheet.cell(row=row, column=2).value: sheet.cell(row=row, column=3)
            for row in range(1, sheet.max_row + 1)
        }

        self.assertIn("Equity IRR", labels)
        self.assertEqual(labels["Equity IRR"].value, 0.14)
        self.assertEqual(labels["Equity IRR"].number_format, "0.0%")
        self.assertIn("Total Investment (USD)", labels)
        self.assertEqual(labels["Total Investment (USD)"].value, 1000000)
        self.assertEqual(labels["Total Investment (USD)"].number_format, "#,##0")
        self.assertIn("Year 1 Buyer Savings (USD)", labels)
        self.assertEqual(labels["Year 1 Buyer Savings (USD)"].value, 50000)

    def test_buyer_analysis_has_annual_savings_table_with_cumulative_column(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={"esco_energy_discount_fraction": 0.9},
            report_data=_report_data(),
        )

        sheet = workbook["Buyer Analysis"]
        headers = [
            sheet.cell(row=row, column=1).value
            for row in range(1, sheet.max_row + 1)
        ]
        self.assertIn("Year", headers)
        header_row = headers.index("Year") + 1
        year_headers = [
            sheet.cell(row=header_row, column=col).value
            for col in range(1, sheet.max_column + 1)
        ]
        self.assertIn("BAU Cost (USD)", year_headers)
        self.assertIn("Cost With Project (USD)", year_headers)
        self.assertIn("Savings (USD)", year_headers)
        self.assertIn("Cumulative Savings (USD)", year_headers)

    def test_developer_returns_sheet_has_kpis_and_annual_equity_cash_flow(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={"esco_energy_discount_fraction": 0.9},
            report_data=_report_data(),
        )

        sheet = workbook["Developer Returns"]
        values = [
            sheet.cell(row=row, column=2).value
            for row in range(1, sheet.max_row + 1)
        ]
        self.assertIn("Minimum DSCR (debt years)", values)
        self.assertIn("Equity IRR", values)
        headers_anywhere = []
        for row in range(1, sheet.max_row + 1):
            for col in range(1, sheet.max_column + 1):
                headers_anywhere.append(sheet.cell(row=row, column=col).value)
        self.assertIn("Equity Cash Flow (USD)", headers_anywhere)
        self.assertIn("Cumulative Equity CF (USD)", headers_anywhere)

    def test_omits_dppa_sheets_when_dppa_type_is_none_or_missing(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            assumptions={"esco_energy_discount_fraction": 0.9},
        )

        self.assertNotIn("Hourly Settlement", workbook.sheetnames)
        self.assertNotIn("Monthly Settlement", workbook.sheetnames)
        self.assertNotIn("Year 1 BAU vs DPPA", workbook.sheetnames)

    def test_adds_settlement_sheets_when_dppa_type_is_grid_dppa_cfd(self):
        cash_flow = _cash_flow_result()
        cash_flow["annual_cash_flows"][0].update({
            "c_dn_vnd": 100.0,
            "c_dppa_vnd": 20.0,
            "c_cl_vnd": 10.0,
            "c_bl_vnd": 40.0,
            "cfd_net_vnd": 5.0,
            "generator_revenue_vnd": 150.0,
            "dppa_offtaker_cost_vnd": 175.0,
        })
        workbook = build_vietnam_esco_workbook(
            cash_flow,
            assumptions={
                "esco_energy_discount_fraction": 0.9,
                "dppa": {
                    "type": "grid_dppa_cfd",
                    "cfd_strike_per_kwh_vnd": 1700.0,
                    "cfd_contract_volume_kwh_per_hour": 80.0,
                    "transmission_loss_factor_k": 1.026,
                    "distribution_loss_factor_kpp": 1.027263,
                    "allocation_fraction_delta": 1.0,
                    "c_dppa_service_fee_vnd_per_kwh": 360.0,
                    "c_cl_settlement_adder_vnd_per_kwh": 163.0,
                    "fmp_series_path": "DPPA DOC/fmp_cfmp_vn.json",
                },
            },
            report_data={
                "dppa_hourly_breakout": [
                    {
                        "hour": 1, "load_kw": 100.0, "q_re_meter_kw": 80.0,
                        "q_re_delivered_kw": 80.0, "q_adj_kw": 75.9,
                        "q_khc_kw": 75.9,
                        "fmp_vnd_per_kwh": 1500.0, "c_dn_vnd": 113850.0,
                        "c_dppa_vnd": 27324.0, "c_cl_vnd": 12372.0,
                        "c_bl_vnd": 48200.0, "cfd_payment_vnd": 16000.0,
                    },
                ],
                "dppa_monthly_breakout": [
                    {"month": 1, "c_dn_vnd": 100.0, "c_dppa_vnd": 20.0, "c_cl_vnd": 10.0,
                     "c_bl_vnd": 40.0, "cfd_net_vnd": 5.0, "generator_revenue_vnd": 150.0,
                     "customer_total_vnd": 175.0},
                ],
            },
        )

        self.assertIn("Hourly Settlement", workbook.sheetnames)
        self.assertIn("Monthly Settlement", workbook.sheetnames)
        self.assertIn("Year 1 BAU vs DPPA", workbook.sheetnames)
        # config + per-year DPPA lines are consolidated into Assumptions and
        # the Pro Forma (Audit) sheet
        self.assertNotIn("DPPA Configuration", workbook.sheetnames)
        self.assertNotIn("DPPA Annual Summary", workbook.sheetnames)

        hourly = workbook["Hourly Settlement"]
        self.assertEqual(hourly.cell(row=1, column=1).value, "Hour")
        self.assertEqual(hourly.cell(row=2, column=1).value, 1)
        headers = [hourly.cell(row=1, column=col).value
                   for col in range(1, hourly.max_column + 1)]
        self.assertIn("Q_Khc (kW)", headers)
        c_dn_column = headers.index("C_DN (VND)") + 1
        self.assertEqual(hourly.cell(row=2, column=c_dn_column).value, 113850.0)

        monthly = workbook["Monthly Settlement"]
        self.assertEqual(monthly.cell(row=1, column=1).value, "Month")
        self.assertEqual(monthly.cell(row=2, column=2).value, 100.0)

def _cash_flow_result_with_derivation():
    from proforma_vietnam.cash_flow import calculate_vietnam_esco_cash_flow

    return calculate_vietnam_esco_cash_flow(
        project_served_pv_kwh=[1000.0],
        evn_energy_rates_vnd_per_kwh=[0.08],
        bau_evn_bill_vnd=900000,
        optimized_evn_bill_vnd=630000,
        bau_demand_charge_vnd=180000,
        optimized_demand_charge_vnd=120000,
        pv_capex_vnd=2100000,
        bess_capex_vnd=900000,
        annual_om_vnd=45000,
        esco_energy_discount_fraction=0.9,
        exchange_rate_vnd_per_usd=25000,
    )


def _cash_flow_result():
    return {
        "summary": {
            "total_capex_vnd": 1000000,
            "debt_principal_vnd": 700000,
            "equity_investment_vnd": 300000,
            "project_irr_fraction": 0.12,
            "equity_irr_fraction": 0.14,
            "npv_vnd": 123456,
            "average_dscr": 1.3,
            "simple_payback_years": 7.5,
            "roi_fraction": 1.8,
        },
        "annual_cash_flows": [
            {
                "year": 1,
                "esco_energy_revenue_vnd": 200000,
                "esco_demand_revenue_vnd": 80000,
                "esco_grid_arbitrage_revenue_vnd": 0,
                "esco_revenue_vnd": 280000,
                "annual_om_vnd": 30000,
                "replacement_cost_vnd": 0,
                "depreciation_vnd": 40000,
                "cit_vnd": 0,
                "cash_available_for_debt_service_vnd": 250000,
                "debt_service_vnd": 110000,
                "principal_vnd": 50000,
                "interest_vnd": 60000,
                "ending_debt_balance_vnd": 640000,
                "equity_cash_flow_vnd": 140000,
                "offtaker_savings_vnd": 50000,
                "offtaker_savings_fraction": 0.05,
                "dscr": 2.27,
            }
        ],
    }


def _report_data():
    return {
        "system_sizing": {
            "pv_kw": 100,
            "battery_kw": 50,
            "battery_kwh": 200,
        },
        "results_comparison": {
            "bau_utility_bill_vnd": 100000,
            "optimized_utility_bill_vnd": 70000,
            "utility_bill_savings_vnd": 30000,
            "demand_charge_savings_vnd": 8000,
        },
        "annual_production": {
            "grid_to_load_kwh": 100,
            "pv_to_load_kwh": 80,
            "pv_to_storage_kwh": 20,
            "storage_to_load_kwh": 15,
            "pv_curtailed_kwh": 5,
            "grid_to_storage_kwh": 0,
        },
        "dispatch_profile": [
            {
                "hour": 1,
                "load_kw": 10,
                "pv_production_factor": 0.2,
                "pv_total_kw": 4,
                "pv_to_load_kw": 3,
                "pv_to_storage_kw": 1,
                "pv_to_grid_kw": 0,
                "pv_curtailed_kw": 0,
                "grid_to_load_kw": 7,
                "grid_to_storage_kw": 0,
                "storage_to_load_kw": 0,
            },
            {
                "hour": 2,
                "load_kw": 20,
                "pv_production_factor": 0.5,
                "pv_total_kw": 7,
                "pv_to_load_kw": 4,
                "pv_to_storage_kw": 2,
                "pv_to_grid_kw": 0,
                "pv_curtailed_kw": 1,
                "grid_to_load_kw": 8,
                "grid_to_storage_kw": 1,
                "storage_to_load_kw": 1,
            },
        ],
        "load_duration": [
            {"rank": 1, "load_kw": 20, "net_load_kw": 8},
            {"rank": 2, "load_kw": 10, "net_load_kw": 7},
        ],
        "developer_financial_performance": {
            "project_irr_fraction": 0.12,
            "equity_irr_fraction": 0.14,
            "npv_vnd": 123456,
            "average_dscr": 1.3,
            "simple_payback_years": 7.5,
            "roi_fraction": 1.8,
        },
    }
