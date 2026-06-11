from pathlib import Path
from unittest import TestCase

from proforma_vietnam.dppa_negotiation_sweep import (
    classify_balanced_deals,
    mark_pareto_frontier,
    run_dppa_negotiation_sweep,
)
from proforma_vietnam.dppa_negotiation_workbook import (
    build_dppa_negotiation_summary,
    build_dppa_negotiation_workbook,
)
from proforma_vietnam.run_dppa_negotiation_sweep import (
    default_output_dir_name,
    reconcile_cash_flows,
    reference_case_paths,
)


class DppaNegotiationSweepTests(TestCase):

    def test_default_grid_has_36_unique_readable_scenarios_and_exact_scaled_volumes(self):
        seen_inputs = {}

        def evaluator(dppa_inputs):
            scenario_id = (
                f"strike_{int(dppa_inputs['cfd_strike_per_kwh_vnd'])}"
                f"_volume_{int(round(dppa_inputs['volume_fraction'] * 100))}"
            )
            seen_inputs[scenario_id] = dppa_inputs
            return _cash_flow()

        study = run_dppa_negotiation_sweep(
            reference_dppa_inputs=_reference_dppa_inputs(),
            evaluator=evaluator,
            non_dppa_case_2_cash_flow=_cash_flow(offtaker_cost=80.0),
        )

        self.assertEqual(len(study["scenarios"]), 36)
        self.assertEqual(len({row["scenario_id"] for row in study["scenarios"]}), 36)
        self.assertIn("strike_1400_volume_70", seen_inputs)
        self.assertIn("strike_2200_volume_100", seen_inputs)
        self.assertEqual(
            seen_inputs["strike_1800_volume_80"]["cfd_contract_volume_kwh_per_hour"],
            [8.0, 16.0, 24.0],
        )

    def test_classification_names_each_failed_gate_and_excludes_no_debt_years_from_minimum_dscr(self):
        # Buyer gate evaluates the first 10 years AND project lifetime, not Year 1.
        rows = [
            {
                "scenario_id": "failed",
                "buyer_savings_10yr_fraction": -0.01,
                "buyer_savings_lifetime_fraction": -0.02,
                "equity_irr_fraction": 0.11,
                "annual_dscr": [1.10, None, None],
            },
            {
                "scenario_id": "passed",
                "buyer_savings_10yr_fraction": 0.01,
                "buyer_savings_lifetime_fraction": 0.02,
                "equity_irr_fraction": 0.13,
                "annual_dscr": [1.25, None, None],
            },
        ]

        classify_balanced_deals(rows)

        self.assertEqual(rows[0]["minimum_dscr"], 1.10)
        self.assertEqual(
            rows[0]["failed_qualification_reasons"],
            [
                "buyer_10yr_savings_below_0_percent",
                "buyer_lifetime_savings_below_0_percent",
                "equity_irr_below_12_percent",
                "minimum_dscr_below_1_20x",
            ],
        )
        self.assertFalse(rows[0]["balanced_deal"])
        self.assertTrue(rows[1]["balanced_deal"])

    def test_buyer_gate_requires_both_10yr_and_lifetime_horizons(self):
        rows = [
            {
                "scenario_id": "lifetime_only",
                "buyer_savings_10yr_fraction": -0.01,
                "buyer_savings_lifetime_fraction": 0.05,
                "equity_irr_fraction": 0.13,
                "annual_dscr": [1.25],
            },
            {
                "scenario_id": "first_decade_only",
                "buyer_savings_10yr_fraction": 0.05,
                "buyer_savings_lifetime_fraction": -0.01,
                "equity_irr_fraction": 0.13,
                "annual_dscr": [1.25],
            },
        ]

        classify_balanced_deals(rows)

        self.assertEqual(
            rows[0]["failed_qualification_reasons"],
            ["buyer_10yr_savings_below_0_percent"],
        )
        self.assertEqual(
            rows[1]["failed_qualification_reasons"],
            ["buyer_lifetime_savings_below_0_percent"],
        )

    def test_scenario_rows_carry_10yr_and_lifetime_buyer_metrics(self):
        study = run_dppa_negotiation_sweep(
            reference_dppa_inputs=_reference_dppa_inputs(),
            evaluator=lambda dppa_inputs: _cash_flow(),
            non_dppa_case_2_cash_flow=_cash_flow(offtaker_cost=80.0),
        )

        row = study["scenarios"][0]
        self.assertEqual(row["buyer_savings_10yr_usd"], 120.0)
        self.assertEqual(row["buyer_savings_10yr_fraction"], 0.06)
        self.assertEqual(row["buyer_savings_lifetime_usd"], 400.0)
        self.assertEqual(row["buyer_savings_lifetime_fraction"], 0.08)

    def test_pareto_frontier_marks_only_non_dominated_balanced_terms(self):
        # Frontier trades off lifetime buyer savings against seller equity IRR.
        rows = [
            _row("buyer_best", 0.10, 0.12),
            _row("seller_best", 0.02, 0.18),
            _row("dominated", 0.01, 0.11),
            {**_row("not_balanced", 0.20, 0.20), "balanced_deal": False},
        ]

        mark_pareto_frontier(rows)

        self.assertTrue(rows[0]["pareto_frontier"])
        self.assertTrue(rows[1]["pareto_frontier"])
        self.assertFalse(rows[2]["pareto_frontier"])
        self.assertFalse(rows[3]["pareto_frontier"])

    def test_output_builders_include_required_sheets_and_both_comparison_baselines(self):
        study = _study()

        workbook = build_dppa_negotiation_workbook(study)
        summary = build_dppa_negotiation_summary(study)

        self.assertEqual(
            workbook.sheetnames,
            [
                "Executive Summary",
                "Scenario Matrix",
                "Balanced Deals",
                "Negotiation Frontier",
                "Strike-Volume Matrix",
                "Buyer 10yr Savings Heatmap",
                "Lifetime Savings Heatmap",
                "ESCO IRR Heatmap",
                "Minimum DSCR Heatmap",
                "Methodology",
            ],
        )
        self.assertIn("BAU", summary)
        self.assertIn("non-DPPA case_2", summary)

    def test_reconciliation_compares_required_metrics_with_tolerance(self):
        actual = _cash_flow()
        reference = _cash_flow()

        reconciliation = reconcile_cash_flows(actual, reference, tolerance=1e-9)

        self.assertTrue(reconciliation["passed"])
        self.assertEqual(
            set(reconciliation["metrics"]),
            {
                "c_dn_usd",
                "c_dppa_usd",
                "c_cl_usd",
                "c_bl_usd",
                "cfd_net_usd",
                "generator_revenue_usd",
                "dppa_offtaker_cost_usd",
                "equity_irr_fraction",
                "npv_usd",
                "minimum_dscr",
                "average_dscr",
            },
        )

    def test_runner_selects_case_6_reference_artifacts_and_separate_output(self):
        paths = reference_case_paths("factory_a", "case_6")

        self.assertEqual(paths["results"], Path("factory_a") / "case_6" / "results.json")
        self.assertEqual(
            paths["assumptions"],
            Path("factory_a") / "case_6" / "assumptions.json",
        )
        self.assertEqual(
            default_output_dir_name("case_6"),
            "dppa_negotiation_study_case_6",
        )


