# Codebase Structure

**Analysis Date:** 2026-04-15

## Directory Layout

```
REopt_API/
├── reopt_api/          # Django project package — settings, root URLs, Celery app, WSGI
├── reoptjl/            # Active v3/stable API app (REopt.jl-backed)
├── reo/                # Legacy v1/v2 app (EOL March 2024, still present)
├── resilience_stats/   # Outage simulation & ERP (Emergency Response Planning) app
├── ghpghx/             # Ground-source heat pump GHX sizing app
├── proforma/           # Financial proforma Excel report generation app
├── summary/            # User run summary/history app
├── load_builder/       # Utility load profile construction app
├── futurecosts/        # Experimental future costs analysis app (dev API)
├── julia_src/          # Julia HTTP microservice (REopt.jl optimization engine)
├── config/             # Deployment config (Gunicorn, Capistrano deploy scripts)
├── nginx/              # Nginx config for production reverse-proxy
├── input_files/        # Static input data files (weather, load profiles, etc.)
├── static/             # Django static files
├── log/                # Application log directory
├── bin/                # Server/worker startup shell scripts
├── EVI-EnLitePy/       # Git submodule — EV load profile tool
├── keys.py.template    # Template for secrets/keys configuration file
├── manage.py           # Django management entry point
├── Procfile            # Foreman/Honcho process definitions (web + worker)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Main Python app container image
├── docker-compose.yml  # Local dev stack (redis, db, celery, django, julia)
└── docker-compose.nginx.yml  # Production stack with nginx
```

## Directory Purposes

**`reopt_api/`:**
- Purpose: Django project configuration package
- Contains: `urls.py` (root URL dispatcher registering all versioned APIs), `celery.py` (Celery app init, broker config, queue config), `wsgi.py`, settings files per environment
- Key files: `reopt_api/urls.py`, `reopt_api/celery.py`, `reopt_api/dev_settings.py`, `reopt_api/production_settings.py`, `reopt_api/staging_settings.py`

**`reoptjl/`:**
- Purpose: Primary active API app; handles all `v3/` and `stable/` routes
- Contains: API resource (`api.py`), URL patterns (`urls.py`), views for results/helpers (`views.py`), input/output Django models for all technologies (`models.py`), input validator (`validators.py`), Celery task + Julia bridge (`src/run_jump_model.py`), results parser (`src/process_results.py`), custom results table helpers, URDB rate validator
- Key files: `reoptjl/api.py`, `reoptjl/models.py`, `reoptjl/validators.py`, `reoptjl/urls.py`, `reoptjl/views.py`, `reoptjl/src/run_jump_model.py`, `reoptjl/src/process_results.py`

**`reo/`:**
- Purpose: Legacy v1/v2 API app (EOL — all POST endpoints now return HTTP 410)
- Contains: `api.py` (Job, Job2 Tastypie resources — commented out logic), `models.py` (ScenarioModel and ~40 technology models), `validators.py` (ValidateNestedInput), `scenario.py` (setup_scenario Celery task), `src/` (data managers, load profile builders, URDB parser, PVWatts, wind resource, SSC bindings)
- Key files: `reo/api.py`, `reo/models.py`, `reo/src/data_manager.py`, `reo/src/load_profile.py`, `reo/src/pvwatts.py`

**`resilience_stats/`:**
- Purpose: Outage simulation and Emergency Response Planning (ERP) app; available on v1, v2, v3, stable
- Contains: `api.py` (OutageSimJob, ERPJob Tastypie resources), `views.py` (run_outage_sim), `models.py`, `outage_simulator_LF.py`, `validators.py`
- Key files: `resilience_stats/api.py`, `resilience_stats/views.py`, `resilience_stats/models.py`

**`ghpghx/`:**
- Purpose: Ground-source heat pump GHX sizing calculations; available on v1, v2, v3, stable
- Contains: `resources.py` (GHPGHXJob Tastypie resource), `models.py` (GHPGHXInputs), `src/` (calculation engine), `validators.py`
- Key files: `ghpghx/resources.py`, `ghpghx/models.py`

