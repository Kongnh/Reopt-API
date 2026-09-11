# Replacement Policy Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Book the same equipment replacement rule in both country branches (whole BESS at year 10 at 100 percent of install, PV inverter at 10 percent of solved PV capex in year 11, 20-year horizon), enforce it at import, re-solve the ten cases it changes, and reissue every figure that moves.

**Architecture:** `proforma_vietnam` is the shared financial core; `proforma_thailand` drives the same engine with Thai defaults. The rule becomes five constants in `proforma_vietnam.defaults`; each country's JSON must agree with them or its package fails to import. Both case builders derive the REopt replacement inputs from the policy and the effective install price, and write what they sent into `assumptions` so the workbook reads a record, never a live default. The PV inverter derivation moves from the Thailand report layer into the core so both countries book it from one function.

**Tech Stack:** Python 3.14 (`./.venv/Scripts/python.exe`), unittest, openpyxl, Docker stack (Django + Celery + Julia/HiGHS), REopt.jl v0.57.0.

**Spec:** `docs/superpowers/specs/2026-09-11-replacement-policy-sync-design.md`

## Global Constraints

- Never create, modify or delete anything under `reo/`.
- Never modify the client source `.xlsm` files under the Keen Project folder.
- No em dash (U+2014) in any generated report output, memo, or note written in this pass. Check with `python -c "print(open(p,encoding='utf-8').read().count('\u2014'))"`.
- The placeholder marker is exactly `PLACEHOLDER - pending Keen confirmation`, matched by equality; never invent a variant.
- `baseline_workbooks/` is gitignored scratch (`.gitignore:139`). Never `git add -f` it, never edit that rule.
- The user's untracked `outputs/vietnam_case/factory_a/case_*/vietnam_report_review*.xlsx` files must not be touched. Select workbooks by run uuid, never by `sorted(glob)[-1]`.
- No `git push`. The user pushes.
- Every commit message ends with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Suites run from the repo root:

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
./.venv/Scripts/python.exe -m unittest reoptjl.test.test_thailand_tariff -v
```

- Gate, from the repo root; delete `gate_check/` afterwards, never commit it:

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

Baseline at plan start (master `cc782d2f`): Thailand 137/137, Vietnam 532/532, tariff 14/14, gate TOTAL DIFFS 0 on 14 cases.

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `proforma_vietnam/defaults/__init__.py` | Policy constants; Vietnam guard | 1 |
| `proforma_vietnam/defaults/vietnam_defaults.json` | `project_years` 20 | 1 |
| `proforma_vietnam/tests/test_defaults.py` | **New.** Policy and guard tests | 1 |
| `proforma_thailand/defaults/thailand_defaults.json` | 100 percent replacement; `pv_inverter_*` keys | 2 |
| `proforma_thailand/defaults/__init__.py` | Couplings use the policy fraction; policy guard | 2 |
| `proforma_thailand/tests/test_thailand_defaults.py` | Coupling tests at 100 percent; guard tests | 2 |
| `proforma_vietnam/case_builder.py` | Derive replacement from policy; horizon from `DEFAULT_PROJECT_YEARS`; record in assumptions | 3 |
| `proforma_vietnam/tests/test_case_builder.py` | Derivation, override, horizon tests | 3 |
| `proforma_thailand/case_builder.py` | Same derivation; explicit years; record in assumptions | 4 |
| `proforma_thailand/tests/test_case_builder.py` | Same | 4 |
| `proforma_vietnam/esco_pro_forma.py` | PV inverter event derived in core; derivation block | 5 |
| `proforma_thailand/report.py` | Delete local derivation; pass policy keys | 5 |
| `proforma_vietnam/run_dppa_negotiation_sweep.py` | Map the two keys | 5 |
| `proforma_vietnam/run_case.py`, `reoptjl/views.py` | Forward the two keys through the API | 5 |
| `proforma_vietnam/tests/test_esco_pro_forma.py`, `proforma_thailand/tests/test_report.py` | Core derivation tests; Thailand report tests rewritten | 5 |
| `proforma_vietnam/audit_sheets.py` | Replacement Policy section; labels; Model Basis from data | 6 |
| `proforma_vietnam/tests/test_audit_sheets.py` | Sheet text tests | 6 |
| `outputs/vietnam_case/**/case.json` (8 files) | Drop the five policy-owned keys and `analysis_years` | 7 |
| `outputs/vietnam_case/factory_a/CASE_JSON_INPUT_GUIDE.md`, `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md`, `proforma_vietnam/MODEL_AUDIT.md` | Say what the policy is | 7 |
| `outputs/**/payload.json`, `assumptions.json` (14) | Regenerated by dry-run | 7 |
| `outputs/**/results.json` (10) | Re-solved | 8 |
| `outputs/**/*_report_<uuid>.xlsx` (14), `baseline_workbooks/` | Rebuilt, re-baselined | 9 |
| scratchpad `soh_check.py`, `soh_check.md` | Throwaway degradation check | 10 |
| `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md`, `_VI.md`, `Rofu_Thailand_Tariff_Structure_Internal.pptx`, HTML artifact | Reissued | 11 |
| `SESSION_NOTES.md` | Handoff; register items 17, 18 closed; new item | 12 |

---

### Task 1: Policy constants in the shared core; Vietnam horizon to 20

**Files:**
- Modify: `proforma_vietnam/defaults/__init__.py` (after `SURPLUS_EXPORT_DEFAULTS = ...`, line 21)
- Modify: `proforma_vietnam/defaults/vietnam_defaults.json` (`financial.project_years`)
- Create: `proforma_vietnam/tests/test_defaults.py`

**Interfaces:**
- Produces: `proforma_vietnam.defaults.PROJECT_YEARS: int = 20`, `BESS_REPLACEMENT_YEAR: int = 10`, `BESS_REPLACE_FRACTION_OF_INSTALL: float = 1.0`, `PV_INVERTER_REPLACEMENT_YEAR: int = 11`, `PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX: float = 0.10`, and `proforma_vietnam.defaults._assert_policy_holds() -> None` (raises `ValueError`).

- [ ] **Step 1: Write the failing tests**

```python
# proforma_vietnam/tests/test_defaults.py
from unittest import TestCase


class ReplacementPolicyTests(TestCase):
    """The rule both countries book. Numbers here are the 2026-09-11 rulings;
    a change to any of them is a change to both countries' deliverables."""

    def test_policy_constants(self):
        from proforma_vietnam import defaults

        self.assertEqual(defaults.PROJECT_YEARS, 20)
        self.assertEqual(defaults.BESS_REPLACEMENT_YEAR, 10)
        self.assertEqual(defaults.BESS_REPLACE_FRACTION_OF_INSTALL, 1.0)
        self.assertEqual(defaults.PV_INVERTER_REPLACEMENT_YEAR, 11)
        self.assertEqual(defaults.PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX, 0.10)

    def test_vietnam_horizon_matches_the_policy(self):
        from proforma_vietnam.defaults import FINANCIAL_DEFAULTS, PROJECT_YEARS

        self.assertEqual(FINANCIAL_DEFAULTS["project_years"], PROJECT_YEARS)

    def test_a_desynced_horizon_fails_at_import(self):
        from proforma_vietnam import defaults

        original = defaults.FINANCIAL_DEFAULTS["project_years"]
        defaults.FINANCIAL_DEFAULTS["project_years"] = 25
        try:
            with self.assertRaises(ValueError):
                defaults._assert_policy_holds()
        finally:
            defaults.FINANCIAL_DEFAULTS["project_years"] = original
```

- [ ] **Step 2: Run to verify they fail**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_defaults -v`
Expected: FAIL, `AttributeError: module 'proforma_vietnam.defaults' has no attribute 'PROJECT_YEARS'`.

- [ ] **Step 3: Add the constants and the guard**

In `proforma_vietnam/defaults/__init__.py`, after `SURPLUS_EXPORT_DEFAULTS = _DEFAULTS["surplus_export"]`:

```python
# Equipment replacement policy shared by every country branch (rulings of
# 2026-09-11). A country's JSON carries its own prices and provenance, but its
# horizon and replacement schedule must agree with these or its defaults
# module refuses to import; that is what keeps the two branches from drifting.
PROJECT_YEARS = 20
BESS_REPLACEMENT_YEAR = 10                       # storage inverter and pack together
BESS_REPLACE_FRACTION_OF_INSTALL = 1.0           # replacement priced at install cost
PV_INVERTER_REPLACEMENT_YEAR = 11
PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX = 0.10


def _assert_policy_holds():
    if FINANCIAL_DEFAULTS["project_years"] != PROJECT_YEARS:
        raise ValueError(
            "vietnam_defaults.json financial.project_years is {} but the shared "
            "replacement policy is {} years. Change the policy for both countries "
            "or re-derive the JSON.".format(
                FINANCIAL_DEFAULTS["project_years"], PROJECT_YEARS
            )
        )


_assert_policy_holds()
```

In `proforma_vietnam/defaults/vietnam_defaults.json`, change `"project_years": 25` to `"project_years": 20`.

- [ ] **Step 4: Run the new tests**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_defaults -v`
Expected: 3 passed.

- [ ] **Step 5: Run the Vietnam suite and triage fixtures that relied on the 25-year default**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . 2>&1 | tail -30`

For each failure, open the test. Two kinds only:
- The test asserts the default itself (for example `assertEqual(derivation["project_years"], 25)` with no `project_years` argument passed): change the expected value to 20.
- The test's arithmetic silently assumed 25 (a hand-computed NPV, a `[0.0] * 24` series, a reference workbook built at 25): pass `project_years=25` explicitly to the call under test and leave the expectation alone. `test_reference_esco_workbook.py` is this kind.

Do not change any test that already passes `project_years=` explicitly.

Run the suite again. Expected: 535 passed (532 + 3).

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/defaults/__init__.py proforma_vietnam/defaults/vietnam_defaults.json proforma_vietnam/tests/
git commit -m "Shared replacement policy constants; Vietnam horizon to 20 years

Five constants in proforma_vietnam.defaults carry the 2026-09-11 rulings.
vietnam_defaults.json project_years moves 25 to 20 and is asserted equal to
the policy at import.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Thailand defaults at 100 percent, PV inverter keys renamed, guards

**Files:**
- Modify: `proforma_thailand/defaults/thailand_defaults.json` (`financial.bess_replace_cost_per_kw`, `bess_replace_cost_per_kwh`, `inverter_replacement_year`, `inverter_replacement_fraction_of_pv_capex`)
- Modify: `proforma_thailand/defaults/__init__.py:64-84`
- Modify: `proforma_thailand/tests/test_thailand_defaults.py:154-175` and every reference to the renamed keys in `proforma_thailand/tests/`

**Interfaces:**
- Consumes: `BESS_REPLACE_FRACTION_OF_INSTALL`, `PROJECT_YEARS`, `PV_INVERTER_REPLACEMENT_YEAR`, `PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX` from Task 1.
- Produces: `FINANCIAL_DEFAULTS["pv_inverter_replacement_year"]`, `FINANCIAL_DEFAULTS["pv_inverter_replacement_fraction_of_pv_capex"]` (renamed), `proforma_thailand.defaults._assert_policy_holds()`.

- [ ] **Step 1: Rewrite the coupling tests and add the guard tests**

Replace `test_replacement_is_seventy_percent_of_install` and edit `test_replacing_never_costs_more_than_buying_new`:

```python
    def test_replacement_matches_the_shared_policy(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of
        from proforma_vietnam.defaults import BESS_REPLACE_FRACTION_OF_INSTALL

        for install_key, replace_key in (
            ("bess_installed_cost_per_kw", "bess_replace_cost_per_kw"),
            ("bess_installed_cost_per_kwh", "bess_replace_cost_per_kwh"),
        ):
            install = value_of(FINANCIAL_DEFAULTS, install_key)
            replace = value_of(FINANCIAL_DEFAULTS, replace_key)
            self.assertAlmostEqual(
                replace, install * BESS_REPLACE_FRACTION_OF_INSTALL, places=9
            )
        # The 2026-09-11 ruling: replacement at install cost, 100 / 150.
        self.assertEqual(value_of(FINANCIAL_DEFAULTS, "bess_replace_cost_per_kw"), 100.0)
        self.assertEqual(value_of(FINANCIAL_DEFAULTS, "bess_replace_cost_per_kwh"), 150.0)

    def test_replacing_never_costs_more_than_buying_new(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of

        for install_key, replace_key in (
            ("bess_installed_cost_per_kw", "bess_replace_cost_per_kw"),
            ("bess_installed_cost_per_kwh", "bess_replace_cost_per_kwh"),
        ):
            self.assertLessEqual(
                value_of(FINANCIAL_DEFAULTS, replace_key),
                value_of(FINANCIAL_DEFAULTS, install_key),
            )

    def test_schedule_and_horizon_match_the_shared_policy(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of
        from proforma_vietnam import defaults as policy

        self.assertEqual(value_of(FINANCIAL_DEFAULTS, "project_years"), policy.PROJECT_YEARS)
        self.assertEqual(
            value_of(FINANCIAL_DEFAULTS, "pv_inverter_replacement_year"),
            policy.PV_INVERTER_REPLACEMENT_YEAR,
        )
        self.assertEqual(
            value_of(FINANCIAL_DEFAULTS, "pv_inverter_replacement_fraction_of_pv_capex"),
            policy.PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX,
        )

    def test_a_desynced_schedule_fails_at_import(self):
        from proforma_thailand import defaults

        entry = defaults.FINANCIAL_DEFAULTS["pv_inverter_replacement_year"]
        original = entry["value"]
        entry["value"] = 12
        try:
            with self.assertRaises(ValueError):
                defaults._assert_policy_holds()
        finally:
            entry["value"] = original

    def test_the_old_inverter_key_names_are_gone(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS

        self.assertNotIn("inverter_replacement_year", FINANCIAL_DEFAULTS)
        self.assertNotIn("inverter_replacement_fraction_of_pv_capex", FINANCIAL_DEFAULTS)
```

Then: `grep -n "inverter_replacement" proforma_thailand/tests/*.py` and rename every `inverter_replacement_year` to `pv_inverter_replacement_year` and every `inverter_replacement_fraction_of_pv_capex` to `pv_inverter_replacement_fraction_of_pv_capex` in the tests (the placeholder-set tests list these keys by name).

- [ ] **Step 2: Run to verify they fail**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults -v 2>&1 | tail -15`
Expected: the new tests FAIL (`KeyError: 'pv_inverter_replacement_year'`, replace 70 != 100).

- [ ] **Step 3: Update the JSON**

In `proforma_thailand/defaults/thailand_defaults.json` `financial`:

```json
    "bess_replace_cost_per_kw": {"value": 100.0, "source": "Client direction 2026-09-11: replacement at 100 percent of install cost; supersedes the 70 percent ruling of 2026-09-09.",
      "note": "Year-10 whole-system replacement (storage inverter and pack together), priced at the original per-kW cost. REopt schedules inverter_replacement_year at 10 but defaults every replace_cost field to 0.0, which would model a FREE replacement and overstate the BESS case over the project horizon."},
    "bess_replace_cost_per_kwh": {"value": 150.0, "source": "Client direction 2026-09-11: replacement at 100 percent of install cost; supersedes the 70 percent ruling of 2026-09-09.",
      "note": "Year-10 pack replacement at the original per-kWh cost, per client direction. Storage O&M in REopt is plain maintenance and carries no capacity-fade allowance, so this event stands in for all battery ageing."},
```

Rename the two PV inverter entries (same values, same placeholder source, note text updated from "25-year analysis" to "20-year analysis"):

```json
    "pv_inverter_replacement_year": {"value": 11, "source": "PLACEHOLDER - pending Keen confirmation",
      "note": "String inverters are normally replaced once inside a 20-year analysis. Year 11 matches the ENS SolarStorage calculation form supplied in the client folder. Shared replacement policy: both countries book this event."},
    "pv_inverter_replacement_fraction_of_pv_capex": {"value": 0.1, "source": "PLACEHOLDER - pending Keen confirmation",
      "note": "Inverter share of PV capex, from the ENS SolarStorage calculation form. Re-benchmarked for Thailand in Task 15. Shared replacement policy: both countries book this fraction."},
```

Edit with a Python script rather than by hand so the file stays valid JSON:

```bash
./.venv/Scripts/python.exe - <<'EOF'
import json
from pathlib import Path
p = Path("proforma_thailand/defaults/thailand_defaults.json")
d = json.loads(p.read_text(encoding="utf-8"))
f = d["financial"]
src = "Client direction 2026-09-11: replacement at 100 percent of install cost; supersedes the 70 percent ruling of 2026-09-09."
f["bess_replace_cost_per_kw"] = {"value": 100.0, "source": src,
  "note": "Year-10 whole-system replacement (storage inverter and pack together), priced at the original per-kW cost. REopt schedules inverter_replacement_year at 10 but defaults every replace_cost field to 0.0, which would model a FREE replacement and overstate the BESS case over the project horizon."}
f["bess_replace_cost_per_kwh"] = {"value": 150.0, "source": src,
  "note": "Year-10 pack replacement at the original per-kWh cost, per client direction. Storage O&M in REopt is plain maintenance and carries no capacity-fade allowance, so this event stands in for all battery ageing."}
year = f.pop("inverter_replacement_year")
frac = f.pop("inverter_replacement_fraction_of_pv_capex")
year["note"] = "String inverters are normally replaced once inside a 20-year analysis. Year 11 matches the ENS SolarStorage calculation form supplied in the client folder. Shared replacement policy: both countries book this event."
frac["note"] = frac["note"] + " Shared replacement policy: both countries book this fraction."
# keep original key order, inserting the renamed keys where the old ones sat
items = list(f.items())
out = {}
for k, v in items:
    out[k] = v
    if k == "bess_replace_cost_per_kwh":
        pass
out["pv_inverter_replacement_year"] = year
out["pv_inverter_replacement_fraction_of_pv_capex"] = frac
d["financial"] = out
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
EOF
git diff --stat proforma_thailand/defaults/thailand_defaults.json
```

Check the diff is confined to those four entries plus reordering; if the JSON was previously formatted with a different indent, re-run with the matching `indent` so the diff is minimal.

- [ ] **Step 4: Point the coupling at the policy and add the guard**

In `proforma_thailand/defaults/__init__.py`, replace the `_DERIVED_COUPLINGS` block and `_assert_couplings_hold()` call with:

```python
from proforma_vietnam.defaults import (
    BESS_REPLACE_FRACTION_OF_INSTALL,
    PROJECT_YEARS,
    PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX,
    PV_INVERTER_REPLACEMENT_YEAR,
)

# The coupling each derived default must satisfy: (derived, base, fraction).
# Kept as an assertion rather than a computation so the JSON stays the single
# readable source of every number, while a price change that desyncs a coupled
# value fails at import instead of silently shipping. The replacement fraction
# is the shared policy's, so Thailand cannot drift from Vietnam on it.
_DERIVED_COUPLINGS = (
    ("annual_om_per_kw", "pv_installed_cost_per_kw", 0.015),
    ("bess_replace_cost_per_kw", "bess_installed_cost_per_kw", BESS_REPLACE_FRACTION_OF_INSTALL),
    ("bess_replace_cost_per_kwh", "bess_installed_cost_per_kwh", BESS_REPLACE_FRACTION_OF_INSTALL),
)

# Schedule and horizon entries that must equal the shared policy outright.
_POLICY_EQUALITIES = (
    ("project_years", PROJECT_YEARS),
    ("pv_inverter_replacement_year", PV_INVERTER_REPLACEMENT_YEAR),
    ("pv_inverter_replacement_fraction_of_pv_capex", PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX),
)


def _assert_couplings_hold():
    for derived_key, base_key, fraction in _DERIVED_COUPLINGS:
        derived = FINANCIAL_DEFAULTS[derived_key]["value"]
        expected = FINANCIAL_DEFAULTS[base_key]["value"] * fraction
        if abs(derived - expected) > 1e-9:
            raise ValueError(
                "{} is {} but is defined as {} of {}, which is {}. "
                "Re-derive it or change the coupling.".format(
                    derived_key, derived, fraction, base_key, expected
                )
            )


def _assert_policy_holds():
    for key, expected in _POLICY_EQUALITIES:
        actual = FINANCIAL_DEFAULTS[key]["value"]
        if actual != expected:
            raise ValueError(
                "thailand_defaults.json financial.{} is {} but the shared "
                "replacement policy (proforma_vietnam.defaults) says {}. Change "
                "the policy for both countries or re-derive the JSON.".format(
                    key, actual, expected
                )
            )


_assert_couplings_hold()
_assert_policy_holds()
```

Put the `from proforma_vietnam.defaults import (...)` with the other imports at the top of the module.

- [ ] **Step 5: Run the Thailand defaults tests, then the whole Thailand suite**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults -v 2>&1 | tail -5`
Expected: all pass.

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . 2>&1 | tail -20`
Expected: failures ONLY in `test_case_builder.py` (assumptions key `inverter_replacement_year` missing, replacement 70 expected) and `test_report.py` (same key). Those are Tasks 4 and 5. Record the failing test names; do not fix them here.

- [ ] **Step 6: Commit**

```bash
git add proforma_thailand/defaults/ proforma_thailand/tests/test_thailand_defaults.py
git commit -m "Thailand replacement at 100 percent of install; PV inverter keys renamed; policy guard

bess_replace_cost 70/105 becomes 100/150 per the 2026-09-11 ruling. The
coupling fraction is now the shared policy's, and project_years plus the
two pv_inverter_* entries are asserted equal to the policy at import.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Vietnam builder derives replacement from the policy

**Files:**
- Modify: `proforma_vietnam/case_builder.py` (`DEFAULT_ANALYSIS_YEARS` line 29; imports lines 5-9; `_financial_inputs` lines 246-252; `_storage_inputs` lines 275-287; `_assumptions` lines 530-532)
- Test: `proforma_vietnam/tests/test_case_builder.py`

**Interfaces:**
- Consumes: policy constants and `FINANCIAL_DEFAULTS` from Task 1.
- Produces: payload `ElectricStorage` carrying `replace_cost_per_kw`, `replace_cost_per_kwh`, `inverter_replacement_year`, `battery_replacement_year` whenever a storage block is sent; `Financial.analysis_years` defaulting to `PROJECT_YEARS`; assumptions carrying `battery_replacement_year`, `bess_replace_cost_per_kw`, `bess_replace_cost_per_kwh`, `pv_inverter_replacement_year`, `pv_inverter_replacement_fraction_of_pv_capex`.

- [ ] **Step 1: Write the failing tests**

Add to `proforma_vietnam/tests/test_case_builder.py` (use the same `_write_load_csv` helper the file already has):

