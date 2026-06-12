# CEBA Vietnam DPPA Training Deck Design

## Objective

Create a new, editable English-language training deck for CEBA members attending
the session **Understanding Vietnam's DPPA Mechanisms and Pricing
Considerations**.

The audience is factory-owner representatives in global-brand supply chains.
The deck must prepare them to evaluate virtual DPPA offers and ask developers
the right commercial questions.

Presenter:

- Cong Nguyen
- Vietnam Clean Energy Manager, Allotrope Partners

## Success Criteria

- The main deck supports a 45-minute training session followed by Q&A.
- Attendees can decompose a virtual DPPA bill, test an offer, and identify the
  commercial questions that require negotiation.
- Technical detail supports procurement decisions without dominating the live
  story.
- The deck is understandable as a standalone asset while using light callbacks
  to prior workshop sessions.
- All regulatory claims and model results are source-backed and dated where
  they may change.
- The final PPTX is editable, visually coherent, and render-verified.

## Scope

### Included

- Virtual grid-connected DPPA with a bilateral CfD overlay.
- EVN business-as-usual baseline and relevant TOU context.
- Five-line buyer settlement explanation.
- Selected settlement formulas and one worked NSMO example.
- Strike price, escalation, contract volume, and hourly matching considerations.
- Buyer, seller, and lender feasibility gates.
- An anonymized continuation of the prior factory case study using Cases 5 and
  6 and the negotiation sweep.
- Buyer decision checklist and procurement questions.
- Backup slides for detailed formulas, assumptions, and common questions.

### Excluded

- Private-wire or physical DPPA.
- Two-component pilot tariff content.
- Re-teaching the full DPPA overview, eligibility, and contracting session.
- Changes to REopt API implementation or financial models.

## Narrative Direction

The deck uses the **Buyer Decision Journey** direction. The session follows six
decisions rather than six technical modules:

1. Establish your baseline.
2. Decode the DPPA bill.
3. Test the commercial offer.
4. Check bankability.
5. Stress-test the deal.
6. Prepare negotiation questions.

Each section follows the same teaching pattern:

1. Explain the mechanism.
2. Show the cost or risk consequence.
3. Give the buyer a concrete question to ask.

The Factory A Cases 5 and 6 evidence is anonymized and serves as the narrative
climax. Light callbacks connect it to the prior on-site cases, but the deck
remains understandable without attending the earlier session.

## Slide Architecture

Target 24 main slides and 6 backup slides. The final build may vary by one main
slide if rendering or teaching rhythm requires a split or consolidation.

### Main Story

1. Title and presenter.
2. Why this session matters to a factory buyer.
3. Buyer decision journey and learning outcomes.
4. Establish the EVN BAU baseline.
5. Confirm eligibility and loss-factor assumptions.
6. Map the physical and financial relationships.
7. Introduce the five-line buyer bill.
8. Explain delivered and settlement volume.
9. Explain fixed fees and their structural cost.
10. Worked NSMO example: inputs and formulas.
11. Worked NSMO example: arithmetic and official totals.
12. Buyer questions after decoding the bill.
13. Explain two-way CfD behavior.
14. Explain strike escalation and Year 1 reality.
15. Explain hourly matching and contract volume.
16. Introduce developer revenue and financing.
17. Explain the buyer, seller, and lender gates.
18. Show lifecycle items that move the bankable strike.
19. Introduce the anonymized factory continuation.
20. Compare Case 5 and Case 6.
21. Show why right-sizing fixes bankability but not buyer value.
22. Show the negotiation sweep and empty three-gate window.
23. Translate findings into realistic pricing expectations.
24. Close with the buyer negotiation checklist and panel bridge.

### Backup

- Detailed settlement formula reference.
- FMP and CFMP context and uncertainty.
- Load-drop and volume-shortfall scenario.
- Renewable attributes and Scope 2 considerations.
- Voltage and loss-factor status.
- Buyer-gate measurement and model assumptions.

## Content Rules

- Every main slide has one claim title, one dominant proof object, and one buyer
  action or question.
- Formulas appear only when they explain a cost consequence.
- The worked NSMO example stays in the main story and is limited to two slides.
- Dense tariff tables, edge cases, and detailed formula references move to
  backup.
- Use conclusion-led titles rather than topic labels.
- Do not imply that a virtual DPPA automatically saves money.
- Distinguish regulatory mechanics, modeled assumptions, and negotiation terms.
- Date or qualify figures that may change, including fees, tariffs, loss
  factors, and market prices.

## Visual System

Use a clean industrial-procurement visual language based on the existing CEBA
palette:

- Navy `#0F293D`: evidence slides, section transitions, and strong conclusions.
- Teal `#127A7A`: mechanisms, navigation, and neutral emphasis.
- Amber `#E09A2B`: negotiation tension, warnings, and unresolved trade-offs.
- Green `#2E9E5B`: only for outcomes that genuinely pass a stated gate.
- White and light gray: explanatory slides and working space.

Typography uses installed Segoe UI family fonts. Slides use a 16:9 layout.

Visual rhythm:

- White mechanism slides explain how the system works.
- Navy evidence slides reveal case-study findings and commercial tension.
- Recurring **Buyer Question** callouts create a consistent procurement lens.
- Proof objects favor diagrams, bridges, comparisons, and compact tables over
  dense bullet pages.
- Sources and assumption dates appear quietly in the footer.

## Sources And Verification

The existing plan and `outputs/ceba_training/build_deck.py` are content
references, not automatically trusted sources.

Before finalizing:

- Verify current regulatory mechanics, eligibility, fees, and loss factors
  against primary sources.
- Reconcile Case 5, Case 6, and negotiation-sweep figures against the latest
  repository model outputs and summaries.
- Reproduce the official NSMO worked-example totals.
- Add an explicit "as of" date to time-sensitive assumptions.
- Do not reuse the stale Case 3 bankability claim from the older CEBA case-study
  deck.

## Delivery

- Preserve the existing PPTX as the prior version.
- Deliver the newly named editable PPTX at
  `outputs/ceba_training/CEBA_DPPA_Buyer_Decision_Journey_2026.pptx`.
- Build with the current artifact-tool presentation workflow.
- Include speaker notes with timing, facilitation cues, and source references.
- Render every slide and inspect the complete contact sheet.
- Verify slide titles, text overflow, layout bounds, source notes, and key
  numerical claims before delivery.

## Acceptance Checks

- Main-session timing totals 45 minutes.
- The deck contains 23-25 main slides and 6 backup slides.
- No physical-DPPA or two-component-tariff teaching content appears.
- Main slides remain procurement-led and technically balanced.
- The official worked-example totals reconcile.
- Case-study figures match the latest model evidence.
- Every main slide contains a buyer implication or action.
- PPTX export succeeds and rendered slides have no visible layout defects.
