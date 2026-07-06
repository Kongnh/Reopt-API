from unittest import TestCase

from proforma_vietnam import proforma_schema as schema
from proforma_vietnam.cash_flow import calculate_vietnam_esco_cash_flow
from proforma_vietnam.structures import DIRECT_OWNERSHIP, DPPA, ESCO, PHYSICAL_DPPA


def _esco_result():
    # Surplus export enabled so the ESCO-scoped surplus lines the schema now
    # presents (surplus_export_kwh / surplus_export_revenue) exist in the
    # compute output the single-source-of-truth test checks against. The Task 4e
    # contract tenor is enabled too (contract_years == project_years, so no
    # truncation) so the ESCO-scoped asset_transfer_proceeds line the schema now
    # presents also exists in the compute output.
    return calculate_vietnam_esco_cash_flow(
        project_served_pv_kwh=[1000, 1000],
        evn_energy_rates_vnd_per_kwh=[2000, 2000],
        bau_evn_bill_vnd=5_000_000,
        optimized_evn_bill_vnd=3_000_000,
        bau_demand_charge_vnd=1_000_000,
        optimized_demand_charge_vnd=600_000,
        pv_capex_vnd=10_000_000,
        bess_capex_vnd=4_000_000,
        annual_om_vnd=200_000,
        esco_energy_discount_fraction=0.9,
        debt_fraction=0.7,
        debt_term_years=2,
        project_years=2,
        surplus_export_kwh_year1=5_000,
        surplus_export_price_usd_per_kwh=1_000,
        contract_years=2,
        contract_residual_value_usd=1_000_000,
    )


def _dppa_result():
    return calculate_vietnam_esco_cash_flow(
        project_served_pv_kwh=[1000, 1000],
        evn_energy_rates_vnd_per_kwh=[2000, 2000],
        bau_evn_bill_vnd=5_000_000,
        optimized_evn_bill_vnd=3_000_000,
        bau_demand_charge_vnd=1_000_000,
        optimized_demand_charge_vnd=600_000,
        pv_capex_vnd=10_000_000,
        bess_capex_vnd=4_000_000,
        annual_om_vnd=200_000,
        esco_energy_discount_fraction=0.9,
        debt_fraction=0.7,
        project_years=2,
        dppa_settlement={
            "type": "grid_dppa_cfd",
            "esco_energy_revenue_vnd": 0.0,
            "year_one": {
                "c_dn_vnd": 500_000.0,
                "c_dppa_vnd": 100_000.0,
                "c_cl_vnd": 50_000.0,
                "c_bl_vnd": 200_000.0,
                "cfd_strike_revenue_vnd": 170_000.0,
                "cfd_fmp_offset_vnd": 150_000.0,
                "generator_fmp_revenue_vnd": 500_000.0,
            },
            "escalation": {"fee_escalation_rate": 0.0, "cfd_strike_escalation_rate": 0.0},
            "hourly_breakout": [],
            "monthly_breakout": [],
        },
    )


def _physical_result():
    # Physical private-wire DPPA with surplus enabled so the PHYSICAL-scoped
    # PPA lines and the surplus lines the schema presents both exist in the
    # compute output the single-source-of-truth test checks against.
    return calculate_vietnam_esco_cash_flow(
        project_served_pv_kwh=[1000, 1000],
        evn_energy_rates_vnd_per_kwh=[2000, 2000],
        bau_evn_bill_vnd=5_000_000,
        optimized_evn_bill_vnd=3_000_000,
        bau_demand_charge_vnd=1_000_000,
        optimized_demand_charge_vnd=600_000,
        pv_capex_vnd=10_000_000,
        bess_capex_vnd=4_000_000,
        annual_om_vnd=200_000,
        esco_energy_discount_fraction=0.9,
        debt_fraction=0.7,
        project_years=2,
        physical_dppa={
            "matched_kwh_year1": 2000.0,
            "ppa_price_usd_per_kwh": 1500.0,
            "ppa_price_escalation_rate": 0.0,
        },
        surplus_export_kwh_year1=5_000,
        surplus_export_price_usd_per_kwh=1_000,
    )


