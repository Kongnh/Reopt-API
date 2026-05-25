# Codex Session Handoff

Last updated: 2026-05-25

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Local branch is 8 commits ahead of `origin/master`.
- Latest commit: `b1e722ee Add Vietnam XLSX workbook builder and handoff updates`.
- Working tree has uncommitted Phase 2/API/domain-migration additions:
  - `proforma_vietnam/reference_workbook_comparison.py`
  - `proforma_vietnam/tests/test_reference_esco_workbook.py`
  - `reoptjl/views.py`
  - `reoptjl/test/test_vietnam_proforma_endpoint.py`
  - `resilience_stats/migrations/0017_alter_erpmeta_job_type.py`
  - existing modified docs/domain-migration files listed by `git status --short`
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
- Added the V3 Vietnam pro forma XLSX query-param flow:
  - `GET /v3/job/<run_uuid>/results?vietnam_proforma=true&esco_energy_discount_fraction=<fraction>` returns an XLSX blob.
  - Response content type is `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
  - Response filename is `vietnam_proforma_<run_uuid>.xlsx`.
  - The normal JSON results response remains the default when `vietnam_proforma` is absent.
- Generated and inspected an actual-payload Vietnam pro forma workbook:
  - First fresh `current` Vietnam tariff run UUID `991b8b06-19f5-4489-a0f9-66a37ec9a034` ended with status `error` because Julia tried the external Solar Dataset Query API at `developer.nrel.gov` during the scheduled domain brownout and received HTTP 410.
  - Second fresh `current` Vietnam tariff run UUID `e685ae81-a3c1-4f5c-bdc1-27c899d58bc2` used an explicit 8760 PV production factor series to avoid that external lookup and completed with status `optimal`.
  - Saved workbook: `outputs/vietnam_proforma_actual_payload/vietnam_proforma_e685ae81-a3c1-4f5c-bdc1-27c899d58bc2.xlsx`.
  - Workbook sheets inspected: Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions.
  - Key inspected Summary values: total capex `1565427.256` VND, project IRR `6.7520%`, equity IRR `5.9904%`, NPV `-31274.7858` VND, average DSCR `0.6763`, simple payback `16.8347` years, ROI `4.2094`.
  - Artifact-tool formula scan found no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or `#N/A` tokens.
  - Rendered all five workbook sheets to PNG previews under `outputs/vietnam_proforma_actual_payload/rendered/`; Summary, Cash Flow, and Tax Schedule were visually inspected and key values were legible.
- Updated the NLR domain migration paths after the developer-domain brownout:
  - Added a Julia Docker image patch step that rewrites `developer.nrel.gov` to `developer.nlr.gov` inside the installed `REopt.jl` package after `Pkg.instantiate()`.
  - Patched the current running Julia container's installed `REopt.jl` package and restarted the Julia service.
  - Rebuilt `reopt_api-julia:latest` and recreated the Julia service so future container recreation uses the patched image.
  - Updated resilience ERP job-type defaults from `developer.nrel.gov` to `developer.nlr.gov` in `resilience_stats/api.py` and `resilience_stats/models.py`.
  - Added and applied migration `resilience_stats/migrations/0017_alter_erpmeta_job_type.py`.
  - Updated public developer docs links in `README.md`, the support email in `CONTRIBUTING.md`, and remaining source comments that used `@nrel.gov` email addresses.
  - Historical `developer.nrel.gov` references still remain in old migrations, changelog entries, and session notes only.
- Added the reference ESCO project workbook comparison gate:
  - `proforma_vietnam/reference_workbook_comparison.py` reads workbook Inputs, Reference Summary, and Reference Annual Cash Flow sheets.
  - `proforma_vietnam/tests/test_reference_esco_workbook.py` builds a deterministic hand-built workbook-style reference case and compares every referenced annual row/metric within 1%.
  - The reference case covers 25 years, VND capex/debt/equity, escalated ESCO revenue, Vietnam depreciation/CIT, debt service, NPV, project IRR, equity IRR, DSCR, payback, and ROI.
