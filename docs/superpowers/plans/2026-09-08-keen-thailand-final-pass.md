# Keen Thailand Final Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the degradation double count from the shared financial core, give Thailand its first regression gate, load the client-confirmed benchmark values, and reissue the Keen deliverable.

**Architecture:** `proforma_vietnam` is the shared financial core; `proforma_thailand` drives the same engine with Thai defaults. The fix divides three generation-linked quantities by REopt's levelization factor before the proforma applies its own degradation. A Thailand baseline is captured *before* that fix so the gate can prove the change does exactly what is claimed and nothing more.

**Tech Stack:** Python 3.14 on `./.venv/Scripts/python.exe`, `unittest`, `openpyxl`, REopt V3 via Django + Julia in Docker.

**Spec:** `docs/superpowers/specs/2026-09-08-keen-thailand-final-pass-design.md`

## Global Constraints

- Use `./.venv/Scripts/python.exe`. It has **no Django**. Django work runs in the `reopt_api-django-1` container.
- Never create, modify or delete anything under `reo/` (deprecated V1/V2, returns 410).
- Never modify the client source `.xlsm` files under the Keen Project folder.
- **No em dash (U+2014) in generated report output.** Use a comma, a colon, or a full stop.
- The placeholder marker is exactly `PLACEHOLDER - pending Keen confirmation`, matched by equality in `placeholder_keys()`. Never invent a variant.
- `outputs/vietnam_case/` and `baseline_workbooks/` **may** be modified in this plan, by explicit user authorisation dated 2026-09-08. This reverses a previous standing prohibition. Outside these tasks the prohibition still applies.
- **`baseline_workbooks/` is gitignored scratch and has never been tracked** (`.gitignore:139`, added in `3a8e418a` alongside the gate itself). Never `git add -f` it and never edit that rule. Baselines are regenerated locally, so no task commits them, and the gate protects only within a session that generated them first.
- Confirmed benchmark values (spec D8): `pv_installed_cost_per_kw` 475.0, `annual_om_per_kw` 7.125 (1.5 percent of PV capex), `bess_installed_cost_per_kw` 100.0, `bess_installed_cost_per_kwh` 150.0, `bess_replace_cost_per_kw` 70.0 (70 percent), `bess_replace_cost_per_kwh` 105.0 (70 percent), `discount_rate` 0.11.
- Measured levelization factors: Thailand 0.960612, Vietnam 0.952869.

**Verification, run all four before and after every task:**

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t . -v
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t . -v
./.venv/Scripts/python.exe -m unittest reoptjl.test.test_thailand_tariff -v
```

Gate (fourth check), from the repo root:

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

Baseline at plan start: Thailand 124/124, Vietnam 509/509, tariff 14/14, gate TOTAL DIFFS 0. Delete the scratch `gate_check/` afterwards; never commit it.

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `proforma_thailand/rebuild_report.py` | **New.** Offline workbook rebuild from a saved Thailand case dir, mirroring `proforma_vietnam/rebuild_report.py` | 1 |
| `proforma_thailand/tests/test_rebuild_report.py` | **New.** Covers the rebuild entry point | 1 |
| `proforma_vietnam/tools/compare_workbooks.py` | Extend `rebuild_all_cases` to cover both countries | 2 |
| `baseline_workbooks/thailand_rofu_case_N/` | **New.** Six Thailand baselines | 3 |
| `proforma_vietnam/esco_pro_forma.py` | Levelization factor and its application | 4 |
| `proforma_vietnam/tests/test_levelization.py` | **New.** Unit cover for the factor and the three scaled quantities | 4 |
| `proforma_vietnam/MODEL_AUDIT.md` | Record the measured residual | 5 |
| `proforma_thailand/defaults/thailand_defaults.json` | Confirmed benchmark values | 8 |
| `proforma_thailand/defaults/__init__.py` | Derive the three coupled values instead of storing literals | 8 |
| `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md` | English memo | 12 |
| `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO_VI.md` | **New.** Vietnamese memo | 13 |

---

### Task 1: Thailand offline rebuild entry point

Thailand has `run_case.py`, which submits to the solver, but no offline rebuild. The gate must rebuild workbooks from saved JSON without Docker, exactly as Vietnam does. Without this task there is no way to build a Thailand baseline.

**Files:**
- Create: `proforma_thailand/rebuild_report.py`
- Test: `proforma_thailand/tests/test_rebuild_report.py`

**Interfaces:**
- Consumes: `proforma_thailand.report.build_thailand_report(reopt_results, assumptions) -> (workbook, extras)`
- Produces: `rebuild_report(case_dir, prepared_on=None) -> Path` writing `thailand_report_<run_uuid>.xlsx` into `case_dir`

Note: `prepared_on` is honoured by the shared builders at `proforma_vietnam/audit_sheets.py:220`, `audit_sheets.py:2501` and `xlsx_builder.py:370`, each reading `(assumptions or {}).get("prepared_on") or date.today().isoformat()`. Thailand renders through those same builders, so setting the key pins the date on the Cover subtitle, the Executive Summary subtitle and the Assumptions row.

- [ ] **Step 1: Write the failing test**

```python
"""Cover the offline Thailand workbook rebuild."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from proforma_thailand.rebuild_report import rebuild_report

CASE_DIR = Path("outputs/thailand_case/rofu_thailand/case_1")


class RebuildReportTests(unittest.TestCase):
    def _scratch_case(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for name in ("results.json", "assumptions.json", "case.json"):
            source = CASE_DIR / name
            if source.exists():
                shutil.copy2(source, tmp / name)
        return tmp

    def test_rebuild_writes_a_workbook_named_for_the_run(self):
        case_dir = self._scratch_case()
        results = json.loads((case_dir / "results.json").read_text(encoding="utf-8"))

        out_path = rebuild_report(case_dir)

        self.assertTrue(out_path.exists())
        self.assertEqual(
            out_path.name, "thailand_report_{}.xlsx".format(results["run_uuid"])
        )

    def test_prepared_on_pins_the_date_so_two_rebuilds_match(self):
        """Without a pinned date the workbook carries date.today() in three
        cells, which would make every baseline comparison fail a day later."""
        from openpyxl import load_workbook

        first = load_workbook(rebuild_report(self._scratch_case(), prepared_on="2026-01-01"))
        second = load_workbook(rebuild_report(self._scratch_case(), prepared_on="2026-01-01"))

        sheet_one = first["Executive Summary"]
        sheet_two = second["Executive Summary"]
        self.assertEqual(
            [row for row in sheet_one.iter_rows(values_only=True)],
            [row for row in sheet_two.iter_rows(values_only=True)],
        )
        joined = " ".join(
            str(value)
            for row in sheet_one.iter_rows(values_only=True)
            for value in row
            if isinstance(value, str)
        )
        self.assertIn("prepared 2026-01-01", joined)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_rebuild_report -v`
Expected: `ModuleNotFoundError: No module named 'proforma_thailand.rebuild_report'`

- [ ] **Step 3: Write the implementation**

```python
"""Rebuild the Thailand report workbook offline from saved case outputs.

