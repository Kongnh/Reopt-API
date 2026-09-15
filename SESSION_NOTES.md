# 2026-09-13 (morning handoff) - The four recommendations implemented; both lines re-solved

Ruling (user, 2026-09-13 08:00): implement recommendations 1 to 4 of
`docs/superpowers/notes/2026-09-12-fade-aware-sizing-research.md`. Layout
unchanged: `REopt_API` = `master` (deliverables), this worktree = research,
Julia for research on 8082 (`docker start julia_api_soh`).

## What landed

- **master** (3 commits, 9329e147 / 9ef15b8b / 37aaaf7a): the Vietnam
  builder sends the pro forma's Financial values and zero incentives; the
  runner waits for the output sections (the Thailand `_is_complete` guard:
  case_4's first re-solve came back "optimal" with no PV block); the eight
  Vietnam cases re-solved, workbooks rebuilt, Excel tie-out ALL CHECKS PASS,
  baselines regenerated, gate 0 on fourteen; MODEL_AUDIT section 10; handoff.
- **this line**: the two master commits cherry-picked (5efc04cf, dfc7d3e2);
  the ageing treatment (53e7fc66); the eight Vietnam cases re-solved with the
  aligned objective; all fourteen assumptions regenerated (two new keys on
  storage cases) and workbooks rebuilt; Excel tie-out ALL CHECKS PASS on the
  nine storage workbooks and on the augment demonstration; baselines
  regenerated, gate 0; Vietnam suite 634 + 4 probe tests, Thailand suite green.
- Records of this line are on the aligned objective AND the SOH derate;
  master's are on the aligned objective AND the year-10 replacement. The
  two lines now differ only by the ageing policy, which is the comparison
  the split exists for.

## Reconcile on this line (old = 2026-09-12 solves at a6388781)

| case | PV kW old / new | BESS kW / kWh old / new | capex USD old / new | equity NPV old / new | equity IRR old / new | min DSCR old / new |
|---|---|---|---|---|---|---|
| factory_a/case_1 | 5,701 / 3,520 | 1,896 / 11,087 to 1,031 / 4,079 | 4,218,573 / 2,261,868 | 585,319 / 1,111,148 | 13.3% / 22.2% | 1.02 / 1.37 |
| factory_a/case_2 | 5,996 / 3,968 | 2,011 / 12,331 to 1,180 / 7,311 | 4,518,797 / 2,876,230 | 405,302 / 765,929 | 12.1% / 16.4% | 0.97 / 1.15 |
| factory_a/case_3 | 6,071 / 2,188 | 2,220 / 14,337 to 579 / 3,088 | 4,812,252 / 1,467,206 | -470,729 / 389,852 | 7.7% / 16.2% | 0.78 / 1.12 |
| factory_a/case_4 | 3,243 / 2,436 | 0 / 0 to 0 / 0 | 1,556,758 / 1,169,156 | 440,925 / 529,270 | 16.8% / 21.1% | 1.17 / 1.33 |
| factory_a/case_5 | 5,996 / 3,968 | 2,011 / 12,331 to 1,180 / 7,311 | 4,518,797 / 2,876,230 | 986,353 / 920,389 | 15.1% / 17.5% | 1.07 / 1.16 |
| factory_a/case_6 | 5,914 / 5,914 | 592 / 1,184 to 592 / 1,184 | 3,028,160 / 3,028,160 | 1,982,816 / 1,982,822 | 26.0% / 26.0% | 1.48 / 1.48 |
| bess_arbitrage_5mw | 0 / 0 | 5,000 / 25,000 to 5,000 / 25,000 | 3,400,000 / 3,400,000 | 4,092,688 / 4,092,688 | 53.9% / 53.9% | 2.40 / 2.40 |
| bess_arbitrage_5mw_mfg | 0 / 0 | 5,000 / 25,000 to 5,000 / 25,000 | 3,400,000 / 3,400,000 | 1,455,082 / 1,455,082 | 24.7% / 24.7% | 1.51 / 1.51 |

## Follow-ups

- case_5 (grid-CfD): the optimiser sizes on the retail bill, the pro forma
  settles on the CfD; NPV fell with the smaller system. Run the probe's
  grid on it (or size on the CfD price) before quoting it.
- `augment` needs a vendor capacity-maintenance price to be more than a
  scenario; the demonstration folder is the template.
- Thailand case_6's levered optimum (1.25 to 1.5 x) is a financing effect;
  the probe is the check, no code change made.
- Vietnam narrative decks and the negotiation sweep outputs are stale on
  both lines.

## 2026-09-15 close

The Rofu feasibility deck (`Rofu_Thailand_Solar_Storage_Feasibility.pptx` and
the PDF handout, with `deck_source/`) was built on `master` from the memo and
the six Thailand case records there; nothing on this line changed. The push
of both branches was blocked by the session's permission mode and is left to
the user (`git push origin battery-soh-fade` here). The open items above
stand.

# 2026-09-13 (overnight handoff) - Permanent worktree; fade-aware sizing research (A + D)

Research line only. Ruling 2026-09-12 22:30 (user, before sleeping): the
split is a permanent, independent **worktree**, not checkout switching;
run A + D on it; full delegation. Everything below happened on
`REopt_API-soh` (branch `battery-soh-fade`); `master` was not changed,
except that its gitignored gate baselines were regenerated (below).

## Layout now

- `REopt_API` (main tree) = `master` (ac68e5cb). Docker compose (Django
  8000, Julia 8081, celery) mounts this tree. Baselines regenerated from
  master's own workbooks: gate 0 diffs on all 14.
- `REopt_API-soh` (worktree) = `battery-soh-fade`. `.venv` is a junction to
  the main tree's venv (`./.venv/Scripts/python.exe` works unchanged);
  `keys.py`, `outputs/pvwatts_cache/` copied in; `baseline_workbooks/`
  (the SOH baselines) moved in. `git worktree list` shows both.
- The research line has its own Julia server: container `julia_api_soh`
  (image `reopt_api-julia:soh`, `docker commit` of the running `julia_api`,
  so no recompilation), port 8082, mounting the worktree's `julia_src`.
  Its `http.jl` coerces `ElectricStorage.degradation.{cycle_fade_coefficient,
  cycle_fade_fraction, maintenance_cost_per_kwh}` to `Vector{Float64}`;
  without that REopt.jl 0.57 rejects them (`Vector{<:Real}` against
  `Vector{Any}` from JSON). `docker start julia_api_soh` after a reboot.
  Django does not accept `model_degradation`, so research solves post to
  8082 directly with the kept run's echoed inputs.
- Stray file in the master tree: `outputs/thailand_case/rofu_thailand/
  case_5/thailand_report_f27e1bf5-...xlsx` is the SOH-branch workbook that
  git could not unlink on the switch (Excel holds it). Close Excel, delete
  it; it is untracked on master.

## What was run

`proforma_vietnam/tools/fade_sizing_probe.py` (new, committed) on Vietnam
case_1, Vietnam case_3, Thailand case_6 and Vietnam bess_arbitrage_5mw (energy grid at 5 MW pinned). Per case: the kept
solve; `blind` (free sizes, no ageing; Vietnam with the objective aligned,
see below); `deg` (method A: `model_degradation`, augmentation, coefficients
scaled by 1/h so REopt's SOH equals `battery_soh` at h = 1, k_cyc 2.5e-5
from the 8,000 EFC ruling, price declination 3 percent); a grid of pinned
energy capacities at 0, 0.25 ... 1.25 of the blind size plus the deg size
and one refinement round (method D), each also re-solved with degradation
on; and for the ESCO cases a `share` solve sized on the contract shares of
the rates. Every candidate scored by the fade-derated pro forma with the
case's own assumptions. Summaries committed under
`outputs/research/fade_sizing/<case>/summary.{json,md}`; per-solve results
gitignored (4 MB each, `solves/`). Note with the tables and the reading:
`docs/superpowers/notes/2026-09-12-fade-aware-sizing-research.md`.

## Findings (numbers in the note)

1. **The Vietnam objective carries the US defaults** (both lines, older
   than the SOH work): 30 percent ITC and 5-year MACRS bonus on PV and
   storage, 6.24 percent discount rate (REopt discards the sent owner rate
   when `third_party_ownership` is false and the offtaker rate is absent),
   26 percent tax, 1.66 percent escalation. REopt's echo:
   `initial_capital_costs_after_incentives` is 51 percent of
   `initial_capital_costs`. Thailand's builder zeroes all of it (C2 critical
   of 2026-09-05); the Vietnam builder never did. Aligned objective:
   case_1 PV 5,701 to 3,520 kW, BESS 11,087 to 4,079 kWh, derated NPV
   585,319 to 1,111,148; case_3 PV 6,071 to 2,188, BESS 14,337 to 3,088,
   NPV -470,729 to +389,852. The aligned REopt NPV lands within 1 percent of
   the pro forma NPV. **This needs a ruling for master** (it changes every
   Vietnam deliverable).
2. **Sizing.** Once aligned, the ageing-blind size sits on the flat top of
   the derated-NPV curve on both Vietnam cases (within 200 USD over a plus
   or minus 5 percent band). Method A moves the size +3.5 / +6 / +3.9
   percent (case_1 / case_3 / Thailand) and is no better on the curve; its
   bias is REopt dropping the kWh O&M when degradation is on (10 USD/kWh
   present worth against a fade cost of 7), not fade. Fade is a 6
   percent-of-capex effect on these duty cycles and does not bend the
   curve. Thailand case_6 is different for a financing reason: its levered
   equity NPV (70 percent debt at 6.5 percent against 11 percent, 5-year
   depreciation) keeps rising to 1.25 to 1.5 times the blind size (best
   5,565 kWh, +30,500 USD, +1.4 percent); REopt's unlevered objective
   cannot see that and neither does A. Arbitrage 5 MW: optimum duration
   about 5.6 h (28,125 kWh, +5 percent), design point sound.
3. **Dispatch.** Same size, degradation on: +0.5 percent (case_1), +1.5
   (case_3), +0.2 (Thailand), +0.2 (arbitrage). EFC and revenue identical; the gain is resting
   SOC (charge late, do not park full), calendar fade down a quarter. An
   EMS rule, not a sizing input. The first scoring pass showed a false 4.6
   to 8.5 percent gain because the pro forma reads REopt's O&M output;
   `restore_kwh_om` in the probe fixes that and the note carries the
   corrected numbers.
4. **ESCO share in the objective: tested, worse.** Sizing on 0.9 x energy
   and 0.8 x demand rates gives smaller systems whose equity NPV on the
   true-rate curve is lower (case_1 1,080,697 against 1,111,148; case_3
   341,180 against 389,852): the levered equity NPV rewards capex the
   optimiser does not see, and the two biases roughly cancel at full rates.
