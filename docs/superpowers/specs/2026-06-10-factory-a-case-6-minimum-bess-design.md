# Factory A Case 6 Minimum BESS Design

## Goal

Create Factory A `case_6` from `case_5`, changing only the fixed PV and BESS
sizes and regenerating the DPPA contract-volume profile from the resulting
case 6 dispatch.

## Fixed Technical Sizes

- PV: `5,914 kW`
- Battery power: `592 kW`
- Battery energy: `1,184 kWh`

These are convenient rounded values derived from the requirement that battery
power is at least 10% of case 5 PV capacity and battery duration is two hours.

## Workflow

1. Clone `case_5/case.json` into `case_6/case.json`.
2. Set PV `min_kw` and `max_kw` to `5914`.
3. Set storage `min_kw` and `max_kw` to `592`.
4. Set storage `min_kwh` and `max_kwh` to `1184`.
5. Run REopt once to obtain the case 6 dispatch.
6. Regenerate the 8760 DPPA contract-volume profile as:
   `PV-to-load + PV-to-grid + curtailed PV + storage-to-load + storage-to-grid`.
7. Run the complete case again to produce internally consistent final
   optimizer and Vietnam financial-model outputs.

## Preserved Inputs

All other case 5 inputs remain unchanged, including the clean load profile,
tariff, technology costs, financial assumptions, DPPA strike, and settlement
configuration.

## Verification

- Final REopt status is `optimal`.
- Final PV size is `5,914 kW`.
- Final storage size is `592 kW / 1,184 kWh`.
- The final 8760 DPPA contract-volume profile matches the stated dispatch
  formula hour by hour.
- `payload.json`, `assumptions.json`, `results.json`, and the Vietnam report
  workbook are generated under `outputs/vietnam_case/factory_a/case_6/`.
