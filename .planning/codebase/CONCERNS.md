# Codebase Concerns

**Analysis Date:** 2026-04-15

---

## Technical Debt

**`exec()` and `eval()` used for attribute access:**
- Issue: Dynamic attribute lookup via `exec()`/`eval()` instead of `getattr()` or proper data structures. This is fragile, untyped, and harder to trace.
- Files:
  - `futurecosts/tasks.py:35-36` — `exec("fcjob.future_scenario{} = ...")` inside a loop
  - `reo/src/data_manager.py:18,137-138,249,257,287,294-295` — `eval('cls.' + tech)`, `exec("self.pv" + str(pv_number) + " = ...")` patterns throughout
  - `reo/models.py:1290,1293` — `eval(modelName).objects.filter(...)` in `updateModel()`
  - `reo/validators.py:578-579,2045,2058,2064,2092` — multiple `eval()` calls during validation
  - `futurecosts/models.py:195` — `eval("self.{}.status".format(fs))`
- Impact: Makes code navigation and refactoring difficult; bypasses static analysis and IDE support; introduces subtle breakage risk.
- Fix approach: Replace `eval`/`exec` patterns with `getattr()`/`setattr()`, dictionaries, or numbered model relations.

**`PickledObjectField` still in use despite migration plan:**
- Issue: `django-picklefield` is still used in production models even though `reoptjl/models.py:6` documents the intent to remove it once v1 is retired.
- Files:
  - `reo/models.py:375,816,1114,1116,1140`
  - `ghpghx/models.py:126,137,148`
  - `reoptjl/models.py:9,4509`
  - `summary/models.py:6`
- Impact: Pickle deserialization is a known arbitrary code execution vector if data is tampered with at the DB layer. Also introduces hidden schema versioning issues when Python objects change.
- Fix approach: Migrate remaining `PickledObjectField` usages to `JSONField` (already used in `reoptjl`).

**v1/v2 API still active alongside v3:**
- Issue: Three API versions (`v1`, `v2`, `v3`, `stable`) all registered and served simultaneously. v1 uses `reo/` app (legacy Django-Tastypie); v3 uses `reoptjl/` (newer). Numerous TODOs reference v1 retirement that hasn't happened.
- Files: `reopt_api/urls.py`, `reo/api.py`, `reoptjl/api.py`
- Impact: Doubled maintenance burden; validation, models, and tests must be kept in sync across codebases for equivalent features.
- Fix approach: Define and communicate v1/v2 deprecation timeline; redirect traffic; retire `reo/` app.

**Proforma not implemented for v3:**
- Issue: `reopt_api/urls.py:73,81` has `# TODO proforma for v3` comments. Proforma functionality only works under v1/v2.
- Files: `reopt_api/urls.py`, `proforma/`
- Impact: Users of the v3/stable API cannot generate financial proforma spreadsheets.
- Fix approach: Port `proforma/proforma_generator.py` to work with v3 model outputs.

**`FutureCostsJob` scenario fields use numbered attributes instead of a relation:**
- Issue: `FutureCostsJob` stores up to 10 future scenarios as `future_scenario1` … `future_scenario10` and `future_year1` … `future_year10` individual fields rather than a related model.
- Files: `futurecosts/models.py`, `futurecosts/tasks.py:35-36`
- Impact: Hard to iterate, extend, or query; currently accessed via `exec()` string building.
- Fix approach: Replace with a `FutureScenario` child model with a FK to `FutureCostsJob`.

**Hardcoded NREL API key for URDB rate downloads:**
- Issue: A literal API key string `"BLLsYv81d8y4w6UPYCfGFsuWlu4IujlZYliDmoq6"` is hardcoded directly in source code for OpenEI URDB lookups.
- Files: `reo/src/urdb_rate.py:78`
- Impact: If the key is rotated or rate-limited, the rate-lookup feature breaks silently. Key is publicly visible in the repository.
- Fix approach: Move to `keys.py` (already used for other NREL keys) or an environment variable.

**Celery memory growth workaround with `CELERY_WORKER_MAX_MEMORY_PER_CHILD`:**
- Issue: Production and staging settings include a comment acknowledging an unresolved memory growth problem in Celery workers, mitigated by recycling workers at 4 GB.
- Files: `reopt_api/production_settings.py:116-119`, `reopt_api/staging_settings.py:115-116`
- Impact: Under heavy load, workers restart frequently, potentially dropping queued jobs or causing latency spikes.
- Fix approach: Profile Celery task memory usage; identify leaked references (likely in Julia result deserialization or large NumPy arrays); eliminate root cause rather than relying on `max_memory_per_child`.

