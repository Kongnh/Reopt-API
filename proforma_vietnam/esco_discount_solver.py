"""Target-IRR ESCO discount solver -- the ESCO analogue of the DPPA sweep.

The negotiation question is "what energy price (as a fraction of the EVN tariff)
must the ESCO charge to earn its hurdle equity IRR?".
``esco_energy_discount_fraction`` is that price fraction -- ESCO energy revenue =
kWh x EVN rate x fraction -- so equity IRR is monotone increasing in the
fraction, which makes bisection exact and robust.

Pure module: it takes a caller-supplied ``evaluate(fraction)`` callable (which
returns the cash-flow ``summary`` dict) so the solver is unit-testable with fakes
and decoupled from case loading. Economic outcomes (target unreachable within the
search range) are returned as a status in the result dict; only genuine input
errors raise.
"""
import math


def solve_esco_discount_for_target_irr(
    evaluate,
    target_equity_irr_fraction,
    *,
    lo=0.5,
    hi=1.0,
    irr_tol=1e-6,
    max_iterations=100,
):
    """Bisect ``esco_energy_discount_fraction`` to a target equity IRR.

    ``evaluate(fraction)`` returns the cash-flow ``summary`` dict; the solver
    reads ``summary["equity_irr_fraction"]``. An IRR of ``None`` (undefined --
    e.g. all-negative equity flows at a very low price) is treated as -inf, below
    any target.

    The default bounds ``(0.5, 1.0)`` are a commercial search range, not a
    regulatory bound (Decree 243/2026 removed the price ceiling); callers
    override freely. ``lo``/``hi`` are the discount-fraction bracket ends and
    each must lie in ``(0, 1]``.

    Returns a result dict with ``status`` one of:
    - ``"converged"``      -- an interior fraction hits the target within
      ``irr_tol``.
    - ``"infeasible_high"`` -- even ``hi`` cannot reach the target (its IRR is
      below target); the ``hi`` endpoint is reported.
    - ``"infeasible_low"``  -- ``lo`` already exceeds the target (any price in
      range beats the hurdle); the ``lo`` endpoint is reported.

    Raises ``ValueError`` for bad inputs and ``RuntimeError`` if the iteration
    cap is exhausted (unreachable for a monotone curve; guarded anyway).
    """
    _validate_inputs(target_equity_irr_fraction, lo, hi, irr_tol)

    target = target_equity_irr_fraction
    lo_raw, lo_irr = _evaluate_irr(evaluate, lo)
    hi_raw, hi_irr = _evaluate_irr(evaluate, hi)

    if hi_irr < target - irr_tol:
        return _result("infeasible_high", hi, hi_raw, 0, lo, hi, target)
    if lo_irr > target + irr_tol:
        return _result("infeasible_low", lo, lo_raw, 0, lo, hi, target)

    low, high = lo, hi
    for iteration in range(1, max_iterations + 1):
        mid = (low + high) / 2
        mid_raw, mid_irr = _evaluate_irr(evaluate, mid)
        if abs(mid_irr - target) <= irr_tol:
            return _result("converged", mid, mid_raw, iteration, lo, hi, target)
        if mid_irr < target:
            low = mid
        else:
            high = mid

    raise RuntimeError(
        f"bisection did not converge within max_iterations={max_iterations} "
        f"(target={target}, bracket=({lo}, {hi})); the IRR curve may not be "
        "monotone over the bracket."
    )


def _validate_inputs(target, lo, hi, irr_tol):
    if isinstance(target, bool) or not isinstance(target, (int, float)) or not math.isfinite(target):
        raise ValueError(f"target_equity_irr_fraction must be a real number, got {target!r}.")
    for name, bound in (("lo", lo), ("hi", hi)):
        if not 0 < bound <= 1:
            raise ValueError(f"{name} bound must lie in (0, 1], got {name}={bound!r}.")
    if lo >= hi:
        raise ValueError(f"lo must be strictly less than hi, got lo={lo!r}, hi={hi!r}.")
    if irr_tol <= 0:
        raise ValueError(f"irr_tol must be positive, got irr_tol={irr_tol!r}.")


def _evaluate_irr(evaluate, fraction):
    """Return ``(raw_irr, comparable_irr)`` for a fraction.

    ``raw_irr`` is the reported value (possibly ``None``) for the result dict;
    ``comparable_irr`` maps ``None`` to -inf so an undefined IRR sorts below any
    target during bisection.
    """
    raw = evaluate(fraction)["equity_irr_fraction"]
    comparable = float("-inf") if raw is None else raw
    return raw, comparable


def _result(status, discount_fraction, achieved_irr, iterations, lo, hi, target):
    return {
        "status": status,
        "discount_fraction": discount_fraction,
        "achieved_equity_irr_fraction": achieved_irr,
        "iterations": iterations,
        "lo": lo,
        "hi": hi,
        "target_equity_irr_fraction": target,
    }
