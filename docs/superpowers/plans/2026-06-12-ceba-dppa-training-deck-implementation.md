# CEBA Vietnam DPPA Training Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify an editable 30-slide CEBA training deck that prepares factory representatives to evaluate Vietnam virtual-DPPA offers.

**Architecture:** Use a thread-scoped artifact-tool workspace for all source ledgers, slide modules, renders, layouts, and QA. Build one editable artifact-tool ESM module per slide, sharing a small visual-system helper and a single verified data ledger. Export only the final PPTX to `outputs/ceba_training/`, preserve the existing deck and Python script, and delete the temporary artifact workspace after final verification.

**Tech Stack:** Node.js ESM, `@oai/artifact-tool/presentation-jsx`, bundled Presentations-skill build/render/layout scripts, PowerShell, repository JSON/Markdown evidence, primary web sources for current regulation.

---

## File Structure

Temporary implementation workspace:

`outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/`

- `profile-plan.txt` - create-mode profile, finance precision gates, and QA blockers.
- `source-notes.txt` - primary-source URLs, repository evidence, dates, and provenance.
- `reference-audit.txt` - useful and stale patterns in the existing CEBA decks.
- `data.json` - verified values used by slides and numerical QA.
- `claim-spine.txt` - final slide claims, proof objects, sources, and timing.
- `design-system.txt` - palette, typography, layout families, footer, and buyer-question grammar.
- `contact-sheet-plan.txt` - slide-by-slide macro-layout plan.
- `lib/theme.mjs` - shared colors, type, dimensions, text styles, and footer helpers.
- `lib/components.mjs` - shared title, kicker, buyer-question, source-footer, table, metric, and gate helpers.
- `lib/data.mjs` - reads and validates `data.json`.
- `slides/slide-01.mjs` through `slides/slide-30.mjs` - one editable slide per module.
- `preview/`, `layout/`, `qa/`, and `assets/` - temporary render and verification files.

Durable repository outputs:

- Create: `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`
- Modify at closeout: `CODEX_SESSION.md`
- Modify at closeout: `SESSION_NOTES.md`

Do not modify or delete:

- `outputs/ceba_training/CEBA_DPPA_Mechanisms_Pricing.pptx`
- `outputs/ceba_training/build_deck.py`
- unrelated untracked files or generated outputs

### Task 1: Initialize The Artifact Workspace And Runtime Gate

**Files:**
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/profile-plan.txt`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/qa/runtime-check.txt`

- [ ] **Step 1: Create the required workspace folders**

Run:

```powershell
$w = 'outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey'
New-Item -ItemType Directory -Force "$w/slides","$w/lib","$w/preview","$w/layout","$w/assets","$w/qa" | Out-Null
```

Expected: all seven directories exist under the thread-scoped workspace.

- [ ] **Step 2: Write the profile plan**

Write `profile-plan.txt` with:

```text
task mode: create
primary deck-profile: strategy-led training using general create-mode gates
secondary profile gates: finance-ir precision; appendix-heavy readability
required proof objects: five-line bill bridge, money-flow diagram, worked NSMO reconciliation, three-gate diagram, Case 5/6 comparison, negotiation-sweep matrix
source requirements: primary regulatory sources plus current repository outputs
brand constraints: use CEBA palette only; no invented CEBA or Allotrope logos
QA gates: exact units and assumptions, 30 slides, 45-minute main story, buyer action on every main slide, no unsupported claims
known missing inputs: artifact-tool speaker-notes support must be tested
```

- [ ] **Step 3: Run the artifact-tool runtime check**

Run:

```powershell
$skill = 'C:/Users/kongn/.codex/plugins/cache/openai-primary-runtime/presentations/26.601.10930/skills/presentations'
$w = 'outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey'
node "$skill/scripts/check_presentation_runtime.mjs" --workspace "$w" *> "$w/qa/runtime-check.txt"
Get-Content "$w/qa/runtime-check.txt"
```

Expected: artifact-tool runtime is available and the command exits `0`.

- [ ] **Step 4: Test speaker-notes support before depending on it**

Search the bundled artifact-tool surface and runtime examples for `notes`, `speakerNotes`, and `addNotes`. Record the supported property or method in `qa/runtime-check.txt`. If no supported API is found, record `speaker notes unsupported by current artifact-tool runtime` and keep facilitation/source cues in the slide source footer and backup assumptions slide; do not mutate PPTX OOXML outside artifact-tool.

- [ ] **Step 5: Commit the runtime gate**

