# Codex Session Handoff

Last updated: 2026-06-07

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Latest commits (this session):
  - `8e0c2d1c` Refresh case_1/3/4 outputs after bess_capex fix
  - `290b8dc2` Ship Phase 3 DPPA settlement with Factory A case_5
- Git state at close: working tree clean for tracked files; untracked artifacts remaining are an Excel-locked workbook copy `outputs/vietnam_case/factory_a/case_5/vietnam_report_*_v5.xlsx` and the pre-layout stale workbook `outputs/vietnam_case/factory_a/vietnam_report_b729db40-*.xlsx`. Both need manual cleanup after closing Excel.
- Detailed delivery log archived in `SESSION_NOTES.md` (2026-06-07 entry).

## Completed Context

- Phase 1 Vietnam EVN tariff builder and acceptance gate are complete.
- Phase 2 Vietnam ESCO pro forma, case builder, report generator, and USD-facing workbook flow are complete.
- Phase 3 DPPA settlement layer is implemented, validated end-to-end against the 8760 FMP series, and committed (`290b8dc2`). `grid_dppa_cfd` contract type (ND57 Điều 14–18 + bilateral CfD) ships with the Phase 2 reference gate preserved byte-identically when `dppa.type = "none"`.
- Factory A case_5 (strike 2000 VND/kWh, 8760 contract volume shaped to case_2 Q_re_meter incl. would-be export) runs end-to-end on docker; all four new DPPA sheets + the Year 1 BAU vs DPPA sheet render correctly; year-one settlement math matches hand-computed totals at 0.000% delta.
- All five Factory A cases (case_1 → case_5) regenerated with honest BESS capex after the `bess_capex_usd=0` bug fix (`8e0c2d1c`).

## Active Product Direction

Phase 3 ships. Next session picks from:

1. **Tune the DPPA deal terms.** At strike 2000 VND/kWh (above max FMP 1944), the CfD is a one-way buyer→seller transfer and case_5 is worse than case_2 on every KPI. Sweep strike (e.g. 1400, 1500, 1600) and/or shrink `cfd_contract_volume_kwh_per_hour` to find the break-even buyer savings curve.
2. **Pull `private_wire` forward from Phase 4** (Điều 25, bilateral pricing, no K_pp/k loss factors, no system service fees, no CfD overlay) if a client deal calls for it.
3. **Pull factory-side BESS forward from Phase 4** if a client deal needs offtaker-owned storage with retail-tariff arbitrage.
4. **Align the REopt optimizer with FMP under DPPA.** Today the optimizer sizes against EVN retail; setting `tou_energy_rates_per_kwh = FMP × K_pp` would let it pick PV/BESS sizes that optimize against spot-priced economics. The trade-off (lower revenue but lower self-consumption value) needs design discussion before implementation.
5. **Optional cleanup**: factor out the unit-mixing risk by renaming the misleading `_vnd` suffix in `cash_flow.py` internal variables (they actually hold whatever currency `_money` produced — USD when REopt is given USD inputs).

## Design Questions Resolved

All five Phase 3 design questions remain resolved (see [proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md](proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md)). New decisions from the 2026-06-07 validation session:

- **Customer-side spot price = CFMP × K_pp** (not FMP × Q_adj). `C_DN = Q_adj × CFMP × K_pp` per user clarification. CFMP series loaded from `DPPA DOC/fmp_cfmp_vn.json`.
- **Curtailed PV under self-consumption REopt run is credited as DPPA grid export at FMP.** Optimizer stays in self-consumption mode (no FMP signal); the generator owns the meter under DPPA and dumps surplus rather than curtailing. Case_2's 1.57 GWh/yr of curtailed PV → +$435k year-1 generator revenue under DPPA accounting.
- **CfD volume shape**: 8760-hour series matched to expected `Q_re_meter` (including would-be-curtailed surplus), not a flat scalar.

## Honest Factory A Economics (post-bess_capex fix)

All cases share `$2.85M` PV capex. BESS capex from REopt:

| Case | Description | BESS capex | Total capex | Equity IRR | NPV (USD) |
|---|---|---:|---:|---:|---:|
| case_1 | Current TOU + PV + BESS | $1.13M | $3.71M | 18.1% | $1.65M |
| case_2 | QĐ963 TOU + PV + BESS (baseline) | $1.44M | $4.29M | 16.0% | $1.44M |
| case_3 | QĐ963 + two-component pilot | $1.93M | $4.88M | 12.3% | $0.65M |
| case_4 | QĐ963 TOU + PV only | $0.00M | $1.66M | 18.7% | $0.80M |
| case_5 | QĐ963 + PV + BESS + grid_dppa_cfd | $1.44M | $4.29M | 14.5% | $0.77M |

Notable: case_4 (PV-only) beats case_2 (PV+BESS) on equity IRR — at current BESS prices ($80/kW + $120/kWh), BESS barely earns its keep for this load shape. Case_5 (DPPA at strike 2000) loses to case_2 because the CfD is one-way transfer at this strike.

## Resume Here Next Session

To explore item 1 (deal-term sweep):

1. Clone `outputs/vietnam_case/factory_a/case_5/case.json` to `case_6/`, `case_7/` etc.
2. Vary `dppa.cfd_strike_per_kwh_vnd` (e.g. 1400, 1500, 1600) and/or scale `cfd_contract_volume_kwh_per_hour` by a factor.
3. Re-run `python -m proforma_vietnam.run_case --case outputs/vietnam_case/factory_a/case_N/case.json --poll-seconds 5 --max-polls 240` for each.
4. Compare buyer savings fraction (from the Year 1 BAU vs DPPA sheet) and ESCO Equity IRR (Summary sheet) across the sweep to identify the bankable strike range.

## Todo

- [x] Build `case_5` end-to-end on docker and validate the four new DPPA sheets render.
- [x] Wire CFMP series into settlement (`C_DN = Q_adj × CFMP × K_pp`).
- [x] Credit case_2 curtailed PV as DPPA grid export under DPPA accounting.
- [x] Add Year 1 BAU vs DPPA summary sheet.
- [x] Fix DPPA-VND-into-USD-cash-flow unit mixing.
- [x] Fix `bess_capex_usd=0` override bug; regenerate all five case assumptions/workbooks.
- [x] Commit Phase 3 + the five fixes (`290b8dc2`, `8e0c2d1c`).
- [ ] Push to `origin/master` (branch is now ahead by several commits).
- [ ] Manual cleanup: close Excel, remove `case_5/vietnam_report_*_v5.xlsx` + `~$*.xlsx` lock + stale parent `vietnam_report_b729db40-*.xlsx`.
- [ ] Decide whether to pursue Active Product Direction item 1 (deal-term sweep) or move on to item 2/3/4.

## Session Close Procedure

Before ending a future working session:

1. Update this file's `Last updated` date.
2. Summarize files changed and why.
3. Record tests or checks run, including failures.
4. Update the todo list so completed work is checked off.
5. Add the current commit hash if a commit was made.
6. Update `SESSION_NOTES.md` with detailed notes needed to preserve context beyond this concise handoff.
7. Record any blockers or assumptions needed to resume cleanly.
