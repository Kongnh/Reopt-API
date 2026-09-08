# Keen Thailand final pass: de-levelization, Thailand gate, confirmed benchmarks

Date: 2026-09-08
Branch: `thailand-adaptation` at `7f501692`, 83 commits ahead of `master`, clean
fast-forward available.

## Motivation

The Keen Thailand deliverable shipped on the branch but carries three classes of
open item, recorded in the `2026-09-08` handoff entry at the top of
`SESSION_NOTES.md`:

1. A degradation double count in the shared financial core, understating savings
   by 4.10 percent (Thailand) and 4.95 percent (Vietnam). Left in place at the
   time because fixing it breaks Vietnam's byte-identical guarantee.
2. Thailand has no regression gate at all. `baseline_workbooks/` holds only
   Vietnam cases. Two Critical defects reached six client workbooks past a green
   test run because nothing compared Thailand output against a known-good state.
3. Nineteen provisional cost inputs, of which the client has now confirmed five.

The user has authorised changes to Vietnam, regeneration of `baseline_workbooks/`
and a merge to `master`, all of which were previously hard constraints. This spec
covers the work those authorisations unlock.

## Findings that shape the design

Each was verified against real case data rather than taken from the handoff.

**The double count is real and enters through REopt's echoed defaults, not
through `case.json`.** Thailand's `case.json` PV block contains only `max_kw`.
But `esco_pro_forma.py:121` reads `inputs.get("PV")`, which is the input REopt
echoes back with its own defaults filled in, including
`degradation_fraction = 0.005`. Confirmed by reconstruction: the stored
`lifetime_avoided_tco2e` of 24820.0789 matches a 0.005 degradation series to the
fourth decimal, against 26341.62 at zero. The consequence is that removing
`degradation_fraction` from the payload would not fix anything.

**REopt's dispatch series are levelized, and the bill is computed from them.**
For Thailand case_1 the four PV dispatch series sum to 2424811.3 kWh, which
equals `annual_energy_produced_kwh` to a ratio of 1.000000, against
`year_one_energy_produced_kwh` of 2524235.0. Separately,
`grid_to_load = load - pv_to_load` holds exactly. So `year_one_bill_before_tax`
is a levelized bill despite its name, and the proforma's `(1 - deg)^y` is applied
on top of a base that already carries degradation.

**Measured levelization factors:** Thailand 0.960612, Vietnam 0.952869 (identical
across the three cases sampled).

**Levelization is not a post-hoc scalar.** REopt applies the factor to the PV
production parameter inside the optimisation, so the returned solution is the
optimum of a modified problem, not the original optimum scaled. Dividing back by
lambda is therefore an approximation, exact only where no other technology
contributes to savings.

**O&M is not levelized.** `year_one_om_costs_before_tax` equals `size_kw` times
`om_cost_per_kw` exactly (ratio 1.0). This gives the fix a sharp invariant: O&M,
capex and debt rows must not move at all.

**REopt rounds PV cost parameters to whole dollars.** An input of 7.5 USD/kWp/yr
is applied as 8.00, confirmed in the echoed inputs.

**Zero export, 8.5 percent curtailment.** Thailand case_1 curtails 206569.5 kWh
against 2424811.3 kWh produced, with `electric_to_grid_series_kw` identically
zero. The roof is not the only binding constraint; the export prohibition also
binds, and this is not disclosed in the current memo.

## Decisions

Numbered for reference from the implementation plan. D1 through D6 were chosen by
the user; D7 through D12 follow from the findings above.

**D1. Fix the degradation double count properly and re-baseline Vietnam.** Not
Thailand-only, which would leave two countries computing differently on one
engine.

**D2. De-levelize, then apply degradation.** Divide the generation-linked
quantities by lambda to recover a true year one, then let the proforma apply
`(1 - deg)^y` on its own time axis. Rejected alternative: treating REopt's
levelized value as the lifetime average and holding it flat. That is wrong
because REopt's lambda is computed with REopt's discount rate, while the proforma
discounts at `owner_discount_rate_fraction`, a different number, so REopt's
average is not the proforma's average. It also flattens the year-by-year stream
and understates year-one DSCR.

**D3. Accept the residual approximation rather than solve twice.** The rigorous
alternative is a second dispatch-only solve at fixed optimal sizes with
degradation zeroed. Rejected as disproportionate: Thailand carries no storage in
five of six cases and 58 kWh in the sixth, so the approximation is effectively
exact there. For Vietnam the residual is bounded by (storage share of savings)
times 4.95 percent, smaller than the 4.95 percent error being removed even under
a pessimistic share. The measured residual will be recorded in `MODEL_AUDIT.md`
as a number, not as prose.