- Fresh verification this session:
  - Red TDD run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.esco_pro_forma'`.
  - Red TDD run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.xlsx_builder'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` passed, 2 tests.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` passed, 4 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder` passed, 15 tests.
  - Green Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 15 tests, `System check identified no issues (0 silenced).`
  - Red API integration run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` failed because the results endpoint returned `application/json` instead of XLSX.
  - Green API integration run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - Green combined Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 16 tests, `System check identified no issues (0 silenced).`
  - Saved V3 payload inspection for run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d` confirmed 8760 `tou_energy_rates_per_kwh`, 8760 `PV.electric_to_load_series_kw`, empty storage-to-load, and `can_grid_charge=true`.
  - Adapter smoke call against that saved payload completed with no shape errors and zero grid-arbitrage revenue.
  - Docker stack check: `docker-compose ps` showed `julia`, `celery`, `db`, `django`, and `redis` running.
  - Actual payload submit: `docker-compose exec -T django python -m reoptjl.src.vietnam.example_submit` returned run UUID `991b8b06-19f5-4489-a0f9-66a37ec9a034`, which later returned status `error` due the external solar API domain-transition brownout.
  - Actual payload submit with explicit `PV.production_factor_series` returned run UUID `e685ae81-a3c1-4f5c-bdc1-27c899d58bc2`, which reached status `optimal` after polling.
  - XLSX endpoint call saved `outputs/vietnam_proforma_actual_payload/vietnam_proforma_e685ae81-a3c1-4f5c-bdc1-27c899d58bc2.xlsx`.
  - Workbook inspection verified the five expected sheets, key Summary values, and no formula-error tokens.
  - NLR migration check: running Julia `REopt.jl` package URLs now point to `developer.nlr.gov` for solar data query, PVWatts, wind toolkit, and NSRDB.
  - Migration run: `docker-compose exec -T django python manage.py migrate resilience_stats` applied `resilience_stats.0017_alter_erpmeta_job_type`.
  - Django health: `docker-compose exec -T django python manage.py check` passed with `System check identified no issues (0 silenced).`
  - Migration consistency: `docker-compose exec -T django python manage.py makemigrations --check --dry-run` returned `No changes detected`.
  - Focused tariff tests: `docker-compose exec -T django python manage.py test reoptjl.test.test_vietnam_tariff -v 2` passed, 8 tests.
  - API smoke: `GET http://localhost:8000/v3/job/inputs/` returned HTTP 200.
  - Regression E2E without explicit PV production factor series: submitted Vietnam payload run UUID `56b65e70-d18d-4eaf-a3ef-8d91ed00ecee`; it reached status `optimal`, confirming the previous solar resource brownout failure no longer reproduces.
  - Final rebuilt-image E2E without explicit PV production factor series: submitted Vietnam payload run UUID `0b1fa767-9b18-4d8c-8153-7b169ca570ff`; it reached status `optimal`.
  - Red reference workbook comparison run: `python -m unittest proforma_vietnam.tests.test_reference_esco_workbook` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.reference_workbook_comparison'`.
  - Green reference workbook comparison run: `python -m unittest proforma_vietnam.tests.test_reference_esco_workbook` passed, 1 test.
  - Green local Phase 2 suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder proforma_vietnam.tests.test_reference_esco_workbook` passed, 16 tests.
  - Green Docker/Django Phase 2 suite: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 16 tests, `System check identified no issues (0 silenced).`
  - Green Docker/Django US pro forma regression: `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test, `System check identified no issues (0 silenced).`

## Active Product Direction

Use `roadmap.md` as the implementation source of truth.

## Resume Here Next Session

Phase 2 acceptance gates are complete. Start by reviewing/staging the uncommitted Phase 2/API/domain-migration changes and decide whether to commit/push or run any final full-stack smoke check first.

Phase 2 completion order before final payload evaluation:

1. [x] Run one actual Vietnam tariff payload, generate the Vietnam pro forma workbook, and inspect the result.
2. [x] Compare one reference ESCO project against a hand-built workbook within +/-1%.
3. [x] Run `python manage.py test proforma_vietnam` and `python manage.py test proforma` in Docker before marking Phase 2 complete.

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
- [x] Add V3 Vietnam pro forma download endpoint or query-param flow.
- [x] Run one actual Vietnam tariff payload, generate the Vietnam pro forma workbook, and inspect the result.
- [x] Validate one reference ESCO project against a hand-built workbook within +/-1%.
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
