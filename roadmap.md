# Roadmap: Vietnam Tariff + Vietnam ProForma Adaptation

## Context

REopt API is a US-centric distributed energy optimization platform. This repo is being adapted for Vietnam's DPPA/ESCO investment feasibility use case (see [vietnam_market_context.md](vietnam_market_context.md)). Two gaps block any meaningful Vietnam project work today:

1. **Tariff encoding** — EVN uses multiplier-based TOU rates (0.52×/1.0×/1.78×) indexed by voltage level, with a Sunday rule and an optional 2-component pilot. REopt's `tou_energy_rates_per_kwh` accepts 8760 absolute rates but has no Vietnam-aware builder.
2. **Pro forma** — Existing `proforma/` module is hardcoded to US tax rules (MACRS, ITC, AMT). Vietnam needs CIT holiday (4-year exempt + 9-year 50% reduced), straight-line depreciation, and VND-denominated cash flows.

**Out of scope** for this roadmap (explicitly deferred): DPPA settlement logic, loss factors, virtual DPPA eligibility, Julia optimizer Vietnam-awareness, production platform integration.

**Decisions locked in:**
- Reusable Vietnam module (balance speed with modularity).
- Tariff: Python helper that expands multiplier-based inputs into the existing 8760-hour `tou_energy_rates_per_kwh` array. **No schema change. No Julia change.**
- ProForma: parallel `proforma_vietnam/` module, mirroring `proforma/` structure. Zero risk to US path.
- Sequencing: Phase 1 Tariff → Phase 2 ProForma (linear, each phase independently shippable).
- Phase 1 output: XLSX workbook only (JSON API, PDF deferred).

---

## Phase 1 — EVN Tariff Builder (target: weeks 1–3)

**Goal:** Given `(voltage_level, tariff_category, base_rate, year, two_component_pilot_enabled)`, produce the 8760-hour `tou_energy_rates_per_kwh` array + `monthly_demand_rates` that feed directly into the existing `ElectricTariffInputs` model.

### Deliverables

1. **`reoptjl/src/vietnam/evn_tariff.py`** — EVN tariff builder
   - TOU schedule constants (peak/normal/off-peak hours, Sunday rule — no peak on Sunday)
   - Voltage-level rate table (≥110kV, 22–110kV, 6–22kV, <6kV) — data-driven, not branched
   - Multiplier application: peak=1.78×, normal=1.0×, off-peak=0.52× (current EVN defaults)
   - Optional 2-component pilot: splits output into `Cp` (capacity → `monthly_demand_rates`) + `Ca` (energy → `tou_energy_rates_per_kwh`)
   - Output: `{"tou_energy_rates_per_kwh": [8760 floats], "monthly_demand_rates": [12 floats]}`

2. **`reoptjl/src/vietnam/evn_rates.py`** (or JSON data file) — Versioned EVN rate table
   - Keyed by year (so 2025 vs. 2026 rates coexist)
   - Source: Circular 05/2024/TT-BCT or successor
   - Validated against a published EVN bill sample

3. **`reoptjl/src/vietnam/__init__.py`** — Module entry point. Exposes `build_evn_tariff(...)`.

4. **Tests** — `reoptjl/test/test_vietnam_tariff.py`
   - Unit: generated 8760 array matches hand-calculated reference for 3 sample days (weekday peak hour, weekday off-peak hour, Sunday — should have no peak).
   - Unit: monthly_demand_rates match Cp schedule when two-component pilot enabled.
   - Integration: full job submission populating `ElectricTariffInputs.tou_energy_rates_per_kwh` from builder output → optimizer returns non-error status.

5. **Example script** — `reoptjl/src/vietnam/example_submit.py` showing end-to-end: voltage + base rate → full job payload.

### Acceptance criteria

- Builder produces correct 8760 array for at least one published EVN schedule (22–110kV Normal Industrial is the default verification case).
- Sunday rule verified: Sundays contain zero peak-multiplier hours.
- A known industrial load submitted via `POST /v3/job/` using builder output returns a completed optimization; computed baseline annual electricity cost is within ±2% of a manually calculated cost using the same rate schedule.
- Rate table for at least one year (2025 or 2026) committed.

### Not in Phase 1

- New Django model fields. The builder is Python-side only — existing `ElectricTariffInputs` is untouched.
- FiT/avoided-cost export rates (handle later via `wholesale_rate`).
- Multi-year tariff escalation beyond one-year snapshots.

---

