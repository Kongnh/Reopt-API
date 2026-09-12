# Battery replacement switch, SOH curve and fade derating

Date: 2026-09-12. Branch: `battery-soh-fade` (kept independent of master; the
user decides on the merge). Supersedes the year-10 whole-system replacement
of `2026-09-11-replacement-policy-sync-design.md` as the default; that
mechanism stays and becomes a per-case option.

## Rulings (user, 2026-09-12)

1. No scheduled battery replacement inside the 20 year horizon, for both
   countries. Whether to replace, in which year and at what cost becomes a
   per-case choice in `case.json`, recorded in `assumptions.json`.
2. Project life stays 20 years. The PV inverter event (year 11, 10 percent of
   solved PV capex) stays.
3. Battery ageing is carried by a state-of-health (SOH) curve computed from
   the solved dispatch, and the battery's share of the savings is derated by
   that curve every year.
4. The SOH recurrence is REopt.jl v0.57.0's, with the hours-per-time-step
   factor removed (h = 1): the same daily energy gives the same fade whether
   the model runs at 15 minute or hourly resolution.
5. Cycle life default: 8,000 equivalent full cycles to 80 percent SOH, in the
   style of an LFP datasheet. Calendar fade keeps the NREL coefficients.
6. Every workbook with a battery gets a "Battery SOH" sheet with the curve.
7. All cases are re-solved. Memo, deck and artifact are not reissued in this
   task; they are flagged stale.

## Part A: replacement switch

### Policy constants (`proforma_vietnam/defaults/__init__.py`)

```python
PROJECT_YEARS = 20
BESS_REPLACEMENT_ENABLED = False      # ruling 2026-09-12
BESS_REPLACEMENT_YEAR = 10            # used only when a case enables it
BESS_REPLACE_FRACTION_OF_INSTALL = 1.0
PV_INVERTER_REPLACEMENT_YEAR = 11
PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX = 0.10
BESS_CYCLE_LIFE_EFC = 8000            # equivalent full cycles to end of life
BESS_END_OF_LIFE_SOH = 0.80
BESS_CALENDAR_FADE_COEFFICIENT = 1.16e-3   # NREL / REopt.jl v0.57.0 default
BESS_CALENDAR_FADE_EXPONENT = 0.428
```

### case.json

`technologies.storage.replacement` (optional block):

```json
"replacement": {"enabled": true, "year": 10, "fraction_of_install": 1.0}
```

- `enabled` absent or false: no replacement. `year` and
  `fraction_of_install` default to the policy constants when enabled.
- `cost_per_kw` / `cost_per_kwh` (absolute, REopt money units) may replace
  `fraction_of_install`; giving both raises `ValueError`.
- The raw REopt keys `replace_cost_per_kw`, `replace_cost_per_kwh`,
  `replace_cost_constant`, `inverter_replacement_year`,
  `battery_replacement_year`, `cost_constant_replacement_year` are removed
  from `STORAGE_PAYLOAD_KEYS`; a case that still carries any of them raises
  `ValueError` naming the `replacement` block. One way to say it.
- `technologies.storage.cycle_life_efc` (optional number, > 0) overrides
  `BESS_CYCLE_LIFE_EFC`.

Same block for Thailand cases (`outputs/thailand_case/.../case.json`);
Thailand's builder calls the shared helper.

### What the builder sends to REopt

Shared helper `apply_replacement_policy(storage_config, storage_payload)` in
`proforma_vietnam/case_builder.py` (public, imported by Thailand):