```python
    def test_replacement_defaults_to_the_shared_policy(self):
        from proforma_vietnam.defaults import (
            BESS_REPLACEMENT_YEAR, BESS_REPLACE_FRACTION_OF_INSTALL,
            PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX, PV_INVERTER_REPLACEMENT_YEAR,
        )
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "technologies": {
                    "storage": {
                        "max_kw": 1000, "max_kwh": 4000,
                        "installed_cost_per_kw": 80, "installed_cost_per_kwh": 120,
                    },
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        storage = case["payload"]["ElectricStorage"]
        self.assertEqual(storage["replace_cost_per_kw"], 80 * BESS_REPLACE_FRACTION_OF_INSTALL)
        self.assertEqual(storage["replace_cost_per_kwh"], 120 * BESS_REPLACE_FRACTION_OF_INSTALL)
        self.assertEqual(storage["inverter_replacement_year"], BESS_REPLACEMENT_YEAR)
        self.assertEqual(storage["battery_replacement_year"], BESS_REPLACEMENT_YEAR)

        assumptions = case["assumptions"]
        self.assertEqual(assumptions["battery_replacement_year"], BESS_REPLACEMENT_YEAR)
        self.assertEqual(assumptions["bess_replace_cost_per_kw"], 80.0)
        self.assertEqual(assumptions["bess_replace_cost_per_kwh"], 120.0)
        self.assertEqual(assumptions["pv_inverter_replacement_year"], PV_INVERTER_REPLACEMENT_YEAR)
        self.assertEqual(
            assumptions["pv_inverter_replacement_fraction_of_pv_capex"],
            PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX,
        )

    def test_an_explicit_replacement_in_case_json_wins_over_the_policy(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "technologies": {
                    "storage": {
                        "max_kw": 1000, "max_kwh": 4000,
                        "installed_cost_per_kw": 80, "installed_cost_per_kwh": 120,
                        "replace_cost_per_kwh": 60, "battery_replacement_year": 12,
                    },
                },
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        storage = case["payload"]["ElectricStorage"]
        self.assertEqual(storage["replace_cost_per_kwh"], 60)
        self.assertEqual(storage["battery_replacement_year"], 12)
        # The untouched half still follows the policy.
        self.assertEqual(storage["replace_cost_per_kw"], 80.0)
        self.assertEqual(storage["inverter_replacement_year"], 10)
        self.assertEqual(case["assumptions"]["bess_replace_cost_per_kwh"], 60)
        self.assertEqual(case["assumptions"]["battery_replacement_year"], 12)

    def test_analysis_years_defaults_to_the_policy_horizon(self):
        from proforma_vietnam.defaults import PROJECT_YEARS
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertEqual(case["payload"]["Financial"]["analysis_years"], PROJECT_YEARS)
        self.assertEqual(case["payload"]["Financial"]["analysis_years"], 20)

    def test_no_storage_block_means_no_replacement_keys(self):
        load_csv_path = _write_load_csv([500.0] * 8760)

        case = build_vietnam_case(
            {
                "site": {"latitude": 10.8231, "longitude": 106.6297},
                "load_profile": {"year": 2025, "path": str(load_csv_path)},
                "tariff": {"year": 2025, "voltage_level": "22-110kV"},
                "esco_contract": {"esco_energy_discount_fraction": 0.9},
            }
        )

        self.assertNotIn("replace_cost_per_kw", case["payload"]["ElectricStorage"])
        self.assertNotIn("bess_replace_cost_per_kw", case["assumptions"])
        # The PV inverter policy is written regardless: it needs PV, not storage.
        self.assertEqual(case["assumptions"]["pv_inverter_replacement_year"], 11)
```

Check first what the existing fixture without a storage block produces for `payload["ElectricStorage"]` (`_storage_inputs({}, ...)` returns a dict with only `can_grid_charge`). The last test relies on that; if it returns something else, adjust the assertion to match the actual empty shape.

- [ ] **Step 2: Run to verify they fail**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_case_builder -k replacement -k analysis_years -k no_storage -v 2>&1 | tail -20`
Expected: the four new tests FAIL (`KeyError: 'replace_cost_per_kw'`, `25 != 20`).

- [ ] **Step 3: Implement**

`proforma_vietnam/case_builder.py`:

Imports (lines 5-9) become:

```python
from proforma_vietnam.defaults import (
    BESS_REPLACEMENT_YEAR,
    BESS_REPLACE_FRACTION_OF_INSTALL,
    FINANCIAL_DEFAULTS,
    PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX,
    PV_INVERTER_REPLACEMENT_YEAR,
    SURPLUS_EXPORT_DEFAULTS,
    dppa_regulatory_for_year,
)
```

Delete `DEFAULT_ANALYSIS_YEARS = 25` (line 29) and add next to the other defaults:

```python
# One horizon: the same value the cash flow runs (vietnam_defaults.json
# project_years, asserted equal to the shared policy at import).
DEFAULT_ANALYSIS_YEARS = FINANCIAL_DEFAULTS["project_years"]
```

`_storage_inputs` becomes:

```python
def _storage_inputs(storage_config, esco_contract, dppa_inputs):
    storage = _allowlisted(storage_config, STORAGE_PAYLOAD_KEYS)
    _apply_replacement_policy(storage)
    if dppa_inputs is not None and dppa_inputs["type"] != DPPA_TYPE_NONE:
        # Co-located BESS only under DPPA: charges from PV, not from the grid.
        storage["can_grid_charge"] = False
        return storage
    if "can_grid_charge" not in storage:
        storage["can_grid_charge"] = esco_contract.get(
            "grid_charging_enabled",
            DEFAULT_GRID_CHARGING_ENABLED,
        )
    storage.setdefault("can_grid_charge", DEFAULT_GRID_CHARGING_ENABLED)
    return storage


def _apply_replacement_policy(storage):
    """Fill the REopt replacement inputs from the shared policy.

    REopt defaults every replace_cost field to 0.0, which models a free
    replacement; the two bess_arbitrage cases shipped that way. The policy
    replaces the whole system (storage inverter and pack) in one year at a
    fraction of the install price actually being sent, so a price sensitivity
    keeps the rule true. An explicit case.json value for any key still wins.
    Only applied when the case sends a storage system at all.
    """
    if not (storage.get("max_kw") or storage.get("max_kwh") or storage.get("min_kw") or storage.get("min_kwh")):
        return
    for install_key, replace_key in (
        ("installed_cost_per_kw", "replace_cost_per_kw"),
        ("installed_cost_per_kwh", "replace_cost_per_kwh"),
    ):
        if replace_key not in storage and storage.get(install_key) is not None:
            storage[replace_key] = storage[install_key] * BESS_REPLACE_FRACTION_OF_INSTALL
    storage.setdefault("inverter_replacement_year", BESS_REPLACEMENT_YEAR)
    storage.setdefault("battery_replacement_year", BESS_REPLACEMENT_YEAR)
```

In `_assumptions`, replace lines 530-532 (`storage = technologies.get("storage", {})` and the `battery_replacement_year` passthrough) with a record of what was sent. `_assumptions` does not receive the payload, so recompute the same way the payload did:

```python
    storage_sent = _allowlisted(technologies.get("storage", {}), STORAGE_PAYLOAD_KEYS)
    _apply_replacement_policy(storage_sent)
    for sent_key, record_key in (
        ("battery_replacement_year", "battery_replacement_year"),
        ("replace_cost_per_kw", "bess_replace_cost_per_kw"),
        ("replace_cost_per_kwh", "bess_replace_cost_per_kwh"),
    ):
        if storage_sent.get(sent_key) is not None:
            assumptions[record_key] = storage_sent[sent_key]
    # The PV inverter event is booked by the shared core from these two values;
    # written at case-build time so the workbook reads a record, not a live
    # default (the O&M lesson of 2026-09-10).
    assumptions["pv_inverter_replacement_year"] = PV_INVERTER_REPLACEMENT_YEAR
    assumptions["pv_inverter_replacement_fraction_of_pv_capex"] = (
        PV_INVERTER_REPLACEMENT_FRACTION_OF_PV_CAPEX
    )
```

- [ ] **Step 4: Run the builder tests, then the Vietnam suite**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_case_builder -v 2>&1 | tail -8`
Expected: all pass, including the pre-existing `test_pv_depreciation_and_battery_replacement_pass_through_assumptions` (its explicit year 11 still wins).

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . 2>&1 | tail -5`
Expected: 539 passed.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/case_builder.py proforma_vietnam/tests/test_case_builder.py
git commit -m "Vietnam builder derives BESS replacement from the shared policy

Whole system at BESS_REPLACEMENT_YEAR at BESS_REPLACE_FRACTION_OF_INSTALL
of the install price actually sent; explicit case.json values still win.
analysis_years defaults to the policy horizon. What was sent is recorded
in assumptions for the workbook.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Thailand builder: same derivation, explicit years, assumptions record

**Files:**
- Modify: `proforma_thailand/case_builder.py:153-195` (storage block) and `:242-247` (assumptions)
- Test: `proforma_thailand/tests/test_case_builder.py` (`test_bess_replacement_is_not_free` at 184 and the renamed-key references)

**Interfaces:**
- Consumes: policy constants; `FINANCIAL_DEFAULTS["pv_inverter_replacement_year"]`, `["pv_inverter_replacement_fraction_of_pv_capex"]` from Task 2.
- Produces: same payload and assumptions keys as Task 3.

- [ ] **Step 1: Write the failing tests**

Read `test_bess_replacement_is_not_free` (line 184) to reuse its fixture; rewrite it and add two:

```python
    def test_bess_replacement_follows_the_shared_policy(self):
        from proforma_vietnam.defaults import (
            BESS_REPLACEMENT_YEAR, BESS_REPLACE_FRACTION_OF_INSTALL,
        )
        case = build_thailand_case(self._storage_case())   # the fixture the old test used
        storage = case["payload"]["ElectricStorage"]

        self.assertEqual(
            storage["replace_cost_per_kw"],
            storage["installed_cost_per_kw"] * BESS_REPLACE_FRACTION_OF_INSTALL,
        )
        self.assertEqual(
            storage["replace_cost_per_kwh"],
            storage["installed_cost_per_kwh"] * BESS_REPLACE_FRACTION_OF_INSTALL,
        )
        self.assertEqual(storage["replace_cost_per_kw"], 100.0)
        self.assertEqual(storage["replace_cost_per_kwh"], 150.0)
        self.assertEqual(storage["inverter_replacement_year"], BESS_REPLACEMENT_YEAR)
        self.assertEqual(storage["battery_replacement_year"], BESS_REPLACEMENT_YEAR)

    def test_replacement_is_recorded_in_assumptions(self):
        case = build_thailand_case(self._storage_case())
        a = case["assumptions"]

        self.assertEqual(a["battery_replacement_year"], 10)
        self.assertEqual(a["bess_replace_cost_per_kw"], 100.0)
        self.assertEqual(a["bess_replace_cost_per_kwh"], 150.0)
        self.assertEqual(a["pv_inverter_replacement_year"], 11)
        self.assertEqual(a["pv_inverter_replacement_fraction_of_pv_capex"], 0.10)
        self.assertNotIn("inverter_replacement_year", a)
        self.assertNotIn("inverter_replacement_cost_usd", a)

    def test_a_price_sensitivity_keeps_the_replacement_rule(self):
        config = self._storage_case()
        config["technologies"]["storage"]["installed_cost_per_kwh"] = 200.0
        case = build_thailand_case(config)

        self.assertEqual(case["payload"]["ElectricStorage"]["replace_cost_per_kwh"], 200.0)
```

If the file has no `_storage_case()` helper, extract the old test's inline dict into one; every test in the class that builds a storage case should use it.

- [ ] **Step 2: Run to verify they fail**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder -v 2>&1 | tail -15`
Expected: the three FAIL.

- [ ] **Step 3: Implement**

In `proforma_thailand/case_builder.py`, replace the `replace_cost_per_kw` / `replace_cost_per_kwh` entries of the storage payload (lines 168-178) and add the years. The block becomes:

```python
    if storage_config.get("max_kw") or storage_config.get("max_kwh"):
        installed_per_kw = storage_config.get(
            "installed_cost_per_kw",
            value_of(FINANCIAL_DEFAULTS, "bess_installed_cost_per_kw"),
        )
        installed_per_kwh = storage_config.get(
            "installed_cost_per_kwh",
            value_of(FINANCIAL_DEFAULTS, "bess_installed_cost_per_kwh"),
        )
        payload["ElectricStorage"] = {
            "max_kw": storage_config.get("max_kw", 0),
            "max_kwh": storage_config.get("max_kwh", 0),
            "installed_cost_per_kw": installed_per_kw,
            "installed_cost_per_kwh": installed_per_kwh,
            "installed_cost_constant": storage_config.get(
                "installed_cost_constant", 0.0
            ),
            # Shared replacement policy: the whole system (storage inverter and
            # pack) in one year at a fraction of the install price actually
            # sent, so a price sensitivity keeps the rule true. REopt defaults
            # every replace_cost field to 0.0, a free replacement.
            "replace_cost_per_kw": storage_config.get(
                "replace_cost_per_kw",
                installed_per_kw * BESS_REPLACE_FRACTION_OF_INSTALL,
            ),
            "replace_cost_per_kwh": storage_config.get(
                "replace_cost_per_kwh",
                installed_per_kwh * BESS_REPLACE_FRACTION_OF_INSTALL,
            ),
            "inverter_replacement_year": storage_config.get(
                "inverter_replacement_year", BESS_REPLACEMENT_YEAR
            ),
            "battery_replacement_year": storage_config.get(
                "battery_replacement_year", BESS_REPLACEMENT_YEAR
            ),
            # REopt inherits 0.0 for both, which permits a physically meaningless
            # zero-duration battery and prices O&M at the US default of 2.5 percent.
            "min_duration_hours": storage_config.get(
                "min_duration_hours",
                value_of(FINANCIAL_DEFAULTS, "bess_min_duration_hours"),
            ),
            "om_cost_fraction_of_installed_cost": storage_config.get(
                "om_cost_fraction_of_installed_cost",
                value_of(FINANCIAL_DEFAULTS, "bess_om_fraction_of_installed_cost"),
            ),
            # Same US incentives as PV above, same reason for zeroing them.
            "total_itc_fraction": 0.0,
            "macrs_option_years": 0,
            "macrs_bonus_fraction": 0.0,
            "can_grid_charge": storage_config.get("can_grid_charge", True),
        }
```

Add the import at the top: `from proforma_vietnam.defaults import BESS_REPLACEMENT_YEAR, BESS_REPLACE_FRACTION_OF_INSTALL`.

In the assumptions dict, replace the `"inverter_replacement_year": value_of(FINANCIAL_DEFAULTS, "inverter_replacement_year"),` entry and its comment (lines 242-247) with:

```python
        # Shared replacement policy, recorded at case-build time so the
        # workbook reads what was decided, not a live default. The PV inverter
        # cost itself is derived by the shared core from the solved PV capex.
        "pv_inverter_replacement_year": value_of(
            FINANCIAL_DEFAULTS, "pv_inverter_replacement_year"
        ),
        "pv_inverter_replacement_fraction_of_pv_capex": value_of(
            FINANCIAL_DEFAULTS, "pv_inverter_replacement_fraction_of_pv_capex"
        ),
```

and after the dict is built (before `for key in RATE_VINTAGE_KEYS:`) add:

```python
    storage_sent = payload.get("ElectricStorage")
    if storage_sent:
        assumptions["battery_replacement_year"] = storage_sent["battery_replacement_year"]
        assumptions["bess_replace_cost_per_kw"] = storage_sent["replace_cost_per_kw"]
        assumptions["bess_replace_cost_per_kwh"] = storage_sent["replace_cost_per_kwh"]
```

- [ ] **Step 4: Run the Thailand builder tests and the whole Thailand suite**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder -v 2>&1 | tail -5`
Expected: all pass.

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . 2>&1 | tail -12`
Expected: only `test_report.py` still fails (Task 5). Note the names.

- [ ] **Step 5: Commit**

```bash
git add proforma_thailand/case_builder.py proforma_thailand/tests/test_case_builder.py
git commit -m "Thailand builder derives BESS replacement from the shared policy and records it

Replacement priced from the install price actually sent; both replacement
years sent explicitly at the policy year; pv_inverter_* recorded in
assumptions at build time.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: PV inverter event derived in the shared core

**Files:**
- Modify: `proforma_vietnam/esco_pro_forma.py:14-31` (pops), `:138-157` (merge), `:246` (return), `:486-490` (`_pv_capex` stays)
- Modify: `proforma_thailand/report.py:38-53` (`PASSTHROUGH_OVERRIDE_KEYS`), delete `:89-97` and `:216-223`
- Modify: `proforma_vietnam/run_dppa_negotiation_sweep.py:152-186` (mapping)
- Modify: `proforma_vietnam/run_case.py:16-37` (`VIETNAM_REPORT_QUERY_KEYS`), `reoptjl/views.py:475-505`
- Test: `proforma_vietnam/tests/test_esco_pro_forma.py`, `proforma_thailand/tests/test_report.py:473-500, 807`

**Interfaces:**
- Consumes: assumptions keys `pv_inverter_replacement_year`, `pv_inverter_replacement_fraction_of_pv_capex` from Tasks 3 and 4.
- Produces: `calculate_esco_pro_forma_from_reopt_results(..., pv_inverter_replacement_year=None, pv_inverter_replacement_fraction_of_pv_capex=None, ...)`; result `derivation["pv_inverter_replacement"] = {"year": int, "fraction": float, "cost_usd": float}` when booked.

- [ ] **Step 1: Write the failing core tests**

Add to `proforma_vietnam/tests/test_esco_pro_forma.py`. Look at the file's existing minimal `reopt_results` fixture (a dict with `inputs` and `outputs`) and reuse its helper if there is one; otherwise build the smallest dict that the function accepts today (the file's first test shows the shape):

```python
class PvInverterReplacementTests(TestCase):
    """The shared core books the PV inverter event for both countries."""

    def _results(self, pv_kw=1000.0, cost_per_kw=500.0, bess_kw=0.0, bess_kwh=0.0):
        rates = [0.1] * 8760
        return {
            "inputs": {
                "ElectricTariff": {"tou_energy_rates_per_kwh": rates},
                "ElectricStorage": {
                    "replace_cost_per_kw": 100.0, "replace_cost_per_kwh": 150.0,
                    "battery_replacement_year": 10, "can_grid_charge": True,
                },
                "Financial": {"analysis_years": 20, "owner_discount_rate_fraction": 0.11},
                "PV": {"degradation_fraction": 0.005},
            },
            "outputs": {
                "PV": [{"size_kw": pv_kw, "installed_cost_per_kw": cost_per_kw,
                        "electric_to_load_series_kw": [0.1] * 8760,
                        "year_one_energy_produced_kwh": 876.0,
                        "annual_energy_produced_kwh": 876.0}],
                "ElectricStorage": {"size_kw": bess_kw, "size_kwh": bess_kwh},
                "ElectricTariff": {"year_one_bill_before_tax": 900.0,
                                   "year_one_bill_before_tax_bau": 1000.0,
                                   "year_one_demand_cost_before_tax": 0.0,
                                   "year_one_demand_cost_before_tax_bau": 0.0},
                "Financial": {"year_one_om_costs_before_tax": 5000.0},
                "ElectricUtility": {}, "ElectricLoad": {},
            },
        }

    def test_the_event_lands_at_fraction_of_solved_pv_capex_in_the_policy_year(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=1000.0, cost_per_kw=500.0),
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )
        series = result["derivation"]["replacement_costs_by_year_usd"]
        self.assertAlmostEqual(series[10], 50000.0)      # year 11, index 10
        self.assertEqual(sum(series[:10]) + sum(series[11:]), 0.0)
        block = result["derivation"]["pv_inverter_replacement"]
        self.assertEqual(block, {"year": 11, "fraction": 0.10, "cost_usd": 50000.0})

    def test_the_event_adds_to_the_bess_event_rather_than_replacing_it(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=1000.0, cost_per_kw=500.0, bess_kw=100.0, bess_kwh=200.0),
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )
        series = result["derivation"]["replacement_costs_by_year_usd"]
        self.assertAlmostEqual(series[9], 100 * 100.0 + 200 * 150.0)   # BESS, year 10
        self.assertAlmostEqual(series[10], 50000.0)                     # PV inverter, year 11

    def test_the_event_adds_to_an_explicit_extra_series_too(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=1000.0, cost_per_kw=500.0),
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
            extra_replacement_costs_by_year=[0.0] * 10 + [1.0],
        )
        self.assertAlmostEqual(
            result["derivation"]["replacement_costs_by_year_usd"][10], 50001.0
        )

    def test_no_pv_means_no_event_and_no_block(self):
        results = self._results(pv_kw=0.0, cost_per_kw=500.0, bess_kw=100.0, bess_kwh=200.0)
        result = calculate_esco_pro_forma_from_reopt_results(
            results,
            esco_energy_discount_fraction=0.9,
            pv_inverter_replacement_year=11,
            pv_inverter_replacement_fraction_of_pv_capex=0.10,
        )
        series = result["derivation"]["replacement_costs_by_year_usd"]
        self.assertEqual(len(series), 10)
        self.assertNotIn("pv_inverter_replacement", result["derivation"])

    def test_omitting_the_policy_keys_books_nothing(self):
        result = calculate_esco_pro_forma_from_reopt_results(
            self._results(pv_kw=1000.0, cost_per_kw=500.0),
            esco_energy_discount_fraction=0.9,
        )
        self.assertNotIn("replacement_costs_by_year_usd", result["derivation"])
        self.assertNotIn("pv_inverter_replacement", result["derivation"])
```

Before running, check what key the derivation uses for the replacement series (`grep -n "replacement_costs_by_year_usd" proforma_vietnam/cash_flow.py`); `audit_sheets.py:1201` reads `d.get("replacement_costs_by_year_usd")`, so that is the name. If a bare fixture like the above raises on some other missing key, add that key with a zero or empty value; do not add anything the function does not read.

- [ ] **Step 2: Run to verify they fail**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_esco_pro_forma.PvInverterReplacementTests -v 2>&1 | tail -12`
Expected: FAIL, `TypeError: ... got an unexpected keyword argument 'pv_inverter_replacement_year'` (it falls through `**cash_flow_overrides` into the cash flow).

- [ ] **Step 3: Implement in the core**

`proforma_vietnam/esco_pro_forma.py`, after `extra_replacement_costs = cash_flow_overrides.pop("extra_replacement_costs_by_year", None)` (line 29-31):

```python
    pv_inverter_year = cash_flow_overrides.pop("pv_inverter_replacement_year", None)
    pv_inverter_fraction = cash_flow_overrides.pop(
        "pv_inverter_replacement_fraction_of_pv_capex", None
    )
```

Replace the block from `replacement_costs = _bess_replacement_costs(` through the end of the `if extra_replacement_costs:` merge (lines 138-157) with:

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
    # Shared replacement policy: one PV inverter event at a fraction of the
    # SOLVED PV capex, derived here so both countries book it from one place.
    # Added, never assigned: a bare override would delete the BESS event.
    pv_inverter_replacement = _pv_inverter_replacement(
        pv_outputs, pv_inverter_year, pv_inverter_fraction
    )
    if pv_inverter_replacement is not None:
        cash_flow_inputs["replacement_costs_by_year"] = _merge_replacement_costs(
            cash_flow_inputs.get("replacement_costs_by_year"),
            _money_series(
                pv_inverter_replacement["series"],
                exchange_rate_vnd_per_usd,
                tariff_money_values_currency,
            ),
        )
    if extra_replacement_costs:
        cash_flow_inputs["replacement_costs_by_year"] = _merge_replacement_costs(
            cash_flow_inputs.get("replacement_costs_by_year"),
            _money_series(
                extra_replacement_costs,
                exchange_rate_vnd_per_usd,
                tariff_money_values_currency,
            ),
        )
```

Replace the final `return calculate_vietnam_esco_cash_flow(**cash_flow_inputs)` (line 246) with:

```python
    result = calculate_vietnam_esco_cash_flow(**cash_flow_inputs)
    if pv_inverter_replacement is not None:
        result["derivation"]["pv_inverter_replacement"] = {
            "year": pv_inverter_replacement["year"],
            "fraction": pv_inverter_replacement["fraction"],
            "cost_usd": _money(
                pv_inverter_replacement["cost"],
                exchange_rate_vnd_per_usd,
                tariff_money_values_currency,
            ),
        }
    return result
