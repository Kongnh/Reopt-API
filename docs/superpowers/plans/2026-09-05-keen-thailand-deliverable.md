# Keen Thailand Deliverable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the Thailand adaptation backlog, then build and run a six-case tree for the Rofu (Thailand) factory and write a client memo for Keen.

**Architecture:** `proforma_vietnam` is the shared core and `proforma_thailand` drives it with `THAILAND_PROFILE`. Every core change in this plan is an additive keyword argument or a `CountryProfile` field defaulting to today's behaviour, so Vietnam's generated workbook is unchanged by construction and an 8-case cell-level gate proves it. Thailand-specific economics (insurance, inverter replacement, Scope 2) are computed in `proforma_thailand/report.py` and passed into the engine through existing keyword arguments.

**Tech Stack:** Python 3, Django (V3 REopt API, container only), openpyxl, unittest, REopt.jl via HTTP, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-05-keen-thailand-deliverable-design.md`

## Global Constraints

- Never modify anything under `reo/`. It is deprecated V1/V2 and returns 410.
- Never modify `outputs/vietnam_case/` or `baseline_workbooks/`.
- Vietnam's generated Excel output must not change.
- No em dash in any generated report output.
- Run Python with `./.venv/Scripts/python.exe`. It has **no Django**. Anything importing Django runs inside the `reopt_api-django-1` container.
- Never modify the client source `.xlsm` under the Keen Project folder.
- `proforma_vietnam` IS the shared core. No rename, no `proforma_core` package. Vietnam-suffixed names carrying Thailand values is by design.
- Thailand money keys keep the historical `_vnd` suffix and carry THB. Only rendered labels change.
- Placeholder marker string: `PLACEHOLDER - pending Keen confirmation`.

**The Vietnam regression gate.** Tasks that touch `proforma_vietnam` must run this and see `TOTAL DIFFS 0`:

```bash
./.venv/Scripts/python.exe -c "
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases, compare_workbooks
built = rebuild_all_cases('.', 'gate_check')
bad = 0
for name, path in built.items():
    diffs = compare_workbooks('baseline_workbooks/%s/%s' % (name, path.name), path)
    print(name, 'OK' if not diffs else diffs[:3])
    bad += len(diffs)
print('TOTAL DIFFS', bad)
raise SystemExit(1 if bad else 0)
"
```

Delete the scratch `gate_check/` directory afterwards. Never commit it.

**The test suites.** Tasks must leave all three green:

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
docker exec reopt_api-django-1 python manage.py test reoptjl.test.test_thailand_tariff -v 2
```

---

## File Structure

**Created:**
- `proforma_thailand/tools/__init__.py` - package marker
- `proforma_thailand/tools/build_load_inputs.py` - regenerates the load CSV, holiday JSON and manifest from the source workbook
- `proforma_thailand/data/load_manifest.json` - month order, row counts and source hash for the committed load CSV
- `proforma_thailand/emissions.py` - Scope 2 avoided-emissions calculation
- `proforma_thailand/tests/test_emissions.py` - tests for the above
- `proforma_thailand/tests/test_build_load_inputs.py` - tests for the regeneration script
- `outputs/thailand_case/rofu_thailand/CASE_JSON_INPUT_GUIDE.md` - input reference
- `outputs/thailand_case/rofu_thailand/case_{1..6}/case.json` - the six cases
- `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md` - the client deliverable

**Modified:**
- `proforma_vietnam/cash_flow.py` - `bess_depreciation_years` kwarg
- `proforma_vietnam/esco_pro_forma.py` - `extra_replacement_costs_by_year` additive merge
- `proforma_vietnam/country_profile.py` - dispatch row label, ESCO-terms flag, returns-section label
- `proforma_vietnam/xlsx_builder.py` - honour the three new profile fields
- `proforma_vietnam/audit_sheets.py` - list-valued rows, FX format, Scope 2 rows
- `proforma_vietnam/report_data.py` - POA irradiance up-sampling
- `proforma_vietnam/tools/compare_workbooks.py` - narrow the ignore rules
- `proforma_thailand/report.py` - insurance, inverter replacement, depreciation passthrough, billed demand, Scope 2
- `proforma_thailand/case_builder.py` - storage duration, storage O&M, PV tilt, month-order validation
- `proforma_thailand/run_case.py` - hard-fail placeholder validation
- `proforma_thailand/defaults/thailand_defaults.json` - re-benchmarked costs, grid emission factor
- `proforma_thailand/load_profile.py` - manifest emission

---

### Task 1: The BESS depreciation life and the CIT rate become keyword arguments

Two tax parameters are module globals the caller cannot reach. `BESS_DEPRECIATION_YEARS` is read at six sites, so the Thailand workbook prints Vietnam's 8 years and cites Circular 45/2013/TT-BTC as the authority for Thai tax. `CIT_STANDARD_RATE` is never passed to `calculate_cit`, so Thailand's `cit_standard_rate` assumption is produced and then ignored; both countries are at 0.20 today, so this is latent rather than active, but it is a silent trap the moment either rate moves.

Both follow the pattern of the existing `pv_depreciation_years` kwarg. They share one file and one expensive gate run, which is why they are one task.

**Files:**
- Modify: `proforma_vietnam/cash_flow.py`
- Test: `proforma_vietnam/tests/test_cash_flow.py`

**Interfaces:**
- Produces: `calculate_vietnam_esco_cash_flow(..., bess_depreciation_years=None, cit_standard_rate=None)`. Each resolves to its module constant when `None`, so every existing caller is unaffected. The derivation dict reports the resolved values under `bess_depreciation_years` and `cit.standard_rate`.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_cash_flow.py`:

```python
class BessDepreciationYearsTests(unittest.TestCase):
    """The BESS life must be injectable, the way the PV life already is."""

    def _kwargs(self, **overrides):
        base = dict(
            project_served_pv_kwh=1_000_000.0,
            evn_energy_rates_vnd_per_kwh=0.1,
            bau_evn_bill_vnd=200_000.0,
            optimized_evn_bill_vnd=150_000.0,
            bau_demand_charge_vnd=60_000.0,
            optimized_demand_charge_vnd=50_000.0,
            pv_capex_vnd=1_000_000.0,
            bess_capex_vnd=400_000.0,
            annual_om_vnd=12_000.0,
            esco_energy_discount_fraction=0.0,
            project_years=25,
        )
        base.update(overrides)
        return base

    def test_defaults_to_the_module_constant(self):
        result = calculate_vietnam_esco_cash_flow(**self._kwargs())
        self.assertEqual(
            result["derivation"]["bess_depreciation_years"],
            BESS_DEPRECIATION_YEARS,
        )

    def test_explicit_life_is_reported(self):
        result = calculate_vietnam_esco_cash_flow(
            **self._kwargs(bess_depreciation_years=5)
        )
        self.assertEqual(result["derivation"]["bess_depreciation_years"], 5)

    def test_shorter_life_front_loads_the_depreciation_shield(self):
        """A 5-year life must charge more per year than an 8-year life."""
        five = calculate_vietnam_esco_cash_flow(
            **self._kwargs(bess_depreciation_years=5)
        )
        eight = calculate_vietnam_esco_cash_flow(
            **self._kwargs(bess_depreciation_years=8)
        )
        self.assertGreater(
            five["annual_rows"][0]["depreciation_vnd"],
            eight["annual_rows"][0]["depreciation_vnd"],
        )


class CitStandardRateTests(unittest.TestCase):
    """The CIT rate must be injectable, not read from a Vietnam module global."""

    def _kwargs(self, **overrides):
        base = dict(
            project_served_pv_kwh=1_000_000.0,
            evn_energy_rates_vnd_per_kwh=0.1,
            bau_evn_bill_vnd=200_000.0,
            optimized_evn_bill_vnd=150_000.0,
            bau_demand_charge_vnd=60_000.0,
            optimized_demand_charge_vnd=50_000.0,
            pv_capex_vnd=1_000_000.0,
            bess_capex_vnd=400_000.0,
            annual_om_vnd=12_000.0,
            esco_energy_discount_fraction=0.0,
            project_years=25,
        )
        base.update(overrides)
        return base

    def test_defaults_to_the_module_constant(self):
        result = calculate_vietnam_esco_cash_flow(**self._kwargs())
        self.assertAlmostEqual(
            result["derivation"]["cit"]["standard_rate"], CIT_STANDARD_RATE
        )

    def test_explicit_rate_is_reported(self):
        result = calculate_vietnam_esco_cash_flow(
            **self._kwargs(cit_standard_rate=0.17)
        )
        self.assertAlmostEqual(result["derivation"]["cit"]["standard_rate"], 0.17)

    def test_a_higher_rate_takes_more_tax(self):
        low = calculate_vietnam_esco_cash_flow(
            **self._kwargs(cit_standard_rate=0.10, cit_regime="standard_flat")
        )
        high = calculate_vietnam_esco_cash_flow(
            **self._kwargs(cit_standard_rate=0.30, cit_regime="standard_flat")
        )
        self.assertGreater(
            sum(row["cit_vnd"] for row in high["annual_rows"]),
            sum(row["cit_vnd"] for row in low["annual_rows"]),
        )
```

Add `BESS_DEPRECIATION_YEARS` to the existing `from proforma_vietnam.cash_flow import ...` line at the top of the file if it is not already imported, and `CIT_STANDARD_RATE` from `proforma_vietnam.tax_model`.

If `cit_vnd` is not the annual-row key for tax paid, read one row from a passing test and correct the key. Do not change the assertion's intent.

- [ ] **Step 2: Run the test and confirm it fails**

```bash
./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_cash_flow.BessDepreciationYearsTests proforma_vietnam.tests.test_cash_flow.CitStandardRateTests -v
```

Expected: FAIL. `test_explicit_life_is_reported` raises `TypeError: calculate_vietnam_esco_cash_flow() got an unexpected keyword argument 'bess_depreciation_years'`, and `test_explicit_rate_is_reported` raises the equivalent for `cit_standard_rate`.

If `depreciation_vnd` is not the key name on an annual row, read one row from the passing default test and correct the key in the third test before proceeding. Do not change the assertion's intent.

- [ ] **Step 3: Add both parameters and resolve them**

In `proforma_vietnam/cash_flow.py`, add to the signature immediately after `pv_depreciation_years=PV_DEPRECIATION_YEARS,` (around line 113):

```python
    bess_depreciation_years=None,
    cit_standard_rate=None,
```

Then, near the top of the function body where other inputs are normalised (next to `replacement_costs_by_year = replacement_costs_by_year or []`, around line 179), add:

```python
    # None means "use the shared-core default". Vietnam passes nothing and is
    # unchanged; Thailand passes 5, its Royal Decree No. 145 machinery life.
    if bess_depreciation_years is None:
        bess_depreciation_years = BESS_DEPRECIATION_YEARS
    # Same pattern for the CIT rate. Both countries sit at 0.20 today, so this
    # is latent, but the rate was being read from a Vietnam constant regardless
    # of what the caller asked for.
    if cit_standard_rate is None:
        cit_standard_rate = CIT_STANDARD_RATE
```

`CIT_STANDARD_RATE` is defined in `proforma_vietnam/tax_model.py:10`. Add it to the existing `from proforma_vietnam.tax_model import (...)` block at `cash_flow.py:18` if it is not already imported.

- [ ] **Step 4: Thread it through the three helpers**

Change each helper signature and its uses of the global.

`_replacement_depreciation_schedules` (around line 1245):

```python
def _replacement_depreciation_schedules(replacement_costs_by_year, project_years,
                                        bess_depreciation_years):
```

Inside it, replace all three uses of `BESS_DEPRECIATION_YEARS` with `bess_depreciation_years`: the `annual_charge = cost / ...` line, the `min(year_index + ..., project_years)` bound, and the `"life_years": ...` field.

`_net_book_values_at_transfer` (around line 1296):

```python
def _net_book_values_at_transfer(pv_basis_vnd, bess_basis_vnd,
                                 pv_depreciation_years, contract_years,
                                 replacement_schedules,
                                 bess_depreciation_years):
```

Inside it, replace both uses of `BESS_DEPRECIATION_YEARS`: the `_remaining(bess_basis_vnd, ...)` call and the `"life_years": ...` field of the `initial_bess` entry.

`_depreciation_schedule` (around line 1340):

```python
def _depreciation_schedule(pv_capex_vnd, bess_capex_vnd, project_years,
                           pv_depreciation_years, bess_depreciation_years,
                           idc_vnd=0.0):
```

Inside it, replace the single use in the `straight_line_depreciation_schedule(bess_basis_vnd, ...)` call.

- [ ] **Step 5: Update the three call sites and the derivation dict**

Around line 419:

```python
            _replacement_depreciation_schedules(
                replacement_costs_by_year, project_years, bess_depreciation_years
            )
