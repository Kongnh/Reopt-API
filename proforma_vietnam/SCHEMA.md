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

- **Schema-driven** (proforma line-items): Cash Flow, Tax Schedule, Debt
  Service, DPPA Annual Summary, Summary, Developer Financials.
- **Bespoke layouts** (hand-tuned labels/formats, intentionally outside the
  schema): Executive Summary, Buyer Analysis, Developer Returns,
  Year 1 BAU vs DPPA.
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

> Follow-up (out of scope here): the EVN tariff rate tables in
> `reoptjl/src/vietnam/evn_rates.py` could move to the same versioned-defaults
> pattern.
