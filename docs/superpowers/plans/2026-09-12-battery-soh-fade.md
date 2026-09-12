# Battery SOH Fade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the year-10 battery replacement a per-case option (default off), compute a battery state-of-health curve from the solved dispatch, derate the battery's share of the savings by that curve every year, and show the curve on a new "Battery SOH" sheet; then re-solve every case.

**Architecture:** The shared core `proforma_vietnam` drives both countries. A new pure module `battery_soh.py` replicates REopt.jl's daily SOH recurrence (h = 1); a new pure module `demand_charge.py` recomputes a year-1 demand charge from a purchase series so the battery's demand relief can be measured against a PV-only counterfactual. `esco_pro_forma` assembles one `battery_fade` dict from the REopt results and `cash_flow` applies it wherever PV degradation already applies, with the battery part on the SOH multiplier. The audit sheet's Excel formulas gain the same terms so the tie-out still holds; `xlsx_builder` adds the sheet.

**Tech Stack:** Python 3 (no Django needed for the proforma suites), openpyxl, unittest. Docker stack (django/celery/julia_api) for the re-solve.

**Spec:** `docs/superpowers/specs/2026-09-12-battery-soh-fade-design.md`

## Global Constraints

- Branch `battery-soh-fade`; never merge to master in this plan; no push.
- No em dash (U+2014) in generated report output (labels, notes, bullets).
- `./.venv/Scripts/python.exe` runs the proforma suites (no Django). Suites:
  `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v`,
  `... -s proforma_thailand/tests -t . -v`, `... -m unittest reoptjl.test.test_thailand_tariff -v`.
  Baseline counts before this plan: Vietnam 551, Thailand 143, tariff 14.
- Never modify anything under `reo/`; never touch the client `.xlsm` files;
  never `git add -f` `baseline_workbooks/`; never edit `.gitignore:139`.
- Placeholder marker text is exactly `PLACEHOLDER - pending Keen confirmation`.
- Untracked `outputs/vietnam_case/factory_a/case_*/vietnam_report_review*.xlsx`
  and the two locked old case_6 workbooks are never touched. Workbooks are
  selected by run uuid, never `sorted(glob)[-1]`.
- Thailand JSON defaults are edited at text level (no `json.dumps` rewrite).
- Bash heredocs containing apostrophes fail in this environment: write
  scripts with the Write tool, then run them.
- Workbooks without a battery must stay numerically identical (gate: 0 diffs).

---

### Task 1: Policy constants and Thailand defaults

**Files:**
- Modify: `proforma_vietnam/defaults/__init__.py:22-31`
- Modify: `proforma_thailand/defaults/thailand_defaults.json:8,17-20`
- Modify: `proforma_thailand/defaults/__init__.py:1-20` (imports), `:70-90`
- Test: `proforma_vietnam/tests/test_defaults.py` (append), `proforma_thailand/tests/test_thailand_defaults.py` (append)

**Interfaces:**
- Produces (from `proforma_vietnam.defaults`): `BESS_REPLACEMENT_ENABLED = False`, `BESS_REPLACEMENT_YEAR = 10`, `BESS_REPLACE_FRACTION_OF_INSTALL = 1.0`, `BESS_CYCLE_LIFE_EFC = 8000`, `BESS_END_OF_LIFE_SOH = 0.80`, `BESS_CALENDAR_FADE_COEFFICIENT = 1.16e-3`, `BESS_CALENDAR_FADE_EXPONENT = 0.428`.
- Produces (Thailand JSON `financial`): `bess_replacement_enabled.value == False`, `bess_cycle_life_efc.value == 8000`; `bess_replace_cost_per_kw/kwh` entries removed.

- [ ] **Step 1: Write the failing tests**

Append to `proforma_vietnam/tests/test_defaults.py` (keep every existing class):

```python
class BatteryAgeingPolicyTests(TestCase):

    def test_replacement_is_off_by_default_but_the_schedule_survives_for_opt_in(self):
        from proforma_vietnam import defaults
        self.assertFalse(defaults.BESS_REPLACEMENT_ENABLED)
        self.assertEqual(defaults.BESS_REPLACEMENT_YEAR, 10)
        self.assertEqual(defaults.BESS_REPLACE_FRACTION_OF_INSTALL, 1.0)

    def test_cycle_life_and_fade_coefficients(self):
        from proforma_vietnam import defaults
        self.assertEqual(defaults.BESS_CYCLE_LIFE_EFC, 8000)
        self.assertEqual(defaults.BESS_END_OF_LIFE_SOH, 0.80)
        self.assertAlmostEqual(defaults.BESS_CALENDAR_FADE_COEFFICIENT, 1.16e-3)
        self.assertAlmostEqual(defaults.BESS_CALENDAR_FADE_EXPONENT, 0.428)
```

Append to `proforma_thailand/tests/test_thailand_defaults.py`:

```python
class BatteryAgeingDefaultsTests(TestCase):

    def test_replacement_flag_and_cycle_life_match_the_shared_policy(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS
        from proforma_vietnam.defaults import BESS_REPLACEMENT_ENABLED, BESS_CYCLE_LIFE_EFC
        self.assertEqual(FINANCIAL_DEFAULTS["bess_replacement_enabled"]["value"], BESS_REPLACEMENT_ENABLED)
        self.assertEqual(FINANCIAL_DEFAULTS["bess_cycle_life_efc"]["value"], BESS_CYCLE_LIFE_EFC)
        self.assertIn("2026-09-12", FINANCIAL_DEFAULTS["bess_replacement_enabled"]["source"])

    def test_replacement_prices_are_no_longer_defaults(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS
        self.assertNotIn("bess_replace_cost_per_kw", FINANCIAL_DEFAULTS)
        self.assertNotIn("bess_replace_cost_per_kwh", FINANCIAL_DEFAULTS)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_defaults.BatteryAgeingPolicyTests proforma_thailand.tests.test_thailand_defaults.BatteryAgeingDefaultsTests -v`
Expected: FAIL (AttributeError / KeyError).

- [ ] **Step 3: Vietnam constants**

Replace lines 22-31 of `proforma_vietnam/defaults/__init__.py` with:

```python
# Equipment replacement and battery ageing policy shared by every country
# branch (rulings of 2026-09-11 and 2026-09-12). A country's JSON carries its
# own prices and provenance, but its horizon and schedule must agree with
# these or its defaults module refuses to import; that is what keeps the two
# branches from drifting.
PROJECT_YEARS = 20
# 2026-09-12: no scheduled battery replacement inside the horizon. A case may
# opt in through technologies.storage.replacement; the year and fraction below
# are then the defaults it inherits (whole system, storage inverter and pack).
BESS_REPLACEMENT_ENABLED = False
BESS_REPLACEMENT_YEAR = 10
BESS_REPLACE_FRACTION_OF_INSTALL = 1.0
PV_INVERTER_REPLACEMENT_YEAR = 11
PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX = 0.10
# Battery ageing carried by a state-of-health curve instead (battery_soh.py).
# Cycle life in the style of an LFP datasheet: equivalent full cycles to end
# of life. Calendar fade keeps the NREL coefficients REopt.jl v0.57.0 ships.
BESS_CYCLE_LIFE_EFC = 8000
BESS_END_OF_LIFE_SOH = 0.80
BESS_CALENDAR_FADE_COEFFICIENT = 1.16e-3
BESS_CALENDAR_FADE_EXPONENT = 0.428
```

- [ ] **Step 4: Thailand JSON, text-level**

In `proforma_thailand/defaults/thailand_defaults.json` replace the two `bess_replace_cost_per_kw` / `bess_replace_cost_per_kwh` entries (lines 17-20) with:

```json
    "bess_replacement_enabled": {"value": false, "source": "Client direction 2026-09-12: no scheduled battery replacement inside the 20 year horizon; capacity fade is carried by the Battery SOH curve and derates the battery's savings instead.",
      "note": "Supersedes the year-10 whole-system replacement at 100 percent of install (2026-09-11). A case may still opt in through technologies.storage.replacement in its case.json; the policy year (10) and fraction (1.0) are then inherited. REopt is sent replace_cost_per_kw = replace_cost_per_kwh = 0."},
    "bess_cycle_life_efc": {"value": 8000, "source": "Client direction 2026-09-12: 8,000 equivalent full cycles to 80 percent state of health, LFP datasheet convention.",
      "note": "Sets the cycle-fade coefficient of the SOH curve: (1 - 0.80) / 8000 = 2.5e-5 kWh lost per kWh discharged. NREL's laboratory default (2.46e-5) corresponds to about 8,130 cycles, so the curve barely moves; the assumption is now a vendor-style input rather than a laboratory constant. Calendar fade keeps NREL's coefficients."},
```

In the `project_years` note (line 8) replace `BESS replacement year 10, inverter replacement year 11` with `inverter replacement year 11; the battery is not replaced (2026-09-12), its fade is carried by the SOH curve`.

Verify with `git diff --stat` that the JSON diff is about 8 lines.

- [ ] **Step 5: Thailand guards**

In `proforma_thailand/defaults/__init__.py`: import `BESS_REPLACEMENT_ENABLED, BESS_CYCLE_LIFE_EFC` from `proforma_vietnam.defaults` (drop `BESS_REPLACE_FRACTION_OF_INSTALL` if nothing else uses it). Replace `_DERIVED_COUPLINGS` with only the O&M row and extend `_POLICY_EQUALITIES`:

```python
_DERIVED_COUPLINGS = (
    ("annual_om_per_kw", "pv_installed_cost_per_kw", 0.015),
)

# Schedule, horizon and ageing entries that must equal the shared policy outright.
_POLICY_EQUALITIES = (
    ("project_years", PROJECT_YEARS),
    ("pv_inverter_replacement_year", PV_INVERTER_REPLACEMENT_YEAR),
    ("pv_inverter_replacement_fraction_of_pv_capex", PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX),
    ("bess_replacement_enabled", BESS_REPLACEMENT_ENABLED),
    ("bess_cycle_life_efc", BESS_CYCLE_LIFE_EFC),
)
```

Update the comment above `_DERIVED_COUPLINGS` (drop the replacement-fraction sentence).

- [ ] **Step 6: Run the two defaults suites**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_defaults proforma_thailand.tests.test_thailand_defaults -v`
Expected: PASS. Existing Thailand tests that asserted `bess_replace_cost_per_kw == 100.0` (ReplacementPolicy tests from 2026-09-11) will fail: rewrite each to assert the new flag/cycle-life instead, keeping the test count.

- [ ] **Step 7: Commit**

```bash
git add proforma_vietnam/defaults/__init__.py proforma_thailand/defaults proforma_vietnam/tests/test_defaults.py proforma_thailand/tests/test_thailand_defaults.py
git commit -m "Turn the battery replacement into an opt-in and add the cycle-life policy"
```

---

### Task 2: Shared replacement switch in the Vietnam builder

**Files:**
- Modify: `proforma_vietnam/case_builder.py:1-15` (imports), `:98-118` (STORAGE_PAYLOAD_KEYS), `:281-317` (`_storage_inputs`, `_apply_replacement_policy`), `:559-577` (assumptions record)
- Test: `proforma_vietnam/tests/test_case_builder.py` (replace `ReplacementPolicyInTheBuilderTests`)

**Interfaces:**
- Produces: `apply_replacement_policy(storage_config, storage_payload)` (public) which mutates `storage_payload` in place and returns a record dict `{"bess_replacement_enabled": bool, "battery_replacement_year": int|None, "bess_replace_cost_per_kw": float|None, "bess_replace_cost_per_kwh": float|None, "bess_cycle_life_efc": number}`; raises `ValueError` on raw REopt replacement keys or conflicting cost inputs.
- `REPLACEMENT_RAW_KEYS` tuple of the six raw keys.

- [ ] **Step 1: Write the failing tests**

Replace the `ReplacementPolicyInTheBuilderTests` class in `proforma_vietnam/tests/test_case_builder.py` with:

```python
class ReplacementSwitchInTheBuilderTests(TestCase):

    def _storage(self, extra=None):
        storage = {"min_kw": 100, "max_kw": 100, "min_kwh": 200, "max_kwh": 200,
                   "installed_cost_per_kw": 80, "installed_cost_per_kwh": 120}
        storage.update(extra or {})
        return storage

    def test_default_sends_a_zero_replacement_and_no_years(self):
        payload = {"max_kw": 100, "max_kwh": 200, "installed_cost_per_kw": 80,
                   "installed_cost_per_kwh": 120}
        record = case_builder.apply_replacement_policy(self._storage(), payload)
        self.assertEqual(payload["replace_cost_per_kw"], 0.0)
        self.assertEqual(payload["replace_cost_per_kwh"], 0.0)
        self.assertNotIn("battery_replacement_year", payload)
        self.assertNotIn("inverter_replacement_year", payload)
        self.assertEqual(record["bess_replacement_enabled"], False)
        self.assertNotIn("battery_replacement_year", record)
        self.assertEqual(record["bess_cycle_life_efc"], 8000)

    def test_enabled_block_prices_the_whole_system_in_one_year(self):
        payload = {"max_kw": 100, "max_kwh": 200, "installed_cost_per_kw": 80,
                   "installed_cost_per_kwh": 120}
        record = case_builder.apply_replacement_policy(
            self._storage({"replacement": {"enabled": True}}), payload)
        self.assertEqual(payload["replace_cost_per_kw"], 80.0)
        self.assertEqual(payload["replace_cost_per_kwh"], 120.0)
        self.assertEqual(payload["battery_replacement_year"], 10)
        self.assertEqual(payload["inverter_replacement_year"], 10)
        self.assertEqual(record["battery_replacement_year"], 10)
        self.assertEqual(record["bess_replace_cost_per_kw"], 80.0)

    def test_enabled_block_accepts_year_fraction_and_absolute_costs(self):
        payload = {"installed_cost_per_kw": 80, "installed_cost_per_kwh": 120, "max_kwh": 1}
        case_builder.apply_replacement_policy(
            self._storage({"replacement": {"enabled": True, "year": 8, "fraction_of_install": 0.5}}), payload)
        self.assertEqual((payload["replace_cost_per_kw"], payload["replace_cost_per_kwh"]), (40.0, 60.0))
        self.assertEqual(payload["battery_replacement_year"], 8)
        payload = {"installed_cost_per_kw": 80, "installed_cost_per_kwh": 120, "max_kwh": 1}
        case_builder.apply_replacement_policy(
            self._storage({"replacement": {"enabled": True, "cost_per_kw": 30, "cost_per_kwh": 45}}), payload)
        self.assertEqual((payload["replace_cost_per_kw"], payload["replace_cost_per_kwh"]), (30, 45))

    def test_fraction_and_absolute_costs_together_are_refused(self):
        with self.assertRaises(ValueError):
            case_builder.apply_replacement_policy(
                self._storage({"replacement": {"enabled": True, "fraction_of_install": 1.0, "cost_per_kw": 30}}),
                {"installed_cost_per_kw": 80, "installed_cost_per_kwh": 120, "max_kwh": 1})

    def test_raw_reopt_replacement_keys_are_refused(self):
        for key in case_builder.REPLACEMENT_RAW_KEYS:
            with self.assertRaises(ValueError, msg=key):
                case_builder.apply_replacement_policy(
                    self._storage({key: 1}), {"installed_cost_per_kw": 80, "max_kwh": 1})

    def test_cycle_life_override_is_recorded(self):
        record = case_builder.apply_replacement_policy(
            self._storage({"cycle_life_efc": 6000}), {"installed_cost_per_kw": 80, "max_kwh": 1})
        self.assertEqual(record["bess_cycle_life_efc"], 6000)
        with self.assertRaises(ValueError):
            case_builder.apply_replacement_policy(
                self._storage({"cycle_life_efc": 0}), {"installed_cost_per_kw": 80, "max_kwh": 1})

    def test_no_storage_means_no_record(self):
        payload = {}
        record = case_builder.apply_replacement_policy({}, payload)
        self.assertEqual(record, {})
        self.assertEqual(payload, {})

    def test_built_case_records_the_switch_in_assumptions(self):
        case = _minimal_case()
        case["technologies"]["storage"] = self._storage()
        built = case_builder.build_case(case)
        storage = built["payload"]["ElectricStorage"]
        self.assertEqual(storage["replace_cost_per_kw"], 0.0)
        self.assertNotIn("battery_replacement_year", storage)
        self.assertIs(built["assumptions"]["bess_replacement_enabled"], False)
        self.assertEqual(built["assumptions"]["bess_cycle_life_efc"], 8000)
        self.assertNotIn("battery_replacement_year", built["assumptions"])
