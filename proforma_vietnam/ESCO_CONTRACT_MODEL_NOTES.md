# Vietnam ESCO Contract Model Notes

Last updated: 2026-05-23

## Purpose

These notes capture the commercial model questions for the Vietnam third-party investment pro forma. They are discussion notes, not a finalized implementation spec.

The current Phase 2 code should not move into cash-flow implementation until this contract model is clarified.

## Existing REopt Third-Party Model

The existing REopt pro forma treats third-party ownership as a two-party finance structure, not a detailed ESCO contract engine.

In the existing model:

- The offtaker does not buy the DER assets.
- The developer or third-party owner invests in the system.
- The offtaker continues to pay the utility bill with the optimized system.
- The offtaker also pays a fixed annualized payment to the third-party owner.
- Host benefit is calculated from utility bill savings net of the third-party payment.
- Developer benefit is calculated from project cost, tax effects, and host payments.

This is closest to a fixed annual service payment or lease-style payment. It is not explicitly modeled as:

- a discount to retail tariff,
- a fixed VND/kWh PPA tariff,
- a peak-shaving shared-savings contract,
- or an energy-arbitrage sharing contract.

## Vietnam ESCO Deal Components To Clarify

The Vietnam model should represent a third-party investment structure where the offtaker signs an ESCO contract covering energy offtake and peak shaving service.

The contract may need three separate value streams.

### 1. Energy Offtake Charge

The ESCO sells useful on-site energy to the offtaker.

Potential structures:

- Discount to EVN retail tariff, for example ESCO tariff equals 90% of the avoided EVN energy tariff.
- Fixed VND/kWh tariff.
- Hybrid: fixed first-year tariff with annual escalation linked to EVN or CPI.

Discussion point:

- Decide whether energy offtake should be based on PV-to-load only, storage-to-load, or all metered project-served energy.

### 2. Peak Shaving Service Charge

The ESCO creates value by reducing demand or capacity charges.

Potential structures:

- Shared savings based on verified demand charge reduction.
- Fixed VND/kW-month availability fee for committed peak reduction.
- Hybrid: minimum fixed service fee plus shared upside.

Recommended starting point for discussion:

- Shared savings from modeled demand charge reduction, because REopt already reports BAU and optimized demand costs.

Discussion point:

- Decide the default ESCO/offtaker split, for example 70% ESCO and 30% offtaker, or another negotiated value.

### 3. Energy Arbitrage Benefit

Battery dispatch can reduce energy cost by charging during lower-cost hours and discharging during higher-cost hours.

This needs careful treatment because the battery can charge from both grid energy and solar energy. A simple cash-flow model should avoid overclaiming value from electron tracing.

Potential structures:

- Treat arbitrage as part of total utility bill savings and share the savings by contract rule.
- Attribute arbitrage only to grid-charged battery cycles.
- Attribute battery discharge value by proportional source mix: solar-charged share and grid-charged share.

Recommended starting point for discussion:

- Treat arbitrage as part of total avoided utility bill, then allocate by agreed savings-share rule. Grid-charging cost remains inside the optimized utility bill and therefore automatically reduces net savings.

Discussion point:

- Decide whether Phase 2 needs source attribution for battery discharge, or whether that belongs in a later Phase 3+ contract-settlement model.

## Candidate Vietnam ESCO Cash Flow Structure

A practical first model could calculate offtaker and ESCO economics as:

```text
Offtaker cost after project =
  EVN bill with project
+ ESCO energy offtake payment
+ ESCO peak shaving service payment
+ ESCO arbitrage sharing payment
```

```text
Offtaker savings =
  BAU EVN bill
- Offtaker cost after project
```

```text
ESCO revenue =
  energy offtake revenue
+ peak shaving service revenue
+ arbitrage sharing revenue
```

```text
ESCO cash flow =
  ESCO revenue
- O&M
- debt service
- CIT
- capital investment or equity contribution
```

## Recommended Default For First Implementation

For the first Vietnam ESCO model, use a shared-savings structure with explicit line items:

- Energy offtake: discount to EVN retail energy tariff.
- Peak shaving: shared demand-charge savings.
- Energy arbitrage: shared remaining energy savings after accounting for energy offtake and optimized utility bill.

This should remain configurable, but the first implementation should avoid Django model migrations unless a real scenario requires persistent user-configurable overrides.

## Open Questions For Next Discussion

1. Should the base energy offtake price be a discount to EVN tariff, fixed VND/kWh, or fixed tariff with EVN-linked escalation?
2. Should ESCO charge energy offtake on PV-to-load only, storage-to-load, or all project-served energy?
3. What is the default peak shaving savings split between ESCO and offtaker?
4. Should peak shaving payment be shared savings, fixed VND/kW-month, or hybrid?
5. Should arbitrage be shared from total utility savings, or explicitly attributed to grid-charged versus solar-charged battery discharge?
6. Should grid charging be allowed in the base ESCO case, or should the base case restrict battery charging to solar only?
7. What minimum offtaker savings threshold is required for the investment memo, for example 5%, 10%, or negotiated case-by-case?
8. What ESCO target equity IRR should be used as the base case, for example 12%, 15%, or another Vietnam-specific hurdle rate?