```

Add next to `_bess_replacement_costs`:

```python
def _pv_inverter_replacement(pv_outputs, year, fraction):
    """One PV inverter event at ``fraction`` of the solved PV capex in ``year``.

    Returns None when either policy value is unset or the run has no PV, so a
    battery-only case books nothing and a caller that never adopted the policy
    is unchanged. Money is in REopt's own currency here; the caller converts.
    """
    if not year or not fraction:
        return None
    cost = _pv_capex(pv_outputs) * fraction
    if cost <= 0:
        return None
    series = [0.0] * int(year)
    series[int(year) - 1] = cost
    return {"year": int(year), "fraction": fraction, "cost": cost, "series": series}
```

Check `_money` exists with signature `_money(value, exchange_rate_vnd_per_usd, reopt_money_values_currency)` (line ~545); it does.

- [ ] **Step 4: Run the core tests**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_esco_pro_forma.PvInverterReplacementTests -v 2>&1 | tail -8`
Expected: 5 passed.

- [ ] **Step 5: Thailand report delegates; map the keys in Vietnam; forward through the API**

`proforma_thailand/report.py`:
- Add `"pv_inverter_replacement_year"` and `"pv_inverter_replacement_fraction_of_pv_capex"` to `PASSTHROUGH_OVERRIDE_KEYS`.
- Delete lines 89-97 (the `inverter_year` / `inverter_cost` / `extra_replacement_costs_by_year` block and its comment).
- Delete lines 216-223 (`assumptions = dict(assumptions)` through the `inverter_replacement_cost_usd` assignment and its comment). Keep `pv_capex = _pv_capex(pv_outputs_list)`, it is still used for insurance.

`proforma_vietnam/run_dppa_negotiation_sweep.py` mapping: add

```python
        "pv_inverter_replacement_year": "pv_inverter_replacement_year",
        "pv_inverter_replacement_fraction_of_pv_capex": "pv_inverter_replacement_fraction_of_pv_capex",
```

`proforma_vietnam/run_case.py` `VIETNAM_REPORT_QUERY_KEYS`: append the same two names.

`reoptjl/views.py` `numeric_query_params`: add the same two entries (key equals value), and add `"pv_inverter_replacement_year"` to the int-cast tuple on line 503.

- [ ] **Step 6: Rewrite the Thailand report tests**

In `proforma_thailand/tests/test_report.py`:
- `test_inverter_replacement_lands_in_the_right_year` (473): the overrides now carry the two keys, not a series:

```python
    def test_pv_inverter_policy_is_passed_to_the_core(self):
        overrides = cash_flow_overrides_from_assumptions({
            "pv_inverter_replacement_year": 11,
            "pv_inverter_replacement_fraction_of_pv_capex": 0.10,
        })
        self.assertEqual(overrides["pv_inverter_replacement_year"], 11)
        self.assertEqual(overrides["pv_inverter_replacement_fraction_of_pv_capex"], 0.10)
        self.assertNotIn("extra_replacement_costs_by_year", overrides)
```

- `test_no_inverter_replacement_emits_no_series` (484): keep the intent, assert neither key is emitted when the assumptions lack them.
- `test_inverter_replacement_does_not_displace_a_battery_replacement` (494) and `test_inverter_replacement_is_nonzero_when_only_solved_capex_is_present` (807): these now test core behaviour and are covered by Task 5 Step 1. Replace them with one end-to-end test through `build_thailand_report` using the file's existing storage fixture: read the built workbook's Pro Forma (Audit) sheet, find the row labelled "Equipment replacement (engine schedule)", and assert the year-10 cell equals `size_kw*100 + size_kwh*150` and the year-11 cell equals `0.10 * pv_size_kw * 500`. Use the fixture's own PV size and cost (the file notes one fixture leaves `installed_cost_per_kw` unset; use the one at line 807 that sets it).
- Every other `inverter_replacement_year` reference in the file becomes `pv_inverter_replacement_year`; every `inverter_replacement_cost_usd` assertion is deleted (the key no longer exists; Task 6 renders the derived cost from the derivation block).

- [ ] **Step 7: Run both suites**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . 2>&1 | tail -5`
Expected: all pass (count will be 137 minus the two removed plus the ones added; record it).

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . 2>&1 | tail -5`
Expected: 544 passed.

- [ ] **Step 8: Commit**

```bash
git add proforma_vietnam/esco_pro_forma.py proforma_thailand/report.py proforma_vietnam/run_dppa_negotiation_sweep.py proforma_vietnam/run_case.py reoptjl/views.py proforma_vietnam/tests/test_esco_pro_forma.py proforma_thailand/tests/test_report.py
git commit -m "PV inverter replacement derived in the shared core for both countries

calculate_esco_pro_forma_from_reopt_results books one event at
pv_inverter_replacement_fraction_of_pv_capex of the solved PV capex in
pv_inverter_replacement_year and reports it in the derivation block. The
Thailand report layer's local derivation is deleted; Vietnam maps the two
keys through the sweep helper, run_case and the API view.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Assumptions and Model Basis sheets read the record

**Files:**
- Modify: `proforma_vietnam/audit_sheets.py:70-80` (`CURATED_ASSUMPTION_KEYS`), `:98` (storage row label), `:304-306` (analysis period), `:387-390` (battery replacement year entry), `:1203-1214` (audit row label), `:2358-2362` and `:2405-2406` (Model Basis)
- Test: `proforma_vietnam/tests/test_audit_sheets.py`

**Interfaces:**
- Consumes: assumptions keys from Tasks 3, 4; `derivation["pv_inverter_replacement"]` and `derivation["project_years"]` from Task 5 and the cash flow.

- [ ] **Step 1: Write the failing tests**

Find how `test_audit_sheets.py` builds a workbook from a small `cash_flow_result` (it has fixtures calling `write_assumptions_sheet` / `write_model_basis_sheet` directly, or `build_vietnam_esco_workbook`). Add, in that style:

```python
class ReplacementPolicyRowsTests(TestCase):

    def _assumptions(self):
        return {
            "case_name": "t", "esco_energy_discount_fraction": 0.9,
            "battery_replacement_year": 10,
            "bess_replace_cost_per_kw": 80.0, "bess_replace_cost_per_kwh": 120.0,
            "pv_inverter_replacement_year": 11,
            "pv_inverter_replacement_fraction_of_pv_capex": 0.10,
        }

    def _derivation(self):
        return {
            "project_years": 20,
            "replacement_costs_by_year_usd": [0.0] * 9 + [26000.0, 50000.0],
            "pv_inverter_replacement": {"year": 11, "fraction": 0.10, "cost_usd": 50000.0},
        }

    def _rows(self, sheet):
        return [[c.value for c in row] for row in sheet.iter_rows()]

    def test_assumptions_sheet_has_a_replacement_policy_section(self):
        wb = Workbook()
        ws = wb.active
        write_assumptions_sheet(ws, wb, self._assumptions(), self._derivation())
        text = "\n".join(str(v) for row in self._rows(ws) for v in row if v is not None)
        self.assertIn("Replacement Policy", text)
        self.assertIn("BESS replacement year", text)
        self.assertIn("BESS replacement cost per kW", text)
        self.assertIn("PV inverter replacement year", text)
        self.assertIn("PV inverter replacement cost", text)
        self.assertIn("proforma_vietnam.defaults replacement policy", text)
        self.assertNotIn("Other Assumptions (assumptions.json echo)", text)

    def test_model_basis_reads_the_horizon_and_names_both_events(self):
        wb = Workbook()
        ws = wb.active
        write_model_basis_sheet(ws, self._assumptions(), self._derivation())
        text = "\n".join(str(v) for row in self._rows(ws) for v in row if v is not None)
        self.assertIn("20-year", text)
        self.assertNotIn("25-year", text)
        self.assertIn("year 10", text)
        self.assertIn("year 11", text)
        self.assertIn("PV inverter", text)

    def test_model_basis_says_25_when_the_data_says_25(self):
        wb = Workbook()
        ws = wb.active
        d = dict(self._derivation(), project_years=25)
        write_model_basis_sheet(ws, self._assumptions(), d)
        text = "\n".join(str(v) for row in self._rows(ws) for v in row if v is not None)
        self.assertIn("25-year", text)

    def test_model_basis_drops_the_pv_clause_without_pv(self):
        wb = Workbook()
        ws = wb.active
        d = {"project_years": 20, "replacement_costs_by_year_usd": [0.0] * 9 + [26000.0]}
        write_model_basis_sheet(ws, self._assumptions(), d)
        text = "\n".join(str(v) for row in self._rows(ws) for v in row if v is not None)
        self.assertNotIn("PV inverter", text)

    def test_storage_pcs_row_is_labelled_as_the_storage_inverter(self):
        from proforma_vietnam.audit_sheets import STORAGE_CASE_ROWS
        labels = {key: label for label, key, unit in STORAGE_CASE_ROWS}
        self.assertEqual(labels["inverter_replacement_year"], "Storage inverter (PCS) replacement year")

    def test_audit_replacement_row_is_equipment_not_battery_for_vietnam(self):
        # The merged series now carries the PV inverter for Vietnam too.
        from proforma_vietnam import audit_sheets
        source = inspect.getsource(audit_sheets.write_pro_forma_audit_sheet)
        self.assertNotIn('"Battery replacement (engine schedule)"', source)
```

The last test is a source-text guard; if the file has a cleaner way to render the audit sheet in tests, assert on the rendered label instead. `write_assumptions_sheet` may need more assumption keys to run (it reads `exchange_rate_vnd_per_usd` etc.); add whatever the smallest existing fixture in the file uses.

- [ ] **Step 2: Run to verify they fail**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_audit_sheets.ReplacementPolicyRowsTests -v 2>&1 | tail -15`
Expected: all six FAIL.

- [ ] **Step 3: Implement**

`CURATED_ASSUMPTION_KEYS` (line 70-80): add `"bess_replace_cost_per_kw", "bess_replace_cost_per_kwh", "pv_inverter_replacement_year", "pv_inverter_replacement_fraction_of_pv_capex",`.

Line 98: `("Storage inverter (PCS) replacement year", "inverter_replacement_year", "year"),`.

Lines 304-306:

```python
    entry("Analysis period", d.get("project_years", assumptions.get("analysis_years", DEFAULT_PROJECT_YEARS)),
          unit="years", source="proforma_vietnam.defaults replacement policy (PROJECT_YEARS) unless case.json financial.analysis_years overrides",
          name="PROJECT_YEARS", fmt="0")
```

with `from proforma_vietnam.defaults import FINANCIAL_DEFAULTS as _VN_FINANCIAL_DEFAULTS` at the top and `DEFAULT_PROJECT_YEARS = _VN_FINANCIAL_DEFAULTS["project_years"]` next to the other module constants (check whether the module already imports `DEFAULT_PROJECT_YEARS` from `cash_flow`; if so, use that).

Lines 387-390 (the `if assumptions.get("battery_replacement_year"):` entry) become a section:

```python
    if assumptions.get("battery_replacement_year") or assumptions.get("pv_inverter_replacement_year"):
        section("Replacement Policy")
        policy_source = "proforma_vietnam.defaults replacement policy unless case.json technologies.storage overrides"
        if assumptions.get("battery_replacement_year"):
            entry("BESS replacement year (storage inverter and pack together)",
                  assumptions["battery_replacement_year"], unit="year",
                  source=policy_source, fmt="0")
            entry("BESS replacement cost per kW", assumptions.get("bess_replace_cost_per_kw"),
                  unit="USD/kW", source=policy_source + " (sent to REopt)", fmt=FMT_AMOUNT_2)
            entry("BESS replacement cost per kWh", assumptions.get("bess_replace_cost_per_kwh"),
                  unit="USD/kWh", source=policy_source + " (sent to REopt)", fmt=FMT_AMOUNT_2)
        pv_inverter = d.get("pv_inverter_replacement") or {}
        if assumptions.get("pv_inverter_replacement_year"):
            entry("PV inverter replacement year", assumptions["pv_inverter_replacement_year"],
                  unit="year", source="proforma_vietnam.defaults replacement policy", fmt="0")
            entry("PV inverter replacement fraction of PV capex",
                  assumptions.get("pv_inverter_replacement_fraction_of_pv_capex"),
                  unit="fraction", source="proforma_vietnam.defaults replacement policy",
                  fmt=FMT_PERCENT)
            entry("PV inverter replacement cost", pv_inverter.get("cost_usd"), unit="USD",
                  source="Engine: fraction x solved PV capex (none booked when the run has no PV)",
                  fmt=FMT_AMOUNT)
```