**GHP `ghpghx_inputs` stored as `ArrayField(PickledObjectField)`:**
- Issue: `reo/models.py:1114-1140` stores GHP inputs and responses as arrays of pickled objects, and the UUID field is still a plain text field rather than a `UUIDField`.
- Files: `reo/models.py:1138` — `# TODO may make this a UUIDField once it's actually assigned one from the GHPGHX endpoint`
- Impact: Schema fragility and pickle-related risks; UUID constraints not enforced at DB level.

---

## Security

**Hardcoded API key in source:**
- Risk: `reo/src/urdb_rate.py:78` contains `api_key = "BLLsYv81d8y4w6UPYCfGFsuWlu4IujlZYliDmoq6"` — a live key committed to the repository.
- Files: `reo/src/urdb_rate.py`
- Current mitigation: `keys.py` is `.gitignore`d, but this key is in a tracked source file.
- Recommendation: Rotate the key, move it to `keys.py` or an env var, remove from tracked source.

**`ALLOWED_HOSTS = ['*']` in all settings files:**
- Risk: All settings (dev, staging, production) set `ALLOWED_HOSTS = ['*']`, which disables Django's host header validation and is a vector for HTTP Host header attacks.
- Files: `reopt_api/dev_settings.py:29`, `reopt_api/staging_settings.py`, `reopt_api/production_settings.py:29`
- Recommendation: Set `ALLOWED_HOSTS` to explicit domain names in staging and production.

**`MIDDLEWARE_CLASSES` instead of `MIDDLEWARE`:**
- Risk: All settings files use the Django 1.x `MIDDLEWARE_CLASSES` setting, which is ignored by Django 4.x. The actual middleware stack applied at runtime may differ from what is configured.
- Files: `reopt_api/dev_settings.py:51`, `reopt_api/staging_settings.py:51`, `reopt_api/production_settings.py:52`, `reopt_api/internal_c110p_settings.py:47`
- Impact: Security middleware (`SecurityMiddleware`, `XFrameOptionsMiddleware`) declared in `MIDDLEWARE_CLASSES` is NOT being applied. This means clickjacking protection and other HTTP security headers are likely absent.
- Recommendation: Rename all `MIDDLEWARE_CLASSES` to `MIDDLEWARE` immediately.

**`PickledObjectField` deserialization from database:**
- Risk: Python's `pickle` deserializes arbitrary bytecode. If database rows can be tampered with (e.g., via SQL injection or compromised DB credentials), pickle fields can execute arbitrary code on deserialization.
- Files: See Technical Debt section above.
- Recommendation: Migrate to `JSONField` as planned.

**Plain HTTP for internal Julia service communication:**
- Risk: All inter-service calls from Django to the Julia optimizer use `http://` with no authentication.
- Files: `reoptjl/src/run_jump_model.py:67`, `reo/src/run_jump_model.py:64`, `reoptjl/views.py` (multiple endpoints)
- Current mitigation: Services communicate on an internal Docker network. Acceptable only if network perimeter is enforced.
- Recommendation: Document the network trust boundary explicitly; add service-to-service auth if the network boundary ever relaxes.

**UUID length check instead of UUID validation:**
- Risk: `reoptjl/api.py:81` validates `user_uuid` by checking `len(bundle.data['user_uuid']) == len(run_uuid)` — checking character length rather than actual UUID format.
- Files: `reoptjl/api.py:78-86`
- Impact: Malformed but correctly-lengthed strings will pass validation and be saved to DB.
- Recommendation: Use `uuid.UUID(user_uuid)` validation (already used in `reo/views.py:154`).

**Hardcoded webtool UUID used to classify job type:**
- Risk: `reoptjl/api.py:130` contains a hardcoded UUID string `'6f09c972-8414-469b-b3e8-a78398874103'` used to classify a request as coming from the "REopt Web Tool".
- Files: `reoptjl/api.py:130`
- Impact: This is effectively a shared secret with no access control — any client can spoof it.
- Recommendation: Move to an environment variable or a proper API key validation mechanism.

**SQL injection concern in `reo/views.py`:**
- Issue: Comment in `reo/views.py:17` — `# should we save bad requests? could be sql injection attack?` — indicates an unresolved security question about whether to log raw request data.
- Files: `reo/views.py:17`
- Recommendation: Clarify and document whether raw input is ever written to DB without sanitization.

---

## Performance