```

Around line 459:

```python
        depreciation_by_year = _depreciation_schedule(
            pv_capex_vnd, bess_capex_vnd, project_years, pv_depreciation_years,
            bess_depreciation_years,
            idc_vnd=idc_vnd,
        )
```

Around line 498:

```python
            nbv_by_asset, nbv_total_vnd = _net_book_values_at_transfer(
                pv_basis_vnd, bess_basis_vnd, pv_depreciation_years, contract_years,
                replacement_schedules if capitalize_replacement else [],
                bess_depreciation_years,
            )
```

Around line 835, in the derivation dict:

```python
        "bess_depreciation_years": bess_depreciation_years,
```

and around line 838, inside the nested `"cit"` block:

```python
            "standard_rate": cit_standard_rate,
```

Then pass the rate at BOTH `calculate_cit` call sites, around lines 512 and 524. Each currently omits `standard_rate` entirely; add it as the second argument in each:

```python
        cit_by_year = calculate_cit(
            taxable_income_by_year,
            standard_rate=cit_standard_rate,
            holiday_years=holiday_years,
            reduced_rate_years=reduced_rate_years,
            preferential_rate=preferential_rate,
            preferential_years=preferential_years,
            immediate_loss_relief=assume_profitable_host,
        )
```

Missing the second call site at line 524 leaves the disposal tax effect computed at the wrong rate, which is a silent inconsistency rather than an error. Verify with:

```bash
grep -n "calculate_cit(" -A 3 proforma_vietnam/cash_flow.py | grep -c "standard_rate=cit_standard_rate"
```

Expected: `2`.

- [ ] **Step 6: Run the new tests**

```bash
./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_cash_flow.BessDepreciationYearsTests proforma_vietnam.tests.test_cash_flow.CitStandardRateTests -v
```

Expected: 6 tests PASS.

- [ ] **Step 7: Run the full Vietnam suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v`

Expected: all pass. A failure here means a call site was missed.

- [ ] **Step 8: Run the Vietnam gate**

Run the gate command from Global Constraints.

Expected: `TOTAL DIFFS 0`. Anything else means the default resolution is not equivalent to the old constant. Do not proceed past a non-zero gate.

- [ ] **Step 9: Commit**

```bash
git add proforma_vietnam/cash_flow.py proforma_vietnam/tests/test_cash_flow.py
git commit -m "Make the BESS depreciation life and CIT rate injectable"
```

---

### Task 2: Replacement costs can be added to, not just replaced

`esco_pro_forma.py:124` sets `cash_flow_inputs["replacement_costs_by_year"]` from the BESS replacement, and `cash_flow_inputs.update(cash_flow_overrides)` then lets a caller's override REPLACE that series wholesale. Thailand needs to add an inverter replacement without destroying the battery replacement.

**Files:**
- Modify: `proforma_vietnam/esco_pro_forma.py`
- Test: `proforma_vietnam/tests/test_esco_pro_forma.py`

**Interfaces:**
- Produces: `calculate_esco_pro_forma_from_reopt_results(..., extra_replacement_costs_by_year=[...])`. The list is summed element-wise onto whatever replacement series already exists, extending the series when longer. Absent or `None` leaves behaviour unchanged.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_esco_pro_forma.py`:

```python
class ExtraReplacementCostsTests(unittest.TestCase):
    """Thailand books an inverter replacement without losing the BESS one."""

    def test_extra_costs_add_to_the_existing_series(self):
        merged = _merge_replacement_costs([0.0, 0.0, 100.0], [0.0, 50.0, 25.0])
        self.assertEqual(merged, [0.0, 50.0, 125.0])

    def test_longer_extra_series_extends_the_result(self):
        merged = _merge_replacement_costs([0.0, 100.0], [0.0, 0.0, 0.0, 70.0])
        self.assertEqual(merged, [0.0, 100.0, 0.0, 70.0])

    def test_missing_base_series_is_treated_as_zeros(self):
        merged = _merge_replacement_costs(None, [0.0, 40.0])
        self.assertEqual(merged, [0.0, 40.0])

    def test_missing_extra_series_leaves_the_base_untouched(self):
        merged = _merge_replacement_costs([0.0, 100.0], None)
        self.assertEqual(merged, [0.0, 100.0])
```

Add `_merge_replacement_costs` to the module's existing import from `proforma_vietnam.esco_pro_forma`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_esco_pro_forma.ExtraReplacementCostsTests -v`

Expected: FAIL with `ImportError: cannot import name '_merge_replacement_costs'`.

- [ ] **Step 3: Write the helper**

Add to `proforma_vietnam/esco_pro_forma.py`, next to `_bess_replacement_costs` (around line 372):

```python
def _merge_replacement_costs(base, extra):
    """Element-wise sum of two replacement-cost series, either of which may be None.

    Overriding replacement_costs_by_year wholesale would drop the BESS
    replacement derived from the REopt inputs. Thailand books an inverter
    replacement alongside it, so the two must add rather than compete.
    """
    base = list(base or [])
    extra = list(extra or [])
    length = max(len(base), len(extra))
    return [
        (base[i] if i < len(base) else 0.0) + (extra[i] if i < len(extra) else 0.0)
        for i in range(length)
    ]
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_esco_pro_forma.ExtraReplacementCostsTests -v`

Expected: 4 tests PASS.

- [ ] **Step 5: Wire the kwarg into the entry point**

In `calculate_esco_pro_forma_from_reopt_results`, alongside the other `cash_flow_overrides.pop(...)` calls near line 28:

```python
    extra_replacement_costs = cash_flow_overrides.pop(
        "extra_replacement_costs_by_year", None
    )
```

Then replace the replacement block at around line 119:

```python
    replacement_costs = _bess_replacement_costs(
        storage_inputs, storage_outputs, battery_replacement_year
    )
    if replacement_costs is not None:
        cash_flow_inputs["replacement_costs_by_year"] = _money_series(
            replacement_costs,
            exchange_rate_vnd_per_usd,
            tariff_money_values_currency,
        )
    if extra_replacement_costs:
        # Added, not assigned: a bare override would silently delete the BESS
        # replacement derived above.
        cash_flow_inputs["replacement_costs_by_year"] = _merge_replacement_costs(
            cash_flow_inputs.get("replacement_costs_by_year"),
            _money_series(
                extra_replacement_costs,
                exchange_rate_vnd_per_usd,
                tariff_money_values_currency,
            ),
        )
```

- [ ] **Step 6: Run the full Vietnam suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v`

Expected: all pass.

- [ ] **Step 7: Run the Vietnam gate**

Run the gate command from Global Constraints.

Expected: `TOTAL DIFFS 0`.

- [ ] **Step 8: Commit**

```bash
git add proforma_vietnam/esco_pro_forma.py proforma_vietnam/tests/test_esco_pro_forma.py
git commit -m "Let replacement costs be added to rather than overwritten"
```

---

### Task 3: Thailand books its own depreciation life and an inverter replacement

**Files:**
- Modify: `proforma_thailand/report.py`
- Modify: `proforma_thailand/case_builder.py`
- Modify: `proforma_thailand/defaults/thailand_defaults.json`
- Test: `proforma_thailand/tests/test_report.py`

**Interfaces:**
- Consumes: `bess_depreciation_years` kwarg from Task 1 and `extra_replacement_costs_by_year` from Task 2.
- Produces: assumptions keys `bess_depreciation_years` and `inverter_replacement_year`; `cash_flow_overrides_from_assumptions` emits `extra_replacement_costs_by_year`.

- [ ] **Step 1: Write the failing test**

Append to `proforma_thailand/tests/test_report.py`:

```python
class DepreciationAndInverterReplacementTests(TestCase):

    def test_bess_life_is_passed_through(self):
        overrides = cash_flow_overrides_from_assumptions(
            dict(ASSUMPTIONS, bess_depreciation_years=5)
        )
        self.assertEqual(overrides["bess_depreciation_years"], 5)

    def test_inverter_replacement_lands_in_the_right_year(self):
        overrides = cash_flow_overrides_from_assumptions(dict(
            ASSUMPTIONS,
            inverter_replacement_year=11,
            inverter_replacement_cost_usd=118_000.0,
        ))
        series = overrides["extra_replacement_costs_by_year"]
        self.assertEqual(len(series), 11)
        self.assertEqual(series[10], 118_000.0)
        self.assertEqual(sum(series[:10]), 0.0)

    def test_no_inverter_replacement_emits_no_series(self):
        overrides = cash_flow_overrides_from_assumptions(dict(ASSUMPTIONS))
        self.assertNotIn("extra_replacement_costs_by_year", overrides)

    def test_cit_rate_is_passed_through(self):
        overrides = cash_flow_overrides_from_assumptions(
            dict(ASSUMPTIONS, cit_standard_rate=0.20)
        )
        self.assertAlmostEqual(overrides["cit_standard_rate"], 0.20)
```

Add `cash_flow_overrides_from_assumptions` to the module's import from `proforma_thailand.report`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report.DepreciationAndInverterReplacementTests -v`

Expected: FAIL. `test_bess_life_is_passed_through` gets a `KeyError: 'bess_depreciation_years'`.

- [ ] **Step 3: Add the passthrough key and the replacement series**

In `proforma_thailand/report.py`, add to `PASSTHROUGH_OVERRIDE_KEYS`:

```python
    "bess_depreciation_years",
    "cit_standard_rate",
```

`cit_standard_rate` is already produced by the case builder and was being dropped; Task 1 gave it somewhere to go.

Then, in `cash_flow_overrides_from_assumptions` immediately before `return overrides`:

```python
    # REopt.jl models no PV inverter replacement, and neither did this proforma,
    # which overstates a 25-year case. Book it as its own replacement event so it
    # hits the year it actually falls in rather than being smeared into O&M.
    inverter_year = assumptions.get("inverter_replacement_year")
    inverter_cost = assumptions.get("inverter_replacement_cost_usd")
    if inverter_year and inverter_cost:
        series = [0.0] * int(inverter_year)
        series[int(inverter_year) - 1] = float(inverter_cost)
        overrides["extra_replacement_costs_by_year"] = series
```

- [ ] **Step 4: Add the defaults**

In `proforma_thailand/defaults/thailand_defaults.json`, add to the `financial` block:

```json
    "inverter_replacement_year": {"value": 11, "source": "PLACEHOLDER - pending Keen confirmation",
      "note": "String inverters are normally replaced once inside a 25-year analysis. Year 11 matches the ENS SolarStorage calculation form supplied in the client folder"},
    "inverter_replacement_fraction_of_pv_capex": {"value": 0.10, "source": "PLACEHOLDER - pending Keen confirmation",
      "note": "Inverter share of PV capex, from the ENS SolarStorage calculation form. Re-benchmarked for Thailand in Task 15"},
```

- [ ] **Step 5: Emit both from the case builder**

In `proforma_thailand/case_builder.py`, add to the `assumptions` dict next to `pv_depreciation_years`:

```python
        "bess_depreciation_years": TAX_DEFAULTS["bess_depreciation_years"],
        "inverter_replacement_year": value_of(
            FINANCIAL_DEFAULTS, "inverter_replacement_year"
        ),
        "inverter_replacement_cost_usd": (
            pv_max_kw
            * pv_config.get(
                "installed_cost_per_kw",
                value_of(FINANCIAL_DEFAULTS, "pv_installed_cost_per_kw"),
            )
            * value_of(
                FINANCIAL_DEFAULTS, "inverter_replacement_fraction_of_pv_capex"
            )
        ),
```

- [ ] **Step 6: Run the Thailand suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v`

Expected: all pass, including the three new tests.

- [ ] **Step 7: Commit**

```bash
git add proforma_thailand/report.py proforma_thailand/case_builder.py proforma_thailand/defaults/thailand_defaults.json proforma_thailand/tests/test_report.py
git commit -m "Book Thailand depreciation lives and an inverter replacement"
```

---

### Task 4: Insurance is costed

`insurance_rate_fraction` sits in the defaults and is read by nothing, so insurance is absent from the model entirely. Fold it into the O&M figure Thailand already hands the engine, where it escalates with O&M and is deducted as opex.

**Files:**
- Modify: `proforma_thailand/report.py`
- Test: `proforma_thailand/tests/test_report.py`

**Interfaces:**
- Produces: `annual_opex_usd(pv_capex_usd, bess_capex_usd, other_capex_usd, annual_om_usd, insurance_rate_fraction) -> float`

- [ ] **Step 1: Write the failing test**

Append to `proforma_thailand/tests/test_report.py`:

```python
class InsuranceTests(TestCase):

    def test_insurance_is_a_fraction_of_total_installed_capex(self):
        # 0.5 percent of 1,200,000 is 6,000, on top of 20,000 of O&M.
        self.assertAlmostEqual(
            annual_opex_usd(1_000_000.0, 150_000.0, 50_000.0, 20_000.0, 0.005),
            26_000.0,
        )

    def test_zero_rate_leaves_om_untouched(self):
        self.assertAlmostEqual(
            annual_opex_usd(1_000_000.0, 0.0, 0.0, 20_000.0, 0.0),
            20_000.0,
        )

    def test_none_rate_is_treated_as_zero(self):
        self.assertAlmostEqual(
            annual_opex_usd(1_000_000.0, 0.0, 0.0, 20_000.0, None),
            20_000.0,
        )
