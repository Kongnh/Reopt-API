# Thailand Adaptation (Keen / Rofu Thailand) - Design

Date: 2026-09-04
Scope: a new `proforma_thailand/` package built on `proforma_vietnam/` as the
shared core, plus a new `reoptjl/src/thailand/` PEA tariff module. Driven by the
KEEN Footwear / Rofu (Thailand) Ltd. rooftop solar (RTS) and RTS+BESS analysis.

## Motivation

The repo models exactly one market. Vietnam-specific concepts (VND, EVN, the
ND57 DPPA settlement chain) sit inside a 17.8k-LOC `proforma_vietnam/` package
that is otherwise generic project finance. Keen needs the same analysis for a
Thai site served by PEA, where there is no DPPA framework, no export buyback, a
different demand-charge structure, and a different tax regime.

Client context: Rofu (Thailand) Ltd., Phimai district, Nakhon Ratchasima
(15.209427, 102.475687). Rob Hardison requested benchmark sizing and pricing for
RTS and RTS+BESS; Lauren Hood needs a grid-offset percentage with and without
storage for a leadership update.

## Decisions taken in brainstorming

1. **Deliverable**: sizing plus a full financed proforma, not sizing alone.
2. **Structure**: `DIRECT_OWNERSHIP` (factory self-invest) first. ESCO/PPA later.
3. **Roadmap**: more countries are possible but not committed. Build a clean
   seam; do not pay for full generalization until a third country is real.
4. **Load resolution**: 15-minute native (`time_steps_per_hour=4`), because PEA
   bills demand on the 15-minute on-peak maximum.
5. **Packaging**: **no renames.** `proforma_vietnam` stays as it is and serves as
   the shared core. `proforma_thailand` imports from it. There is no
   `proforma_core` package and no `_vnd` to `_local` rename.
6. **Missing financing inputs**: stub from benchmarks, visibly flagged.
7. **Sequencing**: refactor first, phases in order.

## Evidence gathered during design

All figures below were verified against source data, not assumed.

### The PEA tariff is TOU, and the rates are exact

From the June 2025 invoice (`02_Bills_2025/06. Electricity Bill Jun 2025
KTH2.pdf`, a Thai-language scan with no text layer, read by rendering the page):

- Rate code `4224`, voltage `22-33 KV`, meter multiplier 2000, PEA Phimai.
- Demand section records three values: P 1368.00 kW, OP 1368.00 kW, H 1328.00 kW.
  **Only P carries a charge**: 181,848.24 THB. `181,848.24 / 1368.00 = 132.93`
  THB/kW exactly. This settles the TOU-versus-TOD question: it is **TOU
  (Schedule 4.2), demand billed on on-peak demand only**.
- Peak energy 288,960 kWh at 1,208,979.74 THB = **4.1839 THB/kWh** exactly.
- Off-peak 164,380 kWh and holiday 178,240 kWh are billed **as a single bucket**:
  `892,079.69 / (164,380 + 178,240) = 2.6037` THB/kWh exactly. Holiday energy is
  charged at the off-peak rate, so the tariff has two energy buckets, not three.
- Service charge 312.24 THB confirmed.
- Power factor charge line present but zero this month (see below).

The entire bill reconstructs from these rates to within 0.01 THB:

| Line | Computed | Invoice |
|---|---|---|
| Demand charge | 181,848.24 | 181,848.24 |
| Peak energy | 1,208,979.74 | 1,208,979.74 |
| Off-peak + holiday energy | 892,079.69 | 892,079.69 |
| Base total (incl. service) | 2,283,219.92 | 2,283,219.91 |
| Ft | 124,547.58 | 124,547.58 |
| VAT 7% | 168,543.72 | 168,543.72 |
| **Total** | **2,576,311.22** | **2,576,311.21** |

### Ft is not a constant, and the value in the data inventory is one window

Ft is read off each invoice. For 2025:

| Window | Ft (THB/kWh) | Source |
|---|---|---|
| Jan-Apr 2025 | **0.3672** | Mar 2025 invoice |
| May-Aug 2025 | **0.1972** | Jun 2025 invoice |
| Sep-Dec 2025 | **0.1572** | Nov 2025 invoice |

Ft fell **57% across 2025**. The 0.3672 figure in
`00_README_KTH_data_inventory.md` is the Jan-Apr 2025 window, not a standing
value. Against a 2.6037 off-peak base, Ft moved from about 14% of the rate to
about 6%. **Modelling Ft as a flat 0.3672 would overstate avoided cost by
roughly 0.21 THB/kWh, about 6-7% of the blended rate.** Ft is therefore modelled
as its own versioned series with its own forecast and its own disclosure line.