```

Reuse the module's existing minimal-case helper (the 2026-09-11 tests already build a case; use the same helper name that file defines, e.g. `_minimal_case`; if it is named differently, use that name).

- [ ] **Step 2: Run to verify failure**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_case_builder.ReplacementSwitchInTheBuilderTests -v`
Expected: FAIL (`apply_replacement_policy` missing).

- [ ] **Step 3: Implement**

In `proforma_vietnam/case_builder.py`:

Imports: replace `BESS_REPLACEMENT_YEAR, BESS_REPLACE_FRACTION_OF_INSTALL` with `BESS_REPLACEMENT_ENABLED, BESS_REPLACEMENT_YEAR, BESS_REPLACE_FRACTION_OF_INSTALL, BESS_CYCLE_LIFE_EFC`.

`STORAGE_PAYLOAD_KEYS`: delete the six raw keys (`replace_cost_per_kw`, `replace_cost_per_kwh`, `replace_cost_constant`, `inverter_replacement_year`, `battery_replacement_year`, `cost_constant_replacement_year`) and add the module constant:

```python
# Raw REopt replacement keys are not accepted in case.json: the replacement
# block below is the one way to say it (ruling 2026-09-12).
REPLACEMENT_RAW_KEYS = (
    "replace_cost_per_kw",
    "replace_cost_per_kwh",
    "replace_cost_constant",
    "inverter_replacement_year",
    "battery_replacement_year",
    "cost_constant_replacement_year",
)
```

Replace `_apply_replacement_policy` with:

```python
def apply_replacement_policy(storage_config, storage_payload):
    """Fill the REopt replacement inputs from technologies.storage.replacement.

    Default (policy 2026-09-12): no scheduled replacement, so REopt is sent a
    zero replacement price explicitly and no replacement years. A case opts in
    with ``replacement: {"enabled": true, "year": 10, "fraction_of_install": 1.0}``
    (or ``cost_per_kw`` / ``cost_per_kwh`` instead of the fraction); the whole
    system, storage inverter and pack, is then replaced in that one year.
    Returns the record the workbook reads (bess_replacement_enabled and, when
    enabled, the year and unit prices; the cycle life either way). Empty when
    the case sends no storage system.
    """
    if not any(storage_payload.get(key) for key in ("max_kw", "max_kwh", "min_kw", "min_kwh")):
        return {}
    present = [key for key in REPLACEMENT_RAW_KEYS if key in storage_config]
    if present:
        raise ValueError(
            "technologies.storage carries {}; use technologies.storage.replacement "
            "{{enabled, year, fraction_of_install | cost_per_kw, cost_per_kwh}} instead.".format(
                ", ".join(present)
            )
        )
    cycle_life = storage_config.get("cycle_life_efc", BESS_CYCLE_LIFE_EFC)
    if not isinstance(cycle_life, (int, float)) or cycle_life <= 0:
        raise ValueError("technologies.storage.cycle_life_efc must be a positive number.")
    record = {"bess_cycle_life_efc": cycle_life}
    replacement = storage_config.get("replacement") or {}
    enabled = bool(replacement.get("enabled", BESS_REPLACEMENT_ENABLED))
    record["bess_replacement_enabled"] = enabled
    if not enabled:
        storage_payload["replace_cost_per_kw"] = 0.0
        storage_payload["replace_cost_per_kwh"] = 0.0
        return record
    absolute = {key: replacement[key] for key in ("cost_per_kw", "cost_per_kwh") if key in replacement}
    if absolute and "fraction_of_install" in replacement:
        raise ValueError(
            "technologies.storage.replacement: give fraction_of_install or "
            "cost_per_kw / cost_per_kwh, not both."
        )
    fraction = replacement.get("fraction_of_install", BESS_REPLACE_FRACTION_OF_INSTALL)
    year = int(replacement.get("year", BESS_REPLACEMENT_YEAR))
    for install_key, replace_key, absolute_key in (
        ("installed_cost_per_kw", "replace_cost_per_kw", "cost_per_kw"),
        ("installed_cost_per_kwh", "replace_cost_per_kwh", "cost_per_kwh"),
    ):
        if absolute_key in absolute:
            storage_payload[replace_key] = absolute[absolute_key]
        elif storage_payload.get(install_key) is not None:
            storage_payload[replace_key] = storage_payload[install_key] * fraction
    storage_payload["inverter_replacement_year"] = year
    storage_payload["battery_replacement_year"] = year
    record["battery_replacement_year"] = year
    record["bess_replace_cost_per_kw"] = storage_payload.get("replace_cost_per_kw")
    record["bess_replace_cost_per_kwh"] = storage_payload.get("replace_cost_per_kwh")
    return record
```

`_storage_inputs`: `storage = _allowlisted(storage_config, STORAGE_PAYLOAD_KEYS)` then `apply_replacement_policy(storage_config, storage)` (discard the record there).

Assumptions block (lines 559-570): replace the recompute loop with

```python
    # Record what the payload sent for replacement (policy or case opt-in),
    # recomputed the same way _storage_inputs did, so the workbook reads a
    # record rather than a live default.
    storage_config = technologies.get("storage", {})
    storage_sent = _allowlisted(storage_config, STORAGE_PAYLOAD_KEYS)
    assumptions.update(apply_replacement_policy(storage_config, storage_sent))
```

Search the module for any other reference to `_apply_replacement_policy` and update it.

- [ ] **Step 4: Run the Vietnam builder suite**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_case_builder -v`
Expected: PASS. If an older test asserts `battery_replacement_year == 10` on a default case, that test now describes the superseded policy: rewrite it to the new default.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/case_builder.py proforma_vietnam/tests/test_case_builder.py
git commit -m "Vietnam builder: replacement block with the policy default off"
```

---

### Task 3: Thailand builder uses the shared switch

**Files:**
- Modify: `proforma_thailand/case_builder.py:20` (import), `:154-205` (storage payload), `:264-269` (assumptions)
- Test: `proforma_thailand/tests/test_case_builder.py` (replace the four 2026-09-11 replacement tests)

**Interfaces:**
- Consumes: `apply_replacement_policy` from Task 2.

- [ ] **Step 1: Write the failing tests**

Replace the four replacement tests (those using `_storage_case`) with:

```python
    def test_default_storage_case_sends_zero_replacement_and_records_the_switch(self):
        built = build_case(_storage_case())
        storage = built["payload"]["ElectricStorage"]
        self.assertEqual(storage["replace_cost_per_kw"], 0.0)
        self.assertEqual(storage["replace_cost_per_kwh"], 0.0)
        self.assertNotIn("battery_replacement_year", storage)
        self.assertNotIn("inverter_replacement_year", storage)
        self.assertIs(built["assumptions"]["bess_replacement_enabled"], False)
        self.assertEqual(built["assumptions"]["bess_cycle_life_efc"], 8000)
        self.assertNotIn("bess_replace_cost_per_kw", built["assumptions"])

    def test_opt_in_replacement_prices_from_the_thai_install_defaults(self):
        case = _storage_case()
        case["technologies"]["storage"]["replacement"] = {"enabled": True}
        built = build_case(case)
        storage = built["payload"]["ElectricStorage"]
        self.assertEqual(storage["replace_cost_per_kw"], 100.0)
        self.assertEqual(storage["replace_cost_per_kwh"], 150.0)
        self.assertEqual(storage["battery_replacement_year"], 10)
        self.assertEqual(built["assumptions"]["battery_replacement_year"], 10)
        self.assertEqual(built["assumptions"]["bess_replace_cost_per_kwh"], 150.0)

    def test_raw_replacement_keys_are_refused(self):
        case = _storage_case()
        case["technologies"]["storage"]["replace_cost_per_kw"] = 70.0
        with self.assertRaises(ValueError):
            build_case(case)

    def test_pv_only_case_records_no_battery_switch(self):
        built = build_case(_minimal_case())   # the file's existing PV-only helper
        self.assertNotIn("bess_replacement_enabled", built["assumptions"])
```

(Use the PV-only helper name the file already has.)

- [ ] **Step 2: Run to verify failure**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder -v`
Expected: the four new tests FAIL.

- [ ] **Step 3: Implement**

`proforma_thailand/case_builder.py` line 20: `from proforma_vietnam.case_builder import apply_replacement_policy` (drop the two policy constants import). In the storage payload dict delete the four `replace_cost_per_kw` / `replace_cost_per_kwh` / `inverter_replacement_year` / `battery_replacement_year` entries and their comment; immediately after the dict:

```python
        replacement_record = apply_replacement_policy(storage_config, payload["ElectricStorage"])
```

(define `replacement_record = {}` before the `if storage_config.get("max_kw") ...` block). Replace the `storage_sent` block in the assumptions with `assumptions.update(replacement_record)`.

- [ ] **Step 4: Run the Thailand suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v`
Expected: PASS (143 tests; count may shift by the tests rewritten). `test_report.py`'s e2e test asserts on `battery_replacement_year` in the passthrough: leave that assertion only if it still holds (the key is absent by default now), otherwise change the expectation to the absent key.

- [ ] **Step 5: Commit**

```bash
git add proforma_thailand/case_builder.py proforma_thailand/tests/test_case_builder.py proforma_thailand/tests/test_report.py
git commit -m "Thailand builder: use the shared replacement switch"
```

---

### Task 4: Plumbing for the two new assumption keys

**Files:**
- Modify: `proforma_vietnam/run_case.py:16-40`, `proforma_vietnam/run_dppa_negotiation_sweep.py:160-190`, `proforma_thailand/report.py:38-57`, `reoptjl/views.py:475-522`
- Test: `proforma_vietnam/tests/test_run_case.py`, `proforma_thailand/tests/test_report.py`

**Interfaces:**
- Produces: the pro forma receives `bess_cycle_life_efc=<number>` as a keyword argument in every flow (Vietnam Django report, Vietnam rebuild, Thailand report/rebuild). `bess_replacement_enabled` reaches `assumptions` in the Django flow.

- [ ] **Step 1: Write the failing tests**

In `proforma_vietnam/tests/test_run_case.py` add:

```python
    def test_report_query_carries_the_battery_ageing_keys(self):
        from proforma_vietnam.run_case import VIETNAM_REPORT_QUERY_KEYS
        self.assertIn("bess_cycle_life_efc", VIETNAM_REPORT_QUERY_KEYS)
        self.assertIn("bess_replacement_enabled", VIETNAM_REPORT_QUERY_KEYS)
```

In `proforma_vietnam/tests/test_dppa_negotiation_sweep.py` add:

```python
    def test_cash_flow_overrides_pass_the_cycle_life(self):
        from proforma_vietnam.run_dppa_negotiation_sweep import cash_flow_overrides_from_assumptions
        overrides = cash_flow_overrides_from_assumptions({"bess_cycle_life_efc": 6000})
        self.assertEqual(overrides["bess_cycle_life_efc"], 6000)
```

In `proforma_thailand/tests/test_report.py` add:

```python
    def test_cash_flow_overrides_pass_the_cycle_life(self):
        overrides = cash_flow_overrides_from_assumptions({"bess_cycle_life_efc": 6000})
        self.assertEqual(overrides["bess_cycle_life_efc"], 6000)
```

