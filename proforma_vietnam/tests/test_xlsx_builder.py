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
        self.assertIn("PV Irradiation (W/m²)", headers)
        self.assertNotIn("PV Production Factor (kWh/kW) — irradiation proxy", headers)
        self.assertIn("PV to Storage (kW)", headers)
        self.assertIn("Grid to Storage (kW)", headers)
        self.assertEqual(dispatch["A2"].value, 1)
        # Column C carries the raw PVWatts irradiance (W/m2).
        self.assertEqual(dispatch["C2"].value, 300)
        # Charging flows are shown negative (PV to Storage col F, Grid to Storage col J).
        self.assertEqual(dispatch["F2"].value, -1)
        self.assertEqual(dispatch["J3"].value, -1)

        self.assertEqual(len(dispatch._charts), 1)
        chart = dispatch._charts[0]
        self.assertIn("Peak-Load Week", chart.title.tx.rich.p[0].r[0].t)
        # The PV-to-Storage line (column F) is charted so the charging dip shows.
        val_refs = [series.val.numRef.ref for series in chart.series]
        self.assertTrue(any("$F$" in ref for ref in val_refs), val_refs)
        # chart spans at most one week of rows, not the whole series
        values_ref = chart.series[0].val.numRef.ref
        first, last = values_ref.split("!")[1].split(":")
        span = int("".join(ch for ch in last if ch.isdigit())) - int(
            "".join(ch for ch in first if ch.isdigit())
        ) + 1
        self.assertLessEqual(span, 168)

        self.assertEqual(workbook["Load Duration"]["B2"].value, 20)
        self.assertGreater(len(workbook["Load Duration"]._charts), 0)

    def test_technical_results_has_solar_resource_section(self):
        workbook = build_vietnam_esco_workbook(
            _cash_flow_result(),
            report_data=_report_data(),
        )

        sheet = workbook["Technical Results"]
        labels = {
            sheet.cell(row=row, column=1).value: sheet.cell(row=row, column=2)
            for row in range(1, sheet.max_row + 1)
        }
        self.assertIn("Solar Resource (Year 1)", labels)
        self.assertEqual(
            labels["Annual POA Irradiation (kWh/m²)"].value, 1650.0
        )
        pr_cell = labels["Performance Ratio (Year 1)"]
        self.assertEqual(pr_cell.value, 0.81)
        self.assertEqual(pr_cell.number_format, "0.0%")

    def test_report_contains_no_em_dash(self):
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
                "dppa": {"type": "grid_dppa_cfd"},
            },
            report_data=_report_data(),
        )

        for worksheet in workbook.worksheets:
            for row in worksheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str):
                        self.assertNotIn("—", cell.value, f"{worksheet.title}!{cell.coordinate}")


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