Lines 1203-1214: one label for both countries:

```python
    # This row is the MERGED battery + PV inverter/extra replacement series
    # (esco_pro_forma._merge_replacement_costs adds them together). Both
    # countries now book the PV inverter, so neither may call it "Battery".
    r_repl = w.line(
        "repl", "Equipment replacement (engine schedule)", "USD",
        values=replacement_by_year[:years + 1], fill=INPUT_FILL)
```

Model Basis, lines 2358-2362: both branches format the horizon:

```python
            "proforma_vietnam post-processes the REopt run: an hourly ND57/2025 DPPA settlement layer "
            "(when applicable) and a {}-year developer cash flow with Vietnam tax and debt.".format(horizon)
            if profile.country == "Vietnam" else
            "The proforma engine post-processes the REopt run into a {}-year owner cash flow "
            "with {} tax and debt. There is no wholesale settlement layer: this is "
            "a behind-the-meter self-consumption case with no export.".format(horizon, profile.country),
```

with, near the top of `write_model_basis_sheet`, `horizon = (derivation or {}).get("project_years") or (assumptions or {}).get("analysis_years") or DEFAULT_PROJECT_YEARS`.

Line 2405-2406 becomes a computed bullet:

```python
            _replacement_bullet(assumptions, derivation),
```

with, at module level:

```python
def _replacement_bullet(assumptions, derivation):
    assumptions = assumptions or {}
    pv_inverter = (derivation or {}).get("pv_inverter_replacement") or {}
    parts = ["O&M escalates at its own rate."]
    if assumptions.get("battery_replacement_year"):
        parts.append(
            "Battery replacement (storage inverter and pack together) is booked in year {} "
            "at the replacement unit prices on the Assumptions sheet ({} USD/kW, {} USD/kWh), "
            "the shared replacement policy of both country branches.".format(
                assumptions["battery_replacement_year"],
                _format_unit_price(assumptions.get("bess_replace_cost_per_kw")),
                _format_unit_price(assumptions.get("bess_replace_cost_per_kwh")),
            )
        )
    if pv_inverter.get("cost_usd"):
        parts.append(
            "The PV inverter is booked in year {} at {:.0f} percent of the solved PV capex.".format(
                pv_inverter["year"], pv_inverter["fraction"] * 100
            )
        )
    return " ".join(parts)


def _format_unit_price(value):
    return "n/a" if value is None else "{:,.2f}".format(value)
```

- [ ] **Step 4: Run the audit sheet tests, then both suites, then the gate against the CURRENT baselines**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_audit_sheets -v 2>&1 | tail -5`
Expected: all pass.

Run both suites. Expected: all pass.

Run the gate (Global Constraints). Expected: TOTAL DIFFS > 0. Inspect: every diff must be on the Assumptions sheet (new section, relabelled rows, analysis-period source text), the Model Basis sheet (horizon text, replacement bullet), the Pro Forma (Audit) replacement row label, or, for the Thailand cases only, the year-11 column (the PV inverter now derived in core must equal what report.py derived before: same number, so NO numeric diff there). Any diff in O&M, capex, a bill, dispatch, or a return metric means a defect: stop and fix before continuing. Record the diff summary (sheet, count) in the commit message. Delete `gate_check/`.

- [ ] **Step 5: Commit**

```bash
git add proforma_vietnam/audit_sheets.py proforma_vietnam/tests/test_audit_sheets.py
git commit -m "Assumptions and Model Basis sheets read the replacement record

Replacement Policy section from assumptions and the derivation block; the
storage PCS row is named as the storage inverter; the audit replacement row
says Equipment for both countries; Model Basis formats the horizon from
project_years and names both replacement events from data.

Gate against pre-change baselines: <N> diffs, all text or label cells on
Assumptions, Model Basis and the audit replacement row; no numeric cell moved.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Case files stop carrying the rule; payloads and assumptions regenerated

**Files:**
- Modify: `outputs/vietnam_case/factory_a/case.json`, `case_1..6/case.json`, `outputs/vietnam_case/bess_arbitrage_5mw/case.json`, `bess_arbitrage_5mw_mfg/case.json`
- Modify: `outputs/vietnam_case/factory_a/CASE_JSON_INPUT_GUIDE.md:149, 184-188, 225-228` and the `analysis_years` row; `proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md:482`; `proforma_vietnam/MODEL_AUDIT.md:269-314` (a dated note, not a rewrite)
- Regenerate: 14 `payload.json` + `assumptions.json`

- [ ] **Step 1: Strip the policy-owned keys from the eight Vietnam case files**

```bash
./.venv/Scripts/python.exe - <<'EOF'
import json
from pathlib import Path
files = [Path("outputs/vietnam_case/factory_a/case.json")] + \
        [Path(f"outputs/vietnam_case/factory_a/case_{n}/case.json") for n in range(1, 7)] + \
        [Path("outputs/vietnam_case/bess_arbitrage_5mw/case.json"),
         Path("outputs/vietnam_case/bess_arbitrage_5mw_mfg/case.json")]
for p in files:
    text = p.read_text(encoding="utf-8")
    indent = 2 if '\n  "' in text else 4
    c = json.loads(text)
    storage = c.get("technologies", {}).get("storage", {})
    removed = []
    for key in ("replace_cost_per_kw", "replace_cost_per_kwh", "replace_cost_constant",
                "inverter_replacement_year", "battery_replacement_year",
                "cost_constant_replacement_year"):
        if key in storage:
            removed.append((key, storage.pop(key)))
    if "analysis_years" in c.get("financial", {}):
        removed.append(("analysis_years", c["financial"].pop("analysis_years")))
    p.write_text(json.dumps(c, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
    print(p, removed)
EOF
git diff --stat outputs/
```

Check the diff for each file is only the removed lines (indent preserved). `replace_cost_constant` and `cost_constant_replacement_year` are removed only where present; they were 0 / 10 and REopt's defaults are the same.

- [ ] **Step 2: Regenerate all fourteen payload and assumptions files by dry run**

```bash
for n in 1 2 3 4 5 6; do
  ./.venv/Scripts/python.exe -m proforma_vietnam.run_case --case outputs/vietnam_case/factory_a/case_$n/case.json --dry-run || exit 1
done
for c in bess_arbitrage_5mw bess_arbitrage_5mw_mfg; do
  ./.venv/Scripts/python.exe -m proforma_vietnam.run_case --case outputs/vietnam_case/$c/case.json --dry-run || exit 1
done
for n in 1 2 3 4 5 6; do
  ./.venv/Scripts/python.exe -m proforma_thailand.run_case --case outputs/thailand_case/rofu_thailand/case_$n/case.json --dry-run || exit 1
done
git status --short outputs/ | sort
```

- [ ] **Step 3: Assert what changed and what did not**

```bash
./.venv/Scripts/python.exe - <<'EOF'
import json, subprocess
from pathlib import Path
def committed(path):
    return json.loads(subprocess.check_output(["git", "show", f"HEAD:{path}"]))
# Thailand 1-4: payload byte-identical to HEAD.
for n in (1, 2, 3, 4):
    p = f"outputs/thailand_case/rofu_thailand/case_{n}/payload.json"
    assert json.loads(Path(p).read_text()) == committed(p), p
    a = json.loads(Path(p.replace("payload", "assumptions")).read_text())
    assert a["pv_inverter_replacement_year"] == 11 and "inverter_replacement_year" not in a, p
print("Thailand 1-4 payload unchanged, assumptions renamed")
# Thailand 5-6: only the storage replacement changed.
for n in (5, 6):
    p = f"outputs/thailand_case/rofu_thailand/case_{n}/payload.json"
    new, old = json.loads(Path(p).read_text()), committed(p)
    es_new, es_old = new.pop("ElectricStorage"), old.pop("ElectricStorage")
    assert new == old, p
    assert es_new["replace_cost_per_kw"] == 100.0 and es_new["replace_cost_per_kwh"] == 150.0
    assert es_new["inverter_replacement_year"] == 10 and es_new["battery_replacement_year"] == 10
    es_new2 = {k: v for k, v in es_new.items() if k not in ("replace_cost_per_kw", "replace_cost_per_kwh", "inverter_replacement_year", "battery_replacement_year")}
    es_old2 = {k: v for k, v in es_old.items() if k not in ("replace_cost_per_kw", "replace_cost_per_kwh")}
    assert es_new2 == es_old2, p
    a = json.loads(Path(p.replace("payload", "assumptions")).read_text())
    assert a["pv_inverter_replacement_year"] == 11 and a["battery_replacement_year"] == 10, p
    assert a["bess_replace_cost_per_kw"] == 100.0 and a["bess_replace_cost_per_kwh"] == 150.0, p
print("Thailand 5-6: replacement keys only; assumptions carry the record")
# Vietnam: horizon 20, replacement at install, both years 10, nothing else.
vn = [f"outputs/vietnam_case/factory_a/case_{n}" for n in range(1, 7)] + \
     ["outputs/vietnam_case/bess_arbitrage_5mw", "outputs/vietnam_case/bess_arbitrage_5mw_mfg"]
for d in vn:
    p = f"{d}/payload.json"
    new, old = json.loads(Path(p).read_text()), committed(p)
    assert new["Financial"]["analysis_years"] == 20 and old["Financial"]["analysis_years"] == 25, p
    es = new["ElectricStorage"]
    assert es["replace_cost_per_kw"] == es["installed_cost_per_kw"], p
    assert es["replace_cost_per_kwh"] == es["installed_cost_per_kwh"], p
    assert es["inverter_replacement_year"] == 10 and es["battery_replacement_year"] == 10, p
    keys = ("replace_cost_per_kw", "replace_cost_per_kwh", "inverter_replacement_year", "battery_replacement_year", "replace_cost_constant", "cost_constant_replacement_year")
    strip = lambda x: {k: v for k, v in x.items() if k not in keys}
    new["ElectricStorage"], old["ElectricStorage"] = strip(new["ElectricStorage"]), strip(old["ElectricStorage"])
    new["Financial"].pop("analysis_years"); old["Financial"].pop("analysis_years")
    assert new == old, p
    a = json.loads(Path(f"{d}/assumptions.json").read_text())
    assert a["battery_replacement_year"] == 10 and a["pv_inverter_replacement_year"] == 11, d
print("Vietnam 8: horizon and replacement only")
EOF
```

Expected: the three "print" lines. Any assertion error means a builder change leaked into something else; fix the builder, not the assertion.

- [ ] **Step 4: Update the three documents**

`CASE_JSON_INPUT_GUIDE.md`: the `analysis_years` row says "Omit to use the shared replacement policy horizon (20 years, `proforma_vietnam.defaults.PROJECT_YEARS`)". Rows 184-188 and 225-228 for `replace_cost_per_kw`, `replace_cost_per_kwh`, `inverter_replacement_year`, `battery_replacement_year` say: "Omit to apply the shared replacement policy: whole system (storage inverter and pack) replaced in year 10 at 100 percent of the install price sent. Set only for a sensitivity on the replacement itself." Label `inverter_replacement_year` as the storage PCS year, and add one row noting the PV inverter is booked by the proforma (10 percent of solved PV capex, year 11) and is not a REopt input.

`ESCO_CONTRACT_MODEL_DESIGN.md:482`: change "(Factory A cases use year 11)" to "(Factory A cases follow the shared replacement policy, year 10, since 2026-09-11)".