def _direct_result():
    # Factory self-invest with surplus enabled so the DIRECT-scoped bill-savings
    # line and the surplus lines the schema presents both exist in the compute
    # output the single-source-of-truth test checks against.
    return calculate_vietnam_esco_cash_flow(
        project_served_pv_kwh=[1000, 1000],
        evn_energy_rates_vnd_per_kwh=[2000, 2000],
        bau_evn_bill_vnd=5_000_000,
        optimized_evn_bill_vnd=3_000_000,
        bau_demand_charge_vnd=1_000_000,
        optimized_demand_charge_vnd=600_000,
        pv_capex_vnd=10_000_000,
        bess_capex_vnd=4_000_000,
        annual_om_vnd=200_000,
        esco_energy_discount_fraction=0.9,
        debt_fraction=0.7,
        project_years=2,
        direct_ownership={},
        surplus_export_kwh_year1=5_000,
        surplus_export_price_usd_per_kwh=1_000,
    )


# Per-year sheet views are validated against an annual cash-flow row; summary
# views against the summary dict.
ANNUAL_VIEWS = [
    schema.CASH_FLOW_VIEW,
    schema.TAX_SCHEDULE_VIEW,
    schema.DEBT_SERVICE_VIEW,
    schema.DPPA_ANNUAL_VIEW,
]
SUMMARY_VIEWS = [schema.SUMMARY_VIEW, schema.DEVELOPER_FINANCIAL_VIEW]


class ProformaSchemaStructureTests(TestCase):
    def test_every_view_key_is_a_registered_rowspec(self):
        for view in ANNUAL_VIEWS + SUMMARY_VIEWS:
            for key in view:
                self.assertIn(key, schema.PROFORMA_ROWS, f"unregistered view key: {key}")


class SchemaIsSingleSourceOfTruthTests(TestCase):
    """Every key the schema presents must exist in the compute output, so a
    label/key rename can no longer silently resolve to None in the workbook."""

    def _assert_view_keys_present(self, view, structure, container):
        for _label, key in schema.columns(view, structure):
            self.assertIn(
                key,
                container,
                f"schema presents '{key}' for {structure} but compute did not emit it",
            )

    def test_esco_presented_keys_exist_in_compute_output(self):
        result = _esco_result()
        annual = result["annual_cash_flows"][0]
        summary = result["summary"]
        for view in ANNUAL_VIEWS:
            self._assert_view_keys_present(view, ESCO, annual)
        for view in SUMMARY_VIEWS:
            self._assert_view_keys_present(view, ESCO, summary)

    def test_dppa_presented_keys_exist_in_compute_output(self):
        result = _dppa_result()
        annual = result["annual_cash_flows"][0]
        summary = result["summary"]
        for view in ANNUAL_VIEWS:
            self._assert_view_keys_present(view, DPPA, annual)
        for view in SUMMARY_VIEWS:
            self._assert_view_keys_present(view, DPPA, summary)

    def test_physical_dppa_presented_keys_exist_in_compute_output(self):
        result = _physical_result()
        annual = result["annual_cash_flows"][0]
        summary = result["summary"]
        for view in ANNUAL_VIEWS:
            self._assert_view_keys_present(view, PHYSICAL_DPPA, annual)
        for view in SUMMARY_VIEWS:
            self._assert_view_keys_present(view, PHYSICAL_DPPA, summary)

    def test_direct_ownership_presented_keys_exist_in_compute_output(self):
        result = _direct_result()
        annual = result["annual_cash_flows"][0]
        summary = result["summary"]
        for view in ANNUAL_VIEWS:
            self._assert_view_keys_present(view, DIRECT_OWNERSHIP, annual)
        for view in SUMMARY_VIEWS:
            self._assert_view_keys_present(view, DIRECT_OWNERSHIP, summary)


