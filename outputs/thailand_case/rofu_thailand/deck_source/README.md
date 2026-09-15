# Rofu feasibility deck: source

`Rofu_Thailand_Solar_Storage_Feasibility.pptx` (and the PDF handout beside it)
are generated, not hand-edited.

1. `extract_data.py` reads the six case records in this folder (results,
   assumptions, summary) and writes `deck_data.json` with the case table,
   monthly load, hourly profiles, the case 6 dispatch and the DSCR series.
   It mirrors the override block of `proforma_thailand.report` (insurance,
   power factor) so the numbers equal the workbooks and the memo.
2. `build_deck.js` (pptxgenjs, `npm install pptxgenjs` in a scratch folder)
   builds the deck from `deck_data.json`, the memo text and the design assets
   under `tmp/keen_design` (Allotrope logo, KEEN reference cover image; not in
   git). Style follows `Rofu_Thailand_Tariff_Structure_Internal.pptx`.
3. Render with LibreOffice (`soffice --headless --convert-to pdf`) for the
   handout.

Grid offset in the results table is the memo's figure (grid-to-load basis);
the workbooks' `grid_offset_fraction` also nets grid-to-storage and reads
48.9 percent for case 6 against the memo's 50.4.
