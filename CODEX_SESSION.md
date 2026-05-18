# Codex Session Handoff

Last updated: 2026-05-18

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Local branch was 2 commits ahead of `origin/master` before adding this handoff work.
- Local Python environment is not ready: `python manage.py check` failed because `django` is not installed.
- Docker stack is running for local development.
- Local ignored `keys.py` was created from `keys.py.template` so Django/Celery can import settings.

## Active Product Direction

Use `roadmap.md` as the implementation source of truth.

Next recommended product task:

1. Run end-to-end Vietnam job submissions using both `tou_schedule="current"` and `tou_schedule="decision_963"`.
2. Inspect optimizer results and compare baseline annual electricity cost against manual EVN tariff calculations for both TOU structures.
3. Begin Phase 2 Vietnam pro forma only after the Phase 1 end-to-end acceptance check is complete.

## Todo

- [x] Start Docker stack with `docker-compose up -d`.
- [x] Verify app health with a Django check inside the container.
- [x] Implement Phase 1 EVN tariff builder.
- [x] Add focused tariff unit tests.
- [x] Add an example Vietnam job submission script after the tariff builder is stable.
- [ ] Defer Vietnam pro forma until tariff builder acceptance criteria are met.
- [ ] Defer DPPA settlement, loss factors, and Julia changes until Phase 3 or an explicit roadmap change.

## Session Close Procedure

Before ending a future working session:

1. Update this file's `Last updated` date.
2. Summarize files changed and why.
3. Record tests or checks run, including failures.
4. Update the todo list so completed work is checked off.
5. Add the current commit hash if a commit was made.
6. Record any blockers or assumptions needed to resume cleanly.

## Latest Session Notes

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
- Note: `docker-compose up -d django` exits after migrations because `/opt/reopt/bin/wait-for-it.bash` cannot execute in this checkout; use an overridden Django command for tests until that compose issue is fixed.
- Current git status: untracked `reoptjl/src/vietnam/` and `reoptjl/test/test_vietnam_tariff.py`; no commit made.