**D4. Do not zero `degradation_fraction` in the payload.** It would make REopt
size the system without knowledge of degradation, biasing capacity selection.
Sizing is currently correct and must not be disturbed.

**D5. Regenerate all baselines, but commit the old ones first.** The pre-change
baselines get their own commit so the transition is recoverable from git history.

**D6. Merge to `master` last,** after all four suites are green and the gate is
clean.

**D7. Build the Thailand baseline before fixing degradation.** Ordering matters.
A baseline captured at the current state turns the gate from an obstacle into the
measuring instrument that proves the fix does exactly what is claimed. Vietnam
already has this property.

**D8. Confirmed benchmark values.**

| Key | Value | Provenance |
|---|---|---|
| `pv_installed_cost_per_kw` | 475.0 | Client, midpoint of a 450 to 500 USD/kWp C&I rooftop range |
| `annual_om_per_kw` | 7.125 | Client direction, 1.5 percent of PV capex. REopt applies 7.00 |
| `bess_installed_cost_per_kw` | 100.0 | Client |
| `bess_installed_cost_per_kwh` | 150.0 | Client |
| `bess_replace_cost_per_kw` | 70.0 | Re-derived at 70 percent of install cost, client's choice over the previous 50 percent |
| `bess_replace_cost_per_kwh` | 105.0 | Re-derived at 70 percent of install cost |
| `discount_rate` | 0.11 | Client |

All seven lose the placeholder marker. The remaining twelve keep it.

**D9. Re-derive the coupled values in code, not as literals.** `annual_om_per_kw`
and the two BESS replacement costs are defined as fractions of costs the client
just changed. Holding them as literals is what produced the contradiction this
change resolves, where replacing a battery would have cost more per kW than
buying one. They become computed from their base cost and fraction so the next
price change cannot reintroduce the defect. The three fractions are 1.5 percent
of PV capex for O&M and 70 percent of install cost for both replacement costs.

**D9a. The O&M citation no longer supports the O&M value.** The previous 1
percent coupling was sourced to Farungsang, Varquez and Tokimatsu, MDPI
Sustainability 17(15):7052 (2025). The client has directed 1.5 percent, so that
paper can no longer be cited as the basis. Its 1 percent is retained in the
source note as a published lower bound, and the value itself is attributed to
client direction. Leaving the old citation attached to a number it does not
support would misrepresent the provenance to a third-party reviewer.

**D10. Power factor and grid connection cost are excluded from capex at client
direction.** Both must be disclosed with that reason. The report must not say
"not required", which is a technical conclusion the analysis does not support.
This also closes the standing "declared but never enters capex" gap for
`grid_connection_cost`: the correct resolution is an honest disclosure, not
adding it to capex.

**D11. Disclose the O&M rounding.** The model applies 7.00 USD/kWp/yr, not the
7.125 supplied. The workbook and memo must state the applied value, and the
existing test that pins the value REopt returns must be updated to 7.00.

**D12. Six cases, unchanged.** No roof-valuation case is added.

## Workstreams

Ordering is load bearing between W3, W1 and W2. The rest are independent.

### W3. Thailand regression gate (first)

Capture the six current Thailand workbooks as baselines under
`baseline_workbooks/thailand_rofu_case_N/`, and extend
`proforma_vietnam/tools/compare_workbooks.py` so `rebuild_all_cases` covers both
countries. The comparator stays `values_only=True`; widening it to number formats
is out of scope and recorded as a known limitation.

### W1. De-levelization

In `proforma_vietnam/esco_pro_forma.py`, compute

```
lambda = sum(annual_energy_produced_kwh) / sum(year_one_energy_produced_kwh)
```

over all PV arrays, guarding to 1.0 when the denominator is zero, missing, or the
ratio is non-positive. Then scale exactly three entries of `cash_flow_inputs`:

- `project_served_pv_kwh`, divided element-wise by lambda
- `optimized_evn_bill_vnd`, as `bau - (bau - optimized) / lambda`
- `optimized_demand_charge_vnd`, by the same delta form

BAU quantities, `pv_capex_vnd`, `bess_capex_vnd` and `annual_om_vnd` are not
touched, because none of them depends on PV production. Scaling the savings delta
rather than the bill directly is what keeps BAU untouched.

