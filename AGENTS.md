# AGENTS.md

This file provides repository instructions for Codex and other agentic coding tools.
It is adapted from `CLAUDE.md`; keep both files aligned when changing project guidance.

## Operating Rules

These rules apply to all work in this repository.

### Think Before Coding

- State assumptions explicitly.
- If multiple interpretations exist, surface them before editing.
- Prefer the simpler approach when it solves the request.
- If the request is unclear enough that a wrong assumption would be expensive, ask before implementing.

### Simplicity First

- Write the minimum code that solves the requested problem.
- Do not add speculative features, flexibility, abstractions, or error handling.
- Avoid single-use abstractions.
- If a solution grows larger than necessary, simplify before finalizing.

### Surgical Changes

- Touch only files required by the current task.
- Do not refactor unrelated code.
- Match existing local style, even when it is not the style you would choose from scratch.
- Mention unrelated issues instead of fixing them opportunistically.
- Every changed line should trace directly to the user's request.

### Goal-Driven Execution

- Define success criteria for non-trivial tasks.
- For bug fixes, reproduce the bug with a test or focused command before fixing when feasible.
- For validation changes, add invalid-input tests before implementation when feasible.
- Verify the change before claiming it is complete.

## Session Continuity

- At the start of a new session, read `CODEX_SESSION.md`, `roadmap.md`, and this file before choosing next work.
- Treat `CODEX_SESSION.md` as the durable handoff file for current status, active todo items, blockers, and verification notes.
- At the end of a working session, update `CODEX_SESSION.md` with:
  - what changed,
  - current git status or commit hash,
  - tests or checks run,
  - remaining todo items,
  - any blockers or assumptions.
- Keep `CODEX_SESSION.md` concise and current. Do not let stale completed work remain in the active todo list.

## Project Overview

REopt API is a Django REST API for distributed energy resource optimization. It wraps a Julia-based MILP solver through HTTP and exposes optimization results through Tastypie endpoints.

The active development goal in this checkout is Vietnam DPPA and ESCO feasibility analysis.
For Vietnam domain context, read `vietnam_market_context.md`.
For the implementation roadmap, read `roadmap.md`.

## Architecture

```text
Django (Tastypie REST) -> Celery Worker -> Julia HTTP Server (JuMP/HiGHS MILP)
                                |
                          PostgreSQL (results) + Redis (broker)
```

- `reoptjl/` - Active V3 API. Put new API work here.
- `reo/` - Deprecated V1/V2. Do not modify unless explicitly requested.
- `julia_src/` - Julia optimization model and HTTP server.
- `proforma/` - Existing US-centric financial pro forma reports.
- `resilience_stats/` - Outage simulation and resilience metrics.
- `reopt_api/` - Django settings, URL routing, WSGI.

## Key Files

| File | Purpose |
| --- | --- |
| `reoptjl/models.py` | Django ORM models for V3 inputs and outputs. |
| `reoptjl/validators.py` | Input validation before sending jobs to Julia. |
| `reoptjl/src/run_jump_model.py` | Celery task that calls Julia and stores results. |
| `reoptjl/src/process_results.py` | Parses Julia output into Django model fields. |
| `julia_src/http.jl` | Julia HTTP server entry point. |
| `reopt_api/dev_settings.py` | Local Django, DB, Celery, and solver settings. |

## Commands

Docker is the preferred development path.

```bash
docker-compose up -d
docker-compose logs -f django
docker-compose logs -f celery
```

Local Django commands, when dependencies are installed:

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Tests:

```bash
python manage.py test reoptjl
python manage.py test proforma
```

Julia server standalone:

```bash
cd julia_src && julia --project http.jl
```

## Optimization Flow

1. `POST /v3/job/` validates inputs in `reoptjl/validators.py` and queues a Celery task.
2. Celery posts the validated JSON payload to the Julia HTTP service.
3. Julia builds and solves the MILP.
4. Python parses Julia results in `reoptjl/src/process_results.py` and saves them to PostgreSQL.
5. `GET /v3/job/<uuid>/results` returns stored inputs, outputs, and messages.

## Vietnam Adaptation Notes

Current roadmap priority is Phase 1: EVN tariff builder.

- Build the Vietnam tariff layer in Python under `reoptjl/src/vietnam/`.
- Use existing `ElectricTariffInputs.tou_energy_rates_per_kwh` for 8760 hourly energy rates.
- Use existing `ElectricTariffInputs.monthly_demand_rates` for two-component pilot capacity charges.
- Do not change Django models or Julia for Phase 1 unless the roadmap is explicitly changed.
- Keep DPPA settlement logic, loss factors, and virtual DPPA eligibility out of Phase 1.

Phase 2 is a separate `proforma_vietnam/` module. Do not modify the existing US `proforma/` path unless explicitly required.

## API Versions

- `v3` and `stable` are active.
- `v1` and `v2` are deprecated legacy paths. Avoid changes there.
