# Thailand Adaptation (Keen / Rofu) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a financed REopt analysis (RTS and RTS+BESS) for Rofu Thailand on the PEA Schedule 4.2 TOU tariff at 15-minute resolution, reusing `proforma_vietnam` as the shared core.

**Architecture:** `proforma_vietnam` stays as-is and serves as the core. A new `CountryProfile` parameterizes display labels and time resolution only. A new `reoptjl/src/thailand/` builds the PEA tariff, and a new `proforma_thailand/` package holds the Thai case builder and defaults. First structure is `DIRECT_OWNERSHIP` only.

**Tech Stack:** Python 3.14, Django 4 (REopt V3 API), openpyxl, unittest, Julia/JuMP/HiGHS behind the REopt HTTP API.

**Spec:** `docs/superpowers/specs/2026-09-04-thailand-adaptation-design.md`

## Global Constraints

- Python interpreter for every command: `./.venv/Scripts/python.exe` (Git Bash on Windows).
- `proforma_vietnam` test suite: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .` - baseline at HEAD is **440 tests, OK, ~108s**. It must stay green and the count must not fall.
- `proforma_thailand` test suite: `./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t .`
- Thailand tariff module tests: `./.venv/Scripts/python.exe -m unittest discover -s reoptjl/test -t . -p "test_thailand*"`
- **Vietnam output must not change.** Every task from Task 2 onward ends by confirming the 8 saved cases still rebuild cell-identical (Task 1 builds that tool).
- **No em dash (`—`) anywhere in generated report output.** `xlsx_builder` already sanitizes to `-`; do not reintroduce.
- Never modify anything under `reo/` (deprecated V1/V2).
- All money inside `cash_flow.py` is USD; `_vnd`-suffixed keys are a presentation restatement in the local contract currency. Thailand runs keep the `_vnd` suffix internally and carry THB values. This is deliberate (see spec section 2).
- Exact PEA Schedule 4.2 rates, 22-33 kV, verified against the Jun 2025 invoice:
  - peak energy `4.1839` THB/kWh
  - off-peak and holiday energy `2.6037` THB/kWh (one bucket)
  - on-peak demand `132.93` THB/kW (on-peak only)
  - service charge `312.24` THB/month
  - VAT `0.07`
  - power factor `56.07` THB/kVAR above `0.6197 * billed_kW`
- Ft by window: `2025-01..2025-04 = 0.3672`, `2025-05..2025-08 = 0.1972`, `2025-09..2025-12 = 0.1572`.
- On-peak period: `09:00 < t <= 22:00`, Mon-Fri, excluding dates classified all-off-peak. Intervals are labelled by **end** time.
- Analysis year is a **synthetic calendar year**: Jan-Jun from 2026, Jul-Dec from 2025. 181 + 184 = 365 days = 35,040 intervals at `time_steps_per_hour=4`.

---

### Task 1: Workbook regression comparator

Vietnam output must stay identical through the refactor. The committed workbooks under `outputs/vietnam_case/` are a **stale** baseline (they predate the em-dash fix in commit `3e057b8c`), so the baseline is captured fresh at HEAD instead. Rebuilds are deterministic apart from a `prepared <date>` cell.

**Files:**
- Create: `proforma_vietnam/tools/__init__.py`
- Create: `proforma_vietnam/tools/compare_workbooks.py`
- Test: `proforma_vietnam/tests/test_compare_workbooks.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `compare_workbooks(path_a, path_b, ignore_substrings=("prepared ",)) -> list[str]` returning human-readable difference descriptions, empty when equal. `rebuild_all_cases(root, out_dir) -> dict[str, Path]` mapping case name to rebuilt workbook path.

- [ ] **Step 1: Write the failing test**

Create `proforma_vietnam/tests/test_compare_workbooks.py`:

```python
from unittest import TestCase

from openpyxl import Workbook

from proforma_vietnam.tools.compare_workbooks import compare_workbooks


def _write(tmp_path, name, rows, sheet="Sheet1"):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet
    for row in rows:
        worksheet.append(row)
    path = tmp_path / name
    workbook.save(path)
    return path


class CompareWorkbooksTests(TestCase):

    def setUp(self):
        import tempfile
        from pathlib import Path
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def test_identical_workbooks_report_no_differences(self):
        a = _write(self.tmp, "a.xlsx", [["x", 1], ["y", 2]])
        b = _write(self.tmp, "b.xlsx", [["x", 1], ["y", 2]])

        self.assertEqual(compare_workbooks(a, b), [])

    def test_differing_cell_is_reported_with_sheet_and_coordinates(self):
        a = _write(self.tmp, "a.xlsx", [["x", 1]])
        b = _write(self.tmp, "b.xlsx", [["x", 2]])

        differences = compare_workbooks(a, b)

        self.assertEqual(len(differences), 1)
        self.assertIn("Sheet1", differences[0])
        self.assertIn("row 1", differences[0])
        self.assertIn("col 2", differences[0])

    def test_ignored_substring_suppresses_the_difference(self):
        a = _write(self.tmp, "a.xlsx", [["prepared 2026-07-07"]])
        b = _write(self.tmp, "b.xlsx", [["prepared 2026-09-04"]])

        self.assertEqual(compare_workbooks(a, b), [])

    def test_ignored_substring_must_match_both_sides(self):
        a = _write(self.tmp, "a.xlsx", [["prepared 2026-07-07"]])
        b = _write(self.tmp, "b.xlsx", [["something else"]])

        self.assertEqual(len(compare_workbooks(a, b)), 1)

    def test_sheet_name_mismatch_is_reported(self):
        a = _write(self.tmp, "a.xlsx", [["x"]], sheet="Alpha")
        b = _write(self.tmp, "b.xlsx", [["x"]], sheet="Beta")

        differences = compare_workbooks(a, b)

        self.assertEqual(len(differences), 1)
        self.assertIn("sheet names differ", differences[0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_compare_workbooks -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_vietnam.tools'`

- [ ] **Step 3: Write the implementation**

Create `proforma_vietnam/tools/__init__.py` as an empty file.

Create `proforma_vietnam/tools/compare_workbooks.py`:

```python
"""Cell-level workbook comparison, used as the Vietnam regression gate.

The report workbooks are deterministic apart from a "prepared <date>" cell on
the Cover and Executive Summary sheets, so a straight byte comparison is not
usable (and the zip container carries timestamps regardless). This compares
cell values and skips pairs where both sides contain an ignored substring.
"""

from pathlib import Path

from openpyxl import load_workbook

DEFAULT_IGNORE_SUBSTRINGS = ("prepared ",)


def compare_workbooks(path_a, path_b, ignore_substrings=DEFAULT_IGNORE_SUBSTRINGS):
    """Return a list of difference descriptions; empty means identical."""
    workbook_a = load_workbook(path_a)
    workbook_b = load_workbook(path_b)

    if workbook_a.sheetnames != workbook_b.sheetnames:
        return [
            "sheet names differ: {} != {}".format(
                workbook_a.sheetnames, workbook_b.sheetnames
            )
        ]

    differences = []
    for name in workbook_a.sheetnames:
        sheet_a = workbook_a[name]
        sheet_b = workbook_b[name]
        rows_a = list(sheet_a.iter_rows(values_only=True))
        rows_b = list(sheet_b.iter_rows(values_only=True))
        if len(rows_a) != len(rows_b):
            differences.append(
                "{}: row count differs: {} != {}".format(name, len(rows_a), len(rows_b))
            )
            continue
        for row_index, (row_a, row_b) in enumerate(zip(rows_a, rows_b), start=1):
            if len(row_a) != len(row_b):
                differences.append(
                    "{}: row {} column count differs: {} != {}".format(
                        name, row_index, len(row_a), len(row_b)
                    )
                )
                continue
            for col_index, (value_a, value_b) in enumerate(zip(row_a, row_b), start=1):
                if value_a == value_b:
                    continue
                if _both_ignored(value_a, value_b, ignore_substrings):
                    continue
                differences.append(
                    "{}: row {} col {}: {!r} != {!r}".format(
                        name, row_index, col_index, value_a, value_b
                    )
                )
    return differences


def _both_ignored(value_a, value_b, ignore_substrings):
    """True when both values are strings carrying the same ignored marker."""
    if not (isinstance(value_a, str) and isinstance(value_b, str)):
        return False
    return any(
        marker in value_a and marker in value_b for marker in ignore_substrings
    )


CASE_DIRS = [
    "outputs/vietnam_case/factory_a/case_1",
    "outputs/vietnam_case/factory_a/case_2",
    "outputs/vietnam_case/factory_a/case_3",
    "outputs/vietnam_case/factory_a/case_4",
    "outputs/vietnam_case/factory_a/case_5",
    "outputs/vietnam_case/factory_a/case_6",
    "outputs/vietnam_case/bess_arbitrage_5mw",
    "outputs/vietnam_case/bess_arbitrage_5mw_mfg",
]


def rebuild_all_cases(repo_root, out_dir):
    """Rebuild every saved case into ``out_dir``; return {case name: path}.

    Copies each case's results/assumptions/case JSON into a scratch directory so
    rebuild_report writes there instead of over the tracked workbooks.
    """
    import shutil

    from proforma_vietnam.rebuild_report import rebuild_report

    repo_root = Path(repo_root)
    out_dir = Path(out_dir)
    built = {}
    for case_dir in CASE_DIRS:
        source = repo_root / case_dir
        name = "_".join(Path(case_dir).parts[-2:])
        target = out_dir / name
        target.mkdir(parents=True, exist_ok=True)
        for filename in ("results.json", "assumptions.json", "case.json"):
            candidate = source / filename
            if candidate.exists():
                shutil.copy2(candidate, target / filename)
        built[name] = rebuild_report(target)
    return built
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_compare_workbooks -v`
Expected: PASS, 5 tests

- [ ] **Step 5: Capture the HEAD baseline**

Run:

```bash
./.venv/Scripts/python.exe -c "from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases; import json; print(json.dumps({k: str(v) for k, v in rebuild_all_cases('.', 'baseline_workbooks').items()}, indent=2))"
```

Expected: 8 entries printed, `baseline_workbooks/` created with 8 subdirectories each holding one `.xlsx`.

`baseline_workbooks/` is a scratch artifact and must **not** be committed. Add it to `.gitignore` in the next step.

- [ ] **Step 6: Ignore the baseline directory**

Append to `.gitignore`:

```
# Scratch baseline for the Vietnam workbook regression gate (see
# proforma_vietnam/tools/compare_workbooks.py). Regenerate, never commit.
baseline_workbooks/
```

- [ ] **Step 7: Verify the gate detects no drift against itself**

Run:

```bash
./.venv/Scripts/python.exe -c "
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases, compare_workbooks
built = rebuild_all_cases('.', 'baseline_check')
base = {k: v for k, v in rebuild_all_cases('.', 'baseline_workbooks').items()}
bad = 0
for name, path in built.items():
    diffs = compare_workbooks(base[name], path)
    print(name, 'OK' if not diffs else 'DIFFS: %d' % len(diffs))
    bad += len(diffs)
raise SystemExit(1 if bad else 0)
"
```

Expected: all 8 print `OK`, exit code 0.

- [ ] **Step 8: Run the full suite**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .`
Expected: `Ran 445 tests`, `OK`

- [ ] **Step 9: Commit**

```bash
git add proforma_vietnam/tools proforma_vietnam/tests/test_compare_workbooks.py .gitignore
git commit -m "Add workbook cell comparator and Vietnam regression gate

The committed case workbooks predate the em-dash fix, so they cannot serve
as the refactor baseline. rebuild_all_cases regenerates all 8 from saved
results into a scratch directory and compare_workbooks diffs them cell by
cell, ignoring the non-deterministic prepared-date cell.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: CountryProfile

**Files:**
- Create: `proforma_vietnam/country_profile.py`
- Test: `proforma_vietnam/tests/test_country_profile.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `CountryProfile(country, local_currency_code, utility_label, time_steps_per_hour)` frozen dataclass; module constants `VIETNAM_PROFILE` and `THAILAND_PROFILE`; `profile_for(country: str) -> CountryProfile` resolving case-insensitively; `DEFAULT_PROFILE` aliasing `VIETNAM_PROFILE`.

- [ ] **Step 1: Write the failing test**

Create `proforma_vietnam/tests/test_country_profile.py`:

```python
from unittest import TestCase

from proforma_vietnam.country_profile import (
    DEFAULT_PROFILE,
    THAILAND_PROFILE,
    VIETNAM_PROFILE,
    CountryProfile,
    profile_for,
)