Do not commit temporary workspace files. Record the successful runtime check in the later session closeout commit.

### Task 2: Build The Verified Source Ledger And Data Contract

**Files:**
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/source-notes.txt`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/reference-audit.txt`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/data.json`

- [ ] **Step 1: Extract current repository evidence**

Read and reconcile:

```text
vietnam_market_context.md
tmp_dppa_simulation_extract.txt
SESSION_NOTES.md, 2026-06-11 final and later entries
outputs/vietnam_case/factory_a/case_5/results.json
outputs/vietnam_case/factory_a/case_5/assumptions.json
outputs/vietnam_case/factory_a/case_6/results.json
outputs/vietnam_case/factory_a/case_6/assumptions.json
outputs/vietnam_case/factory_a/dppa_negotiation_study/NEGOTIATION_SUMMARY.md
outputs/vietnam_case/factory_a/dppa_negotiation_study_case_6/NEGOTIATION_SUMMARY.md
outputs/vietnam_case/factory_a/dppa_negotiation_study_case_6_lower_strikes/NEGOTIATION_SUMMARY.md
```

Expected reconciled case values:

```text
Case 5: equity IRR 16.9%; project IRR 13.5%; NPV USD 1.52M; min DSCR 1.14x; payback 9.1y; buyer Y1 -8.7%; buyer 10yr -8.9%; buyer lifetime -9.3%.
Case 6: equity IRR 26.9%; project IRR 18.2%; NPV USD 2.54M; min DSCR 1.50x; payback 4.7y; buyer -14.4% on all horizons.
Lower-strike Case 6: 0/20 balanced; closest buyer-positive term strike 1,300 and 70% volume; buyer lifetime +0.46%; seller equity IRR 17.85%; min DSCR 1.143x.
Combined Case 6 sweep: 0/56 balanced scenarios.
```

- [ ] **Step 2: Verify time-sensitive regulatory claims with primary sources**

Browse primary Vietnamese government, MOIT, NSMO, or EVN sources for:

```text
Decree 57/2025/NĐ-CP status and relevant virtual-DPPA articles
current eligible voltage levels
current K_pp values or publication status
current C_dppa_dv and P_cl fee values
current EVN TOU tariff values used for the BAU slide
```

Record the exact source URL, publication date, access date `2026-06-12`, claim supported, and whether the claim is regulation, current tariff, NSMO example, or model assumption. Remove or qualify any claim that cannot be confirmed.

- [ ] **Step 3: Reproduce the official worked-example totals**

Use a focused PowerShell or Node calculation and record the inputs and outputs in `source-notes.txt`.

Expected:

```text
C_DN = 7,446,297,600 VND
C_KH = 11,186,097,600 VND
generator revenue = 7,857,600,000 VND
```

- [ ] **Step 4: Create `data.json` with explicit source labels**

The JSON must contain these top-level keys:

```json
{
  "as_of": "2026-06-12",
  "presenter": {},
  "regulation": {},
  "tariff": {},
  "settlement_example": {},
  "case_5": {},
  "case_6": {},
  "case_6_lower_strike": {},
  "session_timing_minutes": {},
  "sources": {}
}
```

Every numerical value must include a unit and source key. Store percentages as fractions and format them only at presentation time.

- [ ] **Step 5: Validate the data contract**

Run a Node assertion script from the command line that checks:

```text
as_of equals 2026-06-12
worked-example totals match exactly
Case 5 and Case 6 values match the reconciled values above
lower-strike balanced count equals 0 of 20
combined Case 6 balanced count equals 0 of 56
main timing values total 45
```

Expected: `data ledger checks passed`.

### Task 3: Lock The Claim Spine, Timing, And Contact-Sheet Rhythm

**Files:**
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/claim-spine.txt`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/design-system.txt`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/contact-sheet-plan.txt`

- [ ] **Step 1: Write the 30-slide claim spine**

Use the approved 24-main-slide and 6-backup architecture. For every main slide specify:

```text
slide number
kicker naming the buyer decision
claim title
proof object
buyer question or action
source key
speaker timing
omission notes
```

Use these six timing blocks, totaling 45 minutes:

```text
Establish your baseline: 5
Decode the DPPA bill: 12
Test the commercial offer: 7
Check bankability: 7
Stress-test the deal: 11
Prepare negotiation questions and close: 3
```

- [ ] **Step 2: Write the design system**

Specify:

