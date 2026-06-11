# Factory A Case 6 Minimum BESS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify Factory A case 6 with case 5 PV capacity, the rounded minimum two-hour BESS, and a regenerated DPPA contract-volume profile.

**Architecture:** Clone case 5 configuration, force the three technical size bounds, run REopt to obtain dispatch, rebuild the DPPA volume from that dispatch, then perform a final end-to-end run to generate consistent financial outputs.

**Tech Stack:** PowerShell, JSON, Docker Compose, REopt V3 API, `proforma_vietnam.run_case`

---

### Task 1: Create Fixed-Size Case 6

**Files:**
- Create: `outputs/vietnam_case/factory_a/case_6/case.json`

- [ ] Clone `case_5/case.json` into the new `case_6` folder.
- [ ] Change the case name to identify the minimum-BESS scenario.
- [ ] Set PV `min_kw = max_kw = 5914`.
- [ ] Set storage `min_kw = max_kw = 592`.
- [ ] Set storage `min_kwh = max_kwh = 1184`.
- [ ] Confirm all other settings match case 5.

### Task 2: Run Initial Dispatch

**Files:**
- Create: `outputs/vietnam_case/factory_a/case_6/payload.json`
- Create: `outputs/vietnam_case/factory_a/case_6/assumptions.json`
- Create: `outputs/vietnam_case/factory_a/case_6/results.json`
- Create: `outputs/vietnam_case/factory_a/case_6/vietnam_report_<run_uuid>.xlsx`

- [ ] Start the required Docker services.
- [ ] Run:

```powershell
python -m proforma_vietnam.run_case --case outputs/vietnam_case/factory_a/case_6/case.json --poll-seconds 5 --max-polls 120
```

- [ ] Confirm the result status is `optimal` and the fixed sizes are returned.

### Task 3: Regenerate DPPA Contract Volume

**Files:**
- Modify: `outputs/vietnam_case/factory_a/case_6/case.json`

- [ ] Calculate each hourly contract volume from the initial result:

```text
PV-to-load + PV-to-grid + curtailed PV + storage-to-load + storage-to-grid
```

- [ ] Replace `dppa.cfd_contract_volume_kwh_per_hour` with the calculated
  8760-value series.
- [ ] Verify the profile has exactly 8760 values.

### Task 4: Run Final Case and Verify

**Files:**
- Regenerate: `outputs/vietnam_case/factory_a/case_6/payload.json`
- Regenerate: `outputs/vietnam_case/factory_a/case_6/assumptions.json`
- Regenerate: `outputs/vietnam_case/factory_a/case_6/results.json`
- Create: `outputs/vietnam_case/factory_a/case_6/vietnam_report_<run_uuid>.xlsx`

- [ ] Run the complete case again with `proforma_vietnam.run_case`.
- [ ] Confirm final status is `optimal`.
- [ ] Confirm final PV and storage sizes equal `5914`, `592`, and `1184`.
- [ ] Confirm the final contract-volume profile reconciles hour by hour.
- [ ] Confirm the final workbook exists and report key financial metrics.
- [ ] Run `git diff --check` on the created case 6 JSON and session docs.
- [ ] Update `CODEX_SESSION.md` and `SESSION_NOTES.md`.
