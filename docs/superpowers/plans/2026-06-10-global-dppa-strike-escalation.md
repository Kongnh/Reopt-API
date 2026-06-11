# Global DPPA Strike Escalation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make 4% annual CfD strike escalation the global default and regenerate Factory A cases 5 and 6 plus both negotiation sweeps.

**Architecture:** Change the single settlement default constant and case-builder fallback, preserving explicit overrides. Update the two Factory A case sources, then use the existing end-to-end runner and fixed-system negotiation runner to regenerate and reconcile all artifacts.

**Tech Stack:** Python, unittest, JSON, Docker Compose, Django/REopt API, openpyxl

---

### Task 1: Global Default And Tests

**Files:**
- Modify: `proforma_vietnam/dppa_settlement.py`
- Modify: `proforma_vietnam/case_builder.py`
- Modify: `proforma_vietnam/tests/test_case_builder.py`
- Modify: `proforma_vietnam/tests/test_cash_flow.py`

- [ ] Change the existing case-builder default test to expect `0.04`.
- [ ] Add a cash-flow test proving Year 2 strike revenue equals Year 1 multiplied by `1.04`.
- [ ] Run focused tests and verify they fail for the old zero default.
- [ ] Set `DEFAULT_CFD_STRIKE_ESCALATION_RATE = 0.04` and make the case builder use that constant.
- [ ] Run focused tests and verify they pass.

### Task 2: Factory A Source Assumptions

**Files:**
- Modify: `outputs/vietnam_case/factory_a/case_5/case.json`
- Modify: `outputs/vietnam_case/factory_a/case_6/case.json`

- [ ] Set `dppa.cfd_strike_escalation_rate` to `0.04` in both case sources.
- [ ] Verify all non-escalation inputs remain unchanged.

### Task 3: Regenerate Cases And Sweeps

**Files:**
- Regenerate: `outputs/vietnam_case/factory_a/case_5/{payload.json,assumptions.json,results.json,vietnam_report_*.xlsx}`
- Regenerate: `outputs/vietnam_case/factory_a/case_6/{payload.json,assumptions.json,results.json,vietnam_report_*.xlsx}`
- Regenerate: `outputs/vietnam_case/factory_a/dppa_negotiation_study/`
- Regenerate: `outputs/vietnam_case/factory_a/dppa_negotiation_study_case_6/`

- [ ] Run case 5 through `python -m proforma_vietnam.run_case`.
- [ ] Run case 6 through `python -m proforma_vietnam.run_case`.
- [ ] Confirm both generated assumptions explicitly contain `0.04`.
- [ ] Run both negotiation sweeps.
- [ ] Confirm 36 unique scenarios and successful direct/workbook reconciliation.

### Task 4: Verification And Handoff

**Files:**
- Modify: `CODEX_SESSION.md`
- Modify: `SESSION_NOTES.md`

- [ ] Run the focused and full local Vietnam pro forma test suites.
- [ ] Compare refreshed financial and negotiation metrics.
- [ ] Run `git diff --check`.
- [ ] Record regenerated UUIDs, metrics, verification, and remaining decisions.