```text
slide size: 1280x720
font: Segoe UI / Segoe UI Semibold
navy #0F293D; teal #127A7A; amber #E09A2B; green #2E9E5B
white mechanism slides; navy evidence slides
green only for a passed gate
minimum body text: 18px main, 15px backup, 11px source footer
named kicker marker/label pairs for layout QA
buyer-question rail on every main slide except title and roadmap
quiet source footer with as-of date
```

- [ ] **Step 3: Plan at least eight macro-layout families**

The contact-sheet plan must use:

```text
editorial title
buyer-journey roadmap
baseline bridge
relationship flow
five-line cost stack
worked-example ledger
two-way comparison
three-gate flow
case comparison
negotiation matrix
decision checklist
appendix reference table
```

Expected: no three consecutive slides use the same macro-layout family.

- [ ] **Step 4: Self-review the story**

Confirm every main title is a conclusion, every main slide has one dominant proof object, and every buyer-question rail contains a procurement action rather than a summary.

### Task 4: Implement And Render The Shared Visual System

**Files:**
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/lib/theme.mjs`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/lib/components.mjs`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/lib/data.mjs`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/slides/slide-01.mjs`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/slides/slide-07.mjs`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/slides/slide-20.mjs`

- [ ] **Step 1: Implement shared primitives**

Implement helpers for:

```text
addMechanismFrame()
addEvidenceFrame()
addKicker() with named kicker-marker and kicker-label elements
addClaimTitle()
addBuyerQuestion()
addSourceFooter()
addMetric()
addCompactTable()
addGate()
addFlowConnector()
```

All helpers must use artifact-tool editable primitives, preserve at least 16px interior padding for multi-line callouts, and never use decorative arrows.

- [ ] **Step 2: Implement three representative slides**

Build:

```text
slide 01: editorial title with Cong Nguyen and Allotrope Partners role
slide 07: five-line buyer bill mechanism slide
slide 20: Case 5 versus Case 6 evidence comparison
```

- [ ] **Step 3: Render the representative slides**

Run the bundled `render_artifact_slide.mjs` once for each slide, writing PNG and layout JSON outputs.

Expected: all three render and export without runtime errors.

- [ ] **Step 4: Run layout QA on the representative slides**

Run:

```powershell
node "$skill/scripts/check_layout_quality.mjs" --layout "$w/layout"
```

Expected: `0 error(s)`. Fix all errors and inspect warnings against the PNGs.

- [ ] **Step 5: Inspect the three rendered slides**

Verify title hierarchy, source-footer legibility, buyer-question consistency, box padding, evidence contrast, and absence of unofficial logos. Revise the primitives before building the remaining slides.

### Task 5: Build Slides 02-18, The Buyer Mechanics And Bankability Story

