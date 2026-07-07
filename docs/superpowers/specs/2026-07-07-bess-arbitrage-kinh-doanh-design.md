# Battery-only grid-arbitrage ESCO case — kinh doanh tariff (design)

Date: 2026-07-07. Status: approved by user (interactive design review).

## Goal

Answer: does a battery-only, grid-charging energy-arbitrage investment make
sense in Vietnam under the Decision 963 TOU structure, for an ESCO that keeps
100% of the arbitrage value? Deliverable: a runnable case in
`outputs/vietnam_case/bess_arbitrage_5mw/`, its report workbook, and an
investment verdict (equity IRR vs hurdle, NPV, payback, DSCR).

## Case definition

- **Load**: flat 5,000 kW × 8760 h (commercial customer proxy), year 2025
  (non-leap, matches rate vintage). New CSV
  `Sample Load Profile/flat_5mw_8760.csv`.
- **Tariff**: EVN retail, **business (kinh doanh) category, ≥22kV tier** —
  off-peak 1,609 / normal 2,887 / peak 5,025 VND/kWh, per Decision
  1279/QD-BCT (2025-05-09), verified against the official scanned annex
  (manufacturing 22–110kV row cross-checked against the existing table:
  1,833/1,190/3,398 — exact match). TOU windows: `decision_963`
  (off-peak 00–06 daily, peak 18–23 Mon–Sat, Sunday no peak).
  4%/yr escalation, contract FX 26,300 VND/USD, currency USD.
- **Battery**: fixed 5 MW / 25 MWh (min=max), $80/kW + $120/kWh = **$3.4M**
  capex, O&M 1% of installed cost/yr, `can_grid_charge` on, **no
  replacement** (replace costs zeroed; user decision).
- **PV**: none (battery-only). PV block zeroed (`max_kw: 0`, zero
  production series to skip PVWatts).
- **ESCO contract**: `grid_charging_enabled: true`,
  `esco_grid_arbitrage_share = 1.00` (engine default),
  `esco_energy_discount_fraction = 0.0` (no PV energy line),
  **`contract_years: 15`, zero residual** (user revised from the original
  10-year mention), no demand-savings relevance (single-component tariff).
- **Financing**: engine defaults — 70% debt @ 8.5% VND, 10-yr term, 10%
  owner discount rate, standard CIT regime, 25-yr proforma with operations
  truncated at contract year 15.

## Code changes (both small, test-first)

### 1. Business (kinh doanh) tariff category

- `proforma_vietnam/defaults/evn_tariff_rates.json`: add
  `standard_business` with a 2025 vintage (source: Decision 1279/QD-BCT
  2025-05-09): `22kv_and_above` 2,887/1,609/5,025; `6_to_22kv`
  3,108/1,829/5,202; `below_6kv` 3,152/1,918/5,422.
- `reoptjl/src/vietnam/evn_rates.py`: expose `STANDARD_BUSINESS_RATES`
  (same reshaping as manufacturing).
- `reoptjl/src/vietnam/evn_tariff.py`: accept
  `tariff_category="business"`; business tier lookup maps normalized
  voltage keys `110kv_and_above`/`22_to_110kv` → `22kv_and_above`,
  others pass through. Vintage fallback identical to manufacturing.
- `proforma_vietnam/case_builder.py`: pass `tariff.tariff_category`
  through (default `manufacturing`) and carry it into `assumptions` for
  workbook disclosure.

### 2. Battery-only grid-arbitrage wiring

`esco_pro_forma.calculate_esco_pro_forma_from_reopt_results` currently
never computes `net_grid_arbitrage_value_vnd` (defaults to 0; the design
doc deferred PV-vs-grid attribution). For a battery-only case attribution
is trivial: **all** discharge is grid-charged, so

```
net_grid_arbitrage_value = (bau_bill − optimized_bill)
                         − (bau_demand_charge − optimized_demand_charge)
```

Wire exactly that, gated on: `can_grid_charge` is true AND the case has no
PV capacity (no PV outputs or total PV `size_kw == 0`). Set it into
`cash_flow_inputs` **before** `cash_flow_overrides` update so explicit
overrides still win. `cash_flow.py` already books
`max(value, 0) × esco_grid_arbitrage_share` when `grid_charging_enabled`,
escalates it at the EVN energy rate, and the schema/xlsx/audit layers
already render the line — no presentation changes.

## Run & verify

1. Unit tests: business-category tests alongside
   `reoptjl.test.test_vietnam_tariff`; battery-only arbitrage tests in
   `proforma_vietnam/tests/test_esco_pro_forma.py`; case_builder
   passthrough test. Full suites must pass (427 + 23 baseline).
2. Docker stack (`db, redis, julia, celery, django`) up; submit via
   `python -m proforma_vietnam.run_case --case <case.json>`; REopt.jl
   produces the optimal dispatch; workbook builds through the normal
   pipeline; validate via
   `python -m proforma_vietnam.validate_workbook <case_dir>` (Excel COM).
3. Verdict from the summary metrics; report caveats: off-peak grid draw
   ≈ 9.4 MW (load + charging) at the 22kV connection; Sunday cycles earn
   only the normal−off-peak spread; offtaker savings are zero by
   construction (100% arbitrage to ESCO).

## Expected shape of the answer (sanity preview)

Net ≈ 3,230 VND per discharged kWh weekdays/Saturdays (5,025 −
1,609/RTE≈0.9), ≈ 1,100 VND Sundays → year-1 revenue ≈ $1.0M on $3.4M
capex, ~3.4-yr simple payback, 15-yr contract with 4% escalation → likely
strongly positive. The model run confirms with debt, CIT, and escalation.
