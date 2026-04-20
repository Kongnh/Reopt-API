# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** Multi-app Django monolith with async Celery workers and a sidecar Julia HTTP microservice

**Key Characteristics:**
- Django REST framework built on Tastypie `ModelResource` classes for all API surface area
- Long-running optimization jobs are dispatched asynchronously via Celery + Redis as the broker
- The actual mathematical optimization is performed by a separate Julia process (`julia_src/http.jl`) exposed on port 8081; Python calls it via HTTP POST using the `requests` library
- PostgreSQL stores all inputs, outputs, and job metadata — each technology (PV, Wind, Battery, CHP, etc.) maps to its own pair of Input/Output Django models
- Multiple versioned API namespaces (`v1`, `v2` — now EOL; `v3`/`stable` — active; `dev` — experimental) share the same Django process

## Layers

**API / Resource Layer:**
- Purpose: Receive HTTP POST, validate, persist inputs, dispatch Celery task, return `run_uuid`
- Location: `reoptjl/api.py`, `reo/api.py`, `resilience_stats/api.py`, `ghpghx/resources.py`, `futurecosts/api.py`
- Contains: Tastypie `ModelResource` subclasses (`Job`, `ERPJob`, `FutureCostsAPI`, `GHPGHXJob`)
- Depends on: Validators, Django models, Celery tasks
- Used by: URL router (`reopt_api/urls.py`)

**Validation Layer:**
- Purpose: Three-pass input validation (field-level → within-model → cross-model)
- Location: `reoptjl/validators.py` (`InputValidator`), `reo/validators.py` (`ValidateNestedInput`)
- Contains: `scrub_fields()`, `InputValidator.clean_fields()`, `.clean()`, `.cross_clean()`
- Depends on: Django models (`reoptjl/models.py`)
- Used by: API resource layer

**Model / Persistence Layer:**
- Purpose: Define schema for all inputs, outputs, and metadata; save/load from PostgreSQL
- Location: `reoptjl/models.py` (9 387 lines, ~55 model classes), `reo/models.py`, `resilience_stats/models.py`, `ghpghx/models.py`
- Contains: `BaseModel` mixin (serialization helpers), `APIMeta`, plus per-technology Input/Output model pairs
- Depends on: Django ORM, `django.contrib.postgres.fields.ArrayField`
- Used by: Validators, API layer, process_results

**Async Task Layer (Celery):**
- Purpose: Execute optimization jobs off the request/response cycle
- Location: `reoptjl/src/run_jump_model.py`, `reo/src/run_jump_model.py`, `futurecosts/tasks.py`
- Contains: `@shared_task` functions with `on_failure` hooks; `RunJumpModelTask` base class
- Depends on: Julia HTTP service (at `http://julia:8081/reopt/`), process_results, Django models
- Used by: API layer via `.apply_async()`

**Optimization Engine (Julia sidecar):**
- Purpose: Formulate and solve the mixed-integer linear program using REopt.jl
- Location: `julia_src/http.jl`, `julia_src/reopt_model.jl`, `julia_src/REopt.jl`
- Contains: HTTP server (`HTTP.jl`), solver setup (HiGHS, Cbc, SCIP, optional Xpress)
- Depends on: REopt.jl Julia package, GhpGhx Julia package
- Used by: Celery task layer via `requests.post("http://julia:8081/reopt/", json=data)`

**Results Processing Layer:**
- Purpose: Parse Julia response JSON and persist each technology's outputs to the DB
- Location: `reoptjl/src/process_results.py`, `reo/process_results.py`
- Contains: `process_results(results, run_uuid)`, `update_inputs_in_database()`
- Depends on: `reoptjl/models.py` Output model classes
- Used by: Celery task (`run_jump_model`)

**Views / Utility Endpoints Layer:**
- Purpose: Serve results reads, helper data lookups, summary pages, proforma generation
- Location: `reoptjl/views.py`, `reo/views.py`, `resilience_stats/views.py`, `proforma/views.py`, `summary/views.py`, `load_builder/views.py`
- Depends on: Django models, external APIs (NREL PVWatts, URDB, AVERT, Cambium, EASIUR)
- Used by: URL router

## Data Flow

**Optimization Job Submission (v3/stable):**

1. Client sends `POST /stable/v3/job/` with JSON scenario inputs
2. `reoptjl/api.py` `Job.obj_create()` assigns a `run_uuid`, builds `APIMeta` metadata dict
3. `InputValidator` (three passes: `clean_fields` → `clean` → `cross_clean`) validates and fills defaults
4. `input_validator.save()` persists all Input models to PostgreSQL (`APIMeta`, `SiteInputs`, `FinancialInputs`, technology-specific `*Inputs`, etc.)
5. `APIMeta.status` set to `"Optimizing..."`; `run_jump_model.s(run_uuid).apply_async()` queued in Redis
6. API returns HTTP 201 with `{"run_uuid": "<uuid>"}`

