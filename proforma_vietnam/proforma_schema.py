"""Declarative proforma schema — the single source of truth for line-items.

Each proforma line-item (an ESCO revenue line, a debt line, a summary metric)
is declared exactly once as a ``RowSpec``: its display label, whether it carries
a ``_vnd``/``_usd`` currency pair, and which financing structures it applies to.
The presentation layers (``xlsx_builder``, ``report_data``) build their column
and row lists from this registry instead of repeating ``(label, key)`` pairs, so
a line can no longer drift between where it is computed and where it is shown.

This mirrors SAM's ``cfline()``: the compute layer (``cash_flow.py``, like an
SSC module) stays imperative and owns the formulas; the schema only declares how
each computed value is presented and which structures it belongs to. "Views" are
thin, ordered lists of keys naming the columns of one sheet — the labels and
formats are never repeated, only referenced.
"""

from dataclasses import dataclass, field

from proforma_vietnam.structures import (
    ALL_STRUCTURES,
    DIRECT_OWNERSHIP,
    DPPA,
    ESCO,
    PHYSICAL_DPPA,
)


@dataclass(frozen=True)
class RowSpec:
    key: str                                  # base key, no currency suffix: "esco_energy_revenue"
    label: str                                # base label, no "(USD)": "ESCO Energy Revenue"
    currency: bool = True                     # True -> has a _vnd/_usd pair
    applies_to: tuple = field(default=ALL_STRUCTURES)  # structures this line appears in


# Canonical registry. Each line-item is declared once. Currency lines carry a
# _vnd/_usd pair (see cash_flow._add_usd_aliases); non-currency lines (year,
# ratios, fractions, payback) are emitted under their bare key.
_ROWS = [
    # --- identity / per-year cash flow ---
    RowSpec("year", "Year", currency=False),
    # ESCO discount-to-EVN / grid-CfD generator energy line. Hidden under the
    # physical private wire (PPA energy line) and under direct ownership (single
    # bill-savings line).
    RowSpec("esco_energy_revenue", "ESCO Energy Revenue",
            applies_to=(ESCO, DPPA)),
    # ND57 Điều 25 private-wire PPA energy line (physical DPPA only).
    RowSpec("ppa_matched_kwh", "PPA Matched Energy (kWh)", currency=False,
            applies_to=(PHYSICAL_DPPA,)),
    RowSpec("ppa_energy_revenue", "PPA Energy Revenue", applies_to=(PHYSICAL_DPPA,)),
    # Factory self-invest: the full avoided EVN bill (energy + demand), captured
    # whole with no ESCO discount or 80/20 demand split (direct ownership only).
    RowSpec("bill_savings_revenue", "Bill Savings (Avoided EVN Bill)",
            applies_to=(DIRECT_OWNERSHIP,)),
    # ESCO / grid-CfD / physical demand + arbitrage share lines. Hidden under
    # direct ownership, where the full bill delta already folds in demand.
    RowSpec("esco_demand_revenue", "ESCO Demand Revenue",
            applies_to=(ESCO, DPPA, PHYSICAL_DPPA)),
    RowSpec("esco_grid_arbitrage_revenue", "ESCO Grid Arbitrage Revenue",
            applies_to=(ESCO, DPPA, PHYSICAL_DPPA)),
    # Decree 243/2026 rooftop surplus-export (ESCO, physical private wire and
    # direct ownership; under grid DPPA the export energy is monetized at FMP).
    RowSpec("surplus_export_kwh", "Surplus Export (kWh)", currency=False,
            applies_to=(ESCO, PHYSICAL_DPPA, DIRECT_OWNERSHIP)),
    RowSpec("surplus_export_revenue", "Surplus Export Revenue",
            applies_to=(ESCO, PHYSICAL_DPPA, DIRECT_OWNERSHIP)),
    RowSpec("esco_revenue", "ESCO Revenue"),
    RowSpec("annual_om", "O&M"),
    RowSpec("replacement_cost", "Replacement Cost"),
    RowSpec("depreciation", "Depreciation"),
    RowSpec("cit", "CIT"),
    RowSpec("cash_available_for_debt_service", "Cash Available For Debt Service"),
    RowSpec("debt_service", "Debt Service"),
    RowSpec("equity_cash_flow", "Equity Cash Flow"),
    RowSpec("offtaker_savings", "Offtaker Savings"),
    RowSpec("offtaker_savings_fraction", "Offtaker Savings Fraction", currency=False),
    RowSpec("dscr", "DSCR", currency=False),
    # --- debt schedule ---
    RowSpec("interest", "Interest"),
    RowSpec("principal", "Principal"),
    RowSpec("ending_debt_balance", "Ending Debt Balance"),
    # --- DPPA-only settlement lines ---
    RowSpec("c_dn", "C_DN", applies_to=(DPPA,)),
    RowSpec("c_dppa", "C_DPPA", applies_to=(DPPA,)),
    RowSpec("c_cl", "C_CL", applies_to=(DPPA,)),
    RowSpec("c_bl", "C_BL", applies_to=(DPPA,)),
    RowSpec("cfd_net", "CfD Net", applies_to=(DPPA,)),
    RowSpec("generator_revenue", "Generator Revenue", applies_to=(DPPA,)),
    RowSpec("dppa_offtaker_cost", "DPPA Offtaker Cost", applies_to=(DPPA,)),
    # --- summary metrics (analogous to SAM's metric()) ---
    RowSpec("total_capex", "Total Capex"),
    RowSpec("debt_principal", "Debt Principal"),
    RowSpec("equity_investment", "Equity Investment"),
    RowSpec("project_irr_fraction", "Project IRR", currency=False),
    RowSpec("equity_irr_fraction", "Equity IRR", currency=False),
    RowSpec("npv", "NPV"),
    RowSpec("average_dscr", "Average DSCR", currency=False),
    RowSpec("simple_payback_years", "Simple Payback (Years)", currency=False),
    RowSpec("roi_fraction", "ROI", currency=False),
]

