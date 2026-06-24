from unittest import TestCase

from proforma_vietnam import proforma_schema as schema
from proforma_vietnam.cash_flow import calculate_vietnam_esco_cash_flow
from proforma_vietnam.structures import DPPA, ESCO


def _esco_result():
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


class StructureFilteringTests(TestCase):
    def test_dppa_only_lines_are_hidden_under_esco(self):
        esco_keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, ESCO)}
        self.assertNotIn("generator_revenue_usd", esco_keys)
        self.assertNotIn("dppa_offtaker_cost_usd", esco_keys)

    def test_dppa_only_lines_appear_under_dppa(self):
        dppa_keys = {key for _label, key in schema.columns(schema.CASH_FLOW_VIEW, DPPA)}
        self.assertIn("generator_revenue_usd", dppa_keys)
        self.assertIn("dppa_offtaker_cost_usd", dppa_keys)