No feature flag. Both countries want the corrected behaviour, and the before and
after states are reachable through git for the W2 measurement.

### W2. Measure, then re-baseline

Build all fourteen workbooks at the pre-fix commit and at the post-fix commit,
and assert three things:

- Bill savings and PV energy rows scale by exactly `1 / lambda`
- The optimized bill moves to `bau - (bau - optimized) / lambda`, which is a
  smaller relative move than `1 / lambda` and must not be checked against it
- Capex, debt and O&M rows are unchanged to the last digit

The distinction in the second bullet matters: it is the savings delta that is
de-levelized, not the bill, so a test asserting `1 / lambda` on the bill would
fail against a correct implementation.

The third assertion is the one that catches a real mistake, because it detects
scaling something that should not have been scaled.

Note that these assertions test the arithmetic, not the modelling judgement. The
approximation acknowledged in D3 is about whether dividing by lambda is the right
thing to do for storage-attributable savings; the division itself is exact, so
the rows will move by exactly the amounts above either way. Then commit the old
baselines and overwrite all fourteen.

### W4. Complete the "Year 1" relabelling

Executive Summary, Buyer Analysis and Year 1 Snapshot still label levelized
figures as "Year 1". Three earlier occurrences were already corrected, so the
workbook is currently self-inconsistent between sheets.

### W5. Thailand residual gaps

- Re-derive the coupled inputs per D9
- Disclose power factor and grid connection per D10, and remove the "not
  computed" status string in favour of the client-direction wording
- Add the missing end-to-end test that derives inverter replacement cost from
  solved PV capex. Every existing inverter test injects the cost explicitly, so
  the derivation that already broke once through `initial_capital_cost` is
  currently unguarded

### W6. Curtailment disclosure

Report the curtailed fraction and the zero-export condition in the memo, and
state the effect on the storage recommendation.

### W7. Repo hygiene

The 102 MB of committed `results.json` and workbooks under
`outputs/thailand_case/`, two unreachable ESCO fallback strings in
`audit_sheets.py`, and the tautological
`test_assumptions_list_the_active_placeholders`.

### W8. Deliverable

Load the D8 values, re-solve, and produce:

- Updated memo in English
- Vietnamese translation for Allotrope internal use
- Six workbooks
- An HTML report published as an artifact
- The tariff deck updated to the new numbers, so the two documents do not
  contradict each other

The D8 changes to PV and BESS cost alter the payload, so a full solver run is
required. `docker-compose up -d` is a prerequisite; only the database container
is currently running.

## Expected change in the answer

Stated in advance so the result can be checked against the expectation rather
than rationalised after the fact.

PV capex falls 36.7 percent, from 750 to 475. A 1.5 hour battery falls 51.9
percent, from 675 to 325 USD/kW installed. Two consequences are likely:

- The unconstrained PV optimum moves further above the roof limit, strengthening
  the existing finding that the roof binds across the whole plausible range
- The current headline finding that storage never pays may reverse

If storage does become economic, that is a material change to the client
recommendation and must be reported as a changed conclusion, not quietly folded
into the numbers.

## Verification

Green means all four, before and after every workstream:

```
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
./.venv/Scripts/python.exe -m unittest reoptjl.test.test_thailand_tariff -v
gate: rebuild_all_cases + compare_workbooks over both countries, TOTAL DIFFS 0
```

Current state: Thailand 124/124, Vietnam 509/509, tariff 14/14, gate clean.

The gate is expected to go red exactly once, at W1, and W2 exists to prove that
the red is the intended change and nothing more.

## Out of scope

- Widening `compare_workbooks` to number formats, fonts and charts
- The unexecuted Vietnam BESS arbitrage and DPPA negotiation designs
- A second dispatch-only solve, per D3
- Any change under `reo/`
- Any change to the client source `.xlsm` files

## Risks

**The fix scales something it should not.** Mitigated by the W2 invariant that
capex, debt and O&M rows must be unchanged to the last digit.

**Thailand baselines are captured from output that is known to have carried two
Criticals.** The baseline records current behaviour, not correct behaviour. It
protects against regression, not against defects already present. W4, W5 and W6
change Thailand output deliberately, and each such change must be inspected
rather than merely re-baselined.

**Re-solving may not reproduce previous sizing exactly.** REopt sizing has been
observed to be non-reproducible across runs on identical payloads. Since D8
changes the payload anyway, sizes will move for real reasons, and the two effects
cannot be separated. Report sizes as a fresh result rather than a delta.
