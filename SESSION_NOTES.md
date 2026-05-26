# Session Notes

Use this file for detailed working-session notes that would make `CODEX_SESSION.md` too long.
At the end of every working session, append or update the latest section here with files changed, checks run, blockers, assumptions, and any context needed to resume.

## 2026-05-26 - Diff Review, Verification, and Commit

- User asked to review the current uncommitted backend-first Vietnam case-builder/report-generator diff, rerun focused verification, and commit the slice if clean.
- Reviewed changed areas:
  - `proforma_vietnam/case_builder.py`
  - `proforma_vietnam/report_data.py`
  - `proforma_vietnam/run_case.py`
  - `proforma_vietnam/xlsx_builder.py`
  - `reoptjl/views.py`
  - related tests and handoff notes.
- Review finding:
  - The V3 Vietnam pro forma XLSX endpoint requires `esco_energy_discount_fraction`, but the case builder could previously produce assumptions with that value missing.
  - Added a narrow validation in `proforma_vietnam/case_builder.py` to require `esco_contract.esco_energy_discount_fraction`.
  - Added `test_requires_esco_energy_discount_for_report_download` in `proforma_vietnam/tests/test_case_builder.py`.
- Verification run:
  - `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 22 tests.
  - First `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` attempt failed before tests because Docker Desktop's Linux engine pipe was unavailable.
  - `docker info` confirmed the Docker client existed but the server was offline.
  - Started Docker Desktop and reran `docker info`; server became available.
  - `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 22 tests, with `System check identified no issues (0 silenced).`
  - `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` was first run in parallel with the API test and failed creating duplicate `test_reopt`; serial rerun passed, 1 test, with `System check identified no issues (0 silenced).`
- Commit action:
  - Stage and commit the backend-first Vietnam case builder/report generator slice after verification.
- Remaining next tasks:
  - Push local commits to `origin/master` if desired.
  - Extend case JSON financial passthrough beyond `analysis_years` before relying on custom owner discount rate, debt fraction/rate, O&M, capex, or ESCO cash-flow overrides.
  - Run one representative custom 8760 load case end-to-end and inspect the generated `vietnam_report_<run_uuid>.xlsx`.

## 2026-05-26 - Custom Input Run Guidance Handoff

- User asked how to run the new backend-first Vietnam case builder with custom input load and financial assumptions and how to get the actual report.
- Verified current implementation shape before answering:
  - `proforma_vietnam/case_builder.py` reads an 8760 hourly load CSV from the first column, builds `ElectricLoad.loads_kw`, builds Vietnam EVN tariff arrays, maps `financial.analysis_years`, defaults `ElectricStorage.can_grid_charge` to false, and stores ESCO/report assumptions.
  - `proforma_vietnam/run_case.py` supports `--dry-run` to write `payload.json` and `assumptions.json`, and a full run path that submits to `/v3/job/`, polls results, writes `results.json`, and downloads `vietnam_report_<run_uuid>.xlsx`.
- Guidance given to user:
  - Create an 8760-row kW CSV with optional header, no negative values.
  - Create a case JSON containing `case`, `site`, `load_profile`, `tariff`, `technologies`, `financial`, and `esco_contract` sections.
  - Start Docker with `docker-compose up -d`.
  - Run dry-run:
    `python -m proforma_vietnam.run_case --case input_files\vietnam_case_factory_a.json --out outputs\vietnam_case\factory_a --dry-run`
  - Run actual optimization/report:
    `python -m proforma_vietnam.run_case --case input_files\vietnam_case_factory_a.json --out outputs\vietnam_case\factory_a --poll-seconds 5 --max-polls 120`
  - Expected outputs: `payload.json`, `assumptions.json`, `results.json`, and `vietnam_report_<run_uuid>.xlsx`.
- Important limitation documented for next session:
  - The current case JSON financial passthrough is minimal: `financial.analysis_years` maps into the REopt payload, and `esco_contract.esco_energy_discount_fraction` drives the Vietnam report download.
  - Custom owner discount rate, debt fraction/rate, O&M, capex, and ESCO cash-flow overrides are not yet fully mapped from case JSON.
- Recommended next task:
  - Add tests and implementation for explicit financial/technology/ESCO passthrough in `proforma_vietnam/case_builder.py` and downstream report assumptions before running a real customer-style custom financial case.
  - Then run one representative custom 8760 load case end-to-end and inspect the generated XLSX report.

## 2026-05-25 - Backend Vietnam Case Builder and Report Generator

- Implemented the backend-first Vietnam case builder + report generator slice requested after reviewing the existing REopt webtool/report assets.
- Added `proforma_vietnam/case_builder.py`:
  - Reads a case config dictionary.
  - Loads an 8760 hourly CSV load profile from `load_profile.path`.
  - Builds a normal REopt V3 payload using existing Vietnam EVN tariff builder output.
  - Defaults to Vietnam, 25-year analysis, `tou_schedule="current"`, grid charging disabled, and 80% ESCO demand-savings share.
  - Returns both `payload` and report `assumptions`.
