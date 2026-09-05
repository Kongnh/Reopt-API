# Keen Thailand (Rofu) deliverable: backlog closure + end-to-end case set

Date: 2026-09-05
Branch: `thailand-adaptation`
Status: design, pending user approval

## Purpose

Two goals, in order:

1. Close the outstanding backlog carried out of the Thailand adaptation work
   (I1-I10 plus minors), because several items change client-facing numbers.
2. Build a complete, runnable case tree for the Rofu (Thailand) Ltd. factory
   under `outputs/thailand_case/rofu_thailand/`, run it end to end against the
   live solver, and produce a client memo for Keen.

The deliverable answers two named client asks recorded in the data inventory:
Rob Hardison wants benchmark sizing and pricing for RTS and RTS+BESS; Lauren
Hood needs a grid-offset percentage for a leadership update, with and without
storage.

## Site

Rofu (Thailand) Ltd., Phimai District, Nakhon Ratchasima 30110.
15.209427, 102.475687. PEA Phimai branch, Schedule 4.2 Large General Service
TOU, 22-33 kV, rate code 4224. Zero export: PEA pays nothing for surplus.

Load: 35,040 intervals at 15-minute resolution, a synthetic calendar year of
Jan-Jun 2026 plus Jul-Dec 2025, built from 432 days of metered interval data.
Annual load 7,235,301 kWh. Billed on-peak demand 1,083-1,343 kW.

## Decisions taken

| # | Decision |
|---|---|
| D1 | Data-blocked inputs get a researched, cited benchmark, used and visibly marked provisional. Nothing stays silently unmodelled. |
| D2 | Insurance and inverter replacement are handled Thailand-side. BESS depreciation years needs an additive core kwarg, because it cannot be reached from `report.py` without monkeypatching a module global. |
| D3 | PV is presented as a sensitivity band across three roof widths plus a roof-unconstrained bound. |
| D4 | BESS is presented as the optimizer result plus a forced case sized to clear the evening peak. |
| D5 | Thai EPC and BESS pricing is re-benchmarked with cited Thailand sources before any case is run. |
| D6 | Cases live in `outputs/thailand_case/rofu_thailand/case_N`, mirroring `outputs/vietnam_case/factory_a/case_N`. |
| D7 | Deliverable is a written memo plus the per-case workbooks. Caveats are inline footnotes; a closing "Information requests" list names what Ou must confirm. |
| D8 | Executed under the SDD process: spec, numbered plan, implementer plus task reviewer per task, ledger with rulings. |

## Standing constraints

- Never modify anything under `reo/` (deprecated V1/V2, returns 410).
- Do not modify `outputs/vietnam_case/` or `baseline_workbooks/`.
- Vietnam's generated Excel output must not change. The 8-case gate must report
  `TOTAL DIFFS 0` after every core change.
- No em dash in generated report output.
- Use `./.venv/Scripts/python.exe`. It has no Django; anything needing Django
  runs inside the `reopt_api-django-1` container.
- Never modify the client source `.xlsm`.
- `proforma_vietnam` IS the shared core. No rename, no `proforma_core` package.
  Vietnam-suffixed names carrying Thailand values is by design.

## Phase 1: backlog closure

### 1a. Core changes (additive only)

Both are keyword arguments defaulting to the current behaviour. Vietnam passes
nothing, so Vietnam output is unchanged by construction, and the 8-case gate
proves it.

**I1 - BESS depreciation years.** `BESS_DEPRECIATION_YEARS` is a module global
read at six sites in `proforma_vietnam/cash_flow.py`: the depreciation
schedule, the tax shield, the net-book-value table and the residual-value line
(`:1261`, `:1271`, `:1313`, `:1318`, `:1352`, `:1354`). Add
`bess_depreciation_years=None` to `calculate_vietnam_esco_cash_flow`, resolving
to `BESS_DEPRECIATION_YEARS` when None, exactly mirroring the existing
`pv_depreciation_years` kwarg. Add `bess_depreciation_years` to
`PASSTHROUGH_OVERRIDE_KEYS` in `proforma_thailand/report.py` and to the
Thailand assumptions block.

Materiality is small at the current battery size. The reason to fix it is that
the Thailand client workbook currently prints "8 years | Circular
45/2013/TT-BTC" as the authority for Thai tax, which is the same provenance
defect as the C4 critical already fixed.

**I10 - inverter replacement.** `esco_pro_forma.py:124` sets
`cash_flow_inputs["replacement_costs_by_year"]` from `_bess_replacement_costs`,
and `cash_flow_inputs.update(cash_flow_overrides)` then lets a caller override
replace that series entirely. Add `extra_replacement_costs_by_year`, merged
element-wise ADDITIVELY into the BESS series rather than replacing it. Vietnam
passes nothing.

Thailand then books an inverter replacement in year 11, at a fraction of PV
capex set by the Phase 2 research. No inverter replacement is modelled by either
REopt.jl or the proforma, which overstates a 25-year case. The ENS vendor tool
in the client's own folder books it at year 11 at 10 percent of capex.