```

Add `annual_opex_usd` to the module's import from `proforma_thailand.report`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report.InsuranceTests -v`

Expected: FAIL with `ImportError: cannot import name 'annual_opex_usd'`.

- [ ] **Step 3: Write the function**

Add to `proforma_thailand/report.py`:

```python
def annual_opex_usd(pv_capex_usd, bess_capex_usd, other_capex_usd,
                    annual_om_usd, insurance_rate_fraction):
    """Year-one operating cost including insurance.

    Insurance was costed nowhere. It is a real annual expense on an owned
    asset, so it belongs in opex where it escalates with O&M and is deducted
    for CIT. The base is total installed capex, which is how underwriters quote
    an all-risk premium.
    """
    total_capex = (pv_capex_usd or 0.0) + (bess_capex_usd or 0.0) + (other_capex_usd or 0.0)
    return (annual_om_usd or 0.0) + total_capex * (insurance_rate_fraction or 0.0)
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report.InsuranceTests -v`

Expected: 3 tests PASS.

- [ ] **Step 5: Apply it in `build_thailand_report`**

In `build_thailand_report`, after `overrides = cash_flow_overrides_from_assumptions(assumptions)` and after the power-factor `other_capex_vnd` adjustment, add:

```python
    # Capex comes from the solved results, so insurance is computed here rather
    # than in the case builder, which does not yet know the optimized sizes.
    outputs = reopt_results.get("outputs") or {}
    pv_outputs = outputs.get("PV") or {}
    if isinstance(pv_outputs, list):
        pv_outputs = pv_outputs[0] if pv_outputs else {}
    storage_outputs = outputs.get("ElectricStorage") or {}
    insurance_rate = value_of(FINANCIAL_DEFAULTS, "insurance_rate_fraction")
    if overrides.get("annual_om_vnd") is not None:
        overrides["annual_om_vnd"] = annual_opex_usd(
            pv_outputs.get("initial_capital_cost") or 0.0,
            storage_outputs.get("initial_capital_cost") or 0.0,
            overrides.get("other_capex_vnd") or 0.0,
            overrides["annual_om_vnd"],
            insurance_rate,
        )
```

- [ ] **Step 6: Render it as its own Assumptions line**

In `build_thailand_report`, where `workbook_assumptions` is built, add:

```python
    workbook_assumptions["insurance_rate_fraction"] = insurance_rate
```

In `proforma_vietnam/audit_sheets.py`, inside the Step 4 assumptions writer immediately before the `placeholder_keys` block (around line 638), add:

```python
    # Gated on the key, so Vietnam workbooks, which never set it, are unchanged.
    insurance_rate = (assumptions or {}).get("insurance_rate_fraction")
    if insurance_rate is not None:
        entry(
            "Insurance (fraction of installed capex per year)",
            insurance_rate,
            unit="per year",
            source="Included in annual operating cost",
            fmt="0.000%",
        )
```

- [ ] **Step 7: Run both suites and the gate**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
```

Then run the gate command from Global Constraints.

Expected: all pass, `TOTAL DIFFS 0`. A non-zero gate means the `audit_sheets.py` insertion is not properly gated on the key.

- [ ] **Step 8: Commit**

```bash
git add proforma_thailand/report.py proforma_thailand/tests/test_report.py proforma_vietnam/audit_sheets.py
git commit -m "Cost insurance as an annual operating expense"
```

---

### Task 5: Thailand sets the payload defaults it was inheriting from the US

Every omitted field in a REopt payload silently takes a US-centric Django default. Three are wrong here: a battery with no minimum duration, storage O&M at the US 2.5 percent, and a PVWatts tilt tuned for Vietnam.

**Files:**
- Modify: `proforma_thailand/case_builder.py`
- Modify: `proforma_thailand/defaults/thailand_defaults.json`
- Test: `proforma_thailand/tests/test_case_builder.py`

**Interfaces:**
- Produces: `ElectricStorage.min_duration_hours` and `ElectricStorage.om_cost_fraction_of_installed_cost` on the payload; `tilt` passed through to `pvwatts_client.fetch_pv_series` via its `overrides` argument.

- [ ] **Step 1: Write the failing test**

Append to `proforma_thailand/tests/test_case_builder.py`:

```python
class PayloadDefaultsTests(TestCase):

    def test_storage_declares_a_minimum_duration(self):
        case = build_thailand_case(_case_config(storage={"max_kw": 500, "max_kwh": 1000}))
        self.assertEqual(
            case["payload"]["ElectricStorage"]["min_duration_hours"], 1.5
        )

    def test_storage_om_fraction_is_explicit(self):
        case = build_thailand_case(_case_config(storage={"max_kw": 500, "max_kwh": 1000}))
        self.assertIn(
            "om_cost_fraction_of_installed_cost",
            case["payload"]["ElectricStorage"],
        )

    def test_tilt_defaults_to_fifteen_degrees(self):
        captured = {}

        def _fake_fetch(latitude, longitude, overrides=None, api_key=None):
            captured["overrides"] = overrides
            return {"production_factor": [0.0] * 8760, "poa_wm2": [0.0] * 8760}

        with mock.patch.object(pvwatts_client, "fetch_pv_series", _fake_fetch):
            build_thailand_case(_case_config())
        self.assertEqual(captured["overrides"]["tilt"], 15)

    def test_case_can_override_tilt(self):
        captured = {}

        def _fake_fetch(latitude, longitude, overrides=None, api_key=None):
            captured["overrides"] = overrides
            return {"production_factor": [0.0] * 8760, "poa_wm2": [0.0] * 8760}

        config = _case_config()
        config["site"]["tilt"] = 7
        with mock.patch.object(pvwatts_client, "fetch_pv_series", _fake_fetch):
            build_thailand_case(config)
        self.assertEqual(captured["overrides"]["tilt"], 7)
```

If the test module has no `_case_config` helper, add one returning a dict matching `proforma_thailand/cases/rts/case.json`, taking `storage` as an optional keyword that lands under `technologies.storage`. Import `mock` from `unittest` and `pvwatts_client` from `proforma_vietnam`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder.PayloadDefaultsTests -v`

Expected: FAIL with `KeyError: 'min_duration_hours'`.

- [ ] **Step 3: Add the defaults**

In `proforma_thailand/defaults/thailand_defaults.json`, add to `financial`:

```json
    "bess_min_duration_hours": {"value": 1.5, "source": "PLACEHOLDER - pending Keen confirmation",
      "note": "REopt inherits 0.0, which permits a physically meaningless zero-duration battery. 1.5 hours is the shortest duration a C&I lithium system is normally offered at"},
    "bess_om_fraction_of_installed_cost": {"value": 0.01, "source": "PLACEHOLDER - pending Keen confirmation",
      "note": "REopt's own default is 2.5 percent, a US figure. Re-benchmarked for Thailand in Task 15"},
```

and to `site`:

```json
    "pv_tilt_degrees": {"value": 15, "source": "PLACEHOLDER - pending Keen confirmation",
      "note": "Approximates both the site latitude of 15.21N and a typical industrial metal roof pitch. Actual roof pitch is not recorded in the RTS Data Collection sheet and is an information request to Ou"},
```

- [ ] **Step 4: Use them in the case builder**

In `proforma_thailand/case_builder.py`, change the PVWatts call:

```python
    production = pvwatts_client.fetch_pv_series(
        site["latitude"],
        site["longitude"],
        overrides={"tilt": site.get("tilt", value_of(SITE_DEFAULTS, "pv_tilt_degrees"))},
    )
```

In the `ElectricStorage` block, add:

```python
            "min_duration_hours": storage_config.get(
                "min_duration_hours",
                value_of(FINANCIAL_DEFAULTS, "bess_min_duration_hours"),
            ),
            "om_cost_fraction_of_installed_cost": storage_config.get(
                "om_cost_fraction_of_installed_cost",
                value_of(FINANCIAL_DEFAULTS, "bess_om_fraction_of_installed_cost"),
            ),
```

Also add `"pv_tilt_degrees": site.get("tilt", value_of(SITE_DEFAULTS, "pv_tilt_degrees")),` to the `assumptions` dict so the tilt is disclosed.

- [ ] **Step 5: Run the tests**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v`

Expected: all pass.

- [ ] **Step 6: Verify the tilt actually reaches PVWatts**

Run:

```bash
./.venv/Scripts/python.exe -c "
import inspect
from proforma_vietnam import pvwatts_client
print(inspect.signature(pvwatts_client.fetch_pv_series))
print('default tilt in module:', pvwatts_client.DEFAULT_PARAMS.get('tilt') if hasattr(pvwatts_client, 'DEFAULT_PARAMS') else 'inspect module for the params dict name')
"
```

Expected: the signature accepts `overrides`, and the module-level params dict shows the Vietnam default of 10. Confirm by reading `proforma_vietnam/pvwatts_client.py` around line 24 that `overrides` is merged over that dict rather than ignored. If it is ignored, fix the merge in `pvwatts_client.py` and re-run the Vietnam suite plus the gate before continuing.

- [ ] **Step 7: Commit**

```bash
git add proforma_thailand/case_builder.py proforma_thailand/defaults/thailand_defaults.json proforma_thailand/tests/test_case_builder.py
git commit -m "Set the Thailand payload defaults instead of inheriting US ones"
```

---

### Task 6: Billed demand counts every kW the meter sees

`billed_demand_kw_by_month` reads only `electric_to_load_series_kw`. The meter sees grid-to-load PLUS grid-to-storage, and REopt's own coincident-peak constraint applies to total grid purchase, so the report understates what the model itself billed. This scales with battery size and must be right before the storage cases are read.

**Files:**
- Modify: `proforma_thailand/report.py`
- Test: `proforma_thailand/tests/test_report.py`

**Interfaces:**
- Produces: `billed_demand_kw_by_month(reopt_results)` unchanged in signature, now summing both grid series.

- [ ] **Step 1: Write the failing test**

Append to the existing `BilledDemandTests` class in `proforma_thailand/tests/test_report.py`:

```python
    def _results_with_storage(self, periods, to_load, to_storage):
        return {
            "inputs": {"ElectricTariff": {
                "coincident_peak_load_active_time_steps": periods}},
            "outputs": {"ElectricUtility": {
                "electric_to_load_series_kw": to_load,
                "electric_to_storage_series_kw": to_storage,
            }},
        }

    def test_grid_charging_counts_towards_billed_demand(self):
        results = self._results_with_storage(
            [[1, 2, 3]], [100.0, 200.0, 150.0], [50.0, 0.0, 0.0]
        )
        # Step 1 draws 100 for load plus 50 for the battery: 150 total.
        # Step 2 draws 200 for load alone. The month peak is 200.
        self.assertEqual(billed_demand_kw_by_month(results), [200.0])

    def test_grid_charging_can_set_the_peak(self):
        results = self._results_with_storage(
            [[1, 2]], [100.0, 120.0], [400.0, 0.0]
        )
        self.assertEqual(billed_demand_kw_by_month(results), [500.0])

    def test_absent_storage_series_is_treated_as_zeros(self):
        results = self._results_with_storage([[1, 2]], [100.0, 120.0], [])
        self.assertEqual(billed_demand_kw_by_month(results), [120.0])
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report.BilledDemandTests -v`

Expected: `test_grid_charging_can_set_the_peak` FAILS, reporting `[120.0]` instead of `[500.0]`.

- [ ] **Step 3: Sum both series**

Replace the body of `billed_demand_kw_by_month` in `proforma_thailand/report.py`:

```python
def billed_demand_kw_by_month(reopt_results):
    """On-peak billed demand per month, from the OPTIMIZED total grid draw.

    PEA bills the on-peak maximum of what the meter sees, which is grid-to-load
    PLUS grid-to-storage. REopt's own coincident-peak constraint applies to
    total grid purchase, so reading only the to-load series under-reports what
    the model already billed. Those step sets are 1-based, matching the Julia
    convention, hence the ``- 1``. Returns [] when either side is absent rather
    than inventing zeros.
    """
    tariff = (reopt_results.get("inputs") or {}).get("ElectricTariff") or {}
    utility = (reopt_results.get("outputs") or {}).get("ElectricUtility") or {}
    periods = tariff.get("coincident_peak_load_active_time_steps") or []
    to_load = utility.get("electric_to_load_series_kw") or []
    to_storage = utility.get("electric_to_storage_series_kw") or []
    if not periods or not to_load:
        return []

    def _draw(step):
        index = step - 1
        charging = to_storage[index] if index < len(to_storage) else 0.0
        return to_load[index] + charging

    return [
        max((_draw(step) for step in steps if 0 < step <= len(to_load)),
            default=0.0)
        for steps in periods
    ]