- Added `proforma_vietnam/report_data.py`:
  - Normalizes raw V3 results into report sections for system sizing, dispatch profile, annual electricity production, results comparison, load duration, and developer financial performance.
  - Keeps report data separate from workbook formatting so the same normalized object can later feed HTML/PDF/UI outputs.
- Added `proforma_vietnam/run_case.py`:
  - CLI entry point: `python -m proforma_vietnam.run_case --case path\to\case.json --out outputs\vietnam_case\factory_a --dry-run`.
  - Dry-run writes `payload.json` and `assumptions.json` without API calls.
  - Non-dry-run submits to `/v3/job/`, polls `/v3/job/<run_uuid>/results`, writes `results.json`, and downloads `vietnam_report_<run_uuid>.xlsx` when status is `optimal`.
- Expanded `proforma_vietnam/xlsx_builder.py`:
  - Existing sheets remain: Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions.
  - New sheets: System Sizing, Results Comparison, Annual Production, Dispatch Profile, Load Duration, Developer Financials.
  - Added basic Excel charts for annual production, dispatch, load duration, and developer financials using `openpyxl` charts.
- Updated `reoptjl/views.py`:
  - V3 Vietnam pro forma XLSX response now builds normalized report data from REopt results and passes it into the workbook builder.
- Updated tests:
  - `proforma_vietnam/tests/test_case_builder.py`
  - `proforma_vietnam/tests/test_report_data.py`
  - `proforma_vietnam/tests/test_run_case.py`
  - `proforma_vietnam/tests/test_xlsx_builder.py`
  - `reoptjl/test/test_vietnam_proforma_endpoint.py`
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_report_data proforma_vietnam.tests.test_xlsx_builder` failed with missing `proforma_vietnam.case_builder`, missing `proforma_vietnam.report_data`, missing `report_data` workbook parameter, and missing workbook sheets.
  - Red run: `python -m unittest proforma_vietnam.tests.test_run_case` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.run_case'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_report_data proforma_vietnam.tests.test_xlsx_builder` passed, 8 tests.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_run_case` passed, 1 test.
  - Green local discovered suite: `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 21 tests.
  - Green Docker/Django Vietnam suite: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 21 tests, `System check identified no issues (0 silenced).`
  - Green Docker/Django API integration: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - Green Docker/Django US pro forma regression: `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test.
  - Green Django health: `docker-compose run --rm --entrypoint python django manage.py check` passed with `System check identified no issues (0 silenced).`
  - `docker-compose exec -T django python manage.py check` failed only because the long-running `django` service was not running; the disposable Django container check passed.
- Current git state:
  - Branch `master` is 9 commits ahead of `origin/master`.
  - Latest commit remains `5e219339 Add reference ESCO workbook comparison gate`.
  - Working tree has uncommitted case-builder/report-generator changes.
- Next recommended work:
  - Review/stage the current uncommitted diff.
  - Optionally run one real case through `proforma_vietnam.run_case` without `--dry-run` after preparing a representative 8760 load CSV case config.
  - Commit and push the backend-first case-builder/report-generator slice if accepted.

## 2026-05-25 - Reference ESCO Workbook Comparison Gate

- Started from the `CODEX_SESSION.md` resume point: compare one reference ESCO project against a hand-built workbook within +/-1%.
- Added `proforma_vietnam/reference_workbook_comparison.py`:
  - Reads a workbook object or workbook path.
  - Expects sheets named `Inputs`, `Reference Summary`, and `Reference Annual Cash Flow`.
  - Converts comma-separated hourly/project arrays from the Inputs sheet into `calculate_vietnam_esco_cash_flow(...)` inputs.
  - Compares each workbook-provided summary metric and annual row field against calculated results.
  - Returns readable discrepancy strings when any value is outside the default 1% tolerance.
- Added `proforma_vietnam/tests/test_reference_esco_workbook.py`:
  - Builds a deterministic workbook-style reference case in memory.
  - Reference project uses VND capex/debt/equity, 25 project years, 4% EVN escalation, 65% debt, 8.5% debt rate, 10-year amortization, 20-year PV depreciation, 8-year BESS depreciation, and Vietnam CIT holiday/reduced/standard periods.
  - Reference Summary includes total capex, debt principal, equity investment, project IRR, equity IRR, NPV, average DSCR, simple payback, and ROI.
  - Reference Annual Cash Flow includes all 25 annual rows for ESCO revenue, depreciation, CIT, cash available for debt service, debt service, and equity cash flow.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_reference_esco_workbook` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.reference_workbook_comparison'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_reference_esco_workbook` passed, 1 test.
  - Green local Phase 2 suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder proforma_vietnam.tests.test_reference_esco_workbook` passed, 16 tests.
  - Green Docker/Django Phase 2 suite: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 16 tests, `System check identified no issues (0 silenced).`
  - Green Docker/Django US pro forma regression: `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test, `System check identified no issues (0 silenced).`