5. **Augmentation against derate.** Derate present worth 25 to 31 USD/kWh
   of capacity; daily augmentation at the installed price declining 3
   percent costs 7.6 USD/kWh (REopt's degradation cost within 3 percent).
   Booking capacity maintenance instead of derating would lift the Vietnam
   NPVs by about 70,000 USD each; needs a vendor price to be more than a
   scenario.
6. REopt's `state_of_health` matches the replica to 5e-4 on every deg
   solve (Thailand at 15 minutes included), so the 1/h correction is right.

## Recommendation (in the note, short form)

Port the alignment to master (ruling needed); keep the aligned blind solve
as the sizing standard; `model_degradation` only as the consistency proof
and the EMS resting-SOC rule; add `battery_ageing_treatment: derate |
augment` to the pro forma; run the probe as the sizing check on new
projects; then soc_min 0.10 for arbitrage, calendar-fade calibration,
dispatch-realism haircut, 15 minute Vietnam demand-charge cases.

## Housekeeping

- Research line: 4 commits tonight (probe + http.jl coercion + ignore;
  probe fixes + summaries + note + MODEL_AUDIT item + this handoff; log
  ignore fix). Not
  pushed by me. Scratch: `run_probes*.sh`, `render_research_tables.py`,
  `baseline_master.py` in the session scratchpad.
- `docs/superpowers/notes/2026-09-12-fade-aware-sizing-research.md` is the
  deliverable of the night; `summary.md` per case has every solve.
- The two locked old case_6 workbooks and the user's
  `vietnam_report_review*.xlsx` untouched.
- Tests not re-run tonight (no change to package code except the new tool
  module, which imports private helpers `_as_list`, `_levelization_factor`,
  `_series` from `esco_pro_forma`).

# 2026-09-12 (second handoff, 09:00) - Replacement off, SOH curve, fade derate

Branch `battery-soh-fade`, kept independent of `master` at the user's request:
NOT merged, and the user pushed it to `origin/battery-soh-fade` themselves
mid-session (they also checked out `master` at 08:26; I switched back).
Ruling 2026-09-12 (after this handoff): the split is PERMANENT. `master`
carries the Rofu / Keen deliverables (100 percent year-10 replacement policy,
the memo issued 12 September); `battery-soh-fade` is the internal research
line (replacement off, SOH derate). The two run in parallel and are compared,
never merged; a finding that should reach the deliverable is ported as its
own change on master. Spec:
`docs/superpowers/specs/2026-09-12-battery-soh-fade-design.md`. Plan:
`docs/superpowers/plans/2026-09-12-battery-soh-fade.md`. Docker stack up.

## Rulings (user, 2026-09-12, after the first handoff)

1. No scheduled battery replacement inside the 20 year horizon, both
   countries. `technologies.storage.replacement` in case.json opts a case
   back in (year, fraction of install or absolute prices); the raw REopt
   replacement keys are refused by the builders.
2. Project life stays 20 years; the PV inverter event (year 11, 10 percent of
   solved PV capex) stays.
3. Battery ageing is carried by a state-of-health curve computed from the
   solved dispatch, and the battery's share of the savings is derated by it
   every year (the user chose the derate over a display-only sheet).
4. The REopt SOH recurrence is taken with the hours-per-time-step factor
   removed (h = 1), so 15 minute and hourly solves age alike.
5. Cycle life 8,000 equivalent full cycles to 80 percent SOH (LFP datasheet
   convention); calendar fade keeps NREL's coefficients.
6. Every workbook with a battery gets a "Battery SOH" sheet with the curve.
7. All cases re-solved; memo, deck and artifact NOT reissued (stale, below).

## What changed in the code (16 commits on the branch)

- `proforma_vietnam/defaults/__init__.py`: `BESS_REPLACEMENT_ENABLED = False`
  (year 10 / fraction 1.0 kept as the opt-in defaults), `BESS_CYCLE_LIFE_EFC`
  8000, `BESS_END_OF_LIFE_SOH` 0.80, NREL calendar coefficients.
  `proforma_thailand/defaults`: `bess_replace_cost_*` entries replaced by
  `bess_replacement_enabled` and `bess_cycle_life_efc`, both asserted equal
  to the policy at import.
- `proforma_vietnam/case_builder.apply_replacement_policy(storage_config,
  storage_payload)` (shared; Thailand imports it): disabled sends
  `replace_cost 0` and no years; enabled prices the whole system in one year.
  Record in assumptions: `bess_replacement_enabled`, `bess_cycle_life_efc`,
  and when enabled `battery_replacement_year`, `bess_replace_cost_per_kw/kwh`.
  `REPLACEMENT_RAW_KEYS` refused. `bess_cycle_life_efc` travels through
  `VIETNAM_REPORT_QUERY_KEYS`, `views.py`, the sweep map and Thailand's
  `PASSTHROUGH_OVERRIDE_KEYS`.
- `proforma_vietnam/battery_soh.py` (new): REopt.jl v0.57.0 `add_degradation`
  recurrence at h = 1, year-1 pattern repeated. Replicates REopt's own
  `state_of_health` on the 2026-09-12 probe (hourly) to 5.0e-4 worst day over
  7,300 days (fixture `tests/fixtures/soh_probe_bess_arbitrage_5mw.json`).
- `proforma_vietnam/demand_charge.py` (new): year-1 demand charge from a
  purchase series (coincident-peak periods, monthly demand rates); ties out
  to REopt's BAU and optimized demand costs on Thailand case_6 and Vietnam
  case_3 within 0.5 USD. PV-only counterfactual = max(load - PV, 0), no
  optimiser needed. This closes the "storage share not separable" limit of
  MODEL_AUDIT section 9 for the demand line.
- `esco_pro_forma._battery_fade_inputs` + `cash_flow(battery_fade=...)`: the
  battery's share of ESCO energy revenue, the retail repurchase, demand
  savings, grid arbitrage and the DPPA generation-linked terms is multiplied
  by the year-average SOH; the PV part keeps `(1 - deg)^y`. Direct ownership
  adds the lost value to the optimized bill. Rows carry
  `battery_soh_fraction` and `battery_fade_loss_usd`; derivation carries
  `battery_fade`. Without a battery every path is untouched: the four
  structures' audit formulas are frozen in `tests/fixtures/plain_formulas.json`
  and asserted byte-identical, and the five PV-only workbooks gate at 0 diffs
  against the pre-change baselines (one operand-order slip fixed to get there).
- `audit_sheets.py`: SOH factor row (values), generation factor row (DPPA),
  five `BESS_*` named inputs, every affected formula carries the terms so the
  Excel tie-out still holds; Replacement Policy section states the switch and
  the cycle life; Model Basis has a battery-ageing bullet.
- `xlsx_builder.py`: "Battery SOH" sheet (method, key results, year table,
  line chart with the 80 percent line) after Technical Results; Cover index.
- Docs: CASE_JSON_INPUT_GUIDE, ESCO_CONTRACT_MODEL_DESIGN, MODEL_AUDIT s10.
- Records: the nine storage `payload.json`/`assumptions.json` regenerated
  (replace_cost 0, no years, the two new keys); the five PV-only records
  verified unchanged against HEAD.

Tests: Vietnam 596 (+45), Thailand 144 (+1), tariff 14, all green. Excel COM
recalculation of the nine storage workbooks (`validate_workbook`, dedicated
Excel instance): ALL CHECKS PASS, nine tie-outs each, zero REVIEW, so the
SOH terms in the live formulas reproduce the engine. Gate TOTAL DIFFS 0 on
all fourteen after re-baselining the nine storage cases.

## Reconcile, old (workbooks committed at `ac68e5cb`, 100 percent year-10 replacement) against new

Nine storage cases re-solved; the five PV-only cases rebuilt only and identical
to the cent (gate 0 diffs against the pre-change baselines). The first six
rows are Thailand rofu, the rest Vietnam.

| case | PV kW old -> new | BESS kW / kWh old -> new | Capex old -> new | Equity IRR old -> new | Equity NPV old -> new | Min DSCR old -> new | SOH y10 / y20 | EFC/yr | Battery energy value y1 | Battery demand relief y1 | Lifetime fade loss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| case_1 | 1,685 -> 1,685 | 0 / 0 -> 0 / 0 | 842,500 -> 842,500 | 66.4% -> 66.4% | 1,304,997 -> 1,304,997 | 2.86 -> 2.86 | no battery |  |  |  |  |
| case_2 | 1,895 -> 1,895 | 0 / 0 -> 0 / 0 | 947,500 -> 947,500 | 64.5% -> 64.5% | 1,415,588 -> 1,415,588 | 2.79 -> 2.79 | no battery |  |  |  |  |
| case_3 | 2,106 -> 2,106 | 0 / 0 -> 0 / 0 | 1,053,000 -> 1,053,000 | 62.2% -> 62.2% | 1,506,642 -> 1,506,642 | 2.72 -> 2.72 | no battery |  |  |  |  |
| case_4 | 2,549 -> 2,549 | 0 / 0 -> 0 / 0 | 1,274,321 -> 1,274,321 | 56.1% -> 56.1% | 1,610,103 -> 1,610,103 | 2.51 -> 2.51 | no battery |  |  |  |  |
| case_5 | 1,685 -> 1,685 | 222 / 367 -> 297 / 682 | 919,716 -> 974,448 | 64.2% -> 61.7% | 1,353,566 -> 1,381,928 | 2.21 -> 2.70 | 90.8% / 83.6% | 248 | 12,618 (net retail value of battery energy) | 13,210 | 67,714 |
| case_6 | 2,847 -> 3,230 | 507 / 1,881 -> 815 / 4,047 | 1,756,407 -> 2,303,615 | 49.6% -> 42.8% | 1,855,912 -> 2,071,873 | 0.64 -> 2.05 | 91.1% / 83.7% | 261 | 108,315 (net retail value of battery energy) | 35,240 | 367,107 |
| case_1 | 4,568 -> 5,701 | 1,452 / 5,679 -> 1,896 / 11,086 | 2,990,365 -> 4,218,573 | 16.5% -> 13.3% | 773,960 -> 585,319 | -0.92 -> 1.02 | 92.1% / 85.9% | 215 | 236,685 (inside the served series) | 0 | 604,588 |
| case_2 | 5,448 -> 5,996 | 1,611 / 9,461 -> 2,011 / 12,331 | 3,879,459 -> 4,518,797 | 11.6% -> 12.1% | 262,548 -> 405,302 | -1.68 -> 0.97 | 92.1% / 85.8% | 221 | 309,908 (inside the served series) | 0 | 794,673 |
| case_3 | 4,649 -> 6,071 | 1,258 / 7,822 -> 2,220 / 14,337 | 3,270,852 -> 4,812,252 | 8.7% -> 7.7% | -177,968 -> -470,729 | -1.74 -> 0.78 | 92.0% / 85.6% | 224 | 208,584 (inside the served series) | 131,445 | 930,135 |
| case_4 | 3,243 -> 3,243 | 0 / 0 -> 0 / 0 | 1,556,758 -> 1,556,758 | 16.8% -> 16.8% | 440,925 -> 440,925 | 1.17 -> 1.17 | no battery |  |  |  |  |
| case_5 | 5,448 -> 5,996 | 1,611 / 9,461 -> 2,011 / 12,331 | 3,879,459 -> 4,518,797 | 14.8% -> 15.1% | 759,543 -> 986,353 | -1.51 -> 1.07 | 92.1% / 85.8% | 221 | 309,908 (inside the served series) | 0 | 589,983 |
| case_6 | 5,914 -> 5,914 | 592 / 1,184 -> 592 / 1,184 | 3,028,160 -> 3,028,160 | 25.7% -> 26.0% | 1,929,382 -> 1,982,816 | 1.38 -> 1.48 | 90.1% / 81.8% | 298 | 41,260 (inside the served series) | 0 | 80,956 |
| bess_arbitrage_5mw | 0 -> 0 | 5,000 / 25,000 -> 5,000 / 25,000 | 3,400,000 -> 3,400,000 | 54.3% -> 53.9% | 3,436,606 -> 4,092,688 | -6.13 -> 2.40 | 90.2% / 81.9% | 297 | 913,007 (net retail value of battery energy) | 0 | 2,935,219 |
| bess_arbitrage_5mw_mfg | 0 -> 0 | 5,000 / 25,000 -> 5,000 / 25,000 | 3,400,000 -> 3,400,000 | 18.1% -> 24.7% | 578,999 -> 1,455,082 | -7.29 -> 1.51 | 90.2% / 81.9% | 297 | 585,440 (net retail value of battery energy) | 0 | 1,882,126 |

## Reading the numbers

- Two things moved at once for every storage case: the year-10 replacement
  left the objective, so the optimiser built bigger batteries (Vietnam
  case_1 5,679 to 11,087 kWh; case_3 7,822 to 14,337; Thailand case_6 1,881
  to 4,047 with PV now at the 3,230 kW roof cap), and the fade derate then
  took value off those batteries every year. The optimiser does not see the
  fade, so its sizing is ageing-blind; the pro forma corrects the cash flow,
  not the size. A fade-aware size would be somewhere between the two runs.
- SOH at year 20 lands between 81.8 and 85.9 percent in every case; none
  reaches 80 percent inside the horizon. Year-1 EFC 215 to 298 a year, so
  cycle fade dominates calendar fade everywhere; Thailand at h = 1 shows
  83.7 percent (case_6) where the probe's h = 0.25 showed 95.9.
- The year-10 DSCR cliff is gone (no replacement inside the debt term):
  Vietnam minimum DSCR 0.78 to 2.40 across the storage cases, Thailand 2.05
  and 2.70.
- Vietnam case_3 (demand-charge tariff) is the loser: NPV -470,729. Its
  battery carries 131k USD a year of demand relief, and that is exactly the
  line the derate hits hardest.
- Thailand storage outcome: still selected in both cases, larger than before
  (297 / 682 kWh and 815 / 4,047 kWh), NPV up (1.42M and 2.16M) because the
  full-price year-10 event is gone and the fade takes less than it did.

## Deliverables: stale, deliberately not reissued

`KEEN_THAILAND_MEMO.md` / `_VI.md`, the pptx (slides 8, 10) and the artifact
still describe the 100 percent year-10 replacement regime, including the
year-10 DSCR paragraph that no longer applies. Reissue is the user's call
after reading the reconcile; the Vietnam narrative decks were already stale.

## Housekeeping

- The two old case_6 workbooks that were locked on 2026-09-11 were released
  and deleted by this rebuild; nothing left to clean there.
- The user's `vietnam_report_review*.xlsx` files untouched, now four changes
  stale.
- `baseline_workbooks/` regenerated locally for the nine storage cases after
  this handoff was written; the five PV-only baselines were not touched.
- Branch not merged, not pushed by me (the user pushed at 08:26; later
  commits are local).

## Follow-ups

- Fade-aware sizing: the optimiser oversizes without a replacement or fade
  cost. Options: a modest `replace_cost` in REopt as a sizing proxy (the
  proforma would then need to drop the double count), or REopt's own
  `model_degradation` for sizing only (rejected 2026-09-12 for the proforma;
  it is defensible as a sizing signal). Needs a ruling.
- Calendar fade calibration to LFP and 30 degree ambient (NREL lab
  coefficients today).
- ESCO structure with grid-charged storage beside PV: the battery's energy
  value is not booked in this model (pre-existing), so nothing is derated
  there; the Assumptions sheet says so. No current case is in that state.
- DPPA structures: battery share on an energy basis (kWh), not value basis;
  Vietnam case_5 and case_6 are grid-CfD, both PV-charged.
- Replacement reserve item (2026-09-12 morning) is moot unless a case opts
  into a replacement; keep the item, mark conditional.
- Register item 19 (API query mapping) unchanged.

# 2026-09-12 - Handoff: replacement policy sync, both branches, 20 years

Executed overnight on the user's instruction to write the plan and implement
it without checkpoints. Spec: `docs/superpowers/specs/2026-09-11-replacement-policy-sync-design.md`.
Plan: `docs/superpowers/plans/2026-09-11-replacement-policy-sync.md`. Branch
`replacement-policy-sync`, fast-forwarded onto `master` at the end. Docker
stack left running.

## What was ruled and why

A client question on 2026-09-11 exposed that the two branches booked equipment
replacement differently. Four rulings followed, all the user's:

1. A battery system's life is 10 years and covers the storage inverter and the
   pack together; year 10 replaces the whole system.
2. Replacement priced at 100 percent of install cost, both countries. This
   supersedes the 70 percent Thailand ruling of 2026-09-09.
3. Vietnam moves to a 20-year horizon to match Thailand.
4. The PV inverter event (10 percent of solved PV capex, year 11) applies to
   Vietnam too.

On `model_degradation`: kept off. Verified in REopt.jl v0.57.0 source that the
storage O&M fraction is plain maintenance with no capacity-fade allowance, that
enabling degradation zeroes the replace_cost inputs the proforma reads, returns
the maintenance cost as one present value rather than a yearly series, and
never feeds SOH back into dispatch. A throwaway probe was run instead (below).

## What changed in the code

- `proforma_vietnam/defaults/__init__.py`: five policy constants
  (`PROJECT_YEARS` 20, `BESS_REPLACEMENT_YEAR` 10,
  `BESS_REPLACE_FRACTION_OF_INSTALL` 1.0, `PV_INVERTER_REPLACEMENT_YEAR` 11,
  `PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX` 0.10) and an import-time
  guard on `vietnam_defaults.json project_years` (now 20).
- `proforma_thailand/defaults/`: `bess_replace_cost` 100/150; coupling uses
  the policy fraction; `project_years` and the two `pv_inverter_*` entries
  (renamed from `inverter_*`) asserted equal to the policy at import.
- `proforma_vietnam/case_builder.py`: `_apply_replacement_policy` derives
  replace costs from the install price actually sent and sets both REopt
  replacement years; `analysis_years` defaults to `FINANCIAL_DEFAULTS["project_years"]`
  (the literal 25 is gone); what was sent is recorded in assumptions
  (`battery_replacement_year`, `bess_replace_cost_per_kw/kwh`,
  `pv_inverter_replacement_year`, `pv_inverter_replacement_fraction_of_pv_capex`).
- `proforma_thailand/case_builder.py`: same derivation and record.
- `proforma_vietnam/esco_pro_forma.py`: `_pv_inverter_replacement` books the
  PV inverter event in the shared core from `pv_inverter_replacement_year` and
  `_fraction_of_pv_capex`; result carries
  `derivation["pv_inverter_replacement"] = {year, fraction, cost_usd}`.
- `proforma_thailand/report.py`: local derivation deleted; passes the two keys.
  `run_dppa_negotiation_sweep.cash_flow_overrides_from_assumptions`,
  `run_case.VIETNAM_REPORT_QUERY_KEYS` and `reoptjl/views.py` map them.
- `proforma_vietnam/audit_sheets.py`: Replacement Policy section on
  Assumptions; storage PCS row named "Storage inverter (PCS) replacement year";
  audit replacement row "Equipment replacement (engine schedule)" for both
  countries; Model Basis horizon and replacement bullet from data.
- Eight Vietnam `case.json` files dropped `analysis_years` and the storage
  replacement keys; all fourteen `payload.json`/`assumptions.json` regenerated
  by dry run (Thailand 1-4 payloads identical; 5-6 replacement keys only;
  Vietnam horizon and replacement only).
- Docs: `CASE_JSON_INPUT_GUIDE.md`, `ESCO_CONTRACT_MODEL_DESIGN.md`, a dated
  note in `MODEL_AUDIT.md`.

Tests: Thailand 143, Vietnam 551, tariff 14, all green; gate TOTAL DIFFS 0 on
all fourteen after re-baselining. Before the re-solve, a gate check of the six
Thailand cases rebuilt from the regenerated records against the pre-change
baselines gave 0 numeric diffs, which proves the core PV inverter derivation
reproduces the old report-layer figure exactly.

## Reconcile, old (pre-change workbooks at `cafedbad`) against new

Ten cases re-solved (8 Vietnam, Thailand 5 and 6); Thailand 1 to 4 rebuilt
only and unchanged to the cent.

| case | PV kW | BESS kW / kWh | Equity IRR old -> new | Equity NPV old -> new | Capex old -> new | Min DSCR old -> new | Avg DSCR old -> new |
|---|---|---|---|---|---|---|---|
| rofu case_1 | 1,685 | 0 / 0 | 66.4% -> 66.4% | 1,304,997 -> 1,304,997 | 842,500 -> 842,500 | 2.86 -> 2.86 | 3.04 -> 3.04 |
| rofu case_2 | 1,895 | 0 / 0 | 64.5% -> 64.5% | 1,415,588 -> 1,415,588 | 947,500 -> 947,500 | 2.79 -> 2.79 | 2.98 -> 2.98 |
| rofu case_3 | 2,106 | 0 / 0 | 62.2% -> 62.2% | 1,506,642 -> 1,506,642 | 1,053,000 -> 1,053,000 | 2.72 -> 2.72 | 2.90 -> 2.90 |
| rofu case_4 | 2,549 | 0 / 0 | 56.1% -> 56.1% | 1,610,103 -> 1,610,103 | 1,274,321 -> 1,274,321 | 2.51 -> 2.51 | 2.69 -> 2.69 |
| rofu case_5 | 1,685 | 222 / 367 | 63.8% -> 64.2% | 1,363,615 -> 1,353,566 | 930,596 -> 919,716 | 2.37 -> 2.21 | 2.89 -> 2.89 |
| rofu case_6 | 2,847 | 507 / 1,881 | 47.8% -> 49.6% | 1,922,690 -> 1,855,912 | 1,892,524 -> 1,756,407 | 0.93 -> 0.64 | 2.28 -> 2.31 |
| factory_a case_1 | 4,568 | 1,452 / 5,679 | 16.7% -> 16.5% | 1,293,942 -> 773,960 | 3,773,743 -> 2,990,365 | 1.15 -> -0.92 | 1.32 -> 1.15 |
| factory_a case_2 | 5,448 | 1,611 / 9,461 | 14.6% -> 11.6% | 1,032,758 -> 262,548 | 4,295,753 -> 3,879,459 | 1.07 -> -1.68 | 1.23 -> 0.91 |
| factory_a case_3 | 4,649 | 1,258 / 7,822 | 10.7% -> 8.7% | 174,522 -> -177,968 | 4,385,448 -> 3,270,852 | 0.87 -> -1.74 | 1.03 -> 0.78 |
| factory_a case_4 | 3,243 | 0 / 0 | 18.9% -> 16.8% | 768,034 -> 440,925 | 1,657,573 -> 1,556,758 | 1.19 -> 1.17 | 1.35 -> 1.33 |
| factory_a case_5 | 5,448 | 1,611 / 9,461 | 16.3% -> 14.8% | 1,412,732 -> 759,543 | 4,295,753 -> 3,879,459 | 1.12 -> -1.51 | 1.31 -> 1.04 |
| factory_a case_6 | 5,914 | 592 / 1,184 | 26.7% -> 25.7% | 2,505,981 -> 1,929,382 | 3,028,160 -> 3,028,160 | 1.48 -> 1.38 | 1.71 -> 1.65 |
| bess_arbitrage_5mw | 0 | 5,000 / 25,000 | 56.4% -> 54.3% | 4,606,891 -> 3,436,606 | 3,400,000 -> 3,400,000 | 2.42 -> -6.13 | 2.79 -> 1.86 |
| bess_arbitrage_5mw_mfg | 0 | 5,000 / 25,000 | 27.1% -> 18.1% | 1,798,483 -> 578,999 | 3,400,000 -> 3,400,000 | 1.52 -> -7.29 | 1.78 -> 0.86 |

Three drivers act at once on Vietnam: five fewer years of revenue, a
full-price whole-system replacement instead of 80/100 USD, and the new PV
inverter event. The optimiser shrank most Vietnam systems in response
(case_1 PV 5,421 to 4,568 kW, BESS 8,640 to 5,679 kWh). Vietnam case_3 NPV
is now negative.

**The finding that matters most.** The year-10 replacement now falls inside
the 10-year debt term. The previous year-11 schedule sat one year outside it,
which is why minimum DSCR looked fine before. With a large battery the
year-10 cash outflow exceeds that year's operating cash and the minimum DSCR
in debt years goes negative (Vietnam) or to 0.64 (Thailand case 6). The model
books the replacement as an operating outflow with no reserve and no
debt-sizing response, deliberately, so the raw effect is visible. The memo
tells Keen a lender would expect a replacement reserve built in years 1 to 9
or a tenor ending before year 10. For Vietnam the same disclosure is owed in
whatever narrative next quotes these workbooks.

## Thailand storage outcome at 100 percent

Storage survives in both cases: 222 kW / 367 kWh alongside the roof-limited
array (was 238 / 429 at 70 percent) and 507 kW / 1,881 kWh with PV 2,847 kW
when the roof is relaxed (was 575 / 2,378 with PV 2,957). Conclusion held at
three price points; the memo calls it settled.

## SOH check (throwaway, scratchpad only)

Kept solves re-run against the Julia server with `model_degradation: true`,
augmentation strategy, sizes pinned. Under NREL's laboratory default
coefficients: Thailand case_6 SOH 0.959 at year 20, never below 0.8,
augmentation present value 3,943 USD against 117,239 USD for our year-10
event; Vietnam bess_arbitrage_5mw SOH 0.823 at year 20, never below 0.8,
230,802 USD against 1,310,847 USD. The year-10 whole-system replacement is
conservative against REopt's own fade model by a wide margin. Caveats: no LFP
or 30 degree calibration; REopt scales daily fade by hours per time step, so
the 15-minute Thailand run shows a quarter of the fade the same duty would
show hourly (a units artefact, the hourly Vietnam row is the fairer one); SOH
never reduces delivered energy. Recorded in the memo's technical basis.

## Deliverables reissued

`KEEN_THAILAND_MEMO.md` (12 September 2026), `KEEN_THAILAND_MEMO_VI.md`
(figures machine-checked identical to EN: 56 large numbers, all
percentages), `Rofu_Thailand_Tariff_Structure_Internal.pptx` slides 8 and
10, HTML artifact redeployed at the same URL. Every memo figure traced to
`memo_figures.json` pulled from the six new workbooks; no em dash anywhere.

## What did not change

- Thailand 1 to 4 solver results and workbooks: payloads identical, figures
  identical to the cent.
- The Vietnam DPPA residual (register item 15).
- The API query mapping gaps beyond the two new keys (item 19 below).

## Housekeeping

- Two superseded workbooks were locked by another process (open in Excel?)
  and could not be deleted: `outputs/vietnam_case/factory_a/case_6/vietnam_report_5b999b24-d8c1-4d91-aa2e-1ea0a973af38.xlsx`
  and `outputs/thailand_case/rofu_thailand/case_6/thailand_report_fa6aa4e5-7c38-42d3-9186-3453f4477dce.xlsx`.
  They are untracked now; close them and delete from disk. They are the OLD
  figures, not the current ones.
- The user's `vietnam_report_review*.xlsx` files were not touched and are
  now three changes stale (levelization, horizon, replacement).
- `baseline_workbooks/` regenerated locally (gitignored, never committed).
- Docker stack up; Julia healthy.

## Follow-ups (register items 17 and 18 closed; new item 19)

- Vietnam narrative deliverables (register item 1) are now stale on three
  axes and Vietnam case_3 has flipped to a negative NPV; the year-10 DSCR
  point needs its own paragraph in whatever next quotes them.
- Item 19: `reoptjl/views.py` query mapping lacks `direct_ownership`,
  `contract_years`, the VAT keys and `surplus_export`, so a solve-time
  workbook for such a case differs from the rebuilt one; the rebuilt one is
  canonical. Size: an hour to add the keys and a test that the two paths
  agree on one case.
- The PV inverter is capitalised under the BESS depreciation class (8 years
  Vietnam, 5 Thailand) because the merged series is one series. Permissible;
  a separate PV-class schedule is a refinement.
- A replacement reserve or a debt-sizing response to the year-10 event is a
  modelling gap now that the event sits inside the debt term (see above).
  Size: half a day, needs a ruling on the reserve convention first.
  2026-09-12 second handoff: conditional. The default policy no longer schedules a
  replacement (see the handoff above); this applies only to a case that
  opts in through technologies.storage.replacement.
- Gate still keys baselines by filename (item 8); tripped again this pass
  and handled by regenerating.

# 2026-09-11 - Follow-up register from the Thailand adaptation

Answers three questions asked at close: does Vietnam need re-running, what
defects did the Thailand work expose in the shared codebase, and how should the
repository be pushed. Each open item below is a task; each is sized.

## Does Vietnam need re-running? Two different answers

**Re-SOLVE (REopt/Julia): NO.** Verified against git: no commit since the
merge-base touched `outputs/vietnam_case/**/{case,payload,results}.json`, and
the only `case_builder.py` change (`a62ac7d3`, resolution-aware CSV reader) was
proven byte-identical for Vietnam by the gate throughout. The saved Vietnam
`results.json` files are still exactly what the solver would return.

**Re-BUILD (workbook from saved results): YES, and it is now done.** The six
`factory_a` workbooks committed under `outputs/vietnam_case/` were built by the
OLD proforma and carried the levelization double count. Measured before the
rebuild: every one understated savings by exactly `1/lambda = 1.049463`, e.g.
case_1 538,255 committed against 564,878 corrected. The two battery-only
arbitrage cases were correctly unchanged (no PV, lambda 1.0). All six were
rebuilt in place on 2026-09-11 with `proforma_vietnam.rebuild_report`; same
run uuid, same filename, so no stale duplicate.

Also stale but NOT touched, because they are the user's own untracked files:
.
They carry the old figures. Note for anyone verifying: a name-sorted glob
picks these over the uuid-named workbook, which is failure mode 8 from the
handoff and tripped the controller once during this very check. Select
workbooks by the run uuid in results.json, never by sort order.

**Still stale, NOT done, needs a decision:** the Vietnam narrative deliverables
were written against the old numbers and are now about 5 percent low on every
savings, NPV and IRR figure:
- `outputs/vietnam_case/factory_a/Factory_A_Solar_BESS_Case_Study.pptx`
- `outputs/vietnam_case/factory_a/Narrative_Session_4.3_VN.md`
- `outputs/vietnam_case/factory_a/SpeakerNotes_Session_4.3_VN.md`,
  `SpeakerNotes_Session_5.2_VN.md`
- `proforma_vietnam/MODEL_AUDIT.md` reconciliation figures, if any were pinned
- The CEBA training deck, if it quotes Factory A figures
Task: regenerate every number in these from the rebuilt workbooks. Do not edit
by hand; the previous Thailand memo shipped stale figures exactly that way.
Size: half a day. Owner: whoever presents them next.

## Defects found in the shared core during the Thailand work

### Fixed this session, in master

1. **Levelization double count, six sites.** REopt dispatch and tariff
   outputs are lifetime-weighted averages despite the `year_one_` prefix; the
   proforma applied `(1-deg)^y` on top. Fixed in `esco_pro_forma` (three
   `cash_flow_inputs` entries, the grid-CfD DPPA dispatch, surplus export),
   `report_data` (dispatch display, results comparison) and
   `emissions` (avoided tCO2e). Understated savings 4.1 percent (Thailand) and
   4.9 percent (Vietnam); emissions 3.6 percent. Every site was found by
   reconciling two figures that had to agree; tests and the gate were green
   through all six.
2. **No end-to-end test covered the de-levelization path.** Added, and each
   new guard was proven to fail on a reverted change.
3. **Coupled defaults stored as literals.** O&M at 1.5 percent of PV capex and
   BESS replacement at 70 percent of install now fail at import if desynced
   (`defaults/__init__._assert_couplings_hold`). Already caught one price change.
4. **Provenance mismatch.** An MDPI citation assuming 1 percent O&M stood as
   the source for a 1.5 percent value; demoted to a lower-bound note.
5. **Inverter cost derivation from solved capex was unguarded**, the exact path
   that broke once before via a nonexistent field. Now tested.
6. **Power factor status read as a technical finding** ("none required") when
   it was a client scoping choice. Reworded and returned as a dict.
7. **Three "Levelized Annual" labels went stale in the opposite direction**
   after the fix and were corrected; one was left until its data was fixed
   first, because changing a label ahead of its data produces a lie.

### Open, recorded as tasks

8. **Gate finds baselines by filename, and filenames carry the run uuid.**
   After any re-solve the gate raises `FileNotFoundError` on its own baselines.
   Content comparison is a manual step today. Task: key baselines by case
   name, not by workbook filename, in `compare_workbooks.rebuild_all_cases`.
   Size: an hour. Blocks: nothing, but every future re-solve trips on it.
9. **Gate is blind to number formats** (`values_only=True`). An FX cell once
   displayed 32.5 as "33" and the gate could not see it. Task: compare
   `number_format` alongside value for numeric cells. Size: an hour.
10. **Gate does not cover the input path.** `case_builder`, `pvwatts_client`
    and `validators` are outside it because it rebuilds from saved results.
    Task: a dry-run payload snapshot test per case. Size: half a day.
11. **`baseline_workbooks/` is gitignored scratch**, so the gate protects only
    within a session that generated baselines first. Deliberate design
    (`3a8e418a`), not a bug, but it means a fresh clone cannot run the gate.
    Task: document the regenerate step in the README, or decide to track them
    (133 MB). Size: decision, then an hour.
12. **"PV O&M cost, sent to REopt" row mislabels its source.** It claims
    `case.json` but `report.py` reads `FINANCIAL_DEFAULTS`. They agree only
    right after a re-solve. Task: read the value from the echoed payload, or
    relabel. Size: 30 minutes.
13. **Four unreachable ESCO discount-to-EVN strings** in
    `proforma_vietnam/audit_sheets.py` at 295, 1136, 2004, 2521, live only when
    the structure is neither DPPA, physical, nor direct ownership. Reported,
    not deleted, per CLAUDE.md. Size: 15 minutes if you want them gone.
14. **Em dash removal design (2026-07-09, section 1) is moot for current
    output** (0 cells in either country) but the two f-strings remain in
    source on branches no current case reaches. Task: close the design as
    done-by-circumstance or strip the strings. Size: 15 minutes.
15. **Vietnam DPPA residual.** Dividing DPPA savings by lambda over-corrects
    the storage-attributable share; bounded per case at 0.00 to 2.17 pp of the
    4.95 percent correction and recorded in `MODEL_AUDIT.md`. The exact fix is
    a second dispatch-only solve at fixed sizes with degradation zeroed. Task
    only if a Vietnam client challenges the DPPA figures. Size: a day.
16. **Thailand: power factor not computed** (site kVAR never requested, by
    client direction), **grid export not modelled** (no price available;
    curtailment runs 8.6 to 19.2 percent), **14 inputs provisional**. All
    disclosed in the memo. Tasks wait on Keen.
17. **Closed 2026-09-12, see the handoff above.** Vietnam books no PV inverter replacement; Thailand does. Found
    2026-09-11 on a client question. Thailand's `report.py` derives a year 11
    event at 10 percent of solved PV capex and passes it through
    `extra_replacement_costs_by_year`; Vietnam's builder never populates that
    hook, and its `inverter_replacement_year` is REopt's
    `ElectricStorage.inverter_replacement_year` (the BATTERY inverter, paid
    via `replace_cost_per_kw`), not the PV inverter. Vietnam PV O&M is 6
    USD/kW-yr (1.25 percent of 480) with no documented statement that it
    carries an inverter reserve, so the omission is real and unfunded.
    Measured in memory against the six factory_a runs (year 11, 10 percent of
    PV capex, no other change): equity IRR falls 0.4 to 0.5 pp, equity NPV
    falls 52 to 92 kUSD, project IRR 0.2 to 0.3 pp; case_3 NPV 174.5 to 85.0
    kUSD. Direction is one way (returns only go down), so the shipped Vietnam
    figures are optimistic on this axis. Task: add `inverter_replacement_year`
    and `inverter_replacement_fraction_of_pv_capex` to the Vietnam profile
    with a Vietnam source (or state in the O&M provenance that the 6 USD/kW
    reserve covers it), rebuild the six workbooks, re-baseline. This
    compounds item 1: the narrative decks then move twice. Size: half a day
    plus the deck refresh already listed.
18. **Closed 2026-09-12, see the handoff above.** Thailand Model Basis sheet says "25-year owner cash flow" in every
    shipped workbook while the Assumptions sheet says 20. The string is a
    literal in `proforma_vietnam/audit_sheets.py:2360`, not read from
    `project_years`; the Vietnam branch of the same conditional is also a
    literal 25. The neighbouring bullet (`audit_sheets.py:2405`) names only
    the battery replacement, though Thailand books an inverter event too.
    Task: format both from `project_years` and list both replacement events
    when `extra_replacement_costs_by_year` is present; rebuild the six
    Thailand workbooks (text-only change, gate should show exactly those
    cells). Size: an hour.

19. **API workbook query mapping lags the sweep helper** (`reoptjl/views.py`
    `_vietnam_proforma_overrides` vs `run_dppa_negotiation_sweep.cash_flow_overrides_from_assumptions`):
    `direct_ownership`, `contract_years`, `vat_rate_fraction`, `vat_refund_year`
    and `surplus_export` never reach the solve-time workbook, so it differs
    from the rebuilt one for any case using them. The rebuilt workbook is the
    canonical one. Task: add the keys and a test that the two paths agree on
    one case. Size: an hour.

## Repository: push as-is now, LFS forward-only later, never prune

Measured 2026-09-11:
- `.git` 562 MB. Largest files in HEAD are upstream REopt binaries under the
  untouchable `reo/` (`climate_cities.shp` 42 MB, `ssc.*` 15 to 18 MB each),
  already on origin. Largest of ours: `results.json` at 14 MB.
- **No file approaches the GitHub 100 MB hard limit.** The repo is under the
  1 GB soft limit with room.
- History holds 67 `results.json` blobs (336 MB) and 112 xlsx blobs (105 MB):
  about 440 MB of the 562 is repeated re-solves and rebuilds. Growth is about
  90 MB per full six-case re-solve.

**Push as-is now.** Nothing blocks it, and both alternatives rewrite history
and force-push, which breaks every other clone (Codex works this repo too).

**Do not prune.** Filter-repo would drop old `results.json` versions, and those
are the only record of pre-change behaviour: the baselines are gitignored by
design and the handoff explicitly points at git history for recovery. Pruning
destroys the reproducibility the gate design depends on.

**When size matters, use LFS forward-only, not a migration.** `git lfs track
"outputs/**/results.json" "outputs/**/*.xlsx"` then commit `.gitattributes`.
New versions go to LFS; old ones stay in ordinary history; no rewrite, no force
push. The GitHub free tier is 1 GB storage and 1 GB/month bandwidth, so a fresh
clone costs about 190 MB of bandwidth; that is five clones a month free, then
5 USD per 50 GB. Trigger point: about 800 MB in `.git`, roughly three more
full re-solves at the current rate.

# 2026-09-10 - Keen Thailand deliverable complete, merged to master

Branch `thailand-adaptation` merged to `master` by fast-forward, 97 commits,
NOT pushed. `origin/master` is 97 behind. Deliverables are in
`outputs/thailand_case/rofu_thailand/`.

## The one thing to know before touching this code

**REopt's dispatch and tariff outputs are LEVELIZED, despite `year_one_` in
their names.** The optimiser applies an escalation/discount/degradation weight
to PV production inside the solve, so every series and every bill it returns is
a lifetime-weighted average, not a first year. The proforma then applied
`(1 - deg)^y` on top, counting degradation twice.

This session found and fixed the defect in **six** separate places. Each was
found by comparing two figures that should have been equal, never by a test or
the gate, both of which stayed green through all six:

1. `esco_pro_forma._apply_de_levelization` - the three `cash_flow_inputs`
   quantities. Note it is the SAVINGS DELTA that scales by `1/lambda`, not the
   bill: BAU carries no PV and is a true first year.
2. `esco_pro_forma._apply_de_levelization_to_dispatch` - the grid-CfD DPPA
   settlement basis. Symptom that led here: Vietnam cases 5 and 6 moved by only
   2 cells when the others moved by 340+, because `cash_flow.py:271` zeroes
   `base_energy_revenue_vnd` for grid-CfD.
3. `esco_pro_forma._apply_surplus_export` - latent, no case enables it.
4. `report_data` dispatch series and `run_case.summarize_results` - the
   displayed figures, which had diverged from the corrected cash flow.
5. `report_data._results_comparison` - Technical Results reported 263279 of
   savings where Executive Summary reported 272717. Same quantity, two numbers,
   one workbook, and the client-facing sheet held the wrong one.
6. `emissions.annual_avoided_tco2e` - avoided emissions understated 3.6 percent.

`_apply_physical_dppa` was checked and is correct: it consumes the already
corrected `project_served_pv_kwh`.

Lambda is term-dependent: 0.960612 at 25 years, 0.965392 at 20. Do not hardcode
it; `_levelization_factor(pv_outputs)` derives it per case.

## Method that actually worked

Every defect this session came from reconciling two numbers that had to agree,
not from adding tests. When you change anything here, pick a quantity that
appears in two places and check it end to end. The suites and the gate are
necessary and they are not sufficient; they were green for all six.

## Gate limitations, now four

- `values_only=True`, so it is blind to number formats, fonts, widths, charts.
- It rebuilds from saved `results.json`, so `case_builder`, `pvwatts_client`
  and `validators` are outside its coverage.
- `baseline_workbooks/` is gitignored scratch (`.gitignore:139`, added in the
  same commit that created the gate). It has NEVER been tracked, so the gate
  protects only within a session that generated baselines first. Never
  `git add -f` it.
- **New:** it locates baselines by FILENAME, and filenames carry the run uuid.
  After any re-solve the gate cannot find its own baselines and raises
  FileNotFoundError. Comparing by content is a manual step today. Fixing this
  properly means separating baseline identity from filename.

## Client-confirmed inputs, 2026-09-09

PV 500 USD/kWp, project life 20 years, BESS 100 USD/kW + 150 USD/kWh,
replacement at 70 percent of install, discount rate 11 percent. O&M is coupled
at 1.5 percent of PV capex and `defaults/__init__._assert_couplings_hold()`
fails at IMPORT if a price change desyncs it. That guard has already earned its
place once. Power factor and grid connection are excluded from capex at client
direction, which is a scoping decision and is disclosed as one, not as a
finding that no mitigation is needed.

The 500 USD/kWp is roughly 19 percent below the bottom of every published Thai
benchmark located (Krungsri 615-769, MDPI 767). Returns scale directly off it,
so the memo states plainly that it is client-supplied rather than benchmarked.

## Results and the two conclusions

Six cases, all optimal. Storage is selected wherever permitted: 429 kWh at the
roof-limited size, 2378 kWh with the roof relaxed, neither at a bound.

**This REVERSES the previously shipped advice that storage never pays.** It
survived a deliberate robustness check: the cases were run at 475/25yr and at
500/20yr, the second worse for storage on both counts, and storage was selected
both times.

**The roof binds.** Unconstrained optimum 2549 kW against a most-generous roof
estimate of 2106 kW. Measuring the roof is the highest-value open item.

A claim that did NOT survive: at 475/25yr the transformer also bound and that
was reported to the user; at 500/20yr it does not. Only the roof is now called
a constraint.

## Open items

- **Repo size.** 112 MB under `outputs/thailand_case`, 76 MB under
  `outputs/vietnam_case`, both tracked. `baseline_workbooks/` is another 133 MB
  but gitignored. The gate rebuilds from those `results.json` files, so
  deleting them breaks it. This needs an LFS-or-prune decision, not a
  unilateral cleanup.
- **Dead code, reported not deleted** per CLAUDE.md: four unreachable ESCO
  discount-to-EVN strings in `audit_sheets.py` at lines 295, 1136, 2004, 2521.
  Reachable only when the structure is neither DPPA, physical, nor direct
  ownership.
- **Power factor** is still not computed; the site kVAR maximum was never
  requested, by client direction.
- **Grid export** is modelled as strictly prohibited. Curtailment runs 8.6
  percent at the roof-limited size and 19.2 percent at the unconstrained
  optimum. If export can be negotiated at any price, the optimal size rises
  again and the economics improve materially. No price was available to model.
- **Fourteen inputs remain provisional**, marked with the exact string
  `PLACEHOLDER - pending Keen confirmation`, matched by equality. Do not invent
  a variant.
- **Not pushed.** `origin/master` is 97 commits behind.

# 2026-09-08 - HANDOFF: Vietnam shared core and Thailand adaptation

Written for the next session picking this up cold. Branch `thailand-adaptation`
at `17059f80`, 41 commits for the Keen Thailand deliverable on top of 41 for the
earlier Thailand adaptation. Kept as a branch, not merged. Base is `master`,
merge-base `74a8b04c`.

## Orientation

`proforma_vietnam` IS the shared financial core. `proforma_thailand` drives the
same engine for a Thai factory (Rofu, Nakhon Ratchasima) that owns its rooftop
solar directly, rather than Vietnam's ESCO structure. There is deliberately no
`proforma_core` package and nothing was renamed: Vietnam-suffixed names carrying
Thailand values (`annual_om_vnd` holding THB, `evn_energy_escalation_rate`
holding a PEA rate) are by design, not debt. Do not "fix" them.

The client deliverable is `outputs/thailand_case/rofu_thailand/`: a memo plus
six case directories, each with `case.json`, `payload.json`, `assumptions.json`,
`results.json`, `summary.json` and one workbook.

## Verification: run all four before and after any change

```
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
./.venv/Scripts/python.exe -m unittest reoptjl.test.test_thailand_tariff -v
./.venv/Scripts/python.exe -c "
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases, compare_workbooks
built = rebuild_all_cases('.', 'gate_check')
bad = 0
for name, path in built.items():
    diffs = compare_workbooks('baseline_workbooks/%s/%s' % (name, path.name), path)
    print(name, 'OK' if not diffs else diffs[:3])
    bad += len(diffs)
print('TOTAL DIFFS', bad)
raise SystemExit(1 if bad else 0)
"
```

Last known green: Thailand 124/124, Vietnam 509/509, tariff 14/14, gate
TOTAL DIFFS 0. Delete the scratch `gate_check/` afterwards; never commit it.

The tariff suite lives under `reoptjl/` but needs no Django, so it runs on the
venv. Useful when Docker is down.

## Hard constraints

- Never create, modify, regenerate or delete anything under `reo/` (deprecated
  V1/V2, returns 410), `outputs/vietnam_case/`, or `baseline_workbooks/`.
- **Vietnam's generated Excel output must not change.** Every change to
  `proforma_vietnam` must be an additive keyword argument defaulting to today's
  behaviour, or a `CountryProfile` field defaulting to Vietnam's current value.
  The gate proves it.
- No em dash in generated report output.
- `./.venv/Scripts/python.exe` has NO Django. Django work runs inside the
  `reopt_api-django-1` container.
- Never modify the client source `.xlsm` files under the Keen Project folder.

## Recurring failure modes on this branch, all of which actually happened

Hunt for further instances of each. Two reached client documents twice.

1. A field read that does not exist on the object, so a feature is a silent
   no-op. (`initial_capital_cost` on PV outputs; `pv_degradation_rate` in
   Thailand assumptions. Both made whole features inert while tests stayed green.)
2. A test that passes identically with and without the feature it names.
3. A test fixture drifting from production, so the suite exercises a path
   production never takes and hides a Critical.
4. A fix applied to one render site while an identical second goes unnoticed.
   Three separate instances.
5. A value rendered correctly under a label that misleads the reader.
6. Vietnamese identity or ESCO language leaking onto a Thai client document.
7. A guard present but not wired to production, or narrowed until it passes.
8. A stale artifact read as current (name-sorted globbing picking an old
   workbook; a cached fixture predating the fixes made for it).

## Shared core (`proforma_vietnam`) - open items

**Degradation is counted roughly twice. Deliberately left in place.**
REopt reports dispatch and bills LEVELIZED: `year_one_energy_produced_kwh` is
raw PVWatts times size, while `annual_energy_produced_kwh` carries a
levelization factor of about 0.9606 derived from escalation, discount,
degradation and term. `electric_to_load_series_kw` and `year_one_bill_before_tax`
carry it too. The proforma then applies `(1 - degradation)^y` on top of that
already-averaged base. Net effect: savings understated by about 4 percent, so
NPV, IRR and lifetime avoided emissions are all understated. It errs in the
client's favour. It was NOT fixed because the behaviour is shared with Vietnam
and changing it breaks the byte-identical guarantee. Fixing it properly means
deciding whether the proforma should stop applying degradation on top of REopt's
levelized base, then re-baselining Vietnam. That is its own piece of work.

**"Year 1" labels are only partly corrected.** Three occurrences were relabelled
"levelized annual" (Technical Results section headers, the avoided-emissions
row). Executive Summary, Buyer Analysis and Year 1 Snapshot rows carry the same
levelization quirk under an unrelabelled "Year 1" name. Cosmetic, consistent
direction, but a reader comparing sheets will notice.

**The regression gate has three blind spots.** It is necessary, not sufficient.
- `compare_workbooks` reads cells with `values_only=True`, so it compares cell
  text and formulas but is blind to number formats, fonts, fills, widths, merged
  ranges, defined names and charts. A styling change must be verified by reading
  the built workbook directly. This already mattered once: the FX cell's
  `number_format` displayed 32.5 as "33" and the gate could not see it.
- `baseline_workbooks/` holds only Vietnam cases, so **Thailand behaviour has
  zero gate protection**. Every Thailand guarantee rests on the unit suites
  alone, which is how two Criticals reached six client workbooks past a green run.
- The gate rebuilds from saved `results.json`, so `case_builder.py`,
  `pvwatts_client.py` and `validators.py` are outside its coverage entirely.

**`_unmasked()` strips `ALLOWED_SUBSTRINGS` case-sensitively** where the older
check was case-insensitive. Harmless today because all entries render lowercase;
it would produce a false positive, not a false negative, if that changed.

**The Important 7 fix is not profile-gated.** The coincident-peak demand read is
a field-read gap rather than a country-specific behaviour, verified empirically
that all eight Vietnam baseline cases carry the field at 0.0. If a future Vietnam
case ever populates `year_one_coincident_peak_cost_before_tax`, revisit.

**Private helpers now cross module boundaries.** `proforma_thailand/report.py`
imports `_pv_capex` and `_storage_capex` from `esco_pro_forma`. This is
deliberate: the engine uses `_pv_capex` for `pv_capex_vnd`, the depreciation
basis, and Thailand's insurance and inverter-replacement bases must not diverge
from it. Do not promote or rename them without updating both callers.

## Thailand (`proforma_thailand`) - open items

- **19 of 24 cost inputs are provisional**, marked with the exact string
  `PLACEHOLDER - pending Keen confirmation`. That string is matched by exact
  equality in `placeholder_keys()` and by a production guard. Do not invent a
  variant; that mistake was made once and had to be undone.
- **Power factor is not computed.** It needs the site's monthly kVAR maximum,
  which Keen has not supplied. Every case reports 0 kVAR and 0 mitigation cost,
  with the status string saying "not computed", not "none required".
- **`annual_om_per_kw` is coupled to `pv_installed_cost_per_kw`** (1 percent of
  capex) but stored as a static literal, so a future capex change silently
  desyncs it. The coupling is disclosed in the JSON note and the research note.
- **`debt_interest_rate` uses MLR directly.** Real project debt prices at a
  spread to MLR. Correct rate class and currency; conservative end taken.
- **One inverter replacement in 25 years**, booked at year 11 with nothing near
  year 22, so the array runs on 14-year-old inverters for the back half. Present
  value of a second is roughly 12k USD.
- **`grid_connection_cost` (308 USD) is disclosed but never enters capex.**
  "Other capex" is 0 in all six cases. Immaterial in size, wrong in principle.
- **REopt rounds PV cost parameters to whole dollars.** O&M is sourced at 7.50
  USD/kWp-yr and sent as 7.5, but the model applies 8.00. This is now disclosed
  in both memo and workbook and pinned by a test asserting the RETURNED value.
  Any fractional PV cost parameter will behave the same way.
- **`proforma_thailand/cases/rts/` and `rts_bess/` are superseded fixtures**
  predating the corrected fuel adjustment. Their tests pass and they are not the
  deliverable; do not read them as current results.
- **No end-to-end test derives the inverter cost from solved PV capex.** Every
  inverter test injects the cost explicitly. The derivation in `report.py` is the
  exact thing that broke once (`initial_capital_cost` on PV outputs) and is
  currently unguarded.

## Deliverable - what a client would act on

- **PV pins at the roof cap in cases 1 to 3.** Case 4 removed the roof limit and
  the optimizer chose about 2,193 kW, ABOVE even the most generous roof estimate
  of 2,106 kW. The roof binds across the whole plausible range, so confirming the
  actual usable roof is the highest-value open item. Roof band derives from the
  site survey: 5 roofs, 108 m long, widths recorded 24 m to 30 m, times 0.65
  usable, times 0.20 kW/m2.
- **Storage does not pay.** Given freedom to 4,000 kW / 16,000 kWh the optimizer
  built zero at the roof-limited size and a token 38.68 kW when PV was oversized.
  Any contractor proposal quoting a battery should be read against that.
- **Never quote REopt's emissions outputs.** AVERT, Cambium and EASIUR are US
  datasets with no Thailand coverage and every emissions output is zero. The
  Scope 2 figure is an Allotrope calculation from avoided grid import at the TGO
  factor 0.4750 kg CO2e/kWh (2022-2024 vintage, CFO Scope 2 grid-mix average,
  effective 1 Jan 2026). A test injects a sentinel to prove the REopt fields stay
  out of the workbook.
- **The memo headline groups four no-storage cases with two storage cases.** A
  reader skimming only the headline must hold that grouping in mind.
- ERC generation licence and Aor.6 permit are required but excluded from capex,
  having no public fee schedule. EIA and IEE are genuinely NOT required below
  5 MWp, so their zero is a finding rather than a gap.

## Tests and repo hygiene

- `test_assumptions_list_the_active_placeholders` is effectively tautological; it
  compares `sorted(placeholder_keys())` to the same call. Set correctness is
  covered independently by the enumeration test, so no coverage gap results.
- `RofuCaseTreeTests` reads raw `case.json` only and never calls
  `build_thailand_case`, despite a docstring implying otherwise.
- Minor style items: a tilt default expression computed twice in
  `case_builder.py`; a test helper treating `storage={}` as `storage=None`;
  `if extra_replacement_costs:` versus `is not None` in `esco_pro_forma.py`;
  `GATE_PREPARED_ON` now defence-in-depth rather than load-bearing.
- Two dead "ESCO discount-to-EVN" fallback strings remain in `audit_sheets.py`,
  unreachable for direct ownership (they fire only when the structure is neither
  DPPA, physical, nor direct ownership).
- **About 102 MB is now committed under `outputs/thailand_case/`** (87 MB of
  `results.json` plus workbooks), on top of 66 MB under `outputs/vietnam_case/`.
  Precedented by convention but not sustainable. Worth an LFS or pruning
  decision before more cases accumulate.

## Where the reasoning lives

- Spec: `docs/superpowers/specs/2026-09-05-keen-thailand-deliverable-design.md`
- Plan: `docs/superpowers/plans/2026-09-05-keen-thailand-deliverable.md`
- Earlier Thailand adaptation: the `2026-09-04-thailand-adaptation` spec and plan
- Research: `docs/superpowers/notes/2026-09-05-thailand-cost-benchmarks.md`,
  `2026-09-04-thai-depreciation.md`, `2026-09-04-coincident-peak-spike.md`
- Client memo: `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md`
- Case input reference: `outputs/thailand_case/rofu_thailand/CASE_JSON_INPUT_GUIDE.md`

The SDD execution ledger for this plan was deleted at handover per process; git
history is the record. 28 controller rulings were reported to the user in session
rather than committed, the load-bearing ones being: the discount rate stays
provisional because 11.5 percent is a third-party developer's cost of equity and
not a self-investing factory's hurdle rate; the degradation double-count is
labels-only by decision; and the storage ceilings were raised before running so a
binding bound could not decide the storage answer.

# 2026-09-08 - Rofu Thailand current-tariff briefing

- Reviewed the Gmail threads `Re: [EXTERNAL] Rofu Thailand - Hourly Data Request Letter of Authorization` and `Keen Thailand tool-related data` for project context. The factory is supplied directly by PEA Phimai; KEEN is evaluating rooftop solar and solar plus BESS. The latest site feedback says some roofs may require reinforcement and recommends an on-site structural assessment.
- Reviewed the internal KEEN project folder, including the PEA tariff summary, 2025 invoices, interval/load workbooks, site data, and the existing Allotrope KEEN clean-energy deck used as the visual reference.
- Created `outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx`, a ten-slide English internal briefing for an audience new to Thailand's electricity market.
- Tariff basis presented: PEA Schedule 4.2 Large General Service, 22-33 kV, rate code 4224; peak energy THB 4.1839/kWh; off-peak and holiday energy THB 2.6037/kWh; on-peak maximum-demand charge THB 132.93/kW-month; service THB 312.24/month; Ft on all kWh; VAT 7%; conditional power-factor charge disclosed but not quantified.
- June 2025 invoice example reconciles to the billed amount due of THB 2,576,311.21 using the invoice-rounded base, Ft, and VAT values. The slide displays whole-baht amounts and the invoice total of THB 2,576,311.
- Existing corrected model outputs were quoted without rerunning the model: conservative roof PV+BESS case 1,685 kWp PV, no battery, 30.7% grid offset; unconstrained PV+BESS case 2,203.2 kWp PV, 38.68 kW / 58.03 kWh BESS, 37.8% grid offset; incremental BESS effect approximately 0.3 percentage points versus the comparable PV-only case.
- Validation: finalizer package integrity passed; first-party Artifact Tool import passed; layout checker reported 0 findings and 0 warnings; PPTX contains 10 slide XML parts and 10 speaker-note parts; all 10 final slides rendered and were visually inspected. Final SHA-256: `A6F960A70126A1EEEDF1A891A43026C5132E9D4E5E843922F7B823E20F9D2B6A`.
- No model rerun, tariff refresh, email reply, or external posting was performed.
- Pre-existing untracked Vietnam review workbooks were preserved outside the topic commit.

# 2026-07-04 (later) - Workbook reorganisation: full case inputs, consolidated sheets, dispatch upgrade

- User goal (session /goal #2): (I) surface ALL case inputs (case.json +
  assumptions.json + contract terms) in the workbook, (II) consolidate the old
  data sheets and drop what the new sheets already carry, (III) keep Dispatch
  Profile / Load Duration separate; add original-PV-generation, hourly
  irradiation, grid→storage and PV→storage columns to Dispatch; chart one week
  only.
- **(I) Assumptions completeness.** `rebuild_report` now loads `case.json` and
  passes it as `assumptions["case_config"]`; `audit_sheets` renders new curated
  groups — Site & Load Profile, PV Technology (incl. PVWatts overrides),
  Storage Technology (full cost/replacement terms, can_grid_charge) — plus
  tariff currency/two-component-pilot rows, grid-charging flag, DPPA
  allocation δ and FMP series path (the old DPPA Configuration sheet is now
  fully covered here). A final "Other Assumptions (assumptions.json echo)"
  group prints any scalar key not shown in a curated group, so nothing can be
  silently dropped (`CURATED_ASSUMPTION_KEYS`).
- **(II) Sheet consolidation.** Removed the duplicated per-year record sheets
  (Summary, System Sizing, Results Comparison, Annual Production, Cash Flow,
  Tax Schedule, Debt Service, Developer Financials, DPPA Configuration, DPPA
  Annual Summary) — all their data lives on Pro Forma (Audit)/Assumptions/
  Executive Summary. New compact "Technical Results" sheet = System Sizing +
  Annual Energy Balance (+ PV-to-Grid row, bar chart) + Year-1 Bill
  Comparison. ESCO workbook: 18 → 11 sheets; DPPA: 23 → 14 (Year 1 BAU vs
  DPPA, Monthly & Hourly Settlement kept — VND-native). proforma_schema views
  stay as the guarded registry; SCHEMA.md notes they are no longer rendered
  as standalone sheets.
- **(III) Dispatch upgrade.** report_data dispatch rows now carry:
  pv_production_factor (PVWatts kWh/kW series from results inputs/outputs —
  the hourly irradiation proxy; REopt does not persist raw irradiance),
  pv_total_kw (original generation = to_load+to_storage+to_grid+curtailed),
  pv_to_storage_kw, pv_to_grid_kw, pv_curtailed_kw, grid_to_storage_kw
  (replacing the combined storage_charge_kw). Dedicated `_write_dispatch_sheet`
  renders 11 columns and charts only the week containing the annual peak load
  (168 h, titled with the hour range) with 4 selected series instead of the
  full 8760-hour all-column chart.
- **Validation.** 128 tests green (2 tests covering dropped sheets removed;
  new Technical Results + dispatch-chart tests added; rebuild test now also
  asserts the case.json groups). Regenerated workbooks and Excel-COM-verified
  (read-only) 5 of 6 cases: 9/9 + 4/4 checks PASS, "ALL CHECKS PASS", new
  dispatch columns and case.json groups present. **case_3 could not be
  regenerated — its workbook was open in the user's Excel (file lock)**; rerun
  `python -m proforma_vietnam.rebuild_report --case-dir
  outputs/vietnam_case/factory_a/case_3` after closing it.
- Files: report_data.py, xlsx_builder.py, audit_sheets.py, rebuild_report.py,
  SCHEMA.md, MODEL_AUDIT.md + tests (report_data, xlsx_builder,
  rebuild_report). Uncommitted.

# 2026-07-04 - Model-audit pass + third-party-ready Excel (audit sheets, FX, currency fix)

- User goal (session /goal): audit the whole model for realism, make it pass an
  independent top-tier consulting-firm review, and rebuild the Excel output as a
  complete investor/lender deliverable — engine outputs may be hardcoded, but
  everything derivable must be a live Excel formula (SAM as reference).
- **Currency question resolved (`_add_usd_aliases`).** Traced the pipeline: the
  engine computes in USD end-to-end (EVN tariff converted VND→USD at 25,000
  before REopt; `esco_pro_forma._money()` normalizes everything incl. DPPA VND
  primitives; `cash_flow_overrides_from_assumptions` maps `pv_capex_usd` →
  `pv_capex_vnd`). The `_vnd` keys were misnomers holding USD. Fix:
  `calculate_vietnam_esco_cash_flow(..., exchange_rate_vnd_per_usd=)` +
  `_finalize_currencies` — `_usd` keeps the computed value, `_vnd` is restated
  at the fixed rate (true VND). No rate → legacy aliasing (reference tests
  unchanged). `esco_pro_forma` passes the rate through; summary sums now read
  `_usd` keys. Verified `npv_vnd/npv_usd == 25000` on all six cases and USD
  headline metrics identical to the 2026-06-24 baseline table.
- **`report_data._results_comparison` keys renamed `_vnd`→`_usd`** (they hold
  REopt USD outputs). Fixed the Year-1 BAU-vs-DPPA `q_adj` fallback that used
  hardcoded `1.026 × 1.027263` (k×K_pp — contradicting "quantity uses K_pp
  only"); now uses configured K_pp.
- **New `proforma_vietnam/audit_sheets.py`** + reworked workbook flow: Cover
  (contents, colour legend, live overall status) → Executive Summary →
  Assumptions (grouped, unit + source, ~36 workbook-scope named cells; year-1
  engine bases exposed as shaded inputs) → Model Basis (methodology +
  simplifications register + validation guide) → **Pro Forma (Audit)** (SAM
  layout: line items down, Year 0..25 across; every white cell a live Excel
  formula incl. debt annuity, straight-line depreciation, CIT incentive clock
  and a fully-visible FIFO 5-year loss-carryforward schedule, IRR/NPV/MIN-DSCR/
  payback as Excel functions; hardcoded only: year-1 dispatch/settlement bases,
  replacement schedule, engine tie-out rows; per-year + per-metric PASS/REVIEW
  checks) → **FX Sensitivity** (editable VND-depreciation scenarios, live IRR/
  NPV, engine check columns) → existing sheets as record-copy appendix.
  `cash_flow` now also emits a `derivation` block (authoritative input echo +
  year-1 bases) and `calculate_fx_sensitivity()`.
- **Two Excel-corruption bugs found via COM bisect** (Excel refused to open,
  repair failed): (1) empty-string cells serialize as `<c t="inlineStr"/>`
  with no `<is>` child — never write "" (guards added); (2) prose source
  strings starting with "=" ("= PV + BESS + Other") become invalid formulas.
  Both guarded by a regression test that scans every cell of a built workbook.
- **Validation.** 130 unittests green (13 new: currency finalization,
  derivation, FX sensitivity, audit-sheet structure/tie-out/corruption guards).
  Regenerated all six Factory A workbooks offline (`rebuild_report`, run_uuid
  now stamped on Cover/Assumptions) and ran a full Excel COM recalculation on
  each: **9/9 pro-forma checks + 4/4 FX checks PASS on every case, cover
  status "ALL CHECKS PASS", per-year max |Excel−engine| = 0.0000 USD** —
  including the DPPA cases 5/6 (C_DN/C_BL degradation repurchase, CfD strike
  vs fee escalation all reproduce the engine).
- **Docs.** New `proforma_vietnam/MODEL_AUDIT.md` (audit pack: deliverable
  inventory, self-audit mechanics, currency resolution, code-vs-doc
  cross-check table, simplifications register, coverage). Fixed
  ESCO_CONTRACT_MODEL_DESIGN.md internal inconsistency (strike escalation
  "Default 0" → 0.04, matching code and its own New Inputs table).
- Tests/checks run: full unittest suite (130 OK), Excel COM recalc on 6
  workbooks (all PASS), engine-vs-baseline tie-out of the Honest Economics
  table (identical).
- Not committed this session (no commit requested). Open follow-ups unchanged:
  case_6 financing sensitivity at 1,300 VND/kWh strikes; wire real
  `direct_ownership`; move `evn_rates.py` tables to versioned defaults.

# 2026-06-24 (later) - E2E Re-run of Factory A case_1..6 (post schema refactor)

- User goal: archive the prior run's artifacts for the six Factory A cases, then
  re-run case_1..6 end-to-end against REopt (Docker now available), validating the
  schema-refactor outputs as a confirmation gate.
- **Archive.** Moved each case's generated artifacts (`payload.json`,
  `assumptions.json`, `results.json`, `vietnam_report_*.xlsx`) into
  `outputs/vietnam_case/factory_a/_archive/pre_rerun_2026-06-24/<case>/` with a
  `MANIFEST.txt`. Left each `case.json` input in place (it drives the re-run), so
  no stale workbooks remain to confuse reconciliation.
- **Stack.** `docker compose up -d` brought up redis/db/celery/django/julia. Django
  reachable (HTTP 405 on `/v3/job/health/` = GET not allowed, server up); Julia
  healthy (HTTP 200, already solving). Ran each case via
  `REOPT_API_URL=http://localhost:8000/v3 .venv/Scripts/python.exe -m
  proforma_vietnam.run_case --case <case.json>`.
- **Result.** All 6 returned status `optimal`, one fresh workbook each (no
  duplicates). New run UUIDs: case_1 `3dd5bf1f-fa51-4f1e-aa64-d24ae11a1820`,
  case_2 `554ee85a-6f3c-4077-8dcb-0145406d4e6e`, case_3
  `b33f4a1f-9de5-4228-ba55-4db9578de73a`, case_4
  `36f36f61-c28e-4c8a-bc9d-66f21300c28e`, case_5
  `c73574b2-1170-4611-a6c8-8a012bd1f50d`, case_6
  `5b999b24-d8c1-4d91-aa2e-1ea0a973af38`.
- **Reconciliation finding — REopt sizing not bit-reproducible vs June baseline.**
  Verified new vs archived `payload.json`: cases 1-4 byte-identical; cases 5-6
  differ only in `ElectricStorage.battery_replacement_year` 10→11 (current
  `case.json` edited Jun 11, after the Jun-10 baseline payload — expected, not a
  re-run artifact). Despite identical payloads, cases 1/2/3/5 re-solved to slightly
  larger PV+BESS (e.g. case_1 BESS 8,640 vs 8,250 kWh, +4.7%); constrained cases 4
  (PV-only) and 6 (fixed BESS) matched exactly. Conclusion: drift is in the REopt
  solver/Julia-package layer, not the proforma — the schema refactor stays
  byte-identical given the same `results.json`. Headline economics moved only
  marginally; the one material change is **case_1 payback 9.9 → 11.6 yr** (larger,
  costlier battery). Also surfaced **case_2 min DSCR 1.01x** (thin lender margin;
  prior baseline showed "—").
- Refreshed the Honest Economics table, retained-UUID list, and todos in
  `CODEX_SESSION.md` to these runs (June baseline now noted as archived).
- Checks run: per-case `results.json` `status == optimal`; new-vs-archived payload
  diff; new-vs-archived REopt sizing; new-vs-documented headline metrics (IRR/NPV/
  min DSCR/payback) pulled from each workbook's Developer Returns sheet.
- Blockers/assumptions: REopt re-solve is not bit-reproducible against the June
  container — flag if a third party expects identical sizing; likely needs a REopt
  Julia package version pin. The 2026-06-24 schema refactor is still uncommitted;
  `master` still unpushed.
- Open next: model-audit pass + third-party-ready Excel (CODEX_SESSION Active
  Direction steps 2-3); decide whether to commit the schema refactor; push `master`.

# 2026-06-24 - Proforma Schema Refactor (SAM-style, declarative presentation)

- User goal: study SAM's financial-model module (sibling repo, added to the same
  workspace) and apply its architecture to harden the Vietnam financial model in
  ReoptAPI, opening it to a third financing structure (direct ownership).
