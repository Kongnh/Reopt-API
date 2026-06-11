# Vietnam ESCO Contract Model Design

Last updated: 2026-06-06

## Purpose

This design defines the Phase 2 Vietnam ESCO contract model used by the
`proforma_vietnam` cash-flow module.

The model is a post-processing financial model. REopt optimizes the technical
system first. The Vietnam pro forma then evaluates the optimized PV/BESS size,
dispatch, tariff savings, contract payments, debt service, tax, and investor
returns.

ROI, IRR, NPV, DSCR, and payback are outputs of the pro forma. They are not
initial sizing inputs in the first implementation.

## Scope

Included in Phase 2:

- Third-party ESCO ownership.
- Offtaker continues paying EVN for residual grid electricity.
- Offtaker pays ESCO for project-served PV energy at a discount to EVN energy
  tariff.
- Demand-charge savings are calculated from REopt results and shared between
  ESCO and offtaker.
- Grid-charging arbitrage is optional and, when enabled, belongs fully to ESCO.
- EVN energy and capacity charge escalation are explicit assumptions.

Excluded from Phase 2:

- DPPA settlement.
- Grid loss factors.
- Virtual DPPA eligibility.
- Detailed electron tracing beyond the battery settlement rules below.
- Julia optimizer changes.
- Existing US `proforma/` changes.

## Contract Alternatives Considered

### Option A: Fixed Annual Service Payment

The offtaker pays ESCO a fixed annual fee regardless of realized tariff savings.
This is closest to existing REopt third-party ownership behavior.

This option is simple, but it does not clearly explain how PV energy, peak
shaving, and battery arbitrage value are shared.

### Option B: Fixed VND/kWh PPA Tariff

The offtaker pays ESCO a fixed first-year tariff for project-served energy,
with optional annual escalation.

This is bankable for ESCO revenue, but it is less transparent to the offtaker
unless benchmarked against EVN tariffs.

### Option C: Discount To EVN Tariff With Explicit Savings Streams

The offtaker pays ESCO a discount to the time-specific EVN energy tariff for
PV-served load. Demand-charge savings and optional grid-charging arbitrage are
separate line items.

This is the selected Phase 2 design because it keeps offtaker savings visible,
keeps demand savings separate from energy pricing, and fits Vietnam ESCO
negotiation logic.

## Selected Model

### Calculation Order

```text
1. Run REopt optimization.
2. Read optimized PV/BESS size and dispatch.
3. Calculate BAU EVN bill.
4. Calculate optimized EVN bill.
5. Calculate ESCO contract payments.
6. Calculate offtaker savings.
7. Calculate ESCO revenue, O&M, debt service, CIT, and equity cash flow.
8. Report ROI, project IRR, equity IRR, NPV, DSCR, and payback.
```

### Core Inputs

```text
evn_energy_escalation_rate
evn_capacity_escalation_rate
esco_energy_discount_fraction
esco_demand_savings_share
grid_charging_enabled
esco_grid_arbitrage_share
```

Default values:

```text
evn_energy_escalation_rate = 0.04
evn_capacity_escalation_rate = 0.04
esco_energy_discount_fraction = scenario input
esco_demand_savings_share = 0.80
grid_charging_enabled = false
esco_grid_arbitrage_share = 1.00
```

The ESCO energy tariff is pegged back-to-back to EVN energy tariff escalation.
Only one EVN escalation assumption is needed for that side of the contract.

### Energy Offtake Payment

The ESCO energy price is a discount to the time-specific EVN energy tariff in
the current tariff year.

```text
esco_energy_price[h] =
  evn_energy_rate[h] * esco_energy_discount_fraction
```

In future years:

```text
esco_energy_price[h, year] =
  esco_energy_price[h, year_1] * (1 + evn_energy_escalation_rate)^(year - 1)
```

The discount applies to energy tariff only. It does not include demand or
capacity charge value.

The energy payment applies to:

```text
PV energy served directly to load
+ PV-charged battery discharge served to load
```

The energy payment does not apply to grid-charged battery discharge.

```text
esco_energy_revenue =
  sum(project_served_pv_kwh[h] * esco_energy_price[h])
```

### Demand-Charge Savings

Demand-charge savings are calculated from REopt results.

