# Code Conventions

**Analysis Date:** 2026-04-15

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `process_results.py`, `validators.py`, `nested_inputs.py`)
- Test files: `test_<feature>.py` (e.g., `test_chp.py`, `test_emissions.py`, `test_job_endpoint.py`)
- JSON fixture files: `<FeatureName>POST.json` or descriptive `<feature>_post.json` (e.g., `nestedPOST.json`, `pv_batt_emissions.json`)

**Classes:**
- Django model classes: `PascalCase` with descriptive suffixes — `Inputs` or `Outputs` suffix for API data models (e.g., `PVInputs`, `ElectricStorageOutputs`, `FinancialInputs`)
- Test classes: `PascalCase` with `Test` suffix or `Tests` suffix (e.g., `CHPTest`, `InputValidatorTests`, `ERPTests`)
- Non-model utility classes: `PascalCase` (e.g., `URDB_RateValidator`, `EmissionsCalculator`)
- Base/mixin classes: `BaseModel`, `ResourceTestCaseMixin`

**Functions and Methods:**
- All functions and methods: `snake_case` (e.g., `check_common_outputs`, `make_error_resp`, `get_response`, `log_and_raise_error`)
- Test methods: always prefixed with `test_` (e.g., `test_chp_sizing_monolith_1pct`, `test_pv_battery_and_emissions_defaults_from_julia`)
- Helper setup methods in tests: `setUp`, `setUpClass` (Django/unittest convention)

**Variables:**
- Local variables: `snake_case` (e.g., `run_uuid`, `nested_data`, `d_expected`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_BIG_NUMBER`, `MAX_INCENTIVE`, `MAX_YEARS`, `MMBTU_TO_KWH`, `TONHOUR_TO_KWHT`)
- Module-level logger: always `log = logging.getLogger(__name__)`

**API / JSON Keys:**
- REopt v1 (legacy `reo`): `PascalCase` for top-level objects (e.g., `"Scenario"`, `"Site"`, `"ElectricTariff"`) and `snake_case` for field names (e.g., `"annual_kwh"`, `"doe_reference_name"`)
- REopt v3 (`reoptjl`): consistent `PascalCase` for all top-level resource keys matching Django model names (e.g., `"Financial"`, `"PV"`, `"ElectricStorage"`)
- Unit suffixes embedded in field names (e.g., `size_kw`, `lcc_bau`, `emissions_factor_lb_CO2_per_kwh`, `blended_monthly_rates_us_dollars_per_kwh`)

## Code Style

**General:**
- Python 3.12 (see `requirements.txt` comment)
- No enforced auto-formatter (no `black` or `isort` config files found). `autopep8==2.3.2` and `pycodestyle==2.14.0` are in `requirements.txt` but no config files (no `.flake8`, `setup.cfg`, `pyproject.toml`) were found.
- Recommended IDE is PyCharm (noted in `CONTRIBUTING.md`)
- No enforced line-length limit detected

**Imports:**
- Standard library imports first, then third-party, then local — loosely followed but not strictly enforced
- Local imports use relative imports within a package: `from .urdb_logger import log_urdb_errors`
- Cross-package imports use full package path: `from reo.utilities import ...`, `from reoptjl.models import ...`

**License Header:**
- Every Python source file begins with:
  ```python
  # REopt®, Copyright (c) Alliance for Sustainable Energy, LLC. See also https://github.com/NREL/REopt_API/blob/master/LICENSE.
  ```

**Logging:**
- All modules use Python `logging` module (not `print`)
- Module-level logger instantiation: `log = logging.getLogger(__name__)`
- Tests globally disable logging: `logging.disable(logging.CRITICAL)`
- Usage: `log.error(...)`, `log.warning(...)`, etc.

**Error Handling:**
- Views and API endpoints wrap logic in try/except and return `JsonResponse` with `{"messages": {"error": msg}, "status": "error"}`
- Custom exceptions in `reo/exceptions.py` (e.g., `UnexpectedError`)
- f-strings used for error message formatting: `f"Error in {task_name}: {exc_value}"`

**Django Model Field Conventions (per inline guidance in `reoptjl/models.py`):**
- Required fields listed first in each model
- `blank=True` added only when blank is explicitly allowed
- `TextField` and `CharField` must NOT have `null=True`
- Output models need `null=True, blank=True`
- `help_text` should use square brackets for units: `[dollars per kWh]`

## Patterns & Idioms

**Django + Tastypie:**
- API resources defined in `api.py` per Django app using `tastypie` (legacy v1 in `reo/api.py`, v3 in `reoptjl/api.py`)
- URL routing in `urls.py` and `urls_v2.py` per app
- Views are plain Django view functions returning `JsonResponse` or `HttpResponse`

**Model-as-Input-Schema:**
- Input and output schemas are defined as Django ORM models (in `reoptjl/models.py`), not as separate serializers
- `BaseModel` mixin provides `.dict`, `.create()`, and `.info_dict()` methods reused across all models
- Model `help_text` field attribute drives the `/job/inputs` help endpoint

**Celery Task Pattern:**
- Optimization jobs are submitted asynchronously via Celery workers
- Scenario orchestration in `reo/scenario.py`; result processing in `reo/process_results.py` and `reoptjl/src/process_results.py`

**Test Data via JSON Fixtures:**
- Tests load JSON POST bodies from `tests/posts/` directories (e.g., `reo/tests/posts/nestedPOST.json`, `reoptjl/test/posts/pv_batt_emissions.json`)
- `copy.deepcopy()` used when mutating shared fixture data across test cases

**Numeric Tolerance:**
- `REopt_tol = 1e-2` (1%) class attribute defined on test classes for `check_common_outputs` comparisons
- `assertAlmostEqual(..., places=N)` or `assertAlmostEqual(..., delta=N)` for floating-point numerical results

## Linting & Formatting

**Installed Tools (via `requirements.txt`):**
- `autopep8==2.3.2` — PEP 8 auto-formatter (available but no config found)
- `pycodestyle==2.14.0` — PEP 8 style checker
- `bandit==1.8.6` — security linter

**Not Configured:**
- No `black`, `isort`, `flake8`, or `pylint`
- No `setup.cfg`, `pyproject.toml`, or `.flake8` config files at project root
- No pre-commit hooks detected

**Practical implication:** Style is not automatically enforced. CONTRIBUTING.md recommends PyCharm for consistent formatting.

## Documentation

**Docstrings:**
- Triple-quoted docstrings used on functions and classes when present
- No enforced docstring standard (no NumPy, Google, or Sphinx style consistently applied)
- Format when used:
  ```python
  def annuity(analysis_period, rate_escalation, rate_discount):
      """
          this formulation assumes cost growth in first period
          i.e. it is a geometric sum of (1+rate_escalation)^n / (1+rate_discount)^n
          for n = 1,..., analysis_period
      """
  ```
- Some functions use `:param name:` and `:return:` Sphinx-style tags:
  ```python
  def check_common_outputs(Test, d_calculated, d_expected):
      """
      :param Test: test class instance
      :param d_calculated: dict of values from API (flat format)
      :return: None
      """
  ```
- Test methods include descriptive docstrings explaining validation intent

**README / Changelog:**
- `README.md` at project root
- `CHANGELOG.md` — actively maintained, updated on PRs
- `CONTRIBUTING.md` — describes PR process, recommended IDE, git commit style
- GitHub issue and PR templates: `.github/ISSUE_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE.md`

**Git Commit Messages (from `CONTRIBUTING.md`):**
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood
- Limit first line to 72 characters
- Reference issues/PRs after the first line
