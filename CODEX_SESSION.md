# Codex Session Handoff

Last updated: 2026-06-06

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Git status at session close: dirty across `proforma_vietnam/`, `reoptjl/views.py`, `roadmap.md`, the design doc, handoff files, plus the new `proforma_vietnam/dppa_settlement.py`, `proforma_vietnam/tests/test_dppa_settlement.py`, and `proforma_vietnam/tests/test_reference_dppa_workbook.py`. Generated case outputs under `outputs/vietnam_case/factory_a/` remain untracked.
- Detailed historical notes and prior verification evidence are archived in `SESSION_NOTES.md`.

## Completed Context

- Phase 1 Vietnam EVN tariff builder and acceptance gate are complete.
- Phase 2 Vietnam ESCO pro forma, case builder, report generator, and USD-facing workbook flow are complete enough for representative Factory A case outputs.
- Phase 3 DPPA settlement layer is implemented end-to-end as of 2026-06-06: `grid_dppa_cfd` contract type (Điều 14–18 with bilateral CfD overlay) ships with the Phase 2 reference gate preserved byte-identically when `dppa.type = "none"`. Co-located BESS only; factory-side BESS and `private_wire` are deferred. See SESSION_NOTES.md for the full delivery log.
- Factory A case-study deck work has been completed outside this repo source tree, using generated case outputs from `outputs\vietnam_case\factory_a\case_1` through `case_4`.

## Active Product Direction

Phase 3 design is finalized and implemented. The remaining work is real-world validation and any roadmap follow-ups the client wants to pull in.

Next session should choose from:

1. Build a `case_5` JSON for Factory A with `dppa.type = "grid_dppa_cfd"` and verify the four new workbook sheets render correctly against the full 8760 FMP series. Compare ESCO/offtaker economics against `case_2`.
2. Pull `private_wire` forward from Phase 4 if a client deal calls for it (Điều 25, bilateral pricing, no K_pp/k loss factors, no system service fees).
3. Pull factory-side BESS forward from Phase 4 if a client deal needs offtaker-owned storage with retail-tariff arbitrage.
4. Align the REopt optimizer with FMP under DPPA (set `tou_energy_rates_per_kwh` from FMP × K_pp so the optimizer sizes against spot-priced economics rather than EVN retail).

## Design Questions Resolved

All five Phase 3 design questions from the prior handoff are resolved (see [proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md](proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md) for the canonical answers):

- DPPA contract type is an enum (`none`, `grid_dppa_cfd`).
- Settlement basis is FMP + K_pp/k losses + flat C_DPPA + flat C_CL + retail C_BL + bilateral CfD overlay.
- Hourly energy accounting uses REopt V3 dispatch series; `Q_re_meter = pv_to_load + pv_to_grid + storage_to_load + storage_to_grid` because co-located BESS sits upstream of the offtaker meter.
- ESCO is the generator; the ESCO discount-to-EVN energy stream is replaced (not layered) by generator FMP + CfD revenue under DPPA.
- The `dppa.type = "none"` default keeps the Phase 2 reference workbook gate green by construction.

## Resume Here Next Session

Run a real Factory A `case_5` end-to-end against the docker stack to validate the new workbook before merging anything:

1. Clone `outputs/vietnam_case/factory_a/case_2/case.json` to `case_5/case.json`.
2. Add a `dppa` block: `{"type": "grid_dppa_cfd", "cfd_strike_per_kwh_vnd": 1700.0, "cfd_contract_volume_kwh_per_hour": <flat or 8760>}`.
3. `docker-compose up -d` and run `python proforma_vietnam/run_case.py --case outputs/vietnam_case/factory_a/case_5/case.json`.
4. Open the generated `vietnam_report_*.xlsx`, confirm the 4 new DPPA sheets render, and sanity-check `generator_revenue`, `c_dn`, `c_bl`, and `cfd_net` against the FMP series in [DPPA DOC/fmp_cfmp_vn.json](DPPA DOC/fmp_cfmp_vn.json).

After that, decide whether to commit the slice as-is or stack the next item from the Active Product Direction list.

## Todo

- [x] Review `vietnam_market_context.md` for DPPA market constraints and settlement assumptions.
- [x] Draft DPPA settlement design in `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`.
- [x] Decide the minimum case JSON fields needed for DPPA contract settings.
- [x] Update `roadmap.md` with a concrete Phase 3 plan.
- [x] Add tests for the first DPPA settlement slice before implementation.
- [x] Preserve the existing EVN-discount ESCO base case as the default behavior.
- [ ] Build `case_5` end-to-end on docker and screenshot the four new DPPA sheets.
- [ ] Commit Phase 3 (currently uncommitted on `master`).

## Session Close Procedure

Before ending a future working session:

1. Update this file's `Last updated` date.
2. Summarize files changed and why.
3. Record tests or checks run, including failures.
4. Update the todo list so completed work is checked off.
5. Add the current commit hash if a commit was made.
6. Update `SESSION_NOTES.md` with detailed notes needed to preserve context beyond this concise handoff.
7. Record any blockers or assumptions needed to resume cleanly.
