# Rofu Thailand Tariff Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a verified ten-slide English PowerPoint and a Vietnamese chat brief explaining the current PEA tariff at Rofu Thailand.

**Architecture:** A single Artifact Tool JavaScript builder will encode sourced constants, calculations, slide layouts, and speaker-note citations. The builder will export a draft, run the presentation finalizer, and write the final deck into the existing Thailand case output folder.

**Tech Stack:** JavaScript ES modules, `@oai/artifact-tool`, bundled presentation finalizer, Poppler rendering tools.

---

### Task 1: Freeze evidence and calculations

**Files:**
- Read: `outputs/thailand_case/rofu_thailand/KEEN_THAILAND_MEMO.md`
- Read: internal PEA tariff PDF and June 2025 bill in the KEEN project folder

- [x] Calculate each June 2025 bill component from the tariff inputs and confirm the total.
- [x] Record the current model's PV and BESS results without running the model.
- [x] Separate confirmed facts, implications, and diligence items in the slide outline.

### Task 2: Build the presentation

**Files:**
- Create: `tmp/presentations/rofu_tariff/build_rofu_tariff_deck.mjs`
- Create: `outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx`

- [x] Recreate the reference deck's color, typography, header, footer, and cover treatment.
- [x] Build ten slides with editable native diagrams and charts.
- [x] Add speaker notes that identify the internal evidence used for every factual slide.
- [x] Export a private draft and finalize to a separate output file.

### Task 3: Verify and deliver

**Files:**
- Inspect: final PPTX, rendered slide PNGs, and validation receipt
- Modify if needed: `tmp/presentations/rofu_tariff/build_rofu_tariff_deck.mjs`

- [x] Render every slide and inspect each image at full size.
- [x] Run package, layout, font, and editable-chart validation.
- [x] Recalculate the bill independently and compare it with slide values.
- [x] Confirm the deck has ten slides and contains the required topics.
- [x] Update `CODEX_SESSION.md` and `SESSION_NOTES.md` with outputs, checks, assumptions, and remaining diligence items.