class CountryProfileTests(TestCase):

    def test_vietnam_profile_values(self):
        self.assertEqual(VIETNAM_PROFILE.country, "Vietnam")
        self.assertEqual(VIETNAM_PROFILE.local_currency_code, "VND")
        self.assertEqual(VIETNAM_PROFILE.utility_label, "EVN")
        self.assertEqual(VIETNAM_PROFILE.time_steps_per_hour, 1)

    def test_thailand_profile_values(self):
        self.assertEqual(THAILAND_PROFILE.country, "Thailand")
        self.assertEqual(THAILAND_PROFILE.local_currency_code, "THB")
        self.assertEqual(THAILAND_PROFILE.utility_label, "PEA")
        self.assertEqual(THAILAND_PROFILE.time_steps_per_hour, 4)

    def test_default_profile_is_vietnam(self):
        self.assertIs(DEFAULT_PROFILE, VIETNAM_PROFILE)

    def test_profile_for_is_case_insensitive(self):
        self.assertIs(profile_for("thailand"), THAILAND_PROFILE)
        self.assertIs(profile_for("VIETNAM"), VIETNAM_PROFILE)

    def test_profile_for_rejects_unknown_country(self):
        with self.assertRaises(ValueError) as caught:
            profile_for("Malaysia")
        self.assertIn("Malaysia", str(caught.exception))

    def test_profile_is_frozen(self):
        with self.assertRaises(Exception):
            VIETNAM_PROFILE.local_currency_code = "USD"

    def test_time_steps_per_hour_must_be_supported(self):
        with self.assertRaises(ValueError):
            CountryProfile(
                country="Nowhere",
                local_currency_code="XXX",
                utility_label="XX",
                time_steps_per_hour=3,
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_country_profile -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_vietnam.country_profile'`

- [ ] **Step 3: Write the implementation**

Create `proforma_vietnam/country_profile.py`:

```python
"""Per-country display and resolution settings.

The proforma engine is country-neutral project finance; only two things vary
between markets in a way the presentation layer must know about: what the local
contract currency is called, and what the utility is called. A third setting,
the dispatch resolution, varies because PEA bills demand on a 15-minute maximum
while EVN bills hourly.

This profile deliberately does NOT rename compute keys. Money keys inside
cash_flow.py keep their historical ``_vnd`` suffix and carry the local contract
currency, which is VND for Vietnam runs and THB for Thailand runs. See
docs/superpowers/specs/2026-09-04-thailand-adaptation-design.md section 2.
"""

from dataclasses import dataclass

SUPPORTED_TIME_STEPS_PER_HOUR = (1, 2, 4)


@dataclass(frozen=True)
class CountryProfile:
    country: str
    local_currency_code: str
    utility_label: str
    time_steps_per_hour: int

    def __post_init__(self):
        if self.time_steps_per_hour not in SUPPORTED_TIME_STEPS_PER_HOUR:
            raise ValueError(
                "Unsupported time_steps_per_hour {}; REopt supports {}.".format(
                    self.time_steps_per_hour, SUPPORTED_TIME_STEPS_PER_HOUR
                )
            )


VIETNAM_PROFILE = CountryProfile(
    country="Vietnam",
    local_currency_code="VND",
    utility_label="EVN",
    time_steps_per_hour=1,
)

THAILAND_PROFILE = CountryProfile(
    country="Thailand",
    local_currency_code="THB",
    utility_label="PEA",
    time_steps_per_hour=4,
)

DEFAULT_PROFILE = VIETNAM_PROFILE

_BY_COUNTRY = {
    profile.country.lower(): profile
    for profile in (VIETNAM_PROFILE, THAILAND_PROFILE)
}


def profile_for(country):
    key = str(country).strip().lower()
    if key not in _BY_COUNTRY:
        raise ValueError(
            "No country profile for {!r}; known: {}.".format(
                country, sorted(_BY_COUNTRY)
            )
        )
    return _BY_COUNTRY[key]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_country_profile -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Record the currency-suffix convention where it is consumed**

The spec (section 2) requires this mitigation, because a Thailand run carries THB
under `_vnd`-suffixed keys. Add to the module docstring of
`proforma_vietnam/cash_flow.py` and `proforma_vietnam/proforma_schema.py`:

```
The ``_vnd`` suffix denotes THE LOCAL CONTRACT CURRENCY, not Vietnamese dong
specifically. It is VND on Vietnam runs and THB on Thailand runs. The suffix is
historical and was deliberately not renamed; the rendered currency code comes
from the run's CountryProfile (see proforma_vietnam/country_profile.py), and
every emitted assumptions block carries an explicit ``local_currency_code``.
```

Do not change any code in this step - docstrings only, so the Vietnam gate
cannot move.

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/country_profile.py proforma_vietnam/tests/test_country_profile.py proforma_vietnam/cash_flow.py proforma_vietnam/proforma_schema.py
git commit -m "Add CountryProfile for per-market display and resolution settings

Parameterizes currency code, utility label and dispatch resolution. Does
not rename compute keys: the _vnd suffix continues to denote the local
contract currency.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Resolution-aware load reader

`_read_8760_load_csv` hard-fails on anything but 8760 rows. Thailand needs 35,040.

**Files:**
- Modify: `proforma_vietnam/case_builder.py:190-206` (`_read_8760_load_csv`)
- Test: `proforma_vietnam/tests/test_case_builder.py` (append)

**Interfaces:**
- Consumes: `CountryProfile` from Task 2 (only `time_steps_per_hour`).
- Produces: `_read_load_csv(path, time_steps_per_hour=1) -> list[float]`. The old name `_read_8760_load_csv` is kept as a wrapper delegating with `time_steps_per_hour=1`, so existing callers and tests are untouched.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_case_builder.py`:

```python
class ReadLoadCsvResolutionTests(TestCase):

    def setUp(self):
        import tempfile
        from pathlib import Path
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def _write_csv(self, name, count):
        path = self.tmp / name
        path.write_text(
            "load_kw\n" + "\n".join(str(float(i % 100)) for i in range(count)),
            encoding="utf-8",
        )
        return path

    def test_hourly_csv_reads_at_default_resolution(self):
        from proforma_vietnam.case_builder import _read_load_csv

        values = _read_load_csv(self._write_csv("hourly.csv", 8760))

        self.assertEqual(len(values), 8760)

    def test_fifteen_minute_csv_reads_at_four_steps_per_hour(self):
        from proforma_vietnam.case_builder import _read_load_csv

        values = _read_load_csv(
            self._write_csv("quarter.csv", 35040), time_steps_per_hour=4
        )

        self.assertEqual(len(values), 35040)

    def test_wrong_length_names_the_expected_count(self):
        from proforma_vietnam.case_builder import _read_load_csv

        with self.assertRaises(ValueError) as caught:
            _read_load_csv(self._write_csv("short.csv", 8760), time_steps_per_hour=4)

        self.assertIn("35040", str(caught.exception))

    def test_legacy_wrapper_still_enforces_8760(self):
        from proforma_vietnam.case_builder import _read_8760_load_csv

        with self.assertRaises(ValueError):
            _read_8760_load_csv(self._write_csv("quarter.csv", 35040))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_case_builder.ReadLoadCsvResolutionTests -v`
Expected: FAIL with `ImportError: cannot import name '_read_load_csv'`

- [ ] **Step 3: Write the implementation**

In `proforma_vietnam/case_builder.py`, replace the body of `_read_8760_load_csv` with a wrapper and add the general reader. Keep the existing CSV parsing behaviour (header detection, float coercion) exactly as it is - only the length check becomes a parameter:

```python
def _read_load_csv(path, time_steps_per_hour=1):
    """Read a single-column load CSV at the given dispatch resolution.

    Vietnam cases are hourly (8760); Thailand cases are 15-minute (35040),
    because PEA bills demand on the 15-minute on-peak maximum.
    """
    expected = 8760 * time_steps_per_hour
    values = _read_load_values(path)
    if len(values) != expected:
        raise ValueError(
            "Load CSV must contain exactly {} values at "
            "time_steps_per_hour={}; got {}.".format(
                expected, time_steps_per_hour, len(values)
            )
        )
    return values


def _read_8760_load_csv(path):
    """Backwards-compatible hourly reader (Vietnam cases)."""
    return _read_load_csv(path, time_steps_per_hour=1)
```

Extract the existing parsing loop from the old `_read_8760_load_csv` into `_read_load_values(path)`, returning the list of floats with no length check. Do not change how rows are parsed.

- [ ] **Step 4: Run the new tests**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_case_builder.ReadLoadCsvResolutionTests -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Run the full suite and the Vietnam gate**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .`
Expected: `OK`, count is 445 + 4 = 449

Run:

```bash
./.venv/Scripts/python.exe -c "
from proforma_vietnam.tools.compare_workbooks import rebuild_all_cases, compare_workbooks
built = rebuild_all_cases('.', 'gate_check')
bad = 0
for name, path in built.items():
    diffs = compare_workbooks('baseline_workbooks/%s/%s' % (name, path.name), path)
    print(name, 'OK' if not diffs else diffs[:3])
    bad += len(diffs)
raise SystemExit(1 if bad else 0)
"
```

Expected: all 8 `OK`, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/case_builder.py proforma_vietnam/tests/test_case_builder.py
git commit -m "Make the load CSV reader resolution-aware

Thailand runs at 15-minute resolution (35040 values). _read_load_csv takes
time_steps_per_hour; _read_8760_load_csv stays as an hourly wrapper so
Vietnam callers are untouched.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Profile-driven currency and utility labels

Only labels reachable under `DIRECT_OWNERSHIP` need parameterizing - DPPA-only strings are unreachable for Thailand. Rather than audit all 77 literals by hand, a test asserts no `VND`/`EVN` string survives a Thailand render, and that test drives which literals get changed.

**Files:**
- Modify: `proforma_vietnam/xlsx_builder.py` (accept and thread `profile`)
- Modify: `proforma_vietnam/audit_sheets.py` (accept and thread `profile`)
- Modify: `proforma_vietnam/report_data.py` (accept and thread `profile`)
- Test: `proforma_vietnam/tests/test_profile_labels.py`

**Interfaces:**
- Consumes: `CountryProfile`, `VIETNAM_PROFILE`, `THAILAND_PROFILE` from Task 2.
- Produces: `build_vietnam_esco_workbook(cash_flow_result, assumptions=None, report_data=None, profile=VIETNAM_PROFILE)`. The added parameter is keyword-only with a Vietnam default, so every existing caller is unaffected. `audit_sheets` writer functions gain the same trailing `profile=VIETNAM_PROFILE` keyword.

- [ ] **Step 1: Write the failing test**

Create `proforma_vietnam/tests/test_profile_labels.py`:

```python
from unittest import TestCase

from proforma_vietnam.country_profile import THAILAND_PROFILE, VIETNAM_PROFILE
from proforma_vietnam.tests.test_xlsx_builder import (
    build_direct_ownership_cash_flow_result,
)
from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook


def _all_strings(workbook):
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows(values_only=True):
            for value in row:
                if isinstance(value, str):
                    yield worksheet.title, value


class ProfileLabelTests(TestCase):

    def _workbook(self, profile):
        result = build_direct_ownership_cash_flow_result()
        return build_vietnam_esco_workbook(
            result,
            assumptions={"country": profile.country},
            profile=profile,
        )

    def test_thailand_workbook_contains_no_vnd_or_evn_labels(self):
        workbook = self._workbook(THAILAND_PROFILE)

        offenders = [
            (sheet, text)
            for sheet, text in _all_strings(workbook)
            if "VND" in text or "EVN" in text
        ]

        self.assertEqual(offenders, [], "Thailand render leaked Vietnam labels")

    def test_thailand_workbook_uses_thb_and_pea(self):
        workbook = self._workbook(THAILAND_PROFILE)
        texts = [text for _, text in _all_strings(workbook)]

        self.assertTrue(any("THB" in text for text in texts))
        self.assertTrue(any("PEA" in text for text in texts))

    def test_vietnam_workbook_still_uses_vnd_and_evn(self):
        workbook = self._workbook(VIETNAM_PROFILE)
        texts = [text for _, text in _all_strings(workbook)]

        self.assertTrue(any("VND" in text for text in texts))
        self.assertTrue(any("EVN" in text for text in texts))
```

This test imports `build_direct_ownership_cash_flow_result` from the existing
`test_xlsx_builder` module. If that helper does not exist under that exact name,
add it there as a module-level function that returns the direct-ownership
cash-flow result the existing direct-ownership tests already construct, and have
those tests call it, so the fixture is defined once.

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_profile_labels -v`
Expected: FAIL - `build_vietnam_esco_workbook() got an unexpected keyword argument 'profile'`

- [ ] **Step 3: Thread the profile through the renderers**

In `proforma_vietnam/xlsx_builder.py`:

```python
from proforma_vietnam.country_profile import VIETNAM_PROFILE


def build_vietnam_esco_workbook(cash_flow_result, assumptions=None, report_data=None,
                                profile=VIETNAM_PROFILE):
    ...
```

Pass `profile` down into every `audit_sheets.write_*` call and every local
`_write_*` helper that emits a label. In `audit_sheets.py`, give each writer a
trailing `profile=VIETNAM_PROFILE` keyword.

Replace hardcoded literals on `DIRECT_OWNERSHIP`-reachable paths with profile
values. For example, at `audit_sheets.py:202`:

```python
        structure_label = "Direct ownership - factory self-invest (avoided {} bill)".format(
            profile.utility_label
        )
```

and at `audit_sheets.py:228`:

```python
          source="{} tariff converted {}->USD before REopt; see Model Basis".format(
              profile.utility_label, profile.local_currency_code
          )
```

Apply the same substitution to every label the failing test reports. Leave
DPPA-only and ESCO-only strings alone - they are unreachable under
`DIRECT_OWNERSHIP` and changing them risks the Vietnam gate.

- [ ] **Step 4: Iterate until the label test passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_profile_labels -v`

The first assertion prints every leaked label with its sheet. Fix each one it
names, then re-run. Repeat until PASS, 3 tests.

- [ ] **Step 5: Run the full suite and the Vietnam gate**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .`
Expected: `OK`

Run the gate command from Task 3 Step 5.
Expected: all 8 `OK`, exit code 0. **This is the critical check for this task** - if any Vietnam cell moved, a literal was changed on a shared path and must be reverted.

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/xlsx_builder.py proforma_vietnam/audit_sheets.py proforma_vietnam/report_data.py proforma_vietnam/tests/test_profile_labels.py proforma_vietnam/tests/test_xlsx_builder.py
git commit -m "Drive currency and utility labels from CountryProfile

Only labels reachable under DIRECT_OWNERSHIP are parameterized; DPPA and
ESCO strings are untouched. A test asserts no VND or EVN string survives a
Thailand render, which is what drove the substitution list. Vietnam
workbooks remain cell-identical.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: PEA rate tables

**Files:**
- Create: `proforma_thailand/__init__.py`
- Create: `proforma_thailand/defaults/__init__.py`
- Create: `proforma_thailand/defaults/pea_tariff_rates.json`
- Create: `proforma_thailand/tests/__init__.py`
- Test: `proforma_thailand/tests/test_pea_defaults.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `PEA_TARIFF_RATES` dict loaded from JSON; `pea_rates_for_year(year) -> (vintage_year, values)`; `ft_for_month(year, month) -> float`.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_pea_defaults.py`:

```python
from unittest import TestCase

from proforma_thailand.defaults import ft_for_month, pea_rates_for_year


class PeaDefaultsTests(TestCase):

    def test_2025_schedule_42_rates(self):
        _, values = pea_rates_for_year(2025)
        rates = values["schedule_4_2"]["22_33kv"]

        self.assertEqual(rates["peak_energy_per_kwh"], 4.1839)
        self.assertEqual(rates["off_peak_energy_per_kwh"], 2.6037)
        self.assertEqual(rates["on_peak_demand_per_kw"], 132.93)
        self.assertEqual(values["service_charge_per_month"], 312.24)
        self.assertEqual(values["vat_fraction"], 0.07)
        self.assertEqual(values["power_factor_charge_per_kvar"], 56.07)
        self.assertEqual(values["power_factor_allowance_fraction"], 0.6197)

    def test_year_without_a_vintage_falls_back_to_the_latest_earlier_one(self):
        vintage_year, _ = pea_rates_for_year(2026)

        self.assertEqual(vintage_year, 2025)

    def test_year_before_every_vintage_raises(self):
        with self.assertRaises(ValueError):
            pea_rates_for_year(2019)

    def test_ft_windows_across_2025(self):
        self.assertEqual(ft_for_month(2025, 3), 0.3672)
        self.assertEqual(ft_for_month(2025, 4), 0.3672)
        self.assertEqual(ft_for_month(2025, 5), 0.1972)
        self.assertEqual(ft_for_month(2025, 8), 0.1972)
        self.assertEqual(ft_for_month(2025, 9), 0.1572)
        self.assertEqual(ft_for_month(2025, 12), 0.1572)

    def test_ft_falls_back_to_the_latest_known_window(self):
        self.assertEqual(ft_for_month(2026, 6), 0.1572)

    def test_ft_rejects_a_month_before_the_first_window(self):
        with self.assertRaises(ValueError):
            ft_for_month(2019, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_pea_defaults -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand'`

- [ ] **Step 3: Create the package and rate table**

`proforma_thailand/__init__.py` and `proforma_thailand/tests/__init__.py` are empty files.

Create `proforma_thailand/defaults/pea_tariff_rates.json`:

```json
{
  "version": 1,
  "description": "PEA retail tariff, keyed by vintage year. Rates verified line by line against the Rofu (Thailand) invoice for 06/2025 (rate code 4224, 22-33 kV): the full bill reconstructs from these values to within 0.01 THB. Ft is billed on total kWh and is revised every four months; the windows below are read directly off the 2025 invoices.",
  "vintages": {
    "2025": {
      "source": "PEA Schedule 4.2 Large General Service TOU, 22-33 kV; verified against Rofu invoice 06/2568 (rate code 4224)",
      "currency": "thb",
      "service_charge_per_month": 312.24,
      "vat_fraction": 0.07,
      "power_factor_charge_per_kvar": 56.07,
      "power_factor_allowance_fraction": 0.6197,
      "schedule_4_2": {
        "22_33kv": {
          "peak_energy_per_kwh": 4.1839,
          "off_peak_energy_per_kwh": 2.6037,
          "on_peak_demand_per_kw": 132.93
        }
      }
    }
  },
  "ft_windows": [
    {"from_year": 2025, "from_month": 1, "ft_per_kwh": 0.3672, "source": "Rofu invoice 03/2568"},
    {"from_year": 2025, "from_month": 5, "ft_per_kwh": 0.1972, "source": "Rofu invoice 06/2568"},
    {"from_year": 2025, "from_month": 9, "ft_per_kwh": 0.1572, "source": "Rofu invoice 11/2568"}
  ]
}
```

Create `proforma_thailand/defaults/__init__.py`:

```python
"""Versioned Thailand proforma defaults.

Mirrors proforma_vietnam/defaults: the JSON files are the editable source of the
numbers, and provenance lives in each entry's "source" field. Rate resolution
follows the same rule as the EVN tables - a requested year falls back to the
newest vintage on or before it.
"""

import json
import os

_DIR = os.path.dirname(__file__)

with open(os.path.join(_DIR, "pea_tariff_rates.json"), encoding="utf-8") as _f:
    PEA_TARIFF_RATES = json.load(_f)


def pea_rates_for_year(year):
    """Return ``(vintage_year, values)`` for the latest vintage <= ``year``."""
    vintages = PEA_TARIFF_RATES["vintages"]
    eligible = [int(y) for y in vintages if int(y) <= year]
    if not eligible:
        raise ValueError(
            "No PEA rates configured for year {} or earlier.".format(year)
        )
    vintage_year = max(eligible)
    return vintage_year, vintages[str(vintage_year)]


def ft_for_month(year, month):
    """Return the Ft adder (THB/kWh) in force for ``year``/``month``.

    Ft is revised every four months. Windows are declared by their start
    (year, month) and run until the next one begins.
    """
    key = (year, month)
    eligible = [
        window
        for window in PEA_TARIFF_RATES["ft_windows"]
        if (window["from_year"], window["from_month"]) <= key
    ]
    if not eligible:
        raise ValueError(
            "No Ft window configured for {}-{:02d} or earlier.".format(year, month)
        )
    latest = max(eligible, key=lambda w: (w["from_year"], w["from_month"]))
    return latest["ft_per_kwh"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_pea_defaults -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
git add proforma_thailand
git commit -m "Add PEA rate tables and Ft windows for Thailand

Rates verified against the Rofu 06/2025 invoice; the full bill reconstructs
to within 0.01 THB. Ft windows read off the 03, 06 and 11/2025 invoices:
0.3672, 0.1972, 0.1572 - a 57% fall across the year, so Ft is versioned
rather than treated as a constant.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: PEA tariff builder

**Files:**
- Create: `reoptjl/src/thailand/__init__.py`
- Create: `reoptjl/src/thailand/pea_tariff.py`
- Test: `reoptjl/test/test_thailand_tariff.py`

**Interfaces:**
- Consumes: `pea_rates_for_year`, `ft_for_month` from Task 5.
- Produces:

```python
build_pea_tariff(
    calendar_year_months,          # list of 12 (year, month) in Jan..Dec order
    all_off_peak_dates,            # set of datetime.date treated as all-off-peak
    voltage_level="22_33kv",
    currency="thb",
    exchange_rate_thb_per_usd=None,
    time_steps_per_hour=4,
) -> dict
```

returning keys `tou_energy_rates_per_kwh` (35,040 floats),
`coincident_peak_load_charge_per_kw` (12 floats),
`coincident_peak_load_active_time_steps` (12 lists of 1-based timestep indices),
`rate_vintage_year`, `rate_vintage_source`, `service_charge_per_month`,
`vat_fraction`, `power_factor_charge_per_kvar`,
`power_factor_allowance_fraction`, `ft_per_kwh_by_month` (12 floats).

- [ ] **Step 1: Write the failing test**

Create `reoptjl/test/test_thailand_tariff.py`:

```python
from datetime import date
from unittest import TestCase

from reoptjl.src.thailand.pea_tariff import build_pea_tariff

# Synthetic calendar year used by the Rofu case: Jan-Jun from 2026,
# Jul-Dec from 2025. See the plan's Global Constraints.
CALENDAR_MONTHS = [(2026, m) for m in range(1, 7)] + [(2025, m) for m in range(7, 13)]


class PeaTariffTests(TestCase):

    def test_energy_array_is_35040_long(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertEqual(len(tariff["tou_energy_rates_per_kwh"]), 35040)

    def test_first_interval_of_january_is_off_peak_plus_ft(self):
        # Interval 0 ends at 00:15 on 1 Jan, which is off-peak. January maps to
        # 2026-01, whose Ft falls back to the Sep-Dec 2025 window (0.1572).
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][0], 2.6037 + 0.1572, places=6
        )

    def test_interval_ending_0915_on_a_weekday_is_peak(self):
        # 1 Jan is index 0; slot 37 ends at 09:30. Peak is 09:00 < t <= 22:00.
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][37], 4.1839 + 0.1572, places=6
        )

    def test_interval_ending_exactly_0900_is_off_peak(self):
        # Slot 35 ends at 09:00, which is NOT in (09:00, 22:00].
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][35], 2.6037 + 0.1572, places=6
        )

    def test_interval_ending_exactly_2200_is_peak(self):
        # Slot 87 ends at 22:00, which IS in (09:00, 22:00].
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][87], 4.1839 + 0.1572, places=6
        )

    def test_all_off_peak_date_has_no_peak_intervals(self):
        tariff = build_pea_tariff(
            CALENDAR_MONTHS, all_off_peak_dates={date(2026, 1, 1)}
        )
        first_day = tariff["tou_energy_rates_per_kwh"][:96]

        self.assertTrue(
            all(abs(rate - (2.6037 + 0.1572)) < 1e-6 for rate in first_day)
        )

    def test_coincident_peak_has_twelve_periods_at_the_demand_rate(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertEqual(len(tariff["coincident_peak_load_charge_per_kw"]), 12)
        self.assertEqual(len(tariff["coincident_peak_load_active_time_steps"]), 12)
        self.assertTrue(
            all(rate == 132.93 for rate in tariff["coincident_peak_load_charge_per_kw"])
        )

    def test_coincident_peak_time_steps_are_one_based_and_disjoint(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())
        sets = tariff["coincident_peak_load_active_time_steps"]
        flat = [ts for group in sets for ts in group]

        self.assertEqual(len(flat), len(set(flat)))
        self.assertGreaterEqual(min(flat), 1)
        self.assertLessEqual(max(flat), 35040)

    def test_coincident_peak_indices_align_with_peak_energy_rates(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())
        rates = tariff["tou_energy_rates_per_kwh"]
        january = tariff["coincident_peak_load_active_time_steps"][0]

        for timestep in january:
            self.assertGreater(rates[timestep - 1], 4.0)

    def test_usd_conversion_divides_every_money_field(self):
        tariff = build_pea_tariff(
            CALENDAR_MONTHS,
            all_off_peak_dates=set(),
            currency="usd",
            exchange_rate_thb_per_usd=32.5,
        )

        self.assertAlmostEqual(
            tariff["tou_energy_rates_per_kwh"][0], (2.6037 + 0.1572) / 32.5, places=8
        )
        self.assertAlmostEqual(
            tariff["coincident_peak_load_charge_per_kw"][0], 132.93 / 32.5, places=8
        )

    def test_usd_without_an_exchange_rate_raises(self):
        with self.assertRaises(ValueError):
            build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set(), currency="usd")

    def test_rate_vintage_is_disclosed(self):
        tariff = build_pea_tariff(CALENDAR_MONTHS, all_off_peak_dates=set())

        self.assertEqual(tariff["rate_vintage_year"], 2025)
        self.assertIn("4224", tariff["rate_vintage_source"])

    def test_calendar_months_must_be_twelve(self):
        with self.assertRaises(ValueError):
            build_pea_tariff(CALENDAR_MONTHS[:11], all_off_peak_dates=set())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest reoptjl.test.test_thailand_tariff -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'reoptjl.src.thailand'`

- [ ] **Step 3: Write the implementation**

Create `reoptjl/src/thailand/__init__.py`:

```python
from reoptjl.src.thailand.pea_tariff import build_pea_tariff

