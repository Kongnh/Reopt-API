# External Integrations

**Analysis Date:** 2026-04-15

## Databases

**Primary Database:**
- PostgreSQL (latest via `postgres` Docker image)
  - Django ORM via `psycopg2` adapter
  - Engine: `django.db.backends.postgresql_psycopg2`
  - Schema search path: `reopt_api` in staging/production, `public` in local/test
  - Connection configured via env vars `SQL_HOST`, `SQL_PORT` (local) or `keys.py` variables (`dev_database_host`, `prod_database_host`, etc.)
  - Django migrations in `reo/migrations/`, `reoptjl/migrations/`, `ghpghx/migrations/`, `resilience_stats/migrations/`, `futurecosts/migrations/`, `proforma/migrations/`, `summary/migrations/`
  - Celery task results stored in DB via `django_celery_results` (table backed `CELERY_RESULT_BACKEND = 'django-db'`)

**ORM:**
- Django ORM (primary) - all models defined in `*/models.py` files per Django app
- SQLAlchemy 2.0.43 - present as dependency, used in specific data-access scenarios alongside Django ORM

## External APIs & Services

**NREL Developer API (`developer.nrel.gov`):**
- **PVWatts v6** - Solar irradiance and PV production data
  - Endpoint: `https://developer.nrel.gov/api/pvwatts/v6.json`
  - Client: `reo/src/pvwatts.py` using `requests`
  - Auth: `developer_nrel_gov_key` / `pvwatts_api_key` from `keys.py`
- **HSDS Wind Toolkit** - Hourly wind resource data from NREL Wind Toolkit (2012 data)
  - Endpoint: `https://developer.nrel.gov/api/hsds/`
  - Client: `reo/src/wind_resource.py` using `h5pyd` library
  - Auth: `developer_nrel_gov_key` from `keys.py`; also requires `~/.hscfg` config file on the host

**URDB (Utility Rate Database - OpenEI):**
- Electricity tariff rate lookup by utility name/rate name or URDB label
  - Client: `reo/src/urdb_rate.py` and `reo/src/urdb_parse.py` using `requests`
  - Validator: `reo/validators.py` (`URDB_RateValidator` class)
  - Error logging: `reo/urdb_logger.py`, stored in `URDBError` Django model (`reo/models.py`)
  - Rate version 3 = US URDB, version 4 = International URDB

**NREL SAM (System Advisor Model):**
- Solar and wind simulation via SSC (SAM Simulation Core) native library
  - Python bindings: `reo/src/sscapi.py`
  - Shared libraries: `reo/src/ssc.so` (Linux), `reo/src/ssc.dll` (Windows), `reo/src/ssc.dylib` (macOS)
  - Used in: `reo/src/wind.py` (wind resource processing)

**Google APIs:**
- `google-api-python-client` + `google-auth` + `google-auth-oauthlib` present in `requirements.txt`
- Exact usage not surfaced in top-level code; likely used for data access or reporting

**Azure:**
- `azure-core`, `msrest`, `msrestazure` present in `requirements.txt`
- Likely used for NREL internal infrastructure access

## Message Queues / Async

**Redis:**
- Image: `redis` (latest) via Docker
- Port: 6379 (internal to Docker network)
- Role: Celery message broker
- Connection: `redis://<host>:6379/0`; host configured via:
  - `REDIS_HOST` env var (local/Docker)
  - `dev_redis_host` / `staging_redis_host` / `production_redis_host` from `keys.py` (deployed envs)
  - Password via `dev_redis_password`, `staging_redis_password`, `production_redis_password` from `keys.py`
- Queue naming: per-server queues named after hostname (`APP_QUEUE_NAME` env var), configured in `reopt_api/celery.py`