```

- [ ] **Step 4: Run the tests**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v`

Expected: all pass.

- [ ] **Step 5: Confirm the existing runs are unaffected**

Run:

```bash
./.venv/Scripts/python.exe -c "
import json
from proforma_thailand.report import billed_demand_kw_by_month
for case in ('rts', 'rts_bess'):
    results = json.load(open('proforma_thailand/cases/%s/results.json' % case, encoding='utf-8'))
    recomputed = billed_demand_kw_by_month(results)
    saved = json.load(open('proforma_thailand/cases/%s/summary.json' % case, encoding='utf-8'))['billed_demand_kw_by_month']
    delta = max(abs(a - b) for a, b in zip(recomputed, saved))
    print(case, 'max delta kW: %.4f' % delta)
"
```

Expected: `rts` shows 0.0000 exactly, because it has no battery. `rts_bess` may show a small positive delta from its 29 kW battery. Record both numbers in the commit message. A large `rts` delta means the change is wrong.

- [ ] **Step 6: Commit**

```bash
git add proforma_thailand/report.py proforma_thailand/tests/test_report.py
git commit -m "Bill demand on total grid draw, not grid-to-load alone"
```

---

### Task 7: Unmarked placeholders stop a run

`validate_no_unmarked_placeholders` is called only from tests, so nothing prevents a workbook reaching a client with a confident IRR and no disclosure that its inputs are provisional.

**Files:**
- Modify: `proforma_thailand/run_case.py`
- Test: `proforma_thailand/tests/test_run_case.py`

**Interfaces:**
- Produces: `assert_placeholders_disclosed(workbook) -> None`, raising `RuntimeError` when a headline metric is present with no marker anywhere.

- [ ] **Step 1: Write the failing test**

Append to `proforma_thailand/tests/test_run_case.py`:

```python
class PlaceholderGuardTests(TestCase):

    def _workbook(self, cells):
        import openpyxl
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        for index, value in enumerate(cells, start=1):
            sheet.cell(row=index, column=1, value=value)
        return workbook

    def test_marked_workbook_passes(self):
        workbook = self._workbook([
            "Equity IRR", "PLACEHOLDER - pending Keen confirmation",
        ])
        assert_placeholders_disclosed(workbook)

    def test_unmarked_workbook_raises(self):
        workbook = self._workbook(["Equity IRR", "all inputs confirmed"])
        with self.assertRaises(RuntimeError) as caught:
            assert_placeholders_disclosed(workbook)
        self.assertIn("placeholder", str(caught.exception).lower())

    def test_workbook_with_no_headline_metric_passes(self):
        workbook = self._workbook(["Dispatch", "Interval"])
        assert_placeholders_disclosed(workbook)
```

Add `assert_placeholders_disclosed` to the module's import from `proforma_thailand.run_case`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_run_case.PlaceholderGuardTests -v`

Expected: FAIL with `ImportError: cannot import name 'assert_placeholders_disclosed'`.

- [ ] **Step 3: Write the guard**

Add to `proforma_thailand/run_case.py`:

```python
HEADLINE_LABELS = ("IRR", "NPV", "Payback")


def assert_placeholders_disclosed(workbook):
    """Refuse to ship a workbook that reports returns without disclosing provisionality.

    The validator checks that placeholders are MARKED, not that they are
    absent, so failing hard here does not block legitimate provisional inputs.
    It blocks a rendering regression that silently drops the markers.
    """
    from proforma_thailand.defaults import PLACEHOLDER_MARKER
    from proforma_vietnam.validate_workbook import validate_no_unmarked_placeholders

    failures = validate_no_unmarked_placeholders(
        workbook, PLACEHOLDER_MARKER, HEADLINE_LABELS
    )
    if failures:
        raise RuntimeError(
            "Refusing to write the workbook: {}".format(" ".join(failures))
        )
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_run_case.PlaceholderGuardTests -v`

Expected: 3 tests PASS.

- [ ] **Step 5: Call it on the production path**

In `main` in `proforma_thailand/run_case.py`, between building the workbook and saving it:

```python
    workbook, extras = build_thailand_report(results, assumptions)
    assert_placeholders_disclosed(workbook)
    workbook.save(out_dir / "thailand_report_{}.xlsx".format(run_uuid))
```

- [ ] **Step 6: Prove the guard runs on a real workbook**

Run:

```bash
./.venv/Scripts/python.exe -c "
import json
from proforma_thailand.report import build_thailand_report
from proforma_thailand.run_case import assert_placeholders_disclosed
results = json.load(open('proforma_thailand/cases/rts/results.json', encoding='utf-8'))
assumptions = json.load(open('proforma_thailand/cases/rts/assumptions.json', encoding='utf-8'))
workbook, _ = build_thailand_report(results, assumptions)
assert_placeholders_disclosed(workbook)
print('guard passed on the real RTS workbook')
"
```

Expected: `guard passed on the real RTS workbook`. A raise here means the markers are not being rendered and must be fixed before continuing.

- [ ] **Step 7: Run the suite and commit**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
git add proforma_thailand/run_case.py proforma_thailand/tests/test_run_case.py
git commit -m "Refuse to write a workbook with undisclosed placeholders"
```

---

### Task 8: The dispatch sheet's irradiance lines up with its rows

PVWatts returns 8760 hourly POA values. Thailand's dispatch has 35,040 rows. Pairing them leaves the column 4x misaligned and zero for 75 percent of rows.

**Files:**
- Modify: `proforma_vietnam/report_data.py`
- Test: `proforma_vietnam/tests/test_report_data.py`

**Interfaces:**
- Produces: `_upsample_series(series, factor) -> list`, and `build_vietnam_report_data` up-samples `poa_irradiance_series` when it is shorter than the dispatch series.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_report_data.py`:

```python
class UpsampleSeriesTests(unittest.TestCase):

    def test_factor_of_one_returns_the_same_values(self):
        self.assertEqual(_upsample_series([1.0, 2.0], 1), [1.0, 2.0])

    def test_each_value_repeats_factor_times(self):
        self.assertEqual(
            _upsample_series([1.0, 2.0], 4),
            [1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0],
        )

    def test_empty_series_stays_empty(self):
        self.assertEqual(_upsample_series([], 4), [])

    def test_hourly_poa_becomes_quarter_hourly(self):
        self.assertEqual(len(_upsample_series([0.5] * 8760, 4)), 35040)
```

Add `_upsample_series` to the module's import from `proforma_vietnam.report_data`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_report_data.UpsampleSeriesTests -v`

Expected: FAIL with `ImportError: cannot import name '_upsample_series'`.

- [ ] **Step 3: Write the helper**

Add to `proforma_vietnam/report_data.py`:

```python
def _upsample_series(series, factor):
    """Repeat each value ``factor`` times.

    PVWatts returns 8760 hourly values regardless of the model's resolution,
    the same way REopt up-samples a production factor onto a finer container.
    Pairing an hourly series against a 15-minute dispatch without this leaves
    the column 4x misaligned and zero for three rows in every four.
    """
    if factor <= 1:
        return list(series)
    return [value for value in series for _ in range(factor)]
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_report_data.UpsampleSeriesTests -v`

Expected: 4 tests PASS.

- [ ] **Step 5: Apply it where the POA series is consumed**

In `build_vietnam_report_data`, immediately after the `poa_irradiance_series` parameter is first used, insert:

```python
    # Vietnam runs hourly, where the factor is 1 and this is a no-op.
    if poa_irradiance_series and time_steps_per_hour > 1:
        poa_irradiance_series = _upsample_series(
            poa_irradiance_series, time_steps_per_hour
        )
```

- [ ] **Step 6: Verify the alignment on the real Thailand run**

Run:

```bash
./.venv/Scripts/python.exe -c "
import json
from proforma_vietnam.report_data import build_vietnam_report_data
results = json.load(open('proforma_thailand/cases/rts/results.json', encoding='utf-8'))
assumptions = json.load(open('proforma_thailand/cases/rts/assumptions.json', encoding='utf-8'))
poa = assumptions.get('pv_poa_irradiance_series')
print('poa length in assumptions:', len(poa) if poa else None)
data = build_vietnam_report_data(results, None, poa_irradiance_series=poa, time_steps_per_hour=4)
rows = data['dispatch_rows'] if 'dispatch_rows' in data else None
print('dispatch rows key present:', rows is not None)
"
```

Expected: `poa length in assumptions: 8760`. If the dispatch key name differs, read `report_data.py` for the actual key and report the non-zero fraction of the irradiance column before and after. It must rise from about 25 percent to the full daylight fraction.

- [ ] **Step 7: Run the Vietnam suite and the gate**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
```

Then run the gate command from Global Constraints.

Expected: all pass, `TOTAL DIFFS 0`. Vietnam runs at `time_steps_per_hour=1` so the branch is never taken.

- [ ] **Step 8: Commit**

```bash
git add proforma_vietnam/report_data.py proforma_vietnam/tests/test_report_data.py
git commit -m "Align the dispatch irradiance column with 15-minute rows"
```

---

### Task 9: The Ft series reaches the workbook

`audit_sheets.py` writes scalars only, so the per-month Ft series is computed, carried in the assumptions and then silently dropped. `ft_forecast_per_kwh` is a separate dead key that nothing reads.

**Files:**
- Modify: `proforma_vietnam/audit_sheets.py`
- Modify: `proforma_thailand/defaults/thailand_defaults.json`
- Test: `proforma_vietnam/tests/test_audit_sheets.py`
- Test: `proforma_thailand/tests/test_thailand_defaults.py`

**Interfaces:**
- Produces: `_format_series(values, places=4) -> str`, a compact comma-joined rendering used for list-valued assumption rows.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_audit_sheets.py`:

```python
class FormatSeriesTests(unittest.TestCase):

    def test_values_are_comma_joined(self):
        self.assertEqual(_format_series([0.3672, 0.1972]), "0.3672, 0.1972")

    def test_trailing_zeros_are_trimmed(self):
        self.assertEqual(_format_series([0.5, 0.25]), "0.5, 0.25")

    def test_empty_series_renders_as_an_empty_string(self):
        self.assertEqual(_format_series([]), "")
```

Add `_format_series` to the module's import from `proforma_vietnam.audit_sheets`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_audit_sheets.FormatSeriesTests -v`

Expected: FAIL with `ImportError: cannot import name '_format_series'`.

- [ ] **Step 3: Write the formatter**

Add to `proforma_vietnam/audit_sheets.py`:

```python
def _format_series(values, places=4):
    """Render a numeric series as one compact cell value.

    Twelve monthly Ft values do not warrant twelve rows, but dropping them
    entirely, which is what happens when a list reaches a scalar writer, leaves
    the reader unable to check the tariff against an invoice.
    """
    return ", ".join(
        ("{:." + str(places) + "f}").format(value).rstrip("0").rstrip(".")
        for value in values
    )
```

- [ ] **Step 4: Render the Ft series**

In the Step 4 assumptions writer in `proforma_vietnam/audit_sheets.py`, immediately before the `placeholder_keys` block, add:

```python
    # Gated on the key, so Vietnam workbooks, which never set it, are unchanged.
    ft_series = (assumptions or {}).get("ft_per_kwh_by_month_thb")
    if ft_series:
        entry(
            "Ft adder by month (Jan to Dec)",
            _format_series(ft_series),
            unit=(assumptions or {}).get("local_currency_code", "") + "/kWh",
            source="PEA Ft schedule, revised every four months",
        )
```

- [ ] **Step 5: Remove the dead key**

Delete the `ft_forecast_per_kwh` entry from the `financial` block of `proforma_thailand/defaults/thailand_defaults.json`.

Confirm nothing reads it:

```bash
grep -rn "ft_forecast_per_kwh" --include=*.py --include=*.json . | grep -v __pycache__
```

Expected: no output. Any hit must be resolved before continuing.

- [ ] **Step 6: Assert the Ft window lookup**

Append to `proforma_thailand/tests/test_thailand_defaults.py`:

```python
class FtWindowTests(TestCase):

    def test_january_2025_uses_the_first_window(self):
        self.assertAlmostEqual(ft_for_month(2025, 1), 0.3672)

    def test_may_2025_uses_the_second_window(self):
        self.assertAlmostEqual(ft_for_month(2025, 5), 0.1972)

    def test_september_2025_uses_the_third_window(self):
        self.assertAlmostEqual(ft_for_month(2025, 9), 0.1572)

    def test_a_month_before_any_window_raises(self):
        with self.assertRaises(ValueError):
            ft_for_month(2000, 1)
```

Add `ft_for_month` to the module's import from `proforma_thailand.defaults`.

- [ ] **Step 7: Run both suites and the gate**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
```

Then run the gate command from Global Constraints.

Expected: all pass, `TOTAL DIFFS 0`.

- [ ] **Step 8: Commit**

```bash
git add proforma_vietnam/audit_sheets.py proforma_vietnam/tests/test_audit_sheets.py proforma_thailand/defaults/thailand_defaults.json proforma_thailand/tests/test_thailand_defaults.py
git commit -m "Render the Ft month series and drop the dead forecast key"
```

---

### Task 10: The exchange rate prints its fractional part

`audit_sheets.py:2110` formats the rate with `{fx:,.0f}`, so Thailand's 32.5 THB/USD is disclosed to the client as "32". Vietnam's 26,300 must keep rendering identically.

**Files:**
- Modify: `proforma_vietnam/audit_sheets.py`
- Test: `proforma_vietnam/tests/test_audit_sheets.py`

**Interfaces:**
- Produces: `_format_exchange_rate(value) -> str`.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_audit_sheets.py`:

```python
class FormatExchangeRateTests(unittest.TestCase):

    def test_vietnam_rate_is_unchanged(self):
        self.assertEqual(_format_exchange_rate(26300), "26,300")

    def test_vietnam_float_rate_is_unchanged(self):
        self.assertEqual(_format_exchange_rate(26300.0), "26,300")

    def test_thailand_rate_keeps_its_decimal(self):
        self.assertEqual(_format_exchange_rate(32.5), "32.5")

    def test_two_decimal_rate_is_preserved(self):
        self.assertEqual(_format_exchange_rate(32.55), "32.55")
```

Add `_format_exchange_rate` to the module's import from `proforma_vietnam.audit_sheets`.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_audit_sheets.FormatExchangeRateTests -v`

Expected: FAIL with `ImportError: cannot import name '_format_exchange_rate'`.

- [ ] **Step 3: Write the formatter**

Add to `proforma_vietnam/audit_sheets.py`:

```python
def _format_exchange_rate(value):
    """Thousands separator, and only as many decimals as the rate actually has.

    Vietnam's 26,300 VND/USD and Thailand's 32.5 THB/USD differ by three orders
    of magnitude. A fixed zero-decimal format disclosed 32.5 to the client as
    "32".
    """
    text = "{:,.4f}".format(value)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_audit_sheets.FormatExchangeRateTests -v`

Expected: 4 tests PASS.

- [ ] **Step 5: Use it at the disclosure line**

At `proforma_vietnam/audit_sheets.py:2110`, replace:

```python
            f"All money flows are computed in USD at the fixed contract rate ({fx:,.0f} {profile.local_currency_code}/USD)."
```

with:

```python
            f"All money flows are computed in USD at the fixed contract rate ({_format_exchange_rate(fx)} {profile.local_currency_code}/USD)."
```

- [ ] **Step 6: Run the Vietnam suite and the gate**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
```

Then run the gate command from Global Constraints.

Expected: all pass, `TOTAL DIFFS 0`. A diff here means some Vietnam case carries a fractional rate; if so, report the case and the two renderings rather than adjusting the format to hide it.

- [ ] **Step 7: Confirm the Thailand rendering**

```bash
./.venv/Scripts/python.exe -c "
from proforma_vietnam.audit_sheets import _format_exchange_rate
print('Thailand:', _format_exchange_rate(32.5))
print('Vietnam :', _format_exchange_rate(26300))
"
```

Expected: `Thailand: 32.5` and `Vietnam : 26,300`.

- [ ] **Step 8: Commit**

```bash
git add proforma_vietnam/audit_sheets.py proforma_vietnam/tests/test_audit_sheets.py
git commit -m "Disclose the exchange rate without truncating its decimals"
```

---

### Task 11: The Vietnam gate stops ignoring subtitle rows

`DEFAULT_IGNORE_SUBSTRINGS = ("prepared ",)` is broad enough to hide any Cover or Executive Summary row containing that substring. `DEFAULT_IGNORE_ROW_LABELS = ("Report prepared",)` already exists and is precise, so the substring rule is redundant as well as dangerous.

**Files:**
- Modify: `proforma_vietnam/tools/compare_workbooks.py`
- Test: `proforma_vietnam/tests/test_compare_workbooks.py`

**Interfaces:**
- Produces: `DEFAULT_IGNORE_SUBSTRINGS = ()`. `compare_workbooks` keeps its signature.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_compare_workbooks.py`:

```python
class NarrowedIgnoreRulesTests(unittest.TestCase):

    def _workbook(self, path, rows):
        import openpyxl
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        for row_index, row in enumerate(rows, start=1):
            for column_index, value in enumerate(row, start=1):
                sheet.cell(row=row_index, column=column_index, value=value)
        workbook.save(path)
        return path

    def test_a_changed_subtitle_is_now_visible(self):
        import tempfile, os
        directory = tempfile.mkdtemp()
        a = self._workbook(os.path.join(directory, "a.xlsx"),
                           [["Case prepared for Factory A"]])
        b = self._workbook(os.path.join(directory, "b.xlsx"),
                           [["Case prepared for Factory B"]])
        self.assertEqual(len(compare_workbooks(a, b)), 1)

    def test_the_report_prepared_date_row_is_still_ignored(self):
        import tempfile, os
        directory = tempfile.mkdtemp()
        a = self._workbook(os.path.join(directory, "a.xlsx"),
                           [["Report prepared", "2026-09-04"]])
        b = self._workbook(os.path.join(directory, "b.xlsx"),
                           [["Report prepared", "2026-09-05"]])
        self.assertEqual(compare_workbooks(a, b), [])
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_compare_workbooks.NarrowedIgnoreRulesTests -v`

Expected: `test_a_changed_subtitle_is_now_visible` FAILS, reporting 0 differences because the substring rule swallows the row.

- [ ] **Step 3: Empty the substring rule**

In `proforma_vietnam/tools/compare_workbooks.py`, replace line 13:

```python
# Nothing is ignored by substring. The precise DEFAULT_IGNORE_ROW_LABELS rule
# below covers the one genuinely volatile row, the prepared-on date. A
# substring of "prepared " also hid Cover and Executive Summary subtitles,
# which is how a Vietnam-titled Thailand workbook passed the gate.
DEFAULT_IGNORE_SUBSTRINGS = ()
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_compare_workbooks -v`

Expected: all pass.

- [ ] **Step 5: Run the gate with the narrowed rules**

Run the gate command from Global Constraints.

Expected: `TOTAL DIFFS 0`.

**If this reports a non-zero count, stop.** The gate was previously blind to those rows, so any diff it now shows is a real, previously hidden finding. Record each one, and report it before changing anything. Do NOT re-widen the ignore rule to make the gate green.

- [ ] **Step 6: Run the full Vietnam suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v`

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add proforma_vietnam/tools/compare_workbooks.py proforma_vietnam/tests/test_compare_workbooks.py
git commit -m "Stop the workbook gate ignoring rows by substring"
```

---

### Task 12: The load inputs can be regenerated and the month order is checked

`extract_intervals` and `build_calendar_year` have no caller outside tests, and no committed script regenerates the load CSV or holiday JSON. The CSV is a bare `load_kw` column with no timestamps, so `calendar_year_months` in `case.json` is unverifiable and only its length is checked. Reordering months silently misaligns load against tariff.

**Files:**
- Create: `proforma_thailand/tools/__init__.py`
- Create: `proforma_thailand/tools/build_load_inputs.py`
- Create: `proforma_thailand/data/load_manifest.json`
- Create: `proforma_thailand/tests/test_build_load_inputs.py`
- Modify: `proforma_thailand/case_builder.py`

**Interfaces:**
- Produces: `build_manifest(calendar_year_months, rows_per_month, source_sha256) -> dict` with keys `calendar_year_months`, `rows_per_month`, `total_rows`, `source_sha256`. `validate_calendar_months(calendar_months, manifest) -> None`, raising `ValueError` on mismatch.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_build_load_inputs.py`:

```python
"""The committed load inputs must be reproducible and self-describing."""

from unittest import TestCase

from proforma_thailand.tools.build_load_inputs import (
    build_manifest,
    validate_calendar_months,
)


class BuildManifestTests(TestCase):

    def test_manifest_records_order_counts_and_hash(self):
        manifest = build_manifest([(2026, 1), (2025, 12)], [2976, 2976], "abc123")
        self.assertEqual(manifest["calendar_year_months"], [[2026, 1], [2025, 12]])
        self.assertEqual(manifest["rows_per_month"], [2976, 2976])
        self.assertEqual(manifest["total_rows"], 5952)
        self.assertEqual(manifest["source_sha256"], "abc123")


class ValidateCalendarMonthsTests(TestCase):

    MANIFEST = {
        "calendar_year_months": [[2026, 1], [2026, 2], [2025, 12]],
        "rows_per_month": [2976, 2688, 2976],
        "total_rows": 8640,
        "source_sha256": "abc123",
    }

    def test_matching_order_passes(self):
        validate_calendar_months([(2026, 1), (2026, 2), (2025, 12)], self.MANIFEST)

    def test_reordered_months_raise(self):
        with self.assertRaises(ValueError) as caught:
            validate_calendar_months(
                [(2026, 2), (2026, 1), (2025, 12)], self.MANIFEST
            )
        self.assertIn("order", str(caught.exception).lower())

    def test_wrong_month_count_raises(self):
        with self.assertRaises(ValueError):
            validate_calendar_months([(2026, 1), (2026, 2)], self.MANIFEST)

    def test_absent_manifest_is_not_an_error(self):
        validate_calendar_months([(2026, 1)], None)
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_build_load_inputs -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand.tools'`.

- [ ] **Step 3: Create the package and the module**

Create `proforma_thailand/tools/__init__.py` as an empty file.

Create `proforma_thailand/tools/build_load_inputs.py`:

```python
"""Regenerate the committed Thailand load inputs from the source workbook.

The load CSV is a bare load_kw column with no timestamps, so nothing in the
repo could previously prove which months it holds or in what order. This script
regenerates the CSV and the holiday list, and writes a manifest recording the
month order, the row count per month and the SHA-256 of the source workbook, so
a case.json can be checked against the data it claims to describe.

Usage:
    python -m proforma_thailand.tools.build_load_inputs \\
        --source "<path to ROFU Thailand 15-Minute Interval Data.xlsm>" \\
        --calendar-months 2026-01,2026-02,2026-03,2026-04,2026-05,2026-06,\\
2025-07,2025-08,2025-09,2025-10,2025-11,2025-12
"""

import argparse
import hashlib
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOAD_CSV = DATA_DIR / "rofu_load_15min.csv"
MANIFEST = DATA_DIR / "load_manifest.json"


def build_manifest(calendar_year_months, rows_per_month, source_sha256):
    """Self-describing record of what the committed CSV actually contains."""
    return {
        "calendar_year_months": [list(pair) for pair in calendar_year_months],
        "rows_per_month": list(rows_per_month),
        "total_rows": sum(rows_per_month),
        "source_sha256": source_sha256,
    }


def validate_calendar_months(calendar_months, manifest):
    """Raise when a case claims a month order the committed data does not have.

    Only the row count was checked before, so swapping two months left the load
    silently misaligned against the tariff with no error anywhere.
    """
    if not manifest:
        return
    expected = [tuple(pair) for pair in manifest["calendar_year_months"]]
    actual = [tuple(pair) for pair in calendar_months]
    if actual != expected:
        raise ValueError(
            "calendar_year_months does not match the committed load data. "
            "The CSV is in the order {}, the case asks for {}. Month order "
            "determines which tariff month each interval is billed under.".format(
                expected, actual
            )
        )


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True,
                        help="Path to the ROFU 15-minute interval .xlsm.")
    parser.add_argument("--calendar-months", required=True,
                        help="Comma-separated YYYY-MM in the order the year is assembled.")
    args = parser.parse_args(argv)

    from proforma_thailand.load_profile import build_calendar_year, extract_intervals

    calendar_months = [
        (int(token.split("-")[0]), int(token.split("-")[1]))
        for token in args.calendar_months.split(",")
        if token.strip()
    ]

    intervals = extract_intervals(args.source)
    loads, rows_per_month = build_calendar_year(intervals, calendar_months)

    LOAD_CSV.write_text(
        "load_kw\n" + "\n".join("{:g}".format(value) for value in loads) + "\n",
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps(
            build_manifest(calendar_months, rows_per_month, sha256_of(args.source)),
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print("Wrote {} rows to {}".format(len(loads), LOAD_CSV))
    print("Wrote manifest to {}".format(MANIFEST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_build_load_inputs -v`