class StructureFilteringTests(TestCase):
    def test_dppa_only_lines_are_hidden_under_esco(self):
        esco_keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, ESCO)}
        self.assertNotIn("generator_revenue_usd", esco_keys)
        self.assertNotIn("dppa_offtaker_cost_usd", esco_keys)

    def test_dppa_only_lines_appear_under_dppa(self):
        dppa_keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, DPPA)}
        self.assertIn("generator_revenue_usd", dppa_keys)
        self.assertIn("dppa_offtaker_cost_usd", dppa_keys)

    def test_surplus_export_lines_appear_under_esco_only(self):
        esco_keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, ESCO)}
        self.assertIn("surplus_export_kwh", esco_keys)
        self.assertIn("surplus_export_revenue_usd", esco_keys)

    def test_surplus_export_lines_are_hidden_under_dppa(self):
        dppa_keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, DPPA)}
        self.assertNotIn("surplus_export_kwh", dppa_keys)
        self.assertNotIn("surplus_export_revenue_usd", dppa_keys)

    def test_physical_ppa_lines_appear_under_physical_only(self):
        physical_keys = {
            key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, PHYSICAL_DPPA)
        }
        self.assertIn("ppa_matched_kwh", physical_keys)
        self.assertIn("ppa_energy_revenue_usd", physical_keys)
        # The physical private wire presents its PPA line, not the ESCO line.
        self.assertNotIn("esco_energy_revenue_usd", physical_keys)
        # Surplus rides on the physical private wire too.
        self.assertIn("surplus_export_kwh", physical_keys)
        self.assertIn("surplus_export_revenue_usd", physical_keys)

    def test_physical_ppa_lines_are_hidden_under_esco_and_dppa(self):
        for structure in (ESCO, DPPA):
            keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, structure)}
            self.assertNotIn("ppa_matched_kwh", keys)
            self.assertNotIn("ppa_energy_revenue_usd", keys)

    def test_cfd_only_lines_are_hidden_under_physical(self):
        physical_keys = {
            key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, PHYSICAL_DPPA)
        }
        self.assertNotIn("generator_revenue_usd", physical_keys)
        self.assertNotIn("dppa_offtaker_cost_usd", physical_keys)

    def test_bill_savings_line_appears_under_direct_ownership_only(self):
        direct_keys = {
            key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, DIRECT_OWNERSHIP)
        }
        self.assertIn("bill_savings_revenue_usd", direct_keys)
        # The self-invest factory presents its avoided-bill line, not the ESCO /
        # grid-CfD energy line nor the private-wire PPA line.
        self.assertNotIn("esco_energy_revenue_usd", direct_keys)
        self.assertNotIn("ppa_energy_revenue_usd", direct_keys)

    def test_bill_savings_line_is_hidden_under_other_structures(self):
        for structure in (ESCO, DPPA, PHYSICAL_DPPA):
            keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, structure)}
            self.assertNotIn("bill_savings_revenue_usd", keys, structure)

    def test_esco_and_dppa_lines_are_hidden_under_direct_ownership(self):
        direct_keys = {
            key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, DIRECT_OWNERSHIP)
        }
        # The full avoided-bill delta already folds in energy, demand and any
        # grid arbitrage, so none of those component lines appear; nor do the
        # grid-CfD generator/offtaker lines.
        for hidden in ("esco_demand_revenue_usd", "esco_grid_arbitrage_revenue_usd",
                       "generator_revenue_usd", "dppa_offtaker_cost_usd"):
            self.assertNotIn(hidden, direct_keys, hidden)

    def test_surplus_export_lines_appear_under_direct_ownership(self):
        # The factory is the rooftop owner and may sell surplus to EVN (Decree
        # 243), so the shared 3a surplus lines ride on this structure too.
        direct_keys = {
            key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, DIRECT_OWNERSHIP)
        }
        self.assertIn("surplus_export_kwh", direct_keys)
        self.assertIn("surplus_export_revenue_usd", direct_keys)
