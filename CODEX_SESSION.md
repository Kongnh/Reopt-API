# Codex Session Handoff

Last updated: 2026-06-12

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master` (`[ahead 16]` of `origin/master`).
- **2026-06-12 CEBA DPPA Buyer Decision Journey deck delivered:**
  `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`.
  The editable artifact-tool deck contains 24 main training slides plus 6
  backup slides, with speaker notes on all 30 slides. Presenter: Cong Nguyen,
  Vietnam Clean Energy Manager, Allotrope Partners. Source basis is current
  through `2026-06-12`; numerical Kpp, 360 VND/kWh service fee, and
  163.3 VND/kWh balancing examples remain explicitly labeled as
  training/model assumptions rather than confirmed current regulated values.
  Verification: data ledger passed; final layout QA `0 errors, 0 warnings`;
  PPTX package has 30 slides, 30 notes slides, 0 empty files, and no media
  dependencies. Final QA score: `40/45`, with no dimension below 4.
- **2026-06-12 detailed facilitator narrative delivered:**
  `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026_Slide_Narrative.md`.
  The Markdown guide covers all 30 slides with objectives, detailed talk
  tracks, buyer prompts/actions, caveats, and transitions. Validation confirmed
  24 main-slide and 6 backup-slide narrative sections.
- **2026-06-11 CD7 alignment pass (committed, 112 tests green):** settlement
  aligned to the official NSMO CD7 simulation deck — k is price-only
  (CFMP = FMP × k; `Q_adj = Q_re_meter / Kpp`, k removed from the volume
  path), CfD settles on `min(Q_c, Q_Khc)` per CD7 Ví dụ 4, C_cl default
  163.3, CD7 Ví dụ 1 reproduced exactly in a new acceptance test. PV
  depreciation now explicit/configurable (`pv_depreciation_years`, 7-20 per
  Circular 45/2013, default 20). Battery replacement moved to year 11 in all
  case JSONs with a new `battery_replacement_year` assumptions override (no
  REopt re-run needed). Buyer evaluation extended to 10-year + lifetime
  cumulative savings; sweep buyer gate = 10yr AND lifetime (Year 1 context
  only). See SESSION_NOTES.md "2026-06-11 (later)".
- **Headline numbers after CD7 alignment** (supersede the table below):
  case_5 equity IRR 16.9%, NPV $1.52M, min DSCR 1.14x, payback 9.1y, buyer
  lifetime −9.3%; case_6 equity IRR 26.9%, NPV $2.54M, min DSCR 1.50x,
  payback 4.7y, buyer −14.4% all horizons. Sweeps: 0/36 balanced both;
  case_5 buyer 16/36 but lender 2/36; case_6 seller 36/36, lender 32/36,
  buyer 0/36. The follow-up lower-strike sweep also found 0/20 balanced:
  buyer-positive terms at 1,300 and below fail the 1.20x lender DSCR gate.
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Latest commits:
  - `13e25cd6` Run case_6 lower-strike sensitivity
  - `25799b46` Refresh Factory A cases and DPPA studies
  - `139f8f01` Redesign investment report workbook
  - `5a74cc86` Add DPPA negotiation sweep
  - `46382938` Align DPPA settlement and lifecycle economics
- **2026-06-11 model audit + fixes (committed):**
  - **Critical settlement fix:** buyer charges (C_DN/C_DPPA/C_CL) now settle on
    `Q_Khc = min(load, Q_adj)` per ND57 / `vietnam_market_context.md`, not on
    full `Q_adj`. On case_5 the old model billed the buyer for 1.40 GWh/yr it
    never consumed (≈ $106k/yr); Year-1 buyer savings move −28.7% → −14.9% at
    strike 2000. `q_khc_kwh` + `matched_retail_value_vnd` now flow through
    settlement, cash flow, and workbook (sweep reconciler label updated).
  - **Real-world mechanics added:** PV degradation (auto from REopt
    `PV.degradation_fraction`, 0.5%/yr; lost energy repurchased at retail),
    battery replacement auto-derived from REopt inputs with a configurable
    override (Factory A cases: $1.21M in year 11), Vietnam CIT 5-year loss
    carryforward + holiday clock from first
    profitable year (Circular 78/2014), `om_escalation_rate` input (default 0),
    and a stale `capacity_multiplier` display bug fixed in `cash_flow.py`.
  - **Assumption review:** PV depreciation stays configurable at 7-20 years
    with default 20; `k = 1.026` is only a fallback/default because actual
    cases use hourly CFMP; fixed FX remains a simplifying assumption requiring
    sensitivity before investor-facing use.
- **2026-06-11 consultant workbook redesign (committed):** every
  `vietnam_report_*.xlsx` now opens on three styled front sheets —
  Executive Summary (system, contract terms, seller returns, buyer outcome,
  model-basis notes), Buyer Analysis (Year-1 cost stack + 25-year savings
  table + cumulative chart), Developer Returns (sources & uses, return
  metrics incl. minimum DSCR, annual CFADS/DSCR/equity CF + chart). Legacy
  sheets remain as appendix with number formats. New offline CLI:
  `python -m proforma_vietnam.rebuild_report --case-dir <dir>` rebuilds the
  workbook from saved results.json/assumptions.json without Django/REopt.
- **DPPA negotiation sweep committed:** fixed-system sweep tooling now supports
  reference-case selection and custom inclusive strike grids.
- **Case_6 lower-strike result:** 0/20 balanced across 1,200-1,400 VND/kWh.
  Closest buyer-positive term is `strike_1300_volume_70`: buyer lifetime
  savings `+0.46%`, seller equity IRR `17.85%`, minimum DSCR `1.143x`.
- **2026-06-10 global CfD escalation updated to 4% (committed):** changed the global default, documented it, set case_5/case_6 source JSON explicitly to `0.04`, and regenerated both cases and negotiation sweeps. Generated assumptions explicitly contain `cfd_strike_escalation_rate: 0.04`.
- **2026-06-10 Factory A case_6 built (committed):** cloned clean `case_5`, fixed PV at `5,914 kW`, fixed the minimum two-hour BESS at `592 kW / 1,184 kWh`, regenerated the 8760 DPPA contract-volume profile from case_6 dispatch, and ran REopt + the Vietnam financial model end to end. Final run UUID: `86acaddb-4dc9-4654-affb-12db1c2bfacf`; status `optimal`.
- **Pre-CD7 audit results are superseded** by the headline numbers above.
  The retained case_5/case_6 run UUIDs are `ea6e1964-f331-45e4-94e7-1e712e45464c`
  and `96571e84-2d04-401b-8135-e0c9766ad445`; their saved reports have been
  rebuilt using the CD7-aligned post-processing model.
- **Reconciliation:** both sweeps pass direct-calculation and regenerated-workbook reconciliation at the configured tolerance.
- **2026-06-09 work (committed):** found and removed a non-physical 24-hour ~40 MW spike in `Sample Load Profile/Emivest.csv` (one day, ~8% of annual energy, real peak only ~2.4 MW). Wrote `Sample Load Profile/Emivest_clean.csv`, repointed `case_1..5/case.json` to it, and re-ran all five cases end-to-end on docker (all `optimal`). For `case_5`, also refreshed the 8760 CfD contract-volume series from clean `case_2` Q_re_meter so the DPPA settlement is fully consistent with the clean-load baseline.
- **New deck:** `outputs/vietnam_case/factory_a/Factory_A_Solar_BESS_Case_Study.pptx` — 7 slides, English, corporate white background, native editable PPTX charts + table. Built by `outputs/vietnam_case/factory_a/build_deck.py` from `outputs/vietnam_case/factory_a/clean_metrics.json`. Scope: case_1..4 only (case_5 DPPA excluded). Financial lens = ESCO developer (Project/Equity IRR, DSCR, 70% debt). Verified visually via LibreOffice → PDF → PNG render of all 7 slides.
- **Deck status after corrected-model rebuild:** `clean_metrics.json` is refreshed,
  but the existing PPTX is stale and must not be presented. Its narrative calls
  case_3 bankable, while the corrected model gives case_3 minimum DSCR `0.83x`.
- **2026-06-09 graphify map:** built `graphify-out/` for `reoptjl` + `proforma_vietnam`, then added a deterministic Vietnam study layer covering `outputs/vietnam_case/factory_a`, `DPPA DOC`, `Sample Load Profile`, `vietnam_market_context.md`, `roadmap.md`, and `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`. Outputs: `graphify-out/graph.html`, `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, and `graphify-out/VIETNAM_STUDY_GRAPH_REPORT.md`. Final merged graph: 2,505 nodes, 3,691 edges, 248 communities. No LLM backend key was configured, so document/data mapping used deterministic extraction rather than semantic LLM extraction.
- Git state at close: implementation and generated Factory A artifacts are
  committed through `13e25cd6`. Remaining dirty files are this handoff update,
  `SESSION_NOTES.md`, and pre-existing untracked source PDFs, graphify output,
  and `tmp_dppa_simulation_extract.txt`.
