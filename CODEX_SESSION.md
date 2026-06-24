# Codex Session Handoff

Last updated: 2026-06-24 (E2E re-run)

> Concise handoff only. Full chronological detail lives in `SESSION_NOTES.md`
> (newest entry at top). Keep this file short — prune history when it grows.

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`, ahead of `origin/master` (not pushed). Remote:
  `https://github.com/Kongnh/Reopt-API.git`.
- **E2E re-run done (2026-06-24) — case_1..6 all `optimal`, reconciled.** Prior
  artifacts archived to `outputs/vietnam_case/factory_a/_archive/pre_rerun_2026-06-24/`
  (payload/assumptions/results/workbook per case + `MANIFEST.txt`); each case dir now
  holds its `case.json` input plus the fresh artifacts. New run UUIDs (workbooks):
  case_1 `3dd5bf1f-fa51-4f1e-aa64-d24ae11a1820`, case_2 `554ee85a-6f3c-4077-8dcb-0145406d4e6e`,
  case_3 `b33f4a1f-9de5-4228-ba55-4db9578de73a`, case_4 `36f36f61-c28e-4c8a-bc9d-66f21300c28e`,
  case_5 `c73574b2-1170-4611-a6c8-8a012bd1f50d`, case_6 `5b999b24-d8c1-4d91-aa2e-1ea0a973af38`.
- **REopt sizing is NOT bit-reproducible vs the June baseline.** Cases 1/2/3/5 have
  *identical payloads* yet the re-solve returned slightly larger PV+BESS (e.g. case_1
  BESS 8,640 vs 8,250 kWh, +4.7%); constrained cases 4 (PV-only) and 6 (fixed BESS)
  match exactly. This is the REopt solver/Julia-package layer, not the proforma — the
  schema refactor stays byte-identical given the same `results.json`. Only material
  economic move: case_1 payback 9.9 → 11.6 yr (bigger, costlier battery). Flag for any
  bit-identical third-party expectation; likely a REopt Julia package version pin.
- **Uncommitted (2026-06-24) — proforma schema refactor, 117 tests green,
  output byte-identical.** `proforma_vietnam` now follows SAM's split: imperative
  compute, declarative presentation. New `structures.py` (ESCO/DPPA +
  `direct_ownership` placeholder), `proforma_schema.py` (`RowSpec` registry +
  per-sheet views), versioned `defaults/vietnam_defaults.json`. `xlsx_builder.py`
  builds the Cash Flow / Tax / Debt / DPPA Annual / Summary / Developer Financials
  sheets from the schema (7 duplicated constants deleted); bespoke sheets
  unchanged. New `tests/test_proforma_schema.py`. No financial numbers changed —
  verified `schema.columns()` reproduces every old constant exactly. See
  `proforma_vietnam/SCHEMA.md` + SESSION_NOTES.md "2026-06-24".
- **Last committed baseline (through `13e25cd6`) — CD7-aligned model.** Headline
  economics: case_5 equity IRR 16.9%, NPV $1.52M, min DSCR 1.14x, payback 9.1y,
  buyer lifetime −9.3%; case_6 equity IRR 26.9%, NPV $2.54M, min DSCR 1.50x,
  payback 4.7y, buyer −14.4%. Negotiation sweeps: 0 balanced deals; buyer-positive
  strikes (≤1,300 VND/kWh) fail the 1.20x lender DSCR gate.
- Recent commits: `13e25cd6` case_6 lower-strike sweep · `25799b46` refresh
  Factory A cases/studies · `139f8f01` redesign report workbook · `5a74cc86` DPPA
  negotiation sweep · `46382938` align DPPA settlement & lifecycle economics.

## Active Product Direction — NEXT OBJECTIVE

**Re-run the six Factory A case studies end-to-end after the schema refactor,
validate outputs and artifacts, and harden the model + Excel for independent
third-party review.** The refactor is byte-identical by construction, so the
re-run is a confirmation gate, not a numbers change. Priorities:

1. **E2E re-run (case_1..6). — DONE 2026-06-24.** Ran on Docker; all 6 `optimal`,
   one fresh workbook each, stale workbooks archived not duplicated. Reconciled vs
   the June baseline (see Honest Economics table + Current State for the REopt sizing
   drift). Offline path if Docker is down: `python -m proforma_vietnam.rebuild_report
   --case-dir <dir>` (pure post-processing).
2. **Model auditing.** Make the assumptions a third party would scrutinise
   explicit and defensible: fixed FX over 25y (add FX sensitivity), PV
   depreciation 7-20y (default 20), k vs hourly CFMP, K_pp, CfD-cap on matched
   volume, Q_Khc settlement, CIT holiday/carryforward. Cross-check against
   `vietnam_market_context.md` and the CD7 deck; list any code-vs-doc deltas.
3. **Excel for external validation.** Ensure each workbook is self-auditable:
   complete Assumptions sheet, Model Basis notes, traceable line-items (now schema-
   driven), and clear VND/USD labeling. Resolve the open `_add_usd_aliases`
   question (USD == VND numerically, no FX applied in `cash_flow.py`) before any
   third party reviews USD figures.

## Honest Factory A Economics (CD7-aligned model; ESCO developer lens, 70% debt)

