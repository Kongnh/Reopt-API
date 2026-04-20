# Testing Approach

**Analysis Date:** 2026-04-15

## Test Framework

**Runner:**
- Django's built-in test runner (`manage.py test`), which wraps `unittest`
- No `pytest`, `pytest.ini`, or `vitest` configuration found

**Base Test Classes:**
- `django.test.TestCase` — standard Django test case; wraps each test in a transaction and flushes DB between tests
- `django.test.TransactionTestCase` — used when DB queries mid-test would cause `TransactionManagementError` (e.g., `reoptjl/test/test_job_endpoint.py`)
- `tastypie.test.ResourceTestCaseMixin` — mixed in alongside `TestCase` to provide `self.api_client` for HTTP endpoint testing

**Assertion Library:**
- Standard `unittest` assertions (`assertEqual`, `assertAlmostEqual`, `assertIn`, `assertTrue`, `assertIsNotNone`)
- Tastypie-provided HTTP assertions: `assertHttpCreated`
- Custom shared helper: `reo.utilities.check_common_outputs` for bulk REopt output validation

**Run Commands:**
```bash
# Run the active v3 test suite (used in CI)
docker exec reopt_api-celery-1 python manage.py test reoptjl.test -v 2 --no-input

# Run v1 (legacy) reo tests
docker exec reopt_api-celery-1 python manage.py test reo.tests -v 2 --no-input

# Run resilience stats tests
docker exec reopt_api-celery-1 python manage.py test resilience_stats.tests -v 2 --no-input

# Run GHP tests
docker exec reopt_api-celery-1 python manage.py test ghpghx.tests -v 2 --no-input

# Run all tests in a specific file
docker exec reopt_api-celery-1 python manage.py test reoptjl.test.test_job_endpoint -v 2 --no-input
```

**Note:** Tests run inside Docker containers (`reopt_api-celery-1`). The Julia optimization engine container must be running and ready before tests execute (CI waits 150 seconds after `docker compose up`).

## Test Organization

**Location pattern:** Each Django app has its own `tests/` (or `test/`) subdirectory.

```
REopt_API/
├── reo/
│   └── tests/
│       ├── __init__.py
│       ├── posts/               # JSON POST fixtures for v1 tests
│       │   ├── nestedPOST.json
│       │   ├── test_chp_sizing_POST.json
│       │   └── ...
│       ├── missing_rate.json    # URDB edge-case fixtures
│       ├── missing_schedule.json
│       ├── test_chp.py
│       ├── test_emissions.py
│       ├── test_validator.py
│       └── test_*.py            # ~27 test files
├── reoptjl/
│   └── test/
│       ├── __init__.py
│       ├── posts/               # JSON POST fixtures for v3 tests
│       │   ├── pv_batt_emissions.json
│       │   ├── outage.json
│       │   └── ...
│       ├── test_job_endpoint.py
│       ├── test_http_endpoints.py
│       └── test_validator.py
├── resilience_stats/
│   └── tests/
│       ├── __init__.py
│       ├── ERP_*.json           # ERP simulation fixtures
│       ├── test_erp.py
│       ├── test_new_post_endpoint.py
│       └── test_resilience_stats.py
├── ghpghx/
│   └── tests/
│       ├── posts/
│       └── test_ghpghx.py
└── load_builder/
    └── tests/
        └── test_load_builder.py
```

**Naming:**
- Test files: `test_<feature>.py`
- Test classes: `<Feature>Test` or `<Feature>Tests` (e.g., `CHPTest`, `InputValidatorTests`)
- Test methods: `test_<what_is_being_tested>` (e.g., `test_chp_sizing_monolith_1pct`, `test_pv_battery_and_emissions_defaults_from_julia`)

## Test Types

**Integration / End-to-End (dominant pattern):**
- The vast majority of tests are full-stack integration tests
- They POST a JSON scenario to the Django API (`/v3/job/`, `/v1/job/`) and then GET results from the results endpoint
- Validate actual optimization outputs (financial, sizing, emissions values) against expected values with numerical tolerance
- Examples: `reoptjl/test/test_job_endpoint.py`, `reo/tests/test_chp.py`, `reo/tests/test_emissions.py`

**HTTP / Endpoint Tests:**
- Test that external Julia HTTP endpoints (e.g., `/chp_defaults`) respond correctly and match Django view forwarding
- Located in `reoptjl/test/test_http_endpoints.py` and `resilience_stats/tests/test_erp.py`

**Validator / Unit Tests:**
- Test input validation logic in isolation without calling the optimization solver
- Use `ValidateNestedInput` (v1) or `InputValidator` (v3) classes directly
- Located in `reo/tests/test_validator.py` and `reoptjl/test/test_validator.py`
- These are the only true unit tests in the suite