### Coincident-peak demand is resolution-agnostic

From `julia_src/reopt_model.jl:1049`:

```julia
@constraint(m, [prd in p.CPPeriod, ts in ...],
    m[:dvPeakDemandCP][prd] >= sum(m[:dvGridPurchase][u,ts] for u in p.PricingTier))
m[:TotalCPCharges] = @expression(m, p.pwf_e * sum(p.CoincidentPeakRates[prd] * m[:dvPeakDemandCP][prd] ...))
```

`dvGridPurchase` is a **power** variable in kW: everywhere energy is needed the
model multiplies by `p.TimeStepScaling` (for example `reopt_model.jl:929` and
`:937`), and the coincident-peak constraint deliberately does not. It compares
power to power and takes the max across whatever timesteps are in the set, so it
is correct at `time_steps_per_hour=4` with no scaling. Ragged period sets are
handled by `nothing`-padding at `julia_src/utils.jl:360-363`, matching the
Django-side padding at `reoptjl/models.py:1799`.

This removes the main technical risk in the design. It is still confirmed
empirically by a real run in Phase 0.

### The interval data reconciles to the invoice

Aggregating `Raw Total Consumption` for calendar June 2025, treating each
interval as labelled by its **end** time and peak as `09:00 < t <= 22:00` on
non-holiday weekdays:

| Bucket | Interval data | Invoice | Diff |
|---|---|---|---|
| Peak kWh | 288,970 | 288,960 | +0.00% |
| Off-peak kWh | 164,387 | 164,380 | +0.00% |
| Holiday kWh | 178,242 | 178,240 | +0.00% |
| Total kWh | 631,599 | 631,580 | +0.00% |
| On-peak demand kW | 1,369.6 | 1,368.00 | +0.12% |

The residual is meter rounding (readings are scaled by the 2000 multiplier). The
`DayType` column therefore reproduces PEA's own billing day classification
exactly, and the end-time interval convention is confirmed.

## Current architecture (relevant facts)

- `esco_pro_forma.py` normalizes all money to **USD** before calling
  `cash_flow.calculate_vietnam_esco_cash_flow`. `_finalize_currencies`
  (`cash_flow.py:1048`) then restates each `_vnd` key from the USD value at the
  contract FX rate. The engine computes in USD; `_vnd` is a presentation
  restatement, not a parallel computation.
- `proforma_schema.RowSpec` already stores `key` **without** a currency suffix
  plus a `currency: bool` flag. Suffix composition happens in two places only:
  `proforma_schema.py:247` and `xlsx_builder.py:906`.
- `structures.py` already abstracts financing structures, and `DIRECT_OWNERSHIP`
  is market-neutral: a single `bill_savings_revenue` line, flat CIT, no discount
  fraction and no demand split.
- `rebuild_report.py` regenerates a workbook purely from saved `results.json` +
  `assumptions.json`, with no Django and no REopt re-run. All 8 saved cases under
  `outputs/vietnam_case/` carry both files. This is the regression harness.
- REopt V3 supports `time_steps_per_hour` in {1,2,4} (`reoptjl/models.py:261`) and
  `validators.py:625` up/down-samples any series to match, so the PVWatts 8760
  production factor auto-upsamples and only load and tariff arrays need 35,040
  entries.
- `FixedMonthlyCharge` exists in the Julia struct (`julia_src/utils.jl:82`) but is
  **not exposed** as a V3 Django input; it arrives only via URDB. Since Thailand
  sets `urdb_label=null`, it defaults to 0.

## Design

### 1. Packaging

`proforma_vietnam/` is the shared core and is not renamed, moved or split. Its
public function names are unchanged, so `rebuild_report.py`, `views.py` and the
8 saved cases keep working untouched.

`proforma_thailand/` is a new sibling package containing only what is genuinely
Thailand-specific:

```
proforma_thailand/
    __init__.py
    case_builder.py          # TH case JSON -> REopt payload + assumptions
    defaults/
        __init__.py
        thailand_defaults.json
        pea_tariff_rates.json
    run_case.py              # TH CLI, mirrors proforma_vietnam/run_case.py
    labels.py                # TH display strings
```

It imports `cash_flow`, `tax_model`, `proforma_schema`, `structures`,
`xlsx_builder`, `audit_sheets`, `report_data`, `pvwatts_client` and
`validate_workbook` from `proforma_vietnam` unchanged.

### 2. The CountryProfile seam

A new `proforma_vietnam/country_profile.py`:

```python
@dataclass(frozen=True)
class CountryProfile:
    country: str                 # "Vietnam" | "Thailand"
    local_currency_code: str     # "VND" | "THB"
    utility_label: str           # "EVN" | "PEA"
    time_steps_per_hour: int     # 1 | 4
```

The profile parameterizes **display and resolution only**. Three changes:

1. Renderers read `local_currency_code` and `utility_label` from the profile
   instead of hardcoding "VND" and "EVN" in labels and note strings.
2. `_read_8760_load_csv` (`case_builder.py:190`) becomes resolution-aware,
   validating `8760 * time_steps_per_hour` entries.
3. `VIETNAM_PROFILE` is the default everywhere, so Vietnam behaviour and output
   are unchanged.

**Known tradeoff, accepted deliberately.** Because there is no rename, a Thailand
run carries internal keys suffixed `_vnd` while holding THB. This is a real
readability cost in an audit-oriented codebase. Two mitigations are required, not
optional:

- A module-level note in `cash_flow.py` and `proforma_schema.py` stating that the
  `_vnd` suffix denotes **the local contract currency**, which is VND for
  Vietnam runs and THB for Thailand runs.
- Every emitted assumptions and summary dict carries an explicit
  `local_currency_code` field, so no downstream consumer has to infer the unit.

No user-visible label may ever read "VND" on a Thailand run. This is covered by a
test.

### 3. PEA tariff module

`reoptjl/src/thailand/pea_tariff.py` + `defaults/pea_tariff_rates.json`,
mirroring the EVN module's vintage-keyed structure: fallback to the latest
vintage at or before the requested year, with `rate_vintage_year` /
`rate_vintage_source` audit keys popped into assumptions rather than the REopt
payload.

PEA Schedule 4.2, Large General Service, 22-33 kV, TOU (rate code 4224):

| Component | Value | REopt mapping |
|---|---|---|
| Peak energy | 4.1839 THB/kWh | `tou_energy_rates_per_kwh`, 35,040-length |
| Off-peak and holiday energy | 2.6037 THB/kWh (one bucket) | same array |
| Ft | versioned series, 0.3672 / 0.1972 / 0.1572 across 2025 | added to every timestep |
| Demand | 132.93 THB/kW, **on-peak only** | `coincident_peak_load_charge_per_kw` (12 entries) + `coincident_peak_load_active_time_steps` (12 monthly on-peak timestep sets) |
| Service charge | 312.24 THB/month | not a V3 input; identical in BAU and optimized, cancels out of savings; proforma display only |
| Power factor | 56.07 THB/kVAR above 61.97% of billed kW | proforma post-processing, see below |
| VAT | 7% | outside the optimization, applied in the proforma |
| Export | none | `can_net_meter=false`, `can_wholesale=false`, `can_export_beyond_nem_limit=false`, `can_curtail=true` |

Periods: on-peak `09:00 < t <= 22:00` Monday to Friday; off-peak everything else,
plus all day Saturday, Sunday and Thai public holidays. Intervals are labelled by
end time.

Rates are converted THB to USD at the contract FX rate before optimization,
mirroring the Vietnam VND to USD convention.

### 4. Power factor: a cost of solar that is easy to miss

The June 2025 invoice records 664.00 kVAR against 1,368 kW billed demand. PEA
charges 56.07 THB/kVAR on the portion of kVAR exceeding 61.97% of billed kW. At
1,368 kW the threshold is about 848 kVAR, so 664 kVAR incurs nothing today.

PV reduces kW but does **not** reduce kVAR. If PV cuts billed on-peak demand to,
say, 900 kW, the threshold falls to about 558 kVAR and the unchanged 664 kVAR
becomes chargeable, costing roughly 6,000 THB/month that did not exist before.

The proforma therefore computes the power factor charge in **both** the BAU and
the optimized case from the post-PV billed demand, and reports it as its own
line. It must not be assumed to net out. Where it becomes material, the
mitigation (capacitor bank or inverter reactive support) is costed as a
flagged stub.

### 5. Load pipeline

Source: `01_Load_Data/ROFU Thailand 15-Minute Interval Data.xlsm`, sheet
`Raw Total Consumption`.

Verified: 39,936 rows = 416 days x 96 intervals, spanning 2025-06-01 to
2026-07-21, with **zero gaps and zero nulls**. Every day carries all 96
intervals. Peak 15-minute consumption is 374.4 kWh, implying 1,497.6 kW.

The `DayType` column (Weekday / Holiday) encodes PEA's own day classification and
is proven correct by the June reconciliation above. It is still cross-checked
against the holiday list in `RTS Data Collection_KTH_followup_Dec2025 (rebuilt).xlsx`.

