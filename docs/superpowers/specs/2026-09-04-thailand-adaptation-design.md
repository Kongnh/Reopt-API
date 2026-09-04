# Thailand Adaptation (Keen / Rofu Thailand) - Design

Date: 2026-09-04
Scope: new `proforma_core/` + `proforma_thailand/` packages, a `proforma_vietnam/`
split, and a new `reoptjl/src/thailand/` PEA tariff module. Driven by the KEEN
Footwear / Rofu (Thailand) Ltd. rooftop solar (RTS) and RTS+BESS analysis.

## Motivation

The repo models exactly one market. Vietnam-specific concepts (VND, EVN, the
ND57 DPPA settlement chain) are baked into a 17.8k-LOC `proforma_vietnam/`
package that is otherwise generic project finance. Keen needs the same analysis
for a Thai site served by PEA, where there is no DPPA framework, no export
buyback, a different demand-charge structure, and a different tax regime.

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
   bills demand on the 15-minute peak-period maximum and hourly averaging would
   understate the demand charge and overstate battery peak-shaving value.
5. **Approach**: shared-core split (below), not a fork and not a full
   country-plugin framework.
6. **Missing financing inputs**: stub from benchmarks, visibly flagged.
7. **Sequencing**: refactor first, phases in order.

## Current architecture (relevant facts)

- `esco_pro_forma.py` normalizes all money to **USD** before calling
  `cash_flow.calculate_vietnam_esco_cash_flow`. `_finalize_currencies`
  (`cash_flow.py:1048`) then restates each `_vnd` key from the USD value at the
  contract FX rate. The engine computes in USD; `_vnd` is a presentation
  restatement, not a parallel computation. The 440 `vnd` tokens in `cash_flow.py`
  are therefore one concept, not 440 decisions.
- `proforma_schema.RowSpec` already stores `key` **without** a currency suffix
  plus a `currency: bool` flag. Suffix composition happens in two places:
  `proforma_schema.py:247` (format detection) and `xlsx_builder.py:906`
  (renderer fallback).
- `structures.py` already abstracts financing structures, and `DIRECT_OWNERSHIP`
  is market-neutral: a single `bill_savings_revenue` line, flat CIT, no discount
  fraction and no demand split.
- `rebuild_report.py` regenerates a workbook purely from saved `results.json` +
  `assumptions.json`, with no Django and no REopt re-run. All 8 saved cases under
  `outputs/vietnam_case/` carry both files. This is the refactor regression
  harness.
- REopt V3 supports `time_steps_per_hour` in {1,2,4} (`reoptjl/models.py:261`) and
  `validators.py:625` up/down-samples any series to match, so the PVWatts 8760
  production factor auto-upsamples and only load and tariff arrays need 35,040
  entries.
- Hard 8760 assumptions in the proforma are confined to
  `case_builder._read_8760_load_csv` (`case_builder.py:190`), `pvwatts_client`,
  and `dppa_settlement` (unused by Thailand).

## Design

### 1. Package split

| Package | Contents |
|---|---|
| `proforma_core/` | `cash_flow.py`, `tax_model.py`, `proforma_schema.py`, `structures.py`, `xlsx_builder.py`, `audit_sheets.py`, `report_data.py`, `pvwatts_client.py`, `validate_workbook.py`, `reopt_adapter.py` |
| `proforma_vietnam/` | EVN rates, `dppa_settlement.py`, `dppa_negotiation_*`, `esco_discount_solver.py`, VN case builder, VN defaults, DPPA appliers |
| `proforma_thailand/` | PEA rates, TH case builder, TH defaults, TH labels |

`esco_pro_forma.py` splits: its generic path and `_apply_direct_ownership` move
to `proforma_core/reopt_adapter.py`; `_apply_physical_dppa` and the DPPA currency
converters stay in `proforma_vietnam` and register as hooks.

### 2. The CountryProfile seam

```python
@dataclass(frozen=True)
class CountryProfile:
    country: str                 # "Vietnam" | "Thailand"
    local_currency_code: str     # "VND" | "THB"
    utility_label: str           # "EVN" | "PEA"
    tariff_builder: Callable     # build_evn_tariff | build_pea_tariff
    defaults: dict               # <country>_defaults.json
    time_steps_per_hour: int     # 1 | 4
```

Three mechanical changes, all confined to `proforma_core`:

1. `_vnd` becomes `_local` in the compute layer, in schema suffix detection
   (`proforma_schema.py:247`) and in the renderer fallback
   (`xlsx_builder.py:906`). `_usd` is untouched. The rename covers keyword
   arguments as well as emitted keys, so
   `calculate_vietnam_esco_cash_flow(exchange_rate_vnd_per_usd=...)` becomes
   `calculate_esco_cash_flow(exchange_rate_local_per_usd=...)`, and the
   public entry points lose their `vietnam` infix
   (`build_vietnam_report_data` becomes `build_report_data`,
   `build_vietnam_esco_workbook` becomes `build_esco_workbook`).
   `proforma_vietnam` keeps thin aliases under the old names so
   `rebuild_report.py` and `views.py` continue to import successfully during
   the refactor.