Numbers below are the **2026-06-24 E2E re-run** (UUIDs in Current State); they
supersede the June baseline. Deltas vs the prior committed baseline are minor
(REopt sizing drift, see Current State) — case_1 is the only meaningful move.

| Case | Description | PV (kW) | BESS (kW / kWh) | Total capex | Equity IRR | NPV (USD) | Min DSCR | Payback |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| case_1 | Current TOU + PV + BESS | 5,421 | 1,685 / 8,640 | $3.77M | 15.7% | $1.12M | 1.09x | 11.6 yr |
| case_2 | QĐ963 TOU + PV + BESS (baseline) | 5,944 | 1,799 / 10,824 | $4.30M | 13.8% | $0.86M | 1.01x | 12.5 yr |
| case_3 | QĐ963 + two-component pilot | 5,830 | 1,872 / 11,977 | $4.39M | 10.2% | $0.04M | 0.82x | 14.4 yr |
| case_4 | QĐ963 TOU + PV only | 3,453 | — | $1.66M | 17.9% | $0.69M | 1.13x | 9.6 yr |
| case_5 | QĐ963 + PV + BESS + grid_dppa_cfd | 5,944 | 1,799 / 10,824 | $4.30M | 16.8% | $1.52M | 1.13x | 9.1 yr |
| case_6 | case_5 + minimum 10% / 2-hour BESS | 5,914 | 592 / 1,184 | $3.03M | 26.9% | $2.54M | 1.50x | 4.7 yr |

- **case_2 min DSCR 1.01x** — razor-thin lender coverage, newly surfaced by the
  schema-driven workbook (prior baseline showed "—"). Flag for any debt review.
- case_4 (PV-only) edges case_2 on IRR; the battery earns its keep on clean-energy
  share and absolute NPV, not IRR. case_5 DPPA at strike 2000 loses to case_2
  because the CfD is a one-way transfer at that strike.
- Prior June-baseline retained UUIDs (now in `_archive/pre_rerun_2026-06-24/`):
  case_5 `ea6e1964-f331-45e4-94e7-1e712e45464c`, case_6
  `96571e84-2d04-401b-8135-e0c9766ad445`.

## Resolved Model Decisions (audit-relevant; see ESCO_CONTRACT_MODEL_DESIGN.md)

- Customer-side spot = **CFMP × K_pp** (CFMP from `DPPA DOC/fmp_cfmp_vn.json`).
- Buyer settlement quantity **Q_Khc = min(load, Q_adj)**; C_DN/C_DPPA/C_CL settle
  on Q_Khc. Surplus generation stays with the generator at FMP, never billed to
  the buyer.
- **k is price-only** (CFMP = FMP × k); `Q_adj = Q_re_meter / K_pp`. C_cl default
  163.3 VND/kWh. CfD settles on `min(Q_c, Q_Khc)` (CD7 Ví dụ 4). CD7 Ví dụ 1 is
  reproduced exactly by an acceptance test.
- Curtailed PV (self-consumption REopt run) credited as DPPA grid export at FMP.
- CfD volume = 8760-hour series matched to expected Q_re_meter (incl. would-be
  surplus), not a flat scalar.
- VN defaults now centralized in `proforma_vietnam/defaults/vietnam_defaults.json`
  (CIT schedule, depreciation years, escalation, debt).

## Open Todo

- [x] E2E re-run case_1..6 after the schema refactor (2026-06-24) — all `optimal`,
  one fresh workbook each, reconciled vs prior baseline. Prior artifacts archived.
- [ ] **NEXT:** Model-audit pass + third-party-ready Excel (Active Direction steps 2–3).
- [ ] Resolve `_add_usd_aliases` USD==VND / FX question before external USD review.
- [ ] Run case_6 financing sensitivity around buyer-positive 1,300 VND/kWh terms.
- [ ] Add an FX sensitivity before investor-facing 25-year USD metrics.
- [ ] Decide whether to commit the 2026-06-24 schema refactor.
- [ ] Push `master` to `origin/master` when ready.
- [ ] (follow-up) Wire real `direct_ownership` compute; move
  `reoptjl/src/vietnam/evn_rates.py` tables to the versioned-defaults pattern.

## Blockers / Assumptions

- Docker Desktop has been intermittently unavailable; the report is pure
  post-processing, so `rebuild_report` regenerates workbooks offline when needed.
- ReoptAPI `.venv` uses `unittest` (no pytest); `openpyxl==3.1.5` was installed
  into it on 2026-06-24 to run the xlsx tests.
- Fixed FX (≈25,000 VND/USD) over 25y is a simplifying assumption, not confirmed
  practice — flag before investor/third-party use.
- The CEBA deck (`outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`)
  and `Factory_A_Solar_BESS_Case_Study.pptx` are prior deliverables; the latter is
  stale vs the corrected model (calls case_3 bankable; corrected min DSCR 0.83x).

## Session Close Procedure

Before ending a future working session:

1. Update `Last updated`.
2. Summarize files changed and why; record tests/checks run (incl. failures).
3. Check off completed todos; add the commit hash if a commit was made.
4. Add a detailed dated entry to `SESSION_NOTES.md`.
5. Record blockers/assumptions needed to resume cleanly.
6. Keep this file concise — move history into `SESSION_NOTES.md`.