```text
demand_charge_savings =
  bau_demand_charge
- optimized_demand_charge
```

The default split is:

```text
ESCO: 80%
Offtaker: 20%
```

```text
esco_demand_revenue =
  max(demand_charge_savings, 0) * esco_demand_savings_share
```

Future demand-charge values escalate with the capacity charge escalation
assumption.

```text
demand_charge_savings[year] =
  demand_charge_savings[year_1] * (1 + evn_capacity_escalation_rate)^(year - 1)
```

### Grid-Charging Arbitrage

Grid charging is disabled in the base case.

```text
grid_charging_enabled = false
```

When grid charging is enabled as an optional scenario, net grid-charging
arbitrage value belongs fully to ESCO.

```text
esco_grid_arbitrage_share = 1.00
```

Grid charging cost remains inside the optimized EVN bill. ESCO only receives
net positive arbitrage value, not gross battery discharge revenue.

```text
net_grid_arbitrage_value =
  grid_charged_battery_discharge_avoided_energy_cost
- grid_charging_energy_cost
```

```text
esco_grid_arbitrage_revenue =
  max(net_grid_arbitrage_value, 0) * esco_grid_arbitrage_share
```

If Phase 2 cannot reliably separate grid-charged discharge from PV-charged
discharge using available REopt outputs, the first implementation should keep
grid charging disabled and report grid-charging arbitrage as unavailable until
the attribution data is available.

### Offtaker Cost And Savings

```text
offtaker_post_project_cost =
  optimized_evn_bill
+ esco_energy_revenue
+ esco_demand_revenue
+ esco_grid_arbitrage_revenue
```

```text
offtaker_savings =
  bau_evn_bill
- offtaker_post_project_cost
```

```text
offtaker_savings_fraction =
  offtaker_savings / bau_evn_bill
```

There is no hard minimum offtaker savings threshold in the base design. The
threshold depends on the input ESCO discount and the negotiated customer case.

### ESCO Cash Flow

```text
esco_revenue =
  esco_energy_revenue
+ esco_demand_revenue
+ esco_grid_arbitrage_revenue
```

```text
esco_cash_flow_before_financing =
  esco_revenue
- O&M
- replacement_costs
- CIT
```

```text
esco_equity_cash_flow =
  esco_cash_flow_before_financing
- debt_service
- equity_investment
```

The pro forma reports ESCO ROI, project IRR, equity IRR, NPV, DSCR, and payback
as outputs. A later pricing mode may solve for the discount needed to hit a
target equity IRR, but that is outside the first cash-flow implementation.

## Implementation Notes

- Keep assumptions in `proforma_vietnam` constants or function inputs first.
- Avoid Django model migrations until persistent user-configurable inputs are
  clearly required.
- Keep the US `proforma/` path unchanged.
- Use VND as the base currency.
- Use the existing Vietnam tax and straight-line depreciation helpers from
  `proforma_vietnam/tax_model.py`.
- Add tests around the cash-flow formulas before implementing the production
  module.

## Acceptance Criteria

- Given REopt BAU and optimized bills, the cash-flow module calculates ESCO
  energy revenue from time-specific EVN rates and the input discount.
- Demand-charge savings are calculated from REopt results and split 80% ESCO /
  20% offtaker by default.
- Base case disables grid charging.
- Optional grid-charging scenario assigns 100% of net grid-arbitrage value to
  ESCO.
- Offtaker savings are calculated after all ESCO payments.
- ROI, IRR, NPV, DSCR, and payback are outputs.

## Phase 3: DPPA Settlement Layer

Phase 3 adds a Direct Power Purchase Agreement (DPPA) settlement mode on top of
the Phase 2 ESCO cash flow. The Phase 2 discount-to-EVN base case remains the
default behavior. DPPA settlement is opt-in via a new `dppa.type` enum.

### Scope

Included in Phase 3:

- Grid-connected DPPA with bilateral CfD overlay (`dppa.type = "grid_dppa_cfd"`).
- Pure-spot grid DPPA (Điều 14–16 without CfD) reachable by setting
  `cfd_contract_volume_kwh_per_hour = 0`.
- BESS co-located with the RE generator only.
- Single-entity model where the ESCO is also the renewable generator.

Excluded from Phase 3 (deferred):