**Files:**
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/slides/slide-02.mjs` through `slide-18.mjs`, excluding existing `slide-07.mjs`

- [ ] **Step 1: Build slides 02-06**

Cover why the topic matters, buyer journey, BAU baseline, eligibility/loss-factor assumptions, and the physical/financial relationship map.

- [ ] **Step 2: Build slides 08-12**

Cover settlement quantity, fixed fee burden, two-slide worked NSMO example, and the first buyer-question checkpoint.

- [ ] **Step 3: Build slides 13-15**

Cover two-way CfD behavior, strike escalation/Year 1 reality, and hourly matching/contract volume.

- [ ] **Step 4: Build slides 16-18**

Cover developer revenue, buyer/seller/lender gates, and lifecycle items that move the bankable strike.

- [ ] **Step 5: Render and check slides 01-18**

Build a partial 18-slide deck, render all previews and layouts, run layout QA, and inspect the contact sheet. Expected: no unsupported metrics, no repeated macro-layout three slides in a row, and `0` layout errors.

### Task 6: Build Slides 19-30, The Case Study, Close, And Backup

**Files:**
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/slides/slide-19.mjs`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/slides/slide-21.mjs` through `slide-30.mjs`

- [ ] **Step 1: Build slides 19-24**

Use the anonymized factory continuation, Case 5/6 evidence, lower-strike result, empty 56-scenario three-gate window, realistic pricing expectations, and final buyer checklist.

Required language:

```text
Pricing alone did not balance the modeled Case 6 deal under the tested assumptions.
Closest buyer-positive tested term: 1,300 VND/kWh at 70% volume; buyer lifetime +0.46%; seller equity IRR 17.85%; minimum DSCR 1.143x.
Zero of 56 tested Case 6 scenarios passed buyer, seller, and lender gates together.
```

Do not generalize the modeled result into a claim that all Vietnam DPPAs are unbankable.

- [ ] **Step 2: Build slides 25-30**

Build six backup slides for detailed settlement formulas, market-price uncertainty, load drop, Scope 2/attributes, voltage/loss-factor status, and buyer-gate/model assumptions.

- [ ] **Step 3: Add supported speaker notes**

If Task 1 confirmed artifact-tool speaker-notes support, add timing, facilitation cue, and source references to every slide. If unsupported, keep the approved fallback recorded in `qa/runtime-check.txt` and ensure the visible sources and backup assumptions slide cover the same factual provenance.

- [ ] **Step 4: Render and check all 30 slides**

Run `build_artifact_deck.mjs` with `--slide-count 30`, final preview, layout, and contact-sheet paths.

Expected: 30 rendered PNGs, 30 layout JSON files, a non-empty draft PPTX, and a complete contact sheet.

### Task 7: Perform Numerical, Narrative, And Visual QA

**Files:**
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/qa/comeback-scorecard.txt`
- Create: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/qa/numerical-check.txt`
- Create only if needed: `outputs/019eb958-026f-78b0-94cd-7d9a6075fd7c/presentations/ceba-dppa-buyer-decision-journey/qa/layout-allowlist.json`

- [ ] **Step 1: Run mechanical layout QA**

Run:

```powershell
node "$skill/scripts/check_layout_quality.mjs" --layout "$w/layout/final"
```

Expected: `0 error(s)`. Any accepted warning must be a documented false positive and visually clean.

- [ ] **Step 2: Run numerical QA**

Compare every metric rendered in slides 04-23 and 25-30 against `data.json`. Confirm:

```text
official worked totals reconcile exactly
Case 5/6 values match the latest repository evidence
lower-strike values match the final 2026-06-11 summary
0/56 is explicitly described as tested Case 6 scenarios
all VND/kWh, USD, percentage, and DSCR units are visible
```

Expected: `numerical checks passed`.

- [ ] **Step 3: Inspect contact-sheet rhythm**

Score story, specificity, rhythm, hierarchy, precision, and visual quality from 0-5. Each dimension must score at least 4. Revise the weakest 2-4 slides if any dimension is below 4.

- [ ] **Step 4: Inspect every slide full-size**

Check no clipping, orphan labels, ambiguous connectors, unsupported logos, cramped callouts, missing source footers, or low-contrast evidence. Verify every main slide except title and roadmap has a buyer question/action.

- [ ] **Step 5: Rebuild after revisions**

Rerender the full deck and rerun layout and numerical QA after any revision.

### Task 8: Export, Verify, Clean Up, And Record The Session

**Files:**
- Create: `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`
- Modify: `CODEX_SESSION.md`
- Modify: `SESSION_NOTES.md`

- [ ] **Step 1: Export the final deck**

Run `build_artifact_deck.mjs` with:

```text
--slides-dir <workspace>/slides
--out outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx
--preview-dir <workspace>/preview/final
--layout-dir <workspace>/layout/final
--contact-sheet <workspace>/preview/final-contact-sheet.png
--slide-count 30
```

Expected: final PPTX exists and is non-empty.

- [ ] **Step 2: Verify the final package**

Confirm:

```text
final PPTX slide count equals 30
slides 01-24 are the 45-minute main story
slides 25-30 are backup
existing CEBA_DPPA_Mechanisms_Pricing.pptx and build_deck.py remain unchanged
no empty media or missing slide content
```

- [ ] **Step 3: Run the presentation cleanup helper**

Run:

```powershell
node "$skill/scripts/cleanup_presentation_workspace.mjs" --workspace "$w" --output-dir "outputs/ceba_training"
```

Expected: temporary workspace is removed and the final PPTX remains.

- [ ] **Step 4: Update repository handoff files**

Update `CODEX_SESSION.md` concisely with the delivered PPTX path, source/date basis, verification commands, notes-support result, git status, and remaining risks. Append detailed chronology and QA evidence to `SESSION_NOTES.md`.

- [ ] **Step 5: Verify handoff edits**

Run:

```powershell
git diff --check -- CODEX_SESSION.md SESSION_NOTES.md
git status --short --branch
```

Expected: no whitespace errors; unrelated existing dirty outputs remain untouched.

- [ ] **Step 6: Commit the final deliverable and handoff**

Run:

```powershell
git add -- outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx CODEX_SESSION.md SESSION_NOTES.md
git commit -m "Add CEBA DPPA buyer decision training deck"
```

Expected: commit contains only the new PPTX and the two handoff files.
