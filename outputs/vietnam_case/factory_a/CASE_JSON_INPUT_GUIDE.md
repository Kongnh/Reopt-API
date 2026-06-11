# Vietnam ESCO Case JSON Input Guide

This guide explains the inputs in `case.json` for running a Vietnam REopt optimization and generating the Vietnam ESCO pro forma workbook.

Monetary inputs in this sample are USD unless the field name explicitly says `vnd` or `exchange_rate_vnd_per_usd`.

## Folder Convention

The site folder (`outputs/vietnam_case/factory_a/`) holds a template `case.json` plus one sub-folder per concrete scenario (`case_1/`, `case_2/`, …). Each scenario sub-folder owns its `case.json` and every artifact produced by the run (payload, assumptions, results, workbook). The runner writes outputs into the directory containing the supplied `--case` file, so each scenario stays self-contained:

```
outputs/vietnam_case/factory_a/
├── CASE_JSON_INPUT_GUIDE.md      # this file
├── case.json                     # template - copy into case_<n>/ to start a new scenario
├── case_1/                       # one scenario
│   ├── case.json                 # frozen scenario inputs
│   ├── payload.json              # REopt V3 payload sent to optimizer
│   ├── assumptions.json          # report/pro forma assumptions
│   ├── results.json              # REopt optimization results
│   └── vietnam_report_<run_uuid>.xlsx
├── case_2/                       # next scenario, created by user
│   └── case.json
└── …
```

## Run Commands

To create a new scenario, copy the template `case.json` into a fresh `case_<n>/` folder and edit it:

```powershell
mkdir outputs\vietnam_case\factory_a\case_2
copy outputs\vietnam_case\factory_a\case.json outputs\vietnam_case\factory_a\case_2\case.json
# edit case_2\case.json
```

Dry-run first to inspect the generated REopt payload and report assumptions (outputs land next to the `--case` file):

```powershell
python -m proforma_vietnam.run_case --case outputs\vietnam_case\factory_a\case_2\case.json --dry-run
```

Run the full end-to-end case after Docker services are available:

```powershell
docker-compose up -d

python -m proforma_vietnam.run_case --case outputs\vietnam_case\factory_a\case_2\case.json --poll-seconds 5 --max-polls 120
```

`--out` is still accepted for backward compatibility but defaults to the directory containing `--case`. A shared PVWatts cache lives at `outputs/pvwatts_cache/` and is reused across scenarios with the same lat/lon and PVWatts params.

Expected outputs (written into the same folder as `--case`):

- `payload.json`: REopt V3 optimizer payload.
- `assumptions.json`: Vietnam report/pro forma assumptions.
- `results.json`: REopt optimization results.
- `vietnam_report_<run_uuid>.xlsx`: Vietnam ESCO workbook.

## Case

| Field | Example | Meaning |
| --- | ---: | --- |
| `case.name` | `Factory A Vietnam ESCO E2E` | Human-readable case name. Used as the REopt payload description and report assumption label. |

## Site

| Field | Example | Meaning |
| --- | ---: | --- |
| `site.latitude` | `10.8231` | Project site latitude. Used by REopt for location-specific resource lookups when needed. |
| `site.longitude` | `106.6297` | Project site longitude. Used by REopt for location-specific resource lookups when needed. |

## Load Profile

| Field | Example | Meaning |
| --- | ---: | --- |
| `load_profile.year` | `2025` | Calendar year assigned to the 8760 hourly load. Must be a non-leap year for the current Vietnam tariff builder. |
| `load_profile.path` | `outputs/vietnam_case/factory_a/load.csv` | CSV path containing exactly 8760 hourly load values in kW. The case builder reads the first numeric column and skips a header row. |

## Tariff

| Field | Example | Options | Meaning |
| --- | ---: | --- | --- |
| `tariff.year` | `2025` | Supported configured years | EVN tariff table year. |
| `tariff.voltage_level` | `22-110kV` | `>=110kV`, `22-110kV`, `6-22kV`, `<6kV` | Customer voltage level used to select the EVN tariff. |
| `tariff.currency` | `usd` | `usd` for this sample | Currency sent to REopt for hourly energy rates and demand charges. Use USD for this sample so all optimizer money inputs are consistent. |
| `tariff.exchange_rate_vnd_per_usd` | `25000` | Positive number | Exchange rate used to convert EVN VND tariff inputs, or any explicitly VND-denominated override, into USD. The report workbook remains USD-based. |
| `tariff.tou_schedule` | `current` | `current`, `decision_963` | Time-of-use hour structure. `current` uses the current EVN peak/off-peak pattern. `decision_963` uses the Decision 963-style schedule encoded in the tariff builder. |
| `tariff.two_component_pilot_enabled` | `false` | `true`, `false` | `false` uses standard energy-only TOU tariff. `true` uses the configured two-component pilot with hourly energy rates plus monthly demand rates. |
| `tariff.evn_energy_escalation_rate` | `0.04` | Decimal fraction | Annual escalation for EVN energy tariff in the ESCO cash flow. `0.04` means 4% per year. |
| `tariff.evn_capacity_escalation_rate` | `0.04` | Decimal fraction | Annual escalation for EVN demand or capacity charges in the ESCO cash flow. `0.04` means 4% per year. |