**Celery:**
- Version: 5.5.3
- App: `reopt_api` (defined in `reopt_api/celery.py`)
- Broker: Redis (above)
- Result backend: Django DB (`django_celery_results`)
- Registered task modules (from `CELERY_IMPORTS` in settings):
  - `reo.api` - v1/v2 optimization job submission
  - `reo.scenario` - scenario setup
  - `reo.process_results` - result post-processing
  - `reo.src.run_jump_model` - calls Julia optimization engine
  - `resilience_stats.outage_simulator_LF` - resilience/outage simulation
  - `futurecosts.api` + `futurecosts.tasks` - future costs analysis
  - `reoptjl.api` - v3/stable optimization job submission
  - `reoptjl.src.run_jump_model` - calls Julia optimization engine (v3)
- Worker memory limit: 4 GB (`CELERY_WORKER_MAX_MEMORY_PER_CHILD = 4000000`)
- Production concurrency: 1 worker per pod (`CELERY_WORKER_CONCURRENCY = 1`)

**Julia HTTP Microservice:**
- Julia optimization engine runs as a separate HTTP server on port 8081
- Entry point: `julia_src/http.jl`
- Python calls it via HTTP from `reo/src/run_jump_model.py` and `reoptjl/src/run_jump_model.py`
- Host configurable via `JULIA_HOST` env var (default: `julia` service in Docker network, or `host.docker.internal` for local)
- Solvers available: HiGHS (open-source default), Cbc, SCIP, Xpress (commercial, optional; controlled by `XPRESS_INSTALLED` env var)

## Storage

**File Storage:**
- Local filesystem only; no S3 or cloud object storage detected
- Static files: `static/` directory; served via `STATIC_ROOT` / `STATIC_URL` in Django settings
- Input files: `input_files/` directory at project root
- Wind cache: `reo/wind_cache/` directory
- Log files: `log/` directory
- Julia source: `julia_src/` directory (mounted as Docker volume in development)

**HDF5 Data Files:**
- Wind Toolkit data accessed remotely via HSDS at `developer.nrel.gov` (see External APIs above)
- Local HDF5 access via `h5py` and `tables` for emissions and other reference datasets in `reo/src/data/`

**Excel Reports:**
- Proforma financial reports generated as `.xlsx` files via `openpyxl` and `xlsxwriter`
- Generator: `proforma/proforma_generator.py`
- Served as static file downloads

## Authentication & Authorization

**API Key (NREL Developer API):**
- Single API key `developer_nrel_gov_key` / `pvwatts_api_key` in `keys.py` (from `keys.py.template`)
- Used for all outbound calls to `developer.nrel.gov` (PVWatts, HSDS wind data)
- DEMO_KEY usable for development/testing

**Django Secret Key:**
- `secret_key_` in `keys.py`; used for Django session signing and CSRF

**Rollbar:**
- `rollbar_access_token` in `keys.py`; used for error reporting to Rollbar service

**Inbound API Authorization:**
- tastypie `ReadOnlyAuthorization` on all API resources (see `reo/api.py`, `reoptjl/api.py`)
- No user login or token-based auth enforced at the API layer; the API is effectively public/open
- No OAuth, API key validation for inbound requests detected in the codebase

**Deployment Secrets:**
- All environment-specific credentials (DB passwords, Redis passwords, Rollbar token) stored in `keys.py` at deploy time
- In Kubernetes deployments: Helm secret values files (`.helm/secret-values.*.yaml`) encrypted with `WERF_SECRET_KEY`
- AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) injected by Jenkins for ECR image push

## Monitoring & Observability

**Error Tracking:**
- Rollbar (`rollbar` 1.3.0) - integrated as Django middleware (`rollbar.contrib.django.middleware.RollbarNotifierMiddleware`) and initialized in all settings files
- Disabled for local/test environments (`ROLLBAR['enabled'] = False` when `APP_ENV == 'local'` or running tests)

**Logging:**
- Python standard `logging` module throughout; loggers named per module (e.g., `log = logging.getLogger(__name__)`)
- Celery log handler configured in `reopt_api/celery.py` (`setup_loggers` signal)
- Log format includes filename, function name, and line number

---

*Integration audit: 2026-04-15*
