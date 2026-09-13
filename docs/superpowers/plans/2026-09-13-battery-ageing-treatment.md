# Battery ageing treatment: derate | augment (research line), 2026-09-13

Ruling (user, 2026-09-13 morning): implement all four recommendations of
`docs/superpowers/notes/2026-09-12-fade-aware-sizing-research.md`. This plan
covers recommendation 3; 1 (objective alignment) is ported to `master` and
cherry-picked here, 2 and 4 are documentation and the probe kept as the
sizing check.

## Design

- `technologies.storage.ageing_treatment` in case.json: `"derate"` (default,
  today's behaviour) or `"augment"`. Recorded in assumptions as
  `battery_ageing_treatment`, with `bess_augmentation_price_declination_rate`
  (defaults constant 0.03) beside it, for storage cases only. Travels through
  the report query keys, the sweep map, Thailand's passthrough and the view.
- `augment`: the battery's savings are not derated; the yearly cost of
  topping the capacity up (replica delta-SOH in kWh times the installed
  USD/kWh declining at the rate, nominal, booked in the year the fade
  happens) is an operating cost line `battery_augmentation_cost_*`, expensed
  and tax-deductible, subtracted in net operating revenue and CFADS.
- `derate`: unchanged; the augmentation figure is computed for information
  only (derivation), no row.
- Rows keep `battery_soh_fraction` (physical SOH, both modes) and
  `battery_fade_loss_*` on the derate basis (booked under derate, informational
  under augment). Derivation carries `treatment`,
  `augmentation_cost_by_year_usd`, price and declination.
- Audit sheet: SOH terms in the live formulas only under derate; under
  augment an "Battery augmentation" values row in operating costs and
  EBITDA subtracts it. Battery SOH sheet shows both figures and states which
  is booked.

## Tasks (TDD, each with its test run)

1. defaults + `battery_soh.augmentation_cost_by_year`.
2. builders (Vietnam, Thailand) record the treatment; invalid value refused.
3. esco_pro_forma passes treatment and the augmentation series.
4. cash_flow books the augmentation under `augment`; derate byte-identical.
5. audit_sheets formulas and rows; plain-formula fixture still byte-identical.
6. xlsx_builder Battery SOH sheet: both figures, treatment stated.
7. query plumbing (run_case, sweep map, Thailand passthrough, views).
8. docs: CASE_JSON_INPUT_GUIDE, ESCO_CONTRACT_MODEL_DESIGN, MODEL_AUDIT.
9. records: assumptions regenerated, workbooks rebuilt, Excel tie-out,
   baselines; an `augment` demonstration of Vietnam case_1 under
   `outputs/research/augment/`.