- [ ] **Step 2: Run to verify failure**

Run the three test modules. Expected: FAIL.

- [ ] **Step 3: Implement**

- `run_case.py` `VIETNAM_REPORT_QUERY_KEYS`: add `"bess_cycle_life_efc"`, `"bess_replacement_enabled"`. Booleans: check `_vietnam_report_query_params` and make sure a `False` value is sent as `"false"` (look at how `grid_charging_enabled` is serialised there and reuse it).
- `run_dppa_negotiation_sweep.py` mapping: add `"bess_cycle_life_efc": "bess_cycle_life_efc"`.
- `proforma_thailand/report.py` `PASSTHROUGH_OVERRIDE_KEYS`: add `"bess_cycle_life_efc"`.
- `reoptjl/views.py` `numeric_query_params`: add `"bess_cycle_life_efc": "bess_cycle_life_efc"`. After the `grid_charging_enabled` block add:

```python
    if "bess_replacement_enabled" in request.GET:
        assumptions["bess_replacement_enabled"] = _parse_boolean_query_param(
            "bess_replacement_enabled", request.GET["bess_replacement_enabled"]
        )
```

- [ ] **Step 4: Run tests**

Run: the three modules plus `./.venv/Scripts/python.exe -c "import ast,sys; ast.parse(open('reoptjl/views.py',encoding='utf-8').read())"` (views needs Django to import; a syntax check is the available guard).
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/run_case.py proforma_vietnam/run_dppa_negotiation_sweep.py proforma_thailand/report.py reoptjl/views.py proforma_vietnam/tests proforma_thailand/tests
git commit -m "Carry bess_cycle_life_efc and bess_replacement_enabled through every report flow"
```

---

### Task 5: SOH engine

**Files:**
- Create: `proforma_vietnam/battery_soh.py`
- Create: `proforma_vietnam/tests/fixtures/soh_probe_bess_arbitrage_5mw.json`
- Test: `proforma_vietnam/tests/test_battery_soh.py`

**Interfaces:**
- Produces: `battery_state_of_health(*, size_kwh, soc_series_fraction, discharge_series_kw, time_steps_per_hour, project_years, cycle_life_efc=..., end_of_life_soh=..., calendar_fade_coefficient=..., calendar_fade_exponent=..., cycle_fade_coefficient=None) -> dict | None` and `cycle_fade_coefficient_from_life(cycle_life_efc, end_of_life_soh=0.80) -> float`. Return dict keys: `soh_fraction_by_day`, `years` (list of dicts: `year, soh_end, soh_average, usable_kwh_end, efc_in_year, efc_cumulative, calendar_fade_kwh, cycle_fade_kwh`), `soh_average_by_year`, `first_year_below_end_of_life`, `coefficients` (`calendar_fade_coefficient, calendar_fade_exponent, cycle_fade_coefficient, cycle_life_efc, end_of_life_soh`), `year_one_daily_average_soc_kwh`, `year_one_daily_discharge_kwh`, `year_one_efc`, `size_kwh`, `project_years`.

- [ ] **Step 1: Build the fixture**

Write and run a scratch script that reads the probe file
`C:\Users\kongn\AppData\Local\Temp\claude\C--Users-kongn-Pictures-CodeProject-Reopt-API-REopt-API\c90d9f8a-d79c-4d9a-95db-5a5e7cb7c421\scratchpad\soh_arbitrage.json`
and writes `proforma_vietnam/tests/fixtures/soh_probe_bess_arbitrage_5mw.json` with

```json
{"source": "REopt.jl v0.57.0 direct solve 2026-09-12, model_degradation=true, augmentation, sizes pinned; NREL default coefficients",
 "size_kwh": 25000.0, "time_steps_per_hour": 1, "analysis_years": 20,
 "calendar_fade_coefficient": 1.16e-3, "cycle_fade_coefficient": 2.46e-5, "time_exponent": 0.428,
 "soc_series_fraction": [...8760...], "storage_to_load_series_kw": [...8760...],
 "state_of_health": [...7300...]}
```

taking the three arrays from `results.outputs.ElectricStorage` (`state_of_health` is REopt's SOH divided by size; confirm `state_of_health[0] == 1.0`). Create `proforma_vietnam/tests/fixtures/__init__.py` only if the discover runner needs it (it does not for data files).

- [ ] **Step 2: Write the failing tests**

```python
import json
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.battery_soh import (
    battery_state_of_health,
    cycle_fade_coefficient_from_life,
)

FIXTURE = Path(__file__).parent / "fixtures" / "soh_probe_bess_arbitrage_5mw.json"


class CycleFadeCoefficientTests(TestCase):

    def test_eight_thousand_cycles_to_eighty_percent(self):
        self.assertAlmostEqual(cycle_fade_coefficient_from_life(8000), 2.5e-5)

    def test_rejects_a_non_positive_life(self):
        with self.assertRaises(ValueError):
            cycle_fade_coefficient_from_life(0)


class ReoptReplicationTests(TestCase):

    def test_matches_reopt_state_of_health_day_by_day(self):
        probe = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = battery_state_of_health(
            size_kwh=probe["size_kwh"],
            soc_series_fraction=probe["soc_series_fraction"],
            discharge_series_kw=probe["storage_to_load_series_kw"],
            time_steps_per_hour=probe["time_steps_per_hour"],
            project_years=probe["analysis_years"],
            calendar_fade_coefficient=probe["calendar_fade_coefficient"],
            calendar_fade_exponent=probe["time_exponent"],
            cycle_fade_coefficient=probe["cycle_fade_coefficient"],
        )
        expected = probe["state_of_health"]
        self.assertEqual(len(result["soh_fraction_by_day"]), len(expected))
        worst = max(abs(a - b) for a, b in zip(result["soh_fraction_by_day"], expected))
        self.assertLess(worst, 2e-3)
        self.assertAlmostEqual(result["soh_fraction_by_day"][-1], expected[-1], delta=1e-3)
        self.assertIsNone(result["first_year_below_end_of_life"])


