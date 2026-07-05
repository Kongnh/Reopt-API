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

Excel-side validation is not simulated: the checks are live in the workbook.
Through 2026-07-04 this was confirmed by opening each workbook in Excel by
hand and reading the recalculated Cover/checks-block cells. From 2026-07-05
it is automated: `python -m proforma_vietnam.validate_workbook <case_dir>`
(Task 5a) drives the same full-recalculation-and-read-back via Excel COM
non-interactively and exits 0 iff every check cell reads PASS — see §7 for
the current run.

## 7. 2026-07-05 re-baseline (regulatory refresh)

Phase 2 of the regulatory refresh changed two engine defaults:

- **DPPA CIT regime**: `calculate_vietnam_esco_cash_flow`'s `cit_regime`
  default is now structure-dependent — a DPPA structure (a licensed RE
  generator) defaults to the Law 67/2025 `re_producer` incentive (0% y1–4,
  5% y5–13, 10% y14–15, 20% y16+) instead of the prior `standard_with_holiday`
  default (4y holiday + 9y at 50% of the 20% standard rate). CIT falls in
  years 5–15, so DPPA equity IRR/NPV/DSCR/payback improve.
- **FX default**: `vietnam_defaults.json` now defaults
  `exchange_rate_vnd_per_usd` to 26,300. This only affects *new* cases run
  without an explicit rate — all six Factory A cases carry their own
  explicit contract FX (25,000) in `assumptions.json`, so their rebuilt
  workbooks are unaffected by the FX default change.
- Tariff and DPPA contract constants (CfD strike, escalation rates, EVN
  tariff schedule, etc.) are unchanged in value; only the CIT regime
  resolution logic changed.

The six committed `vietnam_report_*.xlsx` deliverables (generated before
Phase 2) were regenerated offline with
`python -m proforma_vietnam.rebuild_report --case-dir <case dir>` (no REopt
re-run; pure post-processing of the unmodified `results.json` +
`assumptions.json`).

### Cases 1–4 (ESCO) — no regression

ESCO structures resolve to `standard_with_holiday` by default both before and
after Phase 2, and each case's saved FX is explicit, so headline metrics are
**byte-identical** between a run forcing `cit_regime="standard_with_holiday"`
and a run using engine defaults. Verified for all four cases (equity IRR,
equity NPV, project IRR, payback, average/min DSCR, lifetime CIT — every
field equal):

| Case | Equity IRR | Equity NPV (USD) | Project IRR | Payback (yr) | Avg DSCR | Min DSCR | Lifetime CIT (USD) |
|---|---|---|---|---|---|---|---|
| case_1 | 15.726% | $1,124,715 | 12.839% | 11.618 | 1.270 | 1.093 | $1,979,316 |
| case_2 | 13.794% | $861,175 | 11.769% | 12.454 | 1.182 | 1.012 | $1,978,570 |
| case_3 | 10.163% | $39,914 | 9.595% | 14.401 | 0.993 | 0.825 | $1,714,955 |
| case_4 | 17.855% | $693,480 | 14.046% | 9.569 | 1.302 | 1.131 | $982,179 |

### Cases 5–6 (DPPA/CfD) — BEFORE/AFTER

BEFORE = `cit_regime="standard_with_holiday"` forced (reproduces the
pre-Phase-2 committed workbook). AFTER = engine defaults (`re_producer`,
Law 67/2025). Both runs use the case's saved `results.json` +
`assumptions.json` unmodified; only `cit_regime` resolution differs.

| Metric | case_5 BEFORE | case_5 AFTER | Δ | case_6 BEFORE | case_6 AFTER | Δ |
|---|---|---|---|---|---|---|
| CIT regime | standard_with_holiday | re_producer | — | standard_with_holiday | re_producer | — |
| Equity IRR | 16.776% | 17.020% | +0.244 pp | 26.908% | 27.477% | +0.569 pp |
| Equity NPV (USD) | $1,515,230 | $1,576,314 | +$61,084 | $2,538,196 | $2,651,647 | +$113,451 |
| Project IRR | 13.409% | 13.549% | +0.140 pp | 18.237% | 18.546% | +0.309 pp |
| Simple payback (yr) | 9.139 | 8.923 | −0.216 | 4.714 | 4.671 | −0.043 |
| Average DSCR | 1.322 | 1.339 | +0.017 | 1.713 | 1.748 | +0.035 |
| Min DSCR | 1.133 | 1.133 | +0.000 | 1.497 | 1.497 | +0.000 |
| Lifetime CIT (USD) | $2,410,184 | $2,226,181 | −$184,003 | $2,523,192 | $2,196,077 | −$327,115 |

All deltas move in the expected direction for a lower-tax regime: CIT falls,
equity IRR/NPV/DSCR rise, payback shortens. Min DSCR is unchanged on both
cases because the binding year for debt-service coverage sits in the
identical-CIT window (years 1–4, still 0% under both regimes) for these two
cases' debt schedules.

### Validation run (2026-07-05)

`python -m proforma_vietnam.validate_workbook <case_dir>`, one invocation per
case dir (validator commit `b1dd697b`, "Add Excel COM recalc validator for
the audit workbook"), all six rebuilt workbooks:

```
PASS  .../case_1/vietnam_report_3dd5bf1f-fa51-4f1e-aa64-d24ae11a1820.xlsx  (9 checks)
PASS  .../case_2/vietnam_report_554ee85a-6f3c-4077-8dcb-0145406d4e6e.xlsx  (9 checks)
PASS  .../case_3/vietnam_report_b33f4a1f-9de5-4228-ba55-4db9578de73a.xlsx  (9 checks)
PASS  .../case_4/vietnam_report_36f36f61-c28e-4c8a-bc9d-66f21300c28e.xlsx  (9 checks)
PASS  .../case_5/vietnam_report_c73574b2-1170-4611-a6c8-8a012bd1f50d.xlsx  (9 checks)
PASS  .../case_6/vietnam_report_5b999b24-d8c1-4d91-aa2e-1ea0a973af38.xlsx  (9 checks)
```

Cover status "ALL CHECKS PASS" on every workbook, zero REVIEW cells, exit
code 0 on every invocation.
