# Codex Session Handoff

Last updated: 2026-05-25

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Local branch is 7 commits ahead of `origin/master`.
- Latest commit: `268af7be Finalize Vietnam ESCO contract design`.
- Working tree has uncommitted Phase 2 pro forma additions:
  - `proforma_vietnam/cash_flow.py`
  - `proforma_vietnam/esco_pro_forma.py`
  - `proforma_vietnam/xlsx_builder.py`
  - `proforma_vietnam/tests/test_cash_flow.py`
  - `proforma_vietnam/tests/test_esco_pro_forma.py`
  - `proforma_vietnam/tests/test_xlsx_builder.py`
- Local Python environment is not ready: `python manage.py check` failed because `django` is not installed.
- Docker stack is running for local development.
- Local ignored `keys.py` was created from `keys.py.template` so Django/Celery can import settings.
- Phase 1 Vietnam EVN tariff acceptance gate is complete for the example industrial load:
  - `current` run UUID `0ee531dc-625f-416f-a1dc-44e1671572d4`, status `optimal`, REopt BAU bill `345975.02`, manual bill `345975.02`, error `0.0%`.
  - `decision_963` run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d`, status `optimal`, REopt BAU bill `345975.02`, manual bill `345975.02`, error `0.0%`.
- Detailed chronological session notes now live in `SESSION_NOTES.md`.
- Phase 2 first slice is started:
  - Added standalone Vietnam tax model constants and helpers in `proforma_vietnam/tax_model.py`.
  - PV straight-line depreciation uses 20 years per user correction.
  - BESS straight-line depreciation uses 8 years.
  - CIT schedule tests cover 4-year exemption, 9-year reduced 10% effective rate, and standard 20% rate thereafter.
- Added `proforma_vietnam/ESCO_CONTRACT_MODEL_NOTES.md` to capture third-party investment model questions before cash-flow implementation.
- Finalized the Phase 2 Vietnam ESCO contract model in `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`.
- Key finalized ESCO assumptions:
  - REopt optimization happens first; ROI/IRR/NPV/DSCR/payback are pro forma outputs.
  - ESCO energy price is a discount to the time-specific current-year EVN energy tariff.
  - ESCO energy price is pegged back-to-back to EVN energy escalation.
  - Demand-charge savings are calculated from REopt results and split 80% ESCO / 20% offtaker by default.
  - Grid charging is an optional scenario switch, disabled in the base case.
  - If grid charging is enabled, 100% of net grid-charging arbitrage value belongs to ESCO.
- Added the first Phase 2 cash-flow DCF slice in `proforma_vietnam/cash_flow.py`:
  - Calculates ESCO energy revenue from time-specific EVN rates and the ESCO discount.
  - Escalates energy revenue and demand savings separately.
  - Splits demand-charge savings 80% ESCO / 20% offtaker by default.
  - Keeps grid-charging arbitrage disabled in the base case and assigns net positive arbitrage to ESCO when enabled.
  - Uses Vietnam straight-line depreciation and CIT helpers.
  - Outputs annual cash-flow rows plus ROI, project IRR, equity IRR, NPV, DSCR, and payback metrics.
- Added the REopt-results adapter in `proforma_vietnam/esco_pro_forma.py`:
  - Maps V3 `/results` dictionaries into `calculate_vietnam_esco_cash_flow(...)` inputs.
  - Reads 8760 EVN rates from `inputs.ElectricTariff.tou_energy_rates_per_kwh`.
  - Reads year-one BAU/optimized bills and demand charges from `outputs.ElectricTariff`.
  - Counts PV-to-load energy as ESCO energy revenue.
  - Counts storage-to-load energy only when `inputs.ElectricStorage.can_grid_charge` is explicitly false.
  - Keeps grid-charging arbitrage disabled because the current payload does not expose grid-charged battery attribution.
- Added the Phase 2 XLSX workbook builder in `proforma_vietnam/xlsx_builder.py`:
  - Builds standalone `openpyxl` workbooks from Vietnam ESCO cash-flow results.
  - Includes Summary, Cash Flow, Tax Schedule, Debt Service, and Assumptions sheets.
  - Keeps the builder independent from Django and API response wiring.
- Fresh verification this session:
  - Red TDD run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.esco_pro_forma'`.
  - Red TDD run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.xlsx_builder'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` passed, 2 tests.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` passed, 4 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder` passed, 15 tests.
  - Green Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 15 tests, `System check identified no issues (0 silenced).`
  - Saved V3 payload inspection for run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d` confirmed 8760 `tou_energy_rates_per_kwh`, 8760 `PV.electric_to_load_series_kw`, empty storage-to-load, and `can_grid_charge=true`.
  - Adapter smoke call against that saved payload completed with no shape errors and zero grid-arbitrage revenue.

## Active Product Direction

Use `roadmap.md` as the implementation source of truth.

## Resume Here Next Session

Start with the V3 Vietnam pro forma XLSX download flow:

1. Read `proforma_vietnam/xlsx_builder.py`, `proforma_vietnam/esco_pro_forma.py`, `proforma_vietnam/tests/test_xlsx_builder.py`, and `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`.
2. Add a V3 Vietnam pro forma download endpoint or query-param flow.
3. Add an API integration test for the XLSX response.
4. Keep `proforma/` and Julia untouched unless the roadmap explicitly changes.

Phase 2 completion order before final payload evaluation:

1. Add a V3 Vietnam pro forma download endpoint or query-param flow.
2. Add an API integration test for the XLSX response.
3. Run one actual Vietnam tariff payload, generate the Vietnam pro forma workbook, and inspect the result.
4. Compare one reference ESCO project against a hand-built workbook within +/-1%.
5. Run `python manage.py test proforma_vietnam` and `python manage.py test proforma` in Docker before marking Phase 2 complete.

## Todo

- [x] Start Docker stack with `docker-compose up -d`.
- [x] Verify app health with a Django check inside the container.
- [x] Implement Phase 1 EVN tariff builder.
- [x] Add focused tariff unit tests.
- [x] Add an example Vietnam job submission script after the tariff builder is stable.
- [x] Run end-to-end Vietnam job submissions using both `tou_schedule="current"` and `tou_schedule="decision_963"`.
- [x] Compare REopt baseline annual electricity cost against manual EVN tariff calculations for both TOU structures.
- [x] Begin Phase 2 Vietnam pro forma in `proforma_vietnam/`.
- [x] Add focused unit tests for Vietnam CIT holiday/reduced-rate logic and straight-line depreciation.
- [x] Document open Vietnam ESCO contract model questions before cash-flow implementation.
- [x] Finalize ESCO contract assumptions for energy offtake, peak shaving service, and energy arbitrage treatment.
- [x] Add Phase 2 cash flow DCF module using VND base currency, EVN escalation, debt service assumptions, tested tax schedule, and agreed ESCO contract structure.
- [x] Add ESCO pro forma adapter from REopt outputs into the cash-flow module.
- [x] Add Vietnam XLSX workbook builder.
- [ ] Add V3 Vietnam pro forma download endpoint or query-param flow.
- [ ] Validate one reference ESCO project against a hand-built workbook within +/-1%.
- [ ] Defer DPPA settlement, loss factors, and Julia changes until Phase 3 or an explicit roadmap change.

## Session Close Procedure

Before ending a future working session:

1. Update this file's `Last updated` date.
2. Summarize files changed and why.
3. Record tests or checks run, including failures.
4. Update the todo list so completed work is checked off.
5. Add the current commit hash if a commit was made.
6. Update `SESSION_NOTES.md` with detailed notes needed to preserve context beyond this concise handoff.
7. Record any blockers or assumptions needed to resume cleanly.
