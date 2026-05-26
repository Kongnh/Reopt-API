# Codex Session Handoff

Last updated: 2026-05-26

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Local branch will be 10 commits ahead of `origin/master` after committing the reviewed backend-first case-builder/report-generator slice.
- Latest feature commit: backend-first Vietnam case builder/report generator slice.
- Working tree should be clean after that commit, apart from local ignored files and running Docker containers.
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
- Started the backend-first Vietnam case builder + report generator phase:
  - Added `proforma_vietnam/case_builder.py` to convert a case config and 8760 hourly load CSV into a REopt V3 payload plus report assumptions.
  - Added `proforma_vietnam/report_data.py` to normalize V3 results into report-ready sections for sizing, dispatch, annual production, results comparison, load duration, and developer financials.
  - Added `proforma_vietnam/run_case.py` as a CLI entry point with dry-run payload generation and real submit/poll/report-download support.
  - Expanded the Vietnam XLSX workbook to include System Sizing, Results Comparison, Annual Production, Dispatch Profile, Load Duration, and Developer Financials sheets with basic Excel charts.
  - Updated the V3 Vietnam pro forma response to pass normalized report data into the workbook builder.
- Fresh verification this session:
  - Diff review found one edge case before commit: case JSON could omit `esco_contract.esco_energy_discount_fraction`, but the V3 XLSX endpoint requires it for report downloads.
  - Added early validation in `proforma_vietnam/case_builder.py` plus a focused test so the case builder fails before a full optimizer/report run can produce an invalid report request.
  - Green local discovered suite after review fix: `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 22 tests.
  - Docker recovery note: first Docker/Django verification attempt failed because Docker Desktop's Linux engine pipe was missing; Docker Desktop was started and `docker info` then succeeded.
  - Green Docker/Django Vietnam suite after review fix: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 22 tests, `System check identified no issues (0 silenced).`
  - Green Docker/Django API integration after review fix: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - Docker/Django US pro forma regression was first attempted in parallel with the API integration test and failed creating duplicate `test_reopt`; rerunning it by itself passed.
  - Green Docker/Django US pro forma regression after serial rerun: `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test, `System check identified no issues (0 silenced).`
  - Red TDD run: `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_report_data proforma_vietnam.tests.test_xlsx_builder` failed with missing `proforma_vietnam.case_builder`, missing `proforma_vietnam.report_data`, missing `report_data` workbook parameter, and missing workbook sheets.
  - Red TDD run: `python -m unittest proforma_vietnam.tests.test_run_case` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.run_case'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_report_data proforma_vietnam.tests.test_xlsx_builder` passed, 8 tests.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_run_case` passed, 1 test.
  - Green local discovered suite: `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 21 tests.
  - Green Docker/Django Vietnam suite: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 21 tests, `System check identified no issues (0 silenced).`
  - Green Docker/Django API integration: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - Green Docker/Django US pro forma regression: `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test.
  - Green Django health: `docker-compose run --rm --entrypoint python django manage.py check` passed with `System check identified no issues (0 silenced).`
  - Note: `docker-compose exec -T django python manage.py check` failed because the long-running `django` service was not running; the disposable Django container check passed.
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

The backend-first Vietnam case builder + report generator slice has been reviewed, verified, and committed. The latest user-facing guidance explained how to run it with a custom 8760 load CSV and case JSON to get `payload.json`, `assumptions.json`, `results.json`, and `vietnam_report_<run_uuid>.xlsx`.

Start next session by confirming whether to push the local commits to `origin/master`. If continuing feature work first, the highest-value next task is extending `proforma_vietnam/case_builder.py` so custom financial inputs beyond `analysis_years` are passed through from case JSON into the REopt payload and Vietnam ESCO cash-flow/report assumptions.

Use the new dry-run CLI path to generate payloads from case config before running expensive optimizer E2E checks:

```bash
python -m proforma_vietnam.run_case --case path\to\case.json --out outputs\vietnam_case\factory_a --dry-run
```

Use the full report path after Docker services are available:

```bash
python -m proforma_vietnam.run_case --case path\to\case.json --out outputs\vietnam_case\factory_a --poll-seconds 5 --max-polls 120
```

Current custom-input limitation: `financial.analysis_years` maps into the REopt payload and `esco_contract.esco_energy_discount_fraction` maps into the Vietnam report download. Other financial terms such as owner discount rate, debt fraction, debt rate, O&M, and capex overrides should be added explicitly before relying on them from case JSON.

Completed report-generator slice:

1. [x] Run one actual Vietnam tariff payload, generate the Vietnam pro forma workbook, and inspect the result.
2. [x] Compare one reference ESCO project against a hand-built workbook within +/-1%.
3. [x] Run `python manage.py test proforma_vietnam` and `python manage.py test proforma` in Docker before marking Phase 2 complete.
4. [x] Add backend-first Vietnam case-builder dry-run payload generation.
5. [x] Normalize REopt results into report-ready sizing, dispatch, production, comparison, load-duration, and financial sections.
6. [x] Expand the Vietnam XLSX report with REopt-style report sheets and basic Excel charts.

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
- [x] Add backend-first Vietnam case builder from 8760 load CSV and case config.
- [x] Add normalized Vietnam report-data layer for sizing, dispatch, production, comparison, load-duration, and developer financials.
- [x] Expand Vietnam XLSX report with additional report sheets and charts.
- [x] Add dry-run capable `proforma_vietnam.run_case` CLI.
- [ ] Extend case JSON financial passthrough beyond `analysis_years` if the next case study needs custom owner discount rate, debt fraction/rate, O&M, capex, or ESCO cash-flow overrides.
- [ ] Run one representative custom 8760 load case end-to-end and inspect the generated `vietnam_report_<run_uuid>.xlsx`.
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