- Disabled: `replace_cost_per_kw = replace_cost_per_kwh = 0.0` sent
  explicitly (REopt's own default, but the payload then reads as a decision);
  no replacement years sent.
- Enabled: `replace_cost_per_kw = installed_cost_per_kw × fraction` (or the
  absolute value), same for kWh; `inverter_replacement_year =
  battery_replacement_year = year`. Whole system in one year, as before.
- Only when the case sends a storage system at all.

### assumptions.json record

- `bess_replacement_enabled` (bool) always written when storage is present.
- When enabled: `battery_replacement_year`, `bess_replace_cost_per_kw`,
  `bess_replace_cost_per_kwh` as today. When disabled these keys are absent.
- `bess_cycle_life_efc` written when storage is present (policy or override).
- `pv_inverter_replacement_year`, `pv_inverter_replacement_fraction_of_pv_capex`
  unchanged.

`bess_cycle_life_efc` joins `VIETNAM_REPORT_QUERY_KEYS`, the
`numeric_query_params` map in `reoptjl/views.py` (override key of the same
name) and Thailand's `PASSTHROUGH_OVERRIDE_KEYS`, so the pro forma receives
it the way `pv_inverter_replacement_year` does. `bess_replacement_enabled`
joins `VIETNAM_REPORT_QUERY_KEYS` and is parsed in `views.py` with
`_parse_boolean_query_param` into `assumptions` only (like
`grid_charging_enabled`, but with no cash-flow override: the replacement
series is driven by the REopt inputs, the flag only labels the sheet).
`battery_replacement_year` stays in every list for cases that enable the
event.

### Thailand defaults JSON

`bess_replace_cost_per_kw` and `bess_replace_cost_per_kwh` entries are
replaced by

```json
"bess_replacement_enabled": {"value": false,
  "source": "Client direction 2026-09-12: no scheduled battery replacement inside the 20 year horizon; capacity fade is carried by the Battery SOH curve and derates the battery's savings instead.",
  "note": "..."}
"bess_cycle_life_efc": {"value": 8000, "source": "Client direction 2026-09-12 ...", "note": "..."}
```

`_DERIVED_COUPLINGS` loses the two replace-cost rows; `_POLICY_EQUALITIES`
gains `bess_replacement_enabled` and `bess_cycle_life_efc`. The
`project_years` note that mentions "BESS replacement year 10" is reworded.
Text-level edits only (no `json.dumps` rewrite).

### Proforma core

`_bess_replacement_costs` already returns `None` at zero cost, so a disabled
case books no event without further change. Assumptions sheet "Replacement
Policy" section shows, when disabled: "Battery replacement: not scheduled
inside the 20 year horizon (client direction 2026-09-12); capacity fade is
carried on the Battery SOH sheet". When enabled it shows year and unit
prices as today. The audit row "Equipment replacement (engine schedule)" and
`_replacement_bullet` follow the same switch.

## Part B: SOH engine (`proforma_vietnam/battery_soh.py`)

Pure function, no I/O:

```python
def battery_state_of_health(*, size_kwh, soc_series_fraction, discharge_series_kw,
                            time_steps_per_hour, project_years,
                            cycle_life_efc=BESS_CYCLE_LIFE_EFC,
                            end_of_life_soh=BESS_END_OF_LIFE_SOH,
                            calendar_fade_coefficient=BESS_CALENDAR_FADE_COEFFICIENT,
                            calendar_fade_exponent=BESS_CALENDAR_FADE_EXPONENT,
                            cycle_fade_coefficient=None)
```

- Daily inputs from the year-1 series, repeated for every year:
  `Eavg[d] = mean(soc[ts] for ts in day d) × size_kwh` (kWh),
  `Eminus[d] = Σ discharge_kw[ts] for ts in day d / time_steps_per_hour` (kWh).
  The series may be 8760 or 35040 long; days are consecutive blocks of
  `24 × time_steps_per_hour` steps, 365 per year (REopt's own convention).
- `k_cyc = (1 − end_of_life_soh) / cycle_life_efc` unless
  `cycle_fade_coefficient` is given explicitly (the REopt-replication test
  passes NREL's 2.46e-5).
- Recurrence, D = 365 × project_years days, SOH in kWh:
  `SOH[1] = size_kwh`;
  `SOH[d] = SOH[d−1] − (k_cal × α × Eavg[d−1] × d^(α−1) + k_cyc × Eminus[d−1])`
  for d = 2..D. This is REopt.jl v0.57.0 `add_degradation` with
  `hours_per_time_step` set to 1 (ruling 4). Note REopt's code uses the
  discharged energy, not the documented (E⁺+E⁻)/2; the code is followed.
- Returns a dict:
  - `soh_fraction_by_day` (length D, SOH / size_kwh)
  - `years`: list of per-year dicts, year 1..project_years:
    `soh_end`, `soh_average` (mean of the year's daily fractions),
    `usable_kwh_end`, `efc_in_year` (Σ Eminus / size_kwh),
    `efc_cumulative`, `calendar_fade_kwh`, `cycle_fade_kwh`
  - `soh_average_by_year` (the derate multiplier, list of floats)
  - `first_year_below_end_of_life` (int or None)
  - `coefficients`: k_cal, α, k_cyc, cycle_life_efc, end_of_life_soh
  - `year_one_daily_average_soc_kwh`, `year_one_daily_discharge_kwh`,
    `year_one_efc`
- Returns `None` when `size_kwh <= 0` or the series are empty.

Tests (`proforma_vietnam/tests/test_battery_soh.py`):
1. REopt replication: fixture from the 2026-09-12 probe of
   `bess_arbitrage_5mw` (hourly, 25,000 kWh): its own `soc_series_fraction`,
   `storage_to_load_series_kw` and REopt's `state_of_health` (7,300 days).
   With NREL's k_cyc the replica matches every day within 2e-3 (REopt
   rounds the SOC to three decimals) and day 7,300 within 1e-3 of 0.823.
   Fixture stored as `tests/fixtures/soh_probe_bess_arbitrage_5mw.json`.
2. Resolution invariance: a synthetic hourly day and the same day at 15
   minute resolution (each hourly value split in four) give identical SOH.
3. `k_cyc` derivation: 8,000 EFC → 2.5e-5; a battery cycled exactly once a
   day at full capacity with calendar fade zeroed reaches 80 percent on day
   8,001 (±1).
4. Year table: `soh_average` lies between the year's start and end values;
   `efc_cumulative` is monotone; `first_year_below_end_of_life` is None on
   the probe fixture.
5. `None` for a zero-size battery.

## Part C: fade derating in the cash flow

### Battery quantities (year 1, computed in `esco_pro_forma`)

All in cash-flow currency, on the same de-levelized basis as the other
inputs (storage series divided by λ like `project_served_pv_kwh`; grid
charging left as a grid quantity, matching `report_data`).

| key | definition | when non-zero |
|---|---|---|
| `energy_revenue_vnd` | Σ storage_to_load × rate × discount | storage inside `project_served_pv_kwh` (PV-charged) and ESCO/DPPA structures |
| `served_retail_value_vnd` | Σ storage_to_load × rate | storage inside served |
| `unserved_energy_value_vnd` | Σ storage_to_load × rate − Σ grid_to_storage × rate | storage NOT inside served (grid charging allowed) |
| `demand_savings_vnd` | demand(PV-only counterfactual) − demand(optimized), ÷ λ, floored at 0 | tariff has a supported demand structure |
| `matched_energy_share` | Σ storage_to_load / Σ served (kWh) | storage inside served |
| `soh_by_year` | `soh_average_by_year` from Part B | always |

Passed to `calculate_vietnam_esco_cash_flow(battery_fade=...)` as one dict;
`None` (no storage) leaves every existing path untouched, byte for byte.

### Demand counterfactual (`proforma_vietnam/demand_charge.py`)

`demand_charge_from_series(tariff_inputs, grid_purchase_kw)` returns the
year-1 demand cost for a grid purchase series under the tariff's demand
structure, or `None` if the structure is not supported:

- `coincident_peak_load_charge_per_kw` + `coincident_peak_load_active_time_steps`
  (REopt 1-based step indices per period): Σ_p rate_p × max(purchase[ts], ts ∈ active_p).
- `monthly_demand_rates` (12): Σ_m rate_m × max purchase in calendar month m,
  months as consecutive day blocks of a 365 day year at the series resolution.
- Anything else (URDB, `tou_demand_rates`, ratchets/lookback set): `None`.

`bess_demand_savings` = `demand(max(load − pv_available, 0)) − demand(optimized purchase)`
where `pv_available = pv_to_load + pv_to_storage + pv_curtailed + pv_to_grid`
(raw series) and optimized purchase = `ElectricUtility.electric_to_load +
electric_to_storage`. When the function returns `None`, `demand_savings_vnd`
is 0 and `derivation.battery_fade.demand_attribution = "none: unsupported tariff demand structure"`.

Tests (`test_demand_charge.py`), reading the saved results in `outputs/`
selected by the `run_uuid` in each directory's results file:
- Thailand case_6: BAU from `load_series_kw` equals REopt's
  `year_one_coincident_peak_cost_before_tax_bau`; optimized from the utility
  series equals `year_one_coincident_peak_cost_before_tax`; both within 0.5.
- Vietnam case_3: same two tie-outs against `year_one_demand_cost_before_tax(_bau)`.
- A hand-built 3-period coincident-peak example and a 12-month example with
  known answers; an unsupported structure returns `None`.

### Cash flow application (per year index y, `m_y = soh_by_year[y]`, `deg_y = (1 − pv_deg)^y`)

- ESCO energy revenue:
  `((base_energy − bess_energy) × deg_y + bess_energy × m_y) × energy_mult`.
- Served-retail repurchase (both loops, every structure that uses it):
  `(base_served − bess_served) × (1 − deg_y) + (bess_served + bess_unserved) × (1 − m_y)`
  replaces `base_served × (1 − deg_y)`.
- Demand: `demand_savings = ((base_demand − bess_demand) + bess_demand × m_y) × cap_mult`;
  ESCO share and offtaker remainder as today.
- Grid arbitrage: `base_arb × m_y × energy_mult`.
- Direct ownership: the optimized bill uses the served-retail repurchase
  above plus `bess_demand × (1 − m_y)` inside the same bracket (the existing
  code escalates that whole bracket with the energy factor; kept).
- Grid-CfD DPPA: `_dppa_year_terms` takes a generation multiplier
  `g_y = (1 − share) × deg_y + share × m_y` in place of `degradation_multiplier`.
  Physical DPPA: `matched_kwh × g_y`, revenue × g_y.
- Surplus export: PV only, unchanged.
- New row fields when `battery_fade` is present: `battery_soh_fraction`
  (m_y) and `battery_fade_loss_vnd`, the project-level value lost that year:
  `((bess_served + bess_unserved) × energy_mult + bess_demand × cap_mult) × (1 − m_y)`
  for ESCO and direct ownership, and
  `(matched_retail_value × share × energy_mult + bess_demand × cap_mult) × (1 − m_y)`
  under grid-CfD DPPA (physical DPPA: `matched_kwh × share × ppa_price × ppa_mult × (1 − m_y)`).
  Informational (shown on the SOH sheet); not part of any tie-out.
- Derivation: `derivation["battery_fade"]` = the six inputs above plus
  `years` table, coefficients and `demand_attribution`; money keys converted
  by `_finalize_currencies` like the rest.

Who bears the fade follows the structure's existing PV-degradation
mechanics: ESCO revenue falls with the battery's served kWh and the offtaker
repurchases the shortfall at retail; under direct ownership the owner bears
all of it; under DPPA the generator's FMP/fee terms fall and C_BL rises.

Stated modelling assumption (Model Basis, Battery SOH sheet, MODEL_AUDIT):
energy delivered by the battery scales with SOH, i.e. the battery is treated
as capacity-bound every day. That is the upper bound of the loss for a
battery that is not fully cycled daily, so the derate is conservative.

### Audit sheet (`write_pro_forma_audit_sheet`)

Only when `derivation.battery_fade` is present (workbooks without a battery
stay byte-identical apart from the date stamp):

- Named inputs on the Assumptions sheet: `BESS_ENERGY_REV`,
  `BESS_SERVED_RETAIL`, `BESS_UNSERVED_VALUE`, `BESS_DEMAND_SAVINGS`,
  `BESS_MATCHED_SHARE`.
- Factor rows: `fac_soh` "Battery SOH factor (year average)" with per-year
  values from the derivation (INPUT_FILL, like the replacement row), and
  under DPPA/physical `fac_gen` "Generation factor (PV degradation, battery SOH)"
  `=(1-BESS_MATCHED_SHARE)*fac_deg+BESS_MATCHED_SHARE*fac_soh`.
- Formulas: each line listed under "Cash flow application" gets the
  corresponding term so the Excel recomputation still ties to the engine.
  The tie-out status rows are the test: `validate_workbook` must report
  every check OK on the nine storage workbooks.

## Part D: "Battery SOH" sheet (`xlsx_builder`, both countries)

Written after "Technical Results" when `derivation.battery_fade` exists.

1. Title, then a method block: recurrence (one line), coefficients, cycle
   life and its source, "h = 1" note, the capacity-bound assumption, and
   "REopt's optimiser does not see this curve; it derates the proforma only".
2. Key results: SOH end of year 10 and 20; first year below 80 percent or
   "not within the 20 year horizon"; cumulative EFC over the horizon;
   year-1 EFC; lifetime value lost to fade (USD, Σ rows).
3. Table, year 0..20: Year | SOH end of year | SOH year average (derate
   factor) | Usable capacity (kWh) | EFC in year | Cumulative EFC | Calendar
   fade (kWh) | Cycle fade (kWh) | Value lost to fade (USD). Year 0 row:
   SOH 1.0, zeros.
4. LineChart from the table: SOH end of year (percent) and an 80 percent
   reference series, years on the x axis. openpyxl `LineChart` as on the
   Dispatch Profile sheet.
5. Cover sheet's sheet index gains the entry; Model Basis gains a "Battery
   ageing" paragraph; Assumptions "Replacement Policy" section gains
   "Battery cycle life (EFC to 80 percent)".

No em dash (U+2014) anywhere in generated output.

## Part E: re-solve, rebuild, gate, notes

- Nine storage cases re-solved through Docker (Vietnam factory_a 1, 2, 3, 5,
  6; bess_arbitrage_5mw and _mfg; Thailand case_5, case_6); echo verified
  (`replace_cost_per_kw = replace_cost_per_kwh = 0`, no replacement years
  in the echoed inputs beyond REopt defaults).
- All fourteen workbooks rebuilt; the five without a battery must show 0
  numeric diffs against their current baselines (the regression proof that
  the new code is inert without storage); the nine with a battery get new
  baselines after the reconcile table is written.
- `validate_workbook` clean on all fourteen.
- SESSION_NOTES.md handoff: rulings, code map, reconcile table (old → new
  for the nine: sizes, capex, NPV, IRR, min DSCR, SOH y20, lifetime fade
  loss), the stale deliverables (memo EN/VI, pptx, artifact: year-10 DSCR
  paragraph no longer true), and the open follow-ups.
- Branch left unmerged. No push.

## Out of scope

- Reissuing the memo, deck and artifact.
- Calibrating calendar fade to LFP or ambient temperature.
- Feeding SOH back into REopt's dispatch or sizing.
- A replacement reserve in the debt sizing.
