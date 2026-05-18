# Codex Session Handoff

Last updated: 2026-05-18

## Current State

- Repository: `C:\Users\kongn\Pictures\CodeProject\Reopt API\REopt_API`
- Branch: `master`
- Remote: `origin` -> `https://github.com/Kongnh/Reopt-API.git`
- Local branch was 2 commits ahead of `origin/master` before adding this handoff work.
- Local Python environment is not ready: `python manage.py check` failed because `django` is not installed.
- Docker is the recommended path for this repository.

## Active Product Direction

Use `roadmap.md` as the implementation source of truth.

Next recommended product task:

1. Implement Phase 1 EVN tariff builder as a standalone Python module.
2. Add `reoptjl/src/vietnam/__init__.py`.
3. Add `reoptjl/src/vietnam/evn_rates.py`.
4. Add `reoptjl/src/vietnam/evn_tariff.py`.
5. Add `reoptjl/test/test_vietnam_tariff.py`.
6. Verify 8760 rate generation, Sunday no-peak behavior, voltage-level rates, and two-component pilot demand charges.
7. Only after unit tests pass, wire an example job payload that uses `ElectricTariff.tou_energy_rates_per_kwh` and `monthly_demand_rates`.

## Todo

- [ ] Start Docker stack with `docker-compose up -d`.
- [ ] Verify app health with a Django check inside the container.
- [ ] Implement Phase 1 EVN tariff builder.
- [ ] Add focused tariff unit tests.
- [ ] Add an example Vietnam job submission script after the tariff builder is stable.
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

- Converted the Claude-oriented repo guidance into Codex-compatible `AGENTS.md`.
- Added this persistent handoff file so future Codex sessions can resume from the same context.
- No application code was changed in this session.