- Current git state after this work:
  - New files: `proforma_vietnam/reference_workbook_comparison.py`, `proforma_vietnam/tests/test_reference_esco_workbook.py`.
  - Existing uncommitted files from prior Phase 2/API/domain migration work remain in the working tree, including `reoptjl/views.py`, `reoptjl/test/test_vietnam_proforma_endpoint.py`, `resilience_stats/migrations/0017_alter_erpmeta_job_type.py`, docs, and domain migration edits.
- Phase 2 acceptance gates in `CODEX_SESSION.md` are now marked complete.
- Next recommended work: review the full uncommitted diff, then decide whether to create a commit/push for Phase 2 and the NLR migration changes or run one final full-stack smoke check first.

## 2026-05-25 - NLR Developer Domain Migration

- User provided the NLR developer-team notice that `developer.nrel.gov` is retiring and API calls must move to `developer.nlr.gov`; user also asked to replace `@NREL.gov` email domains with `@NLR.gov`.
- Searched active repo references for `developer.nrel.gov`, `developer.nlr.gov`, `@nrel.gov`, and `@nlr.gov`.
- Found the actual failed solar lookup path in the installed Julia `REopt.jl` dependency inside the Julia container:
  - `/root/.julia/packages/REopt/CGBoo/src/core/utils.jl` used `https://developer.nrel.gov/api/solar/data_query/v2.json` and `https://developer.nrel.gov/api/pvwatts/v8.json`.
  - `/root/.julia/packages/REopt/CGBoo/src/core/production_factor.jl` used `https://developer.nrel.gov/api/wind-toolkit/v2/wind/wtk-srw-download`.
  - `/root/.julia/packages/REopt/CGBoo/src/core/cst_ssc.jl` used `http://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-tmy-v4-0-0-download.csv`.
- Tried `Pkg.update()` in the Julia container; it updated many package pins and still left the old developer domain in `REopt.jl`, so reverted the accidental `julia_src/Manifest.toml` churn and used a targeted patch instead.
- Updated `julia_src/Dockerfile` so future Julia image builds rewrite `developer.nrel.gov` to `developer.nlr.gov` inside installed `REopt.jl` package sources immediately after `Pkg.instantiate()`.
- Patched the currently running Julia container's installed `REopt.jl` package with the same replacement and restarted the Julia service.
- Verified the current Julia package URLs now point to `developer.nlr.gov` for solar data query, PVWatts, wind toolkit, and NSRDB.
- Rebuilt `reopt_api-julia:latest`; the build command exceeded the client timeout, but Docker reported the image was created at `2026-05-25 17:24:10 +0700`.
- Recreated the Julia service with `docker-compose up -d julia`, waited for `Listening on: 0.0.0.0:8081`, and verified the newly created container still had `developer.nlr.gov` in all four `REopt.jl` resource URLs.
- Updated active resilience ERP metadata defaults:
  - `resilience_stats/api.py`: authenticated developer job type now uses `developer.nlr.gov`.
  - `resilience_stats/models.py`: `ERPMeta.job_type` default now uses `developer.nlr.gov`.
  - Added `resilience_stats/migrations/0017_alter_erpmeta_job_type.py`.
  - Applied the migration with `docker-compose exec -T django python manage.py migrate resilience_stats`; result: `OK`.
- Updated email/domain text:
  - `README.md` developer docs links now use `https://developer.nlr.gov/...` and "NLR Developer Network".
  - `CONTRIBUTING.md` support email now uses `reopt@nlr.gov`.
  - `reoptjl/validators.py` and `reo/src/wind_resource.py` comments now use `Jordan.Perr-Sauer@nlr.gov`.
- Verification:
  - `docker-compose exec -T django python manage.py check` passed with `System check identified no issues (0 silenced).`
  - `docker-compose exec -T django python manage.py makemigrations --check --dry-run` returned `No changes detected`.
  - `docker-compose exec -T django python manage.py test reoptjl.test.test_vietnam_tariff -v 2` passed, 8 tests.
  - `GET http://localhost:8000/v3/job/inputs/` returned HTTP 200.
  - Re-ran the actual Vietnam tariff payload without explicit `PV.production_factor_series`; run UUID `56b65e70-d18d-4eaf-a3ef-8d91ed00ecee` reached status `optimal`.
  - Re-ran the same actual Vietnam tariff payload again after rebuilding and recreating the Julia image; run UUID `0b1fa767-9b18-4d8c-8153-7b169ca570ff` reached status `optimal`.
- One false-start check occurred: run UUID `d16ea993-64c8-4086-80f4-366e0831209b` failed because it was submitted while Julia was still precompiling after restart, so Celery could not connect to `julia:8081`.
- Remaining old `developer.nrel.gov` references from `rg` are historical only: old migrations, old changelog entries, and session notes documenting the prior failure.

## 2026-05-25 - Actual Vietnam Payload Workbook Generation