**Celery worker memory growth (unresolved):**
- Problem: Acknowledged memory leak in Celery workers requiring recycling at 4 GB.
- Files: `reopt_api/production_settings.py:116-119`
- Cause: Likely large in-memory data structures (8760-length time series, NumPy arrays) not being released after task completion; may also be related to legacy PyJulia reference (noted in comment).
- Improvement path: Use memory profiling (`tracemalloc`, `objgraph`) on a production-like worker to identify retained objects.

**Summary endpoint issues multiple separate DB queries per model type:**
- Problem: `summary/views.py:113-155` queries 15+ separate model tables individually for each result set rather than using `select_related` or a single aggregating query.
- Files: `summary/views.py:113-155`
- Cause: Each technology (PV, Wind, Generator, Storage, CHP, etc.) is fetched with a separate `.filter()` call.
- Improvement path: Consider a denormalized summary table updated on result write, or use `prefetch_related` combined with annotated queries.

**Large monolithic models file (`reoptjl/models.py` — 9387 lines):**
- Problem: The entire v3 data model is in a single file, causing slow import times and making it difficult to isolate concerns.
- Files: `reoptjl/models.py`
- Improvement path: Split into per-technology sub-modules and re-export from a package `__init__.py`.

**Proforma generator is a single 4985-line file:**
- Problem: `proforma/proforma_generator.py` contains all spreadsheet generation logic for v1/v2 in one file.
- Files: `proforma/proforma_generator.py`
- Improvement path: Decompose into per-section generator classes.

**Wind resource file caching not implemented:**
- Problem: `reo/src/wind.py:203` has `# TODO: check input_files for previously downloaded wind resource file` — wind resource files are re-downloaded on every run.
- Files: `reo/src/wind.py`
- Impact: Repeated identical API calls to NREL wind toolkit; increased latency and external dependency load.

---

## Outdated / Deprecated

**`MIDDLEWARE_CLASSES` (Django 1.x setting used in Django 4.2 project):**
- All settings files use the obsolete `MIDDLEWARE_CLASSES` key. Django 4.x silently ignores it and uses only `MIDDLEWARE`. None of the declared middleware (security, auth, session) is active.
- Files: `reopt_api/dev_settings.py`, `reopt_api/staging_settings.py`, `reopt_api/production_settings.py`, `reopt_api/internal_c110p_settings.py`
- Fix: Rename `MIDDLEWARE_CLASSES` → `MIDDLEWARE` in all settings files.

**`SessionAuthenticationMiddleware` removed in Django 1.10:**
- The `django.contrib.auth.middleware.SessionAuthenticationMiddleware` class no longer exists in Django 1.10+. It is listed in `MIDDLEWARE_CLASSES` in all settings files but has no effect (and would cause an error if `MIDDLEWARE_CLASSES` were fixed to `MIDDLEWARE`).
- Files: All settings files
- Fix: Remove `SessionAuthenticationMiddleware` from all middleware lists.

**`django-picklefield` marked for removal:**
- `reoptjl/models.py:6` contains `# TODO rm picklefield from requirements.txt once v1 is retired`.
- Still in `requirements.txt` and actively used in v1 models.

**`ez_setup.py` is obsolete setuptools bootstrapper:**
- `ez_setup.py` is a very old (pre-pip) setuptools bootstrap script. It has no functional role in a modern Python 3.12 project.
- Files: `ez_setup.py`
- Fix: Delete the file.

**`adal==1.2.7` is deprecated:**
- The `adal` (Azure Active Directory Authentication Library) package is deprecated in favor of `msal`. It remains in `requirements.txt`.
- Files: `requirements.txt:2`
- Fix: Evaluate whether Azure AD auth is still used; if so, migrate to `msal`.

**Django settings comment references Django 2.2 docs:**
- `reopt_api/dev_settings.py` and others have docstrings referencing `https://docs.djangoproject.com/en/2.2/`. The project runs Django 4.2.
- Files: All settings files
- Impact: Developers reading the settings may follow outdated documentation.

---

## Testing Gaps

**GHPGHX tests incomplete:**
- `ghpghx/tests/test_ghpghx.py:73` has `#TODO make a test once GHPGHX is finalized`. The key hybrid GHPGHX path is not tested.
- Files: `ghpghx/tests/test_ghpghx.py`

**ERP tests have known bugs noted in comments:**
- `resilience_stats/tests/test_erp.py:82` — `#TODO: resolve bug where unlimited fuel markov portion of results goes to zero 1 timestep early`
- `resilience_stats/tests/test_erp.py:177` — `#TODO: don't return run_uuid when there's a REoptFailedToStartError`
- Files: `resilience_stats/tests/test_erp.py`

