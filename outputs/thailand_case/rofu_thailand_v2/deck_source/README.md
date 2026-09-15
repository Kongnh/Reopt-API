# Rofu feasibility deck, second edition (measured roof): source

`Rofu_Thailand_Solar_Storage_Feasibility_v2.pptx` (and the PDF handout beside
it) are generated, not hand-edited.

1. `extract_data.py` reads the five case records in this folder (results,
   assumptions, summary) and writes `deck_data.json` with the case table,
   both grid offset bases, monthly load, hourly profiles, the typical-day
   dispatch of every storage case, the DSCR series and the roof table. It
   mirrors the override block of `proforma_thailand.report` (insurance,
   power factor) so the numbers equal the workbooks.
2. `build_deck.js` (pptxgenjs, `npm install pptxgenjs` in a scratch folder)
   builds the deck from `deck_data.json`, the roof measurement, the satellite
   picture (`../../rofu_thailand/Rofu Rooftop satellite picture.jpeg`, copied to the scratch
   folder as `roof.jpeg`) and the design assets under `tmp/keen_design`
   (Allotrope logo, KEEN reference cover image; not in git). Style follows
   `Rofu_Thailand_Tariff_Structure_Internal.pptx` and the first edition.
3. Render with LibreOffice (`soffice --headless --convert-to pdf`) for the
   handout.

Cases: 1 roof F (432.8 kWp), 2 roof F with storage, 3 all roofs (2,121.5 kWp),
4 all roofs with storage, 5 no roof limit with storage (the first edition's
case 6 record, copied unchanged). Roof caps are the measured outline areas
(16,319.27 m2 total, roof F 3,329.30 m2) times 65 percent usable times
0.20 kWp per m2, the memo's conversion.

Grid offset in the results table is on the memo's grid-to-load basis
(`grid_offset_to_load`); the workbooks' `grid_offset_fraction` also nets
grid-to-storage and is carried in `deck_data.json` as `grid_offset`.
