# Thailand case.json input guide

This documents every key `build_thailand_case()` (`proforma_thailand/case_builder.py`)
reads from a Rofu Thailand `case.json`. For each key: what it does, and, if you
omit it, whether it falls back to a **Thailand** default (something researched
and cited for this site) or a **REopt US default** (a value baked into the
solver for a US project, which has no business being applied to a Thai one
unless we explicitly zero or override it). That distinction is the one that
has actually caused a defect on this project before: an unzeroed US 30 percent
investment tax credit plus 5-year MACRS once shrank a modelled battery by a
factor of five, because omitting a key silently pulled in the wrong country's
assumption. Getting this table right is the whole point of the guide.

Thailand defaults live in `proforma_thailand/defaults/thailand_defaults.json`
and `proforma_thailand/defaults/pea_tariff_rates.json`. Anything sourced from
there and still marked `"PLACEHOLDER - pending Keen confirmation"` in that file
renders on the workbook's Assumptions sheet with a visible marker; it is a
researched estimate, not an invented number, but it still needs Keen or Ou to
confirm it.

## `case_name` (optional)

Free text, carried through to `assumptions["case_name"]` for the workbook
title. Omitted: falls back to `"{country} {case_label}"` from the Thailand
country profile, e.g. `"Thailand Direct-ownership rooftop solar case"`.

## `site` block

| Key | Required | Omitted takes |
|---|---|---|
| `latitude`, `longitude` | Yes | No default of any kind. `case_builder.py` reads `site["latitude"]` directly; a missing key raises `KeyError` before anything is sent to REopt. |
| `tilt` | No | **Thailand default**: 15 degrees (`site.pv_tilt_degrees` in `thailand_defaults.json`, itself marked `PLACEHOLDER - pending Keen confirmation`). This is a Thailand-specific override of `proforma_vietnam/pvwatts_client.py`'s own hardcoded PVWatts default of 10 degrees, which was tuned for the Vietnam site and has no bearing on Rofu's roof. 15 degrees approximates both the 15.21N site latitude and a typical industrial metal roof pitch; the actual roof pitch is not in the RTS Data Collection sheet and is an open information request to Ou. |

Latitude and longitude also feed the PVWatts production-factor fetch
(`proforma_vietnam/pvwatts_client.py`), which caches its response to disk
under `outputs/pvwatts_cache/` keyed on lat/lon/tilt, so re-running a case at
the same site and tilt does not re-hit the NREL API.

## `load_profile` block

| Key | Required | Omitted takes |
|---|---|---|
| `path` | Yes | No default. Path to the committed 15-minute load CSV (`proforma_thailand/data/rofu_load_15min.csv`), a bare `load_kw` column of 35,040 rows with no timestamps. |
| `all_off_peak_dates_path` | Yes | No default. Path to the JSON list of public-holiday dates PEA bills at the off-peak rate; weekends are handled automatically and do not need to be listed. |
| `calendar_year_months` | Yes | No default, and it is **validated, not trusted**. |

**`calendar_year_months` and the manifest guard.** The load CSV carries no
timestamps, so nothing in the file itself proves which twelve months it holds
or in what order. `build_thailand_case` checks the declared
`calendar_year_months` against `proforma_thailand/data/load_manifest.json`
(the manifest `proforma_thailand/tools/build_load_inputs.py` writes alongside
the CSV) and raises `ValueError` on any mismatch. Reordering two months here
would otherwise silently bill the load under the wrong tariff month with no
error. Every case in this directory must declare the same order the manifest
records:

```
[[2026,1],[2026,2],[2026,3],[2026,4],[2026,5],[2026,6],
 [2025,7],[2025,8],[2025,9],[2025,10],[2025,11],[2025,12]]
```

If the guard fires, the `case.json` is wrong; do not edit the guard to make it
pass.

## `tariff` block

| Key | Required | Omitted takes |
|---|---|---|
| `voltage_level` | No | **Thailand default**: `"22_33kv"`, PEA Schedule 4.2 Large General Service TOU at 22-33 kV, matching Rofu's actual connection. It is also currently the only voltage level configured in `pea_tariff_rates.json`. |
| `exchange_rate_thb_per_usd` | No | **Thailand default**: 32.5 (`financial.exchange_rate_thb_per_usd`), a planning rate to be revised at contract. Every cost in `technologies` is USD; this rate is what converts the THB-denominated PEA tariff into the USD payload REopt expects. |

## `technologies.pv` block