## Financial

| Field | Example | Meaning |
| --- | ---: | --- |
| `financial.analysis_years` | `25` | REopt analysis period in years. Also used as the default project horizon for the Vietnam pro forma. |
| `financial.owner_discount_rate_fraction` | `0.1` | Generation owner or ESCO discount rate. `0.1` means 10%. Used by REopt and the Vietnam NPV calculation. |
| `financial.debt_fraction` | `0.7` | Share of total project capex funded by debt in the Vietnam ESCO cash flow. `0.7` means 70% debt and 30% equity. |
| `financial.debt_interest_rate_fraction` | `0.085` | Annual debt interest rate. `0.085` means 8.5%. |
| `financial.debt_term_years` | `10` | Debt repayment term in years. |

`financial.annual_om_usd` is intentionally omitted in the sample. When it is omitted, the Vietnam workbook uses REopt's calculated year-one O&M output. Add it only when you want to override REopt's O&M result with a single ESCO O&M value.

## PV

PV size is optimized by core REopt. The case JSON does not directly choose the final PV size unless you force it by setting `min_kw` equal to `max_kw`.

| Field | Example | Meaning |
| --- | ---: | --- |
| `technologies.pv.min_kw` | `0` | Lower bound for optimized PV size in kW. |
| `technologies.pv.max_kw` | `1000` | Upper bound for optimized PV size in kW. |
| `technologies.pv.installed_cost_per_kw` | `480` | PV installed cost in USD per kW. Used by REopt optimization economics. |
| `technologies.pv.om_cost_per_kw` | `6` | Annual PV O&M cost in USD per kW-year. Used by REopt optimization economics. |
| `technologies.pv.degradation_fraction` | `0.005` | Annual PV production degradation. `0.005` means 0.5% lower PV production each year. |
| `technologies.pv.production_factor_series` | `[0.0, …]` (length 8760) | Optional. AC kWh per kW DC installed for each hour of the year. If omitted, the case builder calls NREL PVWatts v8 with the site lat/lon and the defaults below (NREL NSRDB does not cover Vietnam, so the optimizer would otherwise time out). |
| `technologies.pv.pvwatts` | `{ "tilt": 10, "azimuth": 180, "array_type": 1, "module_type": 0, "losses": 14, "dc_ac_ratio": 1.2 }` | Optional overrides for the PVWatts v8 lookup. Any subset of the six keys above is allowed. Defaults shown are the values used when this object is omitted. The fetched series is cached in `outputs/pvwatts_cache/` keyed by lat/lon + these params, so re-runs skip the API. |

PVWatts override knobs:

| Key | Default | Allowed | Meaning |
| --- | ---: | --- | --- |
| `tilt` | `10` | 0–90 (degrees) | Module tilt from horizontal. For Vietnam (low latitude) 10°–15° is typical. |
| `azimuth` | `180` | 0–360 (degrees, 180 = due south, 0 = due north) | Module azimuth. |
| `array_type` | `1` | `0` fixed open rack, `1` fixed roof-mounted, `2` 1-axis, `3` 1-axis backtracked, `4` 2-axis | Module mounting configuration. |
| `module_type` | `0` | `0` standard, `1` premium, `2` thin film | PV module performance class. |
| `losses` | `14` | 0–99 (percent) | System loss percent (soiling, wiring, etc.). |
| `dc_ac_ratio` | `1.2` | Positive number | DC-to-AC nameplate ratio. |

Sizing examples:

- Let REopt choose PV up to 1 MW: `min_kw = 0`, `max_kw = 1000`.
- Force exactly 1 MW PV: `min_kw = 1000`, `max_kw = 1000`.
- Disable PV: `max_kw = 0`.

## Storage

Storage size is optimized by core REopt. Battery power is controlled by kW bounds, and battery energy is controlled by kWh bounds.