`MODEL_AUDIT.md`: above the section at line 269, insert a dated note: "2026-09-11: the figures below were computed under the year-11, 80/100 USD replacement and a 25-year horizon. The shared replacement policy (year 10, replacement at install cost, 20 years, PV inverter at year 11) supersedes them; the tables are kept as the audit record of that earlier state and are regenerated in the 2026-09-11 handoff." Do not rewrite the tables.

Check none of the three now contain an em dash you added: `grep -c $'\u2014'` before and after must match.

- [ ] **Step 5: Commit**

```bash
git add outputs/vietnam_case/ outputs/thailand_case/ proforma_vietnam/ESCO_CONTRACT_MODEL_DESIGN.md proforma_vietnam/MODEL_AUDIT.md
git commit -m "Case files stop carrying the replacement rule; payloads and assumptions regenerated

Eight Vietnam case.json files drop analysis_years and the five storage
replacement keys so the shared policy governs. All fourteen payload.json
and assumptions.json regenerated by dry run: Thailand 1-4 payloads are
byte-identical to before, Thailand 5-6 differ only in the four replacement
keys, Vietnam differs only in analysis_years and the replacement keys.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Docker up; ten solves with echo verification

**Files:**
- Regenerate: `results.json` in the eight Vietnam case directories and Thailand `case_5`, `case_6`
- Create (scratchpad, never committed): `resolve.sh`, `verify_echo.py`

- [ ] **Step 1: Start Docker Desktop and the stack; gate on readiness**

```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

Then poll (Bash, from the repo root):

```bash
for i in $(seq 1 60); do docker ps >/dev/null 2>&1 && break; sleep 5; done
docker ps >/dev/null 2>&1 || { echo "docker engine not up after 5 min"; exit 1; }
docker-compose up -d
for i in $(seq 1 120); do
  curl -sf http://localhost:8081/health >/dev/null 2>&1 && \
  [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/v3/job/)" = "405" ] && { echo READY; break; }
  sleep 10
done
```

`READY` must print. The Julia container precompiles on first start; twenty minutes is normal. If the stack was already running before this task (it was not at plan time), run `docker-compose restart django celery` so the bind-mounted code changes are loaded. Never proceed past this step without `READY`; the last session's `&&`-chained loop skipped every solve and still printed success.

- [ ] **Step 2: Write the echo verifier in the scratchpad**

```python
# /c/Users/kongn/AppData/Local/Temp/claude/C--Users-kongn-Pictures-CodeProject-Reopt-API-REopt-API/c90d9f8a-d79c-4d9a-95db-5a5e7cb7c421/scratchpad/verify_echo.py
import json, sys
from pathlib import Path
d = Path(sys.argv[1]); country = sys.argv[2]
r = json.loads((d / "results.json").read_text(encoding="utf-8"))
assert r.get("status") == "optimal", (d, r.get("status"))
i = r["inputs"]
assert i["Financial"]["analysis_years"] == 20, (d, i["Financial"]["analysis_years"])
es = i.get("ElectricStorage") or {}
if es:
    assert es["replace_cost_per_kw"] == es["installed_cost_per_kw"], (d, es)
    assert es["replace_cost_per_kwh"] == es["installed_cost_per_kwh"], (d, es)
    assert es["inverter_replacement_year"] == 10 and es["battery_replacement_year"] == 10, (d, es)
    assert not es.get("model_degradation"), d
pv = i.get("PV")
pv = pv if isinstance(pv, dict) else (pv[0] if pv else {})
if country == "thailand":
    assert pv["installed_cost_per_kw"] == 500.0, (d, pv["installed_cost_per_kw"])
else:
    assert pv.get("installed_cost_per_kw", 480.0) == 480.0, (d, pv)
uuid = r["outputs"].get("run_uuid") or r.get("run_uuid")
print("OK", d, uuid)
```

- [ ] **Step 3: Solve, one case at a time, verifying each before the next**

```bash
S="/c/Users/kongn/AppData/Local/Temp/claude/C--Users-kongn-Pictures-CodeProject-Reopt-API-REopt-API/c90d9f8a-d79c-4d9a-95db-5a5e7cb7c421/scratchpad"
set -e
for n in 1 2 3 4 5 6; do
  d=outputs/vietnam_case/factory_a/case_$n
  ./.venv/Scripts/python.exe -m proforma_vietnam.run_case --case $d/case.json --max-polls 240
  ./.venv/Scripts/python.exe "$S/verify_echo.py" $d vietnam
done
for c in bess_arbitrage_5mw bess_arbitrage_5mw_mfg; do
  d=outputs/vietnam_case/$c
  ./.venv/Scripts/python.exe -m proforma_vietnam.run_case --case $d/case.json --max-polls 240
  ./.venv/Scripts/python.exe "$S/verify_echo.py" $d vietnam
done
for n in 5 6; do
  d=outputs/thailand_case/rofu_thailand/case_$n
  ./.venv/Scripts/python.exe -m proforma_thailand.run_case --case $d/case.json --max-polls 240
  ./.venv/Scripts/python.exe "$S/verify_echo.py" $d thailand
done
echo ALL_TEN_VERIFIED
```

Run this in the background (it takes 30 to 90 minutes) and check the output file; `set -e` stops it at the first failure. `ALL_TEN_VERIFIED` must be the last line. `run_case` writes a workbook named by the NEW run uuid next to the OLD one; Task 9 removes the old.

- [ ] **Step 4: Confirm the solver saw the new inputs, not cached ones**

```bash
for d in outputs/vietnam_case/factory_a/case_{1..6} outputs/vietnam_case/bess_arbitrage_5mw outputs/vietnam_case/bess_arbitrage_5mw_mfg outputs/thailand_case/rofu_thailand/case_{5,6}; do
  ./.venv/Scripts/python.exe -c "
import json,sys; r=json.load(open('$d/results.json')); o=r['outputs']
es=o.get('ElectricStorage',{}); pv=o.get('PV'); pv=pv if isinstance(pv,list) else [pv] if pv else []
print('$d'.split('/')[-1].ljust(24), 'uuid', (o.get('run_uuid') or r.get('run_uuid'))[:8], 'PV', round(sum(p.get('size_kw',0) for p in pv),1), 'BESS', round(es.get('size_kw',0),1), round(es.get('size_kwh',0),1), 'NPV', round(o['Financial'].get('npv',0)))
"; done
```

Record this table; it is the first sight of whether Thailand storage survived 100 percent replacement.

- [ ] **Step 5: Commit the ten results and the regenerated Thailand assumptions**

Do NOT commit the run-time workbooks yet (Task 9 rebuilds them).

```bash
git add outputs/vietnam_case/factory_a/case_*/results.json outputs/vietnam_case/bess_arbitrage_5mw/results.json outputs/vietnam_case/bess_arbitrage_5mw_mfg/results.json outputs/thailand_case/rofu_thailand/case_5/results.json outputs/thailand_case/rofu_thailand/case_6/results.json
git commit -m "Re-solve the ten cases the replacement policy changes

Eight Vietnam cases at 20 years with whole-system BESS replacement at
install cost in year 10; Thailand cases 5 and 6 at 100 / 150 replacement.
Every results.json echo verified: analysis_years, replace costs equal to
install, both replacement years 10, PV price unchanged.

Sizes: <paste the Step 4 table>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Rebuild fourteen workbooks, re-baseline, reconcile

- [ ] **Step 1: Remove the superseded workbooks by uuid, rebuild every case**

```bash
./.venv/Scripts/python.exe - <<'EOF'
import json, re
from pathlib import Path
from proforma_vietnam.rebuild_report import rebuild_report as vn
from proforma_thailand.rebuild_report import rebuild_report as th
cases = [(Path(f"outputs/vietnam_case/factory_a/case_{n}"), vn, "vietnam_report_") for n in range(1, 7)]
cases += [(Path("outputs/vietnam_case/bess_arbitrage_5mw"), vn, "vietnam_report_"),
          (Path("outputs/vietnam_case/bess_arbitrage_5mw_mfg"), vn, "vietnam_report_")]
cases += [(Path(f"outputs/thailand_case/rofu_thailand/case_{n}"), th, "thailand_report_") for n in range(1, 7)]
for d, rebuild, prefix in cases:
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    uuid = r["outputs"].get("run_uuid") or r["run_uuid"]
    for old in d.glob(prefix + "*.xlsx"):
        if "review" in old.name:      # the user's untracked review files
            continue
        if uuid not in old.name:
            old.unlink(); print("removed", old.name)
    out = rebuild(d)
    print("built", out.name)
    kept = [p.name for p in d.glob(prefix + "*.xlsx") if "review" not in p.name]
    assert kept == [out.name], (d, kept)
EOF
git status --short outputs/ | grep -v "review" | sort
```

Exactly one non-review workbook per directory.

- [ ] **Step 2: Regenerate the baselines and run the gate to zero**

```bash
rm -rf baseline_workbooks
./.venv/Scripts/python.exe -c "
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases
built = rebuild_all_cases('.', 'baseline_workbooks')
print(len(built), 'baselines')
"
```

Then the gate from Global Constraints. Expected: `TOTAL DIFFS 0` on all 14. Delete `gate_check/`. Confirm `git status` does not list `baseline_workbooks/`.

- [ ] **Step 3: Reconcile the shipped figures against the new workbooks**

```bash
./.venv/Scripts/python.exe - <<'EOF'
import json, subprocess, io
from pathlib import Path
import openpyxl
def metrics(path_or_bytes, sheet):
    wb = openpyxl.load_workbook(path_or_bytes, data_only=True); ws = wb[sheet]
    out = {}
    for row in ws.iter_rows(min_row=1, max_row=40):
        if isinstance(row[1].value, str) and row[1].value in ("Total Investment (USD)", "Equity IRR", "Project IRR", "Equity NPV (USD)", "Minimum DSCR (debt years)"):
            out[row[1].value] = row[2].value
    return out
rows = []
for d, prefix, sheet in [(f"outputs/thailand_case/rofu_thailand/case_{n}", "thailand_report_", "Owner Returns") for n in range(1,7)] + \
                        [(f"outputs/vietnam_case/factory_a/case_{n}", "vietnam_report_", "Developer Returns") for n in range(1,7)] + \
                        [("outputs/vietnam_case/bess_arbitrage_5mw", "vietnam_report_", "Developer Returns"), ("outputs/vietnam_case/bess_arbitrage_5mw_mfg", "vietnam_report_", "Developer Returns")]:
    new = [p for p in Path(d).glob(prefix + "*.xlsx") if "review" not in p.name][0]
    old_name = [l.split()[-1] for l in subprocess.check_output(["git", "ls-tree", "--name-only", "HEAD~2", d + "/"]).decode().splitlines() if l.endswith(".xlsx") and "review" not in l]
    old_blob = subprocess.check_output(["git", "show", f"HEAD~2:{old_name[0]}"])
    o, n = metrics(io.BytesIO(old_blob), sheet), metrics(new, sheet)
    rows.append((d.split("/")[-1], o, n))
for name, o, n in rows:
    print(name.ljust(24), " | ".join(f"{k}: {o.get(k)!r:>14} -> {n.get(k)!r}" for k in ("Equity IRR", "Equity NPV (USD)", "Total Investment (USD)")))
EOF
```

`HEAD~2` is the commit before Task 8's results commit and Task 7's case commit; adjust the ref if the history differs (`git log --oneline -5`). Save the printed table to the scratchpad as `reconcile.txt`; Task 11 and Task 12 quote it.

- [ ] **Step 4: Commit the fourteen workbooks**

```bash
git add outputs/vietnam_case/ outputs/thailand_case/
git status --short | grep review && { echo "review files staged: STOP"; exit 1; }
git commit -m "Rebuild the fourteen workbooks under the shared replacement policy

One workbook per case, named by the new run uuid; superseded workbooks
removed. Baselines regenerated; gate TOTAL DIFFS 0 on all fourteen.

<paste reconcile.txt>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: SOH check with `model_degradation` on (throwaway)

