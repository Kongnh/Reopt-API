import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.esco_discount_solver import solve_esco_discount_for_target_irr
from proforma_vietnam.esco_pro_forma import calculate_esco_pro_forma_from_reopt_results
from proforma_vietnam.run_esco_discount_solver import (
    main,
    solve_esco_discount_for_case,
)


class EscoDiscountSolverTests(TestCase):
    """Pure bisection solver with an analytic (fake) evaluate."""

    def test_recovers_known_root_on_monotone_curve_within_tolerance(self):
        # IRR increases 0.20 per unit of discount fraction; the root of the
        # target lies at fraction 0.80 (irr = 0.10 + 0.20 * 0.80 = 0.26).
        evaluate = _linear_irr(intercept=0.10, slope=0.20)
        calls = []

        result = solve_esco_discount_for_target_irr(
            _counting(evaluate, calls),
            target_equity_irr_fraction=0.26,
        )

        self.assertEqual(result["status"], "converged")
        self.assertAlmostEqual(result["discount_fraction"], 0.80, places=4)
        self.assertAlmostEqual(result["achieved_equity_irr_fraction"], 0.26, delta=1e-6)
        self.assertEqual(result["target_equity_irr_fraction"], 0.26)
        self.assertEqual(result["lo"], 0.5)
        self.assertEqual(result["hi"], 1.0)
        self.assertGreater(result["iterations"], 0)
        # Deterministic: the recorded evaluate call count matches iterations + the
        # two endpoint probes.
        self.assertEqual(len(calls), result["iterations"] + 2)

    def test_is_deterministic_across_runs(self):
        evaluate = _linear_irr(intercept=0.10, slope=0.20)

        first = solve_esco_discount_for_target_irr(evaluate, 0.26)
        second = solve_esco_discount_for_target_irr(evaluate, 0.26)

        self.assertEqual(first, second)

    def test_target_above_hi_reports_infeasible_high_endpoint(self):
        # Max reachable IRR at hi=1.0 is 0.30; a 0.40 target is unreachable.
        evaluate = _linear_irr(intercept=0.10, slope=0.20)

        result = solve_esco_discount_for_target_irr(evaluate, 0.40)

        self.assertEqual(result["status"], "infeasible_high")
        self.assertEqual(result["discount_fraction"], 1.0)
        self.assertAlmostEqual(result["achieved_equity_irr_fraction"], 0.30)
        self.assertEqual(result["iterations"], 0)

    def test_target_below_lo_reports_infeasible_low_endpoint(self):
        # Min IRR at lo=0.5 is 0.20; a 0.15 target is already beaten everywhere.
        evaluate = _linear_irr(intercept=0.10, slope=0.20)

        result = solve_esco_discount_for_target_irr(evaluate, 0.15)

        self.assertEqual(result["status"], "infeasible_low")
        self.assertEqual(result["discount_fraction"], 0.5)
        self.assertAlmostEqual(result["achieved_equity_irr_fraction"], 0.20)
        self.assertEqual(result["iterations"], 0)

    def test_none_irr_at_low_end_is_treated_as_below_target(self):
        # Undefined IRR (all-negative equity flows) below fraction 0.6; a defined,
        # monotone curve above it. The solver brackets past the None region.
        def evaluate(fraction):
            if fraction < 0.6:
                return {"equity_irr_fraction": None}
            return {"equity_irr_fraction": 0.10 + 0.20 * fraction}

        result = solve_esco_discount_for_target_irr(evaluate, 0.26)

        self.assertEqual(result["status"], "converged")
        self.assertAlmostEqual(result["discount_fraction"], 0.80, places=4)
        self.assertAlmostEqual(result["achieved_equity_irr_fraction"], 0.26, delta=1e-6)

    def test_none_irr_at_hi_reports_infeasible_high_with_none_endpoint(self):
        # A fully undefined curve: hi is treated as -inf, below any target, and
        # the raw None endpoint is reported (not the -inf sentinel).
        result = solve_esco_discount_for_target_irr(
            lambda fraction: {"equity_irr_fraction": None},
            0.12,
        )

        self.assertEqual(result["status"], "infeasible_high")
        self.assertEqual(result["discount_fraction"], 1.0)
        self.assertIsNone(result["achieved_equity_irr_fraction"])

    def test_rejects_invalid_target_bounds_and_tolerance(self):
        evaluate = _linear_irr(intercept=0.10, slope=0.20)

        with self.assertRaisesRegex(ValueError, "target"):
            solve_esco_discount_for_target_irr(evaluate, "0.12")
        with self.assertRaisesRegex(ValueError, "target"):
            solve_esco_discount_for_target_irr(evaluate, True)
        with self.assertRaisesRegex(ValueError, "target"):
            solve_esco_discount_for_target_irr(evaluate, float("nan"))
        with self.assertRaisesRegex(ValueError, "lo"):
            solve_esco_discount_for_target_irr(evaluate, 0.12, lo=0.9, hi=0.5)
        with self.assertRaisesRegex(ValueError, r"\(0, 1\]"):
            solve_esco_discount_for_target_irr(evaluate, 0.12, lo=0.0, hi=1.0)
        with self.assertRaisesRegex(ValueError, r"\(0, 1\]"):
            solve_esco_discount_for_target_irr(evaluate, 0.12, lo=0.5, hi=1.5)
        with self.assertRaisesRegex(ValueError, "tol"):
            solve_esco_discount_for_target_irr(evaluate, 0.12, irr_tol=0.0)

    def test_raises_runtime_error_when_iteration_cap_is_exhausted(self):
        # Pathological evaluate: endpoints straddle the target (guards pass) but
        # no interior point ever lands within tolerance, so bisection never
        # converges and the safety cap fires.
        def pathological(fraction):
            return {"equity_irr_fraction": 0.0 if fraction <= 0.5 else 1.0}

        with self.assertRaisesRegex(RuntimeError, "max_iterations"):
            solve_esco_discount_for_target_irr(
                pathological,
                0.5,
                max_iterations=8,
            )