The workbook is pure post-processing of results.json + assumptions.json, so it
can be regenerated without Django or a REopt re-run:

    python -m proforma_thailand.rebuild_report --case-dir outputs/thailand_case/rofu_thailand/case_1

Mirrors proforma_vietnam/rebuild_report.py. The Thailand report builder takes
assumptions directly rather than going through a sweep-override helper, so
there is no cash_flow_overrides_from_assumptions call here.
"""
import argparse
import json
from pathlib import Path

from proforma_thailand.report import build_thailand_report


def rebuild_report(case_dir, prepared_on=None):
    case_dir = Path(case_dir)
    results = json.loads((case_dir / "results.json").read_text(encoding="utf-8"))
    assumptions = json.loads((case_dir / "assumptions.json").read_text(encoding="utf-8"))
    if prepared_on is not None:
        assumptions["prepared_on"] = prepared_on
    case_path = case_dir / "case.json"
    if case_path.exists():
        assumptions["case_config"] = json.loads(case_path.read_text(encoding="utf-8"))

    workbook, _extras = build_thailand_report(
        results, dict(assumptions, run_uuid=results.get("run_uuid"))
    )
    out_path = case_dir / "thailand_report_{}.xlsx".format(results["run_uuid"])
    workbook.save(out_path)
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rebuild a Thailand report workbook offline."
    )
    parser.add_argument(
        "--case-dir", required=True,
        help="Case directory with results.json + assumptions.json.",
    )
    args = parser.parse_args(argv)
    print(rebuild_report(args.case_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_rebuild_report -v`
Expected: 2 tests PASS

- [ ] **Step 5: Run the Thailand suite to confirm nothing regressed**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t .`
Expected: 126 tests OK

- [ ] **Step 6: Commit**

```bash
git add proforma_thailand/rebuild_report.py proforma_thailand/tests/test_rebuild_report.py
git commit -m "Add an offline Thailand workbook rebuild

Mirrors proforma_vietnam/rebuild_report.py. The regression gate needs to
rebuild from saved JSON without Docker, and Thailand had no entry point
for that. prepared_on is honoured by the shared builders, so a pinned date
makes two rebuilds byte-comparable."
```

---

### Task 2: Extend the gate to both countries

**Files:**
- Modify: `proforma_vietnam/tools/compare_workbooks.py` (`CASE_DIRS`, `rebuild_all_cases`)
- Test: `proforma_vietnam/tests/test_compare_workbooks.py`

**Interfaces:**
- Consumes: `proforma_thailand.rebuild_report.rebuild_report` from Task 1
- Produces: `rebuild_all_cases(repo_root, out_dir, prepared_on=GATE_PREPARED_ON)` returning a dict that now includes six `thailand_rofu_case_N` entries alongside the eight Vietnam ones

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_compare_workbooks.py`:

```python
class RebuildAllCasesCoversBothCountriesTests(unittest.TestCase):
    """The gate protected Vietnam only, which is how two Critical defects
    reached six Thailand client workbooks past a green test run."""

    def test_case_dirs_include_the_six_thailand_cases(self):
        from proforma_vietnam.tools.compare_workbooks import CASE_DIRS

        thailand = [d for d in CASE_DIRS if "thailand_case" in d]
        self.assertEqual(len(thailand), 6)

    def test_thailand_case_names_do_not_collide_with_vietnam(self):
        from proforma_vietnam.tools.compare_workbooks import case_name_for

        self.assertEqual(
            case_name_for("outputs/thailand_case/rofu_thailand/case_1"),
            "thailand_rofu_case_1",
        )
        self.assertEqual(
            case_name_for("outputs/vietnam_case/factory_a/case_1"),
            "factory_a_case_1",
        )
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_compare_workbooks -v`
Expected: FAIL, `ImportError: cannot import name 'case_name_for'`

- [ ] **Step 3: Implement**

Replace the `CASE_DIRS` list and `rebuild_all_cases` in `proforma_vietnam/tools/compare_workbooks.py`:

```python
CASE_DIRS = [
    "outputs/vietnam_case/factory_a/case_1",
    "outputs/vietnam_case/factory_a/case_2",
    "outputs/vietnam_case/factory_a/case_3",
    "outputs/vietnam_case/factory_a/case_4",
    "outputs/vietnam_case/factory_a/case_5",
    "outputs/vietnam_case/factory_a/case_6",
    "outputs/vietnam_case/bess_arbitrage_5mw",
    "outputs/vietnam_case/bess_arbitrage_5mw_mfg",
    "outputs/thailand_case/rofu_thailand/case_1",
    "outputs/thailand_case/rofu_thailand/case_2",
    "outputs/thailand_case/rofu_thailand/case_3",
    "outputs/thailand_case/rofu_thailand/case_4",
    "outputs/thailand_case/rofu_thailand/case_5",
    "outputs/thailand_case/rofu_thailand/case_6",
]


def case_name_for(case_dir):
    """Baseline directory name for a case path.

    Thailand cases are prefixed because "case_1" alone collides with Vietnam's
    factory_a case_1 once both countries share one baseline tree.
    """
    parts = Path(case_dir).parts
    if "thailand_case" in parts:
        return "thailand_{}_{}".format(parts[-2].replace("rofu_thailand", "rofu"), parts[-1])
    return "_".join(parts[-2:])


def rebuild_all_cases(repo_root, out_dir, prepared_on=GATE_PREPARED_ON):
    """Rebuild every saved case into ``out_dir``; return {case name: path}.

    Copies each case's results/assumptions/case JSON into a scratch directory so
    the country rebuilder writes there instead of over the tracked workbooks.
    """
    import shutil

    from proforma_thailand.rebuild_report import rebuild_report as rebuild_thailand
    from proforma_vietnam.rebuild_report import rebuild_report as rebuild_vietnam

    repo_root = Path(repo_root)
    out_dir = Path(out_dir)
    built = {}
    for case_dir in CASE_DIRS:
        source = repo_root / case_dir
        name = case_name_for(case_dir)
        target = out_dir / name
        target.mkdir(parents=True, exist_ok=True)
        for filename in ("results.json", "assumptions.json", "case.json"):
            candidate = source / filename
            if candidate.exists():
                shutil.copy2(candidate, target / filename)
        rebuild = rebuild_thailand if "thailand_case" in case_dir else rebuild_vietnam
        built[name] = rebuild(target, prepared_on=prepared_on)
    return built
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_compare_workbooks -v`
Expected: PASS

- [ ] **Step 5: Confirm the Vietnam half of the gate is still clean**

Run the gate command from Global Constraints. Expected: the eight Vietnam cases print `OK`; the six Thailand cases raise `FileNotFoundError` on their missing baselines. That is the expected state until Task 3.

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/tools/compare_workbooks.py proforma_vietnam/tests/test_compare_workbooks.py
git commit -m "Extend the regression gate to Thailand cases

Adds the six Rofu cases to CASE_DIRS and dispatches to the country's own
rebuilder. Thailand names are prefixed because case_1 alone collides with
Vietnam's factory_a case_1 in a shared baseline tree."
```

---

### Task 3: Capture the Thailand baselines

Do this **before** the de-levelization fix. A baseline captured now turns the gate into the instrument that measures the fix.

**Files:**
- Create: `baseline_workbooks/thailand_rofu_case_1/` through `_6/`

- [ ] **Step 1: Build the six workbooks at the pinned date**

```bash
./.venv/Scripts/python.exe -c "
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases
built = rebuild_all_cases('.', 'gate_check')
for name, path in sorted(built.items()):
    print(name, path.name)
"
```

- [ ] **Step 2: Copy the Thailand ones into the baseline tree**

```bash
./.venv/Scripts/python.exe -c "
import shutil
from pathlib import Path
for n in range(1, 7):
    name = 'thailand_rofu_case_%d' % n
    src = next(Path('gate_check', name).glob('thailand_report_*.xlsx'))
    dst = Path('baseline_workbooks', name)
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst / src.name)
    print('baselined', dst / src.name)
"
```

- [ ] **Step 3: Run the full gate and confirm it is clean on all fourteen**

Run the gate command from Global Constraints.
Expected: `TOTAL DIFFS 0` across fourteen cases.

- [ ] **Step 4: Remove the scratch directory**

```bash
rm -rf gate_check
```

- [ ] **Step 5: Do not commit. There is nothing to commit.**

`baseline_workbooks/` is excluded by `.gitignore:139`, with the comment
"Scratch baseline for the Vietnam workbook regression gate. Regenerate, never
commit." That rule was added in `3a8e418a`, the same commit that created the
gate, so it is deliberate design and not drift. Zero files under
`baseline_workbooks/` have ever been tracked, including the eight Vietnam ones.

Do **not** `git add -f`, and do **not** edit `.gitignore`. The baselines are
local scratch by design. Task 3 completes with no commit; its deliverable is the
six directories on disk and the clean gate run in Step 3.

The consequence to keep in mind for the rest of this plan: the baselines are the
only copy of pre-change behaviour, and they live only on this machine. Task 6
preserves a copy before overwriting them.

---

### Task 4: De-levelize the generation-linked quantities

**Files:**
- Modify: `proforma_vietnam/esco_pro_forma.py`
- Test: `proforma_vietnam/tests/test_levelization.py` (create)

**Interfaces:**
- Produces: `_levelization_factor(pv_outputs) -> float`, module-private, returning 1.0 when there is no usable PV production

- [ ] **Step 1: Write the failing test**

```python
"""Cover the de-levelization of REopt's levelized dispatch.