### 1b. Thailand-side changes

**I6 - insurance.** Insurance is currently costed nowhere. Fold it into
`annual_om_usd` in `proforma_thailand/report.py` as `insurance_rate_fraction`
times total installed capex, where total installed capex is PV plus storage
plus any other capex booked on the case. It then escalates with O&M and is
deducted as opex, both correct treatments. Render it as its own Assumptions
line so it is not hidden inside an O&M total.

**I7 - `cit_standard_rate`.** Produced in the assumptions block and consumed by
nothing. Wire it to the tax model. Both values are 0.20 today, so this is
latent, not active.

**Minors:** set `min_duration_hours` explicitly, because REopt inherits 0.0
which permits a physically meaningless zero-duration battery; set the storage
O&M fraction explicitly instead of inheriting REopt's US 2.5 percent default;
expose PVWatts `tilt` as a case input instead of the hardcoded Vietnam-tuned 10
degrees. Default it to 15 degrees, which approximates both the site latitude
(15.21N) and a typical industrial metal roof pitch. The actual roof pitch is
not in the data collection sheet and becomes an information request to Ou.

### 1c. Reporting and validation

**I2 - placeholder validation on the production path.**
`validate_no_unmarked_placeholders` exists in
`proforma_vietnam/validate_workbook.py:240` and is called only from tests. Call
it in `proforma_thailand/run_case.py` after the workbook is built and HARD-FAIL
the run. The validator checks that placeholders are MARKED, not that they are
absent, so failing hard is correct and does not block legitimate provisional
inputs.

**Billed demand under-reporting.** `billed_demand_kw_by_month` in
`proforma_thailand/report.py:107` reads only
`ElectricUtility.electric_to_load_series_kw`. The meter sees grid-to-load PLUS
grid-to-storage, and REopt's own coincident-peak constraint applies to total
grid purchase. Our reporting therefore understates what the model itself
billed, whenever the battery grid-charges on-peak. Sum both series. Negligible
at a 29 kW battery; material in the forced-battery case. `can_grid_charge`
stays True: the model is right, the report was wrong.

**I3 - dispatch irradiance alignment.** The POA series is 8760 hourly values
from PVWatts, paired against 35,040 dispatch rows, so it is 4x misaligned and
zero for 75 percent of rows. Up-sample by repeating each hourly value 4 times,
the same way REopt up-samples the production factor.

**I5 - Ft series.** `audit_sheets.py` drops list values, so the per-month Ft
series never reaches the workbook. Render it. Remove the dead
`ft_forecast_per_kwh` key, which nothing reads.

**I8 - Vietnam gate blindness.** `DEFAULT_IGNORE_SUBSTRINGS = ("prepared ",)`
in `proforma_vietnam/tools/compare_workbooks.py` is broad enough to hide Cover
and Executive Summary subtitle rows from the gate. Drop the substring rule and
keep only `DEFAULT_IGNORE_ROW_LABELS = ("Report prepared",)`, which already
exists and is precise. Confirm the gate still reports TOTAL DIFFS 0 after the
narrowing, and treat any newly visible diff as a real finding.

**I9 - FX disclosure.** Prints `{fx:,.0f}`, rendering 32.5 as "32". Use a
format that preserves the fractional rate.

**I4 - regeneration and month-order safety.** `extract_intervals` and
`build_calendar_year` have no caller outside tests, and no committed script
regenerates the load CSV or the holiday JSON. The CSV is a single bare
`load_kw` column of 35,040 rows with no timestamps, so `calendar_year_months`
in `case.json` is independent of the data and only its length is checked.
Reordering months silently misaligns load against tariff.

Add `proforma_thailand/tools/build_load_inputs.py`, taking the source `.xlsm`
path as an argument, regenerating both committed files and emitting a
`manifest.json` recording month order, per-month row counts, and the SHA-256
of the source workbook. Validate `case.json`'s `calendar_year_months` against
that manifest in `build_thailand_case`, raising on mismatch.

**Remaining minors:** suppress ESCO contract terms on a DIRECT_OWNERSHIP case;
rename the dispatch "Hour" column to "Interval", since it is headed 1-35040;
assert `ft_for_month(2025, 1)`.

## Phase 2: Thailand cost re-benchmark

Research and cite Thailand-specific figures, replacing placeholders:
PV installed cost per kWp, BESS per kW and per kWh, PV O&M per kWp-year,
insurance as a fraction of capex, inverter replacement fraction and year,
and the PEA tariff escalation rate.

Current placeholders sit above the ENS vendor comparator (700 versus about 492
USD/kWp; 250 versus about 213 USD/kWh) but below it on opex (12 versus about
5.2 USD/kWp-yr O&M; 0.5 versus 0.25 percent insurance). The vendor tool is
configured for a Vietnam site (lat 11.09, EVN tariff, VND, 10 percent VAT), so
it is a comparator, not a Thailand source. Every replacement value must carry a
Thailand-applicable citation or stay marked provisional.

