# Codex Session Handoff

Last updated: 2026-07-04 (model-audit pass + audit-grade Excel; uncommitted)

> Concise handoff only. Full chronological detail lives in `SESSION_NOTES.md`
> (newest entry at top). Keep this file short — prune history when it grows.

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`, last pushed commit `5280e92b`. Remote:
  `https://github.com/Kongnh/Reopt-API.git`. **Working tree has the
  uncommitted 2026-07-04 audit pass** (see below + SESSION_NOTES "2026-07-04").
- **Model-audit pass + third-party-ready Excel DONE (2026-07-04), 130 tests
  green, USD economics unchanged.** Summary:
  - `_add_usd_aliases` question resolved: engine computes in USD; new
    `exchange_rate_vnd_per_usd` kwarg on `calculate_vietnam_esco_cash_flow`
    restates `_vnd` keys as true VND (×25,000) while `_usd` keeps the computed
    values (`_finalize_currencies`). `report_data` comparison keys renamed
    `_usd`. Verified `npv_vnd/npv_usd == 25000` on all 6 cases.
  - New `proforma_vietnam/audit_sheets.py`: workbook now opens with Cover →
    Executive Summary → Assumptions (named cells, unit + source) → Model Basis
    → **Pro Forma (Audit)** (full cash flow as live Excel formulas incl. CIT
    clock + FIFO loss-carryforward schedule; engine outputs hardcoded and
    shaded; per-year + per-metric PASS/REVIEW tie-out) → **FX Sensitivity**
    (editable VND-depreciation scenarios) → prior sheets as appendix.
    `cash_flow` emits a `derivation` block + `calculate_fx_sensitivity()`.
  - All six Factory A workbooks regenerated offline and verified by full Excel
    COM recalculation: every check PASS, cover "ALL CHECKS PASS", per-year max
    |Excel−engine| = 0.0000 (incl. DPPA cases 5/6).
  - New `proforma_vietnam/MODEL_AUDIT.md` audit pack; design-doc strike-
    escalation default inconsistency fixed; Y1 BAU-vs-DPPA `q_adj` magic-number
    fallback replaced with configured K_pp.
  - Gotcha for future Excel work: never write empty-string cell values and
    never start prose strings with "=" — both corrupt the xlsx (regression
    test guards every built cell).