class BatterySohSheetTests(TestCase):
    """A 'Battery SOH' sheet with the curve appears only when the cash flow
    carries a battery_fade block."""

    def _with_fade(self):
        from proforma_vietnam.tests.test_audit_sheets import _esco_result, _fade_block
        return _esco_result(battery_fade=_fade_block())

    def test_sheet_present_only_with_a_fade_block(self):
        plain = build_vietnam_esco_workbook(_cash_flow_result_with_derivation(), {})
        self.assertNotIn("Battery SOH", plain.sheetnames)
        cover = [str(c.value) for c in plain["Cover"]["B"]]
        self.assertNotIn("Battery SOH", cover)

        faded = build_vietnam_esco_workbook(self._with_fade(), {"bess_cycle_life_efc": 8000})
        self.assertIn("Battery SOH", faded.sheetnames)
        self.assertEqual(
            faded.sheetnames.index("Battery SOH"),
            faded.sheetnames.index("Technical Results") + 1,
        )
        sheet = faded["Battery SOH"]
        text = [str(c.value) for row in sheet.iter_rows() for c in row if c.value is not None]
        self.assertTrue(any("8,000" in t for t in text))
        self.assertTrue(any("h = 1" in t or "hours-per-time-step" in t for t in text))
        self.assertEqual(len(sheet._charts), 1)
        cover = [str(c.value) for c in faded["Cover"]["B"]]
        self.assertIn("Battery SOH", cover)
        for value in text:
            self.assertNotIn("\u2014", value)

    def test_year_rows_and_loss_column(self):
        result = self._with_fade()
        faded = build_vietnam_esco_workbook(result, {"bess_cycle_life_efc": 8000})
        sheet = faded["Battery SOH"]
        header_row = next(
            r for r in range(1, sheet.max_row + 1) if sheet.cell(row=r, column=1).value == "Year"
        )
        headers = [sheet.cell(row=header_row, column=c).value for c in range(1, 11)]
        self.assertEqual(headers[1], "SOH end of year")
        self.assertEqual(headers[8], "Value lost to fade if derated (USD)")
        self.assertEqual(headers[9], "Augmentation cost if augmented (USD)")
        self.assertEqual(sheet.cell(row=header_row + 1, column=1).value, 0)
        self.assertEqual(sheet.cell(row=header_row + 1, column=2).value, 1.0)
        years = len(result["annual_cash_flows"])
        self.assertEqual(sheet.cell(row=header_row + 1 + years, column=1).value, years)
        self.assertAlmostEqual(
            sheet.cell(row=header_row + 1 + years, column=9).value,
            result["annual_cash_flows"][-1]["battery_fade_loss_usd"],
        )
        # end-of-life reference series for the chart
        self.assertEqual(sheet.cell(row=header_row + 1, column=11).value, 0.8)

    def test_treatment_is_stated_and_both_figures_are_shown(self):
        from proforma_vietnam.tests.test_audit_sheets import _esco_result, _fade_block
        derate_fade = _fade_block()
        derate_fade.update(treatment="derate", augmentation_cost_by_year_vnd=[5.0] * 20,
                           augmentation_price_per_kwh_vnd=120.0,
                           augmentation_price_declination_rate=0.03)
        augment_fade = dict(derate_fade, treatment="augment")
        derate = build_vietnam_esco_workbook(_esco_result(battery_fade=derate_fade),
                                             {"bess_cycle_life_efc": 8000})["Battery SOH"]
        augment = build_vietnam_esco_workbook(_esco_result(battery_fade=augment_fade),
                                              {"bess_cycle_life_efc": 8000})["Battery SOH"]

        def labels(sheet):
            return {str(sheet.cell(row=r, column=1).value): sheet.cell(row=r, column=2).value
                    for r in range(1, sheet.max_row + 1)}

        d, a = labels(derate), labels(augment)
        self.assertEqual(d["Ageing treatment"], "derate: the battery's savings are multiplied by the year-average SOH")
        self.assertEqual(a["Ageing treatment"], "augment: capacity kept at nominal, the daily top-up booked as an operating cost")
        self.assertAlmostEqual(d["Augmentation cost over the horizon, not booked (USD)"], 100.0)
        self.assertAlmostEqual(a["Augmentation cost over the horizon, booked (USD)"], 100.0)
        self.assertIn("Value lost to fade over the horizon, booked (USD)", d)
        self.assertIn("Value lost to fade over the horizon, avoided by augmentation (USD)", a)
        self.assertAlmostEqual(d["Augmentation price (USD/kWh, year 1; declining 3.0 percent a year)"], 120.0)
        header_row = next(
            r for r in range(1, augment.max_row + 1) if augment.cell(row=r, column=1).value == "Year"
        )
        self.assertEqual(augment.cell(row=header_row + 2, column=10).value, 5.0)
        self.assertEqual(augment.cell(row=header_row + 1, column=10).value, 0.0)

    def test_key_results_block(self):
        faded = build_vietnam_esco_workbook(self._with_fade(), {"bess_cycle_life_efc": 8000})
        sheet = faded["Battery SOH"]
        labels = {
            str(sheet.cell(row=r, column=1).value): sheet.cell(row=r, column=2).value
            for r in range(1, sheet.max_row + 1)
        }
        self.assertAlmostEqual(labels["SOH end of year 10"], 1.0 - 0.01 * 9)
        self.assertEqual(labels["First year below 80 percent"], "Not within the 20 year horizon")
        self.assertAlmostEqual(labels["Equivalent full cycles, year 1"], 300.0)


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


def build_direct_ownership_cash_flow_result(**overrides):
    # Factory self-invest (DIRECT_OWNERSHIP) with the surplus leg enabled, so
    # callers exercise the live bill-savings formula, the shared surplus
    # cells, and the flat-CIT (profitable-host) row. This mirrors
    # test_audit_sheets._direct_result(), which delegates here so the
    # fixture is defined once instead of duplicated across test modules.
    # The 14 base cash-flow kwargs live in test_audit_sheets._esco_result;
    # only the direct-ownership overrides are defined here. Callers may pass
    # further overrides (e.g. debt_currency="USD") on top of these.
    from proforma_vietnam.tests.test_audit_sheets import _esco_result

    kwargs = dict(
        direct_ownership={},
        surplus_export_kwh_year1=500000.0,
        surplus_export_price_usd_per_kwh=0.04,
        surplus_price_escalation_rate=0.04,
        surplus_cap_fraction=0.5,
    )
    kwargs.update(overrides)
    return _esco_result(**kwargs)


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
        "solar_resource": {
            "annual_poa_irradiation_kwh_per_m2": 1650.0,
            "performance_ratio": 0.81,
        },
        "dispatch_profile": [
            {
                "hour": 1,
                "load_kw": 10,
                "pv_irradiance": 300,
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
                "pv_irradiance": 600,
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
