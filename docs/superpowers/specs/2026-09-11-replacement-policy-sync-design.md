# Replacement policy sync: whole-system BESS at year 10, PV inverter at year 11, 20-year horizon in both countries

Date: 2026-09-11
Branch: `master` at `55bf0178`, clean, 100 commits ahead of `origin/master`.

## Motivation

A client question exposed that the two country branches book equipment
replacement differently, and that neither books what a 10-year battery warranty
implies:

- Thailand replaces the whole BESS (kW and kWh) in year 10 at 70 percent of
  install and books a PV inverter at 10 percent of solved PV capex in year 11.
- Vietnam `factory_a` replaces the storage inverter in year 10 and the pack in
  year 11 in REopt, but the proforma books both in year 11; it uses 100 percent
  of the kW price and 83 percent of the kWh price; and it books no PV inverter.
- Vietnam `bess_arbitrage_5mw` and `bess_arbitrage_5mw_mfg` send
  `replace_cost_per_kw = replace_cost_per_kwh = 0`, which REopt accepts as a free
  replacement. For a battery-only case that is the largest single overstatement
  in the model.
- Vietnam runs 25 years, Thailand 20.

The user's rulings (2026-09-11):

1. A battery system's life is 10 years and covers the storage inverter and the
   pack together; year 10 replaces the whole system, not the inverter alone.
2. Replacement is priced at **100 percent** of install cost, in both countries.
   This supersedes the 70 percent ruling of 2026-09-09 for Thailand.
3. Vietnam moves to a **20-year** horizon to match Thailand, so a 10-year
   battery needs exactly one replacement inside either horizon.
4. The PV inverter event (10 percent of solved PV capex, year 11) applies to
   Vietnam as well.
5. The rule is to be identical across both branches and enforced, not merely
   documented.
6. Re-solve whatever the rule changes; Docker will be started for it.
7. `model_degradation` stays off. One throwaway solve with it on is added as a
   check of the 10-year assumption, reported but not integrated.

## Findings that shape the design

Verified against REopt.jl v0.57.0 source (`src/core/energy_storage/electric_storage.jl`,
`src/constraints/battery_degradation.jl`, `src/results/electric_storage.jl`) and
the saved `results.json` files.

**REopt splits the BESS replacement in two.** `replace_cost_per_kw` is paid at
`inverter_replacement_year` (power components: PCS/inverter) and
`replace_cost_per_kwh` at `battery_replacement_year` (energy: pack). Both
default to year 10. Each enters the objective through `effective_cost`,
discounted at the owner rate to its replacement year, so **both the year and
the price change the sizing**. Any change to them is a solver-input change.

**REopt's storage O&M does not cover capacity fade.**
`om_cost_fraction_of_installed_cost` (1 percent in both countries) is annual
O&M only. Fade is modelled only with `model_degradation = true`, which no case
sets (the echoed inputs carry no such key). With it off the battery keeps its
nominal capacity for the whole horizon; the scheduled replacement is the only
ageing cost in the model. This is why a whole-system event is the right shape:
it is standing in for all ageing.

**`model_degradation` is not a shortcut.** When on, the constructor zeroes
`replace_cost_per_kw`, `replace_cost_per_kwh` and `replace_cost_constant`
(lines 377 to 385), so the proforma's `_bess_replacement_costs`, which reads
those from the echoed inputs, would book nothing. The augmentation strategy
returns `maintenance_cost` as a single present value, not a yearly series, so
the proforma would have to rebuild the daily formula from `state_of_health` to
get annual cash flows for CIT and DSCR. The replacement strategy adds a binary
per month. And `SOH` never feeds back into the dispatch bounds: degradation
adds cost without reducing delivered energy. The fade coefficients are NREL
laboratory defaults with no Thailand or Vietnam calibration.

**The proforma books both REopt components in one year.**
`esco_pro_forma._bess_replacement_costs` sums kW and kWh replacement and
places the total at `battery_replacement_year`, ignoring
`inverter_replacement_year`. With both years equal this is exact; today for
Vietnam it is not.

**The PV inverter event has one derivation site, in the Thailand report layer.**
`proforma_thailand/report.py:218-223` computes `pv_capex * fraction` and
`report.py:89-97` turns it into a series for the shared
`extra_replacement_costs_by_year` hook. The hook itself is in the shared core
(`esco_pro_forma.py:29`), so Vietnam can use it, but nothing populates it.

**Measured effect of the PV inverter alone on Vietnam** (in memory, year 11,
10 percent of PV capex, nothing else changed): equity IRR down 0.4 to 0.5 pp,
equity NPV down 52 to 92 kUSD, `case_3` NPV 174.5 to 85.0 kUSD.