Expected: 6 tests PASS.

- [ ] **Step 5: Check `build_calendar_year`'s return shape**

Run:

```bash
./.venv/Scripts/python.exe -c "
import inspect
from proforma_thailand import load_profile
print(inspect.signature(load_profile.build_calendar_year))
print(inspect.getsource(load_profile.build_calendar_year)[-600:])
"
```

If `build_calendar_year` returns only the loads list and not a `(loads, rows_per_month)` tuple, change the script to compute `rows_per_month` itself from `_days_in_month(year, month) * 96` for each entry in `calendar_months`, and leave `load_profile.py` untouched. Do not change an existing return shape that other callers depend on.

- [ ] **Step 6: Generate the manifest for the committed CSV**

The source workbook lives outside the repo. Generate the manifest from the committed data plus the known month order:

```bash
./.venv/Scripts/python.exe -c "
import json
from pathlib import Path
from proforma_thailand.load_profile import _days_in_month
from proforma_thailand.tools.build_load_inputs import build_manifest, MANIFEST
months = [(2026,1),(2026,2),(2026,3),(2026,4),(2026,5),(2026,6),
          (2025,7),(2025,8),(2025,9),(2025,10),(2025,11),(2025,12)]
rows = [_days_in_month(y, m) * 96 for y, m in months]
csv_rows = sum(1 for _ in open('proforma_thailand/data/rofu_load_15min.csv', encoding='utf-8')) - 1
assert sum(rows) == csv_rows, (sum(rows), csv_rows)
manifest = build_manifest(months, rows, 'not-recorded: manifest backfilled from the committed CSV, source workbook lives outside the repo')
MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('total rows', manifest['total_rows'])
"
```

Expected: `total rows 35040`, and the assertion passes. A mismatch means the committed CSV does not hold the month order the cases claim, which is a finding to report before continuing.

- [ ] **Step 7: Validate the month order in the case builder**

In `proforma_thailand/case_builder.py`, add the import:

```python
from proforma_thailand.tools.build_load_inputs import validate_calendar_months
```

and immediately after `calendar_months` is built:

```python
    # The CSV carries no timestamps, so only the manifest can say which months
    # it holds and in what order. Without this, swapping two months bills the
    # load under the wrong tariff month with no error.
    manifest_path = Path("proforma_thailand/data/load_manifest.json")
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists() else None
    )
    validate_calendar_months(calendar_months, manifest)
```

- [ ] **Step 8: Prove the guard catches a reordering**

```bash
./.venv/Scripts/python.exe -c "
import json
from proforma_thailand.case_builder import build_thailand_case
config = json.load(open('proforma_thailand/cases/rts/case.json', encoding='utf-8'))
months = config['load_profile']['calendar_year_months']
months[0], months[1] = months[1], months[0]
try:
    build_thailand_case(config)
except ValueError as error:
    print('caught as expected:', str(error)[:90])
else:
    raise SystemExit('FAIL: reordering was not caught')
"
```

Expected: `caught as expected: calendar_year_months does not match ...`.

- [ ] **Step 9: Run the suite and commit**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
git add proforma_thailand/tools/ proforma_thailand/data/load_manifest.json proforma_thailand/case_builder.py proforma_thailand/tests/test_build_load_inputs.py
git commit -m "Make the load inputs regenerable and check the month order"
```

---

### Task 13: A direct-ownership workbook stops showing ESCO contract terms

`xlsx_builder.py:412` renders "ESCO Energy Price" and "Demand Savings Share to ESCO" on every non-DPPA case, and line 420 heads the returns block "Developer (Seller) Returns". On a factory self-investing in its own roof there is no ESCO, no seller and no contract. The dispatch column header "Hour" is also wrong at 15-minute resolution, where it is numbered 1 to 35040.

**Files:**
- Modify: `proforma_vietnam/country_profile.py`
- Modify: `proforma_vietnam/xlsx_builder.py`
- Test: `proforma_vietnam/tests/test_country_profile.py`
- Test: `proforma_thailand/tests/test_report.py`

**Interfaces:**
- Produces: three new `CountryProfile` fields, all defaulting to today's Vietnam values: `shows_esco_contract_terms: bool = True`, `returns_section_label: str = "Developer (Seller) Returns"`, `dispatch_row_label: str = "Hour"`.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_country_profile.py`:

```python
class DirectOwnershipPresentationTests(unittest.TestCase):

    def test_vietnam_keeps_the_esco_presentation(self):
        self.assertTrue(VIETNAM_PROFILE.shows_esco_contract_terms)
        self.assertEqual(
            VIETNAM_PROFILE.returns_section_label, "Developer (Seller) Returns"
        )
        self.assertEqual(VIETNAM_PROFILE.dispatch_row_label, "Hour")

    def test_thailand_presents_as_direct_ownership(self):
        self.assertFalse(THAILAND_PROFILE.shows_esco_contract_terms)
        self.assertEqual(THAILAND_PROFILE.returns_section_label, "Owner Returns")
        self.assertEqual(THAILAND_PROFILE.dispatch_row_label, "Interval")
```

Append to `proforma_thailand/tests/test_report.py`, inside the existing provenance test class or as a new one:

```python
class NoEscoLanguageTests(TestCase):

    def test_direct_ownership_workbook_has_no_esco_contract_rows(self):
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for value in row:
                    if isinstance(value, str):
                        self.assertNotIn("ESCO Energy Price", value)
                        self.assertNotIn("Demand Savings Share to ESCO", value)
                        self.assertNotIn("Developer (Seller) Returns", value)
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_country_profile.DirectOwnershipPresentationTests -v
./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report.NoEscoLanguageTests -v
```

Expected: the first fails with `AttributeError: 'CountryProfile' object has no attribute 'shows_esco_contract_terms'`; the second fails on an `ESCO Energy Price` row.

- [ ] **Step 3: Add the profile fields**

In `proforma_vietnam/country_profile.py`, add to the `CountryProfile` dataclass:

```python
    shows_esco_contract_terms: bool = True
    returns_section_label: str = "Developer (Seller) Returns"
    dispatch_row_label: str = "Hour"
```

and to `THAILAND_PROFILE`:

```python
    shows_esco_contract_terms=False,
    returns_section_label="Owner Returns",
    dispatch_row_label="Interval",
```

- [ ] **Step 4: Honour them in the builder**

In `proforma_vietnam/xlsx_builder.py`, replace the `else` branch at line 411:

```python
    elif profile.shows_esco_contract_terms:
        terms.extend([
            ("ESCO Energy Price (fraction of {} tariff)".format(profile.utility_label), assumptions.get("esco_energy_discount_fraction"), FORMAT_PERCENT, None),
            ("Demand Savings Share to ESCO", assumptions.get("demand_savings_esco_share"), FORMAT_PERCENT, None),
        ])
```

At line 420, replace the literal header:

```python
    _write_section_header(worksheet, row, profile.returns_section_label, 4)
```

At lines 19 and 118, the `("Hour", "hour")` column tuples are module-level constants. Leave the constants alone and substitute at the point they are written into the sheet: find where the header text is written from those tuples and replace the `"Hour"` label with `profile.dispatch_row_label` when the header being written equals `"Hour"`. Read the surrounding function first; if the constants are consumed in more than one place, add a small helper in `xlsx_builder.py`:

```python
def _dispatch_headers(columns, profile):
    """Swap the row-unit header for the profile's, leaving other columns alone."""
    return [
        (profile.dispatch_row_label if label == "Hour" else label, key)
        for label, key in columns
    ]
```

and call it where the column list is turned into headers.

- [ ] **Step 5: Also fix the section header on a direct-ownership case**

If `_write_section_header(worksheet, row, "Contract Terms", 4)` at line 394 renders an empty block once the ESCO rows are gone, guard the whole block so a case with no DPPA config and no ESCO terms writes neither the header nor an empty table. Confirm by opening the generated Thailand workbook in Step 7.

- [ ] **Step 6: Run all three suites**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
```

Expected: all pass. `proforma_vietnam/tests/test_xlsx_builder.py:302` asserts the header is `"Hour"`; it must still pass, because Vietnam's profile default is unchanged.

- [ ] **Step 7: Run the Vietnam gate**

Run the gate command from Global Constraints.

Expected: `TOTAL DIFFS 0`. Note that Task 11 already narrowed the ignore rules, so this gate now sees subtitle rows. A diff means a default was changed rather than added.

- [ ] **Step 8: Commit**

```bash
git add proforma_vietnam/country_profile.py proforma_vietnam/xlsx_builder.py proforma_vietnam/tests/test_country_profile.py proforma_thailand/tests/test_report.py
git commit -m "Present a direct-ownership case without ESCO contract language"
```

---

### Task 14: Scope 2 avoided emissions

Keen is a footwear brand with supply-chain decarbonisation targets, so avoided emissions are a first-class output. REopt's own emissions outputs are all zero here because AVERT, Cambium and EASIUR are US datasets, and they must stay out of the workbook.

**Files:**
- Create: `proforma_thailand/emissions.py`
- Create: `proforma_thailand/tests/test_emissions.py`
- Modify: `proforma_thailand/report.py`
- Modify: `proforma_thailand/run_case.py`
- Modify: `proforma_vietnam/audit_sheets.py`

**Interfaces:**
- Produces: `annual_avoided_tco2e(annual_load_kwh, annual_grid_kwh, grid_emission_factor_kg_per_kwh) -> float` and `lifetime_avoided_tco2e(annual_tco2e, project_years, pv_degradation_rate) -> float`.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_emissions.py`:

```python
"""Scope 2 avoided emissions, computed in-house from a cited Thai grid factor."""

from unittest import TestCase

from proforma_thailand.emissions import (
    annual_avoided_tco2e,
    lifetime_avoided_tco2e,
)


class AnnualAvoidedTests(TestCase):

    def test_avoided_energy_times_factor_in_tonnes(self):
        # 2,000,000 kWh avoided at 0.5 kg/kWh is 1,000,000 kg, so 1,000 tonnes.
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 5_000_000.0, 0.5), 1000.0
        )

    def test_no_offset_avoids_nothing(self):
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 7_000_000.0, 0.5), 0.0
        )

    def test_grid_above_load_cannot_produce_a_negative_claim(self):
        """Battery grid-charging can push grid import above load. Claim zero, never less."""
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 7_200_000.0, 0.5), 0.0
        )

    def test_missing_factor_yields_zero(self):
        self.assertAlmostEqual(
            annual_avoided_tco2e(7_000_000.0, 5_000_000.0, None), 0.0
        )


class LifetimeAvoidedTests(TestCase):

    def test_no_degradation_is_a_flat_multiple(self):
        self.assertAlmostEqual(lifetime_avoided_tco2e(100.0, 3, 0.0), 300.0)

    def test_degradation_reduces_later_years(self):
        # Year 1 = 100, year 2 = 99, year 3 = 98.01.
        self.assertAlmostEqual(
            lifetime_avoided_tco2e(100.0, 3, 0.01), 297.01, places=2
        )

    def test_zero_years_avoids_nothing(self):
        self.assertAlmostEqual(lifetime_avoided_tco2e(100.0, 0, 0.01), 0.0)
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_emissions -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand.emissions'`.

- [ ] **Step 3: Write the module**

Create `proforma_thailand/emissions.py`:

```python
"""Scope 2 avoided emissions for the Thailand cases.

REopt's emissions outputs are all zero here because AVERT, Cambium and EASIUR
are US datasets with no Thailand coverage. They stay out of the workbook. This
is an Allotrope calculation from a cited Thai grid emission factor, and is
labelled as such so the two can never be confused.

The basis is avoided grid IMPORT, not PV generation. Curtailed energy displaces
nothing and must not be claimed, and any energy the battery draws from the grid
is grid energy. Avoided import is the same quantity the report already presents
as the grid offset, so the emissions figure and the offset figure cannot drift.
"""


def annual_avoided_tco2e(annual_load_kwh, annual_grid_kwh,
                         grid_emission_factor_kg_per_kwh):
    """Year-one avoided Scope 2 emissions in tonnes CO2e."""
    if not grid_emission_factor_kg_per_kwh:
        return 0.0
    avoided_kwh = max(0.0, (annual_load_kwh or 0.0) - (annual_grid_kwh or 0.0))
    return avoided_kwh * grid_emission_factor_kg_per_kwh / 1000.0


def lifetime_avoided_tco2e(annual_tco2e, project_years, pv_degradation_rate):
    """Avoided emissions across the analysis period, degrading the array yearly.

    The emission factor is held constant. The Thai grid is expected to
    decarbonise under the PDP, which would reduce avoided emissions over time,
    so a constant factor is the optimistic end of the range and must be
    disclosed as an assumption.
    """
    total = 0.0
    for year in range(int(project_years or 0)):
        total += (annual_tco2e or 0.0) * (1.0 - (pv_degradation_rate or 0.0)) ** year
    return total
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_emissions -v`