| Key | Required | Omitted takes |
|---|---|---|
| `max_kw` | No, but see caveat below | **Thailand default**: 1,685.0 kW (`site.pv_max_kw`), the conservative roof cap from the derivation table below. |
| `installed_cost_per_kw` | No, and **must not be set on any committed case** | **Thailand default**: 750.0 USD/kWp (`financial.pv_installed_cost_per_kw`, cited to Krungsri Research). |
| `om_cost_per_kw` | No | **Thailand default**: 7.5 USD/kWp/yr (`financial.annual_om_per_kw`). |

**On `max_kw` and omission.** Leaving the `pv` object out of `technologies`
entirely, or including it as `{}`, does **not** mean "no PV": it takes the
1,685 kW Thailand default. Only an explicit `"max_kw": 0` removes PV, and it
removes the whole `PV` key from the payload rather than sending a zero (a
resampling bug in `validators.py` only rescales the PVWatts production series
when `max_kw > 0`, so a zero-PV case with `PV` still present would ship an
unresampled 8760-length series into a 35,040-row model and the solver would
fail with a dimension mismatch).

**Why `installed_cost_per_kw` is never set per case here.** Leaving it out on
every one of the six committed cases means all six price PV off the same
researched Thailand default. Setting it explicitly in some cases and not
others is how a sweep across roof-area caps would silently stop being an
apples-to-apples comparison; a later re-benchmark of the Thailand default
would then apply to only some of the six cases.

**Not exposed as `case.json` keys at all, hardcoded in `case_builder.py`:**

- `federal_itc_fraction: 0.0`, `macrs_option_years: 0`, `macrs_bonus_fraction: 0.0`.
  REopt.jl's own defaults are a 30 percent US federal investment tax credit and
  5-year MACRS with 100 percent bonus depreciation, ON by default. Neither
  incentive exists in Thailand, and neither is inert: both cut the capital cost
  the optimizer sizes against, so a case that let either default through would
  size and price PV incorrectly. There is no `case.json` key that can turn
  these back on for a Thailand case; they are always zero.
- `can_net_meter: False`, `can_wholesale: False`, `can_export_beyond_nem_limit: False`,
  `can_curtail: True`. PEA pays nothing for exported energy, so every Thailand
  case curtails rather than exports; this is not case-configurable.

## `technologies.storage` block

Storage is only declared in the payload at all when `max_kw` or `max_kwh` is
truthy; otherwise the `ElectricStorage` key is omitted from the payload
entirely (REopt US default: no storage).

| Key | Required | Omitted takes |
|---|---|---|
| `max_kw`, `max_kwh` | No (default: no storage) | See above. When either is set, both should be, sized to the case's intent (see caveat below for case_5/case_6). |
| `installed_cost_per_kw` | No | **Thailand default**: 300.0 USD/kW (`financial.bess_installed_cost_per_kw`, still `PLACEHOLDER - pending Keen confirmation`). |
| `installed_cost_per_kwh` | No | **Thailand default**: 250.0 USD/kWh (`financial.bess_installed_cost_per_kwh`, `PLACEHOLDER`). |
| `installed_cost_constant` | No | Hardcoded to 0.0 whenever omitted, **not** a `thailand_defaults.json` entry. REopt.jl's own default for this field is a **fixed** USD 222,115 upfront battery cost regardless of size, a US commercial-scale figure that would badly overstate a Thai case if it leaked through. `case_builder.py` always overrides it to 0.0 unless the case sets it explicitly. |
| `replace_cost_per_kw` | No | **Thailand default**: 150.0 USD/kW (`financial.bess_replace_cost_per_kw`, `PLACEHOLDER`), a year-10 replacement at half the original per-kW cost. REopt schedules `battery_replacement_year` at 10 but defaults every replace-cost field to 0.0, which models a free replacement and overstates a 25-year case; this default exists specifically to prevent that. |
| `replace_cost_per_kwh` | No | **Thailand default**: 125.0 USD/kWh (`financial.bess_replace_cost_per_kwh`, `PLACEHOLDER`), same year-10 logic. |
| `min_duration_hours` | No | **Thailand default**: 1.5 hours (`financial.bess_min_duration_hours`, `PLACEHOLDER`). REopt.jl's own default is 0.0, which permits a physically meaningless zero-duration battery. |
| `om_cost_fraction_of_installed_cost` | No | **Thailand default**: 0.01, i.e. 1 percent of installed cost per year (`financial.bess_om_fraction_of_installed_cost`, `PLACEHOLDER`). REopt.jl's own default is 0.025 (2.5 percent), a US figure. |
| `can_grid_charge` | No | Defaults to `True` in `case_builder.py` (a Thailand-side explicit choice, not a `thailand_defaults.json` entry). |

