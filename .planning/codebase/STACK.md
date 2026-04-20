# Technology Stack

**Analysis Date:** 2026-04-15

## Languages & Runtimes

**Primary:**
- Python 3.12 - Main application language (Django API, Celery workers, all business logic)
- Julia - Optimization engine (REopt.jl solver, runs as a separate microservice on port 8081)

**Secondary:**
- Ruby - Deployment tooling only (Capistrano deploy scripts in `Gemfile`, `Capfile`, `config/deploy/`)

## Frameworks

**Core:**
- Django 4.2.26 - Web framework; configured in `reopt_api/dev_settings.py`, `reopt_api/production_settings.py`, `reopt_api/staging_settings.py`
- django-tastypie 0.15.1 - REST API framework; all API resources extend `ModelResource` from tastypie (see `reo/api.py`, `reoptjl/api.py`, `ghpghx/resources.py`)

**Task Queue:**
- Celery 5.5.3 - Async task worker; configured in `reopt_api/celery.py`; uses Redis as broker; registered tasks in `reo/api.py`, `reo/scenario.py`, `reo/process_results.py`, `reoptjl/api.py`, `reoptjl/src/run_jump_model.py`, `futurecosts/tasks.py`

**WSGI:**
- Gunicorn 23.0.0 - Production WSGI server; config at `reopt_api/gunicorn.conf.py`; invoked via `bin/server`

## Key Libraries

**Scientific / Optimization:**
- numpy 1.26.0 - Numerical arrays
- scipy 1.16.1 - Scientific computing
- pandas 2.3.2 - Time series and data frames
- numpy-financial 1.0.0 - Financial calculations (NPV, IRR)
- coolprop 7.0.0 - Thermodynamic properties (used by GHP module)

**Geospatial:**
- geopandas 1.1.1 - Geospatial data processing (`reo/src/emissions_calculator.py`)
- shapely 2.1.1 - Geometric operations
- pyproj 3.7.2 - Coordinate reference system transformations
- fiona 1.10.1 - Vector file I/O
- pyogrio 0.11.1 - Fast geospatial I/O

**HDF5 / Wind Data:**
- h5pyd 0.18.0 - HSDS (HDF in the Cloud) client for NREL Wind Toolkit data access (`reo/src/wind_resource.py`)
- h5py 3.14.0 - Local HDF5 file access
- tables 3.10.2 - PyTables / HDF5
- blosc2 3.7.2 - Compression for HDF5
- deepdish 0.3.7 - HDF5 convenience wrapper

**Excel / Reporting:**
- openpyxl 3.1.5 - Excel file generation (proforma reports, `proforma/proforma_generator.py`)
- xlsxwriter 3.2.5 - Excel writing
- xlrd 2.0.2 - Excel reading

**HTTP / API Clients:**
- requests 2.32.5 - HTTP client (PVWatts, URDB, wind resource calls)
- google-api-python-client 2.181.0 + google-auth 2.40.3 - Google API access
- azure-core 1.35.0 + msrest 0.7.1 + msrestazure 0.6.4 - Azure SDK

**SAM SDK (Solar/Wind simulation):**
- `reo/src/sscapi.py` - Python bindings to NREL SAM Simulation Core (SSC); native libs `reo/src/ssc.so`, `reo/src/ssc.dll`, `reo/src/ssc.dylib`

**Data / Serialization:**
- jsonschema 4.25.1 - Input validation
- PyYAML 6.0.2 - YAML parsing
- lxml 6.0.1 - XML parsing
- beautifulsoup4 4.13.5 - HTML/XML parsing

**Security / Auth:**
- PyJWT 2.10.1 - JWT token handling
- cryptography 45.0.7 - Cryptographic operations

**Monitoring:**
- rollbar 1.3.0 - Error tracking (configured in all settings files as `ROLLBAR`)

**Database ORM:**
- psycopg2 2.9.10 - PostgreSQL adapter
- SQLAlchemy 2.0.43 - SQL toolkit (used alongside Django ORM in places)
- django-picklefield 3.3 - Pickle-serialized fields on Django models
- django_celery_results 2.6.0 - Stores Celery task results in the Django DB

## Package Management

**Python:**
- `pip` with pinned `requirements.txt` (163 packages, all pinned to exact versions)
- No `pyproject.toml` or `Pipfile`; plain `requirements.txt` at project root
- Dockerfile installs via `pip install -r requirements.txt`
- Optional submodule: `EVI-EnLitePy` (installed as editable package if the git submodule is present)

**Julia:**
- Standard Julia package manager (`Pkg`) via `julia_src/Project.toml` and `julia_src/Manifest.toml`
- Key Julia packages: `REopt` (NREL optimization library), `JuMP` (algebraic modeling), `HiGHS` (open-source solver), `Cbc` (open-source solver), `SCIP` (open-source solver), `Xpress` (commercial solver, optional), `GhpGhx`, `HTTP`, `JSON`

**Ruby:**
- Bundler with `Gemfile` / `Gemfile.lock`
- Only used for deployment tooling (Capistrano); not part of the runtime

## Build & Deployment

**Containerization:**
- Docker; two images built:
  - `reopt-api` (Python/Django) from `Dockerfile` based on `reopt/py312`
  - `julia-api` from `julia_src/Dockerfile`
- `docker-compose.yml` - Full stack: `redis`, `db` (postgres), `celery`, `django`, `julia` services
- `docker-compose.nojulia.yml` - Stack without the Julia container (Julia runs on host)
- `docker-compose.nginx.yml` - Variant with nginx reverse proxy

**CI/CD:**
- Jenkins (`Jenkinsfile`, `Jenkinsfile-deploy`, `Jenkinsfile-deploy-c110p`, etc.)
- Pipeline stages: build Docker image, lint Helm chart, deploy to development/staging/production
- Uses `werf` (GitOps tool) for Kubernetes deployments (`werf.yaml`, `werf-giterminism.yaml`)
- Images pushed to AWS ECR (`ecr:us-east-2:aws-nrel-tada-ci`)
- Deploys to NREL Kubernetes cluster (`kubeconfig-nrel-reopt-prod4`, `kubeconfig-nrel-reopt-prod5`)

**Process Management:**
- `Procfile` - `web` and `worker` processes via `foreman` / `honcho`
- `bin/server` - Gunicorn startup script
- `bin/worker` - Celery worker startup script
- `bin/wait-for-it.bash` - Service readiness check

**Traditional Deploy (legacy):**
- Capistrano (`Capfile`, `config/deploy.rb`, `config/deploy/`) for SSH-based deployment
- Capistrano plugins from NREL's internal TADA GitHub: `captastic`, `captastic-nginx`, `captastic-foreman`

**Environments:**
- Settings modules for `local`, `development`, `staging`, `production`, `internal_c110p`
- Selected at runtime via `APP_ENV` environment variable
- `keys.py` (from `keys.py.template`) holds all secrets; imported by settings modules

---

*Stack analysis: 2026-04-15*