2. Renderers read the display code and utility label from the profile, emitting
   "(VND)"/"EVN" or "(THB)"/"PEA".
3. `_read_8760_load_csv` becomes resolution-aware, validating
   `8760 * time_steps_per_hour` entries.

**Explicitly unchanged**: Vietnam input API names (`pv_capex_vnd`,
`annual_om_vnd` in `run_case.VIETNAM_REPORT_QUERY_KEYS` and `views.py:470`).
These are country-specific input names; renaming them would break replay of the
8 saved cases. Thailand gets `_thb` input names on its own path.

**Acceptance**: all 8 Vietnam workbooks rebuild cell-identical via
`rebuild_report.py`, and `test_cash_flow.py`, `test_audit_sheets.py`,
`test_reference_esco_workbook.py`, `test_reference_dppa_workbook.py` pass
unchanged. This phase adds zero new behavior.

### 3. PEA tariff module

`reoptjl/src/thailand/pea_tariff.py` + `pea_rates.json`, mirroring the EVN
module vintage-keyed structure: fallback to the latest vintage at or before the
requested year, with `rate_vintage_year` / `rate_vintage_source` audit keys
popped into assumptions rather than the REopt payload.

PEA Schedule 4, Large General Service, 22-33 kV, TOU:

| Component | Value | REopt mapping |
|---|---|---|
| Peak energy | 4.1839 THB/kWh | `tou_energy_rates_per_kwh`, 35,040-length |
| Off-peak energy | 2.6037 THB/kWh | same array |
| Ft adjustment | 0.3672 THB/kWh | added to every timestep, versioned separately |
| Demand | 132.93 THB/kW | `coincident_peak_load_charge_per_kw` (12 entries) + `coincident_peak_load_active_time_steps` (12 monthly peak-period timestep sets) |
| Service charge | 312.24 THB/month | no REopt input exists; identical in BAU and optimized, cancels out of savings; proforma display only |
| VAT | 7% | outside the optimization, applied in the proforma (mirrors Vietnam) |
| Export | none | `can_net_meter=false`, `can_wholesale=false`, `can_export_beyond_nem_limit=false`, `can_curtail=true` |

Periods: peak 09:00-22:00 Mon-Fri; off-peak 22:00-09:00 Mon-Fri plus all day
Saturday, Sunday and Thai public holidays.

**Ft is modelled as a forecast, not a constant.** 0.3672 THB/kWh is the current
four-month window and is revised three times a year. At roughly 9% of the
off-peak rate it is not a rounding error over 25 years, so it carries its own
escalating series and its own disclosure line rather than being folded silently
into the base rate.

Rates are converted THB to USD at the contract FX rate before optimization,
mirroring the Vietnam VND to USD convention.

### 4. Load pipeline

Source: `01_Load_Data/ROFU Thailand 15-Minute Interval Data.xlsm`, sheet
`Raw Total Consumption`.

Verified during design: 39,936 rows = 416 days x 96 intervals, spanning
2025-06-01 to 2026-07-21, with **zero gaps and zero nulls**. Every day carries
all 96 intervals. Peak 15-minute consumption is 374.4 kWh, implying 1,497.6 kW.

The sheet carries a `DayType` column (Weekday / Holiday) that encodes the PEA
day classification: 138 Holiday days of 416, being Saturdays, Sundays and Thai
public holidays. This is the holiday calendar, derived from meter data rather
than reconstructed. It is cross-checked against the holiday list in
`RTS Data Collection_KTH_followup_Dec2025 (rebuilt).xlsx`.

**Window: 2025-07-01 to 2026-06-30.** Twelve complete calendar months, entirely
inside the data, 365 days (2026 is not a leap year), exactly 35,040 intervals,
with month boundaries aligned to billing for tie-out.

Output: a 35,040-row CSV plus a QA report reconciling window totals against the
workbook `Daily Breakdown` sheet.

### 5. Bill tie-out test

The `Summary` sheet carries bill-derived monthly demand and total THB for
Jan-Nov 2025, sourced from the 11 invoices in `02_Bills_2025/`. The interval data
starts 2025-06-01, so the usable overlap is **six months, Jun-Nov 2025**. The
tie-out is a blocking test over those six months: modelled BAU bill versus actual
invoice, month by month.