| Field | Example | Meaning |
| --- | ---: | --- |
| `technologies.storage.min_kw` | `0` | Lower bound for optimized battery power in kW. |
| `technologies.storage.max_kw` | `500` | Upper bound for optimized battery power in kW. |
| `technologies.storage.min_kwh` | `0` | Lower bound for optimized battery energy capacity in kWh. |
| `technologies.storage.max_kwh` | `2000` | Upper bound for optimized battery energy capacity in kWh. |
| `technologies.storage.installed_cost_per_kw` | `120` | Battery power-related installed cost in USD per kW. |
| `technologies.storage.installed_cost_per_kwh` | `180` | Battery energy-related installed cost in USD per kWh. |
| `technologies.storage.installed_cost_constant` | `0` | Fixed one-time battery installed cost in USD that does not scale with kW or kWh. Use this for controls, integration, mobilization, or interconnection if those costs are not already included in per-kW or per-kWh costs. |
| `technologies.storage.replace_cost_per_kw` | `0` | Battery power capacity replacement cost in USD/kW at `inverter_replacement_year`. |
| `technologies.storage.replace_cost_per_kwh` | `0` | Battery energy capacity replacement cost in USD/kWh at `battery_replacement_year`. |
| `technologies.storage.replace_cost_constant` | `0` | Fixed battery replacement cost in USD at `cost_constant_replacement_year`. |
| `technologies.storage.inverter_replacement_year` | `10` | Project year for battery power/inverter replacement cost. |
| `technologies.storage.battery_replacement_year` | `11` | Project year for battery energy capacity replacement cost. |
| `technologies.storage.cost_constant_replacement_year` | `10` | Project year for fixed replacement cost. |
| `technologies.storage.om_cost_fraction_of_installed_cost` | `0.02` | Core REopt annual storage O&M field. It is a fraction of total installed storage cost. Total installed storage cost includes `installed_cost_per_kw * optimized_kw`, `installed_cost_per_kwh * optimized_kwh`, and `installed_cost_constant`. `0.02` means 2% of total installed storage cost per year. |

Sizing examples:

- Let REopt choose battery up to 500 kW / 2000 kWh: `min_kw = 0`, `max_kw = 500`, `min_kwh = 0`, `max_kwh = 2000`.
- Force exactly 500 kW / 2000 kWh: set `min_kw = max_kw = 500` and `min_kwh = max_kwh = 2000`.
- Disable storage: set `max_kw = 0` and `max_kwh = 0`.

## ESCO Contract

| Field | Example | Meaning |
| --- | ---: | --- |
| `esco_contract.esco_energy_discount_fraction` | `0.9` | ESCO energy price as a fraction of EVN time-specific energy tariff. `0.9` means the ESCO charges 90% of EVN energy tariff. |
| `esco_contract.demand_savings_esco_share` | `0.8` | Share of demand-charge savings allocated to ESCO. `0.8` means ESCO keeps 80% and offtaker keeps 20%. |
| `esco_contract.grid_charging_enabled` | `false` | Base case should usually be `false`. Set `true` only for scenario analysis where battery grid charging is allowed. |

## Currency Flow

The sample is set up so all optimizer-facing money inputs are USD:

- EVN tariff rates are converted from VND to USD using `exchange_rate_vnd_per_usd`.
- PV and storage capex/O&M inputs are entered in USD.
- REopt optimizes using USD values.
- Vietnam pro forma outputs remain in USD for investor-facing review.

The Vietnam workbook is USD-based for investor-facing cash flow, NPV, capex, debt, O&M, and ESCO revenue. `exchange_rate_vnd_per_usd` is only a conversion input for VND tariffs or other fields that explicitly say `vnd`.

## Replacement And Degradation

PV degradation is supported by core REopt through `technologies.pv.degradation_fraction`. If you omit it, REopt's model default is used. The current model default is 0.5% per year.

Storage replacement is supported by core REopt through storage replacement fields, and the sample exposes those fields:

| Optional field | Meaning |
| --- | --- |
| `technologies.storage.replace_cost_per_kw` | Battery power capacity replacement cost in USD/kW at the inverter replacement year. |
| `technologies.storage.replace_cost_per_kwh` | Battery energy capacity replacement cost in USD/kWh at the battery replacement year. |
| `technologies.storage.replace_cost_constant` | Fixed replacement cost in USD. |
| `technologies.storage.inverter_replacement_year` | Project year for power-capacity replacement. |
| `technologies.storage.battery_replacement_year` | Project year for energy-capacity replacement. |
| `technologies.storage.cost_constant_replacement_year` | Project year for fixed replacement cost. |

The Vietnam pro forma currently reads REopt result costs and allows explicit capex/O&M overrides, but the first Vietnam cash-flow slice does not yet create a separate manually controlled replacement schedule unless replacement costs are passed into the cash-flow model. Use the REopt replacement fields for optimizer economics, then verify whether the generated workbook reflects the replacement timing you expect.

## Common Edits

| Goal | Edit |
| --- | --- |
| Test another customer load | Change `load_profile.path` to another 8760-row CSV. |
| Change EVN voltage level | Change `tariff.voltage_level`. |
| Compare current tariff vs Decision 963 | Run once with `tariff.tou_schedule = "current"` and once with `"decision_963"`. |
| Test two-component pilot | Set `tariff.two_component_pilot_enabled = true`. |
| Let REopt choose system sizes | Use low `min_*` values and realistic `max_*` limits. |
| Force fixed system sizes | Set each min equal to its max. |
| Change ESCO discount | Adjust `esco_contract.esco_energy_discount_fraction`. |
| Change financing | Adjust `debt_fraction`, `debt_interest_rate_fraction`, and `debt_term_years`. |