## Phase 2 — Vietnam ProForma (target: weeks 4–7)

**Goal:** Parallel `proforma_vietnam/` module that consumes REopt optimizer results and produces a Vietnam-specific XLSX investment memo suitable for ESCO offtaker/LP review.

### Deliverables

1. **`proforma_vietnam/tax_model.py`** — Vietnam tax schedule
   - CIT 20% standard rate
   - 4-year exemption (years 1–4 post-commissioning)
   - 9-year 50%-reduced rate (years 5–13) — effective 10% CIT
   - Straight-line depreciation (PV 10-year, BESS 8-year configurable defaults per [vietnam_market_context.md](vietnam_market_context.md))
   - **No MACRS, no ITC, no bonus depreciation** (those branches never execute)

2. **`proforma_vietnam/cash_flow.py`** — 25-year DCF
   - VND as base currency; optional USD parallel column
   - EVN escalation 4%/yr (default, configurable)
   - VND debt at 8.5% (default) with 70% debt fraction
   - Owner discount rate (ESCO cost of capital) vs. offtaker discount rate, both from existing `FinancialInputs`

3. **`proforma_vietnam/esco_pro_forma.py`** — ESCO/third-party-ownership view
   - Developer equity IRR (target 12–15%)
   - Offtaker savings vs. EVN-only baseline
   - DSCR schedule
   - LCOE calculation

4. **`proforma_vietnam/xlsx_builder.py`** — Multi-sheet workbook
   - **Sheets:** Summary, Cash Flow, Tax Schedule, Debt Service, Assumptions
   - Reuses existing `proforma/` XLSX helpers where trivial (openpyxl patterns only — no US tax logic)

5. **Input extensions** — Minimal, non-breaking additions:
   - If `FinancialInputs` extensions are needed, add: `vietnam_cit_holiday_years` (default 4), `vietnam_cit_reduced_rate_years` (default 9), `vietnam_cit_reduced_rate_fraction` (default 0.50).
   - Preference: keep defaults in `proforma_vietnam/tax_model.py` constants and only add model fields if a real scenario needs override. Migrations are expensive — skip until justified.

6. **API integration** — One new endpoint or query param on `GET /v3/job/<uuid>/results` that triggers Vietnam XLSX generation and returns a download URL or blob. Mirror the existing `generate_results_table` pattern.

7. **Tests** — `proforma_vietnam/tests/`
   - Unit: tax schedule produces correct year-by-year CIT for a reference project (years 1–4 = 0, years 5–13 = 10% of taxable, years 14–25 = 20%).
   - Unit: straight-line depreciation produces correct annual charge.
   - Unit: cash flow DCF matches a hand-built reference Excel pro forma within ±1% at the LCC/NPV level.
   - Integration: end-to-end — submit a Vietnam job (using Phase 1 tariff), fetch results, generate XLSX, inspect summary values.

### Acceptance criteria

- XLSX generated for at least one reference ESCO project.
- Year-by-year cash flows match hand-built reference within ±1%.
- CIT holiday + reduced rate applied correctly (verified by inspecting Tax Schedule sheet).
- Equity IRR calculation produces a value in 12–15% range for a viable project profile (sanity check).
- Zero regression in existing `proforma/` US module (verified by re-running `python manage.py test proforma`).

### Not in Phase 2

- PDF memo (deferred; XLSX only).
- JSON API response for ProForma data (deferred).
- Scenario comparison across multiple DPPA paths (deferred to Phase 3).

---

## Phase 3 — DPPA Settlement Layer (target: weeks 8–10)

**Goal:** Add a Direct Power Purchase Agreement settlement mode on top of the Phase 2 ESCO pro forma. The Phase 2 discount-to-EVN base case remains the default. DPPA is opt-in via a new `dppa.type` enum in the case JSON. v1 covers grid-connected DPPA with a bilateral CfD overlay (`grid_dppa_cfd`); pure-spot grid DPPA is reachable via `cfd_contract_volume_kwh_per_hour = 0`. Private-wire DPPA and factory-side BESS are deferred.

The Phase 2 reference workbook gate must keep passing with **zero delta** on every summary number when `dppa.type = "none"`.

### Deliverables