**Window: 2025-07-01 to 2026-06-30.** Twelve complete calendar months, entirely
inside the data, 365 days (2026 is not a leap year), exactly 35,040 intervals,
with month boundaries aligned to billing.

Output: a 35,040-row CSV plus a QA report reconciling window totals against the
workbook's own `Daily Breakdown` sheet.

### 6. Bill tie-out test

The bills cover Jan-Nov 2025; the interval data starts 2025-06-01, so the usable
overlap is **six months, Jun-Nov 2025**. The tie-out is a blocking test over
those six months: modelled BAU bill versus actual invoice, month by month,
including the Ft window that applies to each month.

June 2025 is already proven to 0.01 THB by hand during design. The test
generalizes that check to all six months and locks it against regression.

### 7. Site constraints

| Constraint | Value | Treatment |
|---|---|---|
| Roof area | 5 roofs at 24x108 m (2,592 m2) and 30x108 m (3,240 m2); split between the two sizes not stated, so gross is 12,960-16,200 m2 | PV `max_kw` about 1.7-2.1 MWp at ~65% usable and ~200 W/m2. **Until Ou confirms, use the conservative lower bound (all five roofs at 24x108 m, so 1.7 MWp)** and carry it as a flagged stub. |
| Interconnection | 4 transformers (500 kVA x2, 1,600 kVA, 630 kVA) = 3,230 kVA, one connection point, described as already fully loaded | Not the PV ceiling against a ~1,500 kW site peak, but "fully loaded" must be clarified before sizing BESS charging |
| Roof age | Oldest over 20 years, newest replaced 2024 | Either exclude aged roofs from usable area or carry a roof-renewal cost against a 25-year asset |
| Site lease | 3-year rolling, last renewed Oct 2024, next renewal Oct 2027 | Risk disclosure under direct ownership; becomes central to contract tenor under the later ESCO structure |
| Outages | About one per month, no backup generation | Secondary resilience value; out of scope for the first deliverable |

### 8. Defaults and flagged stubs

`proforma_thailand/defaults/thailand_defaults.json`, mirroring the
`vietnam_defaults.json` versioned shape.

Known and verified: PEA Schedule 4.2 rates, the 2025 Ft series, service charge,
VAT 7%, CIT 20% flat (maps to the existing `standard_flat` regime), 5-year loss
carryforward.

To research in Phase 4 (no client reference available): Thai depreciation lives.
The Revenue Code generally allows machinery at 20% per year straight line, so
about 5 years, against Vietnam's 20-year PV and 8-year BESS. This is a large
difference in tax-shield timing that flows directly into IRR, and it is
researched and cited rather than assumed. BOI incentive eligibility is checked at
the same time; the inventory records no known incentives.

Stubs, each carrying `"source": "PLACEHOLDER - pending Keen confirmation"` and
rendering with a visible marker on the Assumptions sheet: capex per kWp, BESS
capex, debt fraction, debt rate, debt tenor, insurance, connection cost,
permitting and EIA study cost, O&M, PEA base tariff escalation, Ft forecast,
usable roof area, power factor mitigation cost.

Guard rail: a `validate_workbook` rule that **fails** if a placeholder value
reaches a headline metric (IRR, NPV, payback) without a placeholder marker
attached. The failure mode being made impossible is a stubbed capex quietly
producing a confident-looking IRR in a client deck.

## Phases

| Phase | Work | Acceptance |
|---|---|---|
| 0. Spike | Empirically confirm coincident-peak at `time_steps_per_hour=4` with a real run (source review already done) | Modelled demand charge matches a hand calculation |
| 1. Seam | `CountryProfile` + profile-driven labels + resolution-aware load reader, all inside `proforma_vietnam` | 8 Vietnam workbooks rebuild cell-identical; existing suites pass unchanged |
| 2. Tariff | `reoptjl/src/thailand/` PEA builder + rates JSON incl. Ft series | Six-month bill tie-out passes |
| 3. Load | xlsm to 35,040-row CSV, window selection, QA report | Window totals reconcile to `Daily Breakdown` |
| 4. Case | `proforma_thailand` builder + defaults + DIRECT_OWNERSHIP at 15-min; Thai depreciation researched and cited | Dry-run payload validates |
| 5. Run | RTS and RTS+BESS cases, incl. power factor analysis | Sizing, grid-offset %, workbook |
| 6. Later | ESCO/PPA structure | Out of scope for this spec |

## Out of scope

- ESCO/PPA and roof-lease / hire-purchase structures (Phase 6, separate spec)
- Thai direct-PPA / ERC third-party grid access
- Resilience and outage valuation
- Any change to Vietnam behaviour or output
