# Vietnam ESCO Contract Model Design

Last updated: 2026-05-25

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