PROFORMA_ROWS = {row.key: row for row in _ROWS}


# Views: ordered base-key lists naming the columns of one sheet. DPPA-only keys
# are filtered out for non-DPPA structures by columns(), so a single view serves
# every structure.
CASH_FLOW_VIEW = [
    "year",
    "esco_energy_revenue",
    # Physical private-wire PPA energy lines (hidden under ESCO/grid DPPA):
    "ppa_matched_kwh",
    "ppa_energy_revenue",
    # Direct-ownership avoided-bill line (hidden under ESCO/DPPA/physical):
    "bill_savings_revenue",
    "esco_demand_revenue",
    "esco_grid_arbitrage_revenue",
    # Surplus-export lines (ESCO + physical private wire; hidden under grid DPPA):
    "surplus_export_kwh",
    "surplus_export_revenue",
    "esco_revenue",
    "annual_om",
    "replacement_cost",
    "depreciation",
    "cit",
    "cash_available_for_debt_service",
    "debt_service",
    "equity_cash_flow",
    "offtaker_savings",
    "offtaker_savings_fraction",
    "dscr",
    # DPPA extras (hidden under ESCO):
    "generator_revenue",
    "cfd_net",
    "dppa_offtaker_cost",
]

TAX_SCHEDULE_VIEW = ["year", "depreciation", "cit"]

DEBT_SERVICE_VIEW = ["year", "interest", "principal", "debt_service", "ending_debt_balance"]

DPPA_ANNUAL_VIEW = [
    "year",
    "c_dn",
    "c_dppa",
    "c_cl",
    "c_bl",
    "cfd_net",
    "generator_revenue",
    "dppa_offtaker_cost",
]

SUMMARY_VIEW = [
    "total_capex",
    "debt_principal",
    "equity_investment",
    "project_irr_fraction",
    "equity_irr_fraction",
    "npv",
    "average_dscr",
    "simple_payback_years",
    "roi_fraction",
]

DEVELOPER_FINANCIAL_VIEW = [
    "project_irr_fraction",
    "equity_irr_fraction",
    "npv",
    "average_dscr",
    "simple_payback_years",
    "roi_fraction",
]


def _suffixed_key(spec, currency):
    if spec.currency:
        return f"{spec.key}_{currency}"
    return spec.key


def _decorated_label(spec, currency):
    if spec.currency:
        return f"{spec.label} ({currency.upper()})"
    return spec.label


def columns(view, structure, currency="usd"):
    """Build ``[(label, key), ...]`` for one sheet view and structure.

    Rows whose ``applies_to`` excludes ``structure`` are dropped, so DPPA-only
    lines appear only under DPPA. ``currency`` selects the suffix/label decoration
    ("usd" or "vnd") for currency rows.
    """
    result = []
    for key in view:
        spec = PROFORMA_ROWS[key]
        if structure not in spec.applies_to:
            continue
        result.append((_decorated_label(spec, currency), _suffixed_key(spec, currency)))
    return result


def emitted_keys(structure, currency="usd"):
    """All currency-suffixed keys the given structure presents, for validation."""
    keys = set()
    for spec in _ROWS:
        if structure not in spec.applies_to:
            continue
        keys.add(_suffixed_key(spec, currency))
    return keys


def number_format(key):
    """Excel number format for a (suffixed) key.

    Relocated verbatim from ``xlsx_builder._number_format_for`` so the schema
    owns presentation formatting without changing any output: the heuristic keys
    off the suffix convention (_usd/_vnd amounts, _fraction/_rate percents, dscr
    ratios, _years/year unformatted).
    """
    if key is None:
        return None
    if key == "dscr" or "dscr" in key:
        return "0.00"
    if key.endswith("_years") or key == "year":
        return None
    if key.endswith(("_fraction", "_rate")):
        return "0.0%"
    if key.endswith(("_usd", "_vnd", "_kwh", "_kw")):
        return "#,##0"
    return None