**`proforma/`:**
- Purpose: Generate Excel financial proforma workbooks from completed run results
- Contains: `views.py`, `proforma_generator.py`, `models.py`, template `.xlsx` files
- Key files: `proforma/proforma_generator.py`, `proforma/REoptCashFlowTemplateOneParty.xlsx`

**`summary/`:**
- Purpose: Per-user run history/summary listing endpoint
- Contains: `views.py`, `models.py`, `urls.py`

**`load_builder/`:**
- Purpose: Build custom electric load profiles from DOE reference building data or user uploads
- Contains: `views.py`, `urls.py`, `tests/`

**`futurecosts/`:**
- Purpose: Experimental future technology cost projection runs (accessible via `dev/` route)
- Contains: `api.py` (FutureCostsAPI), `tasks.py` (Celery setup_jobs), `models.py`, `cost_data/`

**`julia_src/`:**
- Purpose: Standalone Julia HTTP microservice; runs as a separate container on port 8081
- Contains: `http.jl` (HTTP server entry point, `/reopt/` endpoint), `reopt_model.jl`, `REopt.jl` (local REopt.jl module for v1/v2), `os_solvers.jl` (HiGHS/Cbc/SCIP solver setup), `xpress_model.jl` (optional Xpress solver), `Project.toml`, `Manifest.toml`
- Key files: `julia_src/http.jl`, `julia_src/reopt_model.jl`, `julia_src/Project.toml`

**`config/`:**
- Purpose: Deployment configuration
- Contains: `gunicorn.conf.py` (Gunicorn workers/timeout settings), `deploy/` (Capistrano deploy scripts for development/staging/production environments)
- Key files: `config/gunicorn.conf.py`, `config/deploy/deploy.rb`

## Key File Locations

**Entry Points:**
- `manage.py`: Django CLI entry point (uses `reopt_api.dev_settings` by default)
- `reopt_api/wsgi.py`: WSGI entry point (loaded by Gunicorn via `config/gunicorn.conf.py`)
- `reopt_api/celery.py`: Celery application init; autodiscovers tasks from all INSTALLED_APPS
- `julia_src/http.jl`: Julia HTTP server entry point; started by `julia --project=. -e '...; include("http.jl")'`
- `Procfile`: Defines `web` (Gunicorn via `bin/server`) and `worker` (Celery via `bin/worker`) processes

**Root URL Routing:**
- `reopt_api/urls.py`: Mounts all versioned URL groups; registers Tastypie `Api` instances for `v1`, `v2`, `v3`, `stable`, `dev`

**Per-App URL Routing:**
- `reoptjl/urls.py`: All v3/stable view-based endpoints
- `reo/urls.py`: Legacy v1 utility view endpoints
- `reo/urls_v2.py`: Legacy v2 utility view endpoints
- `resilience_stats/urls_v1_v2.py`, `resilience_stats/urls_v3plus.py`: Outage sim routes by version
- `ghpghx/urls.py`, `proforma/urls.py`, `summary/urls.py`, `load_builder/urls.py`

**Configuration:**
- `keys.py.template`: Template showing required secrets structure (copy to `keys.py`; never commit actual `keys.py`)
- `reopt_api/dev_settings.py`: Development Django settings (PostgreSQL, Redis, Rollbar, Celery)
- `reopt_api/production_settings.py`: Production settings
- `reopt_api/staging_settings.py`: Staging settings
- `docker-compose.yml`: Local dev environment (services: redis, db, celery, django, julia)