- Ran `docker-compose ps`; the local Docker stack had `julia`, `celery`, `db`, `django`, and `redis` running.
- First attempted a fresh actual Vietnam tariff payload with `docker-compose exec -T django python -m reoptjl.src.vietnam.example_submit`.
- First run UUID: `991b8b06-19f5-4489-a0f9-66a37ec9a034`.
- Polling showed the job moved from `Optimizing...` to status `error`.
- Root cause from `/v3/job/<run_uuid>/results`: Julia called the external Solar Dataset Query API at `developer.nrel.gov` and received HTTP 410 during the scheduled domain-transition brownout. The error message says `developer.nrel.gov` will be shut down on May 29, 2026 and users must update references to `developer.nlr.gov`.
- Submitted a second fresh actual Vietnam tariff payload using the same `current` Vietnam tariff builder output, but with an explicit 8760 `PV.production_factor_series` so the optimizer did not need the external solar data lookup.
- Second run UUID: `e685ae81-a3c1-4f5c-bdc1-27c899d58bc2`.
- Polling reached status `optimal`.
- Expected non-US warnings remained for AVERT, Cambium, and EASIUR lookups at Vietnam coordinates.
- Exported the Vietnam ESCO workbook with:
  - URL: `/v3/job/e685ae81-a3c1-4f5c-bdc1-27c899d58bc2/results?vietnam_proforma=true&esco_energy_discount_fraction=0.9`.
  - Saved file: `outputs/vietnam_proforma_actual_payload/vietnam_proforma_e685ae81-a3c1-4f5c-bdc1-27c899d58bc2.xlsx`.
- Inspected workbook with the spreadsheet artifact tooling:
  - Sheets present: Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions.
  - Summary values: total capex `1565427.256` VND, debt principal `1095799.0792` VND, equity investment `469628.1768` VND, project IRR `0.0675201042`, equity IRR `0.0599040158`, NPV `-31274.7858` VND, average DSCR `0.6762940888`, simple payback `16.8347` years, ROI `4.2094`.
  - Cash Flow shows ESCO energy revenue only; ESCO demand revenue and grid arbitrage revenue are zero for this synthetic actual payload.
  - Tax Schedule shows CIT holiday years 1-8 in this case because taxable income remains non-positive into the reduced-rate period; CIT begins in year 9.
  - Formula-error scan found no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or `#N/A` tokens.
- Rendered all five workbook sheets to PNG under `outputs/vietnam_proforma_actual_payload/rendered/`.
- Visual inspection of Summary, Cash Flow, and Tax Schedule previews showed values and headers were legible.
- Interpretation: the generated workbook path works against an actual optimized Vietnam tariff payload, but this synthetic case is not financially viable at the chosen assumptions; average DSCR is below 1 and NPV is negative.
- Next recommended work: compare one reference ESCO project against a hand-built workbook within +/-1%, then rerun Docker tests for `proforma_vietnam` and `proforma` before marking Phase 2 complete.

## 2026-05-25 - Phase 2 Vietnam Pro Forma XLSX API Flow

- Added the V3 query-param flow on the existing results endpoint:
  - `GET /v3/job/<run_uuid>/results?vietnam_proforma=true&esco_energy_discount_fraction=<fraction>`
  - Returns an XLSX blob with content type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
  - Uses filename `vietnam_proforma_<run_uuid>.xlsx`.
  - Leaves the standard JSON response unchanged when `vietnam_proforma` is absent.
- Implemented the endpoint branch in `reoptjl/views.py` by:
  - detecting `vietnam_proforma` values `true`, `1`, or `xlsx`,
  - requiring `esco_energy_discount_fraction`,
  - passing the already-built V3 results dictionary into `calculate_esco_pro_forma_from_reopt_results(...)`,
  - passing the cash-flow result into `build_vietnam_esco_workbook(...)`,
  - returning the workbook bytes directly in the HTTP response.
- Added `reoptjl/test/test_vietnam_proforma_endpoint.py` as the API integration test:
  - creates a small completed V3 run directly in the test database,
  - calls the results endpoint with the Vietnam pro forma query params,
  - verifies HTTP 200, XLSX content type, attachment filename, required workbook sheets, and key Summary/Assumptions cells.
- TDD evidence:
  - Red run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` failed because the endpoint still returned `application/json`.
  - Green focused run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - Green local pro forma run: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder` passed, 15 tests.
  - Green combined Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 16 tests, `System check identified no issues (0 silenced).`
  - `git diff --check` returned only the existing LF-to-CRLF warning for `reoptjl/views.py`.
- Current git state after this work: branch `master` is 8 commits ahead of `origin/master`; latest commit is `b1e722ee`; `reoptjl/views.py`, `reoptjl/test/test_vietnam_proforma_endpoint.py`, `CODEX_SESSION.md`, and `SESSION_NOTES.md` have uncommitted changes.
- Next recommended work:
  - Generate a workbook from a real completed Vietnam tariff run using `vietnam_proforma=true&esco_energy_discount_fraction=0.9`.
  - Inspect the workbook sheets and key values.
  - Then start the reference ESCO project comparison against a hand-built workbook within +/-1%.