Expected: 7 tests PASS.

- [ ] **Step 5: Add the emission factor default**

In `proforma_thailand/defaults/thailand_defaults.json`, add a top-level `emissions` block:

```json
  "emissions": {
    "grid_emission_factor_kg_co2e_per_kwh": {"value": 0.4999, "source": "PLACEHOLDER - pending Task 15 research",
      "note": "Thailand national grid emission factor. Must be replaced in Task 15 with a cited TGO figure recording vintage year and whether it is combined-margin, operating-margin or average"},
    "grid_emission_factor_vintage": {"value": "pending", "source": "PLACEHOLDER - pending Task 15 research"}
  },
```

and expose it in `proforma_thailand/defaults/__init__.py`:

```python
EMISSIONS_DEFAULTS = THAILAND_DEFAULTS["emissions"]
```

Add `EMISSIONS_DEFAULTS` to the `placeholder_keys` scan by including it in the tuple of blocks iterated there.

- [ ] **Step 6: Compute and report it**

In `proforma_thailand/report.py`, inside `build_thailand_report`, add to the `extras` dict:

```python
    load_outputs = outputs.get("ElectricLoad") or {}
    utility_outputs = outputs.get("ElectricUtility") or {}
    emission_factor = value_of(
        EMISSIONS_DEFAULTS, "grid_emission_factor_kg_co2e_per_kwh"
    )
    annual_tco2e = annual_avoided_tco2e(
        load_outputs.get("annual_calculated_kwh"),
        utility_outputs.get("annual_energy_supplied_kwh"),
        emission_factor,
    )
```

and then, in the `extras` literal:

```python
        "annual_avoided_tco2e": annual_tco2e,
        "lifetime_avoided_tco2e": lifetime_avoided_tco2e(
            annual_tco2e,
            assumptions.get("project_years") or 25,
            assumptions.get("pv_degradation_rate") or 0.0,
        ),
        "grid_emission_factor_kg_co2e_per_kwh": emission_factor,
```

Add the matching imports at the top of `report.py`.

Also add to `workbook_assumptions` so the figures reach the sheet:

```python
    workbook_assumptions["annual_avoided_tco2e"] = annual_tco2e
    workbook_assumptions["grid_emission_factor_kg_co2e_per_kwh"] = emission_factor
    workbook_assumptions["grid_emission_factor_source"] = EMISSIONS_DEFAULTS[
        "grid_emission_factor_kg_co2e_per_kwh"
    ]["source"]
```

The `source` field, not just the value, must reach the sheet. A grid emission factor with no cited authority and vintage is unusable for corporate reporting, and Task 15 replaces this string with the TGO citation.

- [ ] **Step 7: Render the rows**

In the Step 4 assumptions writer in `proforma_vietnam/audit_sheets.py`, before the `placeholder_keys` block:

```python
    # Gated on the key, so Vietnam workbooks, which never set it, are unchanged.
    avoided = (assumptions or {}).get("annual_avoided_tco2e")
    if avoided is not None:
        section("Avoided Emissions (Scope 2)")
        entry(
            "Grid emission factor",
            (assumptions or {}).get("grid_emission_factor_kg_co2e_per_kwh"),
            unit="kg CO2e/kWh",
            source=(assumptions or {}).get(
                "grid_emission_factor_source", "See Assumptions"
            ),
        )
        entry(
            "Avoided emissions, year 1",
            avoided,
            unit="tonnes CO2e",
            source="Allotrope calculation from avoided grid import. Not a REopt output.",
        )
```

- [ ] **Step 8: Add it to the run summary**

In `summarize_results` in `proforma_thailand/run_case.py`, add:

```python
        "annual_avoided_tco2e": float(extras.get("annual_avoided_tco2e") or 0.0),
        "lifetime_avoided_tco2e": float(extras.get("lifetime_avoided_tco2e") or 0.0),
```

- [ ] **Step 9: Verify against the existing run and check the tie-out**

```bash
./.venv/Scripts/python.exe -c "
import json
from proforma_thailand.report import build_thailand_report
results = json.load(open('proforma_thailand/cases/rts/results.json', encoding='utf-8'))
assumptions = json.load(open('proforma_thailand/cases/rts/assumptions.json', encoding='utf-8'))
_, extras = build_thailand_report(results, assumptions)
summary = json.load(open('proforma_thailand/cases/rts/summary.json', encoding='utf-8'))
load = summary['annual_load_kwh']
offset = summary['grid_offset_fraction']
expected = load * offset * extras['grid_emission_factor_kg_co2e_per_kwh'] / 1000.0
print('annual tCO2e   : %.1f' % extras['annual_avoided_tco2e'])
print('from offset    : %.1f' % expected)
print('lifetime tCO2e : %.1f' % extras['lifetime_avoided_tco2e'])
"
```

Expected: the first two numbers agree to within rounding. They are two routes to the same quantity, which is the point of defining the basis as avoided import. A disagreement means the wrong output key was read.

- [ ] **Step 10: Confirm REopt emissions stay out**

```bash
./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report -v
```

Expected: the existing provenance test class still passes.

- [ ] **Step 11: Run the suites and the gate, then commit**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
```

Then run the gate command from Global Constraints. Expected `TOTAL DIFFS 0`.

```bash
git add proforma_thailand/emissions.py proforma_thailand/tests/test_emissions.py proforma_thailand/report.py proforma_thailand/run_case.py proforma_thailand/defaults/ proforma_vietnam/audit_sheets.py
git commit -m "Compute Scope 2 avoided emissions from a Thai grid factor"
```

---

### Task 15: Re-benchmark the Thailand cost and emissions inputs

Every cost placeholder was set as a planning figure. They must carry Thailand-applicable citations before a client memo quotes returns computed from them. This task is research plus a data edit; it writes no logic.

**Files:**
- Modify: `proforma_thailand/defaults/thailand_defaults.json`
- Create: `docs/superpowers/notes/2026-09-05-thailand-cost-benchmarks.md`
- Test: `proforma_thailand/tests/test_thailand_defaults.py`

**Interfaces:**
- Produces: updated `value` and `source` fields. No key names change, so no code changes.

- [ ] **Step 1: Record the current values**

```bash
./.venv/Scripts/python.exe -c "
import json
d = json.load(open('proforma_thailand/defaults/thailand_defaults.json', encoding='utf-8'))
for block in ('financial', 'site', 'emissions'):
    for key, entry in d.get(block, {}).items():
        print('%-46s %-14s %s' % (key, entry['value'], entry['source'][:44]))
"
```

Save this output. It is the before-and-after record for the note.

- [ ] **Step 2: Research each input**

Find a Thailand-applicable, citable figure for each of:

| Key | Current | What to find |
|---|---|---|
| `pv_installed_cost_per_kw` | 700.0 | Thai C&I rooftop EPC, USD/kWp, 1-2 MWp scale |
| `bess_installed_cost_per_kw` | 300.0 | Thai or SE Asia C&I BESS power cost |
| `bess_installed_cost_per_kwh` | 250.0 | Thai or SE Asia C&I BESS energy cost |
| `annual_om_per_kw` | 12.0 | Thai rooftop O&M, USD/kWp-yr |
| `insurance_rate_fraction` | 0.005 | All-risk premium as a fraction of capex |
| `inverter_replacement_fraction_of_pv_capex` | 0.10 | Inverter share of PV capex |
| `bess_om_fraction_of_installed_cost` | 0.01 | BESS O&M as a fraction of capex |
| `pea_tariff_escalation_rate` | 0.03 | PEA retail tariff trend |
| `discount_rate` | 0.08 | Thai corporate WACC or hurdle rate |
| `debt_interest_rate` | 0.06 | Thai commercial lending rate |
| `grid_emission_factor_kg_co2e_per_kwh` | 0.4999 | TGO national grid factor |

For the grid emission factor specifically: TGO is the primary authority. Record the vintage year and whether the figure is combined-margin, operating-margin or average, because those differ materially and an auditor will ask which was used. Cross-check against the IFI/IGES harmonised dataset and the IEA. If sources disagree beyond a narrow band, carry the most conservative and say so.

The ENS SolarStorage form in `05_Vendor_Market/` is a **comparator, not a source**: it is configured for a Vietnam site at latitude 11.09 with EVN tariffs, VND and 10 percent VAT. Cite it as a comparator only, never as a Thailand figure.

- [ ] **Step 3: Write the research note**

Create `docs/superpowers/notes/2026-09-05-thailand-cost-benchmarks.md` with one section per input: the value chosen, the source with enough detail to re-find it, the date accessed, the range the sources span, and why this value was picked from that range. Where no Thailand-applicable source exists, say so explicitly and leave the entry marked with the placeholder marker.

- [ ] **Step 4: Update the defaults**

Edit `proforma_thailand/defaults/thailand_defaults.json`. For each researched input, set the `value` and replace the `source` with the citation. **Leave the placeholder marker in place for anything still unconfirmed** - the marker is what the Task 7 guard checks for, and a workbook with no marker anywhere will now refuse to write.

- [ ] **Step 5: Add a test that the researched keys carry real sources**

Append to `proforma_thailand/tests/test_thailand_defaults.py`:

```python
class BenchmarkedSourcesTests(TestCase):
    """Inputs researched in Task 15 must not still claim to be placeholders."""

    RESEARCHED = (
        "pv_installed_cost_per_kw",
        "annual_om_per_kw",
        "insurance_rate_fraction",
    )

    def test_researched_financial_inputs_cite_a_source(self):
        for key in self.RESEARCHED:
            with self.subTest(key=key):
                source = FINANCIAL_DEFAULTS[key]["source"]
                self.assertNotEqual(source, PLACEHOLDER_MARKER)
                self.assertGreater(len(source), 20)

    def test_grid_emission_factor_records_its_vintage(self):
        vintage = EMISSIONS_DEFAULTS["grid_emission_factor_vintage"]["value"]
        self.assertNotEqual(vintage, "pending")
```

Trim `RESEARCHED` to only the keys actually resolved in Step 2. Do not list a key you could not find a Thailand source for; leave those marked and out of this tuple.

- [ ] **Step 6: Run the suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v`

Expected: all pass.

- [ ] **Step 7: Show the before-and-after**

Re-run the Step 1 command and print both tables side by side in the commit message body, so the change in every number is on the record.

- [ ] **Step 8: Commit**

```bash
git add proforma_thailand/defaults/thailand_defaults.json proforma_thailand/tests/test_thailand_defaults.py docs/superpowers/notes/2026-09-05-thailand-cost-benchmarks.md
git commit -m "Re-benchmark the Thailand cost and emission inputs"
```

---

### Task 16: Build the case tree

**Files:**
- Create: `outputs/thailand_case/rofu_thailand/case_1/case.json` through `case_6/case.json`
- Create: `outputs/thailand_case/rofu_thailand/CASE_JSON_INPUT_GUIDE.md`
- Test: `proforma_thailand/tests/test_case_builder.py`

**Interfaces:**
- Consumes: `build_thailand_case(case_config)` from `proforma_thailand/case_builder.py`.
- Produces: six case directories, each buildable with `--dry-run`.

- [ ] **Step 1: Write the failing test**

Append to `proforma_thailand/tests/test_case_builder.py`:

```python
class RofuCaseTreeTests(TestCase):
    """Every committed Rofu case must build without contacting the solver."""

    ROOT = Path("outputs/thailand_case/rofu_thailand")
    EXPECTED_PV_CAPS = {
        "case_1": 1685.0,
        "case_2": 1895.0,
        "case_3": 2106.0,
        "case_4": 3230.0,
        "case_5": 1685.0,
        "case_6": 3230.0,
    }

    def test_all_six_cases_declare_the_expected_pv_cap(self):
        for name, expected in self.EXPECTED_PV_CAPS.items():
            with self.subTest(case=name):
                config = json.loads(
                    (self.ROOT / name / "case.json").read_text(encoding="utf-8")
                )
                self.assertEqual(
                    config["technologies"]["pv"]["max_kw"], expected
                )

    def test_only_the_storage_cases_declare_storage(self):
        for name in ("case_1", "case_2", "case_3", "case_4"):
            with self.subTest(case=name):
                config = json.loads(
                    (self.ROOT / name / "case.json").read_text(encoding="utf-8")
                )
                storage = config["technologies"].get("storage", {})
                self.assertFalse(storage.get("max_kw"))
                self.assertFalse(storage.get("max_kwh"))
        for name in ("case_5", "case_6"):
            with self.subTest(case=name):
                config = json.loads(
                    (self.ROOT / name / "case.json").read_text(encoding="utf-8")
                )
                self.assertGreater(
                    config["technologies"]["storage"]["max_kw"], 0
                )
```