## Phase 3: case tree

Location `outputs/thailand_case/rofu_thailand/case_N`, mirroring
`outputs/vietnam_case/factory_a/case_N`. Each directory holds `case.json`,
`payload.json`, `assumptions.json`, `results.json`, `summary.json` and the
generated workbook. A `CASE_JSON_INPUT_GUIDE.md` sits at the factory root.

### Roof-area derivation

Source: RTS Data Collection_KTH_followup_Dec2025, Facility Data sheet.
Rooftop size recorded as "24*108 m / 30*108 m (each building differs)"; Keen's
December follow-up answer is "5 large rooftops of similar size (plus several
smaller)".

Gross area = 5 roofs x 108 m x width. Usable fraction 0.65, the midpoint of the
60-70 percent planning band for industrial metal roofs, deducting perimeter
setbacks, maintenance walkways, roof penetrations and cable routing. The
"several smaller" roofs are excluded entirely. Power density 0.20 kW/m2, the
installed density of a 21-22 percent efficient module on a pitched roof after
row spacing.

| Width | Gross m2 | Usable m2 | kWp DC |
|---|---|---|---|
| 24 m | 12,960 | 8,424 | 1,685 |
| 27 m | 14,580 | 9,477 | 1,895 |
| 30 m | 16,200 | 10,530 | 2,106 |

The existing 1,685 kW is the conservative bottom of this band, not an
arbitrary stub. Ou confirming roof widths is worth up to +25 percent of system
size.

Transformer nameplate is 500 + 500 + 1,600 + 630 = 3,230 kVA. The data sheet
calls the transformers "fully loaded" while measured billed demand peaks at
1,343 kW, 42 percent of nameplate; those cannot both describe site-level
loading, so "fully loaded" is read as per-transformer or contracted allocation.
For zero-export behind-the-meter PV the transformer import rating is not the
binding constraint anyway. Case 4 is therefore labelled "roof-unconstrained",
answering where more PV stops paying, NOT "what the transformer permits".

### Cases

| Case | PV cap kW | Storage | Question answered |
|---|---|---|---|
| case_1 | 1,685 | none | RTS base, conservative roof |
| case_2 | 1,895 | none | Mid roof width |
| case_3 | 2,106 | none | Upper roof width |
| case_4 | 3,230 | none | Where does more PV stop paying |
| case_5 | 1,685 | optimizer-sized | The economic battery |
| case_6 | 1,685 | forced, sized in study | A battery that clears the evening peak |

At 1,685 kW the system already curtails about 8 percent of generation under
zero export, and that fraction climbs with size, so cases 2-4 test a real
diminishing return rather than a linear extrapolation.

### Evening-peak battery sizing study (case_6)

PEA's on-peak window is 09:00 to 22:00. PV cannot serve the 18:00-22:00 tail,
so that tail sets a floor on billed demand that PV alone cannot cut. In the
RTS base case billed demand only falls below roughly 1,121 kW in 1 of 12
months.

The target is defined self-referentially rather than picked: it is the LOWEST
monthly billed demand that PV alone achieves in the re-run case_1. In other
words, "level the year down to the best month PV already delivers". This avoids
an arbitrary round number and stays correct after Phase 1 and Phase 2 shift the
case_1 numbers. Report a sensitivity at plus and minus 100 kW around it, so the
cost of a deeper cut is visible.

Method: from the case_1 optimized grid series, for each month take the on-peak
timesteps, compute the maximum power above the target (sets battery kW) and the
largest single-day energy above the target (sets battery kWh). Take the
worst-month requirement, then add headroom for round-trip efficiency and
depth of discharge. Run that size as a forced minimum and price it: capex,
demand-charge reduction, and incremental IRR against case_1.

## Phase 4: memo

Client memo plus the six workbooks. Contents:

- Headline: grid offset with and without storage, for Lauren's leadership update.
- Sizing band across roof widths, with the derivation above shown.
- Storage verdict: the optimizer result, and what the forced battery costs and buys.
- Cost basis, with every benchmark cited and every provisional input marked.
- Inline footnotes for what cannot be computed: power factor without site kVAR,
  emissions outputs which are zero because AVERT, Cambium and EASIUR are US
  datasets and must not be quoted, and the ERC generation licence and Aor.6
  building-modification permit fees which have no public schedule. EIA and IEE
  are genuinely not required below 5 MWp at about 1.7 MWp, so zero there is a
  finding and not a stub.
- Closing "Information requests" list for Ou.

## Verification

After every task: `proforma_thailand`, `proforma_vietnam` and
`reoptjl.test.test_thailand_tariff` green, and the Vietnam 8-case gate at
TOTAL DIFFS 0. Live-solver runs execute against the Docker stack.

## Out of scope

ESCO and PPA structures for Thailand. Resilience and outage valuation, despite
about one outage per month and no backup generator, because no outage cost data
is in hand. Any change to `reo/`, `outputs/vietnam_case/` or
`baseline_workbooks/`.