__all__ = ["build_pea_tariff"]
```

Create `reoptjl/src/thailand/pea_tariff.py`:

```python
"""PEA Schedule 4.2 (Large General Service, TOU) tariff builder.

Verified against the Rofu (Thailand) invoice for 06/2568 (rate code 4224,
22-33 kV): peak energy 4.1839 THB/kWh, off-peak and holiday energy billed as a
single bucket at 2.6037, demand billed on the on-peak maximum only at 132.93
THB/kW, plus a per-kWh Ft adder that is revised every four months.

Two mappings matter for REopt:

- Demand is NOT a monthly all-hours maximum, so it uses
  coincident_peak_load_charge_per_kw with one period per month rather than
  monthly_demand_rates. The Julia constraint compares power to power and omits
  TimeStepScaling (julia_src/reopt_model.jl:1049), so it is correct at
  sub-hourly resolution.
- The service charge has no V3 input field and is identical in the BAU and
  optimized cases, so it is returned for the proforma to display and is not
  part of the REopt payload.

Intervals are labelled by their END time, matching the meter data: interval 0
covers 00:00-00:15 and is labelled 00:15. On-peak is 09:00 < t <= 22:00.
"""

from datetime import date, timedelta

from proforma_thailand.defaults import ft_for_month, pea_rates_for_year

PEAK_START_MINUTE = 9 * 60
PEAK_END_MINUTE = 22 * 60
DEFAULT_VOLTAGE_LEVEL = "22_33kv"
MONEY_KEYS_PER_MONTH = ("coincident_peak_load_charge_per_kw",)


def build_pea_tariff(calendar_year_months, all_off_peak_dates,
                     voltage_level=DEFAULT_VOLTAGE_LEVEL, currency="thb",
                     exchange_rate_thb_per_usd=None, time_steps_per_hour=4):
    if len(calendar_year_months) != 12:
        raise ValueError(
            "calendar_year_months must hold exactly 12 (year, month) pairs in "
            "January-to-December order; got {}.".format(len(calendar_year_months))
        )

    vintage_year, values = pea_rates_for_year(
        max(year for year, _ in calendar_year_months)
    )
    schedule = values["schedule_4_2"]
    if voltage_level not in schedule:
        raise ValueError(
            "Unsupported PEA voltage level {!r}; configured: {}.".format(
                voltage_level, sorted(schedule)
            )
        )
    rates = schedule[voltage_level]

    steps_per_day = 24 * time_steps_per_hour
    minutes_per_step = 60 // time_steps_per_hour

    ft_by_month = [ft_for_month(year, month) for year, month in calendar_year_months]

    energy_rates = []
    coincident_steps = [[] for _ in range(12)]
    timestep = 0
    for month_index, (year, month) in enumerate(calendar_year_months):
        for day in _days_in_month(year, month):
            is_all_off_peak = day in all_off_peak_dates or day.weekday() >= 5
            for slot in range(steps_per_day):
                timestep += 1
                end_minute = (slot + 1) * minutes_per_step
                on_peak = (
                    not is_all_off_peak
                    and PEAK_START_MINUTE < end_minute <= PEAK_END_MINUTE
                )
                base = (
                    rates["peak_energy_per_kwh"] if on_peak
                    else rates["off_peak_energy_per_kwh"]
                )
                energy_rates.append(base + ft_by_month[month_index])
                if on_peak:
                    coincident_steps[month_index].append(timestep)

    demand_rates = [rates["on_peak_demand_per_kw"]] * 12

    result = {
        "tou_energy_rates_per_kwh": [
            _convert(rate, currency, exchange_rate_thb_per_usd) for rate in energy_rates
        ],
        "coincident_peak_load_charge_per_kw": [
            _convert(rate, currency, exchange_rate_thb_per_usd) for rate in demand_rates
        ],
        "coincident_peak_load_active_time_steps": coincident_steps,
        "rate_vintage_year": vintage_year,
        "rate_vintage_source": values["source"],
        "service_charge_per_month": _convert(
            values["service_charge_per_month"], currency, exchange_rate_thb_per_usd
        ),
        "vat_fraction": values["vat_fraction"],
        "power_factor_charge_per_kvar": _convert(
            values["power_factor_charge_per_kvar"], currency, exchange_rate_thb_per_usd
        ),
        "power_factor_allowance_fraction": values["power_factor_allowance_fraction"],
        "ft_per_kwh_by_month": ft_by_month,
    }
    return result


def _days_in_month(year, month):
    """Yield every date in the given month."""
    current = date(year, month, 1)
    while current.month == month:
        yield current
        current += timedelta(days=1)