**Two horizon literals exist for Vietnam.** `case_builder.DEFAULT_ANALYSIS_YEARS
= 25` (sent to REopt) and `vietnam_defaults.json financial.project_years = 25`
(used by the cash flow). They agree by coincidence.

**The Model Basis sheet hard-codes "25-year".** `audit_sheets.py:2360` carries
the literal in both country branches of a conditional; every shipped Thailand
workbook says 25 while its Assumptions sheet says 20.

**The name `inverter_replacement_year` means two things.** On the REopt
storage block it is the storage PCS year (rendered as "Inverter replacement
year" on the Assumptions sheet, value 10). On the Thailand assumptions dict it
is the PV inverter year (rendered as `inverter_replacement_year`, value 11).
The user's question started from exactly this ambiguity.

**Thailand cases 1 to 4 carry no `ElectricStorage` block in their payload**
(`max_kw = max_kwh = 0`), so a change to storage replacement inputs cannot
change their solver results.

**Two Vietnam workbook paths exist.** `run_case.py` downloads a workbook from
the API at solve time via a query-parameter mapping in `reoptjl/views.py`;
`rebuild_report.py` builds one locally via
`run_dppa_negotiation_sweep.cash_flow_overrides_from_assumptions`. The API
mapping already lacks `direct_ownership`, `contract_years` and the VAT keys, so
the rebuilt workbook has been the canonical one since the previous session.

## Design

### D1. One replacement policy in the shared core

`proforma_vietnam/defaults/__init__.py` exports the policy as module constants:

```python
PROJECT_YEARS = 20
BESS_REPLACEMENT_YEAR = 10
BESS_REPLACE_FRACTION_OF_INSTALL = 1.0
PV_INVERTER_REPLACEMENT_YEAR = 11
PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX = 0.10
```

These are the rule. Each country's defaults JSON keeps its own numbers with
its own provenance, and each country's `defaults/__init__.py` asserts at import
that the JSON agrees with the policy. A divergence fails the import of the
package, which is the mechanism that already caught one price change in
Thailand.

Thailand: `_DERIVED_COUPLINGS` imports `BESS_REPLACE_FRACTION_OF_INSTALL` in
place of the literal `0.70`; `bess_replace_cost_per_kw/kwh` become 100 / 150
with the source text "Client direction 2026-09-11: replacement at 100 percent
of install cost; supersedes the 70 percent ruling of 2026-09-09". A second
check asserts `project_years`, `pv_inverter_replacement_year` and
`pv_inverter_replacement_fraction_of_pv_capex` equal the policy. The two PV
inverter entries keep the placeholder marker: the policy is Allotrope's
convention and Keen has not confirmed it.

Vietnam: `financial.project_years` becomes 20 and is asserted equal to
`PROJECT_YEARS`. `case_builder.DEFAULT_ANALYSIS_YEARS` is deleted and the
builder reads `DEFAULT_PROJECT_YEARS`, so the horizon sent to REopt and the
horizon the cash flow runs are the same value by construction. Vietnam's JSON
gains no BESS entries: install prices stay in `case.json` where every Vietnam
case already sets them, and the replacement rule is applied by the builder
(D2).

### D2. Both builders derive replacement from the policy

For the storage block, when `case.json` omits a key:

- `replace_cost_per_kw = BESS_REPLACE_FRACTION_OF_INSTALL * installed_cost_per_kw`
- `replace_cost_per_kwh = BESS_REPLACE_FRACTION_OF_INSTALL * installed_cost_per_kwh`
- `inverter_replacement_year = battery_replacement_year = BESS_REPLACEMENT_YEAR`

where `installed_cost_per_*` is the value the builder is about to send (case
override or default). Deriving from the effective install price rather than
from a stored replace price keeps the rule true under a price sensitivity,
which a stored 100 / 150 would not. An explicit value in `case.json` still
wins, so sensitivities on the replacement itself remain possible.

Thailand's builder already fills from `FINANCIAL_DEFAULTS`; it changes to the
derivation above and additionally sends both replacement years explicitly
(equal to REopt's default, so cases 5 and 6 see the same year they saw before
and cases 1 to 4 send no storage block at all).

The eight Vietnam `case.json` files (`factory_a/case.json`, `case_1..6`,
`bess_arbitrage_5mw`, `bess_arbitrage_5mw_mfg`) drop `analysis_years`,
`replace_cost_per_kw`, `replace_cost_per_kwh`, `inverter_replacement_year` and
`battery_replacement_year`, so the policy governs and the case files stop
carrying a copy of the rule that can drift, which is how 80 / 100 and 10 / 11
came to be. `bess_arbitrage_5mw*` lose their explicit zeros the same way. The
Assumptions sheet source column for these rows reads "replacement policy
(proforma_vietnam.defaults)" rather than `case.json`, closing the mislabel
pattern of register item 12 for these rows.

The `battery_replacement_year` passthrough in the Vietnam builder
(`case_builder.py:531`) and the `cash_flow_overrides_from_assumptions` mapping
keep working: the builder now writes the policy year into assumptions when the
case does not set one.

### D3. PV inverter derivation moves into the shared core

`calculate_esco_pro_forma_from_reopt_results` accepts two new overrides,
`pv_inverter_replacement_year` and
`pv_inverter_replacement_fraction_of_pv_capex`. When both are set and the run
has PV, it builds a one-event series `fraction * _pv_capex(pv_outputs)` at
that year and merges it with the BESS series and any caller-supplied
`extra_replacement_costs_by_year` through the existing
`_merge_replacement_costs`. The derived amount is attached to the result as
`derivation["pv_inverter_replacement"] = {"year", "fraction", "cost_usd"}` so
the Assumptions sheet can show it for either country from one place.

Both builders write the two policy values into `assumptions` at case-build
time, and both report layers read them from `assumptions`, never from the
defaults at render time. That is the same pattern the previous session settled
on for O&M after the render-time read produced a stale figure. Thailand
`report.py` deletes its local derivation (both sites);
`assumptions["inverter_replacement_cost_usd"]` is no longer written and the
Assumptions row reads the derivation block instead. Vietnam's
`cash_flow_overrides_from_assumptions` maps the two keys;
`run_case.VIETNAM_REPORT_QUERY_KEYS` and the `reoptjl/views.py` query mapping
gain the same two keys so the solve-time workbook and the rebuilt workbook agree
on this rule. The other pre-existing gaps in the API mapping are recorded, not
fixed (see Out of scope).

The `extra_replacement_costs_by_year` hook stays as it is, the generic escape
hatch for any event that is not one of these two.

### D4. Rename the PV inverter keys so the two inverters cannot be confused

In both countries' assumptions and defaults JSON, `inverter_replacement_year`
and `inverter_replacement_fraction_of_pv_capex` become
`pv_inverter_replacement_year` and `pv_inverter_replacement_fraction_of_pv_capex`.
The REopt storage block key `inverter_replacement_year` is REopt's name and is
not renamed, but its Assumptions sheet label becomes "Storage inverter (PCS)
replacement year". No migration shim: every `assumptions.json` in both
countries is regenerated by the builder in this pass (D6), so the old key
never reaches a report. `rebuild_report` on a directory whose
`assumptions.json` predates this change books no PV inverter, which is the
honest reading of a record that does not contain one; the plan asserts all
fourteen files carry the new keys before any rebuild.

### D5. Model Basis and replacement text read the data

`audit_sheets.py:2360` formats the horizon from `project_years` in both
branches of the conditional. The replacement bullet at `:2405` says: "Battery
replacement (storage inverter and pack together) is booked in year N at
100 percent of install cost; the PV inverter is booked in year M at
10 percent of PV capex", with N and M from the derivation, and drops the PV
inverter clause when the run has no PV. `audit_sheets.py:304` stops defaulting
`analysis_years` to a literal 25.

`outputs/vietnam_case/factory_a/CASE_JSON_INPUT_GUIDE.md` rows for the five
storage keys and `analysis_years` are rewritten to say the policy applies when
the key is omitted and what the policy is.

### D6. Re-solve, rebuild, re-baseline

Solver inputs change for all eight Vietnam cases (horizon, replacement years,
replacement prices) and for Thailand cases 5 and 6 (replacement prices).
Thailand 1 to 4 are not re-solved: the builder is re-run in dry-run mode to
regenerate their `payload.json` and `assumptions.json`, the plan asserts the
payload is byte-identical to the committed one, and only then are they
rebuilt against their existing `results.json`.

Order matters because the gate compares against baselines by filename:

1. All code and JSON changes land; both suites green; the gate is run once
   against the current baselines and its diffs are inspected and recorded (they
   must be confined to replacement, depreciation, CIT, debt-coverage, returns,
   Model Basis text and Assumptions rows; O&M, capex, bills and dispatch must
   not move).
2. Docker up; readiness gated on `localhost:8081/health` and a 405 from
   `GET localhost:8000/v3/job/`, as in the previous session's script.
3. Ten solves, each followed by reading `results.json` back and asserting
   `Financial.analysis_years == 20`, `ElectricStorage.replace_cost_per_kw ==
   installed_cost_per_kw`, `replace_cost_per_kwh == installed_cost_per_kwh`,
   `inverter_replacement_year == battery_replacement_year == 10`, and for
   Thailand `PV.installed_cost_per_kw == 500`. A solve whose echo fails the
   assertion is not kept.
4. Fourteen workbooks rebuilt with each country's `rebuild_report`; exactly one
   workbook per case directory; the user's untracked
   `vietnam_report_review*.xlsx` files untouched.
5. Baselines regenerated; gate TOTAL DIFFS 0 on all fourteen.

### D7. SOH check with `model_degradation` on (throwaway)

After the ten solves, two extra solves in the scratchpad, never under
`outputs/`: Thailand case 6 and Vietnam `bess_arbitrage_5mw`, each with
`model_degradation: true`, `maintenance_strategy: "augmentation"` (linear, no
binaries), all other inputs identical to the kept solve. From each result
read `outputs.ElectricStorage.state_of_health` and report the first day the
normalised SOH falls below 0.8, and `maintenance_cost` against the present
value of our year-10 event at the owner rate. The finding goes into the memo's
technical basis as one paragraph and into the session notes. Nothing from these
solves enters a workbook.

### D8. Deliverables that move

Thailand: six workbooks; `KEEN_THAILAND_MEMO.md` and `KEEN_THAILAND_MEMO_VI.md`
(every figure, the storage conclusion re-stated from the new solve whichever way
it falls, the replacement paragraph, the SOH check); the internal pptx slides
that quote figures; the HTML artifact (same URL, redeployed). The memo must say
plainly that the 100 percent replacement is a client ruling and that it is the
most conservative of the three price points run.

Vietnam: eight workbooks. The narrative decks and speaker notes were already
stale from the levelization fix (register item 1) and move again; they stay a
recorded follow-up unless the user asks for them in this pass.

`SESSION_NOTES.md`: a 2026-09-11 handoff entry; register items 17 and 18
closed; a new item for the API mapping gap.

## Tests

New, each proven to fail on a reverted change before it passes:

- Thailand and Vietnam defaults: JSON agrees with the policy constants; a
  desynced value raises at import (existing Thailand coupling test rewritten to
  100 percent; "replacing never costs more than buying new" kept, it holds at
  equality).
- Vietnam builder: omitted replacement keys are derived from the effective
  install price and the policy year; explicit keys win; `analysis_years`
  defaults to `PROJECT_YEARS` and to nothing else.
- Thailand builder: same derivation; both replacement years sent; no storage
  block when `max_kw = max_kwh = 0`.
- Core: the PV inverter event lands at `fraction * pv_capex` in the right year
  and merges with the BESS event and an explicit extra series; a run with no PV
  books none; the derivation block carries year, fraction and cost.
- Thailand report: the Assumptions row shows the derived cost from the block;
  the old local derivation is gone (a test that patches `_pv_capex` and sees the
  change in the workbook).
- Audit sheets: Model Basis says "20-year" from data, and says "25-year" when
  fed 25; the replacement bullet names both events with the right years and
  drops the PV clause without PV; the storage row is labelled "Storage inverter
  (PCS) replacement year".
- Existing fixtures pinned to 25 years (six test modules) updated where the 25
  was a default being relied on, left alone where 25 is an explicit input under
  test.

Both suites, then the tariff suite, then the gate, in that order, before any
solve.

## Out of scope, recorded as follow-ups

- The API query mapping in `reoptjl/views.py` lacks `direct_ownership`,
  `contract_years`, the VAT keys and `surplus_export`; a solve-time workbook
  for such a case differs from the rebuilt one. Only the two PV inverter keys
  are added here.
- Vietnam narrative deliverables (item 1 of the register).
- The PV inverter is capitalised under the BESS depreciation class because the
  merged series is one series (8 years Vietnam, 5 years Thailand). Both are
  permissible machinery lives; a separate PV-class schedule is a refinement
  for when a client asks.
- The Vietnam DPPA residual (item 15) is unchanged by this work.

## Risks stated up front

- At 100 percent replacement the optimiser may drop storage in Thailand cases
  5 and 6. If it does, the memo says so and the earlier "storage pays"
  conclusion is withdrawn a second time with the reason. This is the correct
  outcome, not a failure of the work.
- Every Vietnam figure changes in three ways at once (horizon, replacement,
  inverter). NPV falls on all three; IRR direction depends on the case. The
  handoff will tabulate old against new so the size of each driver is visible.
- The Thailand memo has now been re-run at three price points. The memo keeps
  the history in one paragraph so the reader sees a converging answer, not a
  wandering one.