class RecurrencePropertyTests(TestCase):

    def _one_cycle_per_day(self, time_steps_per_hour):
        steps = 24 * time_steps_per_hour
        soc = ([1.0] * (steps // 2) + [0.0] * (steps // 2)) * 365
        discharge = ([0.0] * (steps // 2) + [2.0 * time_steps_per_hour / time_steps_per_hour] * (steps // 2)) * 365
        # 12 h at 2 kW is 24 kWh a day; the same 24 kWh at any resolution.
        discharge = ([0.0] * (steps // 2) + [2.0] * (steps // 2)) * 365
        return soc, discharge

    def test_same_daily_energy_gives_the_same_curve_at_any_resolution(self):
        hourly = self._one_cycle_per_day(1)
        quarter = self._one_cycle_per_day(4)
        a = battery_state_of_health(size_kwh=24.0, soc_series_fraction=hourly[0],
                                    discharge_series_kw=hourly[1], time_steps_per_hour=1, project_years=2)
        b = battery_state_of_health(size_kwh=24.0, soc_series_fraction=quarter[0],
                                    discharge_series_kw=quarter[1], time_steps_per_hour=4, project_years=2)
        for x, y in zip(a["soh_fraction_by_day"], b["soh_fraction_by_day"]):
            self.assertAlmostEqual(x, y, places=12)

    def test_full_cycle_every_day_without_calendar_fade_hits_eol_on_day_8001(self):
        soc = [0.5] * 8760
        discharge = [1.0] * 8760          # 24 kWh a day on a 24 kWh battery = 1 EFC/day
        result = battery_state_of_health(
            size_kwh=24.0, soc_series_fraction=soc, discharge_series_kw=discharge,
            time_steps_per_hour=1, project_years=23, calendar_fade_coefficient=0.0)
        self.assertAlmostEqual(result["soh_fraction_by_day"][8000], 0.80, places=9)
        self.assertEqual(result["first_year_below_end_of_life"], 22)
        self.assertAlmostEqual(result["year_one_efc"], 365.0)
        self.assertAlmostEqual(result["years"][0]["efc_in_year"], 365.0)

    def test_year_table_is_consistent(self):
        soc = [0.6] * 8760
        discharge = [0.5] * 8760
        result = battery_state_of_health(size_kwh=100.0, soc_series_fraction=soc,
                                         discharge_series_kw=discharge, time_steps_per_hour=1,
                                         project_years=3)
        years = result["years"]
        self.assertEqual([y["year"] for y in years], [1, 2, 3])
        start = 1.0
        for y in years:
            self.assertLessEqual(y["soh_end"], y["soh_average"])
            self.assertLessEqual(y["soh_average"], start)
            start = y["soh_end"]
        self.assertAlmostEqual(years[2]["efc_cumulative"], 3 * years[0]["efc_in_year"])
        self.assertEqual(result["soh_average_by_year"], [y["soh_average"] for y in years])
        self.assertAlmostEqual(
            years[0]["calendar_fade_kwh"] + years[0]["cycle_fade_kwh"],
            (1.0 - years[0]["soh_end"]) * 100.0, places=6)

    def test_no_battery_returns_none(self):
        self.assertIsNone(battery_state_of_health(size_kwh=0, soc_series_fraction=[1.0] * 8760,
                                                  discharge_series_kw=[0.0] * 8760,
                                                  time_steps_per_hour=1, project_years=20))
        self.assertIsNone(battery_state_of_health(size_kwh=10, soc_series_fraction=[],
                                                  discharge_series_kw=[], time_steps_per_hour=1,
                                                  project_years=20))
```

(Remove the duplicated `discharge` line in `_one_cycle_per_day`; keep the second definition.)

- [ ] **Step 3: Run to verify failure**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_battery_soh -v`
Expected: FAIL (module missing).

- [ ] **Step 4: Implement `proforma_vietnam/battery_soh.py`**

```python
"""Battery state of health from the solved year-1 dispatch.

Replicates the daily SOH recurrence of REopt.jl v0.57.0 (``add_degradation``
in src/constraints/battery_degradation.jl) with the hours-per-time-step
factor removed, so the same daily energy gives the same fade at 15 minute
and hourly resolution (ruling 2026-09-12). REopt's code applies the cycle
coefficient to the energy discharged, not the documented (E+ + E-)/2; the
code is followed. The optimiser never sees this curve; it derates the
proforma only.
"""

from proforma_vietnam.defaults import (
    BESS_CALENDAR_FADE_COEFFICIENT,
    BESS_CALENDAR_FADE_EXPONENT,
    BESS_CYCLE_LIFE_EFC,
    BESS_END_OF_LIFE_SOH,
)

DAYS_PER_YEAR = 365


def cycle_fade_coefficient_from_life(cycle_life_efc, end_of_life_soh=BESS_END_OF_LIFE_SOH):
    """kWh lost per kWh discharged so that ``cycle_life_efc`` full cycles reach end of life."""
    if not cycle_life_efc or cycle_life_efc <= 0:
        raise ValueError("cycle_life_efc must be a positive number of equivalent full cycles.")
    return (1.0 - end_of_life_soh) / cycle_life_efc


def _daily_energies(soc_series_fraction, discharge_series_kw, size_kwh, time_steps_per_hour):
    steps_per_day = 24 * time_steps_per_hour
    if len(soc_series_fraction) < DAYS_PER_YEAR * steps_per_day:
        raise ValueError(
            "state of health needs a full year of storage series ({} steps), got {}.".format(
                DAYS_PER_YEAR * steps_per_day, len(soc_series_fraction)
            )
        )
    average_energy_kwh = []
    discharged_kwh = []
    for day in range(DAYS_PER_YEAR):
        block = slice(day * steps_per_day, (day + 1) * steps_per_day)
        soc = soc_series_fraction[block]
        average_energy_kwh.append(sum(soc) / len(soc) * size_kwh)
        discharged_kwh.append(sum(discharge_series_kw[block]) / time_steps_per_hour)
    return average_energy_kwh, discharged_kwh


def battery_state_of_health(*, size_kwh, soc_series_fraction, discharge_series_kw,
                            time_steps_per_hour, project_years,
                            cycle_life_efc=BESS_CYCLE_LIFE_EFC,
                            end_of_life_soh=BESS_END_OF_LIFE_SOH,
                            calendar_fade_coefficient=BESS_CALENDAR_FADE_COEFFICIENT,
                            calendar_fade_exponent=BESS_CALENDAR_FADE_EXPONENT,
                            cycle_fade_coefficient=None):
    """SOH by day and by year for a battery cycled like its solved first year.

    Returns None when there is no battery or no series. ``cycle_fade_coefficient``
    given explicitly wins over the one derived from ``cycle_life_efc`` (the
    REopt replication test passes NREL's).
    """
    if not size_kwh or size_kwh <= 0 or not soc_series_fraction or not discharge_series_kw:
        return None
    k_cyc = (
        cycle_fade_coefficient if cycle_fade_coefficient is not None
        else cycle_fade_coefficient_from_life(cycle_life_efc, end_of_life_soh)
    )
    k_cal = calendar_fade_coefficient
    alpha = calendar_fade_exponent
    average_energy_kwh, discharged_kwh = _daily_energies(
        soc_series_fraction, discharge_series_kw, size_kwh, time_steps_per_hour
    )
    total_days = DAYS_PER_YEAR * int(project_years)
    soh_kwh = [float(size_kwh)]
    calendar_by_day = [0.0]
    cycle_by_day = [0.0]
    for day in range(2, total_days + 1):
        previous = (day - 2) % DAYS_PER_YEAR      # day-1 in the repeated year-1 pattern
        calendar = k_cal * alpha * average_energy_kwh[previous] * day ** (alpha - 1)
        cycle = k_cyc * discharged_kwh[previous]
        soh_kwh.append(soh_kwh[-1] - calendar - cycle)
        calendar_by_day.append(calendar)
        cycle_by_day.append(cycle)
    soh_fraction = [value / size_kwh for value in soh_kwh]

    efc_per_year = sum(discharged_kwh) / size_kwh
    years = []
    cumulative = 0.0
    first_below = None
    for year in range(1, int(project_years) + 1):
        block = slice((year - 1) * DAYS_PER_YEAR, year * DAYS_PER_YEAR)
        fractions = soh_fraction[block]
        cumulative += efc_per_year
        years.append({
            "year": year,
            "soh_end": fractions[-1],
            "soh_average": sum(fractions) / len(fractions),
            "usable_kwh_end": fractions[-1] * size_kwh,
            "efc_in_year": efc_per_year,
            "efc_cumulative": cumulative,
            "calendar_fade_kwh": sum(calendar_by_day[block]),
            "cycle_fade_kwh": sum(cycle_by_day[block]),
        })
        if first_below is None and any(value < end_of_life_soh for value in fractions):
            first_below = year
    return {
        "size_kwh": float(size_kwh),
        "project_years": int(project_years),
        "soh_fraction_by_day": soh_fraction,
        "years": years,
        "soh_average_by_year": [entry["soh_average"] for entry in years],
        "first_year_below_end_of_life": first_below,
        "coefficients": {
            "calendar_fade_coefficient": k_cal,
            "calendar_fade_exponent": alpha,
            "cycle_fade_coefficient": k_cyc,
            "cycle_life_efc": cycle_life_efc if cycle_fade_coefficient is None else None,
            "end_of_life_soh": end_of_life_soh,
        },
        "year_one_daily_average_soc_kwh": sum(average_energy_kwh) / DAYS_PER_YEAR,
        "year_one_daily_discharge_kwh": sum(discharged_kwh) / DAYS_PER_YEAR,
        "year_one_efc": efc_per_year,
    }
```

- [ ] **Step 5: Run the tests**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_battery_soh -v`
Expected: PASS. If the replication tolerance fails, print the worst day and check the `previous` index convention before touching tolerances.

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/battery_soh.py proforma_vietnam/tests/test_battery_soh.py proforma_vietnam/tests/fixtures/soh_probe_bess_arbitrage_5mw.json
git commit -m "Battery SOH engine replicating REopt's daily recurrence at h = 1"
```

---

### Task 6: Demand charge counterfactual

**Files:**
- Create: `proforma_vietnam/demand_charge.py`
- Test: `proforma_vietnam/tests/test_demand_charge.py`

**Interfaces:**
- Produces: `demand_charge_from_series(tariff_inputs, grid_purchase_kw, time_steps_per_hour=1) -> float | None` and `battery_demand_savings(tariff_inputs, load_kw, pv_available_kw, optimized_purchase_kw, time_steps_per_hour=1) -> float | None` (counterfactual minus optimized, floored at 0; None when unsupported).

- [ ] **Step 1: Write the failing tests**

```python
import glob
import json
from pathlib import Path
from unittest import TestCase

from proforma_vietnam.demand_charge import battery_demand_savings, demand_charge_from_series

ROOT = Path(__file__).resolve().parents[2]


def _results(case_dir):
    files = sorted(glob.glob(str(ROOT / case_dir / "results*.json")))
    assert files, case_dir
    return json.loads(Path(files[0]).read_text(encoding="utf-8"))


def _purchase(outputs):
    utility = outputs["ElectricUtility"]
    to_load = utility.get("electric_to_load_series_kw") or []
    to_storage = utility.get("electric_to_storage_series_kw") or [0.0] * len(to_load)
    return [a + b for a, b in zip(to_load, to_storage)]


class HandBuiltTests(TestCase):

    def test_coincident_peak_periods(self):
        tariff = {"coincident_peak_load_charge_per_kw": [10.0, 20.0],
                  "coincident_peak_load_active_time_steps": [[1, 2, 3], [4, 5]]}
        purchase = [5.0, 7.0, 6.0, 1.0, 3.0, 100.0]
        self.assertAlmostEqual(demand_charge_from_series(tariff, purchase), 10 * 7 + 20 * 3)

    def test_monthly_rates(self):
        tariff = {"monthly_demand_rates": [1.0] * 12}
        purchase = [1.0] * 8760
        purchase[24 * 31 + 5] = 50.0       # a February hour
        self.assertAlmostEqual(demand_charge_from_series(tariff, purchase), 11 * 1.0 + 50.0)

    def test_unsupported_structures_return_none(self):
        self.assertIsNone(demand_charge_from_series({"urdb_label": "abc"}, [1.0] * 8760))
        self.assertIsNone(demand_charge_from_series(
            {"monthly_demand_rates": [1.0] * 12, "demand_lookback_percent": 0.5}, [1.0] * 8760))

    def test_no_demand_structure_is_zero(self):
        self.assertEqual(demand_charge_from_series({"monthly_demand_rates": [0.0] * 12}, [1.0] * 8760), 0.0)

    def test_battery_savings_is_counterfactual_minus_optimized(self):
        tariff = {"coincident_peak_load_charge_per_kw": [10.0],
                  "coincident_peak_load_active_time_steps": [[1, 2]]}
        load = [10.0, 10.0]
        pv = [4.0, 0.0]
        optimized = [2.0, 3.0]         # the battery shaved the second hour
        self.assertAlmostEqual(battery_demand_savings(tariff, load, pv, optimized), 10 * 10 - 10 * 3)
        self.assertEqual(battery_demand_savings(tariff, load, pv, [20.0, 20.0]), 0.0)
        self.assertIsNone(battery_demand_savings({"urdb_label": "x"}, load, pv, optimized))


class ReoptTieOutTests(TestCase):
    """The replica must reproduce REopt's own demand costs on the saved solves."""

    def test_thailand_coincident_peak_bau_and_optimized(self):
        results = _results("outputs/thailand_case/rofu_thailand/case_6")
        tariff = results["inputs"]["ElectricTariff"]
        outputs = results["outputs"]
        expected_bau = outputs["ElectricTariff"]["year_one_coincident_peak_cost_before_tax_bau"]
        expected_opt = outputs["ElectricTariff"]["year_one_coincident_peak_cost_before_tax"]
        load = outputs["ElectricLoad"]["load_series_kw"]
        self.assertAlmostEqual(demand_charge_from_series(tariff, load, 4), expected_bau, delta=0.5)
        self.assertAlmostEqual(demand_charge_from_series(tariff, _purchase(outputs), 4), expected_opt, delta=0.5)

    def test_vietnam_monthly_demand_bau_and_optimized(self):
        results = _results("outputs/vietnam_case/factory_a/case_3")
        tariff = results["inputs"]["ElectricTariff"]
        outputs = results["outputs"]
        expected_bau = outputs["ElectricTariff"]["year_one_demand_cost_before_tax_bau"]
        expected_opt = outputs["ElectricTariff"]["year_one_demand_cost_before_tax"]
        load = outputs["ElectricLoad"]["load_series_kw"]
        self.assertAlmostEqual(demand_charge_from_series(tariff, load, 1), expected_bau, delta=0.5)
        self.assertAlmostEqual(demand_charge_from_series(tariff, _purchase(outputs), 1), expected_opt, delta=0.5)
```

If a saved solve's `inputs` echo does not carry the tariff arrays (check first), read them from the directory's `payload.json` instead.

- [ ] **Step 2: Run to verify failure**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_demand_charge -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `proforma_vietnam/demand_charge.py`**

```python
"""Year-1 demand charge recomputed from a grid purchase series.

Supports the two demand structures the cases use: REopt's coincident-peak
periods (PEA's on-peak kW charge) and monthly demand rates (EVN's capacity
charge). Anything else (URDB, ratchets, lookback) returns None so the caller
can say the battery's demand relief was not attributed rather than guess.
The PV-only counterfactual needs no optimiser: with no battery, PV serves
load first and the grid covers the rest.
"""

DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

_UNSUPPORTED_KEYS = ("urdb_label", "urdb_response", "urdb_utility_name", "urdb_rate_name",
                     "tou_demand_rates", "blended_annual_demand_rate", "monthly_demand_ratchet")


def demand_charge_from_series(tariff_inputs, grid_purchase_kw, time_steps_per_hour=1):
    tariff_inputs = tariff_inputs or {}
    for key in _UNSUPPORTED_KEYS:
        if tariff_inputs.get(key):
            return None
    if tariff_inputs.get("demand_lookback_percent"):
        return None
    cost = 0.0
    rates = tariff_inputs.get("coincident_peak_load_charge_per_kw") or []
    periods = tariff_inputs.get("coincident_peak_load_active_time_steps") or []
    for rate, steps in zip(rates, periods):
        if steps:
            cost += rate * max(grid_purchase_kw[step - 1] for step in steps)
    monthly = tariff_inputs.get("monthly_demand_rates") or []
    if any(monthly):
        steps_per_day = 24 * time_steps_per_hour
        start = 0
        for days, rate in zip(DAYS_IN_MONTH, monthly):
            end = start + days * steps_per_day
            window = grid_purchase_kw[start:end]
            if window:
                cost += rate * max(window)
            start = end
    return cost


def battery_demand_savings(tariff_inputs, load_kw, pv_available_kw, optimized_purchase_kw,
                           time_steps_per_hour=1):
    """Demand cost the battery removed: PV-only counterfactual minus the solved purchase."""
    counterfactual = [max(load - pv, 0.0) for load, pv in zip(load_kw, pv_available_kw)]
    without = demand_charge_from_series(tariff_inputs, counterfactual, time_steps_per_hour)
    with_battery = demand_charge_from_series(tariff_inputs, optimized_purchase_kw, time_steps_per_hour)
    if without is None or with_battery is None:
        return None
    return max(without - with_battery, 0.0)
```

- [ ] **Step 4: Run the tests**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_demand_charge -v`
Expected: PASS. If the Thailand tie-out is off by more than 0.5, print per-period maxima against REopt (`coincident_peak_load_active_time_steps` are 1-based) before changing anything.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/demand_charge.py proforma_vietnam/tests/test_demand_charge.py
git commit -m "Demand charge replica with a PV-only counterfactual for the battery share"
```

---

### Task 7: Battery fade inputs in `esco_pro_forma`

**Files:**
- Modify: `proforma_vietnam/esco_pro_forma.py:14-40` (pops), `:135-176` (after the replacement block), new helper near `_bess_replacement_costs`
- Test: `proforma_vietnam/tests/test_esco_pro_forma.py` (new class `BatteryFadeInputsTests`)

**Interfaces:**
- Consumes: `battery_state_of_health` (Task 5), `battery_demand_savings` (Task 6).
- Produces: `cash_flow_inputs["battery_fade"]` dict with keys `soh_by_year` (list), `energy_revenue_vnd`, `served_retail_value_vnd`, `unserved_energy_value_vnd`, `demand_savings_vnd`, `matched_energy_share`, `demand_attribution` (str), `energy_attribution` (str), `soh` (the Task 5 dict minus `soh_fraction_by_day`). Present only when the solve has a battery (`size_kwh > 0`).
- Pop `bess_cycle_life_efc` from the overrides (default `BESS_CYCLE_LIFE_EFC`).

- [ ] **Step 1: Write the failing tests**

Add to `test_esco_pro_forma.py` (reuse `_fake_reopt_results`; extend it if it lacks `soc_series_fraction` / `load_series_kw`, keeping existing tests green):

```python
class BatteryFadeInputsTests(TestCase):

    def _results(self, can_grid_charge, pv_kw=100.0):
        results = _fake_reopt_results(can_grid_charge=can_grid_charge)
        storage = results["outputs"]["ElectricStorage"]
        storage["size_kw"] = 10.0
        storage["size_kwh"] = 20.0
        storage["soc_series_fraction"] = [0.5] * 8760
        storage["storage_to_load_series_kw"] = [1.0] * 8760
        results["outputs"]["ElectricUtility"]["electric_to_storage_series_kw"] = (
            [1.2] * 8760 if can_grid_charge else [0.0] * 8760)
        results["outputs"]["ElectricLoad"] = {"load_series_kw": [10.0] * 8760}
        results["inputs"]["ElectricTariff"]["tou_energy_rates_per_kwh"] = [0.1] * 8760
        for pv in results["outputs"]["PV"]:
            pv["size_kw"] = pv_kw
        return results

    def test_pv_charged_storage_splits_served_value_and_share(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=False), esco_energy_discount_fraction=0.9, project_years=2)
        fade = result["derivation"]["battery_fade"]
        served_kwh = sum(_fake_served_kwh())            # helper: PV→load + storage→load of the fake
        self.assertAlmostEqual(fade["served_retail_value_usd"], 8760 * 1.0 * 0.1)
        self.assertAlmostEqual(fade["energy_revenue_usd"], 8760 * 1.0 * 0.1 * 0.9)
        self.assertEqual(fade["unserved_energy_value_usd"], 0.0)
        self.assertAlmostEqual(fade["matched_energy_share"], 8760.0 / served_kwh)
        self.assertEqual(len(fade["soh_by_year"]), 2)
        self.assertLess(fade["soh_by_year"][1], fade["soh_by_year"][0])

    def test_grid_charged_storage_beside_pv_books_no_energy_derate_under_esco(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=True), esco_energy_discount_fraction=0.9, project_years=2)
        fade = result["derivation"]["battery_fade"]
        self.assertEqual(fade["energy_revenue_usd"], 0.0)
        self.assertEqual(fade["unserved_energy_value_usd"], 0.0)
        self.assertIn("not booked", fade["energy_attribution"])

    def test_battery_only_case_uses_the_net_arbitrage_value(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=True, pv_kw=0.0), esco_energy_discount_fraction=0.9, project_years=2)
        fade = result["derivation"]["battery_fade"]
        self.assertAlmostEqual(fade["unserved_energy_value_usd"], 8760 * (1.0 - 1.2) * 0.1 if False else max(8760 * 1.0 * 0.1 - 8760 * 1.2 * 0.1, 0.0))

    def test_direct_ownership_with_grid_charging_books_the_net_value(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=True), esco_energy_discount_fraction=0.0, project_years=2,
            direct_ownership={"enabled": True})
        fade = result["derivation"]["battery_fade"]
        self.assertAlmostEqual(fade["unserved_energy_value_usd"], max(876.0 - 1051.2, 0.0))

    def test_demand_attribution_uses_the_counterfactual(self):
        results = self._results(can_grid_charge=False)
        results["inputs"]["ElectricTariff"]["monthly_demand_rates"] = [1.0] * 12
        results["outputs"]["ElectricUtility"]["electric_to_load_series_kw"] = [4.0] * 8760
        for pv in results["outputs"]["PV"]:
            pv["electric_to_load_series_kw"] = [5.0] * 8760
            pv["electric_to_storage_series_kw"] = [0.0] * 8760
            pv["electric_curtailed_series_kw"] = [0.0] * 8760
        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=1)
        fade = result["derivation"]["battery_fade"]
        # load 10, PV 5: counterfactual peak 5 every month; solved purchase 4.
        self.assertAlmostEqual(fade["demand_savings_usd"], 12 * (5.0 - 4.0))
        self.assertEqual(fade["demand_attribution"], "counterfactual")

    def test_cycle_life_override_reaches_the_curve(self):
        a = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=False), esco_energy_discount_fraction=0.9, project_years=2)
        b = calculate_esco_pro_forma_from_reopt_results(
            self._results(can_grid_charge=False), esco_energy_discount_fraction=0.9, project_years=2,
            bess_cycle_life_efc=2000)
        self.assertLess(b["derivation"]["battery_fade"]["soh_by_year"][1],
                        a["derivation"]["battery_fade"]["soh_by_year"][1])
        self.assertEqual(b["derivation"]["battery_fade"]["soh"]["coefficients"]["cycle_life_efc"], 2000)

    def test_no_battery_means_no_fade_block(self):
        results = _fake_reopt_results(can_grid_charge=False)
        results["outputs"]["ElectricStorage"] = {"size_kw": 0.0, "size_kwh": 0.0}
        result = calculate_esco_pro_forma_from_reopt_results(
            results, esco_energy_discount_fraction=0.9, project_years=1)
        self.assertNotIn("battery_fade", result["derivation"])
```

Write `_fake_served_kwh()` as a tiny module-level helper returning the fake's `PV electric_to_load + storage_to_load` series sum, or inline the number from `_fake_reopt_results`. Adjust the third test's expression to the plain `max(...)` form (the `if False` fragment is a placeholder to delete).

- [ ] **Step 2: Run to verify failure**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_esco_pro_forma.BatteryFadeInputsTests -v`
Expected: FAIL (`battery_fade` missing).

- [ ] **Step 3: Implement**

At the top of `calculate_esco_pro_forma_from_reopt_results` add
`bess_cycle_life_efc = cash_flow_overrides.pop("bess_cycle_life_efc", BESS_CYCLE_LIFE_EFC)`
(import `BESS_CYCLE_LIFE_EFC` from `proforma_vietnam.defaults`; import `battery_state_of_health` and `battery_demand_savings`; import `DEFAULT_PROJECT_YEARS` from `proforma_vietnam.cash_flow`).

After the `extra_replacement_costs` block and after `cash_flow_inputs.update(cash_flow_overrides)` plus the DPPA/direct-ownership resolution (so `direct_ownership_enabled` and `pv_capacity_kw` are known), add:

```python
    battery_fade = _battery_fade_inputs(
        storage_inputs=storage_inputs,
        storage_outputs=storage_outputs,
        utility_outputs=utility_outputs,
        pv_outputs=pv_outputs,
        load_series=_series(load_outputs.get("load_series_kw")) or _series(load_inputs.get("loads_kw")),
        tariff_inputs=tariff_inputs,
        rates=cash_flow_inputs["evn_energy_rates_vnd_per_kwh"],
        served_kwh=cash_flow_inputs["project_served_pv_kwh"],
        storage_in_served=storage_inputs.get("can_grid_charge") is False,
        direct_ownership_enabled=direct_ownership_enabled,
        battery_only=pv_capacity_kw == 0,
        esco_energy_discount_fraction=esco_energy_discount_fraction,
        levelization_factor=_levelization_factor(pv_outputs),
        time_steps_per_hour=cash_flow_inputs.get("time_steps_per_hour", 1),
        project_years=cash_flow_inputs.get("project_years", DEFAULT_PROJECT_YEARS),
        cycle_life_efc=bess_cycle_life_efc,
        exchange_rate_vnd_per_usd=exchange_rate_vnd_per_usd,
        reopt_money_values_currency=tariff_money_values_currency,
    )
    if battery_fade is not None:
        cash_flow_inputs["battery_fade"] = battery_fade
```

Place this so that `direct_ownership_enabled` is already computed (it is defined after the DPPA branch; put the block after `_apply_direct_ownership` runs). Helper:

```python
def _battery_fade_inputs(*, storage_inputs, storage_outputs, utility_outputs, pv_outputs,
                         load_series, tariff_inputs, rates, served_kwh, storage_in_served,
                         direct_ownership_enabled, battery_only, esco_energy_discount_fraction,
                         levelization_factor, time_steps_per_hour, project_years,
                         cycle_life_efc, exchange_rate_vnd_per_usd, reopt_money_values_currency):
    """Year-1 battery quantities the cash flow derates by state of health.

    Storage series are de-levelized like project_served_pv_kwh; grid charging
    is a grid quantity and is left alone, as report_data does. Which quantity
    carries the battery's energy follows the structure's own accounting:
    inside the served series when the battery is PV-charged (ESCO revenue and
    the retail repurchase), as a net value when the solve books the whole bill
    delta (direct ownership, battery-only arbitrage), and not at all when an
    ESCO case has grid-charged storage beside PV (that value is not booked
    today either).
    """
    size_kwh = _value(storage_outputs, "size_kwh")
    discharge_raw = _series(storage_outputs.get("storage_to_load_series_kw"))
    if size_kwh <= 0 or not discharge_raw:
        return None
    discharge = [value / levelization_factor for value in discharge_raw]
    soh = battery_state_of_health(
        size_kwh=size_kwh,
        soc_series_fraction=_series(storage_outputs.get("soc_series_fraction")),
        discharge_series_kw=discharge,
        time_steps_per_hour=time_steps_per_hour,
        project_years=project_years,
        cycle_life_efc=cycle_life_efc,
    )
    if soh is None:
        return None
    to_money = lambda value: _money(value, exchange_rate_vnd_per_usd, reopt_money_values_currency)
    discharge_value = sum(kw * rate for kw, rate in zip(discharge, rates)) / time_steps_per_hour
    grid_to_storage = _series(utility_outputs.get("electric_to_storage_series_kw"))
    charge_cost = sum(kw * rate for kw, rate in zip(grid_to_storage, rates)) / time_steps_per_hour
    fade = {
        "soh_by_year": soh["soh_average_by_year"],
        "energy_revenue_vnd": 0.0,
        "served_retail_value_vnd": 0.0,
        "unserved_energy_value_vnd": 0.0,
        "matched_energy_share": 0.0,
        "energy_attribution": "",
        "soh": {key: value for key, value in soh.items() if key != "soh_fraction_by_day"},
    }
    if storage_in_served:
        fade["energy_revenue_vnd"] = discharge_value * esco_energy_discount_fraction
        fade["served_retail_value_vnd"] = discharge_value
        total_served = sum(served_kwh)
        fade["matched_energy_share"] = sum(discharge) / total_served if total_served else 0.0
        fade["energy_attribution"] = "inside the served series (PV-charged storage)"
    elif direct_ownership_enabled or battery_only:
        fade["unserved_energy_value_vnd"] = max(discharge_value - charge_cost, 0.0)
        fade["energy_attribution"] = "net retail value of battery energy (discharge minus grid charging)"
    else:
        fade["energy_attribution"] = (
            "not booked: grid-charged storage beside PV under an ESCO structure "
            "carries no attributed energy value in this model"
        )
    pv_available = _sum_series([
        _sum_series([
            pv.get("electric_to_load_series_kw", []),
            pv.get("electric_to_storage_series_kw", []),
            pv.get("electric_curtailed_series_kw", []),
            pv.get("electric_to_grid_series_kw", []),
        ]) for pv in pv_outputs
    ]) or [0.0] * len(load_series)
    optimized_purchase = _sum_series([
        _series(utility_outputs.get("electric_to_load_series_kw")),
        grid_to_storage,
    ])
    demand = battery_demand_savings(
        tariff_inputs, load_series, pv_available, optimized_purchase, time_steps_per_hour
    ) if load_series and optimized_purchase else None
    if demand is None:
        fade["demand_savings_vnd"] = 0.0
        fade["demand_attribution"] = "none: unsupported tariff demand structure"
    else:
        fade["demand_savings_vnd"] = demand / levelization_factor
        fade["demand_attribution"] = "counterfactual"
    for key in ("energy_revenue_vnd", "served_retail_value_vnd",
                "unserved_energy_value_vnd", "demand_savings_vnd"):
        fade[key] = to_money(fade[key])
    return fade
```

Note the rates passed in are already in cash-flow currency (`_money_series` was applied), so `discharge_value` / `charge_cost` are already converted: do NOT convert them again. Apply `to_money` only to `demand_savings_vnd` (REopt money). Fix the loop accordingly: convert `demand_savings_vnd` only.

Check `_sum_series` semantics (it pads/aligns) before relying on it for `pv_available`; if it returns `[]` for an empty input list, the `or` fallback covers the battery-only case.

- [ ] **Step 4: Run the pro forma suite**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_esco_pro_forma -v`
Expected: PASS, including the new class. Existing tests pass `project_years=1` on fakes with a battery: the SOH engine needs 8760-long series; the fake's storage series may be short. If so, `_battery_fade_inputs` must return `None` when the series are shorter than a year (guard on `len(discharge) < 365 * 24 * time_steps_per_hour` with a derivation note) rather than raising, and the new tests use full-length series.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/esco_pro_forma.py proforma_vietnam/tests/test_esco_pro_forma.py
git commit -m "Assemble the battery fade inputs from the solved dispatch"
```

---

### Task 8: Apply the fade in the cash flow

**Files:**
- Modify: `proforma_vietnam/cash_flow.py:82-135` (signature), `:253-262` (bases), `:290-372` (loop 1), `:645-700` (loop 2), `:820-870` (derivation), `:1492-1530` (`_dppa_year_terms`)
- Test: `proforma_vietnam/tests/test_cash_flow.py` (new class `BatteryFadeTests`)

**Interfaces:**
- Consumes: `battery_fade` dict (Task 7 keys).
- Produces: per-year row keys `battery_soh_fraction`, `battery_fade_loss_vnd` (+ `_usd`); `derivation["battery_fade"]` with `energy_revenue_usd`, `served_retail_value_usd`, `unserved_energy_value_usd`, `demand_savings_usd`, `matched_energy_share`, `soh_by_year`, `energy_attribution`, `demand_attribution`, `soh`.

- [ ] **Step 1: Write the failing tests**

Add to `test_cash_flow.py` (use the file's existing minimal-kwargs helper for `calculate_vietnam_esco_cash_flow`; call it `_base_kwargs()` below):

```python
class BatteryFadeTests(TestCase):

    def _fade(self, **overrides):
        fade = {"soh_by_year": [1.0, 0.9, 0.8], "energy_revenue_vnd": 0.0,
                "served_retail_value_vnd": 0.0, "unserved_energy_value_vnd": 0.0,
                "demand_savings_vnd": 0.0, "matched_energy_share": 0.0,
                "energy_attribution": "test", "demand_attribution": "test", "soh": {}}
        fade.update(overrides)
        return fade

    def _run(self, fade=None, **kwargs):
        base = _base_kwargs()
        base.update(project_years=3, pv_degradation_rate=0.0, evn_energy_escalation_rate=0.0,
                    evn_capacity_escalation_rate=0.0)
        base.update(kwargs)
        return calculate_vietnam_esco_cash_flow(battery_fade=fade, **base)

    def test_none_is_inert(self):
        a = self._run(None)
        b = self._run(self._fade(soh_by_year=[1.0, 1.0, 1.0]))
        for x, y in zip(a["annual_cash_flows"], b["annual_cash_flows"]):
            self.assertAlmostEqual(x["esco_revenue_vnd"], y["esco_revenue_vnd"])
            self.assertAlmostEqual(x["offtaker_savings_vnd"], y["offtaker_savings_vnd"])
        self.assertNotIn("battery_soh_fraction", a["annual_cash_flows"][0])
        self.assertEqual(b["annual_cash_flows"][2]["battery_fade_loss_vnd"], 0.0)

    def test_esco_energy_revenue_derates_only_the_battery_part(self):
        base = self._run(None)["annual_cash_flows"]
        rows = self._run(self._fade(energy_revenue_vnd=1000.0, served_retail_value_vnd=1200.0))["annual_cash_flows"]
        self.assertAlmostEqual(rows[0]["esco_energy_revenue_vnd"], base[0]["esco_energy_revenue_vnd"])
        self.assertAlmostEqual(rows[1]["esco_energy_revenue_vnd"], base[1]["esco_energy_revenue_vnd"] - 100.0)
        self.assertAlmostEqual(rows[2]["esco_energy_revenue_vnd"], base[2]["esco_energy_revenue_vnd"] - 200.0)
        # offtaker repurchases the lost battery energy at retail
        self.assertAlmostEqual(rows[1]["optimized_evn_bill_vnd"], base[1]["optimized_evn_bill_vnd"] + 120.0)
        self.assertAlmostEqual(rows[1]["battery_fade_loss_vnd"], 120.0)
        self.assertAlmostEqual(rows[1]["battery_soh_fraction"], 0.9)

    def test_demand_and_arbitrage_parts_derate(self):
        base = self._run(None, net_grid_arbitrage_value_vnd=500.0, grid_charging_enabled=True)["annual_cash_flows"]
        rows = self._run(self._fade(demand_savings_vnd=200.0, unserved_energy_value_vnd=500.0),
                         net_grid_arbitrage_value_vnd=500.0, grid_charging_enabled=True)["annual_cash_flows"]
        self.assertAlmostEqual(rows[1]["demand_charge_savings_vnd"], base[1]["demand_charge_savings_vnd"] - 20.0)
        self.assertAlmostEqual(rows[1]["esco_grid_arbitrage_revenue_vnd"], base[1]["esco_grid_arbitrage_revenue_vnd"] * 0.9)
        self.assertAlmostEqual(rows[1]["optimized_evn_bill_vnd"], base[1]["optimized_evn_bill_vnd"] + 50.0 + 20.0)
        self.assertAlmostEqual(rows[1]["battery_fade_loss_vnd"], 50.0 + 20.0)

    def test_demand_part_is_capped_at_the_base(self):
        rows = self._run(self._fade(demand_savings_vnd=10_000_000.0))["annual_cash_flows"]
        self.assertGreaterEqual(rows[2]["demand_charge_savings_vnd"], 0.0)

    def test_direct_ownership_bill_savings_carry_the_fade(self):
        base = self._run(None, direct_ownership={"enabled": True})["annual_cash_flows"]
        rows = self._run(self._fade(unserved_energy_value_vnd=300.0, demand_savings_vnd=100.0),
                         direct_ownership={"enabled": True})["annual_cash_flows"]
        self.assertAlmostEqual(rows[1]["bill_savings_revenue_vnd"], base[1]["bill_savings_revenue_vnd"] - 40.0)
        self.assertAlmostEqual(rows[1]["battery_fade_loss_vnd"], 40.0)

    def test_derivation_records_the_inputs(self):
        result = self._run(self._fade(energy_revenue_vnd=1.0))
        block = result["derivation"]["battery_fade"]
        self.assertEqual(block["soh_by_year"], [1.0, 0.9, 0.8])
        self.assertEqual(block["energy_revenue_usd"], 1.0)
        self.assertEqual(block["energy_attribution"], "test")
```

Add a DPPA variant if the file already has a grid-CfD fixture: with `matched_energy_share=0.5` and `soh_by_year=[1.0, 0.9, 0.8]`, `c_dn_vnd` in year 2 equals the base times `0.5 * 1.0 + 0.5 * 0.9`.

- [ ] **Step 2: Run to verify failure**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_cash_flow.BatteryFadeTests -v`
Expected: FAIL (unexpected keyword `battery_fade`).

- [ ] **Step 3: Implement**

Signature: add `battery_fade=None` after `contract_residual_value_usd`. After the base quantities (after `base_grid_arbitrage_revenue_vnd`):

```python
    # Battery capacity fade (2026-09-12): the battery's share of every
    # generation-linked base is multiplied by the year's average state of
    # health instead of the PV degradation factor; None leaves every path as
    # it was.
    fade = battery_fade or {}
    soh_by_year = list(fade.get("soh_by_year") or [])
    bess_energy_revenue_vnd = fade.get("energy_revenue_vnd") or 0.0
    bess_served_retail_vnd = fade.get("served_retail_value_vnd") or 0.0
    bess_unserved_value_vnd = fade.get("unserved_energy_value_vnd") or 0.0
    bess_demand_savings_vnd = min(fade.get("demand_savings_vnd") or 0.0, base_demand_savings_vnd)
    bess_matched_share = fade.get("matched_energy_share") or 0.0
    if structure == DPPA:
        bess_energy_revenue_vnd = 0.0

    def _soh_multiplier(year_index):
        if year_index < len(soh_by_year):
            return soh_by_year[year_index]
        return 1.0

    def _served_repurchase(degradation_multiplier, soh_multiplier):
        return (
            (base_served_retail_value_vnd - bess_served_retail_vnd) * (1 - degradation_multiplier)
            + (bess_served_retail_vnd + bess_unserved_value_vnd) * (1 - soh_multiplier)
        )
```

Loop 1 (replace the corresponding lines):

```python
        soh_multiplier = _soh_multiplier(year_index)
        generation_multiplier = (
            (1 - bess_matched_share) * degradation_multiplier + bess_matched_share * soh_multiplier
        )
        lost_demand_relief_vnd = bess_demand_savings_vnd * (1 - soh_multiplier) * capacity_multiplier

        if structure == PHYSICAL_DPPA:
            ppa_multiplier = (1 + ppa_price_escalation_rate) ** year_index
            esco_energy_revenue_vnd = base_energy_revenue_vnd * ppa_multiplier * generation_multiplier
        else:
            esco_energy_revenue_vnd = (
                (base_energy_revenue_vnd - bess_energy_revenue_vnd) * degradation_multiplier
                + bess_energy_revenue_vnd * soh_multiplier
            ) * energy_multiplier
        demand_charge_savings_vnd = (
            (base_demand_savings_vnd - bess_demand_savings_vnd)
            + bess_demand_savings_vnd * soh_multiplier
        ) * capacity_multiplier
        esco_demand_revenue_vnd = demand_charge_savings_vnd * esco_demand_savings_share
        esco_grid_arbitrage_revenue_vnd = (
            base_grid_arbitrage_revenue_vnd * soh_multiplier * energy_multiplier
        )
        ...
        dppa_year = _dppa_year_terms(
            dppa_settlement, year_index, energy_multiplier, generation_multiplier
        )
```

Direct ownership block: `optimized_evn_bill_year_vnd = (optimized_evn_bill_vnd + _served_repurchase(degradation_multiplier, soh_multiplier)) * energy_multiplier + lost_demand_relief_vnd`.

`row["ppa_matched_kwh"] = matched_kwh_year1 * generation_multiplier`.

Fade loss row value (computed in loop 1, stored on the row only when `battery_fade` is not None):

```python
        if battery_fade is not None:
            if structure == DPPA:
                matched_retail = dppa_settlement["year_one"].get("matched_retail_value_vnd", 0.0)
                energy_loss = matched_retail * bess_matched_share * (1 - soh_multiplier) * energy_multiplier
            elif structure == PHYSICAL_DPPA:
                energy_loss = base_energy_revenue_vnd * bess_matched_share * (1 - soh_multiplier) * ppa_multiplier
            else:
                energy_loss = (
                    (bess_served_retail_vnd + bess_unserved_value_vnd) * (1 - soh_multiplier) * energy_multiplier
                )
            row["battery_soh_fraction"] = soh_multiplier
            row["battery_fade_loss_vnd"] = energy_loss + lost_demand_relief_vnd
```

Loop 2: recompute `soh_multiplier = _soh_multiplier(year_index)` and replace
`optimized_evn_bill_year_vnd = (optimized_evn_bill_vnd + base_served_retail_value_vnd * (1 - degradation_multiplier)) * energy_multiplier`
with
`optimized_evn_bill_year_vnd = (optimized_evn_bill_vnd + _served_repurchase(degradation_multiplier, soh_multiplier)) * energy_multiplier + bess_demand_savings_vnd * (1 - soh_multiplier) * capacity_multiplier`.
In the DPPA offtaker branch add `+ bess_demand_savings_vnd * (1 - soh_multiplier) * capacity_multiplier` to `offtaker_post_project_cost_vnd`.

`_dppa_year_terms`: rename the fourth parameter to `generation_multiplier` and use it where `degradation_multiplier` was.

Derivation: after `"pv_degradation_rate"` add

```python
        "battery_fade": (
            {
                "energy_revenue_usd": bess_energy_revenue_vnd,
                "served_retail_value_usd": bess_served_retail_vnd,
                "unserved_energy_value_usd": bess_unserved_value_vnd,
                "demand_savings_usd": bess_demand_savings_vnd,
                "matched_energy_share": bess_matched_share,
                "soh_by_year": soh_by_year,
                "energy_attribution": fade.get("energy_attribution"),
                "demand_attribution": fade.get("demand_attribution"),
                "soh": fade.get("soh"),
            }
            if battery_fade is not None else None
        ),
```

and drop the key when `None` (`derivation = {k: v for k, v in derivation.items() if not (k == "battery_fade" and v is None)}` or build conditionally) so workbooks without a battery see no key. Verify `_finalize_currencies` is applied to the derivation values you care about (the existing `_usd` keys there are written directly; follow that: these are USD in the production pipeline, keep the `_usd` names as the other derivation keys do).

- [ ] **Step 4: Run the cash flow and pro forma suites**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_cash_flow proforma_vietnam.tests.test_esco_pro_forma proforma_vietnam.tests.test_reference_esco_workbook proforma_vietnam.tests.test_reference_dppa_workbook -v`
Expected: PASS. The reference-workbook reconciliation tests use fakes without a full-year storage series and must be unaffected; if one now carries a `battery_fade` block, that means Task 7's short-series guard is missing.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/cash_flow.py proforma_vietnam/tests/test_cash_flow.py
git commit -m "Derate the battery's share of the savings by state of health"
```

---

### Task 9: Audit sheet formulas, replacement section, Model Basis

**Files:**
- Modify: `proforma_vietnam/audit_sheets.py:70-80` (CURATED keys), `:392-415` (Replacement Policy), `:700-800` (named engine inputs), `:1108-1240` (factor rows and revenue formulas), `:1555-1610` (offtaker), `:2100-2135` (`_replacement_bullet`), `:2455-2470` (Model Basis bullets)
- Test: `proforma_vietnam/tests/test_audit_sheets.py` (new class `BatteryFadeAuditTests`)

**Interfaces:**
- Consumes: `derivation["battery_fade"]`, rows `battery_soh_fraction`; assumptions `bess_replacement_enabled`, `bess_cycle_life_efc`.
- Produces: defined names `BESS_ENERGY_REV`, `BESS_SERVED_RETAIL`, `BESS_UNSERVED_VALUE`, `BESS_DEMAND_SAVINGS`, `BESS_MATCHED_SHARE`, `BESS_CYCLE_LIFE`; factor rows keyed `fac_soh` and (DPPA/physical) `fac_gen`.

- [ ] **Step 1: Write the failing tests**

Using the file's existing helper that builds a workbook from a fake `cash_flow_result` (the 2026-09-11 `ReplacementPolicyRowsTests` used one; reuse it and its fake-result builder, adding a `battery_fade` derivation block and `battery_soh_fraction` rows in a copy):

```python
class BatteryFadeAuditTests(TestCase):

    def _with_fade(self):
        result = deepcopy(_fake_cash_flow_result())          # the file's helper
        years = len(result["annual_cash_flows"])
        soh = [1.0 - 0.01 * i for i in range(years)]
        result["derivation"]["battery_fade"] = {
            "energy_revenue_usd": 100.0, "served_retail_value_usd": 120.0,
            "unserved_energy_value_usd": 0.0, "demand_savings_usd": 30.0,
            "matched_energy_share": 0.25, "soh_by_year": soh,
            "energy_attribution": "inside the served series (PV-charged storage)",
            "demand_attribution": "counterfactual",
            "soh": {"years": [{"year": i + 1, "soh_end": s, "soh_average": s, "usable_kwh_end": 100 * s,
                               "efc_in_year": 300.0, "efc_cumulative": 300.0 * (i + 1),
                               "calendar_fade_kwh": 0.5, "cycle_fade_kwh": 0.5} for i, s in enumerate(soh)],
                    "coefficients": {"calendar_fade_coefficient": 1.16e-3, "calendar_fade_exponent": 0.428,
                                     "cycle_fade_coefficient": 2.5e-5, "cycle_life_efc": 8000, "end_of_life_soh": 0.8},
                    "first_year_below_end_of_life": None, "year_one_efc": 300.0,
                    "year_one_daily_average_soc_kwh": 50.0, "year_one_daily_discharge_kwh": 80.0,
                    "size_kwh": 100.0, "project_years": years},
        }
        for i, row in enumerate(result["annual_cash_flows"]):
            row["battery_soh_fraction"] = soh[i]
            row["battery_fade_loss_usd"] = row["battery_fade_loss_vnd"] = 5.0 * i
        return result

    def _formulas(self, result, assumptions=None):
        workbook = build_vietnam_esco_workbook(result, assumptions or {"bess_replacement_enabled": False,
                                                                        "bess_cycle_life_efc": 8000})
        sheet = workbook[audit_sheets.PRO_FORMA_SHEET]
        return {str(sheet.cell(row=r, column=1).value): str(sheet.cell(row=r, column=5).value)
                for r in range(1, sheet.max_row + 1)}, workbook

    def test_fade_rows_and_names_only_when_the_block_exists(self):
        plain, wb_plain = self._formulas(_fake_cash_flow_result())
        self.assertNotIn("Battery SOH factor (year average)", plain)
        self.assertNotIn("BESS_ENERGY_REV", wb_plain.defined_names)
        faded, wb = self._formulas(self._with_fade())
        self.assertIn("Battery SOH factor (year average)", faded)
        for name in ("BESS_ENERGY_REV", "BESS_SERVED_RETAIL", "BESS_UNSERVED_VALUE",
                     "BESS_DEMAND_SAVINGS", "BESS_MATCHED_SHARE"):
            self.assertIn(name, wb.defined_names)

    def test_esco_formulas_carry_the_soh_terms(self):
        faded, _ = self._formulas(self._with_fade())
        self.assertIn("BESS_ENERGY_REV", faded["ESCO energy revenue (discount-to-EVN)"])
        self.assertIn("BESS_DEMAND_SAVINGS", faded["Demand charge savings (total)"])
        self.assertIn("BESS_UNSERVED_VALUE", faded["Buyer cost with project"])
        self.assertIn("BESS_DEMAND_SAVINGS", faded["Buyer cost with project"])

    def test_plain_formulas_are_unchanged(self):
        plain, _ = self._formulas(_fake_cash_flow_result())
        self.assertEqual(plain["Demand charge savings (total)"], "=BASE_DEMAND_SAVINGS*E{}".format(
            _row_of(plain, "EVN capacity escalation factor")))   # or compare against a frozen string

    def test_replacement_section_states_the_switch(self):
        _, wb = self._formulas(self._with_fade())
        labels = [str(c.value) for c in wb["Assumptions"]["A"]]
        self.assertIn("Battery replacement", labels)
        self.assertIn("Battery cycle life (EFC to 80 percent)", labels)
        self.assertNotIn("BESS replacement year (storage inverter and pack together)", labels)
        _, wb_on = self._formulas(self._with_fade(), {"bess_replacement_enabled": True,
                                                       "battery_replacement_year": 10,
                                                       "bess_replace_cost_per_kw": 80.0,
                                                       "bess_replace_cost_per_kwh": 120.0,
                                                       "bess_cycle_life_efc": 8000})
        labels_on = [str(c.value) for c in wb_on["Assumptions"]["A"]]
        self.assertIn("BESS replacement year (storage inverter and pack together)", labels_on)

    def test_no_em_dash_in_new_text(self):
        _, wb = self._formulas(self._with_fade())
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                for value in row:
                    if isinstance(value, str) and ("SOH" in value or "cycle life" in value.lower()):
                        self.assertNotIn("\u2014", value)
```

For `test_plain_formulas_are_unchanged` the simplest robust form: build the plain workbook once on master's code (before this task) into `proforma_vietnam/tests/fixtures/plain_formulas.json` (label -> formula for the Pro Forma sheet) and assert equality with the post-change plain build. Do that in Step 2 before editing.

- [ ] **Step 2: Freeze the plain formulas, run to verify failure**

Write a scratch script that builds the plain fake workbook with the current code and dumps `{label: formula}` for column E of `PRO_FORMA_SHEET` to `proforma_vietnam/tests/fixtures/plain_formulas.json`. Then run:
`./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_audit_sheets.BatteryFadeAuditTests -v`
Expected: FAIL (no SOH row, no names).

- [ ] **Step 3: Implement**

1. `CURATED_ASSUMPTION_KEYS`: add `"bess_replacement_enabled", "bess_cycle_life_efc"`.
2. Replacement Policy section (line 392): condition becomes `if assumptions.get("bess_replacement_enabled") is not None or assumptions.get("battery_replacement_year") or assumptions.get("pv_inverter_replacement_year")`. Inside, before the `battery_replacement_year` branch:

```python
        if assumptions.get("bess_replacement_enabled") is False:
            entry("Battery replacement",
                  "Not scheduled inside the {} year horizon".format(
                      (derivation or {}).get("project_years", DEFAULT_PROJECT_YEARS)),
                  source="Client direction 2026-09-12: capacity fade is carried on the Battery SOH "
                         "sheet and derates the battery's savings; REopt sent replace_cost 0. "
                         "Opt in per case with technologies.storage.replacement")
        if assumptions.get("bess_cycle_life_efc") is not None:
            entry("Battery cycle life (EFC to 80 percent)", assumptions["bess_cycle_life_efc"],
                  unit="cycles", source="proforma_vietnam.defaults BESS_CYCLE_LIFE_EFC unless "
                                         "case.json technologies.storage.cycle_life_efc overrides",
                  name="BESS_CYCLE_LIFE", fmt="#,##0")
```

3. Named engine inputs (after `BASE_SERVED_RETAIL`, inside the "Year-1 Engine Outputs" section):

```python
    fade = d.get("battery_fade")
    if fade:
        entry("Year-1 battery energy revenue base", fade.get("energy_revenue_usd", 0.0), unit="USD",
              source="Battery-served kWh x TOU rate x ESCO discount ({})".format(fade.get("energy_attribution")),
              name="BESS_ENERGY_REV", fmt=FMT_AMOUNT)
        entry("Year-1 battery served-energy retail value", fade.get("served_retail_value_usd", 0.0),
              unit="USD", source="Battery-served kWh x TOU rate", name="BESS_SERVED_RETAIL", fmt=FMT_AMOUNT)
        entry("Year-1 battery net energy value outside served", fade.get("unserved_energy_value_usd", 0.0),
              unit="USD", source="Discharge at retail minus grid charging (direct ownership / battery-only)",
              name="BESS_UNSERVED_VALUE", fmt=FMT_AMOUNT)
        entry("Year-1 battery demand relief", fade.get("demand_savings_usd", 0.0), unit="USD",
              source="PV-only counterfactual demand charge minus solved ({})".format(fade.get("demand_attribution")),
              name="BESS_DEMAND_SAVINGS", fmt=FMT_AMOUNT)
        entry("Battery share of matched energy", fade.get("matched_energy_share", 0.0), unit="fraction",
              source="Battery-served kWh / project-served kWh", name="BESS_MATCHED_SHARE", fmt=FMT_PERCENT)
```

4. In `write_pro_forma_audit_sheet`, after `r_fac_deg`:

```python
    fade = d.get("battery_fade")
    has_fade = bool(fade)
    if has_fade:
        r_fac_soh = w.line(
            "fac_soh", "Battery SOH factor (year average)", "index",
            values=[1.0] + list(fade["soh_by_year"]), fill=INPUT_FILL, fmt=FMT_FACTOR)
        if is_dppa or is_physical:
            r_fac_gen = w.line(
                "fac_gen", "Generation factor (PV degradation, battery SOH)", "index",
                formula=lambda y, c: f"=(1-BESS_MATCHED_SHARE)*{c}{r_fac_deg}+BESS_MATCHED_SHARE*{c}{r_fac_soh}",
                fmt=FMT_FACTOR)
        else:
            r_fac_gen = r_fac_deg
    else:
        r_fac_gen = r_fac_deg

    def repurchase(c):
        if not has_fade:
            return f"BASE_SERVED_RETAIL*(1-{c}{r_fac_deg})"
        return (f"(BASE_SERVED_RETAIL-BESS_SERVED_RETAIL)*(1-{c}{r_fac_deg})"
                f"+(BESS_SERVED_RETAIL+BESS_UNSERVED_VALUE)*(1-{c}{r_fac_soh})")

    def lost_demand(c):
        return f"+BESS_DEMAND_SAVINGS*(1-{c}{r_fac_soh})*{c}{r_fac_capacity}" if has_fade else ""
```

Then change formulas:
- DPPA `fmp_rev`, `c_dn`, `c_dppa`, `c_cl`: `r_fac_deg` -> `r_fac_gen`; `c_bl`: `(1-{c}{r_fac_gen})`.
- physical `energy_rev`: `*{c}{r_fac_gen}`.
- direct `energy_rev`: `f"=BAU_BILL_Y1*{c}{r_fac_energy}-((OPT_BILL_Y1+{repurchase(c)})*{c}{r_fac_energy}{lost_demand(c)})"`.
- ESCO `energy_rev`: with fade `f"((BASE_ENERGY_REV-BESS_ENERGY_REV)*{c}{r_fac_deg}+BESS_ENERGY_REV*{c}{r_fac_soh})*{c}{r_fac_energy}"`, else unchanged text.
- `dem_savings`: with fade `f"=((BASE_DEMAND_SAVINGS-BESS_DEMAND_SAVINGS)+BESS_DEMAND_SAVINGS*{c}{r_fac_soh})*{c}{r_fac_capacity}"`, else unchanged.
- `arb_rev`: with fade `f"BASE_GRID_ARB*{c}{r_fac_soh}*{c}{r_fac_energy}"`, else unchanged.
- offtaker `post_cost` direct: `f"=(OPT_BILL_Y1+{repurchase(c)})*{c}{r_fac_energy}{lost_demand(c)}"`; ESCO: same prefix plus `+energy_rev+dem_rev+arb_rev`; DPPA: append `{lost_demand(c)}`.

Every unchanged branch must produce the exact same formula text as before (the frozen fixture test guards it).

5. `_replacement_bullet`: when `assumptions.get("bess_replacement_enabled") is False`, start the bullet with "Battery: no scheduled replacement inside the horizon (client direction 2026-09-12); capacity fade is carried by the Battery SOH curve and derates the battery's savings each year." then the PV inverter sentence as today.

6. Model Basis "4. Multi-year mechanics": after `_replacement_bullet(...)` add, when `derivation.get("battery_fade")`:

```python
            "Battery state of health: REopt.jl v0.57.0's daily fade recurrence (calendar fade on the "
            "average stored energy, cycle fade on the energy discharged) replayed over the horizon on "
            "the solved year-1 dispatch, with the hours-per-time-step factor removed so 15 minute and "
            "hourly solves age alike. Cycle life {cycles:,} EFC to 80 percent sets the cycle coefficient. "
            "The battery's share of energy revenue, retail repurchase, demand relief and grid arbitrage "
            "is multiplied by the year's average SOH; energy delivered is assumed to scale with capacity "
            "(the battery treated as capacity-bound every day), an upper bound on the loss. The optimiser "
            "does not see the curve. See the Battery SOH sheet.".format(cycles=int(cycle_life))
```

with `cycle_life = (derivation["battery_fade"].get("soh") or {}).get("coefficients", {}).get("cycle_life_efc") or assumptions.get("bess_cycle_life_efc") or 8000`.

- [ ] **Step 4: Run the audit and builder suites**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_audit_sheets proforma_vietnam.tests.test_xlsx_builder proforma_vietnam.tests.test_validate_workbook -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/audit_sheets.py proforma_vietnam/tests/test_audit_sheets.py proforma_vietnam/tests/fixtures/plain_formulas.json
git commit -m "Audit sheet: SOH factor and battery terms in the live formulas; replacement switch rows"
```

---

### Task 10: Battery SOH sheet

**Files:**
- Modify: `proforma_vietnam/xlsx_builder.py:1-30` (imports, constants), `:250-256` (sheet order), new `_write_battery_soh_sheet` near `_write_dispatch_sheet`
- Modify: `proforma_vietnam/audit_sheets.py:2640-2655` (cover guide)
- Test: `proforma_vietnam/tests/test_xlsx_builder.py` (new class `BatterySohSheetTests`)

**Interfaces:**
- Consumes: `derivation["battery_fade"]["soh"]` (Task 5 shape), rows `battery_fade_loss_usd`.
- Produces: sheet titled `Battery SOH`.

- [ ] **Step 1: Write the failing tests**

```python
class BatterySohSheetTests(TestCase):

    def test_sheet_present_only_with_a_fade_block(self):
        plain = build_vietnam_esco_workbook(_fake_cash_flow_result(), {})
        self.assertNotIn("Battery SOH", plain.sheetnames)
        faded = build_vietnam_esco_workbook(_with_fade_result(), {"bess_cycle_life_efc": 8000})
        self.assertIn("Battery SOH", faded.sheetnames)
        sheet = faded["Battery SOH"]
        text = [str(c.value) for row in sheet.iter_rows() for c in row if c.value is not None]
        self.assertTrue(any("8,000" in t or "8000" in t for t in text))
        self.assertTrue(any(t.startswith("Year") for t in text))
        self.assertEqual(len(sheet._charts), 1)
        cover = [str(c.value) for c in faded["Cover"]["B"]]
        self.assertIn("Battery SOH", cover)

    def test_year_rows_and_loss_column(self):
        faded = build_vietnam_esco_workbook(_with_fade_result(), {"bess_cycle_life_efc": 8000})
        sheet = faded["Battery SOH"]
        header_row = next(r for r in range(1, sheet.max_row + 1) if sheet.cell(row=r, column=1).value == "Year")
        headers = [sheet.cell(row=header_row, column=c).value for c in range(1, 10)]
        self.assertEqual(headers[-1], "Value lost to fade (USD)")
        self.assertEqual(sheet.cell(row=header_row + 1, column=1).value, 0)
        self.assertEqual(sheet.cell(row=header_row + 1, column=2).value, 1.0)
        years = len(_with_fade_result()["annual_cash_flows"])
        self.assertEqual(sheet.cell(row=header_row + 1 + years, column=1).value, years)
```

Move the `_with_fade` builder from Task 9 into a shared helper `_with_fade_result()` (module-level in `test_xlsx_builder.py`, imported by `test_audit_sheets.py`, or duplicated; duplication is acceptable across the two test files).

- [ ] **Step 2: Run to verify failure**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_xlsx_builder.BatterySohSheetTests -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

In `xlsx_builder.py` add after `_write_dispatch_sheet`:

```python
SOH_COLUMNS = [
    ("Year", "year"),
    ("SOH end of year", "soh_end"),
    ("SOH year average (derate factor)", "soh_average"),
    ("Usable capacity (kWh)", "usable_kwh_end"),
    ("EFC in year", "efc_in_year"),
    ("Cumulative EFC", "efc_cumulative"),
    ("Calendar fade (kWh)", "calendar_fade_kwh"),
    ("Cycle fade (kWh)", "cycle_fade_kwh"),
    ("Value lost to fade (USD)", "fade_loss_usd"),
]


def _write_battery_soh_sheet(worksheet, cash_flow_result, profile=VIETNAM_PROFILE):
    """State of health curve replayed from the solved dispatch, with the derate it drives."""
    fade = (cash_flow_result.get("derivation") or {}).get("battery_fade") or {}
    soh = fade.get("soh") or {}
    coefficients = soh.get("coefficients") or {}
    annual = cash_flow_result.get("annual_cash_flows") or []
    loss_by_year = {row["year"]: row.get("battery_fade_loss_usd", row.get("battery_fade_loss_vnd", 0.0))
                    for row in annual}
    years = soh.get("years") or []
    horizon = soh.get("project_years") or len(years)
    first_below = soh.get("first_year_below_end_of_life")
    cycle_life = coefficients.get("cycle_life_efc")

    row = 1
    worksheet.cell(row=row, column=1, value="Battery state of health").font = TITLE_FONT
    row += 2
    for line in (
        "Method: REopt.jl v0.57.0 daily fade recurrence replayed over the horizon on the solved year-1 "
        "dispatch. SOH[d] = SOH[d-1] - (k_cal x a x Eavg[d-1] x d^(a-1) + k_cyc x E_discharged[d-1]), "
        "SOH in kWh, with the hours-per-time-step factor removed so 15 minute and hourly solves age alike.",
        "Cycle fade: k_cyc = (1 - 0.80) / cycle life = {:.3e} kWh lost per kWh discharged"
        " (cycle life {} EFC to 80 percent).".format(
            coefficients.get("cycle_fade_coefficient", 0.0),
            "{:,.0f}".format(cycle_life) if cycle_life else "n/a"),
        "Calendar fade: k_cal = {:.2e}, exponent a = {} (NREL laboratory defaults, no chemistry or "
        "temperature calibration).".format(coefficients.get("calendar_fade_coefficient", 0.0),
                                           coefficients.get("calendar_fade_exponent", 0.0)),
        "Use: the year-average SOH multiplies the battery's share of the savings on the Pro Forma "
        "(Audit) sheet (row 'Battery SOH factor'). Energy delivered is assumed to scale with capacity, "
        "the battery treated as capacity-bound every day: an upper bound on the loss. The optimiser "
        "does not see this curve; no battery replacement is scheduled unless the case opts in.",
        "Energy attribution: {}. Demand attribution: {}.".format(
            fade.get("energy_attribution"), fade.get("demand_attribution")),
    ):
        worksheet.cell(row=row, column=1, value=line).font = NOTE_FONT
        row += 1
    row += 1

    def result_line(label, value, fmt=None):
        nonlocal row
        worksheet.cell(row=row, column=1, value=label).font = BOLD_FONT
        cell = worksheet.cell(row=row, column=2, value=value)
        if fmt:
            cell.number_format = fmt
        row += 1

    by_year = {entry["year"]: entry for entry in years}
    result_line("Nominal capacity (kWh)", soh.get("size_kwh"), FORMAT_AMOUNT)
    result_line("SOH end of year 10", (by_year.get(10) or {}).get("soh_end"), FORMAT_PERCENT)
    result_line("SOH end of year {}".format(horizon), (by_year.get(horizon) or {}).get("soh_end"), FORMAT_PERCENT)
    result_line("First year below 80 percent", first_below if first_below else
                "Not within the {} year horizon".format(horizon))
    result_line("Equivalent full cycles, year 1", soh.get("year_one_efc"), FORMAT_AMOUNT)
    result_line("Equivalent full cycles, cumulative", (by_year.get(horizon) or {}).get("efc_cumulative"), FORMAT_AMOUNT)
    result_line("Average daily discharge, year 1 (kWh)", soh.get("year_one_daily_discharge_kwh"), FORMAT_AMOUNT)
    result_line("Value lost to fade over the horizon (USD)", sum(loss_by_year.values()), FORMAT_AMOUNT)
    row += 1

    header_row = row
    for column_index, (header, _key) in enumerate(SOH_COLUMNS, start=1):
        cell = worksheet.cell(row=row, column=column_index, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
    row += 1
    table = [{"year": 0, "soh_end": 1.0, "soh_average": 1.0, "usable_kwh_end": soh.get("size_kwh"),
              "efc_in_year": 0.0, "efc_cumulative": 0.0, "calendar_fade_kwh": 0.0,
              "cycle_fade_kwh": 0.0, "fade_loss_usd": 0.0}]
    for entry in years:
        table.append({**entry, "fade_loss_usd": loss_by_year.get(entry["year"], 0.0)})
    for entry in table:
        for column_index, (_header, key) in enumerate(SOH_COLUMNS, start=1):
            cell = worksheet.cell(row=row, column=column_index, value=entry.get(key))
            if key in ("soh_end", "soh_average"):
                cell.number_format = FORMAT_PERCENT
            elif key != "year":
                cell.number_format = FORMAT_AMOUNT
        row += 1
    last_row = row - 1
    threshold_col = len(SOH_COLUMNS) + 1
    worksheet.cell(row=header_row, column=threshold_col, value="End of life (80 percent)").font = HEADER_FONT
    for r in range(header_row + 1, last_row + 1):
        worksheet.cell(row=r, column=threshold_col, value=0.8).number_format = FORMAT_PERCENT

    chart = LineChart()
    chart.title = "Battery state of health by year"
    chart.y_axis.title = "SOH (fraction of nominal kWh)"
    chart.x_axis.title = "Year"
    chart.y_axis.scaling.min = 0.7
    chart.y_axis.scaling.max = 1.0
    for column, title in ((2, "SOH end of year"), (threshold_col, "End of life (80 percent)")):
        chart.series.append(Series(Reference(worksheet, min_col=column, min_row=header_row + 1, max_row=last_row), title=title))
    chart.set_categories(Reference(worksheet, min_col=1, min_row=header_row + 1, max_row=last_row))
    chart.height = 9
    chart.width = 20
    worksheet.add_chart(chart, "L{}".format(header_row))
    worksheet.column_dimensions["A"].width = 44
```

Use the module's existing font/format constants (`TITLE_FONT`, `BOLD_FONT`, `NOTE_FONT`, `HEADER_FONT`, `HEADER_FILL`, `FORMAT_AMOUNT`, `FORMAT_PERCENT`; check their exact names at the top of `xlsx_builder.py` and in `audit_sheets`, importing where needed). In `build_vietnam_esco_workbook` after `_write_technical_results`:

```python
    if (derivation or {}).get("battery_fade"):
        _write_battery_soh_sheet(workbook.create_sheet("Battery SOH"), cash_flow_result, profile=profile)
```

Add `"Battery SOH"` to `CUSTOM_LAYOUT_SHEETS` so it is not autosized (the note lines are long). Cover guide (`audit_sheets.py` ~2650): after the `("Technical Results", ...)` tuple insert conditionally:

```python
    if (derivation or {}).get("battery_fade"):
        guide.insert(
            guide.index(("Technical Results", "System sizing, year-1 energy balance, bill comparison")) + 1,
            ("Battery SOH", "State of health replayed from the solved dispatch; drives the battery derate"),
        )
```

(`write_cover_sheet` already receives `derivation`.)

- [ ] **Step 4: Run the builder and audit suites**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_xlsx_builder proforma_vietnam.tests.test_audit_sheets -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/xlsx_builder.py proforma_vietnam/audit_sheets.py proforma_vietnam/tests/test_xlsx_builder.py
git commit -m "Battery SOH sheet with the curve and the value lost to fade"
```

---

### Task 11: Docs, notes, dry-run regeneration, full suites

**Files:**
- Modify: `outputs/vietnam_case/factory_a/CASE_JSON_INPUT_GUIDE.md`, `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`, `proforma_vietnam/MODEL_AUDIT.md`
- Regenerate: `payload.json` and `assumptions.json` in all 14 case directories (dry run, no solve)

- [ ] **Step 1: Docs**

- `CASE_JSON_INPUT_GUIDE.md`: in the storage section replace the 2026-09-11 replacement paragraph with the `replacement` block (fields, defaults, the raw-key refusal) and add `cycle_life_efc`.
- `ESCO_CONTRACT_MODEL_DESIGN.md`: update the replacement-policy paragraph and add a "Battery ageing" subsection: SOH recurrence, h = 1, cycle life 8,000, the derate per structure (the table from the spec's Part C), capacity-bound assumption.
- `MODEL_AUDIT.md`: dated note 2026-09-12 (second entry): replacement default off, SOH derate, the demand counterfactual tie-outs, what is out of scope.

No em dash in any of them.

- [ ] **Step 2: Dry-run regenerate the 14 records**

Use the case builders offline the way the 2026-09-11 Task 7 did (`task7_strip.py` / `task7_assert.py` in the scratchpad show the pattern): for each of the 8 Vietnam and 6 Thailand case directories, rebuild `payload.json` and `assumptions.json` from `case.json` without solving, then assert for storage cases: `ElectricStorage.replace_cost_per_kw == 0.0`, no `battery_replacement_year` in the payload, `assumptions.bess_replacement_enabled is False`, `assumptions.bess_cycle_life_efc == 8000`, no `battery_replacement_year` in assumptions; for PV-only cases: none of these keys. Vietnam PVWatts series must come from the existing payload (do not refetch): copy `production_factor_series` handling exactly as the 2026-09-11 script did.

- [ ] **Step 3: Full suites**

Run all three suites. Expected: all green; record the counts (Vietnam should be about 551 + ~30, Thailand about 143).

- [ ] **Step 4: Commit**

```bash
git add outputs/vietnam_case/factory_a/CASE_JSON_INPUT_GUIDE.md proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md proforma_vietnam/MODEL_AUDIT.md outputs/
git status --short   # confirm only payload.json / assumptions.json under outputs/ are staged, never the locked or review workbooks
git commit -m "Docs and regenerated case records for the replacement switch and SOH policy"
```

---

### Task 12: Re-solve, rebuild, gate, reconcile, handoff

**Files:**
- Results/workbooks under `outputs/` (9 solves, 14 workbooks), gate baselines (`baseline_workbooks/`, gitignored), `SESSION_NOTES.md`
- Scratchpad scripts: `resolve_soh.sh`, `verify_echo_soh.py`, `rebuild_soh.py`, `reconcile_soh.py`

- [ ] **Step 1: Gate inspection before solving (regression proof)**

Rebuild the 5 PV-only workbooks (Vietnam case_4; Thailand case_1..4) from their existing results with the new code and run `compare_workbooks` against the current baselines. Expected: 0 numeric diffs each. If not, the new code is not inert without a battery: stop and fix before solving anything.

- [ ] **Step 2: Docker readiness and re-solve the nine storage cases**

Check `docker ps`; if the stack is down, `docker-compose up -d` and wait for Julia `/health` 200 and Django `GET /v3/job/` 405. Write `resolve_soh.sh` on the 2026-09-11 `resolve2.sh` pattern for: `outputs/vietnam_case/factory_a/case_{1,2,3,5,6}`, `outputs/vietnam_case/bess_arbitrage_5mw`, `outputs/vietnam_case/bess_arbitrage_5mw_mfg` (`python -m proforma_vietnam.run_case --case <dir>/case.json --max-polls 480`) and `outputs/thailand_case/rofu_thailand/case_{5,6}` (`python -m proforma_thailand.run_case ...`). After each solve run `verify_echo_soh.py <dir> <country>`: the echoed `inputs.ElectricStorage` must show `replace_cost_per_kw == 0.0`, `replace_cost_per_kwh == 0.0`; PV price 480/500 checks as in `verify_echo.py`; new results file present with a new run uuid. Run in the background with a log; poll the log, do not sleep-loop.

- [ ] **Step 3: Rebuild all 14 workbooks**

`rebuild_soh.py`: for each of the 14 directories call the country's `rebuild_report` (Vietnam: `proforma_vietnam.rebuild_report`, Thailand: `proforma_thailand.rebuild_report`), select the results file by the run uuid recorded in the newest `results*.json`, and assert for the 9 storage cases that the workbook has a `Battery SOH` sheet and for the 5 PV-only that it does not. Thailand `summary.json` for case_5/6 is regenerated by its rebuild path if that is what 2026-09-11 did (check `task9_rebuild.py`); keep the same behaviour.

- [ ] **Step 4: Validate and gate**

Run `python -m proforma_vietnam.validate_workbook` on the 9 storage workbooks (Excel COM; if Excel refuses because the user's instance holds files, record that and fall back to reading the tie-out formulas only). Regenerate gate baselines for the 9 storage cases only after the reconcile table (Step 5) is written; the 5 PV-only baselines are untouched and must still show 0 diffs. `compare_workbooks` final run: TOTAL DIFFS 0 on 14.

- [ ] **Step 5: Reconcile table**

`reconcile_soh.py`: old (2026-09-11 baseline workbooks or the summary values recorded in SESSION_NOTES) vs new for the 9 cases: PV kW, BESS kW/kWh, total capex, equity NPV, equity IRR, min DSCR, year-10 CFADS, SOH end y10 and y20, first year below 80 percent, lifetime value lost to fade, battery demand relief y1, energy attribution. Read the new values from the workbooks by uuid (Vietnam NPV label is "NPV (USD)"; Thailand "Equity NPV (USD)" per the 2026-09-11 reconcile script) and from `derivation` via a rebuild in-process.

- [ ] **Step 6: SESSION_NOTES handoff**

Prepend a 2026-09-12 (evening) handoff: rulings (including 8,000 EFC and h = 1), the branch name and "not merged, not pushed", code map, reconcile table, the 5-case 0-diff proof, validator outcome, SOH results per case with the Thailand h = 1 number confirmed, deliverables marked stale (memo EN/VI, pptx, artifact: year-10 DSCR paragraph no longer applies), housekeeping (the two locked old workbooks still to delete), follow-ups (LFP calendar calibration, replacement reserve now moot unless a case opts in, DPPA energy-share vs value-share, SOH not fed to dispatch). Close register item on replacement reserve as superseded; add an item for "battery savings attribution under ESCO with grid-charged storage beside PV: not booked".

- [ ] **Step 7: graphify and final commit**

Run `graphify update .` (AST-only). Commit results, workbooks, summaries, notes:

```bash
git add outputs/ SESSION_NOTES.md graphify-out/
git status --short   # the two locked old case_6 workbooks and review files must not be staged
git commit -m "Re-solve the nine storage cases without a scheduled replacement; rebuild all fourteen workbooks; handoff"
git log --oneline master..battery-soh-fade
```

Leave the branch checked out. Do not merge. Do not push.