**Files:**
- Create (scratchpad only): `soh_check.py`, `soh_case6.json`, `soh_arbitrage.json`, `soh_check.md`

- [ ] **Step 1: Write the probe**

The Django model has no `model_degradation` field, so this goes straight to the Julia server on `localhost:8081/reopt/`, which takes the same dict the Celery task sends: the echoed `inputs` of a kept solve plus `Settings.timeout_seconds`, `optimality_tolerance`, `run_bau`.

```python
# /c/Users/kongn/AppData/Local/Temp/claude/C--Users-kongn-Pictures-CodeProject-Reopt-API-REopt-API/c90d9f8a-d79c-4d9a-95db-5a5e7cb7c421/scratchpad/soh_check.py
import json, sys, time, urllib.request
from pathlib import Path
src = Path(sys.argv[1]); out = Path(sys.argv[2])
r = json.loads((src / "results.json").read_text(encoding="utf-8"))
inputs = json.loads(json.dumps(r["inputs"]))
o = r["outputs"]
# Pin every size to the kept solve so the dispatch, and therefore the duty cycle, is the same.
es_out = o["ElectricStorage"]; es = inputs["ElectricStorage"]
es["min_kw"] = es["max_kw"] = es_out["size_kw"]; es["min_kwh"] = es["max_kwh"] = es_out["size_kwh"]
pv_out = o.get("PV"); pv_out = pv_out if isinstance(pv_out, list) else ([pv_out] if pv_out else [])
if pv_out:
    pv = inputs["PV"]; pv = pv if isinstance(pv, dict) else pv[0]
    pv["min_kw"] = pv["max_kw"] = pv_out[0]["size_kw"]
es["model_degradation"] = True
es["degradation"] = {"maintenance_strategy": "augmentation"}
for k in ("replace_cost_per_kw", "replace_cost_per_kwh", "replace_cost_constant"):
    es[k] = 0.0        # REopt zeroes them anyway; be explicit so the warning is silent
s = inputs.setdefault("Settings", {})
s.setdefault("timeout_seconds", 3600); s.setdefault("optimality_tolerance", 0.001); s["run_bau"] = False
s["solver_name"] = "HiGHS"
req = urllib.request.Request("http://localhost:8081/reopt/", data=json.dumps(inputs).encode(), headers={"Content-Type": "application/json"})
t0 = time.time()
with urllib.request.urlopen(req, timeout=4000) as resp:
    result = json.loads(resp.read())
out.write_text(json.dumps(result, indent=1), encoding="utf-8")
body = result.get("results", result)          # http.jl wraps as {"results": {...}}
es_r = body["ElectricStorage"]
soh = es_r["state_of_health"]
first = next((i for i, v in enumerate(soh) if v < 0.8), None)
years = inputs["Financial"]["analysis_years"]
print(json.dumps({
    "case": str(src), "solve_seconds": round(time.time() - t0),
    "days": len(soh), "soh_end": soh[-1],
    "first_day_below_0.8": first, "years_to_0.8": None if first is None else round(first / 365, 2),
    "maintenance_cost_pv_usd": es_r.get("maintenance_cost"),
    "kept_size_kw": es_out["size_kw"], "kept_size_kwh": es_out["size_kwh"],
}, indent=1))
```

- [ ] **Step 2: Run it for Thailand case 6 and Vietnam bess_arbitrage_5mw**

```bash
S="/c/Users/kongn/AppData/Local/Temp/claude/C--Users-kongn-Pictures-CodeProject-Reopt-API-REopt-API/c90d9f8a-d79c-4d9a-95db-5a5e7cb7c421/scratchpad"
./.venv/Scripts/python.exe "$S/soh_check.py" outputs/thailand_case/rofu_thailand/case_6 "$S/soh_case6.json" | tee "$S/soh_case6.txt"
./.venv/Scripts/python.exe "$S/soh_check.py" outputs/vietnam_case/bess_arbitrage_5mw "$S/soh_arbitrage.json" | tee "$S/soh_arbitrage.txt"
```

If the Julia server rejects a key from the echoed inputs (HTTP 500 with a message naming it), delete that key from `inputs` in the script and rerun; log which keys were dropped in `soh_check.md`. If the solve exceeds an hour, stop and record that instead of waiting; a result is preferable but not required.

- [ ] **Step 3: Compare with our year-10 event**

For each case, in the scratchpad `soh_check.md`, record: years to SOH 0.8 under the same dispatch; REopt's augmentation `maintenance_cost` (present value at the owner rate, daily discounting, 5 percent per year battery price decline); the present value of our year-10 event, `size_kw*replace_kw + size_kwh*replace_kwh` discounted 10 years at the owner rate (`0.11` Thailand, `0.10` Vietnam); and one sentence on whether year 10 is conservative, matched, or optimistic against the fade model. State plainly that the fade coefficients are NREL laboratory defaults with no LFP or 30 degree calibration. Nothing from these solves goes under `outputs/`.

Confirm: `git status --short` shows nothing new under `outputs/`.

---

### Task 11: Thailand memo, translation, deck, artifact

**Files:**
- Modify: `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md`, `KEEN_THAILAND_MEMO_VI.md`, `Rofu_Thailand_Tariff_Structure_Internal.pptx`
- Redeploy: HTML artifact at `https://claude.ai/code/artifact/6316674c-e8e3-4c74-bee6-4cf69faec835` (scratchpad `rofu_report.html`)

- [ ] **Step 1: Pull every memo figure from the six new workbooks, never by hand**

```bash
./.venv/Scripts/python.exe - <<'EOF'
import json
from pathlib import Path
import openpyxl
for n in range(1, 7):
    d = Path(f"outputs/thailand_case/rofu_thailand/case_{n}")
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    wb = openpyxl.load_workbook([p for p in d.glob("thailand_report_*.xlsx")][0], data_only=True)
    def cell(sheet, label):
        for row in wb[sheet].iter_rows(min_row=1, max_row=60):
            if isinstance(row[1].value, str) and row[1].value == label:
                return row[2].value
    o = r["outputs"]; es = o.get("ElectricStorage", {}); pv = o["PV"]; pv = pv if isinstance(pv, list) else [pv]
    print(n, dict(pv_kw=round(sum(p["size_kw"] for p in pv), 1), bess_kw=round(es.get("size_kw", 0), 1), bess_kwh=round(es.get("size_kwh", 0), 1),
        capex=cell("Owner Returns", "Total Investment (USD)"), savings_y1=cell("Buyer Analysis", "Year 1 Savings (USD)"),
        savings_pct=cell("Buyer Analysis", "Year 1 Savings (% of BAU)"), eq_irr=cell("Owner Returns", "Equity IRR"), eq_npv=cell("Owner Returns", "Equity NPV (USD)"),
        payback=cell("Owner Returns", "Simple Equity Payback (Years)"), min_dscr=cell("Owner Returns", "Minimum DSCR (debt years)")))
EOF
```

Also pull the year-10 and year-11 cells of the "O&M + Replacement (USD)" column on Owner Returns for cases 1 and 6, the curtailment percentages (from the Technical Results sheet, same labels the current memo used), and the tCO2e per year. Write the whole set to the scratchpad as `memo_figures.json`.

- [ ] **Step 2: Rewrite `KEEN_THAILAND_MEMO.md`**

Keep the structure. Changes required:
- Date: "11 September 2026".
- "One thing has changed" section: now the history has three price points. State it in one paragraph: 675 USD/kW-equivalent (300 + 250, storage rejected); 325 at 70 percent replacement (storage selected, both at 475/25 and 500/20); and now 325 at 100 percent replacement per Keen's ruling. Then state the result of THIS run for cases 5 and 6 from `memo_figures.json`: if storage is still selected, say the conclusion held at the most conservative point tested; if it dropped to zero in either case, say so, say which, withdraw the storage recommendation for that case and explain the mechanism (a full-price replacement at year 10 discounted at 11 percent adds about 35 percent of install cost to the battery's lifetime cost).
- The six-case table and every figure quoted in prose from `memo_figures.json`.
- A new subsection under "Technical basis", "Equipment replacement", four sentences: whole-system BESS replacement at year 10 at 100 percent of install (Keen's ruling, covering the storage inverter and the pack together, since REopt's storage O&M is plain maintenance with no capacity-fade allowance); PV inverter at 10 percent of PV capex at year 11 (Allotrope convention, provisional); both capitalised and depreciated over the 5-year machinery life; the same rule now applies to Allotrope's Vietnam work.
- A paragraph reporting the Task 10 SOH check: years to 80 percent under this site's dispatch, and whether year 10 is conservative or optimistic against it, with the calibration caveat.
- "What remains provisional": still fourteen inputs; the PV inverter fraction and year are two of them (they were before; say it).
- Check: `grep -c $'\u2014' KEEN_THAILAND_MEMO.md` is 0; every number in the memo appears in `memo_figures.json` (write a five-line script that extracts every `[0-9][0-9,]{3,}` token from the memo and asserts it is in the figures set, allowing the rounding the memo uses).

- [ ] **Step 3: Rewrite `KEEN_THAILAND_MEMO_VI.md` to match, figure for figure**

Translate the changed sections; leave unchanged paragraphs as they are. Then run the same figure-extraction check across both files and assert the two multisets of numeric tokens are identical.

- [ ] **Step 4: Update the deck**

Open `Rofu_Thailand_Tariff_Structure_Internal.pptx` with `python-pptx`; list every slide's text; update every figure and the storage conclusion on the slides that carry them (8 and 10 last time; check all). No layout change. Save. Re-list to confirm no stale figure remains (grep the extracted text for each OLD headline number: 1,304,997; 1,922,690; 66.4; 47.8; 428.7; 2,378).

- [ ] **Step 5: Redeploy the artifact**

Edit the scratchpad `rofu_report.html` with the new figures and the replacement subsection (same content as the memo, same order), then publish with the Artifact tool to the existing URL (`url` parameter). Do not pass a favicon. Read the published page back once and spot-check the six-case table against `memo_figures.json`.

- [ ] **Step 6: Commit**

```bash
git add outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO_VI.md outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx
git commit -m "Reissue the Keen Thailand memo, translation and deck at 100 percent replacement

Every figure regenerated from the six new workbooks; the storage
conclusion restated from this solve; a replacement subsection and the
SOH check added to the technical basis.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: Handoff, register, graph, final verification

**Files:**
- Modify: `SESSION_NOTES.md` (prepend a 2026-09-11 handoff entry; edit items 17 and 18 in the register)

- [ ] **Step 1: Run everything once more, clean**

Both suites, the tariff suite, the gate (TOTAL DIFFS 0), `git status` clean apart from the user's review files and `baseline_workbooks/` (ignored). Record the counts.

- [ ] **Step 2: Write the handoff entry at the top of `SESSION_NOTES.md`**

Sections, in this order, all in plain prose with no em dash:
- What was ruled and why (the four decisions, the degradation answer).
- What changed in the code, by file, one line each.
- The reconcile table from Task 9 (old vs new IRR, NPV, capex, every one of the fourteen cases).
- The Thailand storage outcome at 100 percent, in one sentence.
- The SOH check result and its caveat.
- What did not change: Thailand 1-4 solver results (payload byte-identical), Vietnam DPPA residual, the API mapping gaps.
- Follow-ups: Vietnam narrative decks (now stale on three axes: levelization, horizon, replacement); API mapping lacks `direct_ownership`, `contract_years`, VAT, `surplus_export`; PV inverter depreciated under the BESS class; the gate still keys baselines by filename.
- In the 2026-09-11 register: mark items 17 and 18 "Closed 2026-09-11, see handoff above"; add item 19 for the API mapping gap.

- [ ] **Step 3: Update the knowledge graph and commit**

```bash
graphify update .
git add SESSION_NOTES.md graphify-out/
git commit -m "Record the replacement policy handoff; close register items 17 and 18

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git log --oneline -14
git status --short
```

- [ ] **Step 4: Leave Docker as it is**

Do not stop the stack; the user may want to re-run. Note in the handoff that it is up.
