# Coincident-peak verification against the live solver

Date: 2026-09-04
Run UUID: `63d89a15-7560-4ce9-9ccd-393c6c9e79df`
Status: `optimal`
REopt version: 0.57.0

## Verdict

PASS, exactly. The coincident-peak demand charge is correct at
`time_steps_per_hour=4`.

| | USD |
|---|---|
| Expected (computed independently from the load CSV and the PEA rate) | 67,670.78 |
| REopt `year_one_coincident_peak_cost_before_tax` | 67,670.78 |
| Difference | 0.00 (0.0000%) |

`year_one_demand_cost_before_tax` is `0.0` and every entry of
`monthly_demand_cost_series_before_tax` is `0.0`, confirming the charge flows
entirely through the coincident-peak path and that `monthly_demand_rates` is
not being used.

## What this confirms

- The Julia constraint at `julia_src/reopt_model.jl:1049` compares power to
  power and omits `TimeStepScaling`, so it is resolution-agnostic. The source
  review said so; this is the end-to-end proof.
- The 1-based indexing in `coincident_peak_load_active_time_steps` is right. An
  off-by-one would have shifted which intervals were billed and produced a
  different peak in at least one month.
- The 12 monthly period maxima REopt bills match the on-peak maxima derived from
  the raw interval data.

## Case

`proforma_thailand/cases/coincident_peak_spike/case.json` - the real Rofu load at
15 minutes, PV and storage both disabled, so the run is a pure BAU bill.

## Two defects this run caught that unit tests did not

Both were in the payload the case builder emits, and both were invisible to the
mocked unit tests. This is the whole reason the spec asked for a live check.

1. **`ElectricLoad.year` was missing.** The solver rejected the payload outright:
   `Must provide ElectricLoad.year when using loads_kw input`
   (`core_electric_load.jl:137`). Now derived from the first entry of
   `calendar_year_months` so it cannot drift from the synthetic calendar. 2026 is
   not a leap year, which matches the 365-day, 35,040-interval series.

2. **A zero-PV case shipped an unresampled 8760 production series.**
   `reoptjl/validators.py:226` only resamples `production_factor_series` when
   `max_kw > 0`. With PV disabled the 8760 series reached Julia unchanged and the
   solve died with
   `DimensionMismatch(tried to assign 8760 element array to 35040 destination)`
   in `setup_pv_inputs`. The builder now omits the `PV` block entirely when
   `max_kw` is 0, mirroring how storage is handled.

   Note the narrower conclusion: for a PV-enabled run the resampling does fire,
   so an 8760 PVWatts series is legitimate input there. Only the disabled case
   was broken.

## Expected warnings

The run emits warnings for AVERT, Cambium and EASIUR lookups. All three are US
datasets and the site is in Thailand, so emissions and health-cost factors are
set to zero. Harmless here, but it means REopt's emissions outputs are not
meaningful for this project and must not be reported.
