"""Solve the ESCO energy-discount fraction that earns a target equity IRR.

Offline tool and the ESCO analogue of the DPPA negotiation sweep: it reads a
saved ESCO case (results.json + assumptions.json) exactly the way
``rebuild_report.py`` does and bisects ``esco_energy_discount_fraction`` to the
target equity IRR. It only READS the case dir -- it never writes or rebuilds
workbooks. All 4a-4f financing features flow through automatically because the
evaluate callable re-runs the full engine with the case's saved assumptions.

    python -m proforma_vietnam.run_esco_discount_solver \
        --case-dir outputs/vietnam_case/factory_a/case_1 --target-irr 0.12
"""
import argparse
import json
from pathlib import Path

from proforma_vietnam.dppa_settlement import DPPA_TYPE_NONE
from proforma_vietnam.esco_discount_solver import solve_esco_discount_for_target_irr
from proforma_vietnam.esco_pro_forma import calculate_esco_pro_forma_from_reopt_results
from proforma_vietnam.run_dppa_negotiation_sweep import cash_flow_overrides_from_assumptions


def solve_esco_discount_for_case(case_dir, target_equity_irr_fraction, *, lo=0.5, hi=1.0):
    case_dir = Path(case_dir)
    results = json.loads((case_dir / "results.json").read_text(encoding="utf-8"))
    assumptions = json.loads((case_dir / "assumptions.json").read_text(encoding="utf-8"))
    _require_esco_structure(assumptions)

    overrides = cash_flow_overrides_from_assumptions(assumptions)

    def evaluate(fraction):
        return calculate_esco_pro_forma_from_reopt_results(
            results,
            esco_energy_discount_fraction=fraction,
            **overrides,
        )["summary"]

    return solve_esco_discount_for_target_irr(
        evaluate,
        target_equity_irr_fraction,
        lo=lo,
        hi=hi,
    )


def _require_esco_structure(assumptions):
    """Reject non-ESCO cases: the discount fraction only drives ESCO revenue.

    A DPPA (grid CfD / private wire) or direct-ownership run earns from a
    different revenue chain, so bisecting the ESCO discount would not move -- and
    is not defined against -- its equity IRR.
    """
    dppa = assumptions.get("dppa")
    if isinstance(dppa, dict) and dppa.get("type", DPPA_TYPE_NONE) != DPPA_TYPE_NONE:
        raise ValueError(
            "target-IRR discount solving is ESCO-only; this case carries a "
            f"{dppa.get('type')!r} DPPA structure."
        )
    direct = assumptions.get("direct_ownership")
    if direct is not None and (not isinstance(direct, dict) or direct.get("enabled", True)):
        raise ValueError(
            "target-IRR discount solving is ESCO-only; this case carries a "
            "direct_ownership (factory self-invest) structure."
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Solve the ESCO energy-discount fraction for a target equity IRR."
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        help="ESCO case directory with results.json + assumptions.json.",
    )
    parser.add_argument(
        "--target-irr",
        type=float,
        required=True,
        help="Target equity IRR as a fraction, e.g. 0.12.",
    )
    parser.add_argument(
        "--lo",
        type=float,
        default=0.5,
        help="Lower discount-fraction bracket (default 0.5).",
    )
    parser.add_argument(
        "--hi",
        type=float,
        default=1.0,
        help="Upper discount-fraction bracket (default 1.0).",
    )
    args = parser.parse_args(argv)

    try:
        result = solve_esco_discount_for_case(
            args.case_dir,
            args.target_irr,
            lo=args.lo,
            hi=args.hi,
        )
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, indent=2))
        return 1

    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "converged" else 2


if __name__ == "__main__":
    raise SystemExit(main())