- Plan-mode discovery corrected a wrong premise from an earlier plan: there are
  **no** parallel/Julia Vietnam implementations. `proforma_vietnam/` is the one
  live engine; `reoptjl/src/vietnam/` is only the EVN tariff layer. So this was a
  single-engine refactor, not a consolidation.
- Key SAM lesson applied: compute stays imperative (like an SSC module); only the
  presentation is declarative (like SAM's `cfline()`/`metric()`), and the
  financing type is the primary dispatch key (like `cashflow{'Single Owner'}`).
  Approved deliverable: implement-now refactor covering structure registry +
  declarative schema + externalized defaults + metrics separation + schema-driven
  Excel; scoped open for `direct_ownership`.

## Changes (6 phases, each gated on a green suite; no financial numbers changed)

1. **`proforma_vietnam/structures.py`** (new): `ESCO`/`DPPA`/`DIRECT_OWNERSHIP`
   constants (last is a placeholder, no compute wired) + `resolve_structure()`.
   `cash_flow.py` now computes `structure` once and the two `dppa_settlement is
   not None` branches became `structure == DPPA` / `!= DPPA` (behaviour-identical).
2. **`proforma_vietnam/proforma_schema.py`** (new): `RowSpec` registry
   (`PROFORMA_ROWS`) declaring each line-item once (label, currency, applies_to);
   ordered per-sheet "views" (`CASH_FLOW_VIEW`, `TAX_SCHEDULE_VIEW`,
   `DEBT_SERVICE_VIEW`, `DPPA_ANNUAL_VIEW`, `SUMMARY_VIEW`,
   `DEVELOPER_FINANCIAL_VIEW`); `columns(view, structure)` filters by `applies_to`
   so DPPA-only lines auto-hide under ESCO; `number_format()` relocated verbatim
   from `xlsx_builder._number_format_for`.
3. **`xlsx_builder.py`**: deleted 7 duplicated column constants (`CASH_FLOW_COLUMNS`,
   `DPPA_CASH_FLOW_EXTRA_COLUMNS`, `TAX_SCHEDULE_COLUMNS`, `DEBT_SERVICE_COLUMNS`,
   `DEVELOPER_FINANCIAL_ROWS`, `DPPA_ANNUAL_COLUMNS`, `SUMMARY_ROWS`); those sheets
   now call `schema.columns(...)` at render time using a `structure` derived from
   the dppa_config. `_write_summary_sheet` gained a `rows` param. Bespoke sheets
   (Executive Summary / Buyer Analysis / Developer Returns / Year 1 BAU vs DPPA)
   and REopt-report sheets are intentionally left outside the schema. `report_data.py`
   needed no change (it forwards a summary dict, not column lists).
4. **`tests/test_proforma_schema.py`** (new, 5 tests): every schema-presented key
   (per structure) must exist in the compute output, so a label/key rename now
   fails CI instead of silently resolving to a blank cell; plus structure-filter
   tests.
5. **`defaults/vietnam_defaults.json`** (+ `defaults/__init__.py`, new): versioned
   VN financial + tax constants (escalation, debt, CIT schedule, depreciation
   years). `cash_flow.py` `DEFAULT_*` and `tax_model.py` `CIT_*`/depreciation
   constants now read from there; regulatory provenance kept inline in comments.
   Mirrors SAM `deploy/runtime/defaults/*.json`.
6. **`proforma_vietnam/SCHEMA.md`** (new): documents the architecture and how to
   add a line-item (one `RowSpec` + a view entry) or a new financing structure.

## Verification

- Baseline before changes (after installing `openpyxl` into `.venv`): 112 OK.
- After: **117 OK** = the 112 pre-existing tests + 5 new `test_proforma_schema`
  tests. Ran the full suite after each phase; all green. ResourceWarnings
  (HTTPError) are from network-mocked tests, harmless.
- Parity proof: a script confirmed `schema.columns(...)` reproduces every deleted
  xlsx constant exactly (ESCO 15 / DPPA 18 cash-flow cols, tax/debt/summary/dev/
  dppa-annual), and `number_format` matches the old heuristic on sampled keys.
- Single-source-of-truth proof: adding one `RowSpec` + one view key (ephemeral,
  not committed) made the line appear in both `columns()` and `xlsx_builder`'s
  Cash Flow sheet with no presentation-file edits — previously a >=3-place change.
- `py_compile` clean on all touched modules; no leftover references to the
  deleted constants.

## Environment / blockers

- ReoptAPI `.venv` (`.venv/Scripts/python.exe`, Python 3.14) has no `pytest`; the
  suite is `unittest`. Installed `openpyxl==3.1.5` into `.venv` to run the xlsx
  tests (was previously missing). Docker/Django not used (pure post-processing).
- No commit made. SAM sibling repo was read-only reference (not modified); its
  graphify graph is for SAM, so no `graphify update` run here.

## Out of scope / follow-up

- Wire real `direct_ownership` compute (only the placeholder + `applies_to`
  headroom exist now).
- Confirm with the project owner whether `_add_usd_aliases` (USD == VND
  numerically, no FX applied in `cash_flow.py`) is intended or a missing FX step
  — left untouched because changing it would move the numbers.
- Move `reoptjl/src/vietnam/evn_rates.py` tariff tables to the same
  versioned-defaults pattern.

# 2026-06-12 - CEBA DPPA Detailed Facilitator Narrative

- Created
  `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026_Slide_Narrative.md`.
- Reconstructed the exact final-deck sequence from the delivered PPTX's
  on-slide text and embedded speaker notes, then expanded each slide into a
  facilitator-ready narrative.
- The guide includes:
  - overall facilitation approach and caveat discipline,
  - 24 main-slide objectives, detailed talk tracks, buyer prompts/actions, and
    transitions,
  - 6 backup-slide use cases and detailed explanations,
  - final presenter reminders on modeled evidence and training assumptions.
- Validation: 30 slide headings total, comprising 24 main slides and 6 backup
  slides; 821 lines; `git diff --check` passed.
- Two existing PowerPoint lock files were visible in `outputs/ceba_training/`
  and were left untouched.

# 2026-06-12 - CEBA DPPA Buyer Decision Journey Deck Design

- User requested a new CEBA Procurement Academy training deck for factory-owner
  representatives in global-brand supply chains on "Understanding Vietnam's
  DPPA Mechanisms and Pricing Considerations."
- Reviewed the attached content plan, existing
  `outputs/ceba_training/build_deck.py`, current repo handoff, and latest Case
  5/6 negotiation evidence.
- Approved design decisions:
  - Primary outcome: procurement readiness.
  - Technical depth: balanced, with selected formulas and one worked settlement
    example.
  - Reuse posture: standalone with light callbacks to earlier sessions.
  - Narrative direction: Buyer Decision Journey.
  - Visual direction: white mechanism slides, navy evidence slides, recurring
    buyer-question rails, CEBA teal/navy/amber/green palette.
  - Presenter: Cong Nguyen, Vietnam Clean Energy Manager, Allotrope Partners.
- Wrote and committed the approved design:
  `docs/superpowers/specs/2026-06-12-ceba-dppa-training-deck-design.md`
  (`da554098`).
- Wrote the implementation plan:
  `docs/superpowers/plans/2026-06-12-ceba-dppa-training-deck-implementation.md`.
  The plan uses the artifact-tool presentation workflow, a verified source/data
  ledger, 24 main slides plus 6 backup slides, full render/layout/numerical QA,
  and final delivery at
  `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`.
- Source audit note: latest 2026-06-11 repository evidence supersedes several
  old-draft statements. The new deck must use Case 5 equity IRR 16.9% / min
  DSCR 1.14x / buyer lifetime -9.3%, Case 6 equity IRR 26.9% / min DSCR 1.50x
  / buyer -14.4%, and the lower-strike closest buyer-positive term at 1,300
  VND/kWh and 70% volume with buyer lifetime +0.46%, seller equity IRR 17.85%,
  and min DSCR 1.143x. Zero of 56 tested Case 6 scenarios are balanced.
- Verification:
  - `git diff --check` passed for the design and implementation-plan files.
  - Implementation plan placeholder scan returned no failures.
- No deck implementation was started in this planning session.

# 2026-06-11 (final) - Stabilization Commits + Case_6 Lower-Strike Boundary

- Aligned `ESCO_CONTRACT_MODEL_DESIGN.md` and `CODEX_SESSION.md` with the
  tested CD7 implementation: k is price-only, Q_adj divides by K_pp only, CfD
  is capped by matched quantity, C_cl defaults to 163.3, and Factory A battery
  replacement is year 11.
- Refreshed case_1..4 saved assumptions via `run_case --dry-run`, then rebuilt
  their reports offline. Updated `clean_metrics.json`. The existing CEBA PPTX
  is explicitly stale because its case_3 bankability claim conflicts with the
  corrected model (case_3 minimum DSCR 0.83x).
- Created focused commits:
  - `46382938` fix(vietnam): align DPPA settlement and lifecycle economics
  - `5a74cc86` feat(vietnam): add DPPA negotiation sweep
  - `139f8f01` feat(vietnam): redesign investment report workbook
  - `25799b46` data(vietnam): refresh Factory A cases and DPPA studies
  - `13e25cd6` feat(vietnam): run case 6 lower-strike sensitivity
- Added custom inclusive strike-grid CLI options to
  `run_dppa_negotiation_sweep.py` and ran case_6 across 1,200-1,400 VND/kWh
  in 50 VND/kWh increments with the existing 70/80/90/100% volume grid.
- Lower-strike result: 0/20 balanced. Twelve scenarios pass both buyer gates,
  but none pass the 1.20x lender DSCR gate. Closest buyer-positive term:
  `strike_1300_volume_70`, buyer lifetime savings +0.46%, seller equity IRR
  17.85%, minimum DSCR 1.143x.
- Commercial conclusion: pricing alone cannot balance case_6 under the current
  lender threshold. Next study should hold buyer-positive ~1,300 VND/kWh terms
  and test lower leverage / DSCR-sized debt, debt-service reserve, or debt
  sculpting.
- Assumption review:
  - PV depreciation remains configurable 7-20 years, default 20.
  - k=1.026 remains only the no-CFMP fallback/default; actual cases use hourly
    CFMP series.
  - Fixed FX over 25 years is not treated as confirmed practice; add an FX
    sensitivity before investor-facing use.
- Verification: `python -m unittest discover -s proforma_vietnam/tests -v`
  passed 112 tests. All three negotiation studies pass direct and workbook
  reconciliation.

# 2026-06-11 (later) - CD7 Alignment: k Semantics, CfD Cap, Year-11 Replacement, Multi-Horizon Buyer Gate

User directives (all implemented TDD, 111 tests green):

1. **PV depreciation explicit & configurable**: Circular 45/2013/TT-BTC permits
   7-20 years for generating equipment. `pv_depreciation_years` (default 20,
   validated 7-20 in `tax_model.validate_pv_depreciation_years`) now flows
   case.json `financial.pv_depreciation_years` → assumptions → run_case/views
   query param → cash_flow; noted on the workbook Model Basis sheet.
2. **k semantics fixed per CD7 / user clarification**: k is a *price*
   conversion (CFMP = FMP × k, varies per trading cycle, already embodied in
   the `fmp_cfmp_vn.json` FMP/CFMP spread — measured hourly ratio 1.0058-1.0603).
   `dppa_settlement.py` no longer divides delivered volume by k:
   `Q_adj = Q_re_meter / Kpp × δ` (CD7 Ví dụ 1: Qm 6,048,000 ↔ Q_khhc
   6,000,000 = ÷1.008). No-CFMP fallback is now `FMP × k`, not `FMP`.
3. **CD7 simulation cross-check** (`6. CD7. Mo phong, vi du ve co che DPPA.pdf`):
   - C_cl default corrected 163.0 → 163.3 VND/kWh (also patched into saved
     case_5/case_6 `assumptions.json`).
   - **CfD settles on received volume**: per Ví dụ 4 (plant 1,000 kWh,
     consumed 900, "Doanh thu CfD chỉ tính trên 900 kWh"), CfD now settles
     hourly on `min(Q_c, Q_Khc)`; `q_cfd_kwh` tracked in sums + hourly rows.
     Case Q_c series stay at 100% of generation per user decision.
   - New acceptance test reproduces CD7 Ví dụ 1 totals exactly (C_DN
     7,446,297,600 VND, C_KH 11,186,097,600 VND, generator 7,857,600,000 VND).
   - Flagged only (no change): CD7 settles CfD/C_DN on monthly-average FMP,
     ours hourly (finer); CD7 uses flat P1 retail for C_BL, ours hourly TOU.
4. **Battery replacement year 10 → 11** in all case JSONs + guide; new
   `battery_replacement_year` assumptions override beats the year echoed in
   saved results.json (needed offline; Docker unavailable). Replacement now
   lands after the 10-year debt term.
5. **Multi-horizon evaluation**: cash_flow summary gains
   `buyer_savings_10yr_usd/_fraction` and `buyer_savings_lifetime_usd/_fraction`
   (cumulative vs cumulative BAU). Sweep buyer gate = 10-year AND lifetime
   cumulative ≥ 0 (Year 1 reported as context); Pareto frontier on lifetime
   savings vs equity IRR; workbooks gained Buyer 10yr + Lifetime heatmaps and
   exec-summary lines.

## Corrected results (rebuilt offline via rebuild_report; reconciliations pass)

- **case_5** (run `ea6e1964`): equity IRR 16.9%, project IRR 13.5%, NPV $1.52M,
  min DSCR 1.14x (replacement now post-debt), payback 9.1y. Buyer: Y1 −8.7%,
  10yr −8.9% (−$0.82M), lifetime −9.3% (−$2.98M). The CfD cap removed the
  buyer→seller transfer on surplus volume (strike 2000 > FMP), cutting seller
  IRR 19.0→16.9% and improving the buyer 6 pts.
- **case_6** (run `96571e84`): equity IRR 26.9%, project IRR 18.2%, NPV $2.54M,
  min DSCR 1.50x, payback 4.7y. Buyer: −14.4% on all horizons (was −28.8% Y1)
  — the CfD cap bites hardest here because the small-battery system exports
  most PV, so most contracted volume was never consumed by the buyer.
- **case_5 sweep**: 0/36 balanced. Buyer gate 16/36, seller 24/36, lender 2/36
  (CfD cap cut seller revenue → min DSCR 0.82-1.19 in most scenarios).
  Buyer-best `strike_1400_volume_100`: 10yr +9.8%, lifetime +9.4%.
- **case_6 sweep**: 0/36 balanced. Seller 36/36, lender 32/36, buyer 0/36 —
  closest `strike_1400_volume_100` at −1.4% (10yr and lifetime). Strikes just
  below 1,400 VND/kWh should produce the first balanced deal.

Files: dppa_settlement.py, tax_model.py, cash_flow.py, esco_pro_forma.py,
case_builder.py, run_case.py, run_dppa_negotiation_sweep.py,
dppa_negotiation_sweep.py, dppa_negotiation_workbook.py, xlsx_builder.py,
reoptjl/views.py, all proforma_vietnam tests touched, case JSONs + case_5/6
assumptions.json + CASE_JSON_INPUT_GUIDE.md, regenerated case_5/6 workbooks
and both sweep output packages.

# 2026-06-11 - Model Audit: Q_Khc Settlement Fix + Real-World Mechanics + Consultant Workbook

- User asked to (1) audit/validate the Vietnam ESCO PPA + grid virtual-PPA
  financial model against real-world practice and fix misalignments, and
  (2) redesign the vietnam report workbook into a clean consultant-style
  deliverable for both developer and buyer in PPA negotiation.

## Bugs found and fixed (all TDD, 99 tests green)

1. **Buyer settled on unconsumed energy (critical)**: `dppa_settlement.py`
   charged C_DN/C_DPPA/C_CL on full `Q_adj` even when generation exceeded
   hourly load. Per ND57 / `vietnam_market_context.md`, the settlement
   quantity is `Q_Khc = min(load, Q_adj)`. On case_5 the buyer was billed for
   1.40 GWh/yr it never consumed (19.3% of Q_adj, ≈ $106k/yr): Year-1 buyer
   savings move from −28.7% to −14.9% at strike 2000. `q_khc_kwh` and
   `matched_retail_value_vnd` now surface in settlement sums, hourly rows and
   the workbook.
2. **Stale `capacity_multiplier`** in `cash_flow.py`: non-DPPA annual rows
   displayed `bau/optimized_demand_charge_vnd` escalated by the *final* year's
   multiplier for every year (leaked loop variable). Display-only; fixed.
3. **No PV degradation**: revenue escalated 4%/yr with no production decay.
   Now `pv_degradation_rate` (derived from REopt `PV.degradation_fraction`,
   0.005 in all Factory A cases) shrinks generation-linked terms; lost matched
   energy is repurchased at EVN retail (residual bill / C_BL).
4. **No battery replacement**: `replacement_costs_by_year` existed but was
   never populated. Now auto-derived from REopt
   `battery_replacement_year` + `replace_cost_per_kw/kwh` (case_5: $1.21M in
   year 10) unless overridden.
5. **CIT not law-aligned**: added 5-year tax-loss carryforward and the
   exemption clock counted from first profitable year capped at year 4
   (Circular 78/2014 Art. 9 / Art. 18).
6. **Flat O&M**: new `om_escalation_rate` input (default 0), wired through
   case_builder/run_case/views/sweep.

## Flagged but NOT changed (documented in workbook "Model Basis" notes)

- Fixed FX (25,000 VND/USD) across 25 years; VND depreciation not modelled.
- PV depreciation 20yr in code vs 10yr in `vietnam_market_context.md` table.
- `k = 1.026` in code vs `k = 1.02` in market context doc.
- Replacement expensed (not depreciated); CfD settles on contracted volume
  regardless of degradation.

## Workbook redesign (`xlsx_builder.py`)

- Three new consultant-facing front sheets: **Executive Summary** (system,
  contract terms, seller returns, buyer outcome, model-basis notes),
  **Buyer Analysis** (Year-1 snapshot + DPPA cost stack + 25-year savings
  table with cumulative chart), **Developer Returns** (sources & uses, return
  metrics incl. minimum DSCR, annual CFADS/DSCR/equity CF table + chart).
- Navy/white styling, number formats everywhere, no gridlines on front
  sheets; existing sheets kept as appendix; Hourly Settlement and the BAU vs
  DPPA sheet now carry Q_Khc columns/labels (sweep reconciler updated).
- New offline CLI `python -m proforma_vietnam.rebuild_report --case-dir <dir>`
  rebuilds the workbook from saved results.json/assumptions.json without
  Django/REopt (Docker was down; report is pure post-processing).

## Regenerated artifacts (corrected model)

- case_5 (`ea6e1964`): equity IRR 19.0%, project IRR 14.6%, NPV $1.98M,
  min DSCR −0.92 (year-10 battery replacement coincides with final debt
  year), avg DSCR 1.18, payback 7.3yr; Y1 buyer savings −14.9%.
- case_6 (`96571e84`): equity IRR 36.9%, NPV $3.78M, min DSCR 1.84,
  payback 3.1yr; Y1 buyer savings −28.8%.
- Both 36-scenario sweeps re-run; direct + workbook reconciliations pass.
  case_5 study: 13 scenarios now pass the buyer gate (was 0);
  buyer-best `strike_1400_volume_100` = +9.0% Y1 savings, but lender gate
  fails everywhere (replacement-year DSCR). case_6 study: seller 36/36,
  lender 32/36, buyer 0/36 — buyer-best −2.8% at `strike_1400_volume_70`.
- Commercial read: the oversized case_5 BESS cannot carry its own
  replacement; case_6 sizing is bankable but needs a lower strike (<1400) or
  buyer-side fee relief to clear the buyer gate.
- Stale workbooks deleted (kept only run-uuid-matched): case_5 `bc785b6f`,
  `bf7a908a`; case_6 `86acaddb`.

## Verification

- `python -m unittest discover -s proforma_vietnam/tests -p "test_*.py"`:
  99 tests, OK (Django/docker unavailable this session).
- Both reference workbook gates stayed green (defaults backward compatible).
- Regenerated case_5 Executive Summary visually verified via openpyxl readback.
- `reoptjl/views.py` compile-checked.

# 2026-06-10 - Global 4% CfD Strike Escalation And Factory A Reruns

- User approved making `4%` annual CfD strike escalation the global DPPA
  default and requested it be explicit in generated assumptions.
- Changed `DEFAULT_CFD_STRIKE_ESCALATION_RATE` from `0.0` to `0.04`, updated
  the contract-model design default, and set case_5/case_6 source JSON
  explicitly to `0.04`.
- Added regression coverage proving omitted DPPA escalation resolves to `0.04`,
  explicit overrides remain supported, and Year 2 strike revenue is exactly
  `1.04x` Year 1.
- Regenerated case_5 end to end:
  - Run UUID `ea6e1964-f331-45e4-94e7-1e712e45464c`, status `optimal`.
  - Equity IRR `21.2%`, NPV `$2.58M`, minimum DSCR `1.24x`, average DSCR
    `1.46x`, simple payback `7.14 years`.
- Regenerated case_6 end to end:
  - Run UUID `96571e84-2d04-401b-8135-e0c9766ad445`, status `optimal`.
  - Equity IRR `37.7%`, NPV `$4.03M`, minimum DSCR `1.84x`, average DSCR
    `2.13x`, simple payback `3.05 years`.
- Regenerated both 36-scenario negotiation sweeps. Both direct and workbook
  reconciliations pass.
  - case_5: zero balanced deals; all scenarios now pass seller IRR, 28 still
    fail lender plus buyer, and 8 fail buyer only.
  - case_6: zero balanced deals; all 36 pass seller and lender gates and fail
    only the Year 1 buyer gate.
- Commercial conclusion: escalating the strike improves lifetime seller and
  lender economics but does not change Year 1 buyer cost, so the next
  sensitivity must target the buyer-side cost stack.
- Verification:
  - Focused default/override/compounding tests passed.
  - `python -m unittest discover -s proforma_vietnam/tests -p 'test_*.py'`
    passed 82 tests.
  - `docker-compose exec -T django python manage.py test proforma_vietnam -v 1`
    passed 82 tests with no Django system-check issues.
  - Fixed a negotiation-runner test that hardcoded Windows path separators
    after Docker correctly exposed the portability defect.
  - Both generated workbooks show `CfD Strike Escalation Rate = 0.04`; both
    sweeps contain 36 unique scenarios and pass direct/workbook reconciliation.
  - `git diff --check` passed; only expected Windows LF/CRLF warnings remain.

# 2026-06-10 - Factory A case_6 DPPA Commercial Negotiation Sweep

- Generalized `proforma_vietnam/run_dppa_negotiation_sweep.py` with a
  `--reference-case` option. `case_5` remains the default and keeps its original
  output directory; other cases use a suffixed study directory.
- Ran:
  `python -m proforma_vietnam.run_dppa_negotiation_sweep --reference-case case_6`.
- Wrote 36-scenario JSON, XLSX, and Markdown artifacts under
  `outputs/vietnam_case/factory_a/dppa_negotiation_study_case_6/`.
- The evaluator uses fixed `case_6` technical results and assumptions while
  retaining non-DPPA `case_2` as the comparison baseline.
- Result: zero balanced deals and zero negotiation-frontier scenarios.
  Buyer-best `strike_1400_volume_70` is 35.2% worse than BAU and 46.1% worse
  than non-DPPA `case_2`. Lender-best `strike_2200_volume_100` reaches 1.88x
  minimum DSCR and 36.9% equity IRR but is 69.4% worse than BAU.
- `strike_2000_volume_100` reconciliation passed against both the direct
  `case_6` cash-flow calculation and the existing `case_6` workbook at the
  configured `1e-6` relative tolerance.
- TDD evidence:
  - Red: `python -m unittest proforma_vietnam.tests.test_dppa_negotiation_sweep`
    failed because the new reference-case helpers did not exist.
  - Green: the same focused command passed 6 tests after implementation.
- Verification:
  - `python -m unittest discover -s proforma_vietnam/tests -p 'test_*.py'`
    passed 80 tests.
  - `python manage.py test proforma_vietnam.tests.test_dppa_negotiation_sweep`
    remains unavailable locally because Django is not installed.

# 2026-06-10 - Factory A case_6 Minimum BESS

- User requested a case matching `case_5` except for the minimum storage
  requirement: battery power at 10% of solar capacity and two hours of energy.
- Approved rounded fixed sizes: PV `5,914 kW`; BESS `592 kW / 1,184 kWh`.
- Created the approved design and plan under `docs/superpowers/`, plus
  `outputs/vietnam_case/factory_a/case_6/`.
- Preserved every other current `case_5` input. A structured comparison passed
  after normalizing only the case name, fixed size bounds, and regenerated DPPA
  contract-volume series.
- Initial dispatch run UUID: `04e45388-89a3-4912-bd6a-0929cc1535f2`.
- Regenerated the 8760 DPPA contract volume from
  `PV-to-load + PV-to-grid + curtailed PV + storage-to-load + storage-to-grid`.
- Final run UUID: `86acaddb-4dc9-4654-affb-12db1c2bfacf`; status `optimal`.
- Final verification: PV `5,914 kW`; BESS `592 kW / 1,184 kWh`; contract volume
  `7,896,846.067 kWh/year`; maximum hourly reconciliation delta `0`.
- Final financial results: total capex `$3,028,160.00`; equity IRR `30.707%`;
  NPV `$2,158,972.58`; average DSCR `1.773x`; minimum DSCR `1.708x`; simple
  payback `3.348 years`; Year 1 generator revenue `$631,747.69`; Year 1 DPPA
  offtaker cost `$1,239,750.06`.
- Final workbook:
  `outputs/vietnam_case/factory_a/case_6/vietnam_report_86acaddb-4dc9-4654-affb-12db1c2bfacf.xlsx`.
  Workbook reconciliation against the direct financial-model calculation
  passed.
- Execution notes: the first submission attempt occurred during Django's
  startup/reloader window and did not reach the application. Retrying after
  service readiness succeeded without code changes. The cloned JSON was also
  normalized to BOM-free UTF-8 before submission.

# 2026-06-10 - DPPA Commercial Negotiation Sweep Implemented

- Implemented the approved fixed-system DPPA commercial negotiation sweep without rerunning REopt or cloning case directories.
- Added:
  - `proforma_vietnam/dppa_negotiation_sweep.py` for the 36-scenario grid, metric extraction, balanced-deal gates, and Pareto classification.
  - `proforma_vietnam/dppa_negotiation_workbook.py` for the nine-sheet joint-negotiation workbook and concise Markdown summary.
  - `proforma_vietnam/run_dppa_negotiation_sweep.py` for Factory A artifact loading, sweep execution, output writing, and clean `case_5` reconciliation.
  - `proforma_vietnam/tests/test_dppa_negotiation_sweep.py`.
  - `docs/superpowers/plans/2026-06-10-dppa-commercial-negotiation-sweep.md`.
- Generated:
  - `outputs/vietnam_case/factory_a/dppa_negotiation_study/results.json`.
  - `outputs/vietnam_case/factory_a/dppa_negotiation_study/Factory_A_DPPA_Negotiation_Sweep.xlsx`.
  - `outputs/vietnam_case/factory_a/dppa_negotiation_study/NEGOTIATION_SUMMARY.md`.
- Result:
  - Exactly 36 unique strike/volume scenarios evaluated.
  - Zero scenarios pass all three balanced-deal gates.
  - Every scenario increases Factory A Year 1 cost versus BAU.
  - Buyer-best `strike_1400_volume_100`: 4.8% higher buyer Year 1 cost versus BAU and 13.2% higher versus non-DPPA `case_2`.
  - Lender-best `strike_2200_volume_100`: 1.27x minimum DSCR and 17.7% seller equity IRR, but 36.7% higher buyer Year 1 cost versus BAU.
- Reconciliation:
  - `strike_2000_volume_100` matches the direct clean `case_5` calculation at zero relative delta.
  - It also matches `case_5/vietnam_report_bc785b6f-2b82-4684-b583-3010ca6a9904.xlsx` at zero relative delta for Year 1 settlement totals, equity IRR, NPV, minimum DSCR, and average DSCR.
- TDD/verification:
  - Initial red run: `python -m unittest proforma_vietnam.tests.test_dppa_negotiation_sweep -v` failed with the expected missing sweep-module import.
  - Focused suite: 5 tests passed.
  - Full local suite: `python -m unittest discover -s proforma_vietnam/tests -v` passed, 79 tests.
  - `python -m compileall` passed for all new modules/tests.
  - Docker/Django test command could not run because local Django is not installed and Docker Desktop was unavailable.

# 2026-06-10 - DPPA Commercial Negotiation Sweep Design

- User selected the next-session direction: a fixed-system DPPA commercial term sweep supporting a joint negotiation between Factory A and the ESCO/generator.
- Approved scenario grid:
  - CfD strikes from `1,400` through `2,200 VND/kWh`, inclusive, in `100 VND/kWh` increments.
  - Contract volumes at `70%`, `80%`, `90%`, and `100%` of the clean `case_2` expected hourly `Q_re_meter`.
  - Exactly 36 scenarios.
- Approved approach:
  - Keep clean `case_2` technical sizing and dispatch fixed.
  - Reuse existing DPPA settlement and Vietnam ESCO cash-flow functions.
  - Do not clone 36 case directories and do not rerun REopt.
- Approved balanced-deal gates:
  - Factory Year 1 savings versus BAU `>= 0%`.
  - ESCO/generator equity IRR `>= 12%`.
  - Minimum DSCR during debt-service years `>= 1.20x`.
- The factory result versus non-DPPA `case_2` is a prominent disclosure metric, but it is not a qualification gate.
- Approved outputs: machine-readable results, a joint-negotiation workbook, a Pareto negotiation frontier, a recommended term range, and a concise negotiation summary.
- Wrote and committed the approved design:
  - Spec: `docs/superpowers/specs/2026-06-10-dppa-commercial-negotiation-sweep-design.md`.
  - Commit: `b417ee9f docs: define DPPA negotiation sweep design`.
- Verification:
  - Design spec placeholder scan returned no matches.
  - `git diff --check -- docs/superpowers/specs/2026-06-10-dppa-commercial-negotiation-sweep-design.md` passed before commit.
- Next step: user reviews the written spec; after approval, write the detailed implementation plan under `docs/superpowers/plans/`.

# 2026-06-09 - Clean-Load case_5 DPPA Re-run

- Repointed `outputs/vietnam_case/factory_a/case_5/case.json` from `Sample Load Profile/Emivest.csv` to `Sample Load Profile/Emivest_clean.csv`.
- First successful clean-load run exposed a second stale dependency: the embedded 8760 CfD contract-volume series still reflected dirty-load `case_2` (`7,707,474.773 kWh/year`) rather than clean-load `case_2` Q_re_meter (`7,664,883.239 kWh/year`).
- Refreshed `case_5.dppa.cfd_contract_volume_kwh_per_hour` from clean `case_2` PV-to-load + PV-to-grid + curtailed PV + storage-to-load + storage-to-grid. Changed 2,922 hourly values.
- Final run UUID: `bc785b6f-2b82-4684-b583-3010ca6a9904`; optimizer status `optimal`.
- Final workbook: `outputs/vietnam_case/factory_a/case_5/vietnam_report_bc785b6f-2b82-4684-b583-3010ca6a9904.xlsx`.
- Final clean-load metrics:
  - PV: `5,913.5567 kW`.
  - BESS: `1,796.0 kW / 10,698.95 kWh`.
  - Total capex: `$4,266,061.216`.
  - Project IRR: `11.81%`; Equity IRR: `14.47%`.
  - NPV: `$763,328.59`; average DSCR: `1.213`; simple payback: `10.60 years`.
  - Buyer savings vs BAU: `-28.73%` at the current 2,000 VND/kWh strike.
- Verification:
  - Confirmed all `case_1..5` configs reference `Emivest_clean.csv`.
  - Confirmed `case_5` payload load series exactly matches clean `case_2` (`9,340,091.626 kWh/year`, `2,428 kW` peak).
  - Confirmed `case_5` optimizer sizing exactly matches clean `case_2`.
  - Confirmed the refreshed CfD volume equals clean `case_2` Q_re_meter hour by hour.
  - Confirmed the latest workbook contains all five DPPA-specific sheets and its reported Q_re_meter equals the contract-volume annual sum.
  - `git diff --check` passed for the regenerated `case_5` JSON files.
- Operational notes:
  - Initial submission attempts failed while Django was still starting; retry after the API reported ready succeeded.
  - One completed retry hit a transient Windows `OSError 22` while replacing `results.json`; the file immediately reopened read/write and the next end-to-end retry succeeded.
  - Docker stack remains running.

# 2026-06-09 - Graphify Code Map + Vietnam Study Evidence Map

- User asked to run `/graphify` for the codebase. Full repo detection found 847 supported files / ~3.73M words, over the graphify threshold; top noisy scope was legacy `reo/`.
- Narrowed first map to `reoptjl` + `proforma_vietnam`:
  - Focused corpus: 244 files / ~282,786 words.
  - Code files extracted: 241.
  - Docs/images skipped: 3 because no LLM backend key (`GEMINI_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) was configured.
  - AST/code graph output: 1,990 nodes, 2,996 edges, 247 communities.
- User then asked to include the current Vietnam study scope:
  - `outputs/vietnam_case/factory_a`
  - `DPPA DOC`
  - `Sample Load Profile`
  - `vietnam_market_context.md`
  - `roadmap.md`
  - `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`
- Added deterministic study-layer extraction:
  - Markdown headings for the root/design docs.
  - PDF file/text-sample nodes for DPPA reference docs.
  - JSON structure and case settings for Factory A cases and `DPPA DOC/fmp_cfmp_vn.json`.
  - CSV stats for load profiles, including explicit `Emivest.csv` stale-load and `Emivest_clean.csv` clean-load topic links.
  - Workbook sheet nodes and PowerPoint slide-title nodes.
  - Explicit bridges from study topics to implementation nodes: `settle_dppa_year_one()`, `_dppa_inputs()`, `load_fmp_series()`, `load_cfmp_series()`, `calculate_vietnam_esco_cash_flow()`, `calculate_esco_pro_forma_from_reopt_results()`, `build_vietnam_esco_workbook()`, and `build_evn_tariff()`.
- Final merged graph in `graphify-out/`: 2,505 nodes, 3,691 edges, 248 communities. New study community: `247 - Vietnam Study Evidence`.
- Outputs:
  - `graphify-out/graph.html`
  - `graphify-out/graph.json`
  - `graphify-out/GRAPH_REPORT.md`
  - `graphify-out/VIETNAM_STUDY_GRAPH_REPORT.md`
  - `graphify-out/vietnam_study_map_summary.json`
- Verification query run:
  - `python -m graphify query "How does case_5 stale load connect to DPPA settlement and Factory A clean metrics?" --graph graphify-out\graph.json --budget 1200`
  - Query reached `case_5/case.json`, `Sample Load Profile/Emivest.csv` via the `Case 5 Stale Load` topic, `DPPA DOC/fmp_cfmp_vn.json`, `FMP`, `CFMP`, and implementation nodes including `settle_dppa_year_one()` and `load_fmp_series()`.
- Current limitation: graphify semantic extraction was not run because no LLM backend API key was configured; the study layer is deterministic and evidence-oriented, not a full semantic read of all PDF/doc content.

# 2026-06-09 - Load-Profile Spike Cleaning + Re-run case_1..4 + New 7-Slide CEBA Deck

- User asked for a standalone, max-7-slide, corporate white-background CEBA case-study deck focused only on the four Factory A cases (case_5 DPPA explicitly excluded), in English, built from the data in `outputs/vietnam_case/factory_a`.
- No commit made this session (user asked only to build the deck and update handoff notes). Working tree dirty; see Git state below.

## Data-quality finding + fix (load profile spike)

- While extracting metrics I found `Sample Load Profile/Emivest.csv` contained a non-physical spike: exactly 24 contiguous hours (indices 7344-7367, early November) at ~38,000-41,780 kW while the site's real operating peak is ~2,000-2,428 kW and the mean is 1,157 kW.
  - That one day was ~8% of annual energy (10,139.6 MWh dirty) and set the annual peak at 41,780 kW (vs realistic monthly peaks ~2,000-2,400 kW).
  - It badly distorted case_3 (two-component/demand-charge tariff): the dirty run sized a 4,783 kW battery chasing the spike, and reported a BAU demand charge of ~$611k mostly from that single day.
- User chose "Clean & re-run 4 cases" (AskUserQuestion).
- Cleaning: wrote `Sample Load Profile/Emivest_clean.csv` — replaced each of the 24 anomalous hours with the hour-of-day mean computed from all non-anomalous hours (preserves a realistic daily shape rather than flat-capping). Result: annual energy 10,139.6 → 9,340.1 MWh; peak 41,780 → 2,428 kW.
- Pointed `case_1..4/case.json` `load_profile.path` at `Sample Load Profile/Emivest_clean.csv` (case_5 left untouched).

## Re-ran case_1..4 end-to-end on docker

- `docker compose up -d` (only `db` was up at session start). Julia was already warm from a prior run.
- Ran `python -m proforma_vietnam.run_case --case outputs/vietnam_case/factory_a/case_N/case.json --poll-seconds 5 --max-polls 120` for case_1..4; all returned exit 0 / status `optimal`.
- Gotcha 1 — stale workbooks: each run writes a NEW `vietnam_report_<run_uuid>.xlsx`, so old ones accumulate. My first dedup attempt compared a glob path (backslash on Windows) against a constructed forward-slash path; the mismatch deleted the just-generated workbooks too. Recovered by re-running all four cases. Lesson: match the xlsx to the current `results.json` `run_uuid` and normalize separators before deleting.
- Gotcha 2 — partial results.json: case_2's saved `results.json` came back with only `Financial`+`ElectricTariff` output sections (captured mid-serialization). Re-fetched full results via `curl http://localhost:8000/v3/job/<uuid>/results` — then all 7 output sections present.
- Final metric extraction matches each xlsx to its `results.json` `run_uuid` (proper path handling) and is saved to `outputs/vietnam_case/factory_a/clean_metrics.json`.

## Clean Factory A economics (case_1..4, cleaned load; ESCO developer lens, 70% debt)

| Case | Scenario | PV (kW) | BESS (kW / kWh) | Clean self-supply | Total CapEx | Equity IRR | 25-yr NPV | Avg DSCR | Payback |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| case_4 | Solar only, QĐ963 TOU | 3,453 | — | 35.8% | $1.66M | 18.7% | $0.80M | 1.33 | 9.0 yr |
| case_1 | Solar+BESS, current TOU | 5,322 | 1,662 / 8,250 | 59.5% | $3.68M | 18.2% | $1.65M | 1.31 | 9.4 yr |
| case_2 | Solar+BESS, QĐ963 TOU | 5,914 | 1,796 / 10,699 | 65.5% | $4.27M | 16.1% | $1.44M | 1.21 | 10.5 yr |
| case_3 | Solar+BESS, QĐ963 + two-component | 5,765 | 1,830 / 11,693 | 65.8% | $4.32M | 12.4% | $0.59M | 1.01 | 12.2 yr |

- case_3 grid peak shaved 2,428 → 1,311 kW (−46%); demand-charge savings $128,781/yr; total bill $757,870 → $263,380 (−65%).
- These supersede the case_1..4 rows in the 2026-06-07 "Honest Factory A Economics" table, which were computed on the dirty (spiked) load. The biggest change is case_3: clean battery is 1,830 kW (was 4,783 kW on dirty data).
- **case_5 was NOT re-run** and still reflects the dirty load — it is now inconsistent with case_1..4. Re-run it on the cleaned profile before using it alongside the others.

## Deck built

- `outputs/vietnam_case/factory_a/Factory_A_Solar_BESS_Case_Study.pptx` — 7 slides, 16:9, white background, English, native (editable) PowerPoint charts + table.
  1. Title. 2. The study (Factory A profile + 4 scenarios + method). 3. Finding 1: solar-only stalls at ~36%. 4. Finding 2: BESS nearly doubles clean supply (36%→66%) and savings (+$324k/yr). 5. Finding 3: two-component tariff → peak-shaving (−46% peak, −$129k/yr demand charge). 6. Side-by-side techno-economic table. 7. Conclusions + recommendation.
- Builder script committed as an artifact: `outputs/vietnam_case/factory_a/build_deck.py` (uses `python-pptx`, reads `clean_metrics.json`). `python-pptx` was pip-installed this session.
- Financial lens: ESCO developer (Project/Equity IRR, DSCR, 70% debt) from the Vietnam report workbook Summary sheet — not the REopt offtaker-savings NPV.
- Deck footnotes disclose the 24-hour load-spike removal.

## Verification evidence

- Re-ran all 4 cases to status `optimal`; extracted metrics from the run-matched workbooks.
- Deck verified visually: installed LibreOffice (winget), converted PPTX → PDF (`soffice --headless --convert-to pdf`), rasterized to PNG (PyMuPDF), and inspected all 7 slides. First render showed heavy theme drop-shadows; fixed by stripping each autoshape's `<p:style>` effectRef in `build_deck.py` (`_no_shadow`) for a flat corporate look; re-rendered and confirmed.
- Structural check: 7 slides, charts present on slides 3/4/5, table on slide 6, zero shapes overflowing slide bounds; all numbers cross-checked against `clean_metrics.json`.
- Temporary `_render/` PNG/PDF directory deleted after inspection.

## Files changed / added

- Source/inputs: `Sample Load Profile/Emivest_clean.csv` (new); `case_1..4/case.json` (load path → cleaned CSV).
- Regenerated per case_1..4: `payload.json`, `assumptions.json`, `results.json`, and new `vietnam_report_<uuid>.xlsx` (old per-case workbooks deleted).
- New deck assets: `outputs/vietnam_case/factory_a/Factory_A_Solar_BESS_Case_Study.pptx`, `build_deck.py`, `clean_metrics.json`.
- No `proforma_vietnam/` source code or tests changed.

## Git state at close

- Branch `master`, `[ahead 5]` of `origin/master`. HEAD `f22c9131`. No commit this session.
- Modified (tracked): case_1..4 `case.json` / `payload.json` / `results.json`; deleted (tracked): the four old per-case workbooks.
- Untracked: `Sample Load Profile/Emivest_clean.csv`, the new deck `.pptx`, `build_deck.py`, `clean_metrics.json`, and the four new per-case `vietnam_report_<uuid>.xlsx`.

## Blockers / assumptions / open follow-ups

- Docker stack (django/celery/julia/db/redis) was left **running**; `docker compose down` when done.
- case_5 still on dirty load — re-run on `Emivest_clean.csv` before comparing to case_1..4.
- The pre-existing prior-session cleanup item (case_5 Excel-locked `*_v5.xlsx` + stale parent `vietnam_report_b729db40-*.xlsx`) is still outstanding.
- Decide whether to commit the cleaned-load re-run + deck artifacts (the `outputs/...` tree is tracked, so the regenerated case_1..4 outputs and deck would enter git on commit).

# 2026-06-07 - Case_5 End-to-End Validation, Model Corrections, bess_capex Fix, Commits

- User asked to continue from the prior session and build the deferred Factory A `case_5` end-to-end. The validation surfaced four substantive model corrections + one capex accounting bug, all fixed and committed in this session.
- Commits made:
  - `290b8dc2` Ship Phase 3 DPPA settlement with Factory A case_5
  - `8e0c2d1c` Refresh case_1/3/4 outputs after bess_capex fix

## Plan + Discovery (plan mode)

- Read `CODEX_SESSION.md`, `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`, the existing `dppa_settlement.py`, `case_builder.py`, `run_case.py`, and `xlsx_builder.py` to understand the staged Phase 3 implementation.
- User chose: 8760 CfD volume series matched to case_2 PV+BESS dispatch, strike `2000 VND/kWh` (revised up from initial 1700 during plan review).
- Plan file: `C:\Users\kongn\.claude\plans\dazzling-seeking-phoenix.md` (approved).

## case_5 Built

- `outputs/vietnam_case/factory_a/case_5/case.json` cloned from `case_2/case.json` with the `dppa` block:
  - `type = "grid_dppa_cfd"`, `cfd_strike_per_kwh_vnd = 2000.0`
  - `cfd_contract_volume_kwh_per_hour` = 8760-array derived from case_2 results: `pv_to_load + pv_to_grid + storage_to_load + storage_to_grid + pv_curtailed`. Annual total 7.71 GWh.
- Docker stack brought up via `docker-compose up -d`; Julia + celery + django + db + redis confirmed running.
- REopt optimization completed successfully (run_uuid `bf7a908a-1d47-4772-a81e-062766e848e2`, status `optimal`). PV sized 5945.62 kW, BESS sized 1796.81 kW / 10766.7 kWh — identical to case_2 since the payload is identical (DPPA settlement is post-processing only).

## Five bugs fixed in this session

### 1. HTTP 414 on workbook download

- Symptom: First workbook download attempt failed with `HTTP Error 414: Request-URI Too Long`. The `dppa_config` JSON-encoded into a GET query string was ~260 KB because of the embedded 8760 FMP series + 8760 contract volume.
- Fix: `proforma_vietnam/run_case.py` `_download_vietnam_report` now POSTs the request with `dppa_config` form-encoded in the body when present, keeping the scalar params (esco_energy_discount_fraction etc.) in the GET query. `reoptjl/views.py` `_vietnam_proforma_overrides` reads `dppa_config` from either `request.GET` or `request.POST`.
- `dev_settings.py` does not enable CSRF middleware, so POST works without a token.

### 2. `fee_escalation_rate = None` → TypeError in cash_flow

- Symptom: Optimization succeeded but report generation crashed with `TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'` at `cash_flow.py:365` (`fee_multiplier = (1 + escalation.get("fee_escalation_rate", 0.0)) ** year_index`). `.get(...)` was returning the stored `None` because the key existed.
- Fix: `case_builder.py` `_dppa_inputs(...)` now defaults `fee_escalation_rate` to `tariff_config.evn_energy_escalation_rate` (matches the design doc's documented intent). Function signature gained a `tariff_config` parameter.

### 3. DPPA VND values mixed with USD cash flow

- Symptom: After the first successful render, headline KPIs were absurd (NPV $101B, DSCR 37,917, ROI 311,274) because `settle_dppa_year_one` returns VND-magnitude values from FMP × kWh, but the surrounding cash flow runs in USD (REopt money values are USD; `_money()` passes them through unchanged).
- Fix: `esco_pro_forma.py` `_convert_dppa_year_one_to_cash_flow_currency(...)` divides every `*_vnd` key in `dppa_settlement["year_one"]` by `exchange_rate_vnd_per_usd` before threading into `calculate_vietnam_esco_cash_flow`. Hourly and monthly breakouts stay VND because the Hourly Settlement / Monthly Settlement sheets are explicitly VND-labelled.
- New tests in `test_esco_pro_forma.py` lock in the conversion and the breakout-stays-VND invariant.

### 4. Customer-side spot price formula: FMP → CFMP × K_pp

- Per user clarification of the ND57 formula: `C_DN = Σᵢ Q_KHhc(i) × CFMP(i) × K_pp`, where the buyer's spot energy charge uses CFMP (not FMP) marked up by the distribution loss factor.
- Discovery: `DPPA DOC/fmp_cfmp_vn.json` already carried both `fmp_vnd_per_kwh` and `cfmp_vnd_per_kwh` series. CFMP/FMP ratio averages 1.0274, almost exactly `K_pp = 1.027263` at 22-110kV — CFMP is FMP marked up by distribution losses.
- Fix:
  - `dppa_settlement.py`: new `load_cfmp_series(path)` helper. `settle_dppa_year_one` reads `dppa_inputs["cfmp_series_vnd_per_kwh"]` (falls back to FMP if absent) and computes `C_DN = q_adj × cfmp × kpp`.
  - `case_builder.py`: loads both FMP and CFMP series from the JSON file, stuffs both into the `dppa` assumptions block.
  - New test `test_cfmp_series_drives_c_dn_when_provided`.

### 5. Curtailed PV credited as DPPA grid export

- Discovery: case_2's REopt run curtailed 19.64% of PV production (1.57 GWh/yr) because the payload had no grid-export incentive. Under DPPA the generator owns the meter and dumps surplus at FMP rather than curtailing.
- User decision: optimizer payload stays self-consumption ("side reward, not main objective"); the settlement layer credits the curtailed energy as DPPA grid export.
- Fix:
  - `dppa_settlement.py` accepts `pv_curtailed_kw` in the dispatch dict and adds it to `pv_to_grid_effective`, which flows into `Q_re_meter` and `generator_fmp_revenue`.
  - `esco_pro_forma.py` passes `electric_curtailed_series_kw` from REopt outputs into the dispatch.
  - `report_data.py` exposes `pv_to_grid_effective_kwh = pv_to_grid + pv_curtailed` for the workbook.
  - New test `test_curtailed_pv_is_credited_as_grid_export_in_q_re_meter`.

### Plus: bess_capex_usd=0 silent override bug

- User noticed `"bess_capex_usd": 0` in `case_5/assumptions.json`. Diagnosed:
  - `case_builder.py` `_capex_assumptions` had `if storage.get("installed_cost_constant") is not None: ... has_storage_capex = True`. With `installed_cost_constant=0` present, this flipped `has_storage_capex=True` and wrote 0.
  - `run_case.py` ships `bess_capex_usd=0` in the URL query.
  - `views.py` stuffs it into `cash_flow_overrides`.
  - `esco_pro_forma.py` correctly derives BESS capex from REopt outputs (`storage_outputs["initial_capital_cost"]`), but `cash_flow_inputs.update(cash_flow_overrides)` silently overrides the truth with 0.
- Real BESS capex for case_5: $1,435,748.80 (REopt-reported). The 0 deflated total project capex from $4.29M to $2.85M, inflating IRR/NPV/ROI/payback for all five Factory A cases.
- Fix: `case_builder._capex_assumptions` now only writes `bess_capex_usd` when (a) `size_kw` or `size_kwh` is preset in case.json AND (b) computed storage_capex > 0. When sizes are optimizer-chosen, the field is omitted and `esco_pro_forma` derives capex from REopt outputs as already intended.
- Same logic applies to PV capex — already correctly gated on `size_kw is not None`.
- New regression test `test_bess_capex_omitted_when_storage_size_is_optimizer_chosen`.

## New feature: Year 1 BAU vs DPPA workbook sheet

- New sheet appears when `dppa.type != none`, alongside the existing DPPA Configuration / Hourly Settlement / Monthly Settlement / DPPA Annual Summary sheets.
- Three sections:
  - **Buyer (Factory) — Year 1 Outflow (USD)**: BAU EVN bill vs DPPA line items (C_DN / C_DPPA / C_CL / C_BL / CfD payment / optimized demand charge / ESCO demand savings share / total outflow / savings vs BAU absolute + fraction).
  - **Seller (ESCO/Generator) — Year 1 Revenue (USD)**: Phase 2 discount-to-EVN energy revenue (zeroed under DPPA) / FMP market revenue / CfD net / demand savings share / grid arbitrage revenue / total ESCO revenue.
  - **System Energy Flows (kWh/yr)**: PV→load, PV→storage, PV→grid (export at FMP, including would-be-curtailed under DPPA), storage→load, total Q_re_meter, Q_adj loss-adjusted, EVN retail shortfall.
- Data plumbing: `cash_flow.py` now writes `bau_evn_bill_vnd`, `optimized_evn_bill_vnd`, `bau_demand_charge_vnd`, `optimized_demand_charge_vnd` into each annual row. `report_data.py` exposes `pv_to_grid_effective_kwh`. `xlsx_builder._write_bau_vs_dppa_sheet` reads from both.

## Verification evidence

- 74 unit tests pass: `python -m unittest discover -s proforma_vietnam/tests -t .`
- Hand-checked DPPA settlement math against the full 8760 FMP series (Python script alongside `outputs/vietnam_case/factory_a/case_5/`):
  - CfD net total: hand-computed 3.474 B VND, workbook 3.474 B VND, delta 0.000%
  - C_DN total: hand-computed 8.356 B VND, workbook 8.356 B VND, delta 0.000%
  - Generator FMP revenue: hand 8.807 B VND, workbook matches
  - Generator total revenue (FMP + CfD net): hand 12.281 B VND, workbook matches
- Honest Factory A KPIs after `bess_capex` fix:
  - case_1: capex $2.57M → $3.71M (+$1.13M), equity IRR 30.6% → 18.1%, NPV $2.70M → $1.65M
  - case_2: capex $2.85M → $4.29M (+$1.44M), equity IRR 28.7% → 16.0%, NPV $2.76M → $1.44M
  - case_3: capex $2.95M → $4.88M (+$1.93M), equity IRR 25.0% → 12.3%, NPV $2.43M → $0.65M
  - case_4: unchanged (REopt did not size BESS — true BESS capex $0)
  - case_5: capex $2.85M → $4.29M (+$1.44M), equity IRR 31.3% → 14.5%, NPV $2.09M → $0.77M
- Phase 2 reference workbook gate (`test_reference_esco_workbook.py`) and the new DPPA reference gate (`test_reference_dppa_workbook.py`) both stay green.

## Files changed

- Source:
  - `proforma_vietnam/dppa_settlement.py` (CFMP loader, C_DN formula change, curtailed→export accounting, new sums)
  - `proforma_vietnam/case_builder.py` (bess_capex gating fix, fee_escalation_rate default, CFMP series loading)
  - `proforma_vietnam/esco_pro_forma.py` (DPPA VND→USD conversion, pv_curtailed dispatch wiring)
  - `proforma_vietnam/cash_flow.py` (bau/optimized bill+demand surfaces in annual rows)
  - `proforma_vietnam/report_data.py` (`pv_to_grid_effective_kwh` aggregation)
  - `proforma_vietnam/xlsx_builder.py` (Year 1 BAU vs DPPA sheet)
  - `proforma_vietnam/run_case.py` (POST routing for `dppa_config`)
  - `reoptjl/views.py` (accept `dppa_config` from POST body)
  - `.gitignore` (added `outputs/pvwatts_cache/`, `~$*.xlsx`)
- Tests (74 passing total):
  - `proforma_vietnam/tests/test_dppa_settlement.py` (updated C_DN expectation, +3 new tests for CFMP, curtailed, load_cfmp)
  - `proforma_vietnam/tests/test_esco_pro_forma.py` (+2 new tests for VND→USD conversion + hourly-stays-VND invariant)
  - `proforma_vietnam/tests/test_case_builder.py` (+1 new regression test for bess_capex)
  - `proforma_vietnam/tests/test_run_case.py` (updated POST-body assertions)
- Data assets committed:
  - `DPPA DOC/` (FMP/CFMP JSON series + ND57 PDF set + EVN reports)
- Generated case outputs committed:
  - `outputs/vietnam_case/factory_a/case_1/` through `case_5/` (case.json, payload.json, assumptions.json, results.json, vietnam_report_<uuid>.xlsx)

## Blockers / assumptions / open follow-ups

- Workbook copy `outputs/vietnam_case/factory_a/case_5/vietnam_report_*_v5.xlsx` and Excel lock file `~$...xlsx` could not be removed during the session because Excel was holding them open. Excluded from commit; user needs to close Excel then delete manually.
- Stale pre-layout-migration workbook `outputs/vietnam_case/factory_a/vietnam_report_b729db40-*.xlsx` left in place (untracked). User to decide whether to delete.
- Variable naming smell: `cash_flow.py` uses `_vnd` suffixes throughout for variables that actually carry USD values (because `_money()` normalizes to USD when `reopt_money_values_currency="usd"`). This near-miss naming was the root cause of the unit-mixing bug; a future refactor to rename would reduce risk but touches many files.
- DPPA Annual Summary sheet column labels say "(USD)" and now correctly show USD values after the conversion fix. The Hourly Settlement and Monthly Settlement sheets stay (VND) and that's intentional.
- Under the chosen deal terms (strike 2000 VND/kWh, shaped volume), case_5 is worse than case_2 on every KPI. The CfD at this strike is a one-way buyer→seller transfer because strike > max(FMP) = 1944. To find a bankable strike for both sides, the next session should run a strike sweep (see `CODEX_SESSION.md` resume notes).
- REopt optimizer still sizes against EVN retail tariff under DPPA — aligning the optimizer with FMP is item 4 in Active Product Direction but deferred.

# 2026-06-06 - Phase 3 DPPA Settlement Layer Implementation

- User requested research into Vietnam DPPA settlement under ND57/2025 to design an ESCO contract model, with reference documents staged under `DPPA DOC/`.
- Discovery and design pass (in plan mode):
  - Read `CODEX_SESSION.md`, `SESSION_NOTES.md`, `vietnam_market_context.md`, the Phase 2 design doc, and the seven PDFs + `fmp_cfmp_vn.json` under `DPPA DOC/`.
  - Mapped existing scaffolding: `proforma_vietnam/case_builder.py`, `cash_flow.py`, `esco_pro_forma.py`, `xlsx_builder.py`, `reference_workbook_comparison.py`, `run_case.py`; `reoptjl/views.py` `_vietnam_proforma_overrides`; and `reoptjl/src/vietnam/evn_tariff.py`.
  - Synthesized the ND57 four-layer cost stack (C_DN spot + C_DPPA system fee + C_CL delta + C_BL retail fallback) plus the bilateral CfD overlay from Điều 17–18.
  - User confirmed via AskUserQuestion: (1) ESCO discount-to-EVN is **replaced** (not layered) under grid DPPA; (2) v1 ships `grid_dppa_cfd` (spot path reachable via `Q_c = 0`); (3) FMP series sourced from `DPPA DOC/fmp_cfmp_vn.json`; (4) ESCO is the generator (single-entity model).
  - User refinements: (1) BESS modeled co-located with RE only (factory-side BESS deferred), and (2) signed `cfd_strike_escalation_rate` to support either escalating or step-down strikes per PPA negotiation. Plan file updated and approved at `C:\Users\kongn\.claude\plans\read-the-codex-session-curried-dijkstra.md`.
- Design docs:
  - `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`: appended a Phase 3 DPPA Settlement Layer section with contract type enum, BESS configuration assumption, energy buckets, settlement math, annual escalation rules, cash-flow attribution table, new input fields, and acceptance criteria.
  - `roadmap.md`: added a Phase 3 section with goal, deliverables, acceptance criteria, and "not in Phase 3" list; demoted leftover items to "Deferred (Phase 4+)".
- New module: `proforma_vietnam/dppa_settlement.py`
  - `load_fmp_series(path)` reads `fmp_vnd_per_kwh` from the JSON file at `DPPA DOC/fmp_cfmp_vn.json` (8760 entries; the file also carries `cfmp_vnd_per_kwh` and `_metadata`).
  - `settle_dppa_year_one(*, dppa_inputs, dispatch, evn_energy_rates_vnd_per_kwh)` computes per-hour `C_DN/C_DPPA/C_CL/C_BL/CfD` and aggregates them into year-one totals; `Q_re_meter = pv_to_load + pv_to_grid + storage_to_load + storage_to_grid` accounts for the upstream-of-meter BESS placement.
  - Defaults pinned: `k = 1.026`, `K_pp ∈ {1.008525, 1.027263}`, `delta = 1.0`, `f_dppa = 360 VND/kWh`, `f_cl = 163 VND/kWh`.
  - Returns `year_one` primitives + `hourly_breakout` + `monthly_breakout` + `escalation` rates so the cash flow can apply year-N multipliers.
- `proforma_vietnam/cash_flow.py`:
  - Added optional `dppa_settlement=None` kwarg. When `None`, the Phase 2 code path is byte-identical; when provided, `base_energy_revenue_vnd` and `base_grid_arbitrage_revenue_vnd` are zeroed out, the offtaker post-project cost is rebuilt from `c_dn + c_dppa + c_cl + c_bl + cfd_net + optimized_demand_charge + esco_demand_revenue`, and per-year `c_dn`, `c_dppa`, `c_cl`, `c_bl`, `cfd_net`, `generator_revenue` keys land in each annual row.
  - Year-N escalation: `fee_escalation_rate` for C_DN, C_DPPA, C_CL, FMP-side of CfD, and generator FMP revenue; signed `cfd_strike_escalation_rate` for the strike-side of CfD; `evn_energy_escalation_rate` for C_BL.
  - When DPPA active, top-level `dppa_hourly_breakout` and `dppa_monthly_breakout` are attached to the cash-flow result so downstream consumers can render the new sheets.
- `proforma_vietnam/case_builder.py`:
  - New `_dppa_inputs(dppa_config, voltage_key)` validates the `dppa.type` enum, enforces ND57 Art. 16 voltage eligibility (`110kv_and_above` or `22_to_110kv`), requires `cfd_strike_per_kwh_vnd` + `cfd_contract_volume_kwh_per_hour`, derives `K_pp` from voltage if not supplied, and loads the FMP series via `dppa_settlement.load_fmp_series`.
  - When DPPA is active, `ElectricStorage.can_grid_charge` is forced `False` in the REopt payload (co-located BESS only).
  - When DPPA is active, `assumptions["dppa"]` is populated as a nested dict containing the 8760 FMP series.
- `proforma_vietnam/esco_pro_forma.py`:
  - Accepts `dppa_inputs` via `cash_flow_overrides`. When `type == "grid_dppa_cfd"`, builds the dispatch dict from REopt outputs (load, pv_to_load, pv_to_grid, storage_to_load, storage_to_grid), calls `settle_dppa_year_one`, and threads the result as `dppa_settlement` into `calculate_vietnam_esco_cash_flow`.
- `proforma_vietnam/xlsx_builder.py`:
  - Phase 2 has 11 sheets unchanged when `dppa.type = "none"` or missing.
  - When DPPA is active, adds 4 conditional sheets — DPPA Configuration (key/value), Hourly Settlement (8760 rows), Monthly Settlement (12 rows), DPPA Annual Summary — plus 3 right-edge Cash Flow columns (`generator_revenue_usd`, `cfd_net_usd`, `dppa_offtaker_cost_usd`).
  - `_write_assumptions_sheet` now skips nested dict/list values so the `dppa` block doesn't crash openpyxl.
- `proforma_vietnam/report_data.py`: forwards `dppa_hourly_breakout` and `dppa_monthly_breakout` from the cash-flow result so the workbook builder receives them.
- `proforma_vietnam/run_case.py`: when `assumptions["dppa"]` is present, the entire block is serialized as a single JSON-encoded `dppa_config` GET parameter (one param instead of ten, accommodates the 8760 FMP series).
- `reoptjl/views.py`: `_vietnam_proforma_overrides` decodes `dppa_config` from the request, validates it's a JSON object, records it in `assumptions["dppa"]` for the Assumptions sheet, and passes it as `dppa_inputs` into `calculate_esco_pro_forma_from_reopt_results`.
- `proforma_vietnam/reference_workbook_comparison.py`: existing `compare_reference_workbook(...)` untouched. Added sibling `compare_dppa_reference_workbook(...)` that reads a `DPPA Year One` key/value sheet alongside the Phase 2 `Inputs`/`Reference Summary`/`Reference Annual Cash Flow` sheets and validates the implementation at 1% tolerance.
- Tests added or extended:
  - `proforma_vietnam/tests/test_dppa_settlement.py` (10 tests): hand-computed 24-hour fixture matches `C_DN`, `C_DPPA`, `C_CL`, `C_BL`, CfD, generator revenue, `Q_re_meter`; offtaker cost identity; zero CfD volume reduces to pure spot; scalar volume broadcasts; storage discharge counts toward generator meter; monthly breakout returns 12 entries; `load_fmp_series` reads 8760 values; FMP vs CFMP returned correctly.
  - `proforma_vietnam/tests/test_cash_flow.py` (2 new tests): DPPA replaces ESCO energy revenue with generator revenue; DPPA replaces offtaker post-project cost with `(C_DN+C_DPPA+C_CL+C_BL+CfD) + optimized_demand_charge + esco_demand_revenue`.
  - `proforma_vietnam/tests/test_case_builder.py` (6 new tests): `dppa` block omitted when type is none; populates with defaults and FMP series; forces `can_grid_charge=False`; rejects ineligible voltage; rejects missing `cfd_strike_per_kwh_vnd`/`cfd_contract_volume_kwh_per_hour`; rejects unknown enum value.
  - `proforma_vietnam/tests/test_esco_pro_forma.py` (1 new test): `dppa_inputs` drive the `grid_dppa_cfd` branch and the cash-flow result exposes `c_dn_vnd`/`c_bl_vnd`/`cfd_net_vnd`/`generator_revenue_vnd`.
  - `proforma_vietnam/tests/test_xlsx_builder.py` (3 new tests): DPPA sheets omitted on the `none` path; 4 new sheets present on `grid_dppa_cfd`; Cash Flow gains the 3 DPPA columns.
  - `proforma_vietnam/tests/test_run_case.py` (1 new test): `dppa` block serialized as `dppa_config` JSON query param, not as flat params.
  - `proforma_vietnam/tests/test_reference_dppa_workbook.py` (new file, 1 test): hand-built DPPA reference workbook matches the implementation at 1% tolerance.
- Verification:
  - Green: `python -m unittest discover -s proforma_vietnam.tests` — 68 tests passing, including the Phase 2 reference workbook gate (`test_reference_esco_workbook.py`) which proves the `dppa_settlement=None` default keeps the existing path byte-identical.
  - Green: targeted runs as each module landed (`test_dppa_settlement`, `test_cash_flow`, `test_case_builder`, `test_esco_pro_forma`, `test_xlsx_builder`, `test_run_case`, `test_reference_dppa_workbook`).
  - `reoptjl/views.py` syntax-checked via `python -m py_compile`; Django tests are blocked in this environment (`ModuleNotFoundError: No module named 'django'`) — needs the docker stack.
  - End-to-end docker run on a `case_5` clone is the next manual verification step and is not yet executed.
- Files changed:
  - Modified: `CODEX_SESSION.md`, `SESSION_NOTES.md` (this entry), `roadmap.md`, `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`, `proforma_vietnam/case_builder.py`, `proforma_vietnam/cash_flow.py`, `proforma_vietnam/esco_pro_forma.py`, `proforma_vietnam/reference_workbook_comparison.py`, `proforma_vietnam/report_data.py`, `proforma_vietnam/run_case.py`, `proforma_vietnam/xlsx_builder.py`, `reoptjl/views.py`, plus the five `proforma_vietnam/tests/test_*.py` files for the test additions.
  - New: `proforma_vietnam/dppa_settlement.py`, `proforma_vietnam/tests/test_dppa_settlement.py`, `proforma_vietnam/tests/test_reference_dppa_workbook.py`.
  - Plan file: `C:\Users\kongn\.claude\plans\read-the-codex-session-curried-dijkstra.md` (approved by user; archived plan reference only).
- Git state at close: branch `master`, dirty working tree across the files above plus the still-untracked generated outputs under `outputs/vietnam_case/factory_a/` and `outputs/pvwatts_cache/`. No commit made — Phase 3 is staged for review and waiting on the manual docker validation step.
- Blockers / assumptions:
  - Real-world DPPA case validation against `case_5` was deferred to a docker session because this host lacks Django/Docker reachability.
  - Phase 3 covers only `grid_dppa_cfd` with co-located BESS. `private_wire` (Điều 25) and factory-side BESS are intentionally deferred per the approved plan.
  - REopt optimizer still sizes against EVN-retail tariff under DPPA; aligning the optimizer with FMP is an explicit out-of-scope item.

# 2026-06-06 - CODEX_SESSION Cleanup Before DPPA Settlement Design

- Cleaned `CODEX_SESSION.md` from a long accumulated handoff into a concise resume file.
- Archived the previous active-state context by preserving the important history in this notes file and replacing the live handoff with a short current-state pointer.
- Current git status before cleanup:
  - Branch: `master`
  - Tracking: `master...origin/master [ahead 2]`
  - Pre-existing dirty files/artifacts: `CODEX_SESSION.md`, `SESSION_NOTES.md`, `Sample Load Profile/Emivest.csv`, `outputs/pvwatts_cache/`, and generated Factory A report outputs under `outputs/vietnam_case/factory_a/`.
- No source-code implementation was changed in this cleanup.
- New active direction:
  - Design DPPA settlement as the next product phase.
  - Update `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md` so ESCO cash flow can handle DPPA contract settings.
  - Preserve the existing discount-to-EVN ESCO base case as default behavior.
- Recommended next session flow:
  1. Review `roadmap.md`, `vietnam_market_context.md`, and `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`.
  2. Add a DPPA settlement section to the ESCO contract design with contract settings, hourly equations, required inputs, outputs, and out-of-scope items.
  3. Update `roadmap.md` Phase 3 from deferred bullets into a concrete implementation plan.
  4. Add tests first for the smallest DPPA settlement slice before implementation.

# 2026-05-28 - CEBA Factory A BESS/Solar Case Study Deck

- Built a standalone 10-slide corporate white-background presentation for the CEBA clean-energy procurement workshop:
  - Final PPTX: `C:\Users\kongn\Pictures\CodeProject\CEBA Slide\output\Factory_A_BESS_Solar_Case_Study_CEBA.pptx`.
  - Data source: `outputs\vietnam_case\factory_a\case_1` through `case_4`, especially each case's `vietnam_report_<run_uuid>.xlsx`, `case.json`, and `assumptions.json`.
  - Context sources: `C:\Users\kongn\Pictures\CodeProject\CEBA Slide\Chiến Lược Tích Hợp BESS.pptx` and `C:\Users\kongn\Pictures\CodeProject\CEBA Slide\Soạn thảo tài liệu training BESS Việt Nam.pdf`.
- Narrative:
  - Case 1: current TOU + Solar+BESS.
  - Case 2: QĐ963 TOU + Solar+BESS.
  - Case 3: QĐ963 + two-component/capacity-charge pilot + Solar+BESS.
  - Case 4: QĐ963 TOU + solar-only benchmark.
  - Core conclusion: BESS turns rooftop solar from a simple tariff hedge into a dispatchable procurement asset; under QĐ963, Case 2 adds about `$325k` annual savings and `$1.96M` NPV vs solar-only while cutting payback by about 4.6 years.
- Verification:
  - Exported/rendered with artifact-tool presentation workflow.
  - Contact sheet was visually inspected after export; slide 10 callout was moved after the first QA pass to avoid headline overlap.
  - PPTX package check confirmed 10 slide XML files, zero media files, and no empty media files.
- Added Vietnamese version:
  - Final PPTX: `C:\Users\kongn\Pictures\CodeProject\CEBA Slide\output\Factory_A_BESS_Solar_Case_Study_CEBA_Vietnamese.pptx`.
  - Rebuilt the same 10-slide story in Vietnamese with the same Factory A metrics and corporate white-background style.
  - Vietnamese deck verification: artifact-tool export/render, contact-sheet visual inspection, and PPTX package check confirmed 10 slide XML files, zero media files, and no empty media files.
- Added revised condensed English version:
  - Final PPTX: `C:\Users\kongn\Pictures\CodeProject\CEBA Slide\output\Factory_A_BESS_Solar_Case_Study_CEBA_English_Condensed.pptx`.
  - Reduced the English deck from 10 slides to 7.
  - Condensed the previous slide 4-8 sequence into two table-first slides: a detailed case comparison table and a procurement readout table.
  - Removed bar-chart-style comparison visuals from the condensed section because the user noted they could imply inaccurate precision.
  - Condensed English deck verification: artifact-tool export/render, contact-sheet visual inspection, and PPTX package check confirmed 7 slide XML files, zero media files, and no empty media files.
- Git/worktree note:
  - No repo source code was intentionally changed for this deck.
  - Existing generated Factory A case outputs and `Sample Load Profile/Emivest.csv` remain uncommitted in the working tree.

# Session Notes

Use this file for detailed working-session notes that would make `CODEX_SESSION.md` too long.
At the end of every working session, append or update the latest section here with files changed, checks run, blockers, assumptions, and any context needed to resume.

## 2026-05-27 - Vietnam Case JSON USD Report Currency Update

- User requested the Vietnam case JSON/report currency flow change so outsiders can read all pro forma outputs in USD.
- Updated behavior:
  - Optimizer-facing capex/O&M/storage replacement/debt assumptions remain USD.
  - Vietnam workbook labels now show USD for Summary, Cash Flow, Tax Schedule, Debt Service, Results Comparison, and Developer Financials.
  - `exchange_rate_vnd_per_usd` is only a conversion input for EVN VND tariff inputs or explicitly VND-named overrides.
  - `case_builder.py` report assumptions now prefer `annual_om_usd`, `pv_capex_usd`, and `bess_capex_usd`; `financial.annual_om_vnd` is converted to USD when an exchange rate is supplied.
  - `run_case.py` includes USD report query params in the XLSX download URL.
  - `reoptjl.views._vietnam_proforma_overrides` parses USD report override params and converts legacy VND-named query params to USD if `exchange_rate_vnd_per_usd` is provided.
  - `esco_pro_forma.py` can convert tariff money values from VND to USD only when explicitly passed `tariff_money_values_currency="vnd"` or legacy `reopt_money_values_currency="vnd"`; normal case-builder flow keeps REopt money values USD.
  - `cash_flow.py` adds `_usd` aliases for workbook/report consumption while preserving existing `_vnd` internal keys for compatibility with the reference workbook tests.
- Updated sample artifacts:
  - `outputs/vietnam_case/factory_a/case.json` now describes report outputs as USD.
  - `outputs/vietnam_case/factory_a/CASE_JSON_INPUT_GUIDE.md` now documents USD workbook currency and exchange-rate scope.
- TDD/verification evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_run_case proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder` failed for missing USD assumptions/query params, missing USD workbook labels, and missing USD aliases.
  - Green run: same command passed, 17 tests.
  - Green broader local run: `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 28 tests.
  - Green sample JSON check: `python -m json.tool outputs\vietnam_case\factory_a\case.json > $null`.
  - Local Django endpoint test remains blocked because local Python lacks Django: `python -m unittest reoptjl.test.test_vietnam_proforma_endpoint` failed with `ModuleNotFoundError: No module named 'django'`.
  - Docker endpoint verification is blocked because Docker Desktop is not reachable: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` failed before tests started on missing `//./pipe/dockerDesktopLinuxEngine`.
  - `git diff --check` passed with only CRLF normalization warnings.
- Current git state: branch `codex/vietnam-financial-passthrough` has uncommitted changes across Vietnam passthrough code/tests, `reoptjl/views.py`, `reoptjl/test/test_vietnam_proforma_endpoint.py`, sample artifacts under `outputs/vietnam_case/factory_a/`, and updated handoff files.

## 2026-05-26 - Vietnam Case JSON Financial Passthrough

- User approved and requested implementation of the Vietnam case JSON financial passthrough plan.
- Created feature branch `codex/vietnam-financial-passthrough` from local `master`; `master` was already 10 commits ahead of `origin/master`.
- TDD red run:
  - `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_run_case reoptjl.test.test_vietnam_proforma_endpoint` failed for the expected missing passthrough behavior in the case builder and run-case query flow.
  - The local endpoint test import also failed with `ModuleNotFoundError: No module named 'django'`, consistent with the host Python environment lacking Django; endpoint verification was deferred to Docker/Django.
- Implemented:
  - `proforma_vietnam/case_builder.py` now explicitly allowlists financial payload fields, report assumptions, PV cost/O&M fields, and storage cost/O&M fields.
  - `financial.owner_discount_rate_fraction` maps into the REopt payload and report assumptions.
  - Report assumptions now include allowlisted debt fields and `annual_om_vnd`; unsupported financial/ESCO keys are not passed through.
  - Storage `can_grid_charge` defaults from `esco_contract.grid_charging_enabled` when not explicitly supplied in storage config.
  - `proforma_vietnam/run_case.py` now sends allowlisted assumptions as XLSX endpoint query params instead of only `esco_energy_discount_fraction`.
  - `reoptjl/views.py` now parses optional Vietnam pro forma query params into `cash_flow_overrides`, including `annual_om_vnd`, capex overrides, debt terms, demand-savings share, and grid-charging flag.
- Added tests:
  - `proforma_vietnam/tests/test_case_builder.py::test_maps_allowlisted_financial_and_cost_assumptions`
  - `proforma_vietnam/tests/test_run_case.py::test_dry_run_writes_financial_report_assumptions`
  - `proforma_vietnam/tests/test_run_case.py::test_download_report_uses_allowlisted_assumption_query_params`
  - `reoptjl/test/test_vietnam_proforma_endpoint.py::test_results_endpoint_applies_vietnam_proforma_query_overrides`
- Verification:
  - `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_run_case` passed, 7 tests.
  - `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_run_case proforma_vietnam.tests.test_esco_pro_forma` passed, 9 tests.
  - `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 25 tests.
  - `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 25 tests, with `System check identified no issues (0 silenced).`
  - `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 2 tests, with `System check identified no issues (0 silenced).`
  - `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test, with `System check identified no issues (0 silenced).`
- Current state:
  - Changes are uncommitted on branch `codex/vietnam-financial-passthrough`.
  - Next recommended step is to commit this branch or merge/push it after review.
  - Next product validation remains one representative custom 8760 load case end-to-end with generated `vietnam_report_<run_uuid>.xlsx` inspection.

## 2026-05-26 - Diff Review, Verification, and Commit

- User asked to review the current uncommitted backend-first Vietnam case-builder/report-generator diff, rerun focused verification, and commit the slice if clean.
- Reviewed changed areas:
  - `proforma_vietnam/case_builder.py`
  - `proforma_vietnam/report_data.py`
  - `proforma_vietnam/run_case.py`
  - `proforma_vietnam/xlsx_builder.py`
  - `reoptjl/views.py`
  - related tests and handoff notes.
- Review finding:
  - The V3 Vietnam pro forma XLSX endpoint requires `esco_energy_discount_fraction`, but the case builder could previously produce assumptions with that value missing.
  - Added a narrow validation in `proforma_vietnam/case_builder.py` to require `esco_contract.esco_energy_discount_fraction`.
  - Added `test_requires_esco_energy_discount_for_report_download` in `proforma_vietnam/tests/test_case_builder.py`.
- Verification run:
  - `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 22 tests.
  - First `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` attempt failed before tests because Docker Desktop's Linux engine pipe was unavailable.
  - `docker info` confirmed the Docker client existed but the server was offline.
  - Started Docker Desktop and reran `docker info`; server became available.
  - `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 22 tests, with `System check identified no issues (0 silenced).`
  - `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` was first run in parallel with the API test and failed creating duplicate `test_reopt`; serial rerun passed, 1 test, with `System check identified no issues (0 silenced).`
- Commit action:
  - Stage and commit the backend-first Vietnam case builder/report generator slice after verification.
- Remaining next tasks:
  - Push local commits to `origin/master` if desired.
  - Extend case JSON financial passthrough beyond `analysis_years` before relying on custom owner discount rate, debt fraction/rate, O&M, capex, or ESCO cash-flow overrides.
  - Run one representative custom 8760 load case end-to-end and inspect the generated `vietnam_report_<run_uuid>.xlsx`.

## 2026-05-26 - Custom Input Run Guidance Handoff

- User asked how to run the new backend-first Vietnam case builder with custom input load and financial assumptions and how to get the actual report.
- Verified current implementation shape before answering:
  - `proforma_vietnam/case_builder.py` reads an 8760 hourly load CSV from the first column, builds `ElectricLoad.loads_kw`, builds Vietnam EVN tariff arrays, maps `financial.analysis_years`, defaults `ElectricStorage.can_grid_charge` to false, and stores ESCO/report assumptions.
  - `proforma_vietnam/run_case.py` supports `--dry-run` to write `payload.json` and `assumptions.json`, and a full run path that submits to `/v3/job/`, polls results, writes `results.json`, and downloads `vietnam_report_<run_uuid>.xlsx`.
- Guidance given to user:
  - Create an 8760-row kW CSV with optional header, no negative values.
  - Create a case JSON containing `case`, `site`, `load_profile`, `tariff`, `technologies`, `financial`, and `esco_contract` sections.
  - Start Docker with `docker-compose up -d`.
  - Run dry-run:
    `python -m proforma_vietnam.run_case --case input_files\vietnam_case_factory_a.json --out outputs\vietnam_case\factory_a --dry-run`
  - Run actual optimization/report:
    `python -m proforma_vietnam.run_case --case input_files\vietnam_case_factory_a.json --out outputs\vietnam_case\factory_a --poll-seconds 5 --max-polls 120`
  - Expected outputs: `payload.json`, `assumptions.json`, `results.json`, and `vietnam_report_<run_uuid>.xlsx`.
- Important limitation documented for next session:
  - The current case JSON financial passthrough is minimal: `financial.analysis_years` maps into the REopt payload, and `esco_contract.esco_energy_discount_fraction` drives the Vietnam report download.
  - Custom owner discount rate, debt fraction/rate, O&M, capex, and ESCO cash-flow overrides are not yet fully mapped from case JSON.
- Recommended next task:
  - Add tests and implementation for explicit financial/technology/ESCO passthrough in `proforma_vietnam/case_builder.py` and downstream report assumptions before running a real customer-style custom financial case.
  - Then run one representative custom 8760 load case end-to-end and inspect the generated XLSX report.

## 2026-05-25 - Backend Vietnam Case Builder and Report Generator

- Implemented the backend-first Vietnam case builder + report generator slice requested after reviewing the existing REopt webtool/report assets.
- Added `proforma_vietnam/case_builder.py`:
  - Reads a case config dictionary.
  - Loads an 8760 hourly CSV load profile from `load_profile.path`.
  - Builds a normal REopt V3 payload using existing Vietnam EVN tariff builder output.
  - Defaults to Vietnam, 25-year analysis, `tou_schedule="current"`, grid charging disabled, and 80% ESCO demand-savings share.
  - Returns both `payload` and report `assumptions`.
- Added `proforma_vietnam/report_data.py`:
  - Normalizes raw V3 results into report sections for system sizing, dispatch profile, annual electricity production, results comparison, load duration, and developer financial performance.
  - Keeps report data separate from workbook formatting so the same normalized object can later feed HTML/PDF/UI outputs.
- Added `proforma_vietnam/run_case.py`:
  - CLI entry point: `python -m proforma_vietnam.run_case --case path\to\case.json --out outputs\vietnam_case\factory_a --dry-run`.
  - Dry-run writes `payload.json` and `assumptions.json` without API calls.
  - Non-dry-run submits to `/v3/job/`, polls `/v3/job/<run_uuid>/results`, writes `results.json`, and downloads `vietnam_report_<run_uuid>.xlsx` when status is `optimal`.
- Expanded `proforma_vietnam/xlsx_builder.py`:
  - Existing sheets remain: Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions.
  - New sheets: System Sizing, Results Comparison, Annual Production, Dispatch Profile, Load Duration, Developer Financials.
  - Added basic Excel charts for annual production, dispatch, load duration, and developer financials using `openpyxl` charts.
- Updated `reoptjl/views.py`:
  - V3 Vietnam pro forma XLSX response now builds normalized report data from REopt results and passes it into the workbook builder.
- Updated tests:
  - `proforma_vietnam/tests/test_case_builder.py`
  - `proforma_vietnam/tests/test_report_data.py`
  - `proforma_vietnam/tests/test_run_case.py`
  - `proforma_vietnam/tests/test_xlsx_builder.py`
  - `reoptjl/test/test_vietnam_proforma_endpoint.py`
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_report_data proforma_vietnam.tests.test_xlsx_builder` failed with missing `proforma_vietnam.case_builder`, missing `proforma_vietnam.report_data`, missing `report_data` workbook parameter, and missing workbook sheets.
  - Red run: `python -m unittest proforma_vietnam.tests.test_run_case` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.run_case'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_case_builder proforma_vietnam.tests.test_report_data proforma_vietnam.tests.test_xlsx_builder` passed, 8 tests.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_run_case` passed, 1 test.
  - Green local discovered suite: `python -m unittest discover -s proforma_vietnam\tests -p "test_*.py"` passed, 21 tests.
  - Green Docker/Django Vietnam suite: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 21 tests, `System check identified no issues (0 silenced).`
  - Green Docker/Django API integration: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - Green Docker/Django US pro forma regression: `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test.
  - Green Django health: `docker-compose run --rm --entrypoint python django manage.py check` passed with `System check identified no issues (0 silenced).`
  - `docker-compose exec -T django python manage.py check` failed only because the long-running `django` service was not running; the disposable Django container check passed.
- Current git state:
  - Branch `master` is 9 commits ahead of `origin/master`.
  - Latest commit remains `5e219339 Add reference ESCO workbook comparison gate`.
  - Working tree has uncommitted case-builder/report-generator changes.
- Next recommended work:
  - Review/stage the current uncommitted diff.
  - Optionally run one real case through `proforma_vietnam.run_case` without `--dry-run` after preparing a representative 8760 load CSV case config.
  - Commit and push the backend-first case-builder/report-generator slice if accepted.

## 2026-05-25 - Reference ESCO Workbook Comparison Gate

- Started from the `CODEX_SESSION.md` resume point: compare one reference ESCO project against a hand-built workbook within +/-1%.
- Added `proforma_vietnam/reference_workbook_comparison.py`:
  - Reads a workbook object or workbook path.
  - Expects sheets named `Inputs`, `Reference Summary`, and `Reference Annual Cash Flow`.
  - Converts comma-separated hourly/project arrays from the Inputs sheet into `calculate_vietnam_esco_cash_flow(...)` inputs.
  - Compares each workbook-provided summary metric and annual row field against calculated results.
  - Returns readable discrepancy strings when any value is outside the default 1% tolerance.
- Added `proforma_vietnam/tests/test_reference_esco_workbook.py`:
  - Builds a deterministic workbook-style reference case in memory.
  - Reference project uses VND capex/debt/equity, 25 project years, 4% EVN escalation, 65% debt, 8.5% debt rate, 10-year amortization, 20-year PV depreciation, 8-year BESS depreciation, and Vietnam CIT holiday/reduced/standard periods.
  - Reference Summary includes total capex, debt principal, equity investment, project IRR, equity IRR, NPV, average DSCR, simple payback, and ROI.
  - Reference Annual Cash Flow includes all 25 annual rows for ESCO revenue, depreciation, CIT, cash available for debt service, debt service, and equity cash flow.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_reference_esco_workbook` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.reference_workbook_comparison'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_reference_esco_workbook` passed, 1 test.
  - Green local Phase 2 suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder proforma_vietnam.tests.test_reference_esco_workbook` passed, 16 tests.
  - Green Docker/Django Phase 2 suite: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 16 tests, `System check identified no issues (0 silenced).`
  - Green Docker/Django US pro forma regression: `docker-compose run --rm --entrypoint python django manage.py test proforma -v 2` passed, 1 test, `System check identified no issues (0 silenced).`
- Current git state after this work:
  - New files: `proforma_vietnam/reference_workbook_comparison.py`, `proforma_vietnam/tests/test_reference_esco_workbook.py`.
  - Existing uncommitted files from prior Phase 2/API/domain migration work remain in the working tree, including `reoptjl/views.py`, `reoptjl/test/test_vietnam_proforma_endpoint.py`, `resilience_stats/migrations/0017_alter_erpmeta_job_type.py`, docs, and domain migration edits.
- Phase 2 acceptance gates in `CODEX_SESSION.md` are now marked complete.
- Next recommended work: review the full uncommitted diff, then decide whether to create a commit/push for Phase 2 and the NLR migration changes or run one final full-stack smoke check first.

## 2026-05-25 - NLR Developer Domain Migration

- User provided the NLR developer-team notice that `developer.nrel.gov` is retiring and API calls must move to `developer.nlr.gov`; user also asked to replace `@NREL.gov` email domains with `@NLR.gov`.
- Searched active repo references for `developer.nrel.gov`, `developer.nlr.gov`, `@nrel.gov`, and `@nlr.gov`.
- Found the actual failed solar lookup path in the installed Julia `REopt.jl` dependency inside the Julia container:
  - `/root/.julia/packages/REopt/CGBoo/src/core/utils.jl` used `https://developer.nrel.gov/api/solar/data_query/v2.json` and `https://developer.nrel.gov/api/pvwatts/v8.json`.
  - `/root/.julia/packages/REopt/CGBoo/src/core/production_factor.jl` used `https://developer.nrel.gov/api/wind-toolkit/v2/wind/wtk-srw-download`.
  - `/root/.julia/packages/REopt/CGBoo/src/core/cst_ssc.jl` used `http://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-tmy-v4-0-0-download.csv`.
- Tried `Pkg.update()` in the Julia container; it updated many package pins and still left the old developer domain in `REopt.jl`, so reverted the accidental `julia_src/Manifest.toml` churn and used a targeted patch instead.
- Updated `julia_src/Dockerfile` so future Julia image builds rewrite `developer.nrel.gov` to `developer.nlr.gov` inside installed `REopt.jl` package sources immediately after `Pkg.instantiate()`.
- Patched the currently running Julia container's installed `REopt.jl` package with the same replacement and restarted the Julia service.
- Verified the current Julia package URLs now point to `developer.nlr.gov` for solar data query, PVWatts, wind toolkit, and NSRDB.
- Rebuilt `reopt_api-julia:latest`; the build command exceeded the client timeout, but Docker reported the image was created at `2026-05-25 17:24:10 +0700`.
- Recreated the Julia service with `docker-compose up -d julia`, waited for `Listening on: 0.0.0.0:8081`, and verified the newly created container still had `developer.nlr.gov` in all four `REopt.jl` resource URLs.
- Updated active resilience ERP metadata defaults:
  - `resilience_stats/api.py`: authenticated developer job type now uses `developer.nlr.gov`.
  - `resilience_stats/models.py`: `ERPMeta.job_type` default now uses `developer.nlr.gov`.
  - Added `resilience_stats/migrations/0017_alter_erpmeta_job_type.py`.
  - Applied the migration with `docker-compose exec -T django python manage.py migrate resilience_stats`; result: `OK`.
- Updated email/domain text:
  - `README.md` developer docs links now use `https://developer.nlr.gov/...` and "NLR Developer Network".
  - `CONTRIBUTING.md` support email now uses `reopt@nlr.gov`.
  - `reoptjl/validators.py` and `reo/src/wind_resource.py` comments now use `Jordan.Perr-Sauer@nlr.gov`.
- Verification:
  - `docker-compose exec -T django python manage.py check` passed with `System check identified no issues (0 silenced).`
  - `docker-compose exec -T django python manage.py makemigrations --check --dry-run` returned `No changes detected`.
  - `docker-compose exec -T django python manage.py test reoptjl.test.test_vietnam_tariff -v 2` passed, 8 tests.
  - `GET http://localhost:8000/v3/job/inputs/` returned HTTP 200.
  - Re-ran the actual Vietnam tariff payload without explicit `PV.production_factor_series`; run UUID `56b65e70-d18d-4eaf-a3ef-8d91ed00ecee` reached status `optimal`.
  - Re-ran the same actual Vietnam tariff payload again after rebuilding and recreating the Julia image; run UUID `0b1fa767-9b18-4d8c-8153-7b169ca570ff` reached status `optimal`.
- One false-start check occurred: run UUID `d16ea993-64c8-4086-80f4-366e0831209b` failed because it was submitted while Julia was still precompiling after restart, so Celery could not connect to `julia:8081`.
- Remaining old `developer.nrel.gov` references from `rg` are historical only: old migrations, old changelog entries, and session notes documenting the prior failure.

## 2026-05-25 - Actual Vietnam Payload Workbook Generation

- Ran `docker-compose ps`; the local Docker stack had `julia`, `celery`, `db`, `django`, and `redis` running.
- First attempted a fresh actual Vietnam tariff payload with `docker-compose exec -T django python -m reoptjl.src.vietnam.example_submit`.
- First run UUID: `991b8b06-19f5-4489-a0f9-66a37ec9a034`.
- Polling showed the job moved from `Optimizing...` to status `error`.
- Root cause from `/v3/job/<run_uuid>/results`: Julia called the external Solar Dataset Query API at `developer.nrel.gov` and received HTTP 410 during the scheduled domain-transition brownout. The error message says `developer.nrel.gov` will be shut down on May 29, 2026 and users must update references to `developer.nlr.gov`.
- Submitted a second fresh actual Vietnam tariff payload using the same `current` Vietnam tariff builder output, but with an explicit 8760 `PV.production_factor_series` so the optimizer did not need the external solar data lookup.
- Second run UUID: `e685ae81-a3c1-4f5c-bdc1-27c899d58bc2`.
- Polling reached status `optimal`.
- Expected non-US warnings remained for AVERT, Cambium, and EASIUR lookups at Vietnam coordinates.
- Exported the Vietnam ESCO workbook with:
  - URL: `/v3/job/e685ae81-a3c1-4f5c-bdc1-27c899d58bc2/results?vietnam_proforma=true&esco_energy_discount_fraction=0.9`.
  - Saved file: `outputs/vietnam_proforma_actual_payload/vietnam_proforma_e685ae81-a3c1-4f5c-bdc1-27c899d58bc2.xlsx`.
- Inspected workbook with the spreadsheet artifact tooling:
  - Sheets present: Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions.
  - Summary values: total capex `1565427.256` VND, debt principal `1095799.0792` VND, equity investment `469628.1768` VND, project IRR `0.0675201042`, equity IRR `0.0599040158`, NPV `-31274.7858` VND, average DSCR `0.6762940888`, simple payback `16.8347` years, ROI `4.2094`.
  - Cash Flow shows ESCO energy revenue only; ESCO demand revenue and grid arbitrage revenue are zero for this synthetic actual payload.
  - Tax Schedule shows CIT holiday years 1-8 in this case because taxable income remains non-positive into the reduced-rate period; CIT begins in year 9.
  - Formula-error scan found no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or `#N/A` tokens.
- Rendered all five workbook sheets to PNG under `outputs/vietnam_proforma_actual_payload/rendered/`.
- Visual inspection of Summary, Cash Flow, and Tax Schedule previews showed values and headers were legible.
- Interpretation: the generated workbook path works against an actual optimized Vietnam tariff payload, but this synthetic case is not financially viable at the chosen assumptions; average DSCR is below 1 and NPV is negative.
- Next recommended work: compare one reference ESCO project against a hand-built workbook within +/-1%, then rerun Docker tests for `proforma_vietnam` and `proforma` before marking Phase 2 complete.

## 2026-05-25 - Phase 2 Vietnam Pro Forma XLSX API Flow

- Added the V3 query-param flow on the existing results endpoint:
  - `GET /v3/job/<run_uuid>/results?vietnam_proforma=true&esco_energy_discount_fraction=<fraction>`
  - Returns an XLSX blob with content type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
  - Uses filename `vietnam_proforma_<run_uuid>.xlsx`.
  - Leaves the standard JSON response unchanged when `vietnam_proforma` is absent.
- Implemented the endpoint branch in `reoptjl/views.py` by:
  - detecting `vietnam_proforma` values `true`, `1`, or `xlsx`,
  - requiring `esco_energy_discount_fraction`,
  - passing the already-built V3 results dictionary into `calculate_esco_pro_forma_from_reopt_results(...)`,
  - passing the cash-flow result into `build_vietnam_esco_workbook(...)`,
  - returning the workbook bytes directly in the HTTP response.
- Added `reoptjl/test/test_vietnam_proforma_endpoint.py` as the API integration test:
  - creates a small completed V3 run directly in the test database,
  - calls the results endpoint with the Vietnam pro forma query params,
  - verifies HTTP 200, XLSX content type, attachment filename, required workbook sheets, and key Summary/Assumptions cells.
- TDD evidence:
  - Red run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` failed because the endpoint still returned `application/json`.
  - Green focused run: `docker-compose run --rm --entrypoint python django manage.py test reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 1 test.
  - Green local pro forma run: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder` passed, 15 tests.
  - Green combined Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam reoptjl.test.test_vietnam_proforma_endpoint -v 2` passed, 16 tests, `System check identified no issues (0 silenced).`
  - `git diff --check` returned only the existing LF-to-CRLF warning for `reoptjl/views.py`.
- Current git state after this work: branch `master` is 8 commits ahead of `origin/master`; latest commit is `b1e722ee`; `reoptjl/views.py`, `reoptjl/test/test_vietnam_proforma_endpoint.py`, `CODEX_SESSION.md`, and `SESSION_NOTES.md` have uncommitted changes.
- Next recommended work:
  - Generate a workbook from a real completed Vietnam tariff run using `vietnam_proforma=true&esco_energy_discount_fraction=0.9`.
  - Inspect the workbook sheets and key values.
  - Then start the reference ESCO project comparison against a hand-built workbook within +/-1%.

## 2026-05-25 - Phase 2 Vietnam XLSX Workbook Builder

- Resumed from `CODEX_SESSION.md`, `roadmap.md`, `AGENTS.md`, and the latest Phase 2 notes.
- Implemented `proforma_vietnam/xlsx_builder.py` as a standalone `openpyxl` workbook builder.
- Added `proforma_vietnam/tests/test_xlsx_builder.py` covering:
  - required sheet order: Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions,
  - key Summary values: total capex, debt principal, equity investment, NPV, and equity IRR,
  - representative annual values in Cash Flow, Tax Schedule, and Debt Service,
  - passed-through Assumptions values.
- Workbook behavior:
  - Accepts the dictionary returned by `calculate_vietnam_esco_cash_flow(...)`.
  - Writes summary metrics from `result["summary"]`.
  - Writes annual cash-flow rows from `result["annual_cash_flows"]`.
  - Splits tax and debt views into dedicated sheets using the same annual row data.
  - Keeps the builder independent from Django, V3 API routing, and response serialization.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.xlsx_builder'`.
  - First green attempt caught one bad test assertion around the Cash Flow column order; corrected the assertion to match the declared workbook columns.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_xlsx_builder` passed, 4 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_xlsx_builder` passed, 15 tests.
  - Green Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 15 tests, `System check identified no issues (0 silenced).`
- Current git state after this work: branch `master` remains at commit `268af7be`; `CODEX_SESSION.md`, `SESSION_NOTES.md`, `proforma_vietnam/cash_flow.py`, `proforma_vietnam/esco_pro_forma.py`, `proforma_vietnam/xlsx_builder.py`, and the three Phase 2 test files have uncommitted changes.
- Next recommended work:
  - Add a V3 Vietnam pro forma XLSX download endpoint or query-param flow.
  - Add an API integration test for the XLSX response.
  - Run one actual Vietnam tariff payload through the endpoint/workbook before starting the hand-built workbook comparison.

## 2026-05-25 - Phase 2 Vietnam REopt Results Adapter

- Resumed from `CODEX_SESSION.md`, `roadmap.md`, `AGENTS.md`, and the latest `SESSION_NOTES.md` entry.
- Implemented `proforma_vietnam/esco_pro_forma.py` as the Phase 2 adapter from V3 `/results` dictionaries into `calculate_vietnam_esco_cash_flow(...)`.
- Added `proforma_vietnam/tests/test_esco_pro_forma.py` with a small fake V3 result payload.
- Adapter behavior:
  - Reads 8760 EVN energy rates from `inputs.ElectricTariff.tou_energy_rates_per_kwh`.
  - Reads BAU/optimized year-one bills and demand charges from `outputs.ElectricTariff`.
  - Reads PV direct-to-load series from `outputs.PV.electric_to_load_series_kw`.
  - Includes `outputs.ElectricStorage.storage_to_load_series_kw` in ESCO energy only when `inputs.ElectricStorage.can_grid_charge` is explicitly false.
  - Keeps grid-charging arbitrage disabled because the available V3 payload does not expose grid-charged battery discharge attribution.
  - Uses PV output size and installed cost for PV capex, storage output initial capital cost when available, and year-one O&M from `outputs.Financial.year_one_om_costs_before_tax`.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.esco_pro_forma'`.
  - Green focused run: `python -m unittest proforma_vietnam.tests.test_esco_pro_forma` passed, 2 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma` passed, 11 tests.
  - Green Docker/Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 11 tests, `System check identified no issues (0 silenced).`
- Representative V3 payload inspection:
  - Started Django with `docker-compose up -d django`.
  - `Invoke-WebRequest` closed unexpectedly on the large response, but `curl.exe` successfully saved the JSON response for run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d`.
  - Confirmed output keys: `Financial`, `ElectricTariff`, `ElectricUtility`, `ElectricLoad`, `Site`, `PV`, `ElectricStorage`.
  - Confirmed relevant shapes: 8760 `inputs.ElectricTariff.tou_energy_rates_per_kwh`, 8760 `outputs.PV.electric_to_load_series_kw`, empty `outputs.ElectricStorage.storage_to_load_series_kw`, and `inputs.ElectricStorage.can_grid_charge=true`.
  - Adapter smoke call against the saved payload completed without shape errors and returned zero `esco_grid_arbitrage_revenue_vnd`.
- Current git state after this work: branch `master` is 7 commits ahead of `origin/master`; `CODEX_SESSION.md`, `SESSION_NOTES.md`, `proforma_vietnam/cash_flow.py`, `proforma_vietnam/esco_pro_forma.py`, `proforma_vietnam/tests/test_cash_flow.py`, and `proforma_vietnam/tests/test_esco_pro_forma.py` have uncommitted changes.
- Next recommended work:
  - Add `proforma_vietnam/xlsx_builder.py` with Summary, Cash Flow, Tax Schedule, Debt Service, and Assumptions sheets.
  - Add workbook tests that verify required sheets and key summary values.
  - Keep the workbook builder independent from Django until the workbook tests are green.

## 2026-05-25 - Phase 2 Vietnam Cash Flow Slice

- Implemented the first standalone Vietnam ESCO DCF module in `proforma_vietnam/cash_flow.py`.
- Added `calculate_vietnam_esco_cash_flow(...)` as a pure function that returns:
  - annual cash-flow rows,
  - total capex, debt principal, and equity investment,
  - project IRR, equity IRR, NPV, average DSCR, simple payback, and ROI.
- Formula coverage:
  - ESCO energy revenue uses project-served PV kWh times time-specific EVN energy rates times the ESCO discount fraction.
  - Energy revenue escalates with `evn_energy_escalation_rate`, default 4%.
  - Demand-charge savings are `max(BAU demand charge - optimized demand charge, 0)`.
  - Demand-charge savings escalate with `evn_capacity_escalation_rate`, default 4%.
  - ESCO demand-savings share defaults to 80%; offtaker retained share is the remaining 20%.
  - Grid charging remains disabled by default.
  - When grid charging is enabled, ESCO receives 100% of positive net grid-arbitrage value by default.
  - PV depreciation uses the existing 20-year straight-line helper; BESS depreciation uses the existing 8-year helper.
  - CIT uses the existing Vietnam holiday/reduced-rate helper.
  - Debt service uses a fixed annual amortizing payment with default 70% debt, 8.5% interest, and 10-year term.
- Added `proforma_vietnam/tests/test_cash_flow.py` covering:
  - discounted time-specific ESCO energy revenue,
  - default 80/20 demand-charge savings split,
  - base-case grid charging disabled behavior,
  - optional grid-charging arbitrage settlement,
  - investor metric outputs and Vietnam depreciation/CIT integration.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_cash_flow` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.cash_flow'`.
  - Green local run: `python -m unittest proforma_vietnam.tests.test_cash_flow` passed, 5 tests.
  - Green local suite: `python -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow` passed, 9 tests.
  - First Docker unittest attempt failed before tests started with Docker Desktop API error reading `base-api-image:latest`.
  - Docker investigation showed `docker info` succeeded and `base-api-image:latest` existed; rerun passed.
  - Green Docker unittest run: `docker-compose run --rm --entrypoint python django -m unittest proforma_vietnam.tests.test_tax_model proforma_vietnam.tests.test_cash_flow` passed, 9 tests.
  - Green Docker Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam -v 2` passed, 9 tests, `System check identified no issues (0 silenced).`
- Current git state after this work: branch `master` is 7 commits ahead of `origin/master`; `CODEX_SESSION.md`, `SESSION_NOTES.md`, `proforma_vietnam/cash_flow.py`, and `proforma_vietnam/tests/test_cash_flow.py` have uncommitted changes.
- Next recommended work: review the `cash_flow.py` interface against one representative REopt result payload, then add `esco_pro_forma.py` as the adapter before starting XLSX/API integration.
- Resume point for next session:
  - Start in `proforma_vietnam/esco_pro_forma.py`.
  - First read `proforma_vietnam/cash_flow.py`, `proforma_vietnam/tests/test_cash_flow.py`, and `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`.
  - Inspect one representative V3 result payload shape before writing adapter code.
  - Write failing adapter tests with a small fake V3 results payload, then implement the adapter.
  - Keep grid charging disabled unless the V3 result payload clearly separates grid-charged battery discharge from PV-charged discharge.
- Phase 2 completion order before the final real-payload evaluation:
  1. REopt-results adapter: `proforma_vietnam/esco_pro_forma.py`.
  2. Adapter tests: `proforma_vietnam/tests/test_esco_pro_forma.py`.
  3. Workbook builder: `proforma_vietnam/xlsx_builder.py` with Summary, Cash Flow, Tax Schedule, Debt Service, and Assumptions sheets.
  4. Workbook tests: verify sheets, year rows, and key summary values.
  5. V3 Vietnam pro forma download endpoint or query-param flow.
  6. API integration test for the XLSX response.
  7. One actual Vietnam tariff payload run through the endpoint/workbook.
  8. Hand-built workbook comparison within +/-1%.
  9. Docker verification for `proforma_vietnam` and existing `proforma` tests.

## 2026-05-25 - Vietnam ESCO Contract Design Finalized

- Clarified that the calculation sequence is technical optimization first, then Vietnam ESCO pro forma. ROI, IRR, NPV, DSCR, and payback are outputs, not initial sizing inputs.
- User selected discount-to-EVN-tariff energy pricing:
  - Discount applies to time-specific current-year EVN energy tariff.
  - Discount applies to energy charge only, not demand/capacity value.
  - ESCO tariff escalation is pegged back-to-back to EVN escalation.
- User selected demand-charge savings handling:
  - Demand-charge savings are calculated from REopt results.
  - Default split is 80% ESCO / 20% offtaker.
- User selected grid-charging handling:
  - Grid charging is an optional scenario switch and disabled in the base case.
  - If enabled, net grid-charging arbitrage value belongs 100% to ESCO.
  - Grid charging cost must remain in the optimized EVN bill; ESCO receives net arbitrage value, not gross battery discharge revenue.
- Added `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md` as the finalized design source for the next `cash_flow.py` implementation.
- Updated `proforma_vietnam/ESCO_CONTRACT_MODEL_NOTES.md` to point to the finalized design.
- Next recommended work: write focused cash-flow tests for ESCO energy revenue, demand savings split, grid-charging disabled base case, and optional grid-arbitrage settlement before implementing `proforma_vietnam/cash_flow.py`.

## 2026-06-12 - CEBA DPPA Buyer Decision Journey Deck Delivery

- Built and delivered
  `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`.
- Deck structure: 30 editable artifact-tool slides comprising a 24-slide,
  45-minute main training story and 6 backup slides.
- Presenter line: Cong Nguyen, Vietnam Clean Energy Manager, Allotrope
  Partners.
- Narrative: factory-buyer decision journey from EVN BAU baseline through
  DPPA bill mechanics, offer testing, buyer/seller/lender gates, Factory A
  Case 5/6 evidence, and term-sheet negotiation questions.
- Preserved the prior deck and script:
  `outputs/ceba_training/CEBA_DPPA_Mechanisms_Pricing.pptx` and
  `outputs/ceba_training/build_deck.py`.
- Current-source basis:
  - Decree 57/2025/ND-CP and primary-source status checked through 2026-06-12.
  - Current EVN manufacturing tariff and current applied TOU status separated
    from the published-but-not-yet-applied Decision 963 time bands.
  - Numerical Kpp, 360 VND/kWh service fee, and 163.3 VND/kWh balancing
    examples are explicitly labeled as NSMO training/model assumptions, not
    confirmed current regulated values.
- Factory A evidence used:
  - Case 5: equity IRR 16.9%, minimum DSCR 1.14x, buyer lifetime -9.3%.
  - Case 6: equity IRR 26.9%, minimum DSCR 1.50x, buyer lifetime -14.4%.
  - Closest buyer-positive Case 6 test: 1,300 VND/kWh at 70% volume; buyer
    lifetime +0.46%, seller equity IRR 17.85%, minimum DSCR 1.143x.
  - Zero of 56 tested Case 6 scenarios passed buyer, seller, and lender gates
    together; the deck does not generalize this to all Vietnam DPPAs.
- Verification:
  - `node qa/data-ledger-check.mjs`: `data ledger checks passed`.
  - Full final layout QA: 30 files, `0 error(s), 0 warning(s)`.
  - Final-export contact sheet inspected at thumbnail size; slides 22, 25, and
    30 inspected full-size.
  - QA scorecard: 40/45, with no dimension below 4.
  - PPTX package: 30 slide XML parts, 30 notes-slide parts, 0 empty files,
    0 media dependencies, 142,614 bytes.
- Fresh delegated final-section review attempts were blocked by the subagent
  usage limit. Earlier section reviews passed; the final section was reviewed
  locally.
- Next direction: run a financing sensitivity around the buyer-positive
  Case 6 `1,300 VND/kWh` / 70% volume terms, including FX sensitivity before
  investor-facing use.

## 2026-05-23 - Phase 2 Vietnam Tax Model Start

- Started Phase 2 Vietnam pro forma work in a new standalone `proforma_vietnam/` package.
- Added `proforma_vietnam/tax_model.py` with:
  - Standard Vietnam CIT rate constant: 20%.
  - CIT holiday: 4 years exempt.
  - CIT reduced period: 9 years at 50% of the standard rate, effective 10%.
  - PV straight-line depreciation period: 20 years, per user correction on 2026-05-23.
  - BESS straight-line depreciation period: 8 years.
  - `calculate_cit(...)` and `straight_line_depreciation_schedule(...)` pure helpers.
- Added `proforma_vietnam/tests/test_tax_model.py` covering:
  - 25-year CIT sequence for constant taxable income.
  - No CIT on negative or zero taxable income.
  - PV 20-year straight-line depreciation with zero depreciation after year 20.
  - BESS 8-year straight-line depreciation with zero depreciation after year 8.
- TDD evidence:
  - Red run: `python -m unittest proforma_vietnam.tests.test_tax_model` failed with `ModuleNotFoundError: No module named 'proforma_vietnam.tax_model'`.
  - Green local run: `python -m unittest proforma_vietnam.tests.test_tax_model` passed, 4 tests.
  - Green Docker unittest run: `docker-compose run --rm --entrypoint python django -m unittest proforma_vietnam.tests.test_tax_model` passed, 4 tests.
  - Green Docker Django run: `docker-compose run --rm --entrypoint python django manage.py test proforma_vietnam.tests.test_tax_model -v 2` passed, 4 tests, `System check identified no issues (0 silenced).`
- Current git state after this work: branch `master` is 4 commits ahead of `origin/master`; `proforma_vietnam/`, `CODEX_SESSION.md`, and `SESSION_NOTES.md` have uncommitted changes.
- Next recommended work: add `proforma_vietnam/cash_flow.py` and tests for 25-year VND DCF, EVN escalation, debt service assumptions, and use of the tested CIT/depreciation helpers.

## 2026-05-23 - Vietnam ESCO Contract Model Notes

- User clarified that the Vietnam pro forma should be a third-party investment model where the offtaker signs an ESCO contract covering energy offtake and peak shaving service.
- Paused `cash_flow.py` implementation until the commercial deal structure is discussed in more detail.
- Added `proforma_vietnam/ESCO_CONTRACT_MODEL_NOTES.md` as a discussion anchor for a separate conversation.
- Captured that existing REopt third-party ownership is a fixed annualized host payment / finance structure, not a detailed tariff-contract model.
- Captured open design questions for:
  - energy offtake pricing: EVN discount, fixed VND/kWh, or hybrid escalation,
  - peak shaving benefit sharing,
  - energy arbitrage sharing,
  - treatment of grid charging versus solar charging,
  - minimum offtaker savings and ESCO target equity IRR.
- Next recommended work: discuss and finalize these assumptions before adding `proforma_vietnam/cash_flow.py`.

## 2026-05-22 - Session Notes Split

- Moved the detailed latest session notes out of `CODEX_SESSION.md` into this dedicated file.
- Updated `AGENTS.md` so future agents read this file when context is needed and update it during session closeout.
- Updated `CODEX_SESSION.md` session-close guidance to point detailed notes here.

## 2026-05-22 - Phase 1 Acceptance Gate Closeout

- Confirmed Docker Desktop was running and started the full Compose stack with `docker-compose up -d`.
- Verified running services with `docker-compose ps`: `db`, `redis`, `julia`, `celery`, and `django` were up.
- Verified Django health with `docker-compose exec -T django python manage.py check`; result: `System check identified no issues (0 silenced).`
- The browser result page for `c9da7aa4-f544-425b-b0a0-ebb36e11132d` looked blank, but `Invoke-WebRequest` showed HTTP 200 with a large JSON body and the database later showed status `optimal`.
- Checked Celery/Julia logs while debugging the apparent blank browser page. Julia solved the submitted jobs with `termination_status(m) = OPTIMAL`; Celery task results were `SUCCESS`.
- Retrieved latest tariff output rows from Django:
  - `current`: run UUID `0ee531dc-625f-416f-a1dc-44e1671572d4`, status `optimal`, `year_one_bill_before_tax_bau=345975.02`, `year_one_energy_cost_before_tax_bau=345975.02`, `year_one_demand_cost_before_tax_bau=0.0`.
  - `decision_963`: run UUID `c9da7aa4-f544-425b-b0a0-ebb36e11132d`, status `optimal`, `year_one_bill_before_tax_bau=345975.02`, `year_one_energy_cost_before_tax_bau=345975.02`, `year_one_demand_cost_before_tax_bau=0.0`.
- Ran the manual EVN baseline calculation inside the Django container using `build_example_payload(tou_schedule=...)`:
  - Formula: `sum(hourly_load_kw * tou_energy_rate_per_kwh)`.
  - `current`: manual total `345975.02`, REopt BAU bill `345975.02`, percent error `0.0%`, acceptance `True`.
  - `decision_963`: manual total `345975.02`, REopt BAU bill `345975.02`, percent error `0.0%`, acceptance `True`.
- Phase 1 acceptance gate is complete for the current example industrial load; next recommended work is Phase 2 Vietnam pro forma in a separate `proforma_vietnam/` module.
- Current git status before this handoff update: clean working tree, branch `master` was 3 commits ahead of `origin/master`, latest commit `e47c94ec Split session notes into dedicated handoff file`.

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
