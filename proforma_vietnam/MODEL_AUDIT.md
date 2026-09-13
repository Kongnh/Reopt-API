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
  formulas from those named cells: indexation factors, revenue (ESCO, grid
  DPPA/CfD, physical (private-wire) DPPA, or direct-ownership bill-savings
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
USD-reported equity IRR/NPV under 0–3 %/yr VND depreciation. Debt is
VND-denominated by default, so DSCR is FX-neutral; USD-denominated debt is
available as an option (`debt_currency="USD"`), in which case DSCR is NOT
FX-neutral — USD debt service is FX-fixed while VND-sourced CFADS deflates
under depreciation, an effect the FX Sensitivity sheet also quantifies for
that case.

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
2. Battery replacement is CAPITALIZED by default (Circular 45/2013,
   `battery_replacement_treatment="capitalize"`): each replacement is
   depreciated straight-line over the 8-year BESS class life from its
   in-service year; only the CIT-deduction timing changes — the replacement
   cash outflow is unchanged. Expensing in the replacement year (the pre-4d
   treatment) is retained as a legacy option
   (`battery_replacement_treatment="expense"`).
3. VAT is out of scope (pass-through assumed) by default. Optionally, capex
   input-VAT with refund timing can be modeled (`vat_rate_fraction` +
   `vat_refund_year`, default OFF): paid at year 0 and recovered in the
   configured year, equity-funded and returns-only (no CFADS/DSCR/CIT/IDC
   effect). The operating-stage VAT float (output VAT on invoices vs. input
   VAT on O&M) remains out of scope / pass-through in both modes.
4. No working capital or DSRA is modeled. By default there is also no
   terminal/residual value; optionally (ESCO structures only, default OFF) a
   contract tenor with end-of-term asset transfer can be modeled
   (`contract_years` + `contract_residual_value_usd`): operations truncate at
   year T and the disposal gain/(loss) vs. net book value enters year-T
   taxable income through the case's CIT regime.
5. Single 8760-hour dispatch year escalated forward; no re-dispatch.
6. Project IRR uses post-tax CFADS with the levered CIT (interest shield
   included) — disclosed convention for a simple single-sheet model.
7. REopt sizing is optimizer output and is not bit-reproducible across solver
   versions (see CODEX_SESSION.md); the financial layer is deterministic given
   `results.json`.
8. The default convention is an overnight build: all pre-COD flows collapse
   to year 0. Optionally, a construction period with capitalized interest
   during construction (IDC) and a principal grace period can be modeled
   (`construction_months`, `principal_grace_years`; default OFF/0): IDC is
   simple interest on the average drawn balance, debt-funded and capitalized
   into the depreciable base (not expensed); grace defers principal
   amortization within the debt term.
9. Debt is VND-denominated by default; USD-denominated debt is available as
   an option (`debt_currency="USD"`, ~5% default rate) — its FX exposure is
   quantified on the FX Sensitivity sheet as a deflation overlay only (CIT is
   not recomputed under FX drift). Debt sizing is fraction-of-capex by
   default; DSCR-covenant-driven sizing is available as an option
   (`target_min_dscr`), solved by fixed-point iteration against the full
   debt/IDC/CIT/CFADS derivation on base-case CFADS only (flat FX, no
   downside/stress scenario).

## 6. Test coverage

426 unittests green (`.venv/Scripts/python.exe -m unittest discover -s
proforma_vietnam/tests -t .`), plus 23 in the Vietnam tariff-layer suite
(`reoptjl.test.test_vietnam_tariff`), including:

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
non-interactively and exits 0 iff every check cell reads PASS — see §8 for
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

## 8. 2026-07-06 re-baseline (Circular 45 battery-replacement capitalization, Task 4d)

Task 4d makes battery-replacement capitalization the engine **default**. Under
VAS / Circular 45/2013 a replacement battery is a >30M VND fixed asset: it must
be capitalized and depreciated over the 8-year BESS class life, not expensed in
the replacement year. `calculate_vietnam_esco_cash_flow` gained
`battery_replacement_treatment` (`"capitalize"` default, `"expense"` legacy).
Only the **CIT deduction timing** changes — the replacement cash outflow (CFADS,
equity cash flow, DSCR) is unchanged in both modes. Each replacement year spawns
its own straight-line schedule in service that year (years R..R+7), truncated at
the analysis horizon (the undepreciated remainder is not written off).

> 2026-09-11: the figures below were computed under the year-11, 80/100 USD
> replacement and a 25-year horizon. The shared replacement policy (year 10,
> replacement at install cost, 20 years, PV inverter at 10 percent of PV capex
> in year 11) supersedes them; the tables are kept as the audit record of that
> earlier state and are regenerated in the 2026-09-11 handoff in SESSION_NOTES.md.

All six Factory A cases carry `battery_replacement_year = 11`. Five have a
non-zero year-11 replacement cost and therefore capitalize it; **case_4 has no
battery replacement** (empty REopt replacement schedule) and is unaffected.

The six committed `vietnam_report_*.xlsx` deliverables were regenerated offline
with `python -m proforma_vietnam.rebuild_report --case-dir <case dir>` (no REopt
re-run; pure post-processing of the unmodified `results.json` +
`assumptions.json`).

### case_4 (ESCO, no replacement) — byte-identical

case_4's replacement schedule is empty, so `capitalize` and `expense` produce
identical results and no `battery_replacement` derivation block is emitted. The
committed workbook is left **unchanged** (financially byte-identical): a fresh
`rebuild_report` differs from the committed file only in the cover "prepared"
date stamp and the `docProps/core.xml` save timestamps — no cell value, formula,
or engine tie-out changes. Every headline metric is equal
(equity IRR 17.855%, equity NPV $693,480, lifetime CIT $982,179).

### Cases 1–3 (ESCO) and 5–6 (DPPA) — BEFORE/AFTER

BEFORE = `battery_replacement_treatment="expense"` forced (reproduces the
pre-4d committed workbook — verified byte-identical for case_4 and equity-IRR
exact for case_1 against the committed HEAD workbook). AFTER = engine default
(`"capitalize"`). Both runs use each case's saved `results.json` +
`assumptions.json` unmodified; only the replacement CIT-deduction timing differs.
NPV / CIT shown in USD at each case's saved contract FX (25,000 VND/USD).

| Metric | case_1 B→A | case_2 B→A | case_3 B→A | case_5 B→A | case_6 B→A |
|---|---|---|---|---|---|
| Year-11 replacement (USD) | 998,738 | 1,226,338 | 1,347,451 | 1,226,338 | 165,760 |
| Equity IRR | 15.726%→15.703% | 13.794%→13.767% | 10.163%→10.154% | 17.020%→17.031% | 27.477%→27.476% |
| Δ Equity IRR (pp) | −0.023 | −0.026 | −0.009 | +0.011 | −0.002 |
| Equity NPV (USD) | 1,124,715→1,124,385 | 861,175→858,132 | 39,914→37,802 | 1,576,314→1,585,245 | 2,651,647→2,653,244 |
| Δ Equity NPV (USD) | −330 | −3,043 | −2,111 | +8,931 | +1,597 |
| Lifetime CIT (USD) | 1,979,316→1,941,863 | 1,978,570→1,947,912 | 1,714,955→1,681,268 | 2,226,181→2,157,200 | 2,196,077→2,184,681 |
| Δ Lifetime CIT (USD) | −37,453 | −30,658 | −33,686 | −68,982 | −11,396 |

These deltas are the **Circular 45 replacement capitalization, not a logic
error**. The year-11 replacement's full 8-year life (years 11–18) fits inside
the 25-year horizon, so in a flat-rate world the total deduction — and total CIT
— would be unchanged (pure timing shift). It is not flat here because the
deduction interacts with the CIT regime and loss relief:

- **ESCO (cases 1–3, `standard_with_holiday`)**: expensing books a large
  single deduction in year 11 that partly falls into the reduced-rate window and
  partly exceeds year-11 taxable income (loss carried forward with limited
  relief), so some deduction value is captured at a lower effective rate.
  Spreading it recovers more total value (lifetime CIT falls) but pushes the
  shield later, so equity IRR/NPV tick **down** slightly (delayed cash).
- **DPPA (cases 5–6, `re_producer`: 0% y1–4, 5% y5–13, 10% y14–15, 20% y16+)**:
  expensing concentrates the deduction in the 5% year-11 window; capitalizing
  spreads it into the 10% (y14–15) and 20% (y16–18) windows where it is worth
  more, so both lifetime CIT falls **and** equity IRR/NPV tick **up**.

All movements are small (≤ 0.03 pp on IRR) and directionally consistent with the
regime each case resolves to.

### Validation run (2026-07-06)

`python -m proforma_vietnam.validate_workbook <case dirs...>`, all six committed
workbooks (five rebuilt, case_4 unchanged), real Excel COM recalc:

```
PASS  .../case_1/vietnam_report_3dd5bf1f-fa51-4f1e-aa64-d24ae11a1820.xlsx  (9 checks)
PASS  .../case_2/vietnam_report_554ee85a-6f3c-4077-8dcb-0145406d4e6e.xlsx  (9 checks)
PASS  .../case_3/vietnam_report_b33f4a1f-9de5-4228-ba55-4db9578de73a.xlsx  (9 checks)
PASS  .../case_4/vietnam_report_36f36f61-c28e-4c8a-bc9d-66f21300c28e.xlsx  (9 checks)
PASS  .../case_5/vietnam_report_c73574b2-1170-4611-a6c8-8a012bd1f50d.xlsx  (9 checks)
PASS  .../case_6/vietnam_report_5b999b24-d8c1-4d91-aa2e-1ea0a973af38.xlsx  (9 checks)
```

Cover status "ALL CHECKS PASS" on every workbook, zero REVIEW cells, exit
code 0. The capitalized cases (1–3, 5–6) now carry the per-replacement
depreciation row and the replacement-aware total-depreciation / EBT formulas;
these tie out to the engine under recalc.

## 9. 2026-09-08 de-levelization fix (Task 4/5, Keen Thailand final pass)

REopt applies its own levelization factor to PV production inside the MILP,
so `year_one_bill_before_tax`, `year_one_demand_cost_before_tax`, and every
PV/storage dispatch series carry that weighting despite the `year_one`
prefix on their names. The proforma then applied `(1 - degradation) ^ year`
on its own axis, counting degradation twice and understating savings. Task 4
(commit `b7d7cf05`) added `_levelization_factor` and `_apply_de_levelization`
to `proforma_vietnam/esco_pro_forma.py` to undo REopt's levelization on the
three quantities that carry it (`project_served_pv_kwh`, and the SAVINGS
DELTA on `optimized_evn_bill_vnd` / `optimized_demand_charge_vnd`, not the
bills themselves) before the proforma's own degradation is applied. This
section records the measured movement.

### Measured lambda (levelized / raw year-one PV production)

| Country | Lambda | Understatement (1/lambda - 1) | Cases measured |
|---|---|---|---|
| Thailand | 0.9606123122450961 | 4.100269 percent | rofu_thailand case_1-6, uniform to 9 significant figures |
| Vietnam | 0.9528685459644826 | 4.946270 percent | factory_a case_1-6, uniform to 9 significant figures |

Lambda is computed per case from each case's own `results.json` as
`annual_energy_produced_kwh / year_one_energy_produced_kwh` summed over PV
outputs, per `_levelization_factor`. It is a function of the financial
escalation/discount/degradation parameters REopt levelizes over, not of PV
size, which is why it is uniform within a country. The two battery-only
Vietnam cases (`bess_arbitrage_5mw`, `bess_arbitrage_5mw_mfg`) have no PV
output, so `_levelization_factor` returns 1.0 by design and their rebuilt
workbooks are **byte-identical** to baseline (0 diffs each).

### Rebuild diff counts (all 14 cases, `baseline_workbooks/` vs a fresh rebuild)

| Case | Diffs |
|---|---|
| factory_a_case_1 | 344 |
| factory_a_case_2 | 342 |
| factory_a_case_3 | 342 |
| factory_a_case_4 | 348 |
| factory_a_case_5 (DPPA) | 2 |
| factory_a_case_6 (DPPA) | 2 |
| thailand_rofu_case_1 | 357 |
| thailand_rofu_case_2 | 357 |
| thailand_rofu_case_3 | 357 |
| thailand_rofu_case_4 | 357 |
| thailand_rofu_case_5 | 357 |
| thailand_rofu_case_6 | 357 |
| vietnam_case_bess_arbitrage_5mw | 0 |
| vietnam_case_bess_arbitrage_5mw_mfg | 0 |

factory_a_case_5/6 (grid-CfD DPPA) diff on only 2 Assumptions-sheet cells
(the optimized-EVN-bill and served-energy-retail-value derivations) because
the DPPA settlement path does not route the ESCO energy line through
`optimized_evn_bill_vnd` the way cases 1-4 do; the movement is still present,
just isolated to fewer cells.

Two independent spot checks, both to full floating-point precision:

- **Thailand case_1**: savings 262196.1000000001 to 272946.8451088329, ratio
  1.041002688860867 = 1/lambda exactly. Optimized bill moved to
  570496.364891167 = `843443.21 - 272946.8451088329` (bau minus the new
  savings), **not** `bau_bill / lambda` or `optimized_bill / lambda`.
- **Vietnam case_1**: served-energy retail value 538254.76341496 to
  564878.2989999368, ratio 1.0494627031557764 = 1/lambda exactly. Same ratio
  on the ESCO energy revenue base line (484429.287073464 to
  508390.4690999431), since that line is a scalar multiple of served-energy
  value.

### Invariant: capex, debt schedule, and O&M did not move

**Verdict: HOLDS on all 14 cases.** Checked two independent ways:

1. **Exhaustive cell diff.** `compare_workbooks` performs a full cell-by-cell
   scan of every sheet, so any capex/debt/O&M cell that changed would appear
   in the diff list. Every diffed row across all 12 non-trivial cases was
   inventoried and resolved to its row label; none matched a raw capex,
   debt-schedule (opening/closing balance, interest, principal repayment,
   debt service), O&M, replacement-cost, or capex-driven-depreciation line.
   The only rows that moved are: the three de-levelized Assumptions lines
   (optimized bill, demand-savings base, served-energy retail value / ESCO
   revenue base) and everything mechanically downstream of them (DSCR,
   equity/project IRR, NPV, payback, ROI, per-year cash flow, buyer savings).
   DSCR moving is expected and correct: its numerator (CFADS, driven by
   revenue) changed while its denominator (the debt schedule) did not.
2. **Direct named-cell comparison.** `PV_CAPEX`, `BESS_CAPEX`, `OTHER_CAPEX`,
   `TOTAL_CAPEX`, `DEBT_FRACTION`, `DEBT_RATE`, `DEBT_TERM_YEARS`,
   `DEBT_PRINCIPAL`, `DEBT_PAYMENT`, and `OM_YEAR1` were read directly from
   both the baseline and the rebuilt workbook for all 12 non-trivial cases.
   All 10 named cells were identical, value for value, on every case.

Nothing was scaled that depends on debt or O&M rather than PV production.

### Step 3: Vietnam storage-attributable residual

The correction is derived purely from PV's own levelization ratio and
applied uniformly to the pooled served-to-load energy series
(`project_served_pv_kwh` = PV-to-load + storage-to-load, when
`can_grid_charge` is false), which drives `esco_energy_revenue_vnd`. Storage
dispatch does not carry PV's degradation curve, so the fraction of that
pooled series contributed by storage bounds how much of the correction may
be mis-attributed to storage rather than PV, on that one revenue line:

| Case | PV-to-load (kWh) | Storage-to-load (kWh) | Storage share of served pool | Bound (share x 4.946270 pct) |
|---|---|---|---|---|
| case_1 | 3,764,123 | 1,889,551 | 0.3342 | 1.65 pct |
| case_2 | 3,710,296 | 2,433,129 | 0.3961 | 1.96 pct |
| case_3 | 3,487,762 | 2,720,270 | 0.4382 | 2.17 pct |
| case_4 | 3,345,178 | 0 (no storage) | 0.0000 | 0.00 pct |
| case_5 | 3,710,296 | 2,433,129 | 0.3961 | 1.96 pct |
| case_6 | 3,855,551 | 338,566 | 0.0807 | 0.40 pct |

This bound applies **only** to the served-energy / ESCO-energy-revenue line.
The demand-charge savings and the aggregate `year_one_bill_before_tax` /
`year_one_demand_cost_before_tax` REopt outputs are total, undecomposed
quantities: REopt does not report a PV-only or storage-only counterfactual
bill, so **the storage-attributable share of total bill savings is not
separable from these outputs alone.** The table above is the honest limit of
what the saved `results.json` files support; no single blended percentage is
reported because per-case storage share ranges from 0 to 43.8 percent and a
weighted average would misrepresent the individual cases.

### Test coverage added

`proforma_vietnam/tests/test_levelization.py` gained
`EndToEndDeLevelizationTests`, which drives
`calculate_esco_pro_forma_from_reopt_results` (the actual call site every
rebuild path uses) with a fixture carrying both `year_one_energy_produced_kwh`
and a differing `annual_energy_produced_kwh`, and asserts
`demand_charge_savings_vnd` equals the REopt-reported (levelized) savings
divided by lambda. Verified to actually fail (5000.0 instead of the expected
5555.56) when the `_apply_de_levelization` call is temporarily removed from
the wrapper, then restored. Previously only the two helper functions were
unit-tested directly; nothing pinned that the wrapper itself still calls
them.

### Suites run (2026-09-08)

Thailand 126/126, Vietnam 521/521 (at or above the 514 floor set in the task
brief), tariff (`reoptjl/test/test_thailand_tariff.py`) 14/14. No pinned test
in any of the three suites changed state, consistent with Task 4 Step 10's
finding that neither suite covers `calculate_esco_pro_forma_from_reopt_results`
with an absolute-value assertion on this path.

## 10. 2026-09-13 sizing objective: US incentive defaults removed from the Vietnam solve

Found by the fade-aware sizing probe on the research line
(`battery-soh-fade`, note `docs/superpowers/notes/2026-09-12-fade-aware-sizing-research.md`
there). The Vietnam builder sent no incentive or tax fields, so REopt
optimised with its US defaults: 30 percent ITC and 5-year MACRS with 100
percent bonus on PV and storage, 26 percent tax, 1.66 percent electricity
escalation, 2.5 percent O&M escalation, and a 6.24 percent offtaker discount
rate that, with `third_party_ownership` false, also replaced the owner rate
the case sent. REopt's own echo showed `initial_capital_costs_after_incentives`
at 51 percent of `initial_capital_costs`. The pro forma books none of this,
so the optimiser bought PV and batteries at half price and discounted at 6.24
percent. The Thailand builder had zeroed all of it since 2026-09-05 (its "C2
critical"); the Vietnam builder now does the same: owner rate as both
discount rates, CIT standard rate as both tax rates, the case's EVN energy
escalation and O&M escalation, zero ITC / MACRS on both technologies (an
explicit case.json value for an incentive key still wins).

Effect on the kept cases (old = 2026-09-12 solves, new = 2026-09-13; both
scored by this line's pro forma with the 100 percent year-10 replacement):

| case | PV kW old / new | BESS kW / kWh old / new | capex USD old / new | equity NPV old / new | equity IRR old / new | min DSCR old / new |
|---|---|---|---|---|---|---|
| factory_a/case_1 | 4,568 / 3,006 | 1,452 / 5,679 to 461 / 1,825 | 2,990,365 / 1,698,557 | 773,960 / 993,689 | 16.5% / 25.0% | -0.92 / 0.50 |
| factory_a/case_2 | 5,448 / 2,829 | 1,611 / 9,461 to 306 / 1,451 | 3,879,459 / 1,556,569 | 262,548 / 559,066 | 11.6% / 18.9% | -1.68 / 0.44 |
| factory_a/case_3 | 4,649 / 1,804 | 1,258 / 7,822 to 412 / 1,457 | 3,270,852 / 1,073,495 | -177,968 / 308,612 | 8.7% / 16.9% | -1.74 / -0.22 |
| factory_a/case_4 | 3,243 / 2,436 | 0 / 0 to 0 / 0 | 1,556,758 / 1,169,156 | 440,925 / 529,270 | 16.8% / 21.1% | 1.17 / 1.33 |
| factory_a/case_5 | 5,448 / 2,829 | 1,611 / 9,461 to 306 / 1,451 | 3,879,459 / 1,556,569 | 759,543 / 1,137,682 | 14.8% / 28.4% | -1.51 / 0.91 |
| factory_a/case_6 | 5,914 / 5,914 | 592 / 1,184 to 592 / 1,184 | 3,028,160 / 3,028,160 | 1,929,382 / 1,929,343 | 25.7% / 25.7% | 1.38 / 1.38 |
| bess_arbitrage_5mw | 0 / 0 | 5,000 / 25,000 to 5,000 / 25,000 | 3,400,000 / 3,400,000 | 3,436,606 / 3,436,606 | 54.3% / 54.3% | -6.13 / -6.13 |
| bess_arbitrage_5mw_mfg | 0 / 0 | 5,000 / 25,000 to 5,000 / 25,000 | 3,400,000 / 3,400,000 | 578,999 / 578,999 | 18.1% / 18.1% | -7.29 / -7.29 |

The ESCO cases lose 45 to 60 percent of their PV and 70 to 85 percent of
their battery and gain 200,000 to 490,000 USD of equity NPV; case_3 turns
positive. The pinned cases (case_6, the two arbitrage cases) keep their
sizes and, with the incentives never reaching the pro forma, their numbers.
The Vietnam runner also gained the Thailand runner's completeness guard
(`_is_complete`): `process_results` saves the status before the output
sections, and case_4's first re-solve was written from inside that window.
Memo, decks and the negotiation sweep outputs that quote the old Vietnam
sizes are stale until reissued.