1. **`proforma_vietnam/dppa_settlement.py`** — new module
   - `load_fmp_series(path)` reads [DPPA DOC/fmp_cfmp_vn.json](DPPA DOC/fmp_cfmp_vn.json) (keys `_metadata`, `fmp_vnd_per_kwh`, `cfmp_vnd_per_kwh`; 8760 entries).
   - `settle_dppa_year_one(dppa_inputs, reopt_outputs, evn_tariff_inputs)` returns per-hour and per-month settlement primitives: `c_dn`, `c_dppa`, `c_cl`, `c_bl`, CfD, generator revenue, offtaker DPPA cost.
   - Applies the ND57 formulas: `Q_adj = Q_re_meter / (k × K_pp) × delta`, etc. See [proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md](proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md) Phase 3 section for full equations.

2. **`proforma_vietnam/cash_flow.py`** — wire the DPPA branch
   - Add optional `dppa_settlement=None` kwarg to `calculate_vietnam_esco_cash_flow`. When `None`, code path is byte-identical to Phase 2.
   - When provided, zero out `base_energy_revenue_vnd` and replace `offtaker_post_project_cost_vnd` with the DPPA identity. Adds new annual output keys: `c_dn_vnd`, `c_dppa_vnd`, `c_cl_vnd`, `c_bl_vnd`, `cfd_net_vnd`, `generator_revenue_vnd`.

3. **`proforma_vietnam/case_builder.py`** — case JSON parsing
   - New `_dppa_inputs(case_config, voltage_level)` that validates the `dppa.type` enum, enforces voltage eligibility for `grid_dppa_cfd` (≥22kV per ND57 Art. 16), derives `K_pp` from voltage if not supplied, and loads the FMP series.
   - When `dppa.type != "none"`, force `ElectricStorage.can_grid_charge = False` (co-located BESS only). Raise a validation error if the case JSON explicitly sets `can_grid_charge = True` alongside DPPA.

4. **`proforma_vietnam/esco_pro_forma.py`** — orchestrator update
   - When `dppa.type != "none"`, call `settle_dppa_year_one(...)` and pass the result as `dppa_settlement` into `calculate_vietnam_esco_cash_flow`.
   - Extract `pv_to_grid` and `grid_to_load` series alongside the existing extractions.

5. **`proforma_vietnam/xlsx_builder.py`** — workbook extension
   - 4 new sheets, rendered only when `dppa.type != "none"`: DPPA Configuration, Hourly Settlement (8760 rows), Monthly Settlement (12 rows), DPPA Annual Summary.
   - Cash Flow sheet gets 3 right-edge columns (`generator_revenue_usd`, `cfd_net_usd`, `dppa_offtaker_cost_usd`). They render as zero on the `none` path so existing column readers are not disturbed.

6. **`proforma_vietnam/reference_workbook_comparison.py`** — sibling helper
   - Phase 2 `compare_reference_workbook(...)` is untouched.
   - New `compare_dppa_reference_workbook(...)` validates the `grid_dppa_cfd` fixture against the implementation at 1% tolerance.

7. **`reoptjl/views.py`** + **`proforma_vietnam/run_case.py`** — query-param plumbing
   - Add a single JSON-encoded `dppa_config` GET parameter (URL-encoded) to the Vietnam proforma override pipeline. One param instead of ten; accommodates the 8760 FMP series.
   - Extend `VIETNAM_REPORT_QUERY_KEYS` in [run_case.py](proforma_vietnam/run_case.py) accordingly.

8. **Tests** — `proforma_vietnam/tests/`
   - `test_reference_workbook_unchanged.py` — asserts zero delta on the Phase 2 gate after the merge.
   - `test_dppa_settlement_grid_cfd.py::test_known_day` — hand-computed 24-hour fixture; asserts ±1% on every line item and the year-one summary.
   - `test_case_builder_dppa_validation.py` — enforces voltage eligibility, `can_grid_charge` forced off, FMP series load.

### Acceptance criteria

- Phase 2 reference gate passes with zero delta (`tests/test_reference_workbook_unchanged.py`).
- Hand-computed `grid_dppa_cfd` fixture matches within 1% on `C_DN`, `C_DPPA`, `C_CL`, `C_BL`, CfD, generator revenue, and offtaker total cost.
- Case builder raises a validation error if `dppa.type = "grid_dppa_cfd"` is set at a voltage level outside `{"110kv_and_above", "22_to_110kv"}`.
- Case builder raises a validation error if `dppa.type != "none"` is set alongside `ElectricStorage.can_grid_charge = True`.
- An end-to-end run via [run_case.py](proforma_vietnam/run_case.py) on a `case_5` clone of `case_2` with `dppa.type = "grid_dppa_cfd"` produces a workbook with the 4 new sheets populated.