**Optimization Execution (Celery worker):**

7. Celery worker picks up `run_jump_model` task
8. `get_input_dict_from_run_uuid(run_uuid)` reads all Input models from DB into a flat dict
9. Task POSTs the input dict to `http://julia:8081/reopt/` (Julia HTTP server)
10. Julia formulates and solves the MIP; returns `{"results": {...}, "reopt_version": "...", "inputs_with_defaults_set_in_julia": {...}}`
11. `process_results(results, run_uuid)` iterates output keys and saves each technology's `*Outputs` model
12. `APIMeta.status` updated to optimization status (Optimal / Error / Timed-out)

**Result Retrieval:**

13. Client polls `GET /stable/v3/job/<run_uuid>/results/` → `reoptjl/views.py::results()`
14. View assembles all `*Inputs` and `*Outputs` model dicts into a nested JSON response keyed by technology name

**State Management:**
- All state is PostgreSQL-persisted; workers are stateless
- `APIMeta.status` field tracks job lifecycle: `"Validating..."` → `"Optimizing..."` → `"Optimal"` / error string
- Redis is used solely as a Celery task broker (not a cache)

## Core Domain

**APIMeta** (`reoptjl/models.py:151`): top-level job record linking all child input/output models via FK. Tracks `run_uuid`, `status`, `api_version`, `user_uuid`, `webtool_uuid`, `portfolio_uuid`, `reopt_version`.

**Technology Input/Output pairs** (all in `reoptjl/models.py`): Each dispatchable or load technology has a separate Input model and Output model linked to `APIMeta`:
- `PVInputs` / `PVOutputs` — photovoltaic
- `WindInputs` / `WindOutputs` — wind turbine
- `ElectricStorageInputs` / `ElectricStorageOutputs` — battery
- `GeneratorInputs` / `GeneratorOutputs` — backup generator
- `CHPInputs` / `CHPOutputs` — combined heat and power
- `ElectricHeaterInputs` / `ElectricHeaterOutputs`
- `ASHPSpaceHeaterInputs|WaterHeaterInputs` / `*Outputs` — air-source heat pump
- `BoilerInputs` / `BoilerOutputs`, `SteamTurbineInputs` / `SteamTurbineOutputs`
- `HotThermalStorageInputs|ColdThermalStorageInputs|HighTempThermalStorageInputs` / `*Outputs`
- `AbsorptionChillerInputs` / `AbsorptionChillerOutputs`
- `GHPInputs` / `GHPOutputs` — ground heat pump
- `CSTInputs` / `CSTOutputs` — concentrating solar thermal

**Load models**: `ElectricLoadInputs`, `SpaceHeatingLoadInputs`, `DomesticHotWaterLoadInputs`, `ProcessHeatLoadInputs`, `CoolingLoadInputs` (plus corresponding `*Outputs`)

**Financial/Tariff models**: `FinancialInputs` / `FinancialOutputs`, `ElectricTariffInputs` / `ElectricTariffOutputs`, `ElectricUtilityInputs` / `ElectricUtilityOutputs`

**BaseModel** (`reoptjl/models.py:101`): Mixin providing `.dict` property (serializes model fields to dict), `.create(**kwargs)` factory, `.info_dict()` for API documentation endpoint.

**Settings** (`reoptjl/models.py:237`): Per-job solver settings (`timeout_seconds`, `time_steps_per_hour`, `solver_choice`, `off_grid_flag`, etc.)

**OutageOutputs** (`reoptjl/models.py:2288`): Resilience/outage simulation output model; also used by the `resilience_stats` app independently via `ERPMeta`/`ERPOutputs`.

## Background Processing

**Broker:** Redis on port 6379 (`reopt_api/celery.py`). Queue name is derived from `APP_QUEUE_NAME` env var (defaults to `localhost`), allowing per-server queue isolation in multi-server deployments.

**Workers:** Celery workers launched via `celery -A reopt_api worker`. Tasks autodiscovered from all INSTALLED_APPS.

**Primary tasks:**
- `reoptjl/src/run_jump_model.py::run_jump_model(run_uuid)` — main REopt.jl optimization task
- `reo/src/run_jump_model.py::run_jump_model(data, bau)` — legacy v1/v2 task (EOL)
- `resilience_stats/api.py` — outage simulation dispatched as a Celery shared task
- `futurecosts/tasks.py::setup_jobs` — future costs analysis tasks

**Error handling:** `RunJumpModelTask.on_failure()` saves error details to `Message` model (linked to `APIMeta`) and updates `APIMeta.status`. Supported exception types: `REoptError`, `OptimizationTimeout`, `NotOptimal`, `REoptFailedToStartError`, `UnexpectedError` (all in `reo/exceptions.py`).

**Results backend:** `CELERY_RESULT_BACKEND = 'django-db'` — task results persisted via `django_celery_results`.

---

*Architecture analysis: 2026-04-15*