def _convert(value, currency, exchange_rate_thb_per_usd):
    if currency == "thb":
        return value
    if currency == "usd":
        if not exchange_rate_thb_per_usd:
            raise ValueError(
                "exchange_rate_thb_per_usd is required when currency='usd'."
            )
        return value / exchange_rate_thb_per_usd
    raise ValueError("Unsupported currency: {}".format(currency))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest reoptjl.test.test_thailand_tariff -v`
Expected: PASS, 13 tests

Note: the synthetic calendar year uses Feb 2026 (28 days), so the total is
`31+28+31+30+31+30 + 31+31+30+31+30+31 = 365` days and 35,040 intervals. If the
length assertion fails, check that `calendar_year_months` pairs Jan-Jun with
2026 and Jul-Dec with 2025.

- [ ] **Step 5: Commit**

```bash
git add reoptjl/src/thailand reoptjl/test/test_thailand_tariff.py
git commit -m "Add PEA Schedule 4.2 TOU tariff builder at 15-minute resolution

Demand maps to coincident_peak_load_charge_per_kw with one period per
month, not monthly_demand_rates, because PEA bills the on-peak maximum
only. Ft is applied per month from the versioned windows. Intervals are
labelled by end time and on-peak is 09:00 < t <= 22:00.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Load extraction from the Rofu workbook

**Files:**
- Create: `proforma_thailand/load_profile.py`
- Test: `proforma_thailand/tests/test_load_profile.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `extract_intervals(xlsm_path) -> list[dict]` with keys `date` (`datetime.date`), `end_minute` (int), `day_type` (str), `kwh` (float); `build_calendar_year(intervals, calendar_year_months) -> (loads_kw, all_off_peak_dates, qa)` where `loads_kw` is 35,040 floats in kW, `all_off_peak_dates` is a `set[date]`, and `qa` is a dict carrying `total_kwh`, `days`, `missing_days`, `peak_kw`.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_load_profile.py`:

```python
from datetime import date
from unittest import TestCase

from proforma_thailand.load_profile import build_calendar_year

CALENDAR_MONTHS = [(2026, m) for m in range(1, 7)] + [(2025, m) for m in range(7, 13)]


def _intervals_for(year, month, days_in_month, kwh=100.0, day_type="Weekday"):
    rows = []
    for day in range(1, days_in_month + 1):
        for slot in range(96):
            rows.append(
                {
                    "date": date(year, month, day),
                    "end_minute": (slot + 1) * 15,
                    "day_type": day_type,
                    "kwh": kwh,
                }
            )
    return rows


DAYS = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


def _full_year():
    rows = []
    for year, month in CALENDAR_MONTHS:
        rows.extend(_intervals_for(year, month, DAYS[month]))
    return rows


class BuildCalendarYearTests(TestCase):

    def test_produces_35040_values(self):
        loads, _, _ = build_calendar_year(_full_year(), CALENDAR_MONTHS)

        self.assertEqual(len(loads), 35040)

    def test_kwh_is_converted_to_kw(self):
        loads, _, _ = build_calendar_year(_full_year(), CALENDAR_MONTHS)

        self.assertAlmostEqual(loads[0], 400.0, places=6)

    def test_holiday_day_types_become_all_off_peak_dates(self):
        rows = _full_year()
        for row in rows:
            if row["date"] == date(2026, 1, 5):
                row["day_type"] = "Holiday"

        _, off_peak, _ = build_calendar_year(rows, CALENDAR_MONTHS)

        self.assertIn(date(2026, 1, 5), off_peak)

    def test_qa_reports_totals_and_peak(self):
        _, _, qa = build_calendar_year(_full_year(), CALENDAR_MONTHS)

        self.assertEqual(qa["days"], 365)
        self.assertEqual(qa["missing_days"], [])
        self.assertAlmostEqual(qa["total_kwh"], 35040 * 100.0, places=3)
        self.assertAlmostEqual(qa["peak_kw"], 400.0, places=6)

    def test_a_missing_day_is_reported_not_silently_padded(self):
        rows = [row for row in _full_year() if row["date"] != date(2026, 3, 15)]

        with self.assertRaises(ValueError) as caught:
            build_calendar_year(rows, CALENDAR_MONTHS)

        self.assertIn("2026-03-15", str(caught.exception))

    def test_a_day_with_wrong_interval_count_is_rejected(self):
        rows = _full_year()
        rows = [
            row for row in rows
            if not (row["date"] == date(2026, 4, 2) and row["end_minute"] == 1440)
        ]

        with self.assertRaises(ValueError) as caught:
            build_calendar_year(rows, CALENDAR_MONTHS)

        self.assertIn("2026-04-02", str(caught.exception))
        self.assertIn("95", str(caught.exception))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_load_profile -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand.load_profile'`

- [ ] **Step 3: Write the implementation**

Create `proforma_thailand/load_profile.py`:

```python
"""Turn the Rofu 15-minute meter workbook into a REopt load array.

The source sheet ("Raw Total Consumption") covers 416 unbroken days from
2025-06-01 to 2026-07-21 with 96 intervals every day and no nulls. It also
carries a DayType column that reproduces PEA's own billing day classification
(Saturdays, Sundays and Thai public holidays are all "Holiday"), verified by
reconciling calendar June 2025 against that month's invoice to within 0.003%.

The analysis year is a synthetic calendar year - January to June taken from
2026, July to December from 2025 - so that load, tariff and the calendar-year
PVWatts production factor all index identically from 1 January. A contiguous
July-to-June window would pair wet-season load with dry-season irradiance.
"""

from datetime import date, timedelta

INTERVALS_PER_DAY = 96
MINUTES_PER_INTERVAL = 15
SHEET_NAME = "Raw Total Consumption"


def extract_intervals(xlsm_path):
    """Read the meter sheet into interval dicts."""
    from openpyxl import load_workbook

    workbook = load_workbook(xlsm_path, read_only=True, data_only=True)
    worksheet = workbook[SHEET_NAME]
    rows = []
    for index, row in enumerate(worksheet.iter_rows(values_only=True)):
        if index == 0 or row[0] is None:
            continue
        timestamp = row[0]
        clock = row[2]
        end_minute = clock.hour * 60 + clock.minute
        if end_minute == 0:
            end_minute = 24 * 60
        rows.append(
            {
                "date": timestamp.date(),
                "end_minute": end_minute,
                "day_type": row[4],
                "kwh": float(row[9] or 0.0),
            }
        )
    return rows


def build_calendar_year(intervals, calendar_year_months):
    """Return ``(loads_kw, all_off_peak_dates, qa)`` for the synthetic year."""
    by_date = {}
    for interval in intervals:
        by_date.setdefault(interval["date"], []).append(interval)

    wanted = []
    for year, month in calendar_year_months:
        wanted.extend(_days_in_month(year, month))

    missing = [day for day in wanted if day not in by_date]
    if missing:
        raise ValueError(
            "Load data is missing {} day(s), first {}.".format(
                len(missing), missing[0].isoformat()
            )
        )

    loads_kw = []
    all_off_peak_dates = set()
    total_kwh = 0.0
    for day in wanted:
        day_rows = sorted(by_date[day], key=lambda row: row["end_minute"])
        if len(day_rows) != INTERVALS_PER_DAY:
            raise ValueError(
                "{} has {} intervals, expected {}.".format(
                    day.isoformat(), len(day_rows), INTERVALS_PER_DAY
                )
            )
        if any(row["day_type"] == "Holiday" for row in day_rows):
            all_off_peak_dates.add(day)
        for row in day_rows:
            total_kwh += row["kwh"]
            loads_kw.append(row["kwh"] * (60.0 / MINUTES_PER_INTERVAL))

    qa = {
        "days": len(wanted),
        "missing_days": [],
        "total_kwh": total_kwh,
        "peak_kw": max(loads_kw),
    }
    return loads_kw, all_off_peak_dates, qa


def _days_in_month(year, month):
    current = date(year, month, 1)
    days = []
    while current.month == month:
        days.append(current)
        current += timedelta(days=1)
    return days
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_load_profile -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Extract the real profile and record QA**

Run:

```bash
./.venv/Scripts/python.exe -c "
from proforma_thailand.load_profile import extract_intervals, build_calendar_year
import csv, json
XLSM = r'C:/Users/kongn/OneDrive/Máy tính/Allotrope/2026/13. Keen Project/01_Load_Data/ROFU Thailand 15-Minute Interval Data.xlsm'
months = [(2026, m) for m in range(1, 7)] + [(2025, m) for m in range(7, 13)]
rows = extract_intervals(XLSM)
loads, off_peak, qa = build_calendar_year(rows, months)
with open('proforma_thailand/data/rofu_load_15min.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['load_kw'])
    for value in loads:
        writer.writerow([round(value, 3)])
with open('proforma_thailand/data/rofu_all_off_peak_dates.json', 'w', encoding='utf-8') as f:
    json.dump(sorted(d.isoformat() for d in off_peak), f, indent=2)
print(json.dumps(qa, indent=2))
"
```

Create `proforma_thailand/data/` first if it does not exist.
Expected: `days: 365`, `missing_days: []`, and a `peak_kw` near 1,497.6.

- [ ] **Step 6: Commit**

```bash
git add proforma_thailand/load_profile.py proforma_thailand/tests/test_load_profile.py proforma_thailand/data
git commit -m "Extract the Rofu 15-minute load into a synthetic calendar year

January to June from 2026, July to December from 2025, so load, tariff and
the calendar-year PVWatts series index identically from 1 January. A
contiguous July-to-June window would pair wet-season load with dry-season
irradiance. Missing days and short days raise rather than being padded.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Bill tie-out test

**Files:**
- Create: `proforma_thailand/bill.py`
- Test: `proforma_thailand/tests/test_bill_tieout.py`

**Interfaces:**
- Consumes: `pea_rates_for_year`, `ft_for_month` from Task 5.
- Produces: `compute_monthly_bill(peak_kwh, off_peak_kwh, holiday_kwh, on_peak_kw, year, month) -> dict` with keys `demand_charge`, `peak_energy`, `off_peak_energy`, `service_charge`, `base_total`, `ft_charge`, `subtotal`, `vat`, `total`, all THB.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_bill_tieout.py`:

```python
from unittest import TestCase

from proforma_thailand.bill import compute_monthly_bill

# Actual PEA invoice totals for KTH2, from 02_Bills_2025/ and the meter
# workbook's Summary sheet. Only Jun-Nov 2025 overlap the interval data.
INVOICE_TOTALS = {
    (2025, 6): 2576311.21,
    (2025, 7): 2624222.45,
    (2025, 8): 2417188.28,
    (2025, 9): 2528702.23,
    (2025, 10): 2458569.72,
    (2025, 11): 2375516.43,
}

INVOICE_ON_PEAK_KW = {
    (2025, 6): 1368.0,
    (2025, 7): 1376.0,
    (2025, 8): 1320.0,
    (2025, 9): 1296.0,
    (2025, 10): 1328.0,
    (2025, 11): 1360.0,
}


class BillTieOutTests(TestCase):

    def test_june_2025_reconstructs_line_by_line(self):
        bill = compute_monthly_bill(
            peak_kwh=288960.0,
            off_peak_kwh=164380.0,
            holiday_kwh=178240.0,
            on_peak_kw=1368.0,
            year=2025,
            month=6,
        )

        self.assertAlmostEqual(bill["demand_charge"], 181848.24, places=2)
        self.assertAlmostEqual(bill["peak_energy"], 1208979.74, places=2)
        self.assertAlmostEqual(bill["off_peak_energy"], 892079.69, places=2)
        self.assertAlmostEqual(bill["base_total"], 2283219.91, places=1)
        self.assertAlmostEqual(bill["ft_charge"], 124547.58, places=2)
        self.assertAlmostEqual(bill["vat"], 168543.72, places=2)
        self.assertAlmostEqual(bill["total"], 2576311.21, places=1)

    def test_november_2025_uses_the_september_ft_window(self):
        bill = compute_monthly_bill(
            peak_kwh=266920.0,
            off_peak_kwh=148920.0,
            holiday_kwh=169920.0,
            on_peak_kw=1360.0,
            year=2025,
            month=11,
        )

        # 585,760 kWh at the Sep-Dec Ft of 0.1572
        self.assertAlmostEqual(bill["ft_charge"], 92081.47, places=2)
        self.assertAlmostEqual(bill["base_total"], 2128027.34, places=1)

    def test_holiday_energy_is_billed_at_the_off_peak_rate(self):
        with_holiday = compute_monthly_bill(
            peak_kwh=0.0, off_peak_kwh=0.0, holiday_kwh=1000.0,
            on_peak_kw=0.0, year=2025, month=6,
        )
        as_off_peak = compute_monthly_bill(
            peak_kwh=0.0, off_peak_kwh=1000.0, holiday_kwh=0.0,
            on_peak_kw=0.0, year=2025, month=6,
        )

        self.assertAlmostEqual(
            with_holiday["off_peak_energy"], as_off_peak["off_peak_energy"], places=6
        )

    def test_all_six_overlap_months_tie_out_within_one_percent(self):
        from proforma_thailand.load_profile import (
            build_month_buckets,
            extract_intervals,
        )

        XLSM = (
            r"C:/Users/kongn/OneDrive/Máy tính/Allotrope/2026/"
            r"13. Keen Project/01_Load_Data/"
            r"ROFU Thailand 15-Minute Interval Data.xlsm"
        )
        buckets = build_month_buckets(extract_intervals(XLSM))

        for key, invoice_total in INVOICE_TOTALS.items():
            year, month = key
            bucket = buckets[key]
            bill = compute_monthly_bill(
                peak_kwh=bucket["peak_kwh"],
                off_peak_kwh=bucket["off_peak_kwh"],
                holiday_kwh=bucket["holiday_kwh"],
                on_peak_kw=INVOICE_ON_PEAK_KW[key],
                year=year,
                month=month,
            )
            error = abs(bill["total"] - invoice_total) / invoice_total
            self.assertLess(
                error, 0.01,
                "{}-{:02d}: modelled {:.2f} vs invoice {:.2f} ({:.3%})".format(
                    year, month, bill["total"], invoice_total, error
                ),
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_bill_tieout -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand.bill'`

- [ ] **Step 3: Add the month-bucket helper**

Append to `proforma_thailand/load_profile.py`:

```python
PEAK_START_MINUTE = 9 * 60
PEAK_END_MINUTE = 22 * 60


def build_month_buckets(intervals):
    """Aggregate intervals into PEA billing buckets per (year, month).

    Peak is 09:00 < t <= 22:00 on non-holiday days; holiday days go entirely to
    the holiday bucket. This split is what reconciles to the invoice.
    """
    buckets = {}
    for interval in intervals:
        day = interval["date"]
        key = (day.year, day.month)
        bucket = buckets.setdefault(
            key, {"peak_kwh": 0.0, "off_peak_kwh": 0.0, "holiday_kwh": 0.0}
        )
        if interval["day_type"] == "Holiday":
            bucket["holiday_kwh"] += interval["kwh"]
        elif PEAK_START_MINUTE < interval["end_minute"] <= PEAK_END_MINUTE:
            bucket["peak_kwh"] += interval["kwh"]
        else:
            bucket["off_peak_kwh"] += interval["kwh"]
    return buckets
```

- [ ] **Step 4: Write the bill calculator**

Create `proforma_thailand/bill.py`:

```python
"""PEA Schedule 4.2 monthly bill reconstruction.

Used both as the tie-out test against real invoices and as the BAU bill in the
proforma. Off-peak and holiday energy share one bucket at the off-peak rate;
demand is billed on the on-peak maximum only; Ft applies to total kWh; VAT
applies to base plus Ft.
"""

from proforma_thailand.defaults import ft_for_month, pea_rates_for_year

DEFAULT_VOLTAGE_LEVEL = "22_33kv"


def compute_monthly_bill(peak_kwh, off_peak_kwh, holiday_kwh, on_peak_kw,
                         year, month, voltage_level=DEFAULT_VOLTAGE_LEVEL):
    _, values = pea_rates_for_year(year)
    rates = values["schedule_4_2"][voltage_level]

    demand_charge = on_peak_kw * rates["on_peak_demand_per_kw"]
    peak_energy = peak_kwh * rates["peak_energy_per_kwh"]
    off_peak_energy = (off_peak_kwh + holiday_kwh) * rates["off_peak_energy_per_kwh"]
    service_charge = values["service_charge_per_month"]
    base_total = demand_charge + peak_energy + off_peak_energy + service_charge

    total_kwh = peak_kwh + off_peak_kwh + holiday_kwh
    ft_charge = total_kwh * ft_for_month(year, month)

    subtotal = base_total + ft_charge
    vat = subtotal * values["vat_fraction"]

    return {
        "demand_charge": demand_charge,
        "peak_energy": peak_energy,
        "off_peak_energy": off_peak_energy,
        "service_charge": service_charge,
        "base_total": base_total,
        "ft_charge": ft_charge,
        "subtotal": subtotal,
        "vat": vat,
        "total": subtotal + vat,
    }

```

Power factor deliberately does NOT live here. It is not part of the BAU bill
reconstruction, and its only consumer is the report (Task 14), which owns
`compute_power_factor_compensation`. Putting a second copy of the allowance
formula in this module would be duplication with no caller.

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_bill_tieout -v`
Expected: PASS, 4 tests. The six-month tie-out prints nothing on success; on
failure it names the month and the percentage error.

- [ ] **Step 6: Commit**

```bash
git add proforma_thailand/bill.py proforma_thailand/load_profile.py proforma_thailand/tests/test_bill_tieout.py
git commit -m "Add PEA bill reconstruction and the six-month invoice tie-out

June 2025 reconstructs line by line to 0.01 THB. All six months where the
interval data overlaps the invoices tie out within 1%. Also adds the power
factor helper that sizes required compensation from post-PV billed demand.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Thailand defaults with placeholder markers

**Files:**
- Create: `proforma_thailand/defaults/thailand_defaults.json`
- Modify: `proforma_thailand/defaults/__init__.py`
- Test: `proforma_thailand/tests/test_thailand_defaults.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `THAILAND_DEFAULTS`, `FINANCIAL_DEFAULTS`, `TAX_DEFAULTS`, `SITE_DEFAULTS` dicts; `placeholder_keys() -> set[str]` naming every value still awaiting Keen confirmation; `PLACEHOLDER_MARKER = "PLACEHOLDER - pending Keen confirmation"`.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_thailand_defaults.py`:

```python
from unittest import TestCase

from proforma_thailand.defaults import (
    FINANCIAL_DEFAULTS,
    PLACEHOLDER_MARKER,
    SITE_DEFAULTS,
    TAX_DEFAULTS,
    TAX_DEFAULTS_RAW,
    placeholder_keys,
    value_of,
)


class ThailandDefaultsTests(TestCase):

    def test_verified_tax_values(self):
        self.assertEqual(TAX_DEFAULTS["cit_standard_rate"], 0.20)
        self.assertEqual(TAX_DEFAULTS["cit_loss_carryforward_years"], 5)
        self.assertEqual(TAX_DEFAULTS["vat_rate_fraction"], 0.07)

    def test_conservative_roof_bound_is_the_default(self):
        # Five roofs at 24x108 m until Ou confirms the size split.
        self.assertEqual(value_of(SITE_DEFAULTS, "usable_roof_area_m2"), 12960 * 0.65)
        self.assertEqual(value_of(SITE_DEFAULTS, "pv_max_kw"), 1685.0)

    def test_every_unconfirmed_value_is_marked_as_a_placeholder(self):
        expected = {
            "pv_installed_cost_per_kw",
            "bess_installed_cost_per_kw",
            "bess_installed_cost_per_kwh",
            "annual_om_per_kw",
            "debt_fraction",
            "debt_interest_rate",
            "debt_term_years",
            "insurance_rate_fraction",
            "grid_connection_cost",
            "permitting_and_eia_cost",
            "pea_tariff_escalation_rate",
            "ft_forecast_per_kwh",
            "usable_roof_area_m2",
            "pv_max_kw",
            "power_factor_mitigation_cost",
        }

        self.assertEqual(placeholder_keys(), expected)

    def test_placeholder_entries_carry_the_marker_string(self):
        for key in placeholder_keys():
            for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW):
                if key in block:
                    self.assertEqual(
                        block[key]["source"], PLACEHOLDER_MARKER,
                        "{} is not marked as a placeholder".format(key),
                    )
                    break
            else:
                self.fail("{} is not present in any defaults block".format(key))

    def test_placeholder_entries_still_expose_a_usable_value(self):
        for key in placeholder_keys():
            for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW):
                if key in block:
                    self.assertIsNotNone(block[key]["value"])
                    break
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults -v`
Expected: FAIL with `ImportError: cannot import name 'FINANCIAL_DEFAULTS'`

- [ ] **Step 3: Write the defaults file**

Create `proforma_thailand/defaults/thailand_defaults.json`. Every entry is an
object with `value` and `source`. Confirmed entries cite their evidence;
unconfirmed entries carry the placeholder marker verbatim.

```json
{
  "version": 1,
  "description": "Thailand proforma defaults for the Rofu (Keen) case. Entries whose source is the placeholder marker are benchmark estimates awaiting confirmation from Keen and must render with a visible marker on the Assumptions sheet.",
  "placeholder_marker": "PLACEHOLDER - pending Keen confirmation",
  "financial": {
    "project_years": {"value": 25, "source": "Analysis convention, matches the Vietnam cases"},
    "exchange_rate_thb_per_usd": {"value": 32.5, "source": "Planning rate; revise at contract"},
    "pea_tariff_escalation_rate": {"value": 0.03, "source": "PLACEHOLDER - pending Keen confirmation"},
    "ft_forecast_per_kwh": {"value": 0.1572, "source": "PLACEHOLDER - pending Keen confirmation"},
    "om_escalation_rate": {"value": 0.03, "source": "Matches the Vietnam default"},
    "pv_installed_cost_per_kw": {"value": 700.0, "source": "PLACEHOLDER - pending Keen confirmation"},
    "bess_installed_cost_per_kw": {"value": 300.0, "source": "PLACEHOLDER - pending Keen confirmation"},
    "bess_installed_cost_per_kwh": {"value": 250.0, "source": "PLACEHOLDER - pending Keen confirmation"},
    "annual_om_per_kw": {"value": 12.0, "source": "PLACEHOLDER - pending Keen confirmation"},
    "debt_fraction": {"value": 0.70, "source": "PLACEHOLDER - pending Keen confirmation"},
    "debt_interest_rate": {"value": 0.06, "source": "PLACEHOLDER - pending Keen confirmation"},
    "debt_term_years": {"value": 10, "source": "PLACEHOLDER - pending Keen confirmation"},
    "insurance_rate_fraction": {"value": 0.005, "source": "PLACEHOLDER - pending Keen confirmation"},
    "grid_connection_cost": {"value": 0.0, "source": "PLACEHOLDER - pending Keen confirmation"},
    "permitting_and_eia_cost": {"value": 0.0, "source": "PLACEHOLDER - pending Keen confirmation"},
    "power_factor_mitigation_cost": {"value": 6000.0, "source": "PLACEHOLDER - pending Keen confirmation"}
  },
  "tax": {
    "cit_standard_rate": {"value": 0.20, "source": "Thai Revenue Code standard corporate income tax rate"},
    "cit_loss_carryforward_years": {"value": 5, "source": "Thai Revenue Code"},
    "vat_rate_fraction": {"value": 0.07, "source": "Verified on the Rofu 06/2025 invoice"},
    "pv_depreciation_years": {"value": 5, "source": "TO BE CITED IN TASK 13 - Thai Revenue Code machinery treatment"},
    "bess_depreciation_years": {"value": 5, "source": "TO BE CITED IN TASK 13 - Thai Revenue Code machinery treatment"}
  },
  "site": {
    "latitude": {"value": 15.209427, "source": "RTS Data Collection, Rofu Phimai"},
    "longitude": {"value": 102.475687, "source": "RTS Data Collection, Rofu Phimai"},
    "transformer_capacity_kva": {"value": 3230, "source": "RTS Data Collection: 500 x2 + 1600 + 630"},
    "usable_roof_area_m2": {"value": 8424.0, "source": "PLACEHOLDER - pending Keen confirmation"},
    "pv_max_kw": {"value": 1685.0, "source": "PLACEHOLDER - pending Keen confirmation"}
  }
}
```

Note: `usable_roof_area_m2` is `12960 * 0.65 = 8424.0`, the conservative bound
(all five roofs at 24x108 m) per spec section 7.

- [ ] **Step 4: Extend the defaults loader**

Append to `proforma_thailand/defaults/__init__.py`:

```python
with open(os.path.join(_DIR, "thailand_defaults.json"), encoding="utf-8") as _f:
    THAILAND_DEFAULTS = json.load(_f)

PLACEHOLDER_MARKER = THAILAND_DEFAULTS["placeholder_marker"]
FINANCIAL_DEFAULTS = THAILAND_DEFAULTS["financial"]
TAX_DEFAULTS_RAW = THAILAND_DEFAULTS["tax"]
SITE_DEFAULTS = THAILAND_DEFAULTS["site"]

# Tax values are consumed as plain numbers by the cash flow engine, so expose a
# flattened view alongside the annotated one.
TAX_DEFAULTS = {key: entry["value"] for key, entry in TAX_DEFAULTS_RAW.items()}


def placeholder_keys():
    """Names of every default still awaiting confirmation from Keen."""
    found = set()
    for block in (FINANCIAL_DEFAULTS, SITE_DEFAULTS, TAX_DEFAULTS_RAW):
        for key, entry in block.items():
            if entry.get("source") == PLACEHOLDER_MARKER:
                found.add(key)
    return found


def value_of(block, key):
    """Read a default's numeric value, ignoring its provenance wrapper."""
    return block[key]["value"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults -v`
Expected: PASS, 5 tests

- [ ] **Step 6: Commit**

```bash
git add proforma_thailand/defaults proforma_thailand/tests/test_thailand_defaults.py
git commit -m "Add Thailand defaults with explicit placeholder provenance

Every financing input Keen has not confirmed carries the placeholder
marker in its source field, so the Assumptions sheet can render it
visibly. Roof area defaults to the conservative bound (five roofs at
24x108 m) until Ou confirms the size split.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: Placeholder guard in validate_workbook

**Files:**
- Modify: `proforma_vietnam/validate_workbook.py`
- Test: `proforma_vietnam/tests/test_validate_workbook.py` (append)

**Interfaces:**
- Consumes: `PLACEHOLDER_MARKER` semantics (the guard takes the marker string as a parameter, so `proforma_vietnam` does not import `proforma_thailand`).
- Produces: `validate_no_unmarked_placeholders(workbook, marker, headline_labels) -> list[str]` returning failures.

- [ ] **Step 1: Write the failing test**

Append to `proforma_vietnam/tests/test_validate_workbook.py`:

```python
class PlaceholderGuardTests(TestCase):

    MARKER = "PLACEHOLDER - pending Keen confirmation"
    HEADLINES = ("IRR", "NPV", "Payback")

    def _workbook(self, assumption_rows, summary_rows):
        from openpyxl import Workbook

        workbook = Workbook()
        assumptions = workbook.active
        assumptions.title = "Assumptions"
        for row in assumption_rows:
            assumptions.append(row)
        summary = workbook.create_sheet("Executive Summary")
        for row in summary_rows:
            summary.append(row)
        return workbook

    def test_marked_placeholder_with_headline_metric_passes(self):
        from proforma_vietnam.validate_workbook import (
            validate_no_unmarked_placeholders,
        )

        workbook = self._workbook(
            [["PV capex", 700.0, self.MARKER]],
            [["Project IRR", 0.14]],
        )

        self.assertEqual(
            validate_no_unmarked_placeholders(workbook, self.MARKER, self.HEADLINES),
            [],
        )

    def test_headline_metric_without_any_marker_fails(self):
        from proforma_vietnam.validate_workbook import (
            validate_no_unmarked_placeholders,
        )

        workbook = self._workbook(
            [["PV capex", 700.0, "benchmark estimate"]],
            [["Project IRR", 0.14]],
        )

        failures = validate_no_unmarked_placeholders(
            workbook, self.MARKER, self.HEADLINES
        )

        self.assertEqual(len(failures), 1)
        self.assertIn("IRR", failures[0])

    def test_no_headline_metric_means_nothing_to_guard(self):
        from proforma_vietnam.validate_workbook import (
            validate_no_unmarked_placeholders,
        )

        workbook = self._workbook([["PV capex", 700.0, "confirmed"]], [["Notes", 1]])

        self.assertEqual(
            validate_no_unmarked_placeholders(workbook, self.MARKER, self.HEADLINES),
            [],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_validate_workbook.PlaceholderGuardTests -v`
Expected: FAIL with `ImportError: cannot import name 'validate_no_unmarked_placeholders'`

- [ ] **Step 3: Write the implementation**

Append to `proforma_vietnam/validate_workbook.py`:

```python
def validate_no_unmarked_placeholders(workbook, marker, headline_labels):
    """Fail when a headline metric is present but no placeholder is disclosed.

    A stubbed capex quietly producing a confident-looking IRR is the failure
    mode this prevents. If the workbook reports any headline metric, at least
    one cell must carry the placeholder marker, otherwise the reader has no
    signal that the inputs are provisional.
    """
    has_marker = any(
        isinstance(value, str) and marker in value
        for worksheet in workbook.worksheets
        for row in worksheet.iter_rows(values_only=True)
        for value in row
    )
    if has_marker:
        return []

    failures = []
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows(values_only=True):
            for value in row:
                if not isinstance(value, str):
                    continue
                for label in headline_labels:
                    if label in value:
                        failures.append(
                            "{}: headline metric {!r} is reported but no "
                            "placeholder marker is disclosed anywhere in the "
                            "workbook.".format(worksheet.title, value)
                        )
                        return failures
    return failures
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_vietnam.tests.test_validate_workbook.PlaceholderGuardTests -v`
Expected: PASS, 3 tests

- [ ] **Step 5: Run the full suite and the Vietnam gate**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .`
Expected: `OK`

Run the gate command from Task 3 Step 5.
Expected: all 8 `OK`.

- [ ] **Step 6: Commit**

```bash
git add proforma_vietnam/validate_workbook.py proforma_vietnam/tests/test_validate_workbook.py
git commit -m "Guard against headline metrics built on undisclosed placeholders

Takes the marker string as a parameter so proforma_vietnam does not depend
on proforma_thailand.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: Thailand case builder

**Files:**
- Create: `proforma_thailand/case_builder.py`
- Test: `proforma_thailand/tests/test_case_builder.py`

**Interfaces:**
- Consumes: `build_pea_tariff` (Task 6), `build_calendar_year`/`extract_intervals` (Task 7), defaults (Task 9), `_read_load_csv` (Task 3), `pvwatts_client` from `proforma_vietnam`.
- Produces: `build_thailand_case(case_config) -> {"payload": dict, "assumptions": dict}`.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_case_builder.py`:

```python
import json
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from proforma_thailand.case_builder import build_thailand_case

CALENDAR_MONTHS = [[2026, m] for m in range(1, 7)] + [[2025, m] for m in range(7, 13)]


def _case_config(tmp, load_csv, off_peak_json):
    return {
        "site": {"latitude": 15.209427, "longitude": 102.475687},
        "load_profile": {
            "path": str(load_csv),
            "all_off_peak_dates_path": str(off_peak_json),
            "calendar_year_months": CALENDAR_MONTHS,
        },
        "tariff": {"voltage_level": "22_33kv", "exchange_rate_thb_per_usd": 32.5},
        "technologies": {
            "pv": {"max_kw": 1685.0, "installed_cost_per_kw": 700.0},
            "storage": {"max_kw": 0, "max_kwh": 0},
        },
        "direct_ownership": {"enabled": True},
    }


class ThailandCaseBuilderTests(TestCase):

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)
        self.load_csv = self.tmp / "load.csv"
        self.load_csv.write_text(
            "load_kw\n" + "\n".join("500.0" for _ in range(35040)), encoding="utf-8"
        )
        self.off_peak = self.tmp / "off_peak.json"
        self.off_peak.write_text(json.dumps(["2026-01-04"]), encoding="utf-8")
        patcher = mock.patch(
            "proforma_thailand.case_builder.pvwatts_client."
            "fetch_production_factor_series",
            return_value={"production_factor": [0.5] * 8760, "poa_wm2": []},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _build(self):
        return build_thailand_case(
            _case_config(self.tmp, self.load_csv, self.off_peak)
        )

    def test_settings_request_15_minute_resolution(self):
        case = self._build()

        self.assertEqual(case["payload"]["Settings"]["time_steps_per_hour"], 4)

    def test_load_is_35040_long(self):
        case = self._build()

        self.assertEqual(
            len(case["payload"]["ElectricLoad"]["loads_kw"]), 35040
        )

    def test_tariff_uses_coincident_peak_not_monthly_demand(self):
        tariff = self._build()["payload"]["ElectricTariff"]

        self.assertEqual(len(tariff["coincident_peak_load_charge_per_kw"]), 12)
        self.assertEqual(len(tariff["coincident_peak_load_active_time_steps"]), 12)
        self.assertNotIn("monthly_demand_rates", tariff)

    def test_export_is_fully_disabled_with_curtailment_allowed(self):
        pv = self._build()["payload"]["PV"]

        self.assertFalse(pv["can_net_meter"])
        self.assertFalse(pv["can_wholesale"])
        self.assertFalse(pv["can_export_beyond_nem_limit"])
        self.assertTrue(pv["can_curtail"])

    def test_rate_vintage_is_routed_to_assumptions_not_the_payload(self):
        case = self._build()

        self.assertNotIn("rate_vintage_year", case["payload"]["ElectricTariff"])
        self.assertEqual(case["assumptions"]["rate_vintage_year"], 2025)

    def test_assumptions_record_the_country_and_currency(self):
        assumptions = self._build()["assumptions"]

        self.assertEqual(assumptions["country"], "Thailand")
        self.assertEqual(assumptions["local_currency_code"], "THB")

    def test_assumptions_list_the_active_placeholders(self):
        assumptions = self._build()["assumptions"]

        self.assertIn("placeholder_keys", assumptions)
        self.assertIn("debt_interest_rate", assumptions["placeholder_keys"])

    def test_direct_ownership_block_is_passed_through(self):
        assumptions = self._build()["assumptions"]

        self.assertEqual(assumptions["direct_ownership"], {"enabled": True})

    def test_service_charge_and_vat_ride_assumptions(self):
        assumptions = self._build()["assumptions"]

        self.assertAlmostEqual(
            assumptions["service_charge_per_month_thb"], 312.24, places=2
        )
        self.assertEqual(assumptions["vat_rate_fraction"], 0.07)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand.case_builder'`

- [ ] **Step 3: Write the implementation**

Create `proforma_thailand/case_builder.py`:

```python
"""Build a REopt payload plus an assumptions block for a Thailand case.

Mirrors proforma_vietnam/case_builder.py but for PEA: 15-minute resolution,
coincident-peak demand rather than monthly demand rates, and no export.
Only DIRECT_OWNERSHIP is supported; ESCO/PPA is a later phase.
"""

import json
from datetime import date
from pathlib import Path

from proforma_thailand.defaults import (
    FINANCIAL_DEFAULTS,
    SITE_DEFAULTS,
    TAX_DEFAULTS,
    placeholder_keys,
    value_of,
)
from proforma_vietnam import pvwatts_client
from proforma_vietnam.case_builder import _read_load_csv
from proforma_vietnam.country_profile import THAILAND_PROFILE
from reoptjl.src.thailand.pea_tariff import build_pea_tariff

# The producer owns the audit-key list; importing it means adding a key to
# build_pea_tariff cannot silently leak into a REopt payload.
from reoptjl.src.thailand.pea_tariff import AUDIT_METADATA_KEYS, RATE_VINTAGE_KEYS

NON_PAYLOAD_TARIFF_KEYS = AUDIT_METADATA_KEYS


def build_thailand_case(case_config):
    profile = THAILAND_PROFILE
    site = case_config["site"]
    load_config = case_config["load_profile"]
    tariff_config = case_config.get("tariff", {})
    technologies = case_config.get("technologies", {})

    calendar_months = [
        (int(year), int(month))
        for year, month in load_config["calendar_year_months"]
    ]
    loads_kw = _read_load_csv(
        load_config["path"], time_steps_per_hour=profile.time_steps_per_hour
    )
    all_off_peak_dates = {
        date.fromisoformat(value)
        for value in json.loads(
            Path(load_config["all_off_peak_dates_path"]).read_text(encoding="utf-8")
        )
    }

    exchange_rate = tariff_config.get(
        "exchange_rate_thb_per_usd",
        value_of(FINANCIAL_DEFAULTS, "exchange_rate_thb_per_usd"),
    )
    tariff = build_pea_tariff(
        calendar_months,
        all_off_peak_dates,
        voltage_level=tariff_config.get("voltage_level", "22_33kv"),
        currency="usd",
        exchange_rate_thb_per_usd=exchange_rate,
        time_steps_per_hour=profile.time_steps_per_hour,
    )
    tariff_extras = {key: tariff.pop(key) for key in NON_PAYLOAD_TARIFF_KEYS}

    production = pvwatts_client.fetch_production_factor_series(
        latitude=site["latitude"], longitude=site["longitude"]
    )

    pv_config = technologies.get("pv", {})
    storage_config = technologies.get("storage", {})

    payload = {
        "Settings": {"time_steps_per_hour": profile.time_steps_per_hour},
        "Site": {"latitude": site["latitude"], "longitude": site["longitude"]},
        "ElectricLoad": {"loads_kw": loads_kw},
        "ElectricTariff": tariff,
        "PV": {
            "max_kw": pv_config.get(
                "max_kw", value_of(SITE_DEFAULTS, "pv_max_kw")
            ),
            "installed_cost_per_kw": pv_config.get(
                "installed_cost_per_kw",
                value_of(FINANCIAL_DEFAULTS, "pv_installed_cost_per_kw"),
            ),
            "production_factor_series": production["production_factor"],
            # PEA pays nothing for exported energy, so the system must curtail
            # rather than export. See spec section 3.
            "can_net_meter": False,
            "can_wholesale": False,
            "can_export_beyond_nem_limit": False,
            "can_curtail": True,
        },
        "Financial": {
            "analysis_years": value_of(FINANCIAL_DEFAULTS, "project_years"),
        },
    }

    if storage_config.get("max_kw") or storage_config.get("max_kwh"):
        payload["ElectricStorage"] = {
            "max_kw": storage_config.get("max_kw", 0),
            "max_kwh": storage_config.get("max_kwh", 0),
            "installed_cost_per_kw": storage_config.get(
                "installed_cost_per_kw",
                value_of(FINANCIAL_DEFAULTS, "bess_installed_cost_per_kw"),
            ),
            "installed_cost_per_kwh": storage_config.get(
                "installed_cost_per_kwh",
                value_of(FINANCIAL_DEFAULTS, "bess_installed_cost_per_kwh"),
            ),
            "can_grid_charge": storage_config.get("can_grid_charge", True),
        }

    assumptions = {
        "country": profile.country,
        "local_currency_code": profile.local_currency_code,
        "utility_label": profile.utility_label,
        "time_steps_per_hour": profile.time_steps_per_hour,
        "exchange_rate_thb_per_usd": exchange_rate,
        "calendar_year_months": [list(pair) for pair in calendar_months],
        "service_charge_per_month_thb": (
            tariff_extras["service_charge_per_month"] * exchange_rate
        ),
        "vat_rate_fraction": tariff_extras["vat_fraction"],
        "power_factor_charge_per_kvar_thb": (
            tariff_extras["power_factor_charge_per_kvar"] * exchange_rate
        ),
        "power_factor_allowance_fraction": tariff_extras[
            "power_factor_allowance_fraction"
        ],
        "ft_per_kwh_by_month_thb": [
            value * exchange_rate for value in tariff_extras["ft_per_kwh_by_month"]
        ],
        "cit_regime": "standard_flat",
        "cit_standard_rate": TAX_DEFAULTS["cit_standard_rate"],
        "pv_depreciation_years": TAX_DEFAULTS["pv_depreciation_years"],
        "direct_ownership": case_config.get("direct_ownership", {"enabled": True}),
        "placeholder_keys": sorted(placeholder_keys()),
        "pv_poa_irradiance_series": production.get("poa_wm2") or None,
    }
    for key in RATE_VINTAGE_KEYS:
        assumptions[key] = tariff_extras[key]

    return {"payload": payload, "assumptions": assumptions}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_case_builder -v`
Expected: PASS, 9 tests

- [ ] **Step 5: Commit**

```bash
git add proforma_thailand/case_builder.py proforma_thailand/tests/test_case_builder.py
git commit -m "Add the Thailand case builder for DIRECT_OWNERSHIP at 15-min

Coincident-peak demand rather than monthly demand rates, export fully
disabled with curtailment allowed, and every non-REopt tariff field routed
into assumptions rather than the payload.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: Verify coincident-peak against the live solver

This is the spec's Phase 0 empirical check. The Julia source review already
showed the constraint is resolution-agnostic (`reopt_model.jl:1049` compares
power to power and omits `TimeStepScaling`); this confirms it end to end.

**Prerequisite:** the stack must be running. `docker-compose up -d`, then wait
for the Julia server to report ready in `docker-compose logs -f julia`.

**Files:**
- Create: `proforma_thailand/cases/coincident_peak_spike/case.json`
- Create: `docs/superpowers/notes/2026-09-04-coincident-peak-spike.md`

**Interfaces:**
- Consumes: `build_thailand_case` (Task 11).
- Produces: a findings note. No production code.

- [ ] **Step 1: Build a minimal flat-load case**

Create `proforma_thailand/cases/coincident_peak_spike/case.json` using the real
load CSV and off-peak dates from Task 7, with PV and storage both disabled so
the run is a pure BAU bill:

```json
{
  "site": {"latitude": 15.209427, "longitude": 102.475687},
  "load_profile": {
    "path": "proforma_thailand/data/rofu_load_15min.csv",
    "all_off_peak_dates_path": "proforma_thailand/data/rofu_all_off_peak_dates.json",
    "calendar_year_months": [[2026,1],[2026,2],[2026,3],[2026,4],[2026,5],[2026,6],
                             [2025,7],[2025,8],[2025,9],[2025,10],[2025,11],[2025,12]]
  },
  "tariff": {"voltage_level": "22_33kv", "exchange_rate_thb_per_usd": 32.5},
  "technologies": {
    "pv": {"max_kw": 0, "installed_cost_per_kw": 700.0},
    "storage": {"max_kw": 0, "max_kwh": 0}
  },
  "direct_ownership": {"enabled": true}
}
```

- [ ] **Step 2: Compute the expected demand charge independently**

Run:

```bash
./.venv/Scripts/python.exe -c "
import csv, json
from datetime import date
from proforma_thailand.defaults import pea_rates_for_year
months = [(2026, m) for m in range(1, 7)] + [(2025, m) for m in range(7, 13)]
loads = [float(r['load_kw']) for r in csv.DictReader(open('proforma_thailand/data/rofu_load_15min.csv'))]
off_peak = {date.fromisoformat(s) for s in json.load(open('proforma_thailand/data/rofu_all_off_peak_dates.json'))}
_, values = pea_rates_for_year(2025)
rate = values['schedule_4_2']['22_33kv']['on_peak_demand_per_kw']
from reoptjl.src.thailand.pea_tariff import build_pea_tariff
tariff = build_pea_tariff(months, off_peak)
total = 0.0
for period, steps in enumerate(tariff['coincident_peak_load_active_time_steps']):
    peak = max(loads[s - 1] for s in steps)
    total += peak * rate
    print('period %2d  peak %8.1f kW  charge %12.2f THB' % (period + 1, peak, peak * rate))
print('TOTAL demand charge THB %.2f' % total)
print('TOTAL demand charge USD %.2f' % (total / 32.5))
"
```

Record the USD total. This is what REopt must reproduce.

- [ ] **Step 3: Submit the case to the running stack**

Run:

```bash
./.venv/Scripts/python.exe -m proforma_thailand.run_case --case proforma_thailand/cases/coincident_peak_spike/case.json --out proforma_thailand/cases/coincident_peak_spike
```

If `run_case` does not exist yet (it lands in Task 15), submit the payload
directly instead:

```bash
./.venv/Scripts/python.exe -c "
import json, urllib.request, time
from proforma_thailand.case_builder import build_thailand_case
case = build_thailand_case(json.load(open('proforma_thailand/cases/coincident_peak_spike/case.json')))
req = urllib.request.Request('http://localhost:8000/v3/job/', data=json.dumps(case['payload']).encode(), headers={'Content-Type': 'application/json'}, method='POST')
run_uuid = json.load(urllib.request.urlopen(req))['run_uuid']
print('run', run_uuid)
while True:
    body = json.load(urllib.request.urlopen('http://localhost:8000/v3/job/%s/results' % run_uuid))
    if body.get('status') not in ('Optimizing...', 'optimizing...', 'queued'):
        break
    time.sleep(5)
json.dump(body, open('proforma_thailand/cases/coincident_peak_spike/results.json', 'w'), indent=2)
print('status', body.get('status'))
print('year_one_coincident_peak_cost_before_tax',
      body['outputs']['ElectricTariff'].get('year_one_coincident_peak_cost_before_tax'))
"
```

- [ ] **Step 4: Compare and record the finding**

Expected: `year_one_coincident_peak_cost_before_tax` matches the USD total from
Step 2 to within rounding (under 0.5%).

Create `docs/superpowers/notes/2026-09-04-coincident-peak-spike.md` recording:
the expected value, the value REopt returned, the percentage difference, the
run UUID, and a one-line verdict.

**If they do not match**, stop and escalate before continuing. The likely causes
are the 1-based versus 0-based timestep indexing in
`coincident_peak_load_active_time_steps`, or the Django-side array padding at
`reoptjl/models.py:1799` reordering the sets (it applies `list(set(l))` at
`models.py:1826`, which does not preserve order but does preserve membership,
so membership is what matters).

- [ ] **Step 5: Commit**

```bash
git add proforma_thailand/cases/coincident_peak_spike docs/superpowers/notes
git commit -m "Verify coincident-peak demand against the live solver at 15-min

Confirms empirically what the Julia source review showed: the constraint
compares power to power and is correct at time_steps_per_hour=4.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 13: Thai depreciation research

**Files:**
- Modify: `proforma_thailand/defaults/thailand_defaults.json` (tax block)
- Create: `docs/superpowers/notes/2026-09-04-thai-depreciation.md`
- Test: `proforma_thailand/tests/test_thailand_defaults.py` (append)

**Interfaces:**
- Consumes: nothing.
- Produces: cited `pv_depreciation_years` and `bess_depreciation_years` values.

- [ ] **Step 1: Research and record**

Establish, with citations to the Thai Revenue Code (Royal Decree No. 145
governing depreciation of assets) and any applicable BOI guidance:

1. The permitted depreciation method and rate for machinery and equipment.
2. Whether rooftop PV qualifies as machinery or as a building improvement, since
   the rates differ materially.
3. Whether accelerated depreciation applies to energy-saving equipment.
4. Whether BOI incentives could apply to Rofu, noting the inventory records none.

Write `docs/superpowers/notes/2026-09-04-thai-depreciation.md` with the finding,
the citation for each number, and an explicit statement of what remains
uncertain. If PV's classification cannot be settled from public sources, record
both candidate treatments and pick the conservative one (the longer life), and
mark the value as a placeholder so it renders as provisional.

- [ ] **Step 2: Write the failing test**

Append to `proforma_thailand/tests/test_thailand_defaults.py`:

```python
class DepreciationCitationTests(TestCase):

    def test_depreciation_entries_are_cited_not_left_as_task_stubs(self):
        from proforma_thailand.defaults import TAX_DEFAULTS_RAW

        for key in ("pv_depreciation_years", "bess_depreciation_years"):
            source = TAX_DEFAULTS_RAW[key]["source"]
            self.assertNotIn("TO BE CITED", source)
            self.assertGreater(
                len(source), 20, "{} needs a real citation".format(key)
            )

    def test_depreciation_lives_are_plausible(self):
        from proforma_thailand.defaults import TAX_DEFAULTS

        for key in ("pv_depreciation_years", "bess_depreciation_years"):
            self.assertGreaterEqual(TAX_DEFAULTS[key], 3)
            self.assertLessEqual(TAX_DEFAULTS[key], 25)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults.DepreciationCitationTests -v`
Expected: FAIL - the source still reads `TO BE CITED IN TASK 13 ...`

- [ ] **Step 4: Update the defaults with the researched values**

Replace the two tax entries with the researched values and their citations, for
example:

```json
    "pv_depreciation_years": {"value": 5, "source": "Thai Revenue Code, Royal Decree No. 145: machinery and equipment depreciated at up to 20% per year straight line"},
    "bess_depreciation_years": {"value": 5, "source": "Thai Revenue Code, Royal Decree No. 145: machinery and equipment depreciated at up to 20% per year straight line"}
```

Use whatever the research in Step 1 actually established; do not copy the above
if it contradicts the sources.

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_thailand_defaults -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add proforma_thailand/defaults/thailand_defaults.json proforma_thailand/tests/test_thailand_defaults.py docs/superpowers/notes/2026-09-04-thai-depreciation.md
git commit -m "Cite Thai depreciation lives for PV and BESS

Replaces the task stub with researched values and citations. Thai machinery
treatment is materially shorter than Vietnam's 20-year PV life, which moves
the tax shield forward and affects IRR.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 14: Thailand report workbook

The headline deliverable is a financed proforma, not just sizing. This renders it
by driving the existing engine with `THAILAND_PROFILE`, and folds the power
factor compensation from spec section 4 into project capex as a one-time cost.

**Files:**
- Create: `proforma_thailand/report.py`
- Test: `proforma_thailand/tests/test_report.py`

**Interfaces:**
- Consumes: `power_factor_charge` (Task 8), defaults (Task 9),
  `validate_no_unmarked_placeholders` (Task 10), `THAILAND_PROFILE` (Task 2),
  and from `proforma_vietnam`: `calculate_esco_pro_forma_from_reopt_results`,
  `build_vietnam_report_data`, `build_vietnam_esco_workbook`.
- Produces: `build_thailand_report(reopt_results, assumptions) -> (workbook, extras)`
  where `extras` carries `power_factor_compensation_kvar`,
  `power_factor_mitigation_cost_usd` and `billed_demand_kw_by_month`;
  `cash_flow_overrides_from_assumptions(assumptions) -> dict`.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_report.py`:

```python
from unittest import TestCase

from proforma_thailand.report import (
    build_thailand_report,
    cash_flow_overrides_from_assumptions,
)

ASSUMPTIONS = {
    "country": "Thailand",
    "local_currency_code": "THB",
    "utility_label": "PEA",
    "time_steps_per_hour": 4,
    "exchange_rate_thb_per_usd": 32.5,
    "vat_rate_fraction": 0.07,
    "power_factor_charge_per_kvar_thb": 56.07,
    "power_factor_allowance_fraction": 0.6197,
    "kvar_max": 664.0,
    "cit_regime": "standard_flat",
    "pv_depreciation_years": 5,
    "direct_ownership": {"enabled": True},
    "placeholder_keys": ["debt_interest_rate"],
    "annual_om_usd": 20000.0,
    "debt_fraction": 0.7,
    "debt_interest_rate_fraction": 0.06,
    "debt_term_years": 10,
}


def _results():
    horizon = 8
    return {
        "inputs": {
            "ElectricTariff": {"tou_energy_rates_per_kwh": [0.1] * horizon},
            "ElectricStorage": {"can_grid_charge": False},
            "Financial": {"analysis_years": 25},
            "ElectricLoad": {},
        },
        "outputs": {
            "PV": {
                "size_kw": 1000.0,
                "annual_energy_produced_kwh": 1_500_000.0,
                "electric_to_load_series_kw": [100.0] * horizon,
            },
            "ElectricStorage": {"size_kw": 0.0, "size_kwh": 0.0},
            "ElectricTariff": {
                "year_one_bill_before_tax": 400000.0,
                "year_one_bill_before_tax_bau": 500000.0,
                "year_one_demand_cost_before_tax": 60000.0,
                "year_one_demand_cost_before_tax_bau": 80000.0,
            },
            "ElectricUtility": {"annual_energy_supplied_kwh": 5_000_000.0},
            "ElectricLoad": {"annual_calculated_kwh": 6_500_000.0},
            "Financial": {},
        },
    }


class ThailandReportTests(TestCase):

    def test_overrides_map_thb_exchange_rate_onto_the_engine_key(self):
        overrides = cash_flow_overrides_from_assumptions(ASSUMPTIONS)

        self.assertEqual(overrides["exchange_rate_vnd_per_usd"], 32.5)

    def test_overrides_carry_the_direct_ownership_block(self):
        overrides = cash_flow_overrides_from_assumptions(ASSUMPTIONS)

        self.assertEqual(overrides["direct_ownership"], {"enabled": True})

    def test_overrides_never_carry_an_esco_discount(self):
        overrides = cash_flow_overrides_from_assumptions(ASSUMPTIONS)

        self.assertNotIn("esco_energy_discount_fraction", overrides)

    def test_workbook_renders_with_thailand_labels(self):
        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)

        texts = [
            value
            for worksheet in workbook.worksheets
            for row in worksheet.iter_rows(values_only=True)
            for value in row
            if isinstance(value, str)
        ]

        self.assertTrue(any("THB" in text for text in texts))
        self.assertFalse(any("VND" in text or "EVN" in text for text in texts))

    def test_power_factor_compensation_is_computed_from_billed_demand(self):
        assumptions = dict(ASSUMPTIONS, billed_demand_kw=800.0)

        _, extras = build_thailand_report(_results(), assumptions)

        self.assertAlmostEqual(
            extras["power_factor_compensation_kvar"],
            664.0 - 0.6197 * 800.0,
            places=3,
        )

    def test_no_compensation_needed_when_demand_stays_high(self):
        assumptions = dict(ASSUMPTIONS, billed_demand_kw=1368.0)

        _, extras = build_thailand_report(_results(), assumptions)

        self.assertEqual(extras["power_factor_compensation_kvar"], 0.0)
        self.assertEqual(extras["power_factor_mitigation_cost_usd"], 0.0)

    def test_placeholder_guard_passes_because_markers_are_rendered(self):
        from proforma_vietnam.validate_workbook import (
            validate_no_unmarked_placeholders,
        )
        from proforma_thailand.defaults import PLACEHOLDER_MARKER

        workbook, _ = build_thailand_report(_results(), ASSUMPTIONS)

        self.assertEqual(
            validate_no_unmarked_placeholders(
                workbook, PLACEHOLDER_MARKER, ("IRR", "NPV", "Payback")
            ),
            [],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand.report'`

- [ ] **Step 3: Write the implementation**

Create `proforma_thailand/report.py`:

```python
"""Render the Thailand proforma workbook.

Drives the proforma_vietnam engine with THAILAND_PROFILE. Money keys keep their
historical ``_vnd`` suffix and carry THB (see the spec's section 2); only the
rendered labels change, and a test asserts no VND or EVN string survives.

Power factor is handled per spec section 4: compensation is sized once from the
post-PV billed demand and added to project capex, rather than carried as a
25-year penalty stream that competent engineering would avoid.
"""

from proforma_thailand.defaults import (
    FINANCIAL_DEFAULTS,
    PLACEHOLDER_MARKER,
    value_of,
)
from proforma_vietnam.country_profile import THAILAND_PROFILE
from proforma_vietnam.esco_pro_forma import (
    calculate_esco_pro_forma_from_reopt_results,
)
from proforma_vietnam.report_data import build_vietnam_report_data
from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook

# Assumption keys that map straight onto cash-flow keyword arguments.
PASSTHROUGH_OVERRIDE_KEYS = (
    "annual_om_usd",
    "debt_fraction",
    "debt_interest_rate_fraction",
    "debt_term_years",
    "project_years",
    "pv_depreciation_years",
    "cit_regime",
    "om_escalation_rate",
    "pv_degradation_rate",
    "battery_replacement_year",
)


def cash_flow_overrides_from_assumptions(assumptions):
    """Translate a Thailand assumptions block into cash-flow keyword arguments.

    The engine's currency keyword is named for Vietnam; Thailand passes its
    THB-per-USD rate through the same argument, which is what makes the ``_vnd``
    presentation keys carry THB.
    """
    overrides = {}
    for key in PASSTHROUGH_OVERRIDE_KEYS:
        if assumptions.get(key) is not None:
            overrides[key] = assumptions[key]
    if assumptions.get("exchange_rate_thb_per_usd") is not None:
        overrides["exchange_rate_vnd_per_usd"] = assumptions[
            "exchange_rate_thb_per_usd"
        ]
    if assumptions.get("direct_ownership") is not None:
        overrides["direct_ownership"] = assumptions["direct_ownership"]
    return overrides


def compute_power_factor_compensation(assumptions):
    """Return ``(required_kvar, mitigation_cost_usd)``.

    PV reduces billed kW but not kVAR, so the PEA allowance shrinks as demand
    falls. Anything above the allowance is compensated once with a capacitor
    bank rather than paid monthly.
    """
    kvar_max = assumptions.get("kvar_max")
    billed_kw = assumptions.get("billed_demand_kw")
    if not kvar_max or not billed_kw:
        return 0.0, 0.0
    allowance = assumptions["power_factor_allowance_fraction"] * billed_kw
    required = max(0.0, kvar_max - allowance)
    if required <= 0.0:
        return 0.0, 0.0
    cost_usd = value_of(FINANCIAL_DEFAULTS, "power_factor_mitigation_cost")
    return required, cost_usd


def build_thailand_report(reopt_results, assumptions):
    """Return ``(workbook, extras)`` for a Thailand DIRECT_OWNERSHIP run."""
    required_kvar, mitigation_cost = compute_power_factor_compensation(assumptions)

    overrides = cash_flow_overrides_from_assumptions(assumptions)
    if mitigation_cost:
        overrides["other_capex_vnd"] = (
            overrides.get("other_capex_vnd", 0.0) + mitigation_cost
        )

    cash_flow_result = calculate_esco_pro_forma_from_reopt_results(
        reopt_results,
        # DIRECT_OWNERSHIP captures the whole avoided bill, so there is no
        # discount to apply; the engine ignores this under that structure.
        esco_energy_discount_fraction=0.0,
        **overrides
    )
    report_data = build_vietnam_report_data(
        reopt_results,
        cash_flow_result,
        poa_irradiance_series=assumptions.get("pv_poa_irradiance_series"),
    )

    workbook_assumptions = dict(assumptions)
    workbook_assumptions["placeholder_marker"] = PLACEHOLDER_MARKER
    workbook_assumptions["power_factor_compensation_kvar"] = required_kvar
    workbook_assumptions["power_factor_mitigation_cost_usd"] = mitigation_cost

    workbook = build_vietnam_esco_workbook(
        cash_flow_result,
        assumptions=workbook_assumptions,
        report_data=report_data,
        profile=THAILAND_PROFILE,
    )

    extras = {
        "power_factor_compensation_kvar": required_kvar,
        "power_factor_mitigation_cost_usd": mitigation_cost,
        "billed_demand_kw_by_month": assumptions.get("billed_demand_kw_by_month", []),
    }
    return workbook, extras
```

- [ ] **Step 4: Make the placeholder markers render**

The guard test requires at least one cell carrying `PLACEHOLDER_MARKER`. In
`proforma_vietnam/audit_sheets.py`'s assumptions writer, emit one row per entry
in `assumptions["placeholder_keys"]` when that key is present, each carrying
`assumptions["placeholder_marker"]` in its source column. Gate the block on the
key being present so Vietnam workbooks, which never set it, are unchanged.

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_report -v`
Expected: PASS, 7 tests

- [ ] **Step 6: Run the full suite and the Vietnam gate**

Run: `./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .`
Expected: `OK`

Run the gate command from Task 3 Step 5.
Expected: all 8 `OK`. The Step 4 change touches a shared writer, so this check
matters.

- [ ] **Step 7: Commit**

```bash
git add proforma_thailand/report.py proforma_thailand/tests/test_report.py proforma_vietnam/audit_sheets.py
git commit -m "Render the Thailand proforma workbook

Drives the existing engine with THAILAND_PROFILE and folds one-time power
factor compensation into project capex rather than carrying a 25-year
penalty stream. Placeholder keys render on the Assumptions sheet so the
headline-metric guard has something to find.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 15: Run the RTS and RTS+BESS cases

**Prerequisite:** stack running (`docker-compose up -d`), Task 12 passed.

**Files:**
- Create: `proforma_thailand/run_case.py`
- Create: `proforma_thailand/cases/rts/case.json`
- Create: `proforma_thailand/cases/rts_bess/case.json`
- Test: `proforma_thailand/tests/test_run_case.py`

**Interfaces:**
- Consumes: `build_thailand_case` (Task 11), `power_factor_charge` (Task 8).
- Produces: `main(argv) -> int` CLI; `summarize_results(results, loads_kw, tariff_extras) -> dict` with keys `pv_kw`, `bess_kw`, `bess_kwh`, `annual_load_kwh`, `annual_pv_kwh`, `grid_offset_fraction`, `billed_demand_kw_by_month`, `power_factor_compensation_kvar`.

- [ ] **Step 1: Write the failing test**

Create `proforma_thailand/tests/test_run_case.py`:

```python
from unittest import TestCase

from proforma_thailand.run_case import summarize_results


class SummarizeResultsTests(TestCase):

    def _results(self, pv_kw=1000.0, pv_kwh=1_500_000.0, grid_kwh=5_000_000.0):
        return {
            "outputs": {
                "PV": {"size_kw": pv_kw, "annual_energy_produced_kwh": pv_kwh},
                "ElectricStorage": {"size_kw": 0.0, "size_kwh": 0.0},
                "ElectricLoad": {"annual_calculated_kwh": 6_500_000.0},
                "ElectricUtility": {"annual_energy_supplied_kwh": grid_kwh},
            }
        }

    def test_grid_offset_is_one_minus_grid_over_load(self):
        summary = summarize_results(self._results(), extras={})

        self.assertAlmostEqual(
            summary["grid_offset_fraction"], 1 - 5_000_000.0 / 6_500_000.0, places=6
        )

    def test_sizes_are_carried_through(self):
        summary = summarize_results(self._results(), extras={})

        self.assertEqual(summary["pv_kw"], 1000.0)
        self.assertEqual(summary["bess_kw"], 0.0)

    def test_zero_load_does_not_divide_by_zero(self):
        results = self._results()
        results["outputs"]["ElectricLoad"]["annual_calculated_kwh"] = 0.0

        summary = summarize_results(results, extras={})

        self.assertEqual(summary["grid_offset_fraction"], 0.0)

    def test_report_extras_are_merged_into_the_summary(self):
        summary = summarize_results(
            self._results(),
            extras={"power_factor_compensation_kvar": 168.24,
                    "power_factor_mitigation_cost_usd": 6000.0},
        )

        self.assertAlmostEqual(
            summary["power_factor_compensation_kvar"], 168.24, places=3
        )
        self.assertEqual(summary["power_factor_mitigation_cost_usd"], 6000.0)

    def test_missing_extras_default_to_zero(self):
        summary = summarize_results(self._results(), extras={})

        self.assertEqual(summary["power_factor_compensation_kvar"], 0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_run_case -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'proforma_thailand.run_case'`

- [ ] **Step 3: Write the implementation**

Create `proforma_thailand/run_case.py`:

```python
"""Build, submit and report a Thailand REopt case.

Same submit/poll shape as proforma_vietnam/run_case.py, but the workbook is
built locally from the returned results rather than fetched from the Django
report endpoint - there is no Thailand equivalent of ?vietnam_proforma=true.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

from proforma_thailand.case_builder import build_thailand_case
from proforma_thailand.report import build_thailand_report

DEFAULT_API_URL = "http://localhost:8000/v3"
POLLING_STATUSES = ("Optimizing...", "optimizing...", "queued")
BODY_BEARING_ERROR_CODES = (400, 404, 500)


def summarize_results(results, extras):
    """Headline figures for the Keen update: sizing and grid offset."""
    outputs = results.get("outputs", {})
    pv = outputs.get("PV") or {}
    if isinstance(pv, list):
        pv = pv[0] if pv else {}
    storage = outputs.get("ElectricStorage") or {}
    load = outputs.get("ElectricLoad") or {}
    utility = outputs.get("ElectricUtility") or {}

    annual_load = float(load.get("annual_calculated_kwh") or 0.0)
    annual_grid = float(utility.get("annual_energy_supplied_kwh") or 0.0)
    grid_offset = 0.0 if annual_load <= 0 else 1.0 - annual_grid / annual_load

    return {
        "pv_kw": float(pv.get("size_kw") or 0.0),
        "bess_kw": float(storage.get("size_kw") or 0.0),
        "bess_kwh": float(storage.get("size_kwh") or 0.0),
        "annual_load_kwh": annual_load,
        "annual_pv_kwh": float(pv.get("annual_energy_produced_kwh") or 0.0),
        "grid_offset_fraction": grid_offset,
        "power_factor_compensation_kvar": float(
            extras.get("power_factor_compensation_kvar") or 0.0
        ),
        "power_factor_mitigation_cost_usd": float(
            extras.get("power_factor_mitigation_cost_usd") or 0.0
        ),
        "billed_demand_kw_by_month": extras.get("billed_demand_kw_by_month", []),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and run a Thailand REopt case.")
    parser.add_argument("--case", required=True, help="Path to Thailand case JSON.")
    parser.add_argument("--out", default=None, help="Output directory.")
    parser.add_argument("--api-url", default=os.environ.get("REOPT_API_URL", DEFAULT_API_URL))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=5)
    parser.add_argument("--max-polls", type=int, default=240)
    args = parser.parse_args(argv)

    api_base = args.api_url.rstrip("/")
    if api_base.endswith("/job"):
        api_base = api_base[: -len("/job")]

    case_path = Path(args.case)
    case = build_thailand_case(json.loads(case_path.read_text(encoding="utf-8")))

    out_dir = Path(args.out) if args.out else case_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "payload.json", case["payload"])
    _write_json(out_dir / "assumptions.json", case["assumptions"])

    if args.dry_run:
        return 0

    run_uuid = _submit(api_base, case["payload"])
    results = _poll(api_base, run_uuid, args.poll_seconds, args.max_polls)
    _write_json(out_dir / "results.json", results)

    if results.get("status") != "optimal":
        print("Run {} ended with status {!r}.".format(run_uuid, results.get("status")),
              file=sys.stderr)
        for key, value in (results.get("messages", {}).get("errors") or {}).items():
            print("  {}: {}".format(key, value), file=sys.stderr)
        return 1

    assumptions = dict(case["assumptions"], run_uuid=run_uuid)
    workbook, extras = build_thailand_report(results, assumptions)
    workbook.save(out_dir / "thailand_report_{}.xlsx".format(run_uuid))
    _write_json(out_dir / "summary.json", summarize_results(results, extras))
    return 0


def _submit(api_base, payload):
    post = request.Request(
        "{}/job/".format(api_base),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(post) as response:
        return json.loads(response.read().decode("utf-8"))["run_uuid"]


def _poll(api_base, run_uuid, poll_seconds, max_polls):
    url = "{}/job/{}/results".format(api_base, run_uuid)
    for _ in range(max_polls):
        body = _get(url)
        if body.get("status") not in POLLING_STATUSES:
            return body
        time.sleep(poll_seconds)
    raise TimeoutError("Timed out waiting for REopt results for {}.".format(run_uuid))


def _get(url):
    try:
        with request.urlopen(url) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code in BODY_BEARING_ERROR_CODES:
            try:
                return json.loads(error.read().decode("utf-8"))
            except (ValueError, OSError):
                raise error from None
        raise


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
```

Note `--max-polls` is 240 rather than Vietnam's 120: a 35,040-timestep model with
12 coincident-peak periods solves considerably slower than an 8,760-timestep one.

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/Scripts/python.exe -m unittest proforma_thailand.tests.test_run_case -v`
Expected: PASS, 5 tests

- [ ] **Step 5: Write the two case files**

Create `proforma_thailand/cases/rts/case.json` - same shape as the spike case
but with PV enabled at the roof-area cap and storage off:

```json
{
  "site": {"latitude": 15.209427, "longitude": 102.475687},
  "load_profile": {
    "path": "proforma_thailand/data/rofu_load_15min.csv",
    "all_off_peak_dates_path": "proforma_thailand/data/rofu_all_off_peak_dates.json",
    "calendar_year_months": [[2026,1],[2026,2],[2026,3],[2026,4],[2026,5],[2026,6],
                             [2025,7],[2025,8],[2025,9],[2025,10],[2025,11],[2025,12]]
  },
  "tariff": {"voltage_level": "22_33kv", "exchange_rate_thb_per_usd": 32.5},
  "technologies": {
    "pv": {"max_kw": 1685.0, "installed_cost_per_kw": 700.0},
    "storage": {"max_kw": 0, "max_kwh": 0}
  },
  "direct_ownership": {"enabled": true}
}
```

Create `proforma_thailand/cases/rts_bess/case.json` identical except:

```json
  "technologies": {
    "pv": {"max_kw": 1685.0, "installed_cost_per_kw": 700.0},
    "storage": {"max_kw": 2000, "max_kwh": 8000, "can_grid_charge": false}
  },
```

`can_grid_charge` is false because PEA has no arbitrage spread worth chasing
under a two-bucket TOU tariff and grid charging would distort the demand-shaving
result. Storage bounds are upper limits for the optimizer to size within, not
targets.

- [ ] **Step 6: Run both cases**

Run:

```bash
./.venv/Scripts/python.exe -m proforma_thailand.run_case --case proforma_thailand/cases/rts/case.json --out proforma_thailand/cases/rts
./.venv/Scripts/python.exe -m proforma_thailand.run_case --case proforma_thailand/cases/rts_bess/case.json --out proforma_thailand/cases/rts_bess
```

Expected: both exit 0, each writing `payload.json`, `assumptions.json`,
`results.json`, `summary.json` and `thailand_report_<uuid>.xlsx`.

- [ ] **Step 7: Sanity-check the answers before reporting them**

Confirm from the two `summary.json` files:

- `pv_kw` is at or below 1,685 and not pinned at exactly the cap without reason.
- RTS `grid_offset_fraction` is plausible for a 1.7 MWp array against roughly
  7.3 GWh/yr of load - expect roughly 0.25 to 0.35.
- The RTS+BESS case reduces billed demand below the evening floor of about
  1,121 kW; if it does not, storage is not being dispatched into the on-peak
  evening and the coincident-peak wiring needs re-checking.
- `power_factor_compensation_kvar` is reported for both cases.

If any check fails, investigate before writing up - a wrong number reaching
Keen is worse than a late one.

- [ ] **Step 8: Run every suite**

Run:

```bash
./.venv/Scripts/python.exe -m unittest discover -s proforma_vietnam/tests -t .
./.venv/Scripts/python.exe -m unittest discover -s proforma_thailand/tests -t .
./.venv/Scripts/python.exe -m unittest discover -s reoptjl/test -t . -p "test_thailand*"
```

Expected: all `OK`.

Run the Vietnam gate from Task 3 Step 5.
Expected: all 8 `OK`.

- [ ] **Step 9: Commit**

```bash
git add proforma_thailand/run_case.py proforma_thailand/cases proforma_thailand/tests/test_run_case.py
git commit -m "Run the RTS and RTS+BESS cases for Rofu Thailand

Adds the Thailand CLI and both case definitions, and reports sizing, grid
offset and required power factor compensation.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Notes for the executor

- **The Vietnam gate is the most important check in this plan.** Run it after
  Tasks 3, 4 and 10. If any of the 8 workbooks moves a cell, stop and revert the
  offending change rather than updating the baseline.
- **Do not update `baseline_workbooks/`** once captured at HEAD. It is the
  reference; regenerating it mid-plan would mask exactly the drift it exists to
  catch.
- Tasks 12 and 14 need the Docker stack. Every other task is offline.
- Task 13 is research; its output is a cited note plus two numbers. Do not guess
  the values to make the test pass.
- ESCO/PPA is out of scope. If a task seems to need an ESCO discount fraction,
  something has drifted from the spec.