## 2026-05-25 - Phase 2 Vietnam XLSX Workbook Builder

- Resumed from `CODEX_SESSION.md`, `roadmap.md`, `AGENTS.md`, and the latest Phase 2 notes.
- Implemented `proforma_vietnam/xlsx_builder.py` as a standalone `openpyxl` workbook builder.
- Added `proforma_vietnam/tests/test_xlsx_builder.py` covering:
  - required sheet order: Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions,
  - key Summary values: total capex, debt principal, equity investment, NPV, and equity IRR,
  - representative annual values in Cash Flow, Tax Schedule, and Debt Service,
  - passed-through Assumptions values.
- Workbook behavior:
  - Accepts the dictionary returned by `calculate_vietnam_esco_cash_flow(...)`.
  - Writes summary metrics from `result["summary"]`.
  - Writes annual cash-flow rows from `result["annual_cash_flows"]`.
  - Splits tax and debt views into dedicated sheets using the same annual row data.
  - Keeps the builder independent from Django, V3 API routing, and response serialization.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.xlsx_builder'`.
  - First green attempt caught one bad test assertion around the Cash Flow column order; corrected the assertion to match the declared workbook columns.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` passed, 4 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder` passed, 15 tests.
  - Green Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 15 tests, `System check identified no issues (0 silenced).`
- Current git state after this work: branch `master` remains at commit `268af7be`; `CODEX_SESSION.md`, `SESSION_NOTES.md`, `proforma_vietnam/cash_flow.py`, `proforma_vietnam/esco_pro_forma.py`, `proforma_vietnam/xlsx_builder.py`, and the three Phase 2 test files have uncommitted changes.
- Next recommended work:
  - Add a V3 Vietnam pro forma XLSX download endpoint or query-param flow.
  - Add an API integration test for the XLSX response.
  - Run one actual Vietnam tariff payload through the endpoint/workbook before starting the hand-built workbook comparison.

## 2026-05-25 - Phase 2 Vietnam REopt Results Adapter

- Resumed from `CODEX_SESSION.md`, `roadmap.md`, `AGENTS.md`, and the latest `SESSION_NOTES.md` entry.
- Implemented `proforma_vietnam/esco_pro_forma.py` as the Phase 2 adapter from V3 `/results` dictionaries into `calculate_vietnam_esco_cash_flow(...)`.
- Added `proforma_vietnam/tests/test_esco_pro_forma.py` with a small fake V3 result payload.
- Adapter behavior:
  - Reads 8760 EVN energy rates from `inputs.ElectricTariff.tou_energy_rates_per_kwh`.
  - Reads BAU/optimized year-one bills and demand charges from `outputs.ElectricTariff`.
  - Reads PV direct-to-load series from `outputs.PV.electric_to_load_series_kw`.
  - Includes `outputs.ElectricStorage.storage_to_load_series_kw` in ESCO energy only when `inputs.ElectricStorage.can_grid_charge` is explicitly false.
  - Keeps grid-charging arbitrage disabled because the available V3 payload does not expose grid-charged battery discharge attribution.
  - Uses PV output size and installed cost for PV capex, storage output initial capital cost when available, and year-one O&M from `outputs.Financial.year_one_om_costs_before_tax`.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.esco_pro_forma'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` passed, 2 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma` passed, 11 tests.
  - Green Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 11 tests, `System check identified no issues (0 silenced).`
