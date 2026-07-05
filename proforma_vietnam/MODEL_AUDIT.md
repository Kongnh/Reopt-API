# Model Audit Pack — proforma_vietnam

Last audit pass: 2026-07-04. Scope: the full Vietnam financial model
(`proforma_vietnam/` + `reoptjl/src/vietnam/` tariff layer) and the Excel
deliverable, prepared for independent third-party review (investor, lender,
or model auditor).

## 1. What the reviewer receives

Per case: `case.json` (input), `payload.json` (REopt request),
`results.json` (optimizer output), `assumptions.json`, and
`vietnam_report_<uuid>.xlsx` (the deliverable). The workbook is pure
post-processing of `results.json` + `assumptions.json` and can be regenerated
offline at any time:

```
python -m proforma_vietnam.rebuild_report --case-dir outputs/vietnam_case/factory_a/case_5
```

## 2. How the workbook self-audits

The workbook (see its **Cover** and **Model Basis** sheets) follows the split
used by SAM's cash-flow-to-Excel export: engine outputs are hardcoded and
shaded; everything derivable is a **live Excel formula**.

- **Assumptions** — every input grouped with unit + source, exposed as named
  cells (`ESC_ENERGY`, `DEBT_RATE`, `PV_DEP_YEARS`, …). Carries the complete
  case definition (site & load profile, PV and storage technology terms,
  tariff, contract incl. full DPPA configuration) plus a raw echo of any
  assumptions.json key not shown in a curated group — nothing in the case
  file or assumptions file is omitted from the workbook.
- **Pro Forma (Audit)** — the 25-year cash flow rebuilt entirely with Excel
  formulas from those named cells: indexation factors, revenue (ESCO or DPPA
  decomposition), O&M, debt annuity schedule, straight-line depreciation, the
  Vietnam CIT block (incentive clock + FIFO 5-year loss-carryforward schedule,
  fully visible), CFADS, equity cash flow, DSCR, and Excel-native `IRR`/`NPV`/
  payback metrics. Only three kinds of cells are hardcoded: year-1 dispatch/
  settlement bases (8760-hour engine results), the battery-replacement
  schedule, and the engine tie-out rows.
- **Checks block** — per-year tie-out (max |Excel − engine| across equity CF,
  CFADS, CIT) plus every headline metric, each with PASS/REVIEW at stated
  tolerances (amounts $1, rates 5 bp, DSCR 0.005, payback 0.05 yr). The Cover
  sheet aggregates them into a single status.
- **FX Sensitivity** — editable VND-depreciation scenarios recomputed live.
- **Technical Results / Dispatch Profile / Load Duration** — REopt technical
  record. The Dispatch sheet shows the original PV generation before the
  dispatch split (to load / storage / grid / curtailed), grid- and PV-charging
  flows, and the hourly PVWatts production factor (kWh/kW) as the irradiation
  proxy (REopt does not persist raw irradiance); its chart plots the peak-load
  week rather than all 8760 hours.
- The former per-year record tables (Summary, Cash Flow, Tax Schedule, Debt
  Service, Developer Financials, DPPA Configuration, DPPA Annual Summary) were
  consolidated into the sheets above to remove duplication; the VND-native
  Monthly/Hourly Settlement sheets remain.

Validation run 2026-07-04 (Excel COM full recalculation, all six Factory A
cases, including the two DPPA cases): **every check PASS**, cover status
"ALL CHECKS PASS", per-year max delta 0.0000 USD.

## 3. Currency treatment (resolved)

The prior open question — `_add_usd_aliases` copying values between `_vnd`
and `_usd` keys with no FX applied — is resolved:

- The engine computes in **USD**: the EVN tariff is converted VND→USD at the
  contract rate before REopt runs, and `esco_pro_forma` normalizes every money
  input (including the intrinsically-VND DPPA settlement primitives) to USD.
- `cash_flow.calculate_vietnam_esco_cash_flow(..., exchange_rate_vnd_per_usd=)`
  now restates every `_vnd` key at the fixed contract rate
  (`_finalize_currencies`), so VND labels carry true VND and USD labels carry
  the computed USD values. Without a rate the legacy aliasing is preserved for
  direct native-VND callers (reference workbook tests unchanged).