- Stale workbooks deleted (kept only run-uuid-matched): case_5 `bc785b6f`,
  `bf7a908a`; case_6 `86acaddb`.
- Docker Desktop was unavailable on 2026-06-11; workbooks were regenerated
  offline via `rebuild_report` (the report is pure post-processing) and
  verification used local pure-Python `unittest` (112 tests, OK).
- Detailed delivery log in `SESSION_NOTES.md` (2026-06-11 entry).

## Completed Context

- Phase 1 Vietnam EVN tariff builder and acceptance gate are complete.
- Phase 2 Vietnam ESCO pro forma, case builder, report generator, and USD-facing workbook flow are complete.
- Phase 3 DPPA settlement layer is implemented, validated end-to-end against the 8760 FMP series, and committed (`290b8dc2`). `grid_dppa_cfd` contract type (ND57 Điều 14–18 + bilateral CfD) ships with the Phase 2 reference gate preserved byte-identically when `dppa.type = "none"`.
- Factory A case_5 (strike 2000 VND/kWh, 8760 contract volume shaped to case_2 Q_re_meter incl. would-be export) runs end-to-end on docker; all four new DPPA sheets + the Year 1 BAU vs DPPA sheet render correctly; year-one settlement math matches hand-computed totals at 0.000% delta.
- All five Factory A cases (case_1 → case_5) regenerated with honest BESS capex after the `bess_capex_usd=0` bug fix (`8e0c2d1c`).