- **Workbook reorganisation (2026-07-04 later), 128 tests green.** Full case
  inputs now on Assumptions (case.json site/load/PV/storage groups via
  `case_config`, DPPA δ + FMP path, raw assumptions echo); duplicated record
  sheets dropped (ESCO 18→11 sheets, DPPA 23→14) with new compact "Technical
  Results" sheet; Dispatch Profile upgraded (original PV generation, PVWatts
  production-factor irradiation proxy, PV/grid→storage, PV→grid, curtailed
  columns; chart = peak-load week only, not 8760 h). 5/6 workbooks
  regenerated + COM-verified all-PASS; **case_3 workbook was locked open in
  the user's Excel — rerun `python -m proforma_vietnam.rebuild_report
  --case-dir outputs/vietnam_case/factory_a/case_3` after closing it.** See
  SESSION_NOTES "2026-07-04 (later)".
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
- **Committed `871b4f5d` (2026-06-24) — proforma schema refactor, 117 tests green,
  output byte-identical** (plus CEBA DPPA training deck, DPPA reference docs, and the
  refreshed Vietnam case outputs in the same commit). `proforma_vietnam` now follows SAM's split: imperative
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
- **History rewritten (2026-06-24, `git filter-repo`)** to purge `graphify-out/`
  (885 files / 40 MB) and `.superpowers/` from ALL history; both added to
  `.gitignore` and force-pushed. Files remain on disk locally (ignored). Backup
  bundle of the pre-rewrite repo saved to the session scratchpad. NOTE: every
  commit hash from the schema-refactor commit onward changed — re-clone any other
  checkout of this repo rather than pulling.
- Recent commits (post-rewrite): `5280e92b` stop tracking tooling artifacts ·
  `871b4f5d` schema refactor + CEBA deck + DPPA docs + refreshed outputs ·
  `91a03884` CEBA DPPA slide facilitator narrative · `ae97edec` CEBA DPPA buyer
  decision training deck.

## Active Product Direction — NEXT OBJECTIVE

**Re-run the six Factory A case studies end-to-end after the schema refactor,
validate outputs and artifacts, and harden the model + Excel for independent
third-party review.** All three steps are now DONE:

1. **E2E re-run (case_1..6). — DONE 2026-06-24.** Ran on Docker; all 6 `optimal`,
   one fresh workbook each, stale workbooks archived not duplicated. Reconciled vs
   the June baseline (see Honest Economics table + Current State for the REopt sizing
   drift). Offline path if Docker is down: `python -m proforma_vietnam.rebuild_report --case-dir <dir>` (pure post-processing).
2. **Model auditing. — DONE 2026-07-04.** Assumptions register + code-vs-doc
   cross-check in `proforma_vietnam/MODEL_AUDIT.md` (settlement math, CIT,
   depreciation all match docs; one doc-internal default inconsistency fixed).
   FX sensitivity added; `_add_usd_aliases` resolved (see Current State).
3. **Excel for external validation. — DONE 2026-07-04.** Workbooks are
   self-auditable: Cover/Assumptions/Model Basis/Pro Forma (Audit)/FX
   Sensitivity, live formulas with engine tie-out PASS on every case.

Next objective: commit the audit pass, then the case_6 financing sensitivity
around buyer-positive 1,300 VND/kWh terms (last open economics question).

## Honest Factory A Economics (CD7-aligned model; ESCO developer lens, 70% debt)

Numbers below are the **2026-06-24 E2E re-run** (UUIDs in Current State); they
supersede the June baseline. Deltas vs the prior committed baseline are minor
(REopt sizing drift, see Current State) — case_1 is the only meaningful move.

| Case   | Description                        | PV (kW) | BESS (kW / kWh) |             Total capex | Equity IRR | NPV (USD) | Min DSCR | Payback |
| ------ | ---------------------------------- | ------: | --------------: | ----------------------: | ---------: | --------: | -------: | ------: |
| case_1 | Current TOU + PV + BESS            |   5,421 |   1,685 / 8,640 | $3.77M | 15.7% | $1.12M |      1.09x |   11.6 yr |          |         |
| case_2 | QĐ963 TOU + PV + BESS (baseline)  |   5,944 |  1,799 / 10,824 | $4.30M | 13.8% | $0.86M |      1.01x |   12.5 yr |          |         |
| case_3 | QĐ963 + two-component pilot       |   5,830 |  1,872 / 11,977 | $4.39M | 10.2% | $0.04M |      0.82x |   14.4 yr |          |         |
| case_4 | QĐ963 TOU + PV only               |   3,453 |              — | $1.66M | 17.9% | $0.69M |      1.13x |    9.6 yr |          |         |
| case_5 | QĐ963 + PV + BESS + grid_dppa_cfd |   5,944 |  1,799 / 10,824 | $4.30M | 16.8% | $1.52M |      1.13x |    9.1 yr |          |         |
| case_6 | case_5 + minimum 10% / 2-hour BESS |   5,914 |     592 / 1,184 | $3.03M | 26.9% | $2.54M |      1.50x |    4.7 yr |          |         |

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

- [X] E2E re-run case_1..6 after the schema refactor (2026-06-24) — all `optimal`,
  one fresh workbook each, reconciled vs prior baseline. Prior artifacts archived.
- [X] Model-audit pass + third-party-ready Excel (2026-07-04) — audit_sheets.py,
  MODEL_AUDIT.md, 130 tests, all-cases Excel COM verification PASS.
- [X] Resolve `_add_usd_aliases` USD==VND / FX question — engine is USD;
  `_finalize_currencies` restates true VND at the contract rate (2026-07-04).
- [X] Add an FX sensitivity before investor-facing 25-year USD metrics —
  `calculate_fx_sensitivity` + live FX Sensitivity sheet (2026-07-04).
- [ ] **NEXT:** Commit the 2026-07-04 audit pass; then case_6 financing
  sensitivity around buyer-positive 1,300 VND/kWh terms.
- [X] Commit the 2026-06-24 schema refactor — committed `871b4f5d`.
- [X] Push `master` to `origin/master` — pushed; in sync at `5280e92b`. Also
  purged `graphify-out/`/`.superpowers/` from history and force-pushed.
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