- Private-wire DPPA (Điều 25).
- Factory-side BESS configuration.
- REopt optimizer alignment with FMP.
- Spot-price stochastics, REC accounting, congestion pricing.
- Multi-buyer allocation (`delta < 1`).
- MOIT annual re-set of `f_dppa` and `f_cl`.

### Contract Type Enum

```text
dppa.type = "none"           # Phase 2 behavior (default)
dppa.type = "grid_dppa_cfd"  # Grid-connected DPPA per ND57 Điều 14-18
```

Eligibility for `grid_dppa_cfd` (ND57 Điều 16):

```text
voltage_level in {"110kv_and_above", "22_to_110kv"}
```

### BESS Configuration

Two BESS siting options exist in Vietnam DPPA deals:

- Co-located with the RE generator: sits upstream of the offtaker meter; can
  only charge from PV.
- Factory-side (offtaker-owned): sits behind the offtaker meter; can charge
  from the grid at retail tariff.

Phase 3 covers only the co-located case. The case builder forces
`ElectricStorage.can_grid_charge = false` and raises a validation error if the
case JSON sets it to `true`.

### Energy Buckets

Sourced from REopt V3 dispatch output series. BESS sits upstream of the
offtaker meter, so its discharge counts toward generator-side injection.

```text
Q_re_meter[h]    = pv_to_load[h]
                 + pv_to_grid[h]
                 + storage_to_load[h]
                 + storage_to_grid[h]

Q_re_delivered[h] = pv_to_load[h] + storage_to_load[h]

Q_Khc[h]          = min(load[h], Q_adj[h])

shortfall[h]      = load[h] - Q_Khc[h]
```

`Q_Khc` is the matched-consumption settlement quantity (corrected 2026-06-11):
the buyer settles C_DN/C_DPPA/C_CL only on the portion of loss-adjusted
generation it actually consumes in the hour. Excess generation above the
hourly load is sold by the generator at FMP and is never billed to the buyer.

### Settlement Math

ND57-prescribed losses and fees are applied per hour. Defaults reflect 2025
NLDC and EVN values.

```text
Q_adj[h] = Q_re_meter[h] / K_pp * delta
```

```text
C_DN[h]   = Q_Khc[h] * CFMP[h] * K_pp        # spot energy, buyer-side price
C_DPPA[h] = Q_Khc[h] * f_dppa_per_kwh        # -> EVN/regulator
C_CL[h]   = Q_Khc[h] * f_cl_per_kwh          # -> EVN/regulator
C_BL[h]   = shortfall[h] * P_evn[h]          # -> EVN retail TOU
Q_cfd[h]  = min(Q_c[h], Q_Khc[h])
CfD[h]    = (P_c[h] - FMP[h]) * Q_cfd[h]     # offtaker <-> ESCO, matched contracted volume
```

ESCO/generator revenue and offtaker DPPA cost per hour:

```text
generator_revenue[h] = Q_re_meter[h] * FMP[h] + CfD[h]
offtaker_cost[h]     = C_DN[h] + C_DPPA[h] + C_CL[h] + C_BL[h] + CfD[h]
```

Defaults:

```text
k                              = 1.026  # price conversion only: CFMP = FMP * k
K_pp (>=110 kV)                = 1.008525
K_pp (22 to 110 kV)            = 1.027263
delta                          = 1.0
f_dppa_per_kwh (2025, VND)     = 360
f_cl_per_kwh   (2025, VND)     = 163.3
```

Per the official NSMO CD7 simulation examples, `k` converts FMP to CFMP and
does not reduce the settlement quantity. CfD settlement is capped by both the
contract volume and the buyer's matched-consumption quantity.

### Annual Escalation

```text
f_dppa[year]     = f_dppa[year_1] * (1 + dppa.fee_escalation_rate)^(year - 1)
f_cl[year]       = f_cl[year_1]   * (1 + dppa.fee_escalation_rate)^(year - 1)
FMP[year]        = FMP[year_1]    * (1 + dppa.fee_escalation_rate)^(year - 1)
P_c[year]        = P_c[year_1]    * (1 + dppa.cfd_strike_escalation_rate)^(year - 1)
C_BL[year]       = C_BL[year_1]   * (1 + evn_energy_escalation_rate)^(year - 1)
```