## Active Product Direction

Resume the case_6 financing sensitivity around the buyer-positive
`1,300 VND/kWh` / 70% volume terms. Preserve the delivered CEBA deck and the
prior `outputs/ceba_training/CEBA_DPPA_Mechanisms_Pricing.pptx` /
`build_deck.py`.

## Design Questions Resolved

All five Phase 3 design questions remain resolved (see [proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md](proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md)). New decisions from the 2026-06-07 validation session:

- **Customer-side spot price = CFMP × K_pp** (not FMP × Q_adj). CFMP series loaded from `DPPA DOC/fmp_cfmp_vn.json`.
- **(2026-06-11) Buyer settlement quantity = Q_Khc = min(load, Q_adj)** per ND57 / `vietnam_market_context.md`: `C_DN = Q_Khc × CFMP × K_pp`, and C_DPPA/C_CL also settle on Q_Khc. Excess generation above hourly load stays with the generator as FMP spot revenue and is never billed to the buyer.
- **Curtailed PV under self-consumption REopt run is credited as DPPA grid export at FMP.** Optimizer stays in self-consumption mode (no FMP signal); the generator owns the meter under DPPA and dumps surplus rather than curtailing. Case_2's 1.57 GWh/yr of curtailed PV → +$435k year-1 generator revenue under DPPA accounting.
- **CfD volume shape**: 8760-hour series matched to expected `Q_re_meter` (including would-be-curtailed surplus), not a flat scalar.

## Honest Factory A Economics

**All case rows below reflect the corrected 2026-06-11 post-processing model.
case_1..4 were rebuilt offline from their clean-load optimizer results after
refreshing saved assumptions with year-11 battery replacement.** ESCO developer
lens, 70% debt:

| Case | Description | PV (kW) | BESS (kW / kWh) | Clean self-supply | Total capex | Equity IRR | NPV (USD) | Payback |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| case_1 | Current TOU + PV + BESS | 5,322 | 1,662 / 8,250 | 59.5% | $3.68M | 16.1% | $1.17M | 9.9 yr |
| case_2 | QĐ963 TOU + PV + BESS (baseline) | 5,914 | 1,796 / 10,699 | 65.5% | $4.27M | 13.9% | $0.87M | 12.4 yr |
| case_3 | QĐ963 + two-component pilot | 5,765 | 1,830 / 11,693 | 65.8% | $4.32M | 10.3% | $0.07M | 14.3 yr |
| case_4 | QĐ963 TOU + PV only | 3,453 | — | 35.8% | $1.66M | 17.9% | $0.69M | 9.6 yr |
| case_5 | QĐ963 + PV + BESS + grid_dppa_cfd | 5,914 | 1,796 / 10,699 | — | $4.27M | 16.9% | $1.52M | 9.1 yr |
| case_6 | case_5 settings + minimum 10% / 2-hour BESS | 5,914 | 592 / 1,184 | — | $3.03M | 26.9% | $2.54M | 4.7 yr |

- case_5 minimum DSCR is `1.14x`; case_6 minimum DSCR is `1.50x`. Lender lens,
  not just IRR, still separates
  the two sizings.

- `case_5` clean-load run UUID: `bc785b6f-2b82-4684-b583-3010ca6a9904`. Its load series and optimizer sizing match clean `case_2` exactly; its CfD contract-volume series also matches clean `case_2` Q_re_meter hour by hour (7,664,883.239 kWh/year).
- Cleaning the load most affected case_3: on clean data the battery is **1,830 kW** (was 4,783 kW on dirty data, where it chased the spike). case_3 still shaves grid peak 2,428 → 1,311 kW (−46%), demand-charge savings $128,781/yr.
- Notable: case_4 (PV-only) still edges case_2 (PV+BESS) on equity IRR — at current BESS prices ($80/kW + $120/kWh) the battery earns its keep on clean energy share and absolute savings/NPV, not on IRR. case_5 (DPPA at strike 2000) loses to case_2 because the CfD is a one-way transfer at this strike.