class EscoDiscountSolverRealEngineTests(TestCase):
    """Solver driven by the real ESCO cash-flow engine (no engine changes)."""

    def test_recovers_the_discount_fraction_behind_a_known_target_irr(self):
        evaluate = _real_engine_evaluate()
        target = evaluate(0.80)["equity_irr_fraction"]

        result = solve_esco_discount_for_target_irr(evaluate, target)

        self.assertEqual(result["status"], "converged")
        self.assertAlmostEqual(result["discount_fraction"], 0.80, places=3)
        self.assertAlmostEqual(
            result["achieved_equity_irr_fraction"], target, delta=1e-6
        )

    def test_equity_irr_is_monotone_increasing_in_the_discount_fraction(self):
        evaluate = _real_engine_evaluate()

        self.assertLess(
            evaluate(0.70)["equity_irr_fraction"],
            evaluate(0.90)["equity_irr_fraction"],
        )

    def test_converges_with_dscr_sized_debt_recomputed_each_step(self):
        # Task 4c: target_min_dscr re-runs the fixed-point sizing loop inside each
        # evaluate; the solver treats it as any other monotone curve.
        evaluate = _real_engine_evaluate(target_min_dscr=1.20)
        target = evaluate(0.80)["equity_irr_fraction"]

        result = solve_esco_discount_for_target_irr(evaluate, target)

        self.assertEqual(result["status"], "converged")
        self.assertAlmostEqual(
            result["achieved_equity_irr_fraction"], target, delta=1e-6
        )


