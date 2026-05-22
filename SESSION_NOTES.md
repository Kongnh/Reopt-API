# Session Notes

Use this file for detailed working-session notes that would make `CODEX_SESSION.md` too long.
At the end of every working session, append or update the latest section here with files changed, checks run, blockers, assumptions, and any context needed to resume.

## 2026-05-22 - Session Notes Split

- Moved the detailed latest session notes out of `CODEX_SESSION.md` into this dedicated file.
- Updated `AGENTS.md` so future agents read this file when context is needed and update it during session closeout.
- Updated `CODEX_SESSION.md` session-close guidance to point detailed notes here.

## 2026-05-18 - Latest Session Notes

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
- Fixed `example_submit.py` to include `ElectricLoad.year=2025`; Julia rejects `loads_kw` payloads without `ElectricLoad.year`.
- Verification run: local Docker E2E `current` schedule submitted to `POST /v3/job/`, run UUID `a75db5cb-f345-40b9-a878-d88d57d3f930`, completed with status `optimal`.
- Verification run: local Docker E2E `decision_963` schedule submitted to `POST /v3/job/`, run UUID `18def5ef-6c6b-4f37-84f0-8967ecd0fc6d`, completed with status `optimal`.
- Verification run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_tariff -v 2` passed after the example payload fix.
- Updated local API credentials in ignored `keys.py` and tracked `julia_src/.env`; do not commit a real key unless this repository is kept private and that is intentional.
- Switched active developer API URLs from `developer.nrel.gov` to `developer.nlr.gov`; only the historical `reoptjl/migrations/0001_initial.py` migration still has the old string.
- Updated support email text from `reopt@nrel.gov` to `reopt@nlr.gov` in active/deprecated API response code.
- Simplified `docker-compose.yml` so `docker-compose up -d django` no longer calls the CRLF-sensitive `wait-for-it.bash` script.
- Added migration `reoptjl/migrations/0114_alter_apimeta_job_type.py` for the `APIMeta.job_type` default change to `developer.nlr.gov`; applied locally with `docker-compose run --rm --entrypoint python django manage.py migrate`.
- Verification run: `docker-compose up -d django` starts Django and `GET http://localhost:8000/v3/job/inputs/` returned HTTP 200.
- Verification run: Python container reports both local developer keys configured and Julia container sees `NREL_DEVELOPER_EMAIL`.
- Current git status: modified `CODEX_SESSION.md`, `docker-compose.yml`, `futurecosts/views.py`, `julia_src/.env`, `julia_src/http.jl`, `keys.py.template`, `reo/api.py`, `reo/exceptions.py`, `reo/src/pvwatts.py`, `reo/src/wind_resource.py`, `reo/validators.py`, `reo/views.py`, `reoptjl/api.py`, `reoptjl/models.py`, `reoptjl/src/vietnam/example_submit.py`, `reoptjl/test/test_vietnam_tariff.py`, `reoptjl/views.py`; untracked `reoptjl/migrations/0114_alter_apimeta_job_type.py` and `Sample Load Profile/`; no commit made.