A design-time sanity check already passes: mean interval 209.9 kWh gives roughly
604,500 kWh/month; at about 3.0 THB/kWh blended plus 0.3672 Ft, plus 1,300 kW at
132.93 THB/kW, plus 7% VAT, the estimate is about 2.4M THB against actual bills
of 2.38-2.58M THB.

### 6. Site constraints

| Constraint | Value | Treatment |
|---|---|---|
| Roof area | 5 roofs at 24x108 m (2,592 m2) and 30x108 m (3,240 m2); split between the two sizes not stated, so gross is 12,960-16,200 m2 | PV `max_kw` approximately 1.7-2.1 MWp at ~65% usable and ~200 W/m2. Requires confirmation from Ou. **Until confirmed, the case uses the conservative lower bound (all five roofs at 24x108 m, so 1.7 MWp)** and carries the assumption as a flagged stub. |
| Interconnection | 4 transformers (500 kVA x2, 1,600 kVA, 630 kVA) = 3,230 kVA, one connection point, described as already fully loaded | Not the PV ceiling against a ~1,500 kW site peak, but "fully loaded" must be clarified before sizing BESS charging |
| Roof age | Oldest over 20 years, newest replaced 2024 | Either exclude aged roofs from usable area or carry a roof-renewal cost against a 25-year asset |
| Site lease | 3-year rolling, last renewed Oct 2024, next renewal Oct 2027 | Risk disclosure under direct ownership; becomes central to contract tenor under the later ESCO structure |
| Outages | About one per month, no backup generation | Secondary resilience value; out of scope for the first deliverable |

### 7. Defaults and flagged stubs

`proforma_thailand/defaults/thailand_defaults.json`, mirroring the
`vietnam_defaults.json` versioned shape.

Known: CIT 20% flat (maps to the existing `standard_flat` regime), VAT 7%, PEA
Schedule 4 rates, 5-year loss carryforward, FX THB/USD.

To verify against a Thai tax reference, not guessed: depreciation lives.
The Thai Revenue Code generally allows machinery at 20% per year straight
line, i.e. 5 years, against Vietnam 20-year PV and 8-year BESS. This is a large
difference in tax-shield timing that flows directly into IRR.

Stubs, each carrying `"source": "PLACEHOLDER - pending Keen confirmation"` and
rendering with a visible marker on the Assumptions sheet: capex per kWp, BESS
capex, debt fraction, debt rate, debt tenor, insurance, connection cost,
permitting and EIA study cost, O&M, PEA tariff escalation, Ft forecast.

Guard rail: a `validate_workbook` rule that **fails** if a placeholder value
reaches a headline metric (IRR, NPV, payback) without a placeholder marker
attached. The failure mode being made impossible is a stubbed capex quietly
producing a confident-looking IRR in a client deck.

## Open questions resolved before build (Phase 0)

1. **Does REopt.jl handle `coincident_peak_load_charge_per_kw` correctly at
   `time_steps_per_hour=4`?** 12 sets of roughly 1,130 timesteps each is within
   the array padding at `models.py:1799`, but sub-hourly coincident-peak
   behaviour is unverified. The entire demand-charge and BESS value story rests
   on it. Go/no-go.
2. **Is the site on TOU (Schedule 4.2) or TOD (Schedule 4.1)?** The Summary sheet
   reports three monthly demand values (on-peak 1,208-1,376 kW, off-peak,
   holiday) all within about 4% of each other. 132.93 THB/kW is the TOU on-peak
   demand rate, which bills on-peak demand only, but three recorded demands is
   also what a TOD bill looks like, and TOD rates differ completely (about 224
   on-peak, 30 partial, 0 off-peak). Must be settled against an actual invoice
   PDF in `02_Bills_2025/`. Go/no-go.

## Phases

| Phase | Work | Acceptance |
|---|---|---|
| 0. Spike | Resolve the two open questions above | Both answered; design confirmed or revised |
| 1. Refactor | `proforma_core` + `CountryProfile` | 8 Vietnam workbooks rebuild cell-identical; existing suites pass unchanged |
| 2. Tariff | `reoptjl/src/thailand/` PEA builder + rates JSON | Six-month bill tie-out passes |
| 3. Load | xlsm to 35,040-row CSV, window selection, QA report | Window totals reconcile to `Daily Breakdown` |
| 4. Case | `proforma_thailand` builder + defaults + DIRECT_OWNERSHIP at 15-min | Dry-run payload validates |
| 5. Run | RTS and RTS+BESS cases | Sizing, grid-offset %, workbook |
| 6. Later | ESCO/PPA structure | Out of scope for this spec |

## Out of scope

- ESCO/PPA and roof-lease / hire-purchase structures (Phase 6, separate spec)
- Thai direct-PPA / ERC third-party grid access
- Resilience and outage valuation
- Any change to Vietnam behaviour or output