**Core Business Logic:**
- `reoptjl/models.py`: All 55+ Input/Output Django model classes (~9 400 lines)
- `reoptjl/validators.py`: `InputValidator` — three-pass validation pipeline
- `reoptjl/src/run_jump_model.py`: Celery task bridging Python → Julia HTTP API
- `reoptjl/src/process_results.py`: Julia response → Django model persistence
- `reoptjl/views.py`: Results retrieval and all utility GET endpoints
- `reo/src/data_manager.py`: v1/v2 legacy data assembly layer
- `reo/src/load_profile.py`, `reo/src/pvwatts.py`, `reo/src/wind.py`: External data fetch utilities (still used by some helper endpoints in v3)

**Testing:**
- `reoptjl/test/test_job_endpoint.py`: Integration tests for v3 job endpoint
- `reoptjl/test/test_validator.py`: Unit tests for InputValidator
- `reoptjl/test/test_http_endpoints.py`: HTTP endpoint smoke tests
- `reoptjl/test/posts/`: JSON POST body fixtures for tests
- `reo/tests/`, `resilience_stats/tests/`, `ghpghx/tests/`, `proforma/tests/`, `summary/tests/`, `load_builder/tests/`

## Naming Conventions

**Files:**
- Django app files follow standard Django conventions: `models.py`, `views.py`, `urls.py`, `api.py`, `validators.py`, `admin.py`, `migrations/`
- Celery task files: `tasks.py` (futurecosts) or `src/run_jump_model.py` (reoptjl, reo)
- Julia files: lowercase with underscores, `.jl` extension

**Django Model Classes:**
- Input models: `<Technology>Inputs` (e.g., `PVInputs`, `ElectricStorageInputs`)
- Output models: `<Technology>Outputs` (e.g., `PVOutputs`, `ElectricStorageOutputs`)
- Meta/junction: `APIMeta`, `ERPMeta`, `UserUnlinkedRuns`, `PortfolioUnlinkedRuns`

**API Resources (Tastypie):**
- Named `Job` within each app's `api.py`; disambiguated by import alias in `reopt_api/urls.py`

## Where to Add New Code

**New optimization technology (input/output modeling):**
- Add `<Tech>Inputs` and `<Tech>Outputs` model classes to `reoptjl/models.py`
- Register models in `reoptjl/validators.py` `InputValidator.objects` tuple
- Add result persistence branch in `reoptjl/src/process_results.py`
- Add imports to `reoptjl/views.py` for the results endpoint assembly
- Create migration: `python manage.py makemigrations reoptjl`

**New v3/stable API utility endpoint:**
- Add view function to `reoptjl/views.py`
- Add URL pattern to `reoptjl/urls.py`

**New Celery background task:**
- Add `@shared_task` function to the relevant app's `tasks.py` or `src/` directory
- Celery autodiscovers tasks — no manual registration needed

**New app/module:**
- Create Django app with `python manage.py startapp <appname>`
- Add to `INSTALLED_APPS` in `reopt_api/dev_settings.py` (and other settings files)
- Mount URLs in `reopt_api/urls.py`

**Shared utilities:**
- Per-technology calculation helpers: `reo/src/<technology>.py` (legacy) or new file in `reoptjl/src/`
- Cross-app exception types: `reo/exceptions.py`

## Special Directories

**`reo/src/data/`:**
- Purpose: Static reference data (emissions factors, fuel rates, URDB cache)
- Generated: No
- Committed: Yes

**`reoptjl/migrations/`**, **`reo/migrations/`**, etc.:
- Purpose: Django database migration history
- Generated: Yes (via `makemigrations`)
- Committed: Yes

**`input_files/`:**
- Purpose: Static input data files referenced at runtime (e.g., load profile templates, weather data)
- Generated: No
- Committed: Yes

**`EVI-EnLitePy/`:**
- Purpose: Git submodule for EV load profile generation
- Generated: No (external submodule)
- Committed: As submodule reference only

**`static/`:**
- Purpose: Django static assets served by `collectstatic`
- Generated: Partially (via `collectstatic`)
- Committed: Partially

---

*Structure analysis: 2026-04-15*
