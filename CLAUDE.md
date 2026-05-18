# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Coding Principles

Behavioral guidelines to reduce common LLM coding mistakes. These apply to all work in this repo.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.**
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.**
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
- Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution
**Define success criteria. Loop until verified.**
- Transform "fix the bug" → "write a test that reproduces it, then make it pass"
- Transform "add validation" → "write tests for invalid inputs, then make them pass"
- For multi-step tasks, state a brief plan with a verify step for each action.
- Clarifying questions come *before* implementation, not after mistakes.

## Project Overview

REopt API is a Django REST API for distributed energy resource (DER) optimization. It wraps a Julia-based MILP solver (JuMP + HiGHS) via HTTP and exposes optimization results through Tastypie endpoints. The primary use case being developed here is feasibility analysis for ESCO investment models under Vietnam's DPPA framework (private wire vs. national grid paths).

For Vietnam-specific domain knowledge (EVN tariffs, DPPA mechanics, loss factors, financial parameters), see [`vietnam_market_context.md`](vietnam_market_context.md).

## Architecture

```
Django (Tastypie REST) → Celery Worker → Julia HTTP Server (JuMP/HiGHS MILP)
                                ↓
                          PostgreSQL (results)  Redis (broker)
```

- **`reoptjl/`** — Active V3 API. All new work goes here.
- **`reo/`** — Deprecated V1/V2 (returns 410). Do not modify.
- **`julia_src/`** — Julia optimization model (`http.jl` server, `reopt_model.jl` MILP).
- **`proforma/`** — Financial pro forma reports (XLSX generation).
- **`resilience_stats/`** — Outage simulation and resilience metrics.
- **`reopt_api/`** — Django settings, URL routing, WSGI.

## Key Files

| File | Purpose |
|------|---------|
| `reoptjl/models.py` | Django ORM models for all V3 inputs/outputs (ElectricTariffInputs, FinancialInputs, etc.) |
| `reoptjl/validators.py` | Input validation before sending to Julia |
| `reoptjl/src/run_jump_model.py` | Celery task: HTTP POST to Julia, store results |
| `reoptjl/src/process_results.py` | Parse Julia output → Django model fields |
| `julia_src/http.jl` | Julia HTTP server entry point |
| `reopt_api/dev_settings.py` | Django settings (DB, Celery, solver config) |

## Commands

### Docker (recommended)
```bash
docker-compose up -d          # Start full stack (Redis, Postgres, Celery, Django, Julia)
docker-compose logs -f django # Tail Django logs
docker-compose logs -f celery # Tail Celery worker logs
```

### Local Django
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Tests
```bash
python manage.py test reoptjl                         # All V3 tests
python manage.py test reoptjl.tests.test_chp          # Single test file
python manage.py test reoptjl.tests.test_chp.CHPTest.test_chp_defaults  # Single test
python manage.py test proforma                        # Pro forma tests
```

### Julia server (standalone)
```bash
cd julia_src && julia --project http.jl
```

## Optimization Flow

1. `POST /v3/job/` → validate inputs (`validators.py`) → enqueue Celery task
2. Celery task → HTTP POST to Julia server with JSON inputs
3. Julia builds & solves MILP (HiGHS by default) → returns JSON results
4. Python parses results (`process_results.py`) → saves to PostgreSQL
5. `GET /v3/job/<uuid>/results` → return stored results

Solver is configurable via `Settings.solver_name` (HiGHS, Cbc, SCIP, Xpress).

## Electric Tariff Model

Tariff inputs live in `ElectricTariffInputs` ([reoptjl/models.py](reoptjl/models.py)). Key fields:
- `urdb_label` — pull rate from NREL URDB
- `blended_annual_energy_rate` / `blended_annual_demand_charge_rate` — simple flat rates
- `tou_energy_rates_per_kwh` — 8760-length time-of-use array
- `monthly_demand_rates`, `monthly_energy_rates` — monthly rate schedules

For Vietnam tariff adaptation, use `tou_energy_rates_per_kwh` and `monthly_demand_rates` to encode EVN tariff tiers; set `urdb_label` to `null`.

## Financial Model

`FinancialInputs` ([reoptjl/models.py](reoptjl/models.py)) key fields:
- `analysis_years`, `offtaker_discount_rate_fraction`, `owner_discount_rate_fraction`
- `om_cost_escalation_rate_fraction`, `elec_cost_escalation_rate_fraction`
- MACRS depreciation schedule fields (US only — **not applicable for Vietnam**)

For ESCO models: `owner_discount_rate_fraction` = ESCO cost of capital; `offtaker_discount_rate_fraction` = offtaker WACC. Third-party ownership is toggled via `third_party_ownership` boolean.

## Vietnam / DPPA Adaptation Notes

New scenario inputs to add for DPPA comparison:
- `dppa_type` — enum: `"private_wire"` | `"grid_connected"`
- `dppa_wheeling_charge_per_kwh` — transmission/wheeling fee for grid-path DPPA
- `esco_fee_structure` — capacity charge or energy charge to offtaker

When adding new input fields: add to `reoptjl/models.py`, `reoptjl/validators.py`, and pass through in `run_jump_model.py` to Julia. Mirror in Julia's input struct if the optimizer needs it; otherwise handle in Python post-processing.

## API Versions

- **v3 / stable**: Active. `stable` URL prefix = long-term support alias for v3.
- **v1 / v2**: Return 410. Do not touch.
