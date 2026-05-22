# Codex Session Handoff

Last updated: 2026-05-22

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Local branch was 2 commits ahead of `origin/master` before adding this handoff work.
- Local Python environment is not ready: `python manage.py check` failed because `django` is not installed.
- Docker stack is running for local development.
- Local ignored `keys.py` was created from `keys.py.template` so Django/Celery can import settings.
- Detailed chronological session notes now live in `SESSION_NOTES.md`.

## Active Product Direction

Use `roadmap.md` as the implementation source of truth.

Next recommended product task:

1. Inspect optimizer results and compare baseline annual electricity cost against manual EVN tariff calculations for both TOU structures.
2. Add a reusable end-to-end test script if repeated acceptance checks are needed.
3. Begin Phase 2 Vietnam pro forma only after the Phase 1 end-to-end acceptance check is complete.

## Todo

- [x] Start Docker stack with `docker-compose up -d`.
- [x] Verify app health with a Django check inside the container.
- [x] Implement Phase 1 EVN tariff builder.
- [x] Add focused tariff unit tests.
- [x] Add an example Vietnam job submission script after the tariff builder is stable.
- [x] Run end-to-end Vietnam job submissions using both `tou_schedule="current"` and `tou_schedule="decision_963"`.
- [ ] Defer Vietnam pro forma until tariff builder acceptance criteria are met.
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