- `report_data` results-comparison keys were renamed `_usd` to match what they
  actually hold (REopt USD outputs).
- Verified: `npv_vnd / npv_usd == 25,000` on all six cases; all USD headline
  metrics byte-identical to the committed 2026-06-24 baseline.

Fixed FX over 25 years remains a disclosed simplification; the **FX
Sensitivity** sheet (and `cash_flow.calculate_fx_sensitivity`) quantifies
USD-reported equity IRR/NPV under 0–3 %/yr VND depreciation. Debt is assumed
VND-denominated, so DSCR is FX-neutral.

## 4. Code-vs-doc cross-check (ESCO_CONTRACT_MODEL_DESIGN.md, CD7, ND57)

| Decision | Doc | Code | Status |
|---|---|---|---|
| Q_adj = Q_re_meter / K_pp × δ (quantity uses K_pp only) | §Settlement Math | `dppa_settlement.py` | match |
| k is price-only (CFMP = FMP × k) | CD7 Ví dụ 1 | CFMP series or `fmp × k` fallback | match |
| Q_Khc = min(load, Q_adj); surplus never billed to buyer | 2026-06-11 correction | `q_khc = min(load, q_adj)` | match |
| C_DN = Q_Khc × CFMP × K_pp; C_DPPA/C_CL on Q_Khc; C_BL = shortfall × P_evn | §Settlement Math | hourly loop | match |
| CfD settles on min(Q_c, Q_Khc) | CD7 Ví dụ 4 | `q_cfd = min(q_c_h, q_khc)` | match |
| Curtailed PV credited as export at FMP | case_5 design note | `pv_to_grid_effective` | match |
| Strike escalates at strike rate; market legs at fee rate; C_BL at EVN energy rate | §Annual Escalation | `_dppa_year_terms` | match |
| CIT 4y holiday + 9y 50%, clock capped at year 4, 5y FIFO loss carryforward | Circular 78/2014 Art. 9/18 | `tax_model.calculate_cit` | match |
| PV depreciation 7–20y band, default 20; BESS 8 | Circular 45/2013 | `validate_pv_depreciation_years` | match |
| `cfd_strike_escalation_rate` default | doc said 0 in one place, 0.04 in the New Inputs table | code 0.04 | **doc fixed 2026-07-04** (was an internal doc inconsistency only) |

Also fixed in this pass: the Year-1 BAU-vs-DPPA sheet's `q_adj` fallback used
hardcoded `1.026 × 1.027263` (k × K_pp), contradicting the "quantity uses
K_pp only" rule; it now uses the configured K_pp (display-only fallback,
settlement always emits `q_adj_kw`).

## 5. Simplifications register (disclosed; also on the Model Basis sheet)

1. Fixed FX over the analysis period — quantified on FX Sensitivity.
2. Battery replacement expensed in the replacement year (not capitalized).
3. VAT out of scope (pass-through assumed).
4. No working capital, DSRA, or terminal/residual value.
5. Single 8760-hour dispatch year escalated forward; no re-dispatch.
6. Project IRR uses post-tax CFADS with the levered CIT (interest shield
   included) — disclosed convention for a simple single-sheet model.
7. REopt sizing is optimizer output and is not bit-reproducible across solver
   versions (see CODEX_SESSION.md); the financial layer is deterministic given
   `results.json`.

## 6. Test coverage

130 unittests green (`.venv/Scripts/python.exe -m unittest discover -s
proforma_vietnam/tests -t .`), including:

- CD7 Ví dụ 1 reproduced exactly (acceptance test).
- Reference ESCO workbook (hand-built 25-year model) within tolerance.
- Currency finalization: `_vnd == _usd × FX`, non-currency metrics untouched.
- FX sensitivity: d=0 reproduces base metrics; monotonic erosion.
- Audit sheets: named cells complete, formula/hardcode split, engine tie-out
  values, DPPA row/name variants, no empty-string cells (Excel-corrupting),
  no prose stored as formulas.

Excel-side validation is not simulated: the checks are live in the workbook
and were confirmed by a full Excel recalculation on all six cases.