### Not in Phase 3

- Private-wire DPPA (Điều 25).
- Factory-side BESS configuration (offtaker-owned, grid-chargeable).
- REopt optimizer alignment with FMP (`tou_energy_rates_per_kwh = FMP × K_pp`). Optimizer continues to size against EVN-retail tariff.
- Spot-price stochastics, REC accounting, congestion pricing, multi-generator portfolios, multi-buyer `delta < 1`.
- MOIT annual re-set of `f_dppa` and `f_cl` (held constant in real terms, escalating at `evn_energy_escalation_rate`).
- `K_pp` re-calibration over project life.
- Django ORM persistence of DPPA params.
- Julia changes.

---

## Critical Files

**New:**
- `reoptjl/src/vietnam/__init__.py`
- `reoptjl/src/vietnam/evn_tariff.py`
- `reoptjl/src/vietnam/evn_rates.py` (or `.json`)
- `reoptjl/src/vietnam/example_submit.py`
- `reoptjl/test/test_vietnam_tariff.py`
- `proforma_vietnam/__init__.py`
- `proforma_vietnam/tax_model.py`
- `proforma_vietnam/cash_flow.py`
- `proforma_vietnam/esco_pro_forma.py`
- `proforma_vietnam/xlsx_builder.py`
- `proforma_vietnam/tests/test_tax_model.py`
- `proforma_vietnam/tests/test_cash_flow.py`
- `proforma_vietnam/tests/test_end_to_end.py`

**Modified (only if Phase 2 requires):**
- [reoptjl/models.py](reoptjl/models.py) — optional `FinancialInputs` additions for CIT override
- `reoptjl/views.py` or `reoptjl/api.py` — new endpoint for Vietnam XLSX generation
- `reoptjl/urls.py` — route for new endpoint

**Untouched:**
- `julia_src/*` — zero changes. Tariff is pre-processed in Python; pro forma is post-processing.
- `proforma/*` — zero changes. US path preserved.
- `reo/*` — deprecated, don't touch.

---

## Existing Code to Reuse

- **`ElectricTariffInputs.tou_energy_rates_per_kwh`** ([reoptjl/models.py](reoptjl/models.py)) — accepts the 8760 array from the builder directly.
- **`ElectricTariffInputs.monthly_demand_rates`** ([reoptjl/models.py](reoptjl/models.py)) — accepts Cp capacity charges when 2-component pilot is enabled.
- **`FinancialInputs.third_party_ownership`** ([reoptjl/models.py](reoptjl/models.py)) — already toggles ESCO model.
- **`FinancialInputs.owner_discount_rate_fraction` / `offtaker_discount_rate_fraction`** — already supports dual-party DCF.
- **`proforma/` XLSX helpers** — openpyxl patterns can be imported into `proforma_vietnam/xlsx_builder.py` where purely presentational.
- **`reoptjl/src/process_results.py`** — read-only consumer of optimizer output; the pro forma module plugs in after this step.

---

## Verification Plan

### Phase 1 end-to-end
```bash
# Unit + integration tests for the tariff builder
python manage.py test reoptjl.test.test_vietnam_tariff

# Manual sanity check: submit a job with Vietnam tariff and inspect the rate array
python reoptjl/src/vietnam/example_submit.py
```

### Phase 2 end-to-end
```bash
# Unit tests for each ProForma module
python manage.py test proforma_vietnam

# Regression: ensure US pro forma still passes
python manage.py test proforma

# Full stack: submit Vietnam job via docker-compose, generate XLSX
docker-compose up -d
# Then POST /v3/job/ with Vietnam tariff payload, GET results, trigger XLSX export
```

### Acceptance gate (before declaring Phase 2 complete)
- One reference ESCO project (to be defined during Phase 2) produces an XLSX that matches a hand-built Excel pro forma within ±1% at the LCC/NPV/IRR level.
- All new tests pass; existing `proforma/` tests unchanged and passing.

---

## Deferred (Phase 4+)

- Private-wire DPPA (Điều 25)
- Factory-side BESS (offtaker-owned, grid-chargeable)
- Julia optimizer Vietnam-awareness (FMP / DPPA settlement inside the MILP)
- JSON API response for ProForma data
- PDF investment memo generation
- Production platform integration (country = Vietnam as a first-class market)

These are intentionally held back until Phase 3 is shipped and validated against at least one real customer project.