class RunEscoDiscountSolverCliTests(TestCase):

    def test_solves_a_saved_esco_case_and_recovers_its_fraction(self):
        case_dir = _write_case(_esco_assumptions())
        target = calculate_esco_pro_forma_from_reopt_results(
            _reopt_results(), esco_energy_discount_fraction=0.80
        )["summary"]["equity_irr_fraction"]

        result = solve_esco_discount_for_case(case_dir, target)

        self.assertEqual(result["status"], "converged")
        self.assertAlmostEqual(result["discount_fraction"], 0.80, places=3)

    def test_rejects_a_non_esco_case_with_a_clear_error(self):
        dppa_assumptions = {
            **_esco_assumptions(),
            "dppa": {"type": "grid_dppa_cfd", "cfd_strike_per_kwh_vnd": 1700.0},
        }
        case_dir = _write_case(dppa_assumptions)

        with self.assertRaisesRegex(ValueError, "ESCO"):
            solve_esco_discount_for_case(case_dir, 0.12)

    def test_rejects_a_direct_ownership_case_with_a_clear_error(self):
        direct_assumptions = {**_esco_assumptions(), "direct_ownership": {"enabled": True}}
        case_dir = _write_case(direct_assumptions)

        with self.assertRaisesRegex(ValueError, "ESCO"):
            solve_esco_discount_for_case(case_dir, 0.12)

    def test_main_prints_result_json_and_exits_zero_on_convergence(self):
        case_dir = _write_case(_esco_assumptions())
        target = calculate_esco_pro_forma_from_reopt_results(
            _reopt_results(), esco_energy_discount_fraction=0.80
        )["summary"]["equity_irr_fraction"]

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                ["--case-dir", str(case_dir), "--target-irr", repr(target)]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "converged")
        self.assertEqual(
            set(payload),
            {
                "status",
                "discount_fraction",
                "achieved_equity_irr_fraction",
                "iterations",
                "lo",
                "hi",
                "target_equity_irr_fraction",
            },
        )
        self.assertAlmostEqual(payload["discount_fraction"], 0.80, places=3)

    def test_main_exits_two_on_infeasible_target(self):
        case_dir = _write_case(_esco_assumptions())

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--case-dir", str(case_dir), "--target-irr", "5.0"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(json.loads(buffer.getvalue())["status"], "infeasible_high")

    def test_main_exits_one_on_error(self):
        case_dir = _write_case(
            {**_esco_assumptions(), "dppa": {"type": "grid_dppa_cfd"}}
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--case-dir", str(case_dir), "--target-irr", "0.12"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(buffer.getvalue())["status"], "error")


def _linear_irr(*, intercept, slope):
    return lambda fraction: {"equity_irr_fraction": intercept + slope * fraction}


def _counting(evaluate, calls):
    def wrapped(fraction):
        calls.append(fraction)
        return evaluate(fraction)

    return wrapped


def _real_engine_evaluate(**overrides):
    results = _reopt_results()

    def evaluate(fraction):
        return calculate_esco_pro_forma_from_reopt_results(
            results,
            esco_energy_discount_fraction=fraction,
            **overrides,
        )["summary"]

    return evaluate


def _reopt_results():
    return {
        "inputs": {
            "ElectricTariff": {"tou_energy_rates_per_kwh": [1000, 2000]},
            "ElectricStorage": {"can_grid_charge": False},
            "Financial": {"owner_discount_rate_fraction": 0.11},
        },
        "outputs": {
            "PV": {
                "size_kw": 100,
                "installed_cost_per_kw": 1000,
                "electric_to_load_series_kw": [1, 2],
            },
            "ElectricStorage": {
                "initial_capital_cost": 10000,
                "storage_to_load_series_kw": [3, 4],
            },
            "ElectricTariff": {
                "year_one_bill_before_tax_bau": 50000,
                "year_one_bill_before_tax": 30000,
                "year_one_demand_cost_before_tax_bau": 8000,
                "year_one_demand_cost_before_tax": 3000,
            },
            "Financial": {"year_one_om_costs_before_tax": 1000},
        },
    }


def _esco_assumptions():
    return {"esco_energy_discount_fraction": 0.85}


def _write_case(assumptions):
    case_dir = Path(tempfile.mkdtemp())
    (case_dir / "results.json").write_text(json.dumps(_reopt_results()), encoding="utf-8")
    (case_dir / "assumptions.json").write_text(json.dumps(assumptions), encoding="utf-8")
    return case_dir
