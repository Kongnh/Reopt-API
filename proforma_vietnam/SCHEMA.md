# Proforma schema — how the Vietnam proforma is declared

The Vietnam proforma follows SAM's split between **imperative compute** and
**declarative presentation**:

- `cash_flow.py` (like an SSC compute module) owns the financial formulas and
  emits a per-year row dict plus a summary dict. It stays imperative.
- `proforma_schema.py` (like SAM's `cfline()`/`metric()`) declares each
  line-item once: its label, whether it carries a `_vnd`/`_usd` pair, and which
  financing structures it belongs to. The presentation layers build their
  columns from the schema instead of repeating `(label, key)` pairs.
- `structures.py` names the financing structures and resolves which one a run
  uses — the primary dispatch key, like SAM's `financing()`.

```
inputs ─► cash_flow.calculate_vietnam_esco_cash_flow()   # imperative formulas
              │  annual_cash_flows[], summary{}           # _vnd + _usd aliases
              ▼
        proforma_schema.columns(view, structure)          # declared once
              ▼
        xlsx_builder / report_data                         # render
```

## Adding a new line-item (the payoff)

Before, a line lived in three places (compute dict, xlsx column constant, report
map) and could drift. Now:

1. Compute the value in `cash_flow.py` and put it on the row/summary dict under
   `<key>_vnd` (the USD alias is added automatically by `_add_usd_aliases`).
2. Add one `RowSpec` to `_ROWS` in `proforma_schema.py`.
3. Reference its `key` in whichever view(s) should show it
   (`CASH_FLOW_VIEW`, `TAX_SCHEDULE_VIEW`, `DEBT_SERVICE_VIEW`,
   `DPPA_ANNUAL_VIEW`, `SUMMARY_VIEW`, `DEVELOPER_FINANCIAL_VIEW`).

It then appears in every layer that renders that view — no presentation file
edits. `tests/test_proforma_schema.py` fails if a presented key is missing from
the compute output, so drift is caught in CI instead of resolving to a blank
cell.

## Adding a new financing structure (e.g. direct ownership)

`DIRECT_OWNERSHIP` already exists as a placeholder in `structures.py`.

1. Teach `resolve_structure()` (and `xlsx_builder`'s structure detection) when a
   run is that structure.
2. Set `applies_to` on the `RowSpec`s that differ between structures; shared
   financial lines default to `ALL_STRUCTURES` and need no change.
3. Wire the structure's formulas in `cash_flow.py`.

`columns(view, structure)` filters by `applies_to`, so one view serves every
structure (DPPA-only settlement lines are hidden under ESCO automatically).

## What is schema-driven vs not

- **Schema views** (proforma line-items): `CASH_FLOW_VIEW`, `TAX_SCHEDULE_VIEW`,
  `DEBT_SERVICE_VIEW`, `DPPA_ANNUAL_VIEW`, `SUMMARY_VIEW`,
  `DEVELOPER_FINANCIAL_VIEW` remain the declared registry (guarded by
  `tests/test_proforma_schema.py`), but since 2026-07-04 the workbook no longer
  renders them as standalone sheets — the per-year record tables (Cash Flow,
  Tax Schedule, Debt Service, DPPA Annual Summary, Summary, Developer
  Financials, DPPA Configuration) were consolidated into the Pro Forma (Audit)
  sheet + Assumptions to remove duplication from the deliverable.
- **Bespoke layouts** (hand-tuned labels/formats, intentionally outside the
  schema): Executive Summary, Buyer Analysis, Developer Returns,
  Year 1 BAU vs DPPA, Technical Results, Dispatch Profile.
- **Audit layer** (`audit_sheets.py`, added 2026-07-04): Cover, Assumptions
  (named cells), Model Basis, Pro Forma (Audit) and FX Sensitivity rebuild the
  cash flow with live Excel formulas from `cash_flow`'s `derivation` block and
  tie every metric back to the engine (PASS/REVIEW checks). These mirror the
  compute layer directly (like SAM's cash-flow-to-Excel-with-equations export),
  not the schema views. See `MODEL_AUDIT.md`.
- **REopt report data** (not proforma line-items): System Sizing, Results
  Comparison, Annual Production, Dispatch, Load Duration, and the DPPA
  settlement hourly/monthly breakouts. These stay in `xlsx_builder`.

Number formats are derived from the key suffix (`proforma_schema.number_format`,
relocated verbatim from the old `_number_format_for`), preserving prior output.

Section headers/grouping inside the generic sheets are **not** added: the sheets
are flat tables and adding headers would change existing output. The schema is
structured so this could be layered on later if wanted.

## Defaults

Regulatory/commercial constants live in `defaults/vietnam_defaults.json`
(versioned), mirroring SAM's `deploy/runtime/defaults`. `cash_flow.py` and
`tax_model.py` read their `DEFAULT_*` / `CIT_*` / depreciation constants from
there; regulatory provenance stays in code comments next to each use.

The EVN tariff rate tables also follow this pattern: they live in
`defaults/evn_tariff_rates.json`, keyed by year (vintage) rather than a single
snapshot. `reoptjl/src/vietnam/evn_rates.py` loads the JSON and re-exposes it
under its original Python names/shapes; `reoptjl/src/vietnam/evn_tariff.py`
resolves a requested year to the latest vintage year <= that year (raising
only when the requested year predates every vintage), and
`build_evn_tariff(...)` reports the resolved vintage via `rate_vintage_year`
/ `rate_vintage_source`, which `case_builder.py` carries into the case's
`assumptions` for the audit workbook's raw echo.

The DPPA regulatory constants (transmission/distribution loss factors,
settlement fee adders) live in `defaults/dppa_regulatory.json`, year-keyed the
same way. `dppa_settlement.py` initializes its module constants from the
latest vintage (its settlement functions take per-case overrides, so it needs
no year plumbing); `defaults.dppa_regulatory_for_year(year)` resolves a
requested year to the latest vintage <= that year, and `case_builder.py` uses
it to stamp `dppa_regulatory_vintage_year` / `dppa_regulatory_source` into the
`assumptions` of DPPA cases only (ESCO-only cases never carry these keys).
The default contract FX rate is `vietnam_defaults.json`'s
`financial.exchange_rate_vnd_per_usd`, exposed as
`case_builder.DEFAULT_EXCHANGE_RATE_VND_PER_USD`. Commercial/structural
defaults that are not regulatory vintages (allocation fraction delta, CfD
strike escalation) stay as plain code constants in `dppa_settlement.py`.