## Resume Here Next Session

1. Design and run a case_6 financing sensitivity around the buyer-positive
   `1,300 VND/kWh` terms.
2. Add an FX sensitivity before using 25-year USD-facing metrics in an
   investor-facing deliverable.
3. Push the committed work when ready (`master` is ahead of `origin/master`).

## Todo

- [x] Build `case_5` end-to-end on docker and validate the four new DPPA sheets render.
- [x] Wire CFMP series into settlement (`C_DN = Q_Khc × CFMP × K_pp`).
- [x] Credit case_2 curtailed PV as DPPA grid export under DPPA accounting.
- [x] Add Year 1 BAU vs DPPA summary sheet.
- [x] Fix DPPA-VND-into-USD-cash-flow unit mixing.
- [x] Fix `bess_capex_usd=0` override bug; regenerate all five case assumptions/workbooks.
- [x] Commit Phase 3 + the five fixes (`290b8dc2`, `8e0c2d1c`).
- [ ] Push to `origin/master` (branch is now ahead by 12 commits).
- [x] Manual cleanup: `*_v5.xlsx`, `~$*.xlsx` lock, and stale parent `vietnam_report_b729db40-*.xlsx` are gone (verified 2026-06-11); non-current-run case workbooks also deleted.
- [x] Decide next direction: fixed-system DPPA commercial negotiation sweep.
- [x] Approve and commit negotiation-sweep design (`b417ee9f`).
- [x] Implement the fixed-system DPPA negotiation sweep and generated output package.
- [x] Reconcile `2000 VND/kWh` / `100%` against clean `case_5` calculation and workbook.
- [x] Generalize the negotiation runner and run the 36-scenario sweep against fixed-system `case_6`.
- [x] Set global CfD strike escalation to 4%, regenerate case_5/case_6, and rerun both negotiation sweeps.
- [x] Review the zero-balanced-deal result and choose the next direction (became the 2026-06-11 model audit).
- [x] (2026-06-11) Audit model vs real-world practice; fix Q_Khc settlement, degradation, battery replacement, CIT carryforward/holiday clock, O&M escalation, capacity_multiplier bug.
- [x] (2026-06-11) Redesign vietnam report into consultant-style workbook (Executive Summary / Buyer Analysis / Developer Returns) + add offline `rebuild_report` CLI.
- [x] (2026-06-11) Regenerate case_5/case_6 workbooks and rerun both 36-scenario sweeps with the corrected model; reconciliations pass; stale workbooks deleted.
- [x] Regenerate case_1..4 workbooks with the corrected model (`rebuild_report`) and refresh `clean_metrics.json`.
- [x] Build and verify the approved CEBA DPPA Buyer Decision Journey deck;
  delivered `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`
  with 30 slides, speaker notes, and final QA passing.
- [x] Commit the 2026-06-11 audit + workbook redesign + regenerated artifacts.
- [x] Run the case_6 lower-strike sensitivity (1,200-1,400 VND/kWh); 0/20 balanced because buyer-positive terms fail lender DSCR.
- [x] Resolve depreciation and k assumptions; keep fixed FX flagged for sensitivity.
- [ ] Run case_6 financing sensitivity around buyer-positive 1,300 VND/kWh terms.
- [x] (2026-06-09) Clean the 24-hour ~40 MW spike in `Emivest.csv`; re-run case_1..4 on `Emivest_clean.csv`.
- [x] (2026-06-09) Build the 7-slide English CEBA case-study deck (`Factory_A_Solar_BESS_Case_Study.pptx`) from cleaned case_1..4 data.
- [x] (2026-06-09) Build graphify code + Vietnam study map under `graphify-out/`.
- [x] Re-run case_5 on `Emivest_clean.csv` and refresh its CfD volume from clean case_2 Q_re_meter.
- [x] Build case_6 with fixed `5,914 kW` PV and `592 kW / 1,184 kWh` BESS; regenerate its DPPA volume and run the final financial workbook.
- [ ] Decide whether to commit the 2026-06-09 cleaned-load re-run + deck artifacts.
- [x] Confirm Docker stack is not running (Docker Desktop unavailable on 2026-06-10).

## Session Close Procedure

Before ending a future working session:

1. Update this file's `Last updated` date.
2. Summarize files changed and why.
3. Record tests or checks run, including failures.
4. Update the todo list so completed work is checked off.
5. Add the current commit hash if a commit was made.
6. Update `SESSION_NOTES.md` with detailed notes needed to preserve context beyond this concise handoff.
7. Record any blockers or assumptions needed to resume cleanly.
