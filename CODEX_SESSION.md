# Codex Session Handoff

Last updated: 2026-05-22

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Local branch is 3 commits ahead of `origin/master`.
- Latest commit: `e47c94ec Split session notes into dedicated handoff file`.
- Local Python environment is not ready: `python manage.py check` failed because `django` is not installed.
- Docker stack is running for local development.
- Local ignored `keys.py` was created from `keys.py.template` so Django/Celery can import settings.
- Phase 1 Vietnam EVN tariff acceptance gate is complete for the example industrial load:
  - `current` run UUID `0ee531dc-625f-416f-a1dc-44e1671572d4`, status `optimal`, REopt BAU bill `345975.02`, manual bill `345975.02`, error `0.0%`.
  - `decision_963` run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d`, status `optimal`, REopt BAU bill `345975.02`, manual bill `345975.02`, error `0.0%`.
- Detailed chronological session notes now live in `SESSION_NOTES.md`.

## Active Product Direction

Use `roadmap.md` as the implementation source of truth.

Next recommended product task:

1. Begin Phase 2 Vietnam pro forma in a separate `proforma_vietnam/` module.
2. Start with focused unit tests for Vietnam CIT holiday/reduced-rate logic and straight-line depreciation.
3. Add a reusable end-to-end tariff acceptance script only if repeated manual acceptance checks become necessary.

## Todo

- [x] Start Docker stack with `docker-compose up -d`.
- [x] Verify app health with a Django check inside the container.
- [x] Implement Phase 1 EVN tariff builder.
- [x] Add focused tariff unit tests.
- [x] Add an example Vietnam job submission script after the tariff builder is stable.
- [x] Run end-to-end Vietnam job submissions using both `tou_schedule="current"` and `tou_schedule="decision_963"`.
- [x] Compare REopt baseline annual electricity cost against manual EVN tariff calculations for both TOU structures.
- [ ] Begin Phase 2 Vietnam pro forma in `proforma_vietnam/`.
- [ ] Defer DPPA settlement, loss factors, and Julia changes until Phase 3 or an explicit roadmap change.

## Session Close Procedure

Before ending a future working session:

1. Update this file's `Last updated` date.
2. Summarize files changed and why.
3. Record tests or checks run, including failures.
4. Update the todo list so completed work is checked off.
5. Add the current commit hash if a commit was made.
6. Update `SESSION_NOTES.md` with detailed notes needed to preserve context beyond this concise handoff.
7. Record any blockers or assumptions needed to resume cleanly.