def _reference_dppa_inputs():
    return {
        "type": "grid_dppa_cfd",
        "cfd_strike_per_kwh_vnd": 2000.0,
        "cfd_contract_volume_kwh_per_hour": [10.0, 20.0, 30.0],
    }


def _cash_flow(offtaker_cost=90.0):
    return {
        "summary": {
            "equity_irr_fraction": 0.13,
            "npv_usd": 100.0,
            "average_dscr": 1.30,
            "buyer_savings_10yr_usd": 120.0,
            "buyer_savings_10yr_fraction": 0.06,
            "buyer_savings_lifetime_usd": 400.0,
            "buyer_savings_lifetime_fraction": 0.08,
        },
        "annual_cash_flows": [
            {
                "bau_evn_bill_usd": 100.0,
                "offtaker_post_project_cost_usd": offtaker_cost,
                "generator_revenue_usd": 50.0,
                "cfd_net_usd": 10.0,
                "c_dn_usd": 20.0,
                "c_dppa_usd": 5.0,
                "c_cl_usd": 3.0,
                "c_bl_usd": 12.0,
                "dppa_offtaker_cost_usd": 50.0,
                "debt_service_usd": 10.0,
                "dscr": 1.25,
            },
            {"debt_service_usd": 0.0, "dscr": None},
        ],
    }


def _row(scenario_id, savings, irr):
    return {
        "scenario_id": scenario_id,
        "factory_savings_vs_bau_fraction": savings,
        "buyer_savings_10yr_fraction": savings,
        "buyer_savings_lifetime_fraction": savings,
        "equity_irr_fraction": irr,
        "balanced_deal": True,
    }


def _study():
    scenarios = [
        {
            **_row("strike_1800_volume_80", 0.05, 0.14),
            "strike_vnd_per_kwh": 1800,
            "volume_fraction": 0.8,
            "annual_contracted_kwh": 1000.0,
            "factory_savings_vs_bau_usd": 50.0,
            "buyer_savings_10yr_usd": 120.0,
            "buyer_savings_lifetime_usd": 400.0,
            "factory_savings_vs_case_2_usd": -10.0,
            "factory_savings_vs_case_2_fraction": -0.01,
            "factory_year_one_outflow_usd": 950.0,
            "npv_usd": 100.0,
            "minimum_dscr": 1.25,
            "average_dscr": 1.30,
            "generator_year_one_revenue_usd": 500.0,
            "cfd_year_one_net_usd": 50.0,
            "cfd_transfer_direction": "buyer_to_seller",
            "failed_qualification_reasons": [],
            "pareto_frontier": True,
        },
    ]
    return {
        "configuration": {
            "strikes_vnd_per_kwh": [1800],
            "volume_fractions": [0.8],
            "thresholds": {
                "buyer_savings_10yr_fraction": 0.0,
                "buyer_savings_lifetime_fraction": 0.0,
                "equity_irr_fraction": 0.12,
                "minimum_dscr": 1.20,
            },
        },
        "scenarios": scenarios,
        "balanced_deals": scenarios,
        "negotiation_frontier": scenarios,
        "recommended_negotiation_range": scenarios,
        "reconciliation": {"passed": True},
    }