REopt applies a levelization factor to PV production inside the optimisation,
so annual_energy_produced_kwh is an escalation/discount/degradation weighted
average and year_one_energy_produced_kwh is the raw first year. The dispatch
series and therefore year_one_bill_before_tax carry that weighting despite
their names. The proforma then applies (1 - deg)^y on its own axis, so
without this correction degradation is counted roughly twice.
"""
import unittest

from proforma_vietnam.esco_pro_forma import _levelization_factor


class LevelizationFactorTests(unittest.TestCase):
    def test_factor_is_the_ratio_of_levelized_to_raw_production(self):
        pv_outputs = [{
            "year_one_energy_produced_kwh": 2524235.0,
            "annual_energy_produced_kwh": 2424811.22,
        }]

        self.assertAlmostEqual(_levelization_factor(pv_outputs), 0.960612, places=6)

    def test_multiple_arrays_are_summed_before_the_ratio(self):
        pv_outputs = [
            {"year_one_energy_produced_kwh": 1000.0, "annual_energy_produced_kwh": 950.0},
            {"year_one_energy_produced_kwh": 3000.0, "annual_energy_produced_kwh": 2850.0},
        ]

        self.assertAlmostEqual(_levelization_factor(pv_outputs), 0.95, places=9)

    def test_no_pv_yields_one_so_a_battery_only_case_is_untouched(self):
        self.assertEqual(_levelization_factor([]), 1.0)

    def test_zero_production_yields_one_rather_than_dividing_by_zero(self):
        pv_outputs = [{
            "year_one_energy_produced_kwh": 0.0,
            "annual_energy_produced_kwh": 0.0,
        }]

        self.assertEqual(_levelization_factor(pv_outputs), 1.0)

    def test_missing_fields_yield_one(self):
        self.assertEqual(_levelization_factor([{"size_kw": 100.0}]), 1.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_levelization -v`
Expected: FAIL, `ImportError: cannot import name '_levelization_factor'`

- [ ] **Step 3: Add the factor helper**

Add to `proforma_vietnam/esco_pro_forma.py`, near the other module-private helpers:

```python
def _levelization_factor(pv_outputs):
    """Ratio of REopt's levelized annual PV production to its raw first year.

    REopt applies this weighting to the PV production parameter inside the
    optimisation, so every dispatch series and the bill computed from them
    carry it, despite the "year_one" prefix on their names. Dividing by this
    factor recovers a true first year for the proforma to degrade on its own
    time axis. Returns 1.0 whenever there is no usable production, which
    leaves battery-only cases untouched.
    """
    raw = sum(_value(pv, "year_one_energy_produced_kwh") for pv in pv_outputs)
    levelized = sum(_value(pv, "annual_energy_produced_kwh") for pv in pv_outputs)
    if raw <= 0 or levelized <= 0:
        return 1.0
    return levelized / raw
```

- [ ] **Step 4: Run the factor tests and confirm they pass**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_levelization -v`
Expected: 5 tests PASS

- [ ] **Step 5: Write the failing test for the application**

Append to `proforma_vietnam/tests/test_levelization.py`:

```python
class DeLevelizationApplicationTests(unittest.TestCase):
    """Only three quantities depend on PV production. BAU, capex and O&M
    must not move at all: that invariant is what catches scaling the wrong
    thing, which is the likely way to get this change wrong."""

    def _inputs(self):
        from proforma_vietnam.esco_pro_forma import _apply_de_levelization

        return _apply_de_levelization

    def test_served_energy_is_inflated_by_one_over_lambda(self):
        apply = self._inputs()
        cash_flow_inputs = {
            "project_served_pv_kwh": [100.0, 200.0],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 0.0,
            "optimized_demand_charge_vnd": 0.0,
        }

        apply(cash_flow_inputs, 0.8)

        self.assertEqual(cash_flow_inputs["project_served_pv_kwh"], [125.0, 250.0])

    def test_the_savings_delta_scales_not_the_bill(self):
        apply = self._inputs()
        cash_flow_inputs = {
            "project_served_pv_kwh": [],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 500.0,
            "optimized_demand_charge_vnd": 400.0,
        }

        apply(cash_flow_inputs, 0.8)

        # savings 200 / 0.8 = 250, so the bill lands at 1000 - 250 = 750.
        # A test asserting 800 / 0.8 = 1000 would be asserting the wrong rule.
        self.assertAlmostEqual(cash_flow_inputs["optimized_evn_bill_vnd"], 750.0)
        self.assertAlmostEqual(cash_flow_inputs["optimized_demand_charge_vnd"], 375.0)

    def test_bau_is_never_touched_because_it_has_no_pv(self):
        apply = self._inputs()
        cash_flow_inputs = {
            "project_served_pv_kwh": [],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 500.0,
            "optimized_demand_charge_vnd": 400.0,
        }

        apply(cash_flow_inputs, 0.8)

        self.assertEqual(cash_flow_inputs["bau_evn_bill_vnd"], 1000.0)
        self.assertEqual(cash_flow_inputs["bau_demand_charge_vnd"], 500.0)

    def test_lambda_of_one_is_a_no_op(self):
        apply = self._inputs()
        before = {
            "project_served_pv_kwh": [100.0],
            "bau_evn_bill_vnd": 1000.0,
            "optimized_evn_bill_vnd": 800.0,
            "bau_demand_charge_vnd": 500.0,
            "optimized_demand_charge_vnd": 400.0,
        }
        after = dict(before, project_served_pv_kwh=list(before["project_served_pv_kwh"]))

        apply(after, 1.0)

        self.assertEqual(after, before)
```

- [ ] **Step 6: Run it and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_levelization -v`
Expected: FAIL, `ImportError: cannot import name '_apply_de_levelization'`

- [ ] **Step 7: Add the application helper**

```python
def _apply_de_levelization(cash_flow_inputs, levelization_factor):
    """Undo REopt's levelization on the three quantities that carry it.

    ``project_served_pv_kwh`` is PV production, so it scales directly. The
    bills do not: BAU carries no PV and is a true first year, so it is the
    SAVINGS DELTA that is levelized. Scaling the optimized bill by
    1 / lambda would inflate the whole bill including the part PV never
    touched. Capex, debt and O&M are absent here on purpose; none of them
    depends on production.
    """
    if levelization_factor == 1.0:
        return

    served = cash_flow_inputs.get("project_served_pv_kwh")
    if served:
        cash_flow_inputs["project_served_pv_kwh"] = [
            value / levelization_factor for value in served
        ]

    for optimized_key, bau_key in (
        ("optimized_evn_bill_vnd", "bau_evn_bill_vnd"),
        ("optimized_demand_charge_vnd", "bau_demand_charge_vnd"),
    ):
        bau = cash_flow_inputs[bau_key]
        savings = bau - cash_flow_inputs[optimized_key]
        cash_flow_inputs[optimized_key] = bau - savings / levelization_factor
```

- [ ] **Step 8: Wire it into the builder**

In `proforma_vietnam/esco_pro_forma.py`, immediately after the `cash_flow_inputs = {...}` literal closes and **before** the `pv_capacity_kw = ...` line that begins the grid-arbitrage block, insert:

```python
    # REopt returns levelized dispatch, so year_one_bill_before_tax and every
    # dispatch series already carry degradation. The cash flow then applies
    # (1 - deg)^y on its own axis, which counted degradation roughly twice
    # and understated savings by 4.10 percent (Thailand) / 4.95 percent
    # (Vietnam). Undo the levelization here so the cash flow's own degradation
    # is the only one applied.
    _apply_de_levelization(cash_flow_inputs, _levelization_factor(pv_outputs))
```

- [ ] **Step 9: Run the levelization tests**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_levelization -v`
Expected: 9 tests PASS

- [ ] **Step 10: Run both full suites**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .`
Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t .`

Expected: some tests that pin absolute financial figures will now FAIL, because the numbers legitimately changed. Record each failing test name and its before/after values. Do **not** adjust a test until Task 5 has confirmed the movement matches `1 / lambda`. A failure that does not match that pattern is a bug in this task, not a stale expectation.

- [ ] **Step 11: Commit**

```bash
git add proforma_vietnam/esco_pro_forma.py proforma_vietnam/tests/test_levelization.py
git commit -m "Undo REopt's levelization before the proforma degrades

REopt applies its levelization factor to PV production inside the
optimisation, so the dispatch series and the bill computed from them carry
degradation despite the year_one prefix on their names. The proforma then
applied (1 - deg)^y on top, counting it roughly twice and understating
savings by 4.10 percent in Thailand and 4.95 percent in Vietnam.

Only three quantities carry the weighting. BAU bills, capex, debt and O&M
do not depend on production and are deliberately untouched. It is the
savings delta that is de-levelized, not the bill."
```

---

### Task 5: Prove the movement, then update the pinned expectations

**Files:**
- Modify: `proforma_vietnam/MODEL_AUDIT.md`
- Modify: whichever tests Task 4 Step 10 recorded as failing

- [ ] **Step 1: Measure the movement across all fourteen cases**

```bash
./.venv/Scripts/python.exe -c "
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases, compare_workbooks
built = rebuild_all_cases('.', 'gate_after')
for name, path in sorted(built.items()):
    diffs = compare_workbooks('baseline_workbooks/%s/%s' % (name, path.name), path)
    print(name, len(diffs), 'diffs')
    for d in diffs[:5]:
        print('   ', d)
"
```

- [ ] **Step 2: Assert the invariant that catches a wrong fix**

For each case, confirm from the diff output that:

1. Bill-savings rows and PV energy rows moved by a factor of `1 / lambda` (1.041 Thailand, 1.049 Vietnam)
2. The optimized bill moved to `bau - (bau - optimized) / lambda`, a **smaller** relative move. Do not check it against `1 / lambda`
3. Capex, debt principal and O&M rows show **zero** diffs

Item 3 is the real check. If any capex, debt or O&M row moved, this task fails: something was scaled that does not depend on PV production. Stop and fix Task 4 rather than proceeding.

- [ ] **Step 3: Measure the Vietnam storage residual**

```bash
./.venv/Scripts/python.exe -c "
import json, glob
for p in sorted(glob.glob('outputs/vietnam_case/factory_a/case_*/results.json')):
    d = json.load(open(p)); o = d.get('outputs', d)
    et = o.get('ElectricTariff', {}); st = o.get('ElectricStorage') or {}
    bau = et.get('year_one_bill_before_tax_bau') or 0.0
    opt = et.get('year_one_bill_before_tax') or 0.0
    print(p.split('/')[-2], 'savings %.0f' % (bau - opt), 'storage_kwh', st.get('size_kwh'))
"
```

Record the storage-attributable share of savings you can establish, and state the residual as `share x 4.95 percent`. If the share cannot be established from the outputs alone, say so explicitly rather than guessing.

- [ ] **Step 4: Write the finding into MODEL_AUDIT.md**

Add a section recording: the measured lambda per country, the invariant that capex/debt/O&M did not move, and the residual from Step 3 as a number with its derivation. Do not write prose where a number is available.

- [ ] **Step 5: Update the pinned test expectations**

For each test recorded in Task 4 Step 10, update the expected value and add a one-line comment naming the cause, for example:

```python
        # Moved by 1 / 0.952869 at the de-levelization fix (2026-09-08).
```

- [ ] **Step 6: Run all three suites green**

Expected: Thailand 126/126, Vietnam 514/514 or higher, tariff 14/14.

- [ ] **Step 7: Commit**

```bash
git add proforma_vietnam/MODEL_AUDIT.md proforma_vietnam/tests proforma_thailand/tests
git commit -m "Record the de-levelization movement and repin the affected tests

Confirms the invariant: capex, debt and O&M rows did not move, only
production-linked ones. Records the measured residual for Vietnam's
storage-attributable savings, which the lambda division over-corrects."
```

---

### Task 6: Re-baseline all fourteen workbooks

**Files:**
- Modify: `baseline_workbooks/` (all fourteen)

- [ ] **Step 1: Preserve the pre-change baselines, because git does not**

Spec D5 requires the old baselines to be recoverable before they are overwritten. The original plan text claimed they were tracked and committed. **That was wrong**: `baseline_workbooks/` is gitignored scratch and has never been tracked, so `HEAD` holds no copy and overwriting them destroys the only record of pre-change behaviour.

Copy all fourteen aside first, into the plan's SDD workspace:

```bash
cp -r baseline_workbooks .superpowers/sdd/2026-09-08-keen-thailand-final-pass/baselines-pre-delevelization
ls -d .superpowers/sdd/2026-09-08-keen-thailand-final-pass/baselines-pre-delevelization/*/ | wc -l
```

Expected: 14. Do not proceed until that reads 14. The durable record of what changed is Task 5's measurement written into `MODEL_AUDIT.md`; this copy is what lets you re-measure without rebuilding.

Then confirm the working tree is clean, so the overwrite buries nothing:

```bash
git status --short --ignored=no
```

Expected: no output. If there is output, stop: an earlier task left the baselines dirty.

- [ ] **Step 2: Rebuild and overwrite**

```bash
./.venv/Scripts/python.exe -c "
import shutil
from pathlib import Path
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases
built = rebuild_all_cases('.', 'gate_rebase')
for name, path in sorted(built.items()):
    dst = Path('baseline_workbooks', name)
    for old in dst.glob('*.xlsx'):
        old.unlink()
    shutil.copy2(path, dst / path.name)
    print('rebaselined', name)
"
rm -rf gate_rebase
```

- [ ] **Step 3: Confirm the gate is clean**

Run the gate command from Global Constraints. Expected: `TOTAL DIFFS 0`.

- [ ] **Step 4: Commit**

Nothing to stage: `baseline_workbooks/` is gitignored scratch. The overwrite is
a local state change only, and this task produces no commit.

The record of what moved is Task 5's entry in `MODEL_AUDIT.md`, which IS
committed, plus the pre-change copy preserved in Step 1.

---

### Task 7: Finish the "Year 1" relabelling

Three occurrences were already corrected to "levelized annual". Executive Summary, Buyer Analysis and Year 1 Snapshot still say "Year 1" over figures carrying the same treatment, leaving the workbook self-inconsistent between sheets.

Note: after Task 4 the figures are no longer levelized in the cash flow, so re-read each label against what it now shows. A label that was wrong before this plan may be **correct** now. Change only labels that still misdescribe their value.

**Files:**
- Modify: `proforma_vietnam/xlsx_builder.py`, `proforma_vietnam/proforma_schema.py`, `proforma_vietnam/audit_sheets.py`

- [ ] **Step 1: Find every remaining occurrence**

```bash
grep -rn "Year 1\|Year-1\|year_one" proforma_vietnam/xlsx_builder.py proforma_vietnam/proforma_schema.py proforma_vietnam/audit_sheets.py
```

- [ ] **Step 2: For each, decide from the data path whether the label is now accurate**

Write the decision down per occurrence before editing anything. An occurrence fed by `cash_flow_result["annual_cash_flows"][0]` is a true first year after Task 4 and its "Year 1" label is correct. An occurrence fed directly from a REopt `year_one_*` field is still levelized and needs relabelling.

- [ ] **Step 3: Apply only the changes justified in Step 2**

- [ ] **Step 4: Rebuild one workbook and read the changed cells**

```bash
./.venv/Scripts/python.exe -m proforma_vietnam.rebuild_report --case-dir outputs/vietnam_case/factory_a/case_1
```

Open the result and confirm each changed label reads correctly against its value. The gate cannot do this for you: it compares text, so it will report the change without judging whether it is right.

- [ ] **Step 5: Re-baseline the affected workbooks and run the gate**

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/
git commit -m "Finish relabelling the levelized figures

Three occurrences were corrected earlier, leaving the workbook
inconsistent between sheets. Each remaining occurrence was checked against
its data path: those now fed by the corrected cash flow are true first-year
figures and keep the Year 1 label."
```

---

### Task 8: Load the confirmed benchmarks and derive the coupled values

**Files:**
- Modify: `proforma_thailand/defaults/thailand_defaults.json`
- Modify: `proforma_thailand/defaults/__init__.py`
- Modify: `proforma_thailand/tests/test_case_builder.py:201-244`, `proforma_thailand/tests/test_report.py:675-696`
- Test: `proforma_thailand/tests/test_thailand_defaults.py`

**Interfaces:**
- Produces: `derived_value(key) -> float` in `proforma_thailand/defaults/__init__.py`, computing the three coupled values from their base cost and fraction

- [ ] **Step 1: Write the failing test**

Append to `proforma_thailand/tests/test_thailand_defaults.py`:

```python
class CoupledDefaultsAreDerivedTests(unittest.TestCase):
    """Holding these as literals is what let a price change leave the file
    self-contradictory: at 100/150 install with the old 150/125 replacement,
    replacing a battery cost more per kW than buying one."""

    def test_om_is_one_and_a_half_percent_of_pv_capex(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of

        pv_capex = value_of(FINANCIAL_DEFAULTS, "pv_installed_cost_per_kw")
        om = value_of(FINANCIAL_DEFAULTS, "annual_om_per_kw")

        self.assertAlmostEqual(om, pv_capex * 0.015, places=9)
        self.assertAlmostEqual(om, 7.125, places=9)

    def test_replacement_is_seventy_percent_of_install(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of

        for install_key, replace_key in (
            ("bess_installed_cost_per_kw", "bess_replace_cost_per_kw"),
            ("bess_installed_cost_per_kwh", "bess_replace_cost_per_kwh"),
        ):
            install = value_of(FINANCIAL_DEFAULTS, install_key)
            replace = value_of(FINANCIAL_DEFAULTS, replace_key)
            self.assertAlmostEqual(replace, install * 0.70, places=9)

    def test_replacing_never_costs_more_than_buying_new(self):
        from proforma_thailand.defaults import FINANCIAL_DEFAULTS, value_of

        for install_key, replace_key in (
            ("bess_installed_cost_per_kw", "bess_replace_cost_per_kw"),
            ("bess_installed_cost_per_kwh", "bess_replace_cost_per_kwh"),
        ):
            self.assertLess(
                value_of(FINANCIAL_DEFAULTS, replace_key),
                value_of(FINANCIAL_DEFAULTS, install_key),
            )

    def test_the_seven_confirmed_inputs_lost_the_placeholder_marker(self):
        from proforma_thailand.defaults import placeholder_keys

        confirmed = {
            "pv_installed_cost_per_kw", "annual_om_per_kw",
            "bess_installed_cost_per_kw", "bess_installed_cost_per_kwh",
            "bess_replace_cost_per_kw", "bess_replace_cost_per_kwh",
            "discount_rate",
        }

        self.assertEqual(confirmed & placeholder_keys(), set())
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults -v`
Expected: FAIL on all four.

- [ ] **Step 3: Update the JSON values and their provenance**

In `proforma_thailand/defaults/thailand_defaults.json`, set:

- `pv_installed_cost_per_kw.value` to `475.0`, source: client-confirmed C&I rooftop range 450 to 500 USD/kWp, midpoint taken
- `annual_om_per_kw.value` to `7.125`, source: **client direction at 1.5 percent of PV capex.** Move the MDPI citation into the `note` field as a published lower bound of 1 percent. Do not leave it in `source`: it assumes 1 percent and no longer supports the value (spec D9a)
- `bess_installed_cost_per_kw.value` to `100.0`, `bess_installed_cost_per_kwh.value` to `150.0`, source: client-confirmed
- `bess_replace_cost_per_kw.value` to `70.0`, `bess_replace_cost_per_kwh.value` to `105.0`, source: client direction, 70 percent of install cost
- `discount_rate.value` to `0.11`, source: client-confirmed. Keep the existing note explaining that the prior 11.5 percent was a third-party developer's cost of equity
- `power_factor_mitigation_cost` and `grid_connection_cost`: keep the values, change `source` to record exclusion from capex at client direction (spec D10)

Every one of these loses the `PLACEHOLDER - pending Keen confirmation` string except `power_factor_mitigation_cost` and `grid_connection_cost`, which are excluded rather than confirmed and keep their marker.

- [ ] **Step 4: Add the derivation guard**

Add to `proforma_thailand/defaults/__init__.py`:

```python
# The coupling each derived default must satisfy: (derived, base, fraction).
# Kept as an assertion rather than a computation so the JSON stays the single
# readable source of every number, while a price change that desyncs a coupled
# value fails at import instead of silently shipping.
_DERIVED_COUPLINGS = (
    ("annual_om_per_kw", "pv_installed_cost_per_kw", 0.015),
    ("bess_replace_cost_per_kw", "bess_installed_cost_per_kw", 0.70),
    ("bess_replace_cost_per_kwh", "bess_installed_cost_per_kwh", 0.70),
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


_assert_couplings_hold()
```

- [ ] **Step 5: Run the defaults test and confirm it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults -v`
Expected: PASS

- [ ] **Step 6: Update the two O&M rounding tests**

`proforma_thailand/tests/test_case_builder.py:206-244` and `proforma_thailand/tests/test_report.py:675-696` pin the old 7.5 sent / 8.0 applied pair. Change to 7.125 sent / 7.0 applied, and update the docstrings, which name the old figures.

The applied value must remain asserted against what REopt **returns**, not against a recomputed expectation. That is the whole point of those tests.

- [ ] **Step 7: Run the Thailand suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t .`
Expected: OK

- [ ] **Step 8: Commit**

```bash
git add proforma_thailand/defaults/ proforma_thailand/tests/
git commit -m "Load the client-confirmed benchmarks and guard the coupled ones

PV capex 475, BESS 100/150, discount rate 11 percent, O&M at 1.5 percent
of PV capex per client direction, BESS replacement at 70 percent of
install.

Adds an import-time assertion for the three couplings. Without it the
70 percent replacement and the 1.5 percent O&M are literals that a future
price change silently desyncs, which is exactly how the file arrived at a
state where replacing a battery cost more per kW than buying one.

The MDPI citation moves from source to note: it assumes 1 percent O&M and
no longer supports the value."
```

---

### Task 9: Disclose the two excluded inputs honestly

**Files:**
- Modify: `proforma_thailand/report.py:100-118` (`compute_power_factor_compensation`)

- [ ] **Step 1: Write the failing test**

Append to `proforma_thailand/tests/test_report.py`:

```python
class ExcludedInputsAreDisclosedAsChoicesTests(unittest.TestCase):
    """"Not required" is a technical conclusion this analysis does not
    support. "Excluded at client direction" is what actually happened, and
    a reader is entitled to tell the two apart."""

    def test_power_factor_status_names_the_client_direction(self):
        from proforma_thailand.report import compute_power_factor_compensation

        result = compute_power_factor_compensation({})

        self.assertIn("client", result["status"].lower())
        self.assertNotIn("none required", result["status"].lower())
        self.assertEqual(result["compensation_kvar"], 0.0)
        self.assertEqual(result["mitigation_cost_usd"], 0.0)
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report -v`

- [ ] **Step 3: Change the status wording**

Set the status string to exactly:

```
Excluded from capex at client direction; site kVAR data not requested
```

Keep the numeric outputs at 0.0. Do the same for `grid_connection_cost` wherever it is disclosed on the Assumptions or Model Basis sheet.

- [ ] **Step 4: Run the test and the suite**

- [ ] **Step 5: Commit**

```bash
git add proforma_thailand/
git commit -m "Disclose power factor and grid connection as client exclusions

Both are excluded from capex at client direction. The prior wording risked
reading as a technical finding that no mitigation was required, which the
analysis does not support because the site kVAR maximum was never obtained."
```

---

### Task 10: Guard the inverter cost derivation end to end

The derivation in `report.py` reads solved PV capex. Every existing inverter test injects the cost explicitly, so the derivation itself is unguarded. This is the exact code that already broke once, when `initial_capital_cost` was read off PV outputs where that field does not exist, silently making inverter replacement inert while tests stayed green.

**Files:**
- Test: `proforma_thailand/tests/test_report.py`

- [ ] **Step 1: Write the failing test**

```python
class InverterCostIsDerivedFromSolvedCapexTests(unittest.TestCase):
    """The one path no existing test covers: cost taken from the solved PV
    capex rather than injected. Reading a field that does not exist on PV
    outputs made this inert once already."""

    def test_inverter_replacement_is_nonzero_when_only_solved_capex_is_present(self):
        from proforma_thailand.report import build_thailand_report

        results = self._results_with_solved_pv(size_kw=1000.0, cost_per_kw=475.0)
        assumptions = self._assumptions_without_explicit_inverter_cost()

        workbook, _extras = build_thailand_report(results, assumptions)

        cells = [
            value
            for sheet in workbook.worksheets
            for row in sheet.iter_rows(values_only=True)
            for value in row
        ]
        labels = [v for v in cells if isinstance(v, str) and "nverter" in v]
        self.assertTrue(labels, "no inverter row rendered at all")

        # 10 percent of 1000 kW x 475 USD/kW = 47,500, discounted into year 11.
        amounts = [v for v in cells if isinstance(v, (int, float)) and v > 0]
        self.assertTrue(
            any(abs(v - 47500.0) < 1.0 for v in amounts),
            "inverter cost was not derived from solved PV capex",
        )

    def test_the_row_is_not_labelled_as_a_battery_replacement(self):
        """It rendered as "Battery replacement (engine schedule)" in case_1,
        which has no battery. That reached the client."""
        from proforma_thailand.report import build_thailand_report

        results = self._results_with_solved_pv(size_kw=1000.0, cost_per_kw=475.0)
        workbook, _extras = build_thailand_report(
            results, self._assumptions_without_explicit_inverter_cost()
        )

        text = " ".join(
            value
            for sheet in workbook.worksheets
            for row in sheet.iter_rows(values_only=True)
            for value in row
            if isinstance(value, str)
        )
        self.assertNotIn("Battery replacement", text)
```

Build `_results_with_solved_pv` and `_assumptions_without_explicit_inverter_cost` from the existing fixtures in this file. **The fixture must carry `PV.installed_cost_per_kw`**: a fixture lacking it makes `_pv_capex` return 0, which is precisely how the earlier provenance guard passed while testing nothing.

- [ ] **Step 2: Run it and confirm it fails or passes for the right reason**

If it passes immediately, verify by temporarily breaking the derivation that the test catches it. A guard that cannot fail is not a guard.

- [ ] **Step 3: Fix the derivation if the test found a real defect**

- [ ] **Step 4: Run the Thailand suite**

- [ ] **Step 5: Commit**

```bash
git add proforma_thailand/tests/test_report.py proforma_thailand/report.py
git commit -m "Guard the inverter cost derivation from solved PV capex

Every existing inverter test injects the cost, leaving the derivation
itself uncovered. That derivation already broke once by reading a field
absent from PV outputs, making the feature inert against green tests. The
fixture carries installed_cost_per_kw so _pv_capex is non-zero, which is
what a previous guard got wrong."
```

---

### Task 11: Re-solve the six Thailand cases

**Prerequisite: Docker.** Only the database container is running at plan start.

- [ ] **Step 1: Bring up the stack**

```bash
docker-compose up -d
```

- [ ] **Step 2: Wait for Julia to answer**

```bash
curl -s -m 5 http://localhost:8081/health
```

Retry until it responds. Do not proceed on a silent failure.

- [ ] **Step 3: Run each case**

```bash
for n in 1 2 3 4 5 6; do
  ./.venv/Scripts/python.exe -m proforma_thailand.run_case \
    --case "outputs/thailand_case/rofu_thailand/case_$n/case.json" \
    --out  "outputs/thailand_case/rofu_thailand/case_$n"
done
```

Note: `run_case` needs the Django API at `localhost:8000`, not the venv's Python packages. If the venv cannot reach it, run from inside the `reopt_api-django-1` container.

- [ ] **Step 4: Confirm every case solved**

```bash
./.venv/Scripts/python.exe -c "
import json, glob
for p in sorted(glob.glob('outputs/thailand_case/rofu_thailand/case_*/results.json')):
    d = json.load(open(p))
    o = d.get('outputs', d)
    pv = o.get('PV') or {}
    st = o.get('ElectricStorage') or {}
    print(p.split('/')[-2], d.get('status'), 'pv_kw', pv.get('size_kw'),
          'bess_kwh', st.get('size_kwh'))
"
```

Expected: all six `optimal`. A case at a bound means the bound decided the answer; report it rather than accepting it.

- [ ] **Step 5: Compare against the pre-change results and write down what moved**

Specifically state whether storage is now built where it previously was not. Spec section "Expected change in the answer" predicts it may be. Confirm or refute against the numbers.

- [ ] **Step 6: Re-baseline Thailand and run the gate**

- [ ] **Step 7: Commit**

```bash
git add outputs/thailand_case/
git commit -m "Re-solve the six Rofu cases on the confirmed benchmarks"
```

---

### Task 12: Rewrite the English memo

**Files:**
- Modify: `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md`

- [ ] **Step 1: Regenerate every figure in the memo from the new `summary.json` files**

Do not carry a single number over by hand. The last memo shipped with figures that predated their own fixes.

- [ ] **Step 2: Add the curtailment finding**

State the curtailed kWh and its share of production, that `electric_to_grid_series_kw` is identically zero, and what that means for sizing and for storage. This is a client-actionable finding absent from the previous memo.

- [ ] **Step 3: If the storage conclusion reversed, say so as a changed conclusion**

The previous memo told Keen storage does not pay. If it now does, the memo must say the recommendation changed and why, not quietly present new numbers.

- [ ] **Step 4: Check the disclosures**

- O&M applied as 7.00, not the 7.125 sourced
- Power factor and grid connection excluded at client direction
- Twelve inputs still provisional
- No REopt emissions figures anywhere: AVERT, Cambium and EASIUR have no Thailand coverage and every such output is zero

- [ ] **Step 5: Scan for forbidden content**

```bash
grep -c "—" outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md
grep -niE "VAS|Circular 45|QĐ963|QD963|EVN|ESCO|Vietnam" outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md
```

Expected: zero em dashes, and no Vietnamese accounting standards, tariff decisions or ESCO language on a Thai client document. Search for the Unicode `QĐ963` as well as ASCII `QD963`: a previous guard banned only the ASCII form while the render used the Unicode one.

- [ ] **Step 6: Commit**

---

### Task 13: Vietnamese memo

**Files:**
- Create: `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO_VI.md`

- [ ] **Step 1: Translate the English memo**

For Allotrope internal use. The English version stays the client deliverable.

- [ ] **Step 2: Confirm every figure matches the English memo exactly**

Translate the prose, never the numbers. A transcription error between two versions of one memo is the failure mode here.

- [ ] **Step 3: Check for em dashes and commit**

---

### Task 14: HTML report artifact

- [ ] **Step 1: Build a single-page HTML report**

Six-case comparison table, the sizing and economics headline, the roof-binding and curtailment findings, and the provisional-input disclosure. Source every number from `summary.json`, not from the memo prose.

- [ ] **Step 2: Publish it as an artifact and give the user the link**

---

### Task 15: Update the tariff deck

**Files:**
- Modify: `outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx`

The deck was built by a concurrent session against the pre-change numbers. Leaving it is not an option: two documents describing the same site would disagree.

**Two constraints established before writing this task.** Commit `7f501692` added the 2.6 MB `.pptx` and nothing else: **there is no build script**, so the deck cannot be regenerated and must be edited in place. And **`python-pptx` is not installed** in `./.venv`, so `import pptx` currently fails. The concurrent session evidently used a different environment.

- [ ] **Step 1: Install the dependency**

```bash
./.venv/Scripts/python.exe -m pip install python-pptx
```

Confirm with `./.venv/Scripts/python.exe -c "import pptx; print(pptx.__version__)"`.

- [ ] **Step 2: Extract every number currently in the deck**

```bash
./.venv/Scripts/python.exe -c "
from pptx import Presentation
p = Presentation('outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx')
for i, slide in enumerate(p.slides, 1):
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            print('--- slide', i, '---')
            print(shape.text_frame.text[:600])
"
```

- [ ] **Step 3: List which of those figures the re-solve changed**

Write the list down before editing. The deck also covers PEA tariff structure and a reconciled June 2025 bill, neither of which this plan touches. Change only what actually moved.

- [ ] **Step 4: Edit those runs in place, and the speaker notes that repeat them**

Edit text at the run level rather than replacing a paragraph, so the deck's formatting survives.

- [ ] **Step 5: Verify the deck still opens with ten slides and ten note pages**

```bash
./.venv/Scripts/python.exe -c "
from pptx import Presentation
p = Presentation('outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx')
print('slides', len(p.slides.__iter__.__self__._sldIdLst))
print('with notes', sum(1 for s in p.slides if s.has_notes_slide))
"
```

Expected: 10 slides, 10 with notes, matching what the concurrent session recorded in `CODEX_SESSION.md`.

- [ ] **Step 6: Commit**

---

### Task 16: Repo hygiene, final verification, merge

- [ ] **Step 1: Report the dead code rather than deleting it**

`proforma_vietnam/audit_sheets.py` carries two unreachable ESCO discount-to-EVN fallback strings at lines 295 and 2519, reachable only when the structure is neither DPPA, physical, nor direct ownership. Line 2002 also contains an em dash inside generated report output. Report all three to the user; do not delete or change them in this plan, as they touch Vietnam output outside this plan's scope.

Note: `test_assumptions_list_the_active_placeholders` was already de-tautologised at `proforma_thailand/tests/test_case_builder.py:119-129`. No action.

- [ ] **Step 2: Raise the repository size question, do not act on it unilaterally**

About 102 MB sits under `outputs/thailand_case/` and 66 MB under `outputs/vietnam_case/`. The regression gate rebuilds from those `results.json` files, so deleting them breaks the gate. Present the user with the LFS-versus-prune choice and the gate dependency. Do not decide it in this plan.

- [ ] **Step 3: Run all four verifications one final time**

Expected: three suites green, gate `TOTAL DIFFS 0`.

- [ ] **Step 4: Confirm the working tree is clean**

```bash
git status --short
```

Pre-existing untracked `outputs/vietnam_case/factory_a/case_*/vietnam_report_review*.xlsx` files belong to the user and are expected. Anything else must be resolved.

- [ ] **Step 5: Merge to master**

```bash
git checkout master
git merge --ff-only thailand-adaptation
git log --oneline -3
```

`--ff-only` is deliberate: master is zero commits ahead, so a fast-forward is possible and a merge commit would be noise. If it refuses, master has moved and the situation needs reporting, not forcing.

- [ ] **Step 6: Report to the user**

State what merged, the final six-case results, whether the storage conclusion changed, and the two decisions deferred to them from Steps 1 and 2.

---

## Notes for the executor

**The gate is necessary, not sufficient.** `compare_workbooks` reads with `values_only=True`, so it compares cell text and formulas but is blind to number formats, fonts, fills, column widths, merged ranges, defined names and charts. This already mattered once: an FX cell's `number_format` displayed 32.5 as "33" and the gate could not see it. Any styling change must be verified by reading the built workbook directly.

**The gate also cannot see the input path.** It rebuilds from saved `results.json`, so `case_builder.py`, `pvwatts_client.py` and `validators.py` are outside its coverage entirely.

**Recurring failure modes on this branch.** Each of these actually happened; two reached client documents twice.

1. Reading a field that does not exist on the object, making a feature a silent no-op while tests stay green
2. A test that passes identically with and without the feature it names
3. A test fixture drifting from production, so the suite exercises a path production never takes
4. A fix applied to one render site while an identical second goes unnoticed. Three separate instances
5. A correct value under a label that misleads the reader
6. Vietnamese identity or ESCO language leaking onto a Thai client document
7. A guard present but not wired to production, or narrowed until it passes
8. A stale artifact read as current
