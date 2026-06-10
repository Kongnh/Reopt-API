# DPPA Commercial Negotiation Sweep Design

Date: 2026-06-10

## Purpose

Build a fixed-system commercial term sweep that supports a joint negotiation
between Factory A and the ESCO/generator. The study converts the validated
Factory A DPPA settlement model into a shared decision tool that shows the
trade-off between factory savings and seller bankability.

The study does not optimize for either party in isolation. It identifies the
set of commercially balanced terms and discloses how each term compares with
both the EVN-only BAU and the existing non-DPPA ESCO alternative.

## Fixed Technical Baseline

Use the clean Factory A `case_2` technical result as the fixed baseline:

- Clean load profile and Decision 963 EVN tariff
- Existing PV and BESS sizing
- Existing hourly dispatch
- Existing financing and ESCO assumptions
- Existing FMP and CFMP hourly series
- Existing Phase 3 DPPA settlement formulas

The sweep changes commercial terms only. It must not rerun REopt or alter PV,
BESS, dispatch, load, tariff, financing, or settlement formulas.

The clean `case_5` result is the reconciliation reference because it uses the
same technical result and a 100% contract volume at a 2,000 VND/kWh strike.

## Scenario Grid

Run all combinations of:

- CfD strike: 1,400 through 2,200 VND/kWh, inclusive, in 100 VND/kWh increments
- Contract volume: 70%, 80%, 90%, and 100% of the clean `case_2` expected
  hourly `Q_re_meter`

This creates exactly 36 scenarios.

For every scenario, preserve the hourly shape of the reference contract-volume
series and multiply every hourly value by the selected volume fraction.

Each scenario identifier must be deterministic and readable, for example:

```text
strike_1800_volume_80
```

## Scenario Evaluation

For each scenario:

1. Copy the validated DPPA inputs in memory.
2. Replace the CfD strike with the selected strike.
3. Scale the reference hourly contract-volume series by the selected fraction.
4. Reuse the existing DPPA settlement and Vietnam ESCO cash-flow functions.
5. Extract joint-negotiation metrics and classify the scenario.

Required metrics:

- CfD strike in VND/kWh
- Contract-volume fraction and annual contracted kWh
- Factory Year 1 savings versus BAU, in USD and percent
- Factory Year 1 savings versus non-DPPA `case_2`, in USD and percent
- Factory Year 1 total outflow
- ESCO/generator equity IRR
- ESCO/generator NPV
- Minimum DSCR over years with debt service
- Average DSCR
- Generator Year 1 revenue
- CfD Year 1 net transfer
- Whether the CfD net transfer is buyer-to-seller, seller-to-buyer, or zero
- Balanced-deal qualification status
- Failed qualification reason or reasons
- Pareto-frontier status

The non-DPPA `case_2` comparison is a prominent disclosure metric, but it is
not a qualification gate.

## Balanced-Deal Qualification

A scenario qualifies as a balanced deal only when all of these conditions are
true:

- Factory Year 1 savings versus BAU is at least 0%
- ESCO/generator equity IRR is at least 12%
- Minimum DSCR over years with debt service is at least 1.20x

The classification must show each gate separately so both parties can see why
a scenario fails.

## Negotiation Frontier And Recommendation

Within the balanced-deal scenarios, remove dominated terms. A scenario is
dominated when another balanced scenario provides both:

- Greater or equal factory Year 1 savings versus BAU; and
- Greater or equal ESCO/generator equity IRR;

with at least one metric strictly greater.

The remaining scenarios form the negotiation frontier.

The study must recommend a practical negotiation range rather than one rigid
term. Recommendations should prioritize margin above the 12% equity IRR and
1.20x minimum DSCR floors instead of selecting a term exactly at either floor.
The recommendation must also disclose the factory's result versus non-DPPA
`case_2`.

## Outputs

Write all generated artifacts to a dedicated Factory A negotiation-study
directory. The output package contains:

### Machine-Readable Results

A JSON file containing:

- Study configuration and qualification thresholds
- Fixed-baseline source paths and identifiers
- All 36 scenario result rows
- Balanced-deal shortlist
- Negotiation-frontier shortlist
- Recommended negotiation range
- Reconciliation results

### Joint-Negotiation Workbook

An Excel workbook containing:

- `Executive Summary`: thresholds, counts, recommended range, and key
  disclosures
- `Scenario Matrix`: all 36 scenarios and required metrics
- `Balanced Deals`: scenarios passing all qualification gates
- `Negotiation Frontier`: non-dominated balanced scenarios
- `Strike-Volume Matrix`: compact strike-by-volume qualification matrix
- `Factory Savings Heatmap`: Year 1 savings versus BAU
- `ESCO IRR Heatmap`: equity IRR
- `Minimum DSCR Heatmap`: minimum DSCR
- `Methodology`: fixed baseline, formulas reused, thresholds, and limitations

The workbook must use clear buyer, seller, and lender labels. It must not imply
that beating BAU means beating non-DPPA `case_2`.

### Concise Negotiation Summary

A short Markdown summary suitable for presentation or email that states:

- The balanced-deal range
- The negotiation frontier
- The recommended starting range
- The main concession trade-offs
- Comparison against BAU and non-DPPA `case_2`
- Material limitations and assumptions

## Reconciliation And Validation

The study is accepted only when:

- Exactly 36 unique scenarios are present.
- Every contract-volume series is the exact hourly reference series multiplied
  by its selected fraction.
- The 100% volume, 2,000 VND/kWh scenario reproduces clean `case_5` within a
  documented numerical tolerance for Year 1 DPPA settlement totals, equity
  IRR, NPV, and DSCR.
- Balanced-deal classification applies all three gates consistently.
- Minimum DSCR excludes years without debt service.
- Pareto-frontier classification follows the stated dominance rule.
- Selected scenarios reconcile against the existing workbook calculations.
- The workbook and Markdown summary disclose comparisons against both BAU and
  non-DPPA `case_2`.

## Implementation Boundaries

The implementation should add a dedicated sweep runner and a dedicated
negotiation workbook builder under `proforma_vietnam/`, with focused tests.

It must reuse existing functions for DPPA settlement and ESCO cash flow. It
must not:

- Clone 36 case directories
- Submit or rerun REopt jobs
- Modify Julia
- Modify Django models or API behavior
- Modify the US pro forma
- Change Phase 3 settlement formulas
- Add market-price sensitivity cases in this scope
- Change the technical system sizing or dispatch

## Known Interpretation

Because the factory qualification gate is savings versus BAU, a balanced deal
may still be worse for the factory than non-DPPA `case_2`. The output package
must make that trade-off visible, but such a result does not disqualify the
scenario.
