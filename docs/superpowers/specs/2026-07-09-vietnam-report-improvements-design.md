# Vietnam Report Improvements — Design

Date: 2026-07-09
Scope: `proforma_vietnam/` Excel report (Vietnam ESCO/DPPA workbook) + the two
report-generation paths (`reoptjl/views.py` server endpoint and
`proforma_vietnam/rebuild_report.py` offline rebuild).

## Motivation

Review of the Vietnam case surfaced three report improvements:

1. Remove the em dash `—` from the entire Excel report (use `-` instead).
2. Dispatch Profile column C should show real PVWatts **POA irradiance (W/m²)**
   instead of the PV production factor (kWh/kW). Add the annual POA irradiation
   total and the annual Performance Ratio to the Technical Results sheet.
3. Show battery-charging flows as **negative** values on the Dispatch sheet and
   add a PV-to-Storage line to the peak-week chart (the dip below zero makes the
   chart easier to read).

## Current architecture (relevant facts)

- Both report paths call `build_vietnam_report_data(reopt_results, cash_flow_result)`
  then `build_vietnam_esco_workbook(...)`.
  - **Server** (`run_case.py` → `/job/<uuid>/results?vietnam_proforma=true`):
    `reopt_results` carries the echoed PV input `production_factor_series` and
    the site lat/lon. `run_case._download_vietnam_report` already forwards a
    whitelist of assumption keys as query params and POSTs `dppa_config`
    (8760-length lists) in the request body.
  - **Offline** (`rebuild_report.py`): reads `results.json`, `assumptions.json`,
    `case.json`; `build_vietnam_report_data` is a pure post-processor (no network).
- `pvwatts_client.fetch_production_factor_series` fetches the PVWatts v8 hourly
  response and extracts only `ac` (→ AC kW per kW DC). The same response also
  contains `poa` (plane-of-array irradiance, W/m²).
- `case_builder._pv_inputs` calls `fetch_production_factor_series` and stores the
  result as `payload["PV"]["production_factor_series"]` (a valid REopt key, so it
  round-trips through REopt's input echo). POA is **not** a valid REopt key, so it
  cannot ride the input echo — it must be threaded explicitly.
- Dispatch table/columns/chart live in `xlsx_builder.py`
  (`DISPATCH_COLUMNS`, `DISPATCH_CHART_SERIES`, `_write_dispatch_sheet`).
  `annual_production` totals are computed in `report_data.py` from the raw
  positive series, independently of the per-hour dispatch rows.

## Design

### 1. Remove em dash from the report

Add a central sanitizer at the end of `build_vietnam_esco_workbook` that walks
every worksheet cell and replaces `"—"` with `"-"` in string values. This is DRY
and guaranteed regardless of which schema label / note / audit string produced
the dash. Scope is limited to `"—"` only — `"→"`, `"m²"`, `"°C"`, `"–"` are left
untouched (user confirmed: only the em dash).

Chart titles are not cells. The only chart title containing an em dash is the
Dispatch peak-week title (`f"Dispatch — Peak-Load Week ..."`); fix that f-string
at source to use `-`.

Verification: a test builds a representative workbook and asserts no cell value
contains `"—"`.

### 2. POA irradiance column + Performance Ratio

**`pvwatts_client.py`**
- Extract `poa` alongside `ac` from the PVWatts response.
- New function `fetch_pv_series(latitude, longitude, overrides, api_key)` returns
  `{"production_factor": [...8760...], "poa_wm2": [...8760...]}` and caches both
  (cache payload becomes a dict; bump/replace the cached format).
- `fetch_production_factor_series` becomes a thin wrapper returning the
  `production_factor` list, so `case_builder` / the REopt payload are unchanged.
- POA is the raw plane-of-array irradiance in W/m² (rounded), depending on
  tilt/azimuth/array_type — the same params already used for the AC fetch.

**Threading POA to the report builder** (mirrors the `dppa_config` pattern)
- `case_builder._pv_inputs` fetches both series; PF goes into the payload as
  today, POA is stored on the returned case for the report. Store it in
  `vietnam_case["assumptions"]["pv_poa_irradiance_series"]` (a report-only field;
  it is written to `assumptions.json`).
- **Offline path**: `rebuild_report` passes `assumptions["pv_poa_irradiance_series"]`
  into `build_vietnam_report_data`.
- **Server path**: `run_case._download_vietnam_report` sends the POA series in the
  POST body (same mechanism as `dppa_config`, which already carries 8760-lists).
  `reoptjl/views.py` reads it and passes it into `build_vietnam_report_data`.
- `build_vietnam_report_data` gains a `poa_irradiance_series=None` parameter.
  When absent (endpoint hit without the param), the irradiance column is blank
  and Performance Ratio is omitted — graceful degradation.

**Dispatch column C**
- `DISPATCH_COLUMNS[2]` changes from
  `("PV Production Factor (kWh/kW) — irradiation proxy", "pv_production_factor")`
  to `("PV Irradiation (W/m²)", "pv_irradiance")`.
- `report_data._dispatch_rows` emits `pv_irradiance` (from the POA series). The
  production-factor series is still computed internally (needed for PR) but no
  longer shown as a dispatch column.
- Number format for the irradiance column: `"#,##0"` (W/m²).

**Technical Results — new "Solar Resource (Year 1)" section**
- `Annual POA Irradiation (kWh/m²)` = Σ(POA_wm2 / 1000) over 8760 h.
- `Performance Ratio (Year 1)` = Σ(production_factor) ÷ Σ(POA_wm2 / 1000),
  IEC 61724 definition (final yield ÷ reference yield), formatted as a percent.
  Includes the PVWatts 14% system losses, so a realistic value is ~0.75–0.82.
- Both come from `report_data` (new `solar_resource` block). If POA is absent the
  section is skipped.

### 3. Negative charging flows + PV-to-Storage chart line

- In `_write_dispatch_sheet`, write the `pv_to_storage_kw` and `grid_to_storage_kw`
  cell values negated (`-value`). This is purely presentational at the Excel-write
  layer — `report_data`, `annual_production`, and every downstream formula keep
  the original positive values, so structure/formulas are unaffected.
- Add `("PV to Storage (kW)", 6)` to `DISPATCH_CHART_SERIES` so the peak-week
  LineChart shows the (now negative) PV-to-Storage line dipping below zero.
  Grid to Storage is also negative in the table but not added to the chart (it is
  typically 0 under DPPA where grid charging is disabled).

## Testing

- `test_pvwatts_client`: `fetch_pv_series` returns both series from a stubbed
  response; `fetch_production_factor_series` wrapper still returns the PF list;
  cache round-trips both.
- `test_report_data`: irradiance appears in dispatch rows; `solar_resource`
  block carries annual POA and PR; PR math matches the formula; POA-absent case
  degrades (no PR, blank irradiance).
- `test_xlsx_builder`: Dispatch header is `PV Irradiation (W/m²)`; charging cells
  are negative; chart includes the PV-to-Storage series; Technical Results shows
  the Solar Resource section; **no cell contains `"—"`**.
- `test_case_builder`: POA series stashed into assumptions when PVWatts is
  fetched; skipped when a PV series is user-provided (mirrors existing PF test).
- `test_run_case` / endpoint test: POA forwarded in the report request body and
  reaches the report builder.

## Out of scope

- Per-project-year (degraded) PR — Technical Results is a Year-1 snapshot; a
  single annual PR value is used (user confirmed).
- Changing the `→` arrows or other non-em-dash glyphs.
- Re-fetching POA server-side from lat/lon (rejected: report builder stays a pure
  function; avoids a network/API-key dependency in the results endpoint).