**Not exposed as `case.json` keys, hardcoded:** `total_itc_fraction: 0.0`,
`macrs_option_years: 0`, `macrs_bonus_fraction: 0.0`. Same US-incentive
reasoning as PV above.

**The `max_kw` / `max_kwh` bound in case_5 and case_6 is not a forced size.**
Both storage cases declare `"max_kw": 2000, "max_kwh": 8000`, an upper bound
the optimizer sizes freely beneath, not a target the model is trying to hit.
It is set generously so the bound does not bind. If a completed run ever
returns storage at exactly 2,000 kW or exactly 8,000 kWh, the bound decided
the answer instead of the economics; the case must be re-run with the bound
raised, not reported as-is.

## `direct_ownership` block

| Key | Required | Omitted takes |
|---|---|---|
| `enabled` | No | Defaults to `true` (`{"enabled": True}`) when the whole block is omitted. Thailand only supports the direct-ownership structure today; ESCO and PPA are out of scope for this case tree (see `proforma_thailand/case_builder.py` module docstring). |
| `assume_profitable_host`, `cit_regime` | No | Advanced overrides inherited from the shared `proforma_vietnam` cash-flow engine, rarely needed here; omitted, the engine assumes a profitable host and the standard flat CIT regime, both of which already match Thailand's 20 percent standard corporate rate. |

## Roof-area derivation (the four PV caps)

Source: RTS Data Collection_KTH_followup_Dec2025, Facility Data sheet. Rooftop
size is recorded as "24*108 m / 30*108 m (each building differs)"; Keen's
December follow-up answer is "5 large rooftops of similar size (plus several
smaller)".

Gross area = 5 roofs x 108 m x width. Usable fraction 0.65, the midpoint of the
60-70 percent planning band for industrial metal roofs after deducting
perimeter setbacks, maintenance walkways, roof penetrations and cable
routing. The "several smaller" roofs are excluded entirely. Power density
0.20 kW/m2, the installed density of a 21-22 percent efficient module on a
pitched roof after row spacing.

| Width | Gross m2 | Usable m2 | kWp DC | Case |
|---|---|---|---|---|
| 24 m | 12,960 | 8,424 | 1,685 | case_1, case_5 |
| 27 m | 14,580 | 9,477 | 1,895 | case_2 |
| 30 m | 16,200 | 10,530 | 2,106 | case_3 |
| n/a (transformer nameplate) | - | - | 3,230 | case_4, case_6 |

The 1,685 kW figure is the conservative bottom of this band, not an arbitrary
stub. Ou confirming the actual roof widths is worth up to +25 percent of
system size.

Case 4 and case_6's 3,230 kW cap is the transformer nameplate rating
(500 + 500 + 1,600 + 630 kVA), used here purely as a generous upper bound with
no physical roof-area meaning; behind-the-meter PV with zero export is not
actually transformer-import-limited. It is deliberately labelled
"roof-unconstrained" rather than "what the transformer permits": it answers
where more PV stops paying, not a transformer-sizing question.

## The six committed cases

| Case | PV cap kW | Storage bound | Question answered |
|---|---|---|---|
| case_1 | 1,685 | none | RTS base, conservative roof |
| case_2 | 1,895 | none | Mid roof width |
| case_3 | 2,106 | none | Upper roof width |
| case_4 | 3,230 | none | Where does more PV stop paying |
| case_5 | 1,685 | optimizer-sized (bound 2,000 kW / 8,000 kWh) | Does a battery pay at the conservative roof |
| case_6 | 3,230 | optimizer-sized (bound 2,000 kW / 8,000 kWh) | Does a battery pay when PV is not roof-limited |

Every case above omits `installed_cost_per_kw` so all six price PV off the
same Thailand default, and every case's payload must show
`federal_itc_fraction: 0.0` and `macrs_option_years: 0` for PV, and the
equivalent `total_itc_fraction: 0.0` / `macrs_option_years: 0` for storage in
case_5 and case_6. Confirm with:

```bash
./.venv/Scripts/python.exe -c "
import json
from pathlib import Path
root = Path('outputs/thailand_case/rofu_thailand')
for name in ['case_%d' % i for i in range(1, 7)]:
    payload = json.loads((root / name / 'payload.json').read_text(encoding='utf-8'))
    pv = payload.get('PV', {})
    storage = payload.get('ElectricStorage', {})
    print('%-8s PV max %-8s ITC %-5s MACRS %-3s | storage max_kw %s' % (
        name, pv.get('max_kw'), pv.get('federal_itc_fraction'),
        pv.get('macrs_option_years'), storage.get('max_kw', '-')))
"
```

A non-zero incentive on any row means stop and fix `case_builder.py` before
running anything against the live solver; it is not a value to patch per case.