**No E2E browser tests detected.** No Selenium, Playwright, or similar tooling found.

## How to Run Tests

**Prerequisites:**
1. Docker and Docker Compose installed
2. `keys.py` created from `keys.py.template` (requires `NREL_DEV_API_KEY`)
3. All containers running: `docker compose up -d`
4. Wait ~150 seconds for Julia optimization service to be ready

**CI command (from `.github/workflows/`):**
```bash
# Used for both push and pull_request workflows
docker exec reopt_api-celery-1 python manage.py test reoptjl.test -v 2 --no-input
```

**Run by module:**
```bash
# v3 stable tests (CI-tested)
docker exec reopt_api-celery-1 python manage.py test reoptjl.test -v 2 --no-input

# v1 legacy tests (not in CI workflows)
docker exec reopt_api-celery-1 python manage.py test reo.tests -v 2 --no-input

# Single test method
docker exec reopt_api-celery-1 python manage.py test reoptjl.test.test_job_endpoint.TestJobEndpoint.test_pv_battery_and_emissions_defaults_from_julia -v 2 --no-input
```

## Coverage & Quality Gates

**CI Gates:**
- Pull requests to `master` or `develop` trigger `.github/workflows/pull_request_tests.yml`
- All pushes (except README/CHANGELOG changes) trigger `.github/workflows/push_tests.yml`
- Both workflows run only `reoptjl.test` (v3 suite)
- `reo.tests` (v1) and other module tests are NOT run in CI — they must be run manually

**Coverage tooling:**
- No `pytest-cov`, `coverage.py` configuration, or coverage thresholds detected
- Coverage is not measured or enforced automatically

**Test count summary (approximate):**
- `reo/tests/`: ~67 test methods across ~27 files
- `reoptjl/test/`: ~33 test methods across 3 files
- `resilience_stats/tests/`: ~12 test methods across 3 files
- `ghpghx/tests/`: ~1 test method
- `load_builder/tests/`: present but not counted

## Fixtures & Mocking

**JSON POST Fixtures:**
- Primary mechanism for test data is loading JSON files from `tests/posts/` directories
- Pattern used throughout:
  ```python
  post_file = os.path.join('reoptjl', 'test', 'posts', 'pv_batt_emissions.json')
  post = json.load(open(post_file, 'r'))
  ```
- `copy.deepcopy()` is used when a test modifies a shared fixture to avoid cross-test contamination:
  ```python
  post = copy.deepcopy(self.post)
  post['ElectricLoad']['loads_kw'] = list(range(length))
  ```

**setUp Pattern:**
- Most test classes use `setUp` (instance method) rather than `setUpClass` (class method)
- `setUp` initializes URL strings and loads fixture files:
  ```python
  def setUp(self):
      super(ERPTests, self).setUp()
      self.reopt_base_erp = '/v3/erp/'
      self.post_sim_only = os.path.join('resilience_stats', 'tests', 'ERP_sim_only_post.json')
  ```
- `setUpClass` used in `reo/tests/test_reopt_url.py` to load shared data once per class

**API Client:**
- `self.api_client` provided by `ResourceTestCaseMixin` for posting/getting to Django URLs:
  ```python
  resp = self.api_client.post('/v3/job/', format='json', data=scenario)
  r = json.loads(resp.content)
  run_uuid = r.get('run_uuid')
  resp = self.api_client.get(f'/v3/job/{run_uuid}/results')
  ```

**Mocking:**
- No `unittest.mock`, `pytest-mock`, or `MagicMock` usage found
- External services (Julia solver, NREL APIs) are called for real during tests — full live integration testing
- Julia service host is resolved via environment variable: `os.environ.get('JULIA_HOST', "julia")`

**Custom Assertion Helper:**
- `reo.utilities.check_common_outputs(Test, d_calculated, d_expected)` — compares flat output dicts against expected values using `REopt_tol = 1e-2` tolerance
- Used in `reo` legacy tests for bulk output validation:
  ```python
  d_expected = {'lcc': 13476072.0, 'npv': 1231748.579, 'chp_kw': 468.718}
  check_common_outputs(self, c, d_expected)
  ```

**Numerical Tolerance:**
- Class-level constant: `REopt_tol = 1e-2` (1%)
- `assertAlmostEqual` with `places=N` for tight checks, `delta=N` for absolute tolerance:
  ```python
  self.assertAlmostEqual(results["Financial"]["lcc"], 12391786, places=-3)
  self.assertAlmostEqual(results["Outages"]["microgrid_upgrade_capital_cost"], 1974429.4, delta=5000.0)
  self.assertAlmostEqual(results["Financial"]["lcc"], 59865240.0, delta=0.01*results["Financial"]["lcc"])
  ```

---

*Testing analysis: 2026-04-15*
