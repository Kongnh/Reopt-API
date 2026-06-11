# DPPA Commercial Negotiation Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a fixed-system 36-scenario DPPA commercial negotiation sweep for Factory A without rerunning REopt.

**Architecture:** Add a pure negotiation-sweep evaluator that copies the validated DPPA inputs, scales the reference hourly CfD volume, and calls the existing ESCO pro forma path for each strike-volume pair. Add a dedicated workbook/summary builder and a small CLI runner that reads clean Factory A case artifacts and writes the JSON, XLSX, and Markdown package.

**Tech Stack:** Python standard library, existing `proforma_vietnam` settlement/cash-flow modules, `openpyxl`, Django test runner.

---

### Task 1: Pure Scenario Sweep And Classification

**Files:**
- Create: `proforma_vietnam/dppa_negotiation_sweep.py`
- Test: `proforma_vietnam/tests/test_dppa_negotiation_sweep.py`

- [ ] **Step 1: Write failing tests for the scenario grid and volume scaling**

Add tests asserting that the default grid contains exactly 36 deterministic IDs and that every hourly volume is the reference value multiplied by its selected fraction.

- [ ] **Step 2: Run the focused tests and verify the expected import failure**

Run: `python manage.py test proforma_vietnam.tests.test_dppa_negotiation_sweep`

Expected: FAIL because `proforma_vietnam.dppa_negotiation_sweep` does not exist.

- [ ] **Step 3: Implement scenario generation and evaluation**

Implement:

```python
DEFAULT_STRIKES_VND_PER_KWH = tuple(range(1400, 2201, 100))
DEFAULT_VOLUME_FRACTIONS = (0.70, 0.80, 0.90, 1.00)

def run_dppa_negotiation_sweep(
    *,
    reopt_results,
    reference_dppa_inputs,
    cash_flow_assumptions,
    non_dppa_case_2_cash_flow,
    strikes_vnd_per_kwh=DEFAULT_STRIKES_VND_PER_KWH,
    volume_fractions=DEFAULT_VOLUME_FRACTIONS,
    thresholds=None,
):
    ...
```

For every scenario, deep-copy the DPPA inputs, replace the strike, scale the reference 8760 volume, call `calculate_esco_pro_forma_from_reopt_results`, and extract the required buyer, seller, lender, qualification, and CfD-direction metrics.

- [ ] **Step 4: Add failing tests for qualification gates, debt-service-only minimum DSCR, and Pareto dominance**

Use small synthetic rows for classification tests and assert that each failed gate is named separately.

- [ ] **Step 5: Implement qualification and Pareto-frontier helpers**

Implement pure helpers that apply the three gates and mark non-dominated balanced rows using factory savings versus BAU and equity IRR.

- [ ] **Step 6: Run focused tests**

Run: `python manage.py test proforma_vietnam.tests.test_dppa_negotiation_sweep`

Expected: PASS.

### Task 2: Negotiation Workbook And Markdown Summary

**Files:**
- Create: `proforma_vietnam/dppa_negotiation_workbook.py`
- Modify: `proforma_vietnam/tests/test_dppa_negotiation_sweep.py`

- [ ] **Step 1: Write failing output-builder tests**

Assert the workbook contains the nine required sheets and the Markdown summary explicitly mentions both BAU and non-DPPA `case_2`.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `python manage.py test proforma_vietnam.tests.test_dppa_negotiation_sweep`

Expected: FAIL because the output builders do not exist.

- [ ] **Step 3: Implement the workbook builder**

Create `build_dppa_negotiation_workbook(study)` using `openpyxl`. Include:

```text
Executive Summary
Scenario Matrix
Balanced Deals
Negotiation Frontier
Strike-Volume Matrix
Factory Savings Heatmap
ESCO IRR Heatmap
Minimum DSCR Heatmap
Methodology
```

Use buyer, seller, and lender labels, freeze headers, apply readable number formats, and use conditional color scales for the heatmaps.

- [ ] **Step 4: Implement the Markdown summary builder**

Create `build_dppa_negotiation_summary(study)` describing balanced terms, frontier terms, recommended starting range, trade-offs, both comparison baselines, and limitations.

- [ ] **Step 5: Run focused tests**

Run: `python manage.py test proforma_vietnam.tests.test_dppa_negotiation_sweep`

Expected: PASS.

### Task 3: Factory A Runner And Reconciliation

**Files:**
- Create: `proforma_vietnam/run_dppa_negotiation_sweep.py`
- Modify: `proforma_vietnam/tests/test_dppa_negotiation_sweep.py`

- [ ] **Step 1: Write failing reconciliation and artifact tests**

Assert the runner writes JSON, XLSX, and Markdown artifacts and that `strike_2000_volume_100` matches a direct clean `case_5` calculation within documented tolerances for Year 1 settlement totals, equity IRR, NPV, and DSCR.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `python manage.py test proforma_vietnam.tests.test_dppa_negotiation_sweep`

Expected: FAIL because the runner does not exist.

- [ ] **Step 3: Implement the runner**

Read:

```text
outputs/vietnam_case/factory_a/case_2/results.json
outputs/vietnam_case/factory_a/case_2/assumptions.json
outputs/vietnam_case/factory_a/case_5/assumptions.json
```

Calculate the non-DPPA `case_2` comparison, run the sweep, reconcile the `2000/100%` scenario against a direct `case_5` calculation, and write:

```text
outputs/vietnam_case/factory_a/dppa_negotiation_study/results.json
outputs/vietnam_case/factory_a/dppa_negotiation_study/Factory_A_DPPA_Negotiation_Sweep.xlsx
outputs/vietnam_case/factory_a/dppa_negotiation_study/NEGOTIATION_SUMMARY.md
```

- [ ] **Step 4: Run focused tests**

Run: `python manage.py test proforma_vietnam.tests.test_dppa_negotiation_sweep`

Expected: PASS.

- [ ] **Step 5: Run the Factory A sweep**

Run: `python -m proforma_vietnam.run_dppa_negotiation_sweep`

Expected: exit 0 and all three artifacts written with exactly 36 scenarios.

### Task 4: Regression Verification And Session Handoff

**Files:**
- Modify: `CODEX_SESSION.md`
- Modify: `SESSION_NOTES.md`

- [ ] **Step 1: Run the full Vietnam pro forma suite**

Run: `python manage.py test proforma_vietnam`

Expected: PASS.

- [ ] **Step 2: Inspect generated study metrics**

Verify exactly 36 unique scenarios, exact hourly volume scaling, balanced/frontier counts, and successful `2000/100%` reconciliation.

- [ ] **Step 3: Check changed files**

Run: `git diff --check`

Expected: no whitespace errors.

- [ ] **Step 4: Update handoff docs**

Record implementation, generated artifacts, verification commands, reconciliation result, remaining limitations, and current git status without modifying unrelated dirty outputs.