`dppa.cfd_strike_escalation_rate` is signed. Positive values model an
escalating strike. Negative values model a strike that ratchets down annually
per the PPA negotiation. Default 0.

Default for `dppa.fee_escalation_rate` is the existing
`evn_energy_escalation_rate` (4 percent per year).

### Multi-Year Mechanics (added 2026-06-11)

The cash flow applies the following real-world mechanics across the analysis
period (all opt-out by overriding the relevant input):

- **PV degradation**: generation-linked revenue and buyer settlement terms
  scale by `(1 - pv_degradation_rate)^(year - 1)`. The rate is derived from
  the REopt `PV.degradation_fraction` input (default 0.5 percent per year).
  Matched energy lost to degradation is repurchased from EVN at retail
  (added to the residual bill / C_BL). The CfD settles on the contracted
  volume and does not degrade.
- **O&M escalation**: `om_escalation_rate` compounds annual O&M (default 0).
- **Battery replacement**: a replacement expense is booked in the configured
  `battery_replacement_year` assumption (Factory A cases use year 11) at
  `size_kw × replace_cost_per_kw + size_kwh × replace_cost_per_kwh`,
  derived automatically from REopt inputs/outputs unless the assumption or
  `replacement_costs_by_year` is overridden.
- **Vietnam CIT**: 4-year exemption + 9-year 50 percent reduction counted
  from the first profitable year (no later than year 4, Circular 78/2014
  Art. 18), with 5-year tax-loss carryforward (Art. 9).

### Cash-Flow Attribution

```text
Stream                                  | none       | grid_dppa_cfd
ESCO discount-to-EVN energy revenue     | OFF -> ESCO| zero (replaced)
Demand savings share (80/20)            | OFF -> ESCO| OFF -> ESCO
Grid arbitrage (when can_grid_charge)   | OFF -> ESCO| n/a (forced off)
C_DN spot energy                        | -          | OFF -> ESCO (via system)
C_DPPA system fee                       | -          | OFF -> EVN
C_CL delta adder                        | -          | OFF -> EVN
C_BL retail shortfall                   | OFF -> EVN | OFF -> EVN
CfD net                                 | -          | OFF <-> ESCO (signed)
Retail demand charge                    | OFF -> EVN | OFF -> EVN
```

For `dppa.type = "none"`, only the Phase 2 streams apply and the cash-flow
identities reduce exactly to the existing `calculate_vietnam_esco_cash_flow`
formulas. The Phase 2 reference workbook gate is preserved by construction.

### New Inputs

All new keys live in the case JSON under a new top-level `dppa` block. The
case builder flattens them into the existing assumptions dict. None of these
fields are added to the REopt payload; the optimizer is unaware of DPPA
settlement.

```text
dppa.type                                 string enum, default "none"
dppa.fmp_series_path                      string, default "DPPA DOC/fmp_cfmp_vn.json"
dppa.cfd_strike_per_kwh_vnd               float, required for grid_dppa_cfd
dppa.cfd_strike_escalation_rate           float (signed), default 0.04
dppa.cfd_contract_volume_kwh_per_hour     float or 8760-list, required
dppa.transmission_loss_factor_k           float, default 1.026; price conversion only
dppa.distribution_loss_factor_kpp         float, derived from voltage_level
dppa.allocation_fraction_delta            float in (0, 1], default 1.0
dppa.c_dppa_service_fee_vnd_per_kwh       float, default 360
dppa.c_cl_settlement_adder_vnd_per_kwh    float, default 163.3
dppa.fee_escalation_rate                  float, default evn_energy_escalation_rate
```

### Acceptance Criteria

- With `dppa.type = "none"` the existing reference workbook comparison passes
  with zero delta on every summary number.
- With `dppa.type = "grid_dppa_cfd"`, a hand-computed 24-hour fixture matches
  the implementation within 1 percent on `C_DN`, `C_DPPA`, `C_CL`, `C_BL`,
  CfD, generator revenue, and offtaker total cost.
- The case builder raises a validation error if `dppa.type != "none"` is set
  alongside `ElectricStorage.can_grid_charge = true`.
- The case builder raises a validation error if `dppa.type = "grid_dppa_cfd"`
  is set at a voltage level outside `{"110kv_and_above", "22_to_110kv"}`.