**No test coverage for `futurecosts` app:**
- `futurecosts/tests.py` exists but appears empty. The FutureCosts workflow (posting 10 future scenario jobs, tracking statuses) has no automated test coverage.
- Files: `futurecosts/tests.py`

**Proforma test class incomplete:**
- `proforma/tests/test_pro_forma.py` has only `test_bad_run_uuid` — it verifies the endpoint returns an error for a bad UUID but does not test actual proforma generation.
- Files: `proforma/tests/test_pro_forma.py`

**No test for `summary` endpoint correctness:**
- `summary/tests/test_summary_and_unlink.py` tests the unlink flow but no test verifies the summary response fields against actual optimization outputs.
- Files: `summary/tests/`

**`reoptjl` validator alignment with v1 unresolved:**
- `reoptjl/validators.py:54` — `# TODO figure out how to align with MessagesModel from v1 with validation errors`. Resampling behavior alignment between v1 and v3 is also undocumented.
- Files: `reoptjl/validators.py:54,638-639`

**No coverage configuration detected:**
- No `.coveragerc`, `pytest.ini`, or coverage threshold configuration found. Test coverage is not measured or enforced.

**Test result numeric tolerances undocumented:**
- `reoptjl/test/test_job_endpoint.py:35` — `# TODO figure out why microgrid_upgrade_capital_cost is about $3000 different locally than on GitHub Actions`. Results differ between environments with no explanation or accepted tolerance documented.
- Files: `reoptjl/test/test_job_endpoint.py`

---

## Documentation Gaps

**v3 inputs/outputs endpoints not documented in wiki:**
- `reoptjl/views.py:96` — `# TODO document inputs and outputs endpoints in Analysis wiki once deployed`.
- Files: `reoptjl/views.py`

**`reoptjl/api.py` disables `api_key` from request:**
- `reoptjl/api.py:77` — `api_key = keys.developer_nrel_gov_key #bundle.request.GET.get("api_key", "")`. The request-provided `api_key` is silently ignored and replaced with the server's own key. This behavior is undocumented.

**GHP model field validation methods unimplemented:**
- `ghpghx/models.py:153,160,165` contain multi-line TODO docstrings explaining that `clean_cop_map()` and `clean()` (for pipe diameter vs. shank space validation) need to be defined.
- Files: `ghpghx/models.py`

**Profiler not confirmed in use:**
- `reoptjl/src/run_jump_model.py:51` — `profiler = Profiler()  # TODO? are we still using the Profile?`. Profiling infrastructure exists but it's unclear if timing data is ever consumed.
- Files: `reoptjl/src/run_jump_model.py`, `reo/src/profiler.py`

---

## Complexity Hotspots

**`reoptjl/models.py` (9387 lines):**
- Contains all v3 Django model definitions — inputs, outputs, and helper methods for every technology. Any change to a model requires navigating nearly 10,000 lines. Star-import from `django.contrib.postgres.fields` (`from django.contrib.postgres.fields import *`) also hides where fields come from.
- Safe modification: Identify natural technology boundaries (PV, Wind, Storage, CHP, GHP, etc.) and split into a `reoptjl/models/` package.

**`proforma/proforma_generator.py` (4985 lines):**
- Single-file spreadsheet generator covering all technologies and financial calculations for v1/v2. Deeply nested conditional logic.
- Safe modification: Only modify within explicitly identified row-generation methods; add regression tests before refactoring.

**`reo/validators.py` (2450 lines) and `reo/nested_inputs.py` (2717 lines):**
- Validation and input schema definition for v1 are tightly coupled. `validators.py` uses `eval()` extensively to dynamically look up field types defined in `nested_inputs.py`.
- Safe modification: Do not change field names in `nested_inputs.py` without tracing all `eval()` callsites in `validators.py`.

**`reo/src/data_manager.py` (2059 lines):**
- Builds optimization input dictionaries from Django models. Uses `exec()`/`eval()` for dynamic PV numbering and tech iteration. Any new technology must be threaded through multiple methods manually.
- Safe modification: Trace the full `DataManager` method call chain; use integration tests to verify optimizer input JSON after any change.

**`reoptjl/views.py` (2594 lines):**
- Contains all v3 view functions including optimization job submission, results retrieval, and 15+ helper endpoints. Single-file scope makes it hard to identify the request/response contract for any individual endpoint.
- Safe modification: Use the URL routing in `reoptjl/urls.py` to identify which view function handles each endpoint before editing.

---

*Concerns audit: 2026-04-15*