- Representative V3 payload inspection:
  - Started Django with `docker-compose up -d django`.
  - `Invoke-WebRequest` closed unexpectedly on the large response, but `curl.exe` successfully saved the JSON response for run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d`.
  - Confirmed output keys: `Financial`, `ElectricTariff`, `ElectricUtility`, `ElectricLoad`, `Site`, `PV`, `ElectricStorage`.
  - Confirmed relevant shapes: 8760 `inputs.ElectricTariff.tou_energy_rates_per_kwh`, 8760 `outputs.PV.electric_to_load_series_kw`, empty `outputs.ElectricStorage.storage_to_load_series_kw`, and `inputs.ElectricStorage.can_grid_charge=true`.
  - Adapter smoke call against the saved payload completed without shape errors and returned zero `esco_grid_arbitrage_revenue_vnd`.
- Current git state after this work: branch `master` is 7 commits ahead of `origin/master`; `CODEX_SESSION.md`, `SESSION_NOTES.md`, `proforma_vietnam/cash_flow.py`, `proforma_vietnam/esco_pro_forma.py`, `proforma_vietnam/tests/test_cash_flow.py`, and `proforma_vietnam/tests/test_esco_pro_forma.py` have uncommitted changes.
- Next recommended work:
  - Add `proforma_vietnam/xlsx_builder.py` with Summary, Cash Flow, Tax Schedule, Debt Service, and Assumptions sheets.
  - Add workbook tests that verify required sheets and key summary values.
  - Keep the workbook builder independent from Django until the workbook tests are green.

## 2026-05-25 - Phase 2 Vietnam Cash Flow Slice

- Implemented the first standalone Vietnam ESCO DCF module in `proforma_vietnam/cash_flow.py`.
- Added `calculate_vietnam_esco_cash_flow(...)` as a pure function that returns:
  - annual cash-flow rows,
  - total capex, debt principal, and equity investment,
  - project IRR, equity IRR, NPV, average DSCR, simple payback, and ROI.
- Formula coverage:
  - ESCO energy revenue uses project-served PV kWh times time-specific EVN energy rates times the ESCO discount fraction.
  - Energy revenue escalates with `evn_energy_escalation_rate`, default 4%.
  - Demand-charge savings are `max(BAU demand charge - optimized demand charge, 0)`.
  - Demand-charge savings escalate with `evn_capacity_escalation_rate`, default 4%.
  - ESCO demand-savings share defaults to 80%; offtaker retained share is the remaining 20%.
  - Grid charging remains disabled by default.
  - When grid charging is enabled, ESCO receives 100% of positive net grid-arbitrage value by default.
  - PV depreciation uses the existing 20-year straight-line helper; BESS depreciation uses the existing 8-year helper.
  - CIT uses the existing Vietnam holiday/reduced-rate helper.
  - Debt service uses a fixed annual amortizing payment with default 70% debt, 8.5% interest, and 10-year term.
- Added `proforma_vietnam/tests/test_cash_flow.py` covering:
  - discounted time-specific ESCO energy revenue,
  - default 80/20 demand-charge savings split,
  - base-case grid charging disabled behavior,
  - optional grid-charging arbitrage settlement,
  - investor metric outputs and Vietnam depreciation/CIT integration.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_cash_flow` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.cash_flow'`.
  - Green local run: `python -m unittest proforma_vietnam.tests.test_cash_flow` passed, 5 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow` passed, 9 tests.
  - First Docker unittest attempt failed before tests started with Docker Desktop API error reading `base-api-image:latest`.
  - Docker investigation showed `docker info` succeeded and `base-api-image:latest` existed; rerun passed.
  - Green Docker unittest run: `docker-compose run --rm --entrypoint python django -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow` passed, 9 tests.
  - Green Docker Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 9 tests, `System check identified no issues (0 silenced).`
- Current git state after this work: branch `master` is 7 commits ahead of `origin/master`; `CODEX_SESSION.md`, `SESSION_NOTES.md`, `proforma_vietnam/cash_flow.py`, and `proforma_vietnam/tests/test_cash_flow.py` have uncommitted changes.
- Next recommended work: review the `cash_flow.py` interface against one representative REopt result payload, then add `esco_pro_forma.py` as the adapter before starting XLSX/API integration.
- Resume point for next session:
  - Start in `proforma_vietnam/esco_pro_forma.py`.
  - First read `proforma_vietnam/cash_flow.py`, `proforma_vietnam/tests/test_cash_flow.py`, and `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`.
  - Inspect one representative V3 result payload shape before writing adapter code.
  - Write failing adapter tests with a small fake V3 results payload, then implement the adapter.
  - Keep grid charging disabled unless the V3 result payload clearly separates grid-charged battery discharge from PV-charged discharge.
- Phase 2 completion order before the final real-payload evaluation:
  1. REopt-results adapter: `proforma_vietnam/esco_pro_forma.py`.
  2. Adapter tests: `proforma_vietnam/tests/test_esco_pro_forma.py`.
  3. Workbook builder: `proforma_vietnam/xlsx_builder.py` with Summary, Cash Flow, Tax Schedule, Debt Service, and Assumptions sheets.
  4. Workbook tests: verify sheets, year rows, and key summary values.
  5. V3 Vietnam pro forma download endpoint or query-param flow.
  6. API integration test for the XLSX response.
  7. One actual Vietnam tariff payload run through the endpoint/workbook.
  8. Hand-built workbook comparison within +/-1%.
  9. Docker verification for `proforma_vietnam` and existing `proforma` tests.

## 2026-05-25 - Vietnam ESCO Contract Design Finalized

- Clarified that the calculation sequence is technical optimization first, then Vietnam ESCO pro forma. ROI, IRR, NPV, DSCR, and payback are outputs, not initial sizing inputs.
- User selected discount-to-EVN-tariff energy pricing:
  - Discount applies to time-specific current-year EVN energy tariff.
  - Discount applies to energy charge only, not demand/capacity value.
  - ESCO tariff escalation is pegged back-to-back to EVN escalation.
- User selected demand-charge savings handling:
  - Demand-charge savings are calculated from REopt results.
  - Default split is 80% ESCO / 20% offtaker.
- User selected grid-charging handling:
  - Grid charging is an optional scenario switch and disabled in the base case.
  - If enabled, net grid-charging arbitrage value belongs 100% to ESCO.
  - Grid charging cost must remain in the optimized EVN bill; ESCO receives net arbitrage value, not gross battery discharge revenue.
- Added `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md` as the finalized design source for the next `cash_flow.py` implementation.
- Updated `proforma_vietnam/ESCO_CONTRACT_MODEL_NOTES.md` to point to the finalized design.
- Next recommended work: write focused cash-flow tests for ESCO energy revenue, demand savings split, grid-charging disabled base case, and optional grid-arbitrage settlement before implementing `proforma_vietnam/cash_flow.py`.

## 2026-05-23 - Phase 2 Vietnam Tax Model Start

- Started Phase 2 Vietnam pro forma work in a new standalone `proforma_vietnam/` package.
- Added `proforma_vietnam/tax_model.py` with:
  - Standard Vietnam CIT rate constant: 20%.
  - CIT holiday: 4 years exempt.
  - CIT reduced period: 9 years at 50% of the standard rate, effective 10%.
  - PV straight-line depreciation period: 20 years, per user correction on 2026-05-23.
  - BESS straight-line depreciation period: 8 years.
  - `calculate_cit(...)` and `straight_line_depreciation_schedule(...)` pure helpers.
- Added `proforma_vietnam/tests/test_tax_model.py` covering:
  - 25-year CIT sequence for constant taxable income.
  - No CIT on negative or zero taxable income.
  - PV 20-year straight-line depreciation with zero depreciation after year 20.
  - BESS 8-year straight-line depreciation with zero depreciation after year 8.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_tax_model` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.tax_model'`.
  - Green local run: `python -m unittest proforma_vietnam.tests.test_tax_model` passed, 4 tests.
  - Green Docker unittest run: `docker-compose run --rm --entrypoint python django -m unittest proforma_vietnam.tests.test_tax_model` passed, 4 tests.
  - Green Docker Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam.tests.test_tax_model -v 2` passed, 4 tests, `System check identified no issues (0 silenced).`
- Current git state after this work: branch `master` is 4 commits ahead of `origin/master`; `proforma_vietnam/`, `CODEX_SESSION.md`, and `SESSION_NOTES.md` have uncommitted changes.
- Next recommended work: add `proforma_vietnam/cash_flow.py` and tests for 25-year VND DCF, EVN escalation, debt service assumptions, and use of the tested CIT/depreciation helpers.

## 2026-05-23 - Vietnam ESCO Contract Model Notes

- User clarified that the Vietnam pro forma should be a third-party investment model where the offtaker signs an ESCO contract covering energy offtake and peak shaving service.
- Paused `cash_flow.py` implementation until the commercial deal structure is discussed in more detail.
- Added `proforma_vietnam/ESCO_CONTRACT_MODEL_NOTES.md` as a discussion anchor for a separate conversation.
- Captured that existing REopt third-party ownership is a fixed annualized host payment / finance structure, not a detailed tariff-contract model.
- Captured open design questions for:
  - energy offtake pricing: EVN discount, fixed VND/kWh, or hybrid escalation,
  - peak shaving benefit sharing,
  - energy arbitrage sharing,
  - treatment of grid charging versus solar charging,
  - minimum offtaker savings and ESCO target equity IRR.
- Next recommended work: discuss and finalize these assumptions before adding `proforma_vietnam/cash_flow.py`.

## 2026-05-22 - Session Notes Split

- Moved the detailed latest session notes out of `CODEX_SESSION.md` into this dedicated file.
- Updated `AGENTS.md` so future agents read this file when context is needed and update it during session closeout.
- Updated `CODEX_SESSION.md` session-close guidance to point detailed notes here.

## 2026-05-22 - Phase 1 Acceptance Gate Closeout

- Confirmed Docker Desktop was running and started the full Compose stack with `docker-compose up -d`.
- Verified running services with `docker-compose ps`: `db`, `redis`, `julia`, `celery`, and `django` were up.
- Verified Django health with `docker-compose exec -T django python manage.py check`; result: `System check identified no issues (0 silenced).`
- The browser result page for `c9da7aa4-f544-425b-b0a0-ebb36e11132d` looked blank, but `Invoke-WebRequest` showed HTTP 200 with a large JSON body and the database later showed status `optimal`.
- Checked Celery/Julia logs while debugging the apparent blank browser page. Julia solved the submitted jobs with `termination_status(m) = OPTIMAL`; Celery task results were `SUCCESS`.
- Retrieved latest tariff output rows from Django:
  - `current`: run UUID `0ee531dc-625f-416f-a1dc-44e1671572d4`, status `optimal`, `year_one_bill_before_tax_bau=345975.02`, `year_one_energy_cost_before_tax_bau=345975.02`, `year_one_demand_cost_before_tax_bau=0.0`.
  - `decision_963`: run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d`, status `optimal`, `year_one_bill_before_tax_bau=345975.02`, `year_one_energy_cost_before_tax_bau=345975.02`, `year_one_demand_cost_before_tax_bau=0.0`.