Add `import json` and `from pathlib import Path` if absent.

- [ ] **Step 2: Run the test and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder.RofuCaseTreeTests -v`

Expected: FAIL with `FileNotFoundError` for `case_1/case.json`.

- [ ] **Step 3: Create case_1 through case_4**

Create each directory and write `case.json`. `case_1`:

```json
{
  "case_name": "Rofu Thailand RTS - conservative roof (1,685 kWp)",
  "site": {"latitude": 15.209427, "longitude": 102.475687},
  "load_profile": {
    "path": "proforma_thailand/data/rofu_load_15min.csv",
    "all_off_peak_dates_path": "proforma_thailand/data/rofu_all_off_peak_dates.json",
    "calendar_year_months": [[2026,1],[2026,2],[2026,3],[2026,4],[2026,5],[2026,6],
                             [2025,7],[2025,8],[2025,9],[2025,10],[2025,11],[2025,12]]
  },
  "tariff": {"voltage_level": "22_33kv", "exchange_rate_thb_per_usd": 32.5},
  "technologies": {
    "pv": {"max_kw": 1685.0},
    "storage": {"max_kw": 0, "max_kwh": 0}
  },
  "direct_ownership": {"enabled": true}
}
```

`case_2` is identical with `"max_kw": 1895.0` and case name `"Rofu Thailand RTS - mid roof (1,895 kWp)"`.

`case_3` is identical with `"max_kw": 2106.0` and case name `"Rofu Thailand RTS - upper roof (2,106 kWp)"`.

`case_4` is identical with `"max_kw": 3230.0` and case name `"Rofu Thailand RTS - roof unconstrained (3,230 kWp cap)"`.

Do **not** set `installed_cost_per_kw` in any case. Leaving it out makes the case take the Task 15 researched default, so all six cases price consistently and a later re-benchmark does not silently apply to some cases and not others.

- [ ] **Step 4: Create case_5 and case_6**

`case_5` matches `case_1` but with:

```json
    "pv": {"max_kw": 1685.0},
    "storage": {"max_kw": 2000, "max_kwh": 8000}
```

and case name `"Rofu Thailand RTS+BESS - conservative roof, optimizer-sized storage"`.

`case_6` matches `case_5` but with `"max_kw": 3230.0` on the PV block and case name `"Rofu Thailand RTS+BESS - roof unconstrained, optimizer-sized storage"`.

The storage `max_kw` and `max_kwh` here are upper bounds the optimizer sizes beneath, not forced sizes. They are set generously so the bound does not bind; if a run returns storage at exactly 2,000 kW or 8,000 kWh, the bound DID bind and must be raised and the case re-run.

- [ ] **Step 5: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder.RofuCaseTreeTests -v`

Expected: 2 tests PASS.

- [ ] **Step 6: Dry-run every case**

```bash
for case in 1 2 3 4 5 6; do
  echo "=== case_$case ==="
  ./.venv/Scripts/python.exe -m proforma_thailand.run_case \
    --case "outputs/thailand_case/rofu_thailand/case_$case/case.json" \
    --dry-run || echo "FAILED case_$case"
done
```

Expected: six successes, each writing `payload.json` and `assumptions.json` into its own directory. A failure here is a case-definition error, not a solver problem.

- [ ] **Step 7: Confirm the payloads differ only where intended**

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

Expected: six rows. Every row must show `ITC 0.0` and `MACRS 0`. A non-zero incentive on any case is the C2 critical returning and must be fixed before any run.

- [ ] **Step 8: Write the input guide**

Create `outputs/thailand_case/rofu_thailand/CASE_JSON_INPUT_GUIDE.md` documenting every key a Thailand `case.json` accepts: the `site` block including the optional `tilt`, the `load_profile` block and its manifest-validated `calendar_year_months`, the `tariff` block, the `technologies.pv` and `technologies.storage` blocks with which keys fall back to which default, and `direct_ownership`. State for each whether omitting it takes a Thailand default or a REopt US default. Include the roof-area derivation table from the spec so the four PV caps are traceable.

- [ ] **Step 9: Commit**

```bash
git add outputs/thailand_case/ proforma_thailand/tests/test_case_builder.py
git commit -m "Define the six Rofu Thailand cases"
```

---

### Task 17: Run all six cases against the live solver

**Files:**
- Modify: `outputs/thailand_case/rofu_thailand/case_{1..6}/` - run artifacts

**Interfaces:**
- Consumes: the six `case.json` files from Task 16.
- Produces: `results.json`, `summary.json` and `thailand_report_<uuid>.xlsx` per case.

- [ ] **Step 1: Bring the stack up and confirm it is healthy**

```bash
docker-compose up -d
docker ps --format "{{.Names}}\t{{.Status}}"
```

Expected: `reopt_api-django-1`, the Celery worker, the Julia server, Postgres and Redis all up.

- [ ] **Step 2: Confirm the API answers**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/v3/job/
```

Expected: a 4xx status, not a connection error. A connection error means the stack is not ready; wait and retry rather than proceeding.

- [ ] **Step 3: Run the Django-side Thailand tariff tests**

```bash
docker exec reopt_api-django-1 python manage.py test reoptjl.test.test_thailand_tariff -v 2
```

Expected: 14 tests pass.

- [ ] **Step 4: Run all six cases**

```bash
for case in 1 2 3 4 5 6; do
  echo "=== case_$case ==="
  ./.venv/Scripts/python.exe -m proforma_thailand.run_case \
    --case "outputs/thailand_case/rofu_thailand/case_$case/case.json" \
    || echo "FAILED case_$case"
done
```

Expected: six runs reaching `optimal`. Each writes its own workbook. This takes time; do not shorten `--max-polls`.

- [ ] **Step 5: Read the summaries**

```bash
./.venv/Scripts/python.exe -c "
import json
from pathlib import Path
root = Path('outputs/thailand_case/rofu_thailand')
print('%-8s %9s %9s %10s %8s %10s' % ('case','PV kW','BESS kW','BESS kWh','offset','tCO2e/yr'))
for name in ['case_%d' % i for i in range(1, 7)]:
    s = json.loads((root / name / 'summary.json').read_text(encoding='utf-8'))
    print('%-8s %9.1f %9.1f %10.1f %7.1f%% %10.0f' % (
        name, s['pv_kw'], s['bess_kw'], s['bess_kwh'],
        s['grid_offset_fraction'] * 100, s.get('annual_avoided_tco2e', 0)))
"
```

Record this table. It is the core of the memo.

- [ ] **Step 6: Check whether any bound bound**

Confirm that `case_5` and `case_6` did not return storage at exactly 2,000 kW or 8,000 kWh, and that `case_4` and `case_6` did not return PV at exactly 3,230 kW. If any did, the bound was binding rather than the economics, so raise that bound and re-run that case before reading anything into the result.

For `case_1` through `case_3` the PV cap is a real roof constraint, so pinning at the cap there is a finding, not a problem.

- [ ] **Step 7: Sanity-check the physics**

```bash
./.venv/Scripts/python.exe -c "
import json
from pathlib import Path
root = Path('outputs/thailand_case/rofu_thailand')
for name in ['case_%d' % i for i in range(1, 7)]:
    r = json.loads((root / name / 'results.json').read_text(encoding='utf-8'))
    pv = r['outputs'].get('PV') or {}
    if isinstance(pv, list): pv = pv[0] if pv else {}
    size = pv.get('size_kw') or 0
    produced = pv.get('annual_energy_produced_kwh') or 0
    yield_kwh = produced / size if size else 0
    print('%-8s specific yield %7.0f kWh/kWp  (PR %.3f at 1,948 kWh/m2 GHI)' % (
        name, yield_kwh, yield_kwh / 1948.0))
"
```

Expected: specific yield around 1,300 to 1,500 kWh/kWp for Nakhon Ratchasima, and a performance ratio between 0.70 and 0.85. A PR above 1.0 is physically impossible and means the 4x energy bug has returned. Stop and report if so.

- [ ] **Step 8: Confirm each workbook was written and passed the guard**

```bash
ls -1 outputs/thailand_case/rofu_thailand/case_*/thailand_report_*.xlsx
```

Expected: six files. The Task 7 guard runs before each save, so their existence proves the placeholder disclosure survived.

- [ ] **Step 9: Commit**

```bash
git add outputs/thailand_case/
git commit -m "Run the six Rofu Thailand cases against the live solver"
```

---

### Task 18: Write the client memo

**Files:**
- Create: `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md`

**Interfaces:**
- Consumes: the six `summary.json` files and workbooks from Task 17, and the research note from Task 15.

- [ ] **Step 1: Assemble the numbers**

```bash
./.venv/Scripts/python.exe -c "
import json
from pathlib import Path
root = Path('outputs/thailand_case/rofu_thailand')
for name in ['case_%d' % i for i in range(1, 7)]:
    s = json.loads((root / name / 'summary.json').read_text(encoding='utf-8'))
    c = json.loads((root / name / 'case.json').read_text(encoding='utf-8'))
    print(name, c['case_name'])
    print('   ', json.dumps(s, indent=6)[:900])
"
```

Also read the financial figures (equity IRR, project IRR, NPV, payback) from each workbook's Executive Summary sheet.

- [ ] **Step 2: Write the memo**

Create `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md` with these sections:

1. **Headline** - grid offset with and without storage, and Scope 2 tonnes avoided per year. This is what Lauren needs for the leadership update; put the two numbers in the first three lines.
2. **What we modelled** - site, tariff, load provenance and resolution, zero export, direct ownership.
3. **Solar sizing** - the roof-area derivation table, the four PV caps, what each returned, and where more PV stops paying. State plainly that cases 1 to 3 pin at their roof cap, so roof confirmation is the single highest-value open item.
4. **Storage** - what the optimizer built at each PV cap and why. If it is near zero, say so directly: a battery does not pay against PEA's tariff at these prices, and any contractor proposal including one should be read against that.
5. **Emissions** - annual and lifetime tCO2e, the factor with vintage and source, the constant-factor assumption, and the note that a market-based claim depends on Keen retaining the I-RECs.
6. **Financials** - equity IRR, project IRR, NPV and payback per case, with the cost basis and its citations.
7. **Information requests** - the specific items Ou must confirm: roof widths and pitch, the monthly kVAR maximum, and any EPC quotes in hand.

Rules for the memo:
- Every figure that rests on a provisional input carries an inline footnote naming the input and its status. No separate limitations annex.
- Footnote power factor as not computed, because the site kVAR maximum was never supplied.
- Footnote that the ERC generation licence and the Aor.6 building-modification permit are required but excluded, having no public fee schedule.
- State that EIA and IEE are genuinely not required below 5 MWp, so their zero cost is a finding rather than a gap.
- Do **not** quote any REopt emissions output. The Scope 2 figure is the Allotrope calculation and must be labelled as such.
- No em dash anywhere in the memo.

- [ ] **Step 3: Check every number against its source**

For each figure in the memo, confirm it against the `summary.json` or workbook it came from. Do not carry a number from an earlier draft or from this plan; the Task 15 re-benchmark changed the cost basis, so any figure predating it is stale.

- [ ] **Step 4: Check the memo's own rules**

```bash
grep -n "—" outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md && echo "FAIL: em dash found" || echo "OK: no em dash"
grep -niE "AVERT|Cambium|EASIUR" outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md && echo "FAIL: US emissions dataset referenced" || echo "OK: no US emissions dataset"
```

Expected: `OK` on both.

- [ ] **Step 5: Commit**

```bash
git add outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md
git commit -m "Write the Keen Thailand client memo"
```

---

## Final verification

- [ ] All three suites green:

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
docker exec reopt_api-django-1 python manage.py test reoptjl.test.test_thailand_tariff -v 2
```

- [ ] Vietnam gate at `TOTAL DIFFS 0` (command in Global Constraints).
- [ ] `git status` clean apart from the pre-existing untracked `outputs/vietnam_case/*.xlsx`.
- [ ] Six workbooks present under `outputs/thailand_case/rofu_thailand/case_*/`.
- [ ] No file under `reo/`, `outputs/vietnam_case/` or `baseline_workbooks/` modified:

```bash
git diff --name-only master...HEAD | grep -E "^(reo/|outputs/vietnam_case/|baseline_workbooks/)" && echo "FAIL: protected path touched" || echo "OK: protected paths untouched"
```