- Ran the manual EVN baseline calculation inside the Django container using `build_example_payload(tou_schedule=...)`:
  - Formula: `sum(hourly_load_kw * tou_energy_rate_per_kwh)`.
  - `current`: manual total `345975.02`, REopt BAU bill `345975.02`, percent error `0.0%`, acceptance `True`.
  - `decision_963`: manual total `345975.02`, REopt BAU bill `345975.02`, percent error `0.0%`, acceptance `True`.
- Phase 1 acceptance gate is complete for the current example industrial load; next recommended work is Phase 2 Vietnam pro forma in a separate `proforma_vietnam/` module.
- Current git status before this handoff update: clean working tree, branch `master` was 3 commits ahead of `origin/master`, latest commit `e47c94ec Split session notes into dedicated handoff file`.

## 2026-05-18 - Latest Session Notes

- Started Docker Desktop-backed stack: `db`, `redis`, `julia`, `celery`, and `django` are running.
- Built missing local `base-api-image:latest` via `docker-compose build celery`.
- Created ignored local `keys.py` from `keys.py.template` to unblock settings import.
- Verified Django health with `docker-compose exec -T django python manage.py check`; result: `System check identified no issues (0 silenced).`
- Added Phase 1 Vietnam EVN tariff package under `reoptjl/src/vietnam/`.
- Added `evn_rates.py` with 2025 standard manufacturing rates and two-component pilot rates.
- Added `evn_tariff.py` builder returning `tou_energy_rates_per_kwh` and `monthly_demand_rates`.
- Added `example_submit.py` with a Vietnam payload using the builder output in `ElectricTariff`.
- Added `reoptjl/test/test_vietnam_tariff.py` covering 8760 output, Sunday no-peak behavior, voltage-level rates, USD conversion, base-rate multipliers, pilot Cp/Ca mapping, and example payload wiring.
- Added selectable TOU schedules via `tou_schedule`: `current` remains the default; `decision_963` models Decision 963/QD-BCT with no morning peak, off-peak hours 00:00-06:00, and evening peak mapped to hourly hours 18-22 for REopt's 8760 array.
- Updated `example_submit.py` so case studies can build payloads for either TOU structure.
- Verification run: `python -m unittest reoptjl.test.test_vietnam_tariff` passed locally.
- Verification run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_tariff -v 2` passed in Docker.
- Verification run: example payload smoke check produced 8760 hourly rates and empty standard `monthly_demand_rates`.
- Fixed `example_submit.py` to include `ElectricLoad.year=2025`; Julia rejects `loads_kw` payloads without `ElectricLoad.year`.
- Verification run: local Docker E2E `current` schedule submitted to `POST /v3/job/`, run UUID `a75db5cb-f345-40b9-a878-d88d57d3f930`, completed with status `optimal`.
- Verification run: local Docker E2E `decision_963` schedule submitted to `POST /v3/job/`, run UUID `18def5ef-6c6b-4f37-84f0-8967ecd0fc6d`, completed with status `optimal`.
- Verification run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_tariff -v 2` passed after the example payload fix.
- Updated local API credentials in ignored `keys.py` and tracked `julia_src/.env`; do not commit a real key unless this repository is kept private and that is intentional.
- Switched active developer API URLs from `developer.nrel.gov` to `developer.nlr.gov`; only the historical `reoptjl/migrations/0001_initial.py` migration still has the old string.
- Updated support email text from `reopt@nrel.gov` to `reopt@nlr.gov` in active/deprecated API response code.
- Simplified `docker-compose.yml` so `docker-compose up -d django` no longer calls the CRLF-sensitive `wait-for-it.bash` script.
- Added migration `reoptjl/migrations/0114_alter_apimeta_job_type.py` for the `APIMeta.job_type` default change to `developer.nlr.gov`; applied locally with `docker-compose run --rm --entrypoint python django manage.py migrate`.
- Verification run: `docker-compose up -d django` starts Django and `GET http://localhost:8000/v3/job/inputs/` returned HTTP 200.
- Verification run: Python container reports both local developer keys configured and Julia container sees `NREL_DEVELOPER_EMAIL`.
- Current git status: modified `CODEX_SESSION.md`, `docker-compose.yml`, `futurecosts/views.py`, `julia_src/.env`, `julia_src/http.jl`, `keys.py.template`, `reo/api.py`, `reo/exceptions.py`, `reo/src/pvwatts.py`, `reo/src/wind_resource.py`, `reo/validators.py`, `reo/views.py`, `reoptjl/api.py`, `reoptjl/models.py`, `reoptjl/src/vietnam/example_submit.py`, `reoptjl/test/test_vietnam_tariff.py`, `reoptjl/views.py`; untracked `reoptjl/migrations/0114_alter_apimeta_job_type.py` and `Sample Load Profile/`; no commit made.
