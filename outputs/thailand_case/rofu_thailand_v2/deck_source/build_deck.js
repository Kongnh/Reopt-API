// Rofu Thailand rooftop solar and storage: feasibility results deck, v2 (measured roof).
// Style follows outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx
// (pale green ground, teal title band, Allotrope logo, condensed layouts); content
// from the five case records under outputs/thailand_case/rofu_thailand_v2 (deck_data.json)
// and the roof measurement of September 2026 (seven buildings from satellite imagery).
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const ROOT = "C:/Users/kongn/Pictures/CodeProject/Reopt API/REopt_API";
const HERE = path.join(ROOT, "tmp/presentations/rofu_feasibility/v2");
const OUT = path.join(ROOT, "outputs/thailand_case/rofu_thailand_v2/Rofu_Thailand_Solar_Storage_Feasibility_v2.pptx");
const D = JSON.parse(fs.readFileSync(path.join(HERE, "deck_data.json"), "utf8"));

const C = {
  bg: "EAF5F2", header: "24857B", dark: "17685F", ink: "143B37", muted: "4D6D68",
  pale: "CFE7E2", pale2: "B7D9D2", green: "70AD52", green2: "3F8E73", yellow: "F7D98B",
  orange: "E98A55", red: "D77C7F", white: "FFFFFF", line: "8AB8B0", gray: "E5E9E8",
};
const FONT = "Arial";
const FOOT = "Rofu Thailand feasibility, measured roof  |  Allotrope Partners  |  September 2026";
const px = (v) => v / 96; // 1280 x 720 px design grid on a 13.333 x 7.5 in canvas

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Allotrope Partners";
pres.title = "Rofu Thailand rooftop solar and storage feasibility (measured roof)";

const logo = "image/png;base64," + fs.readFileSync(path.join(ROOT, "tmp/keen_design/allotrope-logo-1.png")).toString("base64");
const cover = "image/png;base64," + fs.readFileSync(path.join(ROOT, "tmp/keen_design/cover-03.png")).toString("base64");
const roofImg = "image/jpeg;base64," + fs.readFileSync(path.join(HERE, "roof.jpeg")).toString("base64");

let pageNo = 0;
function text(slide, str, x, y, w, h, o = {}) {
  slide.addText(str, {
    x: px(x), y: px(y), w: px(w), h: px(h), fontFace: FONT, fontSize: o.size || 14,
    bold: !!o.bold, italic: !!o.italic, color: o.color || C.ink, align: o.align || "left",
    valign: o.valign || "top", margin: 0, isTextBox: true, fill: o.fill ? { color: o.fill } : undefined,
    lineSpacingMultiple: o.lineSpacing, paraSpaceAfter: o.paraAfter, shrinkText: false,
  });
}
function rich(slide, runs, x, y, w, h, o = {}) {
  slide.addText(runs.map((r) => ({ text: r.t, options: { bold: !!r.b, color: r.c || o.color || C.ink, fontSize: r.s || o.size || 14, breakLine: !!r.br, bullet: r.bullet ? { indent: 14 } : undefined, paraSpaceAfter: r.after } })), {
    x: px(x), y: px(y), w: px(w), h: px(h), fontFace: FONT, valign: o.valign || "top", align: o.align || "left", margin: 0, isTextBox: true,
  });
}
function bullets(slide, items, x, y, w, h, o = {}) {
  slide.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1, paraSpaceAfter: o.after ?? 6 } })), {
    x: px(x), y: px(y), w: px(w), h: px(h), fontFace: FONT, fontSize: o.size || 14, color: o.color || C.ink, valign: "top", margin: 0, isTextBox: true,
  });
}
function box(slide, x, y, w, h, fill, o = {}) {
  slide.addShape(o.round === false ? pres.ShapeType.rect : pres.ShapeType.roundRect, {
    x: px(x), y: px(y), w: px(w), h: px(h), fill: { color: fill }, rectRadius: o.round === false ? undefined : px(o.radius || 16),
    line: o.line ? { color: o.line, width: o.lineWidth || 1 } : { color: fill, width: 0 },
    shadow: o.shadow ? { type: "outer", blur: 4, offset: 2, angle: 90, color: "000000", opacity: 0.12 } : undefined,
  });
}
function line(slide, x1, y1, x2, y2, color, width = 1.5) {
  slide.addShape(pres.ShapeType.line, { x: px(x1), y: px(y1), w: px(x2 - x1), h: px(y2 - y1), line: { color, width } });
}
function standard(title, notesText) {
  pageNo += 1;
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  box(slide, 8, 8, 1264, 96, C.header, { radius: 22 });
  text(slide, title, 42, 22, 980, 68, { size: 24, bold: true, color: C.white, valign: "middle" });
  slide.addImage({ data: logo, x: px(1068), y: px(24), w: px(170), h: px(52) });
  text(slide, FOOT, 42, 686, 700, 20, { size: 10, color: C.muted, valign: "middle" });
  text(slide, String(pageNo), 1190, 686, 48, 20, { size: 10, color: C.muted, align: "right", valign: "middle" });
  if (notesText) slide.addNotes(notesText);
  return slide;
}
function card(slide, x, y, w, h, o = {}) {
  box(slide, x, y, w, h, o.fill || C.white, { radius: o.radius || 18, line: o.line === false ? undefined : (o.lineColor || C.line), lineWidth: 1 });
}
function stat(slide, x, y, w, h, value, label, o = {}) {
  card(slide, x, y, w, h, { fill: o.fill || C.white, line: !o.fill });
  text(slide, value, x + 18, y + 12, w - 36, h * 0.40, { size: o.valueSize || 30, bold: true, color: o.valueColor || C.dark, valign: "middle" });
  text(slide, label, x + 18, y + h * 0.50, w - 36, h * 0.46, { size: o.labelSize || 12, color: o.labelColor || C.muted, valign: "top" });
}
const fmt0 = (v) => Math.round(v).toLocaleString("en-US");
const pct1 = (v) => (100 * v).toFixed(1) + "%";
const M = (v) => (v / 1e6).toFixed(2);
const floor1 = (v) => (Math.floor(v * 10) / 10).toFixed(1);
const cases = D.cases;
const c1 = cases[0], c2 = cases[1], c3 = cases[2], c4 = cases[3], c5 = cases[4];
const chartBase = {
  fontFace: FONT, catAxisLabelColor: C.muted, valAxisLabelColor: C.muted, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
  valGridLine: { color: "D5E3DF", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, plotArea: { fill: { color: C.white } },
  chartArea: { fill: { color: C.white } },
};

// ---------------------------------------------------------------- 1 cover
{
  pageNo += 1;
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addImage({ data: cover, x: 0, y: 0, w: px(1280), h: px(720) });
  box(s, 52, 58, 430, 604, C.dark, { radius: 56 });
  text(s, "Rofu Thailand\nrooftop solar and storage", 92, 170, 360, 150, { size: 34, bold: true, color: C.white, valign: "middle" });
  text(s, "Feasibility results on the measured roof: five configurations on the PEA time-of-use tariff, sized by optimisation and tested on a 20 year pro forma", 92, 350, 350, 150, { size: 17, color: C.white });
  text(s, "Prepared by Allotrope Partners\nSeptember 2026", 92, 560, 340, 60, { size: 14, color: C.pale });
  s.addNotes("Second edition of the feasibility deck. The roof has been measured from satellite imagery (seven buildings, 16,319 m2) and the cases re-run: PV only and PV with storage on roof F (the roof replaced one to two years ago) and on all seven roofs, plus the unconstrained storage case carried over from the 12 September memo. Built from the five case records under outputs/thailand_case/rofu_thailand_v2 on master. Visual style follows the Rofu tariff structure briefing (Allotrope KEEN reference deck). All money in USD at 32.5 THB per USD unless marked THB.");
}

// ---------------------------------------------------------------- 2 summary
{
  const s = standard("Summary: roof F pays alone; all roofs earn four times as much", `Headline numbers from the five workbooks of 15 September 2026. Roof F alone (${fmt0(c1.pv_kw)} kWp) returns its equity in ${c1.payback_years.toFixed(1)} years with an equity NPV of ${fmt0(c1.npv_usd)} USD; all seven roofs (${fmt0(c3.pv_kw)} kWp) with storage reach ${fmt0(c4.npv_usd)} USD. Storage is immaterial on roof F (the optimiser adds ${fmt0(c2.bess_kw)} kW / ${fmt0(c2.bess_kwh)} kWh, below any practical size) and is selected on all roofs at ${fmt0(c4.bess_kw)} kW / ${fmt0(c4.bess_kwh)} kWh. The roof still binds: the unconstrained optimum is 2,847 kWp.`);
  const stats = [
    [`${fmt0(D.roof_total_m2)} m2`, `measured roof on seven buildings; roof F (3,329 m2, replaced 1 to 2 years ago) carries ${fmt0(D.roof_f_kwp)} kWp, all roofs ${fmt0(D.roof_all_kwp)} kWp`],
    [`${fmt0(c1.pv_kw)} / ${fmt0(c3.pv_kw)} kWp`, `the two roof groups; storage is immaterial on roof F (${fmt0(c2.bess_kwh)} kWh) and selected on all roofs (${fmt0(c4.bess_kw)} kW / ${fmt0(c4.bess_kwh)} kWh)`],
    [`${fmt0(c1.year1_savings_usd / 1000)}k-${fmt0(c4.year1_savings_usd / 1000)}k USD`, "year-1 bill savings, roof F alone to all roofs with storage, against a business-as-usual bill of 843,443 USD"],
    [`${M(c1.npv_usd)}-${M(c4.npv_usd)} M USD`, `equity NPV at 11 percent over 20 years; equity IRR ${pct1(c4.equity_irr)} to ${pct1(c1.equity_irr)} on 70 percent debt`],
  ];
  stats.forEach(([v, l], i) => stat(s, 54 + i * 296, 126, 276, 168, v, l, { valueSize: 21, labelSize: 11.5 }));
  text(s, "What the analysis found", 54, 318, 600, 30, { size: 18, bold: true, color: C.dark });
  bullets(s, [
    `Roof F alone is a sound first project: ${fmt0(c1.capex_usd)} USD of capex, ${fmt0(c1.year1_savings_usd)} USD of year-1 savings, equity IRR ${pct1(c1.equity_irr)}, and almost no curtailment (${pct1(c1.curtailed_fraction)}) because the array is small against a 1.15 MW daytime load.`,
    `The other six roofs hold four fifths of the value: all roofs with storage lifts NPV from ${M(c1.npv_usd)} to ${M(c4.npv_usd)} M USD, at the cost of a condition review those roofs have not had.`,
    `Storage only earns at scale. On roof F the optimiser adds a token ${fmt0(c2.bess_kwh)} kWh; on all roofs it adds ${fmt0(c4.bess_kwh)} kWh, recovering curtailed energy (${pct1(c3.curtailed_fraction)} without storage, ${pct1(c4.curtailed_fraction)} with) and clipping the monthly peak.`,
    "Every return still scales off the 500 USD/kWp quotation, below published Thai benchmarks; the price is worth confirming before anything else.",
  ], 54, 356, 720, 300, { size: 13.5, after: 8 });
  card(s, 812, 318, 420, 332, { fill: C.dark, line: false });
  text(s, "Recommended path: two phases", 840, 340, 370, 30, { size: 16, bold: true, color: C.white });
  bullets(s, [
    `Phase 1, roof F, PV only (case 1): ${fmt0(c1.pv_kw)} kWp, ${fmt0(c1.capex_usd)} USD, NPV ${fmt0(c1.npv_usd)} USD. No structural question; can proceed to an EPC quotation now.`,
    `Phase 2, the six older roofs with storage (case 4 less case 1): about ${fmt0(c4.pv_kw - c1.pv_kw)} kWp and ${fmt0(c4.bess_kwh)} kWh more, ${fmt0(c4.capex_usd - c1.capex_usd)} USD more capex, ${fmt0(c4.npv_usd - c1.npv_usd)} USD more NPV; conditional on the roof condition review.`,
    "Reference: the unconstrained optimum (case 5) remains 2,847 kWp; the measured roof carries three quarters of it.",
  ], 840, 380, 370, 260, { size: 12, color: C.white, after: 7 });
}

// ---------------------------------------------------------------- 3 scope and method
{
  const s = standard("Scope and method", "The optimiser is REopt (NREL) at 15 minute resolution with the HiGHS solver: it chooses PV and battery sizes and the hourly dispatch that minimise the 20 year cost of electricity for the site under the PEA tariff, with no export allowed. The pro forma (proforma_vietnam engine, Thailand profile) then builds the 20 year cash flow for direct ownership: capex, financing, O&M, insurance, replacements, depreciation and CIT. This edition replaces the survey-based roof estimate of the 12 September memo with a measurement from satellite imagery and re-runs the roof cases in two groups, roof F alone and all seven roofs; the unconstrained storage case is carried over unchanged as the reference optimum. The battery price history (300 + 250 rejected; 100 + 150 selected at a 70 percent and again at a 100 percent year-10 replacement) is unchanged.");
  text(s, "Question", 54, 128, 380, 30, { size: 18, bold: true, color: C.dark });
  text(s, "How much rooftop solar, with or without battery storage, should Rofu Thailand install under its current PEA tariff, and what does the investment return over 20 years?", 54, 162, 380, 120, { size: 14 });
  text(s, "Method", 54, 300, 380, 30, { size: 18, bold: true, color: C.dark });
  bullets(s, [
    "Dispatch and sizing: REopt optimisation at 15 minute resolution, one full year of metered load, PVWatts irradiance for Phimai, no grid export.",
    "Economics: 20 year pro forma, direct ownership by the factory, 70 percent debt, Thai CIT and depreciation.",
    "Five cases: roof F and all roofs, each without and with storage, plus the unconstrained storage optimum from the memo.",
  ], 54, 336, 380, 300, { size: 13, after: 8 });

  text(s, "What changed since the 12 September memo", 490, 128, 740, 30, { size: 18, bold: true, color: C.dark });
  const steps = [
    ["1", "The roof is measured", "Seven buildings traced on satellite imagery: 16,319 m2 in total, of which roof F is 3,329 m2. The memo worked from a survey estimate of 12,960 to 16,200 m2.", `Capacity at the memo's 65 percent and 0.20 kWp/m2: ${fmt0(D.roof_f_kwp)} kWp on roof F, ${fmt0(D.roof_all_kwp)} kWp on all roofs`, C.pale2, C.ink],
    ["2", "Roof condition is known", "Roof F was replaced one to two years ago after unrepairable leaks. The other six roofs are older, no replacement is planned, and their suitability has not been assessed.", "The cases split into roof F alone and all seven roofs after a condition review", C.green2, C.white],
    ["3", "Four cases re-run, one carried over", "PV only and PV with storage on roof F and on all roofs, all other inputs as in the memo. Case 5 is the memo's unconstrained storage case, unchanged.", "Five workbooks, one per case, replace the memo's six", C.dark, C.white],
  ];
  steps.forEach(([n, t, sub, res, fill, col], i) => {
    const y = 168 + i * 162;
    box(s, 490, y, 740, 148, fill, { radius: 18 });
    text(s, n, 512, y + 18, 40, 44, { size: 30, bold: true, color: col });
    text(s, t, 566, y + 16, 640, 30, { size: 17, bold: true, color: col });
    text(s, sub, 566, y + 50, 640, 44, { size: 12.5, color: col });
    text(s, res, 566, y + 100, 640, 40, { size: 13, bold: true, color: col });
  });
}

// ---------------------------------------------------------------- 4 facility
{
  const s = standard("The facility: Rofu Thailand, Phimai", "Sources: PEA invoice June 2025; RTS data collection workbook; KTH2 electricity use; 15 minute interval data for 2025 supplied by PEA. Monthly energy from the metered series used by the optimiser (7,235,301 kWh in the year). Roof: seven buildings measured from satellite imagery in September 2026, 16,319 m2 in total; roof F was replaced one to two years ago, the others are older and unreviewed.");
  card(s, 54, 128, 420, 250);
  text(s, "Supply", 78, 146, 380, 28, { size: 17, bold: true, color: C.dark });
  rich(s, [
    { t: "Utility: ", b: true }, { t: "Provincial Electricity Authority, Phimai branch", br: true, after: 6 },
    { t: "Tariff: ", b: true }, { t: "Schedule 4.2 Large General Service, time of use, 22-33 kV, rate code 4224", br: true, after: 6 },
    { t: "Connection: ", b: true }, { t: "one grid connection, four transformers, 3,230 kVA installed (500 + 500 + 1,600 + 630)", br: true, after: 6 },
    { t: "Location: ", b: true }, { t: "Phimai district, Nakhon Ratchasima" },
  ], 78, 182, 375, 190, { size: 13 });
  card(s, 54, 398, 420, 250);
  text(s, "Roof", 78, 416, 380, 28, { size: 17, bold: true, color: C.dark });
  rich(s, [
    { t: "Measured: ", b: true }, { t: `seven buildings, ${fmt0(D.roof_total_m2)} m2 of roof from satellite imagery (next slide)`, br: true, after: 6 },
    { t: "Roof F: ", b: true }, { t: "3,329 m2, replaced one to two years ago after unrepairable leaks; the newest roof on site", br: true, after: 6 },
    { t: "Roofs A to E and G: ", b: true }, { t: "older, no replacement planned; condition to be reviewed before a solar decision" },
  ], 78, 452, 375, 180, { size: 13 });

  text(s, "Metered electricity use, 2025 (MWh per month)", 520, 128, 700, 28, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "MWh", labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], values: D.monthly_load_mwh.map((v) => Math.round(v)) }], {
    ...chartBase, x: px(520), y: px(160), w: px(710), h: px(300), barDir: "col", chartColors: [C.green2], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9, dataLabelColor: C.ink, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 850,
  });
  const stats = [
    ["7.24 GWh", "annual consumption"], ["1.21-1.38 MW", "monthly on-peak maximum demand"], ["843,443 USD", "business-as-usual bill per year (THB 27.4 million)"],
  ];
  stats.forEach(([v, l], i) => stat(s, 520 + i * 240, 480, 226, 168, v, l, { valueSize: 20 }));
}

// ---------------------------------------------------------------- 5 roof measurement
{
  const s = standard("The roof: seven buildings measured from satellite imagery", `Roof outlines traced on satellite imagery (September 2026) and measured building by building: A 2,818 m2, B 2,859, C 2,733, D 2,720, E 885, F 3,329, G 975; 16,319 m2 in total. The conversion to capacity keeps the memo's assumptions: 65 percent of the outlined area is usable (skylight strips, edges, walkways and equipment take the rest) at 0.20 kWp per usable m2, so all seven roofs carry ${fmt0(D.roof_all_kwp)} kWp and roof F alone ${fmt0(D.roof_f_kwp)} kWp. Condition: roof F, the main building at the front of the site, was replaced one to two years ago after leaks that could no longer be repaired; the other roofs are older, no replacement is planned, and their condition and suitability need a closer review before a decision. The memo's survey estimate (five roofs, 108 m long, 24 to 30 m wide: 12,960 to 16,200 m2 gross, 1,685 to 2,106 kWp) is superseded by the measurement, which sits at the top of that range.`);
  s.addImage({ data: roofImg, x: px(54), y: px(126), w: px(700), h: px(374) });
  text(s, "Satellite view with the seven roof outlines (A to G). Roof F, front of the site, is the replaced roof.", 54, 504, 700, 22, { size: 10.5, color: C.muted, italic: true });
  const chain = [`${fmt0(D.roof_total_m2)} m2 outlined`, "x 65% usable", "x 0.20 kWp/m2", `= ${fmt0(D.roof_all_kwp)} kWp all roofs`];
  chain.forEach((t, i) => {
    const x = 54 + i * 178;
    box(s, x, 534, 166, 50, i === chain.length - 1 ? C.dark : C.pale, { radius: 12 });
    text(s, t, x + 6, 534, 154, 50, { size: 12, bold: true, color: i === chain.length - 1 ? C.white : C.ink, align: "center", valign: "middle" });
  });
  text(s, `Roof F alone: 3,329 m2 x 65% x 0.20 = ${fmt0(D.roof_f_kwp)} kWp. The memo's survey estimate (five roofs, 12,960 to 16,200 m2 gross, 1,685 to 2,106 kWp) is superseded; the measured total sits at the top of that range.`, 54, 596, 700, 60, { size: 11.5, color: C.ink });

  const H = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.header }, align: "center" } });
  const cond = { A: "older, to be reviewed", B: "older, to be reviewed", C: "older, to be reviewed", D: "older, to be reviewed", E: "older, to be reviewed", F: "new (1 to 2 years)", G: "older, to be reviewed" };
  const rows = [[H("Roof"), H("Area (m2)"), H("kWp"), H("Condition")]];
  D.roofs.forEach((r) => {
    const isF = r.id === "F";
    const opt = { bold: isF, fill: { color: isF ? C.pale : C.white } };
    rows.push([{ text: r.id, options: { ...opt, align: "center" } }, { text: r.m2.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }), options: { ...opt, align: "right" } }, { text: fmt0(r.kwp), options: { ...opt, align: "right" } }, { text: cond[r.id], options: { ...opt, align: "left" } }]);
  });
  rows.push([{ text: "Total", options: { bold: true, fill: { color: C.pale2 }, align: "center" } }, { text: fmt0(D.roof_total_m2), options: { bold: true, fill: { color: C.pale2 }, align: "right" } }, { text: fmt0(D.roof_all_kwp), options: { bold: true, fill: { color: C.pale2 }, align: "right" } }, { text: "seven buildings", options: { bold: true, fill: { color: C.pale2 } } }]);
  s.addTable(rows, {
    x: px(790), y: px(126), w: px(442), colW: [px(56), px(100), px(86), px(200)], fontFace: FONT, fontSize: 11, color: C.ink, border: { type: "solid", pt: 0.5, color: C.line }, rowH: px(28), valign: "middle", margin: [1, 5, 1, 5],
  });
  card(s, 790, 412, 442, 244, { fill: C.dark, line: false });
  text(s, "What the roof condition means", 812, 426, 400, 28, { size: 16, bold: true, color: C.white });
  bullets(s, [
    "Roof F is the one surface that can carry panels without a structural question: new sheeting, no leak history, about one fifth of the total area.",
    "Roofs A to E and G hold the other four fifths. Their age and condition have not been assessed; a structural and sheeting review is a precondition, not a formality.",
    "The cases therefore come in two groups: roof F alone, and all seven roofs once the review clears them.",
  ], 812, 460, 400, 190, { size: 11, color: C.white, after: 6 });
}

// ---------------------------------------------------------------- 6 load profile and tariff clock
{
  const s = standard("Daily load against the tariff clock and the solar day", "Average load by hour across 2025 from the metered 15 minute series. The plant runs two shifts with a lunch dip and an evening step-down; weekday on-peak energy is billed from 09:00 to 22:00, the demand charge on the single highest on-peak interval of the month. Solar generation falls between about 06:00 and 18:00, so it overlaps the first nine hours of the peak window but none of the evening.");
  text(s, "Average load by hour, 2025 (kW)", 54, 124, 700, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.line, [{ name: "kW", labels: Array.from({ length: 24 }, (_, h) => String(h).padStart(2, "0")), values: D.avg_load_by_hour_kw.map((v) => Math.round(v)) }], {
    ...chartBase, x: px(54), y: px(152), w: px(760), h: px(300), chartColors: [C.dark], lineSize: 2.5, lineDataSymbol: "none", valAxisMinVal: 0, valAxisMaxVal: 1400, catAxisLabelFontSize: 9, valAxisTitle: "kW", showValAxisTitle: false,
  });
  // tariff clock and solar day bars (00-24 across the chart's plot width)
  const x0 = 200, x1 = 814, W = x1 - x0;
  const hx = (h) => x0 + (W * h) / 24;
  text(s, "Weekday tariff", 54, 470, 140, 34, { size: 12, bold: true, color: C.dark, valign: "middle" });
  box(s, hx(0), 470, hx(9) - hx(0), 34, C.pale2, { round: false });
  box(s, hx(9), 470, hx(22) - hx(9), 34, C.orange, { round: false });
  box(s, hx(22), 470, hx(24) - hx(22), 34, C.pale2, { round: false });
  text(s, "off-peak 2.6037", hx(0) + 6, 470, hx(9) - hx(0) - 8, 34, { size: 10, color: C.ink, valign: "middle" });
  text(s, "peak 4.1839 THB/kWh + monthly demand charge", hx(9) + 8, 470, hx(22) - hx(9) - 12, 34, { size: 9.5, color: C.white, valign: "middle" });
  text(s, "off", hx(22) + 4, 470, hx(24) - hx(22) - 6, 34, { size: 9.5, color: C.ink, valign: "middle" });
  text(s, "Solar output", 54, 514, 140, 34, { size: 12, bold: true, color: C.dark, valign: "middle" });
  box(s, hx(6), 514, hx(18) - hx(6), 34, C.yellow, { round: false });
  text(s, "generation 06:00 to 18:00, peak 11:00 to 14:00", hx(6) + 8, 514, hx(18) - hx(6) - 12, 34, { size: 9.5, color: C.ink, valign: "middle" });
  [0, 6, 9, 12, 18, 22, 24].forEach((h) => text(s, String(h).padStart(2, "0") + ":00", hx(h) - 22, 552, 44, 18, { size: 9, color: C.muted, align: "center" }));
  text(s, "Weekends and Thai public holidays are off-peak all day.", 54, 580, 760, 24, { size: 11, color: C.muted, italic: true });

  card(s, 850, 124, 382, 470, { fill: C.dark, line: false });
  text(s, "What this means for the design", 876, 146, 340, 30, { size: 17, bold: true, color: C.white });
  bullets(s, [
    "Solar displaces the 4.18 THB peak energy from 09:00 to 18:00 on weekdays, the most valuable kWh on the bill.",
    "The 08:00 to 16:00 load plateau of about 1.15 MW is above the roof-limited array's average output, so most weekday solar is used on site.",
    "The demand charge is set by one interval a month; PV alone cannot guarantee a lower peak, storage can.",
    "Weekends and holidays are off-peak all day and the load is lower: that is where curtailment happens without export.",
  ], 876, 190, 336, 390, { size: 12.5, color: C.white, after: 10 });
}

// ---------------------------------------------------------------- 7 tariff
{
  const s = standard("The PEA tariff: five building blocks, one monthly peak", "Rates verified line by line against the June 2025 invoice (rate code 4224, 22-33 kV): the full bill reconstructs from these values to within 0.01 THB. June 2025: 631,580 kWh, 1,368 kW on-peak maximum, Ft 0.1972 THB/kWh, pre-VAT subtotal THB 2,407,767, amount due THB 2.58 million. Ft is revised every four months: 0.3672 (Jan-Apr 2025), 0.1972 (May-Aug 2025), 0.1572 (Sep-Dec 2025), 0.0972 (Jan-Apr 2026), 0.1623 (May-Aug 2026). A power-factor charge of 56.07 THB per kVAR applies above the tariff allowance; monthly kVAR data were not supplied, so it is not modelled.");
  const blocks = [
    ["Peak energy", "4.1839 THB/kWh", "weekdays 09:00-22:00", C.orange, C.white],
    ["Off-peak energy", "2.6037 THB/kWh", "nights, weekends, holidays", C.green2, C.white],
    ["On-peak demand", "132.93 THB/kW a month", "highest on-peak interval", C.yellow, C.ink],
    ["Ft adjustment", "0.10-0.37 THB/kWh", "all kWh; reset every four months", C.red, C.white],
    ["Service and VAT", "312.24 THB/month", "then 7 percent VAT on the subtotal", C.pale2, C.ink],
  ];
  blocks.forEach(([t, v, sub, fill, col], i) => {
    const x = 54 + i * 238;
    box(s, x, 130, 222, 134, fill, { radius: 18 });
    text(s, t, x + 14, 140, 194, 30, { size: 15, bold: true, color: col, align: "center", valign: "middle" });
    text(s, v, x + 10, 176, 202, 32, { size: 13, bold: true, color: col, align: "center", valign: "middle" });
    text(s, sub, x + 14, 214, 194, 42, { size: 11, color: col, align: "center", valign: "top" });
  });
  text(s, "June 2025 invoice: THB 2.58 million", 54, 290, 560, 30, { size: 16, bold: true, color: C.dark });
  const peakEnergy = 2407767 * 0.50, offEnergy = 2407767 * 0.37, demand = 1368 * 132.93, ft = 631580 * 0.1972;
  s.addChart(pres.ChartType.doughnut, [{ name: "Bill", labels: ["Peak energy", "Off-peak energy", "Demand", "Ft"], values: [Math.round(peakEnergy), Math.round(offEnergy), Math.round(demand), Math.round(ft)] }], {
    ...chartBase, x: px(54), y: px(322), w: px(330), h: px(330), chartColors: [C.orange, C.green2, C.yellow, C.red], holeSize: 55, showLegend: true, legendPos: "r", legendFontSize: 10, legendColor: C.ink, showPercent: true, dataLabelFontSize: 9, dataLabelColor: C.white, showLabel: false,
  });
  card(s, 410, 322, 380, 330);
  text(s, "Pre-VAT subtotal THB 2,407,767", 432, 340, 340, 26, { size: 13, bold: true, color: C.dark });
  rich(s, [
    { t: "631,580 kWh", b: true }, { t: " billed in the month", br: true, after: 6 },
    { t: "1,368 kW", b: true }, { t: " on-peak maximum demand, the single interval that sets THB 181,848 of demand charge", br: true, after: 6 },
    { t: "Ft 0.1972 THB/kWh", b: true }, { t: " on every kWh in that period", br: true, after: 6 },
    { t: "Energy is 87 percent of the bill;", b: true }, { t: " demand 8 percent, Ft 5 percent; the service charge is negligible" },
  ], 432, 372, 340, 260, { size: 12.5 });
  card(s, 820, 290, 412, 362, { fill: C.dark, line: false });
  text(s, "Why the structure matters", 846, 310, 360, 30, { size: 17, bold: true, color: C.white });
  bullets(s, [
    "Solar earns the peak rate on weekdays and the off-peak rate on weekends and holidays; the blended value of a solar kWh is well below the peak rate.",
    "One monthly interval sets the demand charge, so a cloudy quarter hour can wipe out a month of peak shaving unless a battery covers it.",
    "Ft moves every four months and is outside the site's control; the model carries 3 percent a year tariff escalation and does not forecast Ft.",
  ], 846, 352, 366, 290, { size: 12.5, color: C.white, after: 10 });
}

// ---------------------------------------------------------------- 8 assumptions technical and cost
{
  const s = standard("Assumptions (1): technical and cost inputs", "Roof conversion as in the September memo: 65 percent of the outlined area usable at 0.20 kWp per usable m2, which is 0.13 kWp per outlined m2. Cost inputs from Keen's quotation: 500 USD/kWp installed for PV (the top of the confirmed C&I rooftop range), 100 USD/kW plus 150 USD/kWh for the battery. O&M was supplied at 1.5 percent of PV capex (7.50 USD/kWp per year); the optimiser rounds cost parameters to whole dollars and applied 8.00, which the workbooks disclose. Battery O&M 1 percent of its install cost a year. The year-10 whole-system replacement at 100 percent of install cost is the conservative case; the PV inverter replacement at 10 percent of PV capex in year 11 is an Allotrope convention awaiting confirmation.");
  const rows = [
    [{ text: "Item", options: { bold: true, color: C.white, fill: { color: C.header } } }, { text: "Value", options: { bold: true, color: C.white, fill: { color: C.header } } }, { text: "Basis", options: { bold: true, color: C.white, fill: { color: C.header } } }],
    ["Usable roof share", "65 percent of the outlined roof area", "memo assumption kept; skylights, edges, walkways and equipment take the rest"],
    ["Installed power density", "0.20 kWp per usable m2", "memo assumption kept; equivalent to 0.13 kWp per outlined m2"],
    ["PV installed cost", "500 USD/kWp", "Keen quotation; below published Thai benchmarks (see slide 15)"],
    ["Battery installed cost", "100 USD/kW + 150 USD/kWh", "Keen quotation; 325 USD/kW installed for a 1.5 hour system"],
    ["Battery minimum duration", "1.5 hours", "provisional"],
    ["PV operating cost", "8.00 USD/kWp per year", "supplied at 7.50 (1.5 percent of capex); optimiser rounds to whole dollars"],
    ["Battery operating cost", "1 percent of install cost per year", "optimiser convention"],
    ["Insurance", "0.5 percent of capex per year", "provisional"],
    ["Specific yield, year 1", "1,498 kWh/kWp", "PVWatts irradiance for Phimai: 2,049 kWh/m2 plane of array; performance ratio 0.731; tilt 15 degrees"],
    ["PV degradation", "0.5 percent per year", "optimiser default"],
    ["Battery replacement", "year 10, 100 percent of install cost, whole system", "conservative case; capitalised and depreciated over 5 years"],
    ["PV inverter replacement", "year 11, 10 percent of PV capex", "Allotrope convention, provisional"],
    ["Grid export", "none", "strict no-export site; surplus is curtailed"],
    ["Grid connection, power factor mitigation, permit fees", "excluded from capex", "to be added when quoted"],
  ];
  s.addTable(rows, {
    x: px(54), y: px(126), w: px(1178), colW: [px(300), px(300), px(578)], fontFace: FONT, fontSize: 11, color: C.ink, border: { type: "solid", pt: 0.5, color: C.line }, fill: { color: C.white }, rowH: px(33), valign: "middle", margin: [2, 6, 2, 6], autoPage: false,
  });
}

// ---------------------------------------------------------------- 9 assumptions financial and scope
{
  const s = standard("Assumptions (2): financing, tax and scope", "Discount rate 11 percent (client-confirmed; a Thai rooftop developer cost of equity, on the conservative side for a factory investing in its own roof). Debt 70 percent at 6.5 percent over 10 years, provisional: the rate tracks Thai commercial bank MLR at end 2025; the fraction and tenor are placeholders pending confirmation. Emissions are an Allotrope calculation: avoided grid import times the TGO grid factor of 0.4750 kg CO2e per kWh (2022-2024 vintage, effective 1 January 2026); the optimiser's own emissions outputs are built on US datasets and are not used.");
  const left = [
    ["Project life", "20 years"], ["Discount rate", "11 percent, equity NPV basis"], ["Debt", "70 percent of capex, 6.5 percent, 10 years, level payments"],
    ["Exchange rate", "32.5 THB per USD, planning rate"], ["Corporate income tax", "20 percent flat, no incentive regime"],
    ["Depreciation", "5 year machinery life, PV and battery alike"], ["Tariff escalation", "3 percent a year on the PEA bill (provisional)"], ["O&M escalation", "3 percent a year"], ["VAT", "7 percent on the bill"],
  ];
  card(s, 54, 126, 600, 470);
  text(s, "Financing and tax", 78, 144, 540, 28, { size: 17, bold: true, color: C.dark });
  left.forEach(([k, v], i) => {
    const y = 182 + i * 38;
    text(s, k, 78, y, 200, 32, { size: 12.5, bold: true, color: C.ink, valign: "middle" });
    text(s, v, 286, y, 350, 32, { size: 12.5, color: C.ink, valign: "middle" });
    if (i < left.length - 1) line(s, 78, y + 35, 630, y + 35, C.gray, 0.75);
  });
  card(s, 686, 126, 546, 200, { fill: C.dark, line: false });
  text(s, "Ownership structure", 710, 144, 500, 28, { size: 17, bold: true, color: C.white });
  text(s, "Direct ownership: the factory invests in its own roof and keeps the whole avoided PEA bill. No ESCO discount, no third-party developer margin, no new-project tax incentive. Returns are equity returns after debt service and CIT.", 710, 178, 500, 130, { size: 12.5, color: C.white });
  card(s, 686, 346, 546, 250);
  text(s, "Emissions and scope", 710, 364, 500, 28, { size: 17, bold: true, color: C.dark });
  bullets(s, [
    "Avoided emissions: avoided grid import multiplied by 0.4750 kg CO2e per kWh (Thailand Greenhouse Gas Management Organization, 2022-2024 grid mix).",
    "Excluded at the client's direction: grid connection cost, power factor mitigation (no kVAR data supplied), permit and licence fees (no published schedule).",
    "Fifteen inputs are provisional and marked as such in the workbooks; the ones that move the answer are the usable roof share, the debt terms and the insurance rate (Appendix A).",
  ], 710, 398, 500, 190, { size: 11.5, after: 6 });
  text(s, "All results are before grid connection, permitting and power-factor costs; add them when quoted.", 54, 616, 1178, 26, { size: 12, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 10 the five cases
{
  const s = standard("Five configurations were optimised", `Cases 1 and 2 cap the array at roof F (${fmt0(D.roof_f_kwp)} kWp), cases 3 and 4 at all seven roofs (${fmt0(D.roof_all_kwp)} kWp); the even-numbered cases let the optimiser add storage up to 4 MW / 16 MWh and choose its size. Case 5 is the memo's unconstrained storage case (PV free up to the 3,230 kVA connection), carried over as the reference optimum; the memo's three survey-width cases and its unconstrained PV-only case are retired. All five solved to optimality with every other input as in the memo: 500 USD/kWp, 100 USD/kW plus 150 USD/kWh, no export, direct ownership, 70 percent debt.`);
  const defs = [
    ["1", "Roof F", `PV capped at ${fmt0(D.roof_f_kwp)} kWp (3,329 m2)`, "no storage", C.pale2, C.ink],
    ["2", "Roof F, with storage", `PV capped at ${fmt0(D.roof_f_kwp)} kWp`, "storage sized by the optimiser", C.green2, C.white],
    ["3", "All roofs", `PV capped at ${fmt0(D.roof_all_kwp)} kWp (16,319 m2)`, "no storage", C.pale2, C.ink],
    ["4", "All roofs, with storage", `PV capped at ${fmt0(D.roof_all_kwp)} kWp`, "storage sized by the optimiser", C.green2, C.white],
    ["5", "No roof limit, with storage", "PV free up to the 3,230 kVA connection", "storage sized by the optimiser: the memo's reference optimum", C.dark, C.white],
  ];
  defs.forEach(([n, t, pv, st, fill, col], i) => {
    const x = 54 + (i % 3) * 396, y = 130 + Math.floor(i / 3) * 150;
    box(s, x, y, 380, 132, fill, { radius: 18 });
    text(s, n, x + 20, y + 16, 44, 48, { size: 30, bold: true, color: col });
    text(s, t, x + 76, y + 18, 290, 30, { size: 16, bold: true, color: col });
    text(s, pv, x + 76, y + 54, 290, 36, { size: 12, color: col });
    text(s, st, x + 76, y + 92, 290, 36, { size: 12, bold: true, color: col });
  });
  card(s, 846, 280, 386, 132, { fill: C.white, line: true });
  text(s, "Two roof groups", 868, 292, 350, 26, { size: 14, bold: true, color: C.dark });
  text(s, "Roof F is one fifth of the measured area and the only roof without a structural question today. All roofs is the full site once the six older roofs pass a condition review.", 868, 320, 350, 86, { size: 11.5, color: C.ink });
  card(s, 54, 440, 1178, 200);
  text(s, "How the capacity caps are built", 78, 458, 500, 28, { size: 16, bold: true, color: C.dark });
  const chain = ["Roof outlines on satellite imagery", "x 65% usable", "x 0.20 kWp per m2", `Roof F: 3,329 m2 = ${fmt0(D.roof_f_kwp)} kWp`, `All roofs: 16,319 m2 = ${fmt0(D.roof_all_kwp)} kWp`];
  chain.forEach((t, i) => {
    const x = 78 + i * 228;
    box(s, x, 498, 212, 52, i >= chain.length - 2 ? C.dark : C.pale, { radius: 12 });
    text(s, t, x + 8, 498, 196, 52, { size: 12, bold: true, color: i >= chain.length - 2 ? C.white : C.ink, align: "center", valign: "middle" });
  });
  text(s, "The memo's optimum with no roof limit is 2,847 kWp with storage; the full measured roof carries about three quarters of that, so the roof still binds. A layout drawing on the confirmed roofs will replace the 65 percent share with a panel count.", 78, 566, 1130, 56, { size: 12.5, color: C.ink });
}

// ---------------------------------------------------------------- 11 results table
{
  const s = standard("Results: the five cases side by side", `Figures from the five pro forma workbooks (15 September 2026). Financing throughout is 70 percent debt at 6.5 percent over 10 years, 20 year life, 11 percent discount rate. Case 1 equity ${fmt0(c1.equity_usd)} USD against ${fmt0(c1.debt_usd)} USD of debt; case 4 equity ${fmt0(c4.equity_usd)} USD against ${fmt0(c4.debt_usd)} USD. Grid offset is on the memo's grid-to-load basis; the workbooks' figure also nets grid-to-storage and reads lower for the storage cases. Equity IRR falls as the system grows because each additional kilowatt is pushed further from the load; NPV, not IRR, is the figure to size on.`);
  const H = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.header }, align: "center" } });
  const rows = [[H("Case"), H("PV (kWp)"), H("Storage"), H("Capex (USD)"), H("Year-1 savings (USD)"), H("Grid offset"), H("tCO2e / yr"), H("Equity IRR"), H("Equity NPV (USD)")]];
  cases.forEach((c) => {
    const bold = c.n === 1 || c.n === 4;
    const opt = { bold, fill: { color: bold ? C.pale : C.white }, color: c.n === 5 ? C.muted : C.ink };
    rows.push([
      { text: `${c.n}. ${c.label}`, options: { ...opt, align: "left" } },
      { text: fmt0(c.pv_kw), options: { ...opt, align: "right" } },
      { text: c.bess_kwh ? `${fmt0(c.bess_kw)} kW / ${fmt0(c.bess_kwh)} kWh` : "none", options: { ...opt, align: "center" } },
      { text: fmt0(c.capex_usd), options: { ...opt, align: "right" } },
      { text: fmt0(c.year1_savings_usd), options: { ...opt, align: "right" } },
      { text: pct1(c.grid_offset_to_load), options: { ...opt, align: "right" } },
      { text: fmt0(c.tco2e), options: { ...opt, align: "right" } },
      { text: pct1(c.equity_irr), options: { ...opt, align: "right" } },
      { text: fmt0(c.npv_usd), options: { ...opt, align: "right" } },
    ]);
  });
  s.addTable(rows, {
    x: px(54), y: px(130), w: px(1178), colW: [px(220), px(90), px(190), px(120), px(140), px(90), px(90), px(80), px(158)], fontFace: FONT, fontSize: 11.5, color: C.ink, border: { type: "solid", pt: 0.5, color: C.line }, rowH: px(38), valign: "middle", margin: [2, 6, 2, 6],
  });
  text(s, "Reading the table", 54, 400, 400, 28, { size: 16, bold: true, color: C.dark });
  bullets(s, [
    `Roof F alone (case 1) returns its equity in ${c1.payback_years.toFixed(1)} years; its ${fmt0(c1.pv_kw)} kWp are almost fully used on site (${pct1(c1.curtailed_fraction)} curtailed).`,
    `All roofs (case 3) multiplies capex by ${(c3.capex_usd / c1.capex_usd).toFixed(1)} and NPV by ${(c3.npv_usd / c1.npv_usd).toFixed(1)}; the marginal kilowatts are used less and IRR falls from ${pct1(c1.equity_irr)} to ${pct1(c3.equity_irr)}.`,
    `Storage on roof F (case 2) is a token ${fmt0(c2.bess_kwh)} kWh worth ${fmt0(c2.npv_usd - c1.npv_usd)} USD of NPV: not a project. On all roofs (case 4) it adds ${fmt0(c4.capex_usd - c3.capex_usd)} USD of capex and ${fmt0(c4.npv_usd - c3.npv_usd)} USD of NPV.`,
    `Case 5, the unconstrained optimum from the memo, is shown for reference: the measured roof stops about ${fmt0(c5.pv_kw - c4.pv_kw)} kWp short of it.`,
  ], 54, 434, 1178, 200, { size: 12.5, after: 7 });
  text(s, "Grid offset on the memo's grid-to-load basis. The memo's cases 1 to 4 (survey-based roof widths) are retired; case 5 here is the memo's case 6, unchanged.", 54, 600, 1178, 40, { size: 11, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 12 NPV and IRR chart
{
  const s = standard("Bigger systems return more in total, less per dollar", `Equity NPV at 11 percent and equity IRR from the five workbooks. NPV rises with size from ${fmt0(c1.npv_usd)} USD on roof F to ${fmt0(c4.npv_usd)} USD on all roofs with storage and ${fmt0(c5.npv_usd)} USD at the unconstrained optimum; IRR falls from ${pct1(c1.equity_irr)} to ${pct1(c5.equity_irr)}. Cases 1 and 2 are indistinguishable on both measures: the roof F battery is a rounding difference.`);
  text(s, "Equity NPV (USD, 20 years at 11 percent)", 54, 124, 600, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "Equity NPV", labels: cases.map((c) => `${c.n}. ${c.label}`), values: cases.map((c) => Math.round(c.npv_usd)) }], {
    ...chartBase, x: px(54), y: px(154), w: px(620), h: px(420), barDir: "bar", catAxisOrientation: "maxMin", chartColors: [C.green2], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, dataLabelFormatCode: "#,##0", valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 2300000, catAxisLabelFontSize: 10,
  });
  text(s, "Equity IRR", 720, 124, 500, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "Equity IRR", labels: cases.map((c) => `${c.n}`), values: cases.map((c) => Math.round(1000 * c.equity_irr) / 10) }], {
    ...chartBase, x: px(720), y: px(154), w: px(512), h: px(230), barDir: "col", chartColors: [C.orange], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, dataLabelFormatCode: "0.0\"%\"", valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 90,
  });
  card(s, 720, 404, 512, 170, { fill: C.dark, line: false });
  text(s, "Capex and equity by case (USD)", 744, 420, 470, 26, { size: 13, bold: true, color: C.white });
  rich(s, cases.flatMap((c, i) => [{ t: `${c.n}: `, b: true, c: C.white }, { t: `capex ${fmt0(c.capex_usd)}, equity ${fmt0(c.equity_usd)}, debt ${fmt0(c.debt_usd)}`, c: C.white, br: i < cases.length - 1 }]), 744, 450, 470, 120, { size: 11.5 });
  text(s, `Simple equity payback runs from ${c1.payback_years.toFixed(1)} years (case 1) to ${c5.payback_years.toFixed(1)} years (case 5). These are consequences of the 500 USD/kWp input; see slide 15.`, 54, 590, 1178, 40, { size: 12, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 13 what storage does
{
  const d4 = D.dispatch["4"];
  const s = standard("What storage buys, and why it needs the full roof", `Case 4 average day across 2025 from the optimiser's dispatch: PV serves the daytime load and charges the battery late morning when the array would otherwise be curtailed; the battery also charges from the grid off-peak overnight, discharges on the morning ramp (about 37 percent of its output) and into the evening on-peak hours (about 56 percent). Case 4, annual average over the analysis period (levelised dispatch): storage to load ${fmt0(c4.storage_to_load_kwh / 1000)} MWh, PV to storage ${fmt0(c4.pv_to_storage_kwh / 1000)} MWh, grid to storage ${fmt0(c4.grid_to_storage_kwh / 1000)} MWh, PV curtailed ${fmt0(c4.curtailed_kwh / 1000)} MWh (${pct1(c4.curtailed_fraction)}), demand charge savings ${fmt0(c4.demand_savings_usd)} USD. Comparing cases 3 and 4 (identical arrays): curtailment falls from ${pct1(c3.curtailed_fraction)} to ${pct1(c4.curtailed_fraction)} when storage is added. On roof F (cases 1 and 2) the array is small against the load, curtailment is ${pct1(c1.curtailed_fraction)}, and the optimiser adds only ${fmt0(c2.bess_kw)} kW / ${fmt0(c2.bess_kwh)} kWh for ${fmt0(c2.demand_savings_usd - c1.demand_savings_usd)} USD a year of demand charge: below any practical battery size, so roof F is treated as PV only.`);
  text(s, "Case 4, average day: who serves the load (kW by hour)", 54, 124, 700, 26, { size: 15, bold: true, color: C.dark });
  const hours = Array.from({ length: 24 }, (_, h) => String(h).padStart(2, "0"));
  s.addChart(pres.ChartType.bar, [
    { name: "PV to load", labels: hours, values: d4.pv_to_load.map((v) => Math.round(v)) },
    { name: "Battery to load", labels: hours, values: d4.storage_to_load.map((v) => Math.round(v)) },
    { name: "Grid to load", labels: hours, values: d4.grid_to_load.map((v) => Math.round(v)) },
  ], {
    ...chartBase, x: px(54), y: px(154), w: px(760), h: px(330), barDir: "col", barGrouping: "stacked", barGapWidthPct: 40, chartColors: [C.yellow, C.green2, C.pale2], showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: C.ink, catAxisLabelFontSize: 9, valAxisMinVal: 0, valAxisMaxVal: 1300,
  });
  text(s, `Late morning the array also charges the battery (up to ${fmt0(Math.max(...d4.pv_to_storage))} kW on the average day) and still curtails up to ${fmt0(Math.max(...d4.pv_curtailed))} kW; the battery gives it back on the morning ramp and in the evening, inside the peak window, and tops up from the grid overnight at the off-peak rate.`, 54, 494, 760, 44, { size: 11.5, color: C.muted, italic: true });
  const stats = [
    [`${fmt0(c4.storage_to_load_kwh / 1000)} MWh / yr`, "delivered by the case 4 battery to the load: about 56 percent in the evening peak hours (17:00 to 22:00), 37 percent on the morning ramp", C.dark, C.white],
    [`${pct1(c3.curtailed_fraction)} to ${pct1(c4.curtailed_fraction)}`, "curtailment on all roofs without and with storage (cases 3 and 4): energy that would otherwise be lost", C.green2, C.white],
    [`${fmt0(c2.bess_kwh)} kWh on roof F`, `all the optimiser adds to the roof F array (case 2), for ${fmt0(c2.npv_usd - c1.npv_usd)} USD of NPV: storage needs the full roof to earn`, C.white, C.dark],
  ];
  stats.forEach(([v, l, fill, col], i) => {
    const y = 124 + i * 150;
    card(s, 850, y, 382, 134, { fill, line: fill === C.white });
    text(s, v, 874, y + 14, 340, 44, { size: 24, bold: true, color: col === C.white ? C.white : C.dark, valign: "middle" });
    text(s, l, 874, y + 62, 340, 66, { size: 11.5, color: col === C.white ? C.white : C.muted });
  });
  text(s, "The storage conclusion from the memo stands, with a size condition: the battery earns from curtailed energy and the monthly peak, and there is little of either until the array is large against the load.", 54, 576, 1178, 40, { size: 12.5, color: C.ink, bold: true });
}

// ---------------------------------------------------------------- 14 year-10 replacement and DSCR
{
  const s = standard("The year-10 battery replacement meets the final loan year", `Debt service coverage by year from the case 4 and case 5 workbooks (case 1, PV only, for comparison). The whole battery system is replaced in year 10 at 100 percent of install cost, the same year as the last of ten level debt payments. Case 4, year 10: cash available for debt service ${fmt0(c4.cfads_year10_usd)} USD against a payment of ${fmt0(c4.debt_service_year10_usd)} USD after a ${fmt0(c4.replacement_year10_usd)} USD replacement: coverage ${c4.dscr_by_year[9].toFixed(2)} in that one year against ${c4.avg_dscr.toFixed(2)} on average, still above a typical 1.2 covenant. Case 5, with a battery three times larger, is the case that breaks: ${fmt0(c5.cfads_year10_usd)} against ${fmt0(c5.debt_service_year10_usd)} USD, coverage ${c5.dscr_by_year[9].toFixed(2)}. Neither a reserve nor a longer tenor has been modelled, deliberately, so the raw effect is visible.`);
  text(s, "Debt service coverage ratio, years 1 to 10", 54, 124, 700, 26, { size: 15, bold: true, color: C.dark });
  const years = Array.from({ length: 10 }, (_, i) => `Y${i + 1}`);
  s.addChart(pres.ChartType.line, [
    { name: "Case 1: roof F, PV only", labels: years, values: c1.dscr_by_year.slice(0, 10).map((v) => Math.round(v * 100) / 100) },
    { name: "Case 4: all roofs, with storage", labels: years, values: c4.dscr_by_year.slice(0, 10).map((v) => Math.round(v * 100) / 100) },
    { name: "Case 5: no roof limit, with storage", labels: years, values: c5.dscr_by_year.slice(0, 10).map((v) => Math.round(v * 100) / 100) },
  ], {
    ...chartBase, x: px(54), y: px(154), w: px(760), h: px(360), chartColors: [C.pale2, C.green2, C.orange], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 6, showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: C.ink, valAxisMinVal: 0, valAxisMaxVal: 4, showValue: true, dataLabelFontSize: 9, dataLabelColor: C.ink, dataLabelPosition: "t", dataLabelFormatCode: "0.00",
  });
  card(s, 850, 124, 382, 470, { fill: C.dark, line: false });
  text(s, "A structuring point", 874, 146, 340, 30, { size: 17, bold: true, color: C.white });
  bullets(s, [
    `Case 4, year 10: cash available for debt service ${fmt0(c4.cfads_year10_usd)} USD against ${fmt0(c4.debt_service_year10_usd)} USD of debt service after a ${fmt0(c4.replacement_year10_usd)} USD battery replacement; coverage ${c4.dscr_by_year[9].toFixed(2)} in that year.`,
    `Still above a typical 1.2 covenant; the memo's unconstrained case (5) with a ${fmt0(c5.bess_kwh)} kWh battery is the one that falls to ${c5.dscr_by_year[9].toFixed(2)}. A reserve built in years 1 to 9, or a tenor set so the replacement falls after the final payment, removes the dip in either case.`,
    `Roof F alone has no such year: PV only, coverage above ${floor1(c1.min_dscr)} throughout; the inverter replacement (10 percent of PV capex) falls in year 11, after the loan.`,
    "The whole-system replacement at 100 percent of install cost in year 10 is the memo's conservative case; a partial or cheaper replacement shrinks the dip.",
  ], 874, 188, 336, 400, { size: 11.5, color: C.white, after: 7 });
  text(s, `Average coverage over the loan: case 1 ${c1.avg_dscr.toFixed(2)}, case 4 ${c4.avg_dscr.toFixed(2)}, case 5 ${c5.avg_dscr.toFixed(2)}. PV inverter replacement follows in year 11, after the loan.`, 54, 530, 760, 44, { size: 11.5, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 15 capex and export
{
  const s = standard("Two inputs move the answer: capital cost and export", `Benchmarks: Krungsri Research puts Thai C&I rooftop at THB 20,000 to 25,000 per kWp (615 to 769 USD at 32.5); Farungsang, Varquez and Tokimatsu (MDPI Sustainability 17(15):7052, August 2025) assume 767 USD/kWp. The 500 USD/kWp used here is Keen's quotation, about 19 percent below the bottom of that range; a current quotation is better evidence than a published average, but every return in the deck scales off it. Curtailment: the site is modelled with no export, so surplus generation is lost: ${pct1(c1.curtailed_fraction)} on roof F, ${pct1(c3.curtailed_fraction)} on all roofs without storage, ${pct1(c4.curtailed_fraction)} with. If export at any reasonable price can be negotiated, the larger systems improve and the optimal size rises. No price was assumed because none is known.`);
  text(s, "Installed PV cost, USD per kWp", 54, 124, 560, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "USD/kWp", labels: ["Keen quotation", "Krungsri low", "Krungsri high", "MDPI 2025"], values: [500, 615, 769, 767] }], {
    ...chartBase, x: px(54), y: px(154), w: px(560), h: px(300), barDir: "col", chartColors: [C.dark, C.pale2, C.pale2, C.pale2], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 900, catAxisLabelFontSize: 10,
  });
  text(s, `The 500 USD/kWp price is used as given. It is why simple equity payback is ${c1.payback_years.toFixed(1)} years on roof F; a quotation at 650 USD/kWp would change the picture materially. Confirming the price, on roof F first, is worth more than refining anything else in the analysis.`, 54, 464, 560, 90, { size: 12.5, color: C.ink });
  text(s, "Share of production curtailed (no export)", 670, 124, 560, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "Curtailed", labels: cases.map((c) => `${c.n}`), values: cases.map((c) => Math.round(1000 * c.curtailed_fraction) / 10) }], {
    ...chartBase, x: px(670), y: px(154), w: px(560), h: px(300), barDir: "col", chartColors: [C.orange], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, dataLabelFormatCode: "0.0\"%\"", valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 16, catAxisLabelFontSize: 10,
  });
  text(s, "Roof F alone wastes almost nothing because the array is small against the daytime load. Curtailment appears with the full roof and is where an export price, if PEA or a third party offers one, would raise both the value of the larger systems and the optimal size; the question is left open rather than priced by assumption.", 670, 464, 560, 90, { size: 12.5, color: C.ink });
  text(s, "Cases: 1 roof F, 2 roof F with storage, 3 all roofs, 4 all roofs with storage, 5 no roof limit with storage.", 54, 580, 1178, 24, { size: 11, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 16 recommendation
{
  const s = standard("Recommendation: roof F now, the other roofs after review", `Two phases. Phase 1 is roof F, PV only (case 1): the roof is new, the array is small against the load, curtailment is negligible and the battery the optimiser would add is a token. Phase 2 extends to the six older roofs with storage (case 4) once a structural and sheeting review clears them; its figures here are the difference between cases 4 and 1, not a modelled sequence, so a phased build would be re-priced for mobilisation and for the timing of the second array. Case 5 remains the reference: the measured roof carries three quarters of the unconstrained optimum. Next steps in order of value: commission the roof condition review of A to E and G; obtain an EPC quotation for roof F against 500 USD/kWp; decide on grid export; supply monthly kVAR maxima. Permits: an ERC generation licence and an Aor.6 building modification permit are required; no environmental assessment below 5 MWp.`);
  card(s, 54, 126, 580, 258, { fill: C.dark, line: false });
  text(s, "Phase 1: roof F, PV only (case 1)", 78, 144, 520, 30, { size: 18, bold: true, color: C.white });
  rich(s, [
    { t: `${fmt0(c1.pv_kw)} kWp on the roof replaced 1 to 2 years ago; no storage`, b: true, c: C.white, br: true, after: 6 },
    { t: `Capex ${fmt0(c1.capex_usd)} USD, equity ${fmt0(c1.equity_usd)} USD`, c: C.white, br: true, after: 4 },
    { t: `Year-1 savings ${fmt0(c1.year1_savings_usd)} USD; grid offset ${pct1(c1.grid_offset_to_load)}; ${fmt0(c1.tco2e)} tCO2e a year avoided`, c: C.white, br: true, after: 4 },
    { t: `Equity NPV ${fmt0(c1.npv_usd)} USD; IRR ${pct1(c1.equity_irr)}; payback ${c1.payback_years.toFixed(1)} years; coverage above ${floor1(c1.min_dscr)} in every year`, c: C.white, br: true, after: 4 },
    { t: "Ready for an EPC quotation now; no structural question on this roof.", c: C.pale },
  ], 78, 182, 530, 180, { size: 12.5 });
  card(s, 652, 126, 580, 258);
  text(s, "Phase 2: the other six roofs, with storage", 676, 144, 540, 30, { size: 18, bold: true, color: C.dark });
  rich(s, [
    { t: `Case 4 less case 1: ${fmt0(c4.pv_kw - c1.pv_kw)} kWp more PV, ${fmt0(c4.bess_kw)} kW / ${fmt0(c4.bess_kwh)} kWh of storage`, b: true, br: true, after: 6 },
    { t: `Capex ${fmt0(c4.capex_usd - c1.capex_usd)} USD more (case 4 total ${fmt0(c4.capex_usd)} USD)`, br: true, after: 4 },
    { t: `Year-1 savings ${fmt0(c4.year1_savings_usd - c1.year1_savings_usd)} USD more; site total grid offset ${pct1(c4.grid_offset_to_load)}; ${fmt0(c4.tco2e)} tCO2e a year`, br: true, after: 4 },
    { t: `Equity NPV ${fmt0(c4.npv_usd - c1.npv_usd)} USD more (case 4 total ${fmt0(c4.npv_usd)} USD); year-10 battery replacement dips coverage to ${c4.dscr_by_year[9].toFixed(2)}`, br: true, after: 4 },
    { t: "Conditional on the older roofs passing a condition review.", c: C.muted },
  ], 676, 182, 530, 180, { size: 12.5 });
  text(s, "Next steps, in order of value", 54, 400, 600, 30, { size: 18, bold: true, color: C.dark });
  const steps = [
    ["1", "Roof condition review", "Structural capacity and sheeting condition of A to E and G. Four fifths of the site's solar value sits on them."],
    ["2", "Quote roof F", "An EPC quotation for the phase 1 array, checked against the 500 USD/kWp used here. Every return in this deck scales off that figure."],
    ["3", "Decide on grid export", "A price for surplus generation would raise the value of phase 2 and the optimal size; none is assumed today."],
    ["4", "Supply kVAR maxima", "Monthly kVAR maxima are needed to assess power factor; mitigation is currently outside the capital cost."],
  ];
  steps.forEach(([n, t, sub], i) => {
    const x = 54 + i * 296;
    box(s, x, 438, 276, 176, i === 0 ? C.green2 : C.white, { radius: 18, line: i === 0 ? undefined : C.line });
    const col = i === 0 ? C.white : C.ink;
    text(s, n, x + 20, 452, 40, 44, { size: 28, bold: true, color: i === 0 ? C.white : C.dark });
    text(s, t, x + 66, 456, 200, 40, { size: 14, bold: true, color: col, valign: "middle" });
    text(s, sub, x + 20, 504, 240, 100, { size: 11.5, color: i === 0 ? C.white : C.muted });
  });
  text(s, "Then: ERC generation licence and Aor.6 building modification permit (no published fee schedule); no environmental assessment below 5 MWp. Phase 2 figures are case 4 less case 1, not a modelled sequence.", 54, 628, 1178, 30, { size: 11.5, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 17 appendix A provisional inputs
{
  const s = standard("Appendix A: provisional inputs", "Fifteen inputs are Allotrope estimates rather than confirmed figures and are marked 'PLACEHOLDER - pending Keen confirmation' on the Assumptions sheet of each workbook. The roof area itself is now measured; what remains provisional is the usable share (65 percent) and the condition of the six older roofs. The debt fraction and tenor and the insurance rate are the other inputs that move the answer. The rest are immaterial at this scale.");
  const H = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.header } } });
  const rows = [[H("Input"), H("Value used"), H("Effect if changed")],
    ["Usable roof share and PV cap", `65 percent of 16,319 m2 measured; ${fmt0(D.roof_all_kwp)} kWp all roofs, ${fmt0(D.roof_f_kwp)} kWp roof F`, "Sets the size of every roof case; a layout drawing will replace the share"],
    ["Roof condition, A to E and G", "assumed able to carry panels once reviewed", "A failed review removes those roofs from phase 2 or adds re-roofing cost"],
    ["Debt fraction", "70 percent of capex", "Moves equity IRR and DSCR; NPV to equity changes with leverage"],
    ["Debt term", "10 years", "A longer tenor takes the year-10 replacement past the final payment"],
    ["Insurance rate", "0.5 percent of capex per year", "Recurring cost; second-order at this scale"],
    ["PEA tariff escalation", "3 percent per year", "Raises or lowers every year's savings; Ft is not forecast"],
    ["Battery minimum duration", "1.5 hours", "Shapes the kW to kWh ratio the optimiser may choose"],
    ["Battery O&M", "1 percent of install cost per year", "Small; offset by the conservative replacement assumption"],
    ["PV inverter replacement", "year 11, 10 percent of PV capex", "Allotrope convention; a different year or share moves one year's cash flow"],
    ["PV tilt", "15 degrees", "Pitch not recorded; yield sensitivity is small at this latitude"],
    ["Grid connection cost", "excluded; placeholder pending quotation", "Add when quoted"],
    ["Permitting and licence fees", "excluded (no published schedule)", "Add when quoted"],
    ["Power factor mitigation", "excluded (no kVAR data)", "Conditional charge of 56.07 THB per kVAR above the allowance"],
  ];
  s.addTable(rows, {
    x: px(54), y: px(126), w: px(1178), colW: [px(300), px(400), px(478)], fontFace: FONT, fontSize: 11, color: C.ink, border: { type: "solid", pt: 0.5, color: C.line }, fill: { color: C.white }, rowH: px(33), valign: "middle", margin: [2, 6, 2, 6],
  });
  text(s, "Counted as fifteen items on the workbook because the roof area and the PV cap are listed separately, as are the PV inverter year and share; the roof condition line is added here.", 54, 622, 1178, 24, { size: 10.5, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 18 appendix B technical basis
{
  const s = standard("Appendix B: technical basis, permitting and files", "REopt (NREL) v0.57 via the Allotrope REopt API fork, HiGHS solver, 15 minute resolution, one metered year (2025). PVWatts irradiance and production factor for the site coordinates. Emissions from the TGO grid factor, not the optimiser. Permitting thresholds: initial environmental examination at 5 MWp, full assessment at 10 MWp; this project is under 3 MWp. Five workbooks accompany this edition, one per case, each with the full cash flow, the assumptions with sources, and the dispatch profile; case inputs, solver payload and raw results sit beside each.");
  const cards = [
    ["Optimisation", ["REopt (NREL) v0.57 through Allotrope's REopt API, HiGHS solver.", "15 minute resolution, one metered year of load (2025).", "PVWatts irradiance for Phimai; tilt 15 degrees; 0.5 percent a year PV degradation.", "Objective: lowest 20 year cost of electricity for the site; no export; storage may charge from grid or PV."]],
    ["Pro forma", ["20 year cash flow, direct ownership, 70 percent debt at 6.5 percent over 10 years.", "Thai CIT 20 percent flat; 5 year machinery depreciation; 7 percent VAT on the bill.", "Battery replaced in year 10 at 100 percent of install cost; PV inverter in year 11 at 10 percent of PV capex; both capitalised.", "Every workbook reconciles its live formulas to the engine (audit sheet)."]],
    ["Emissions and permitting", ["Avoided import x 0.4750 kg CO2e per kWh (TGO 2022-2024 grid mix, effective 1 January 2026).", "The optimiser's emissions outputs use US datasets and are not used.", "ERC generation licence and Aor.6 building modification permit required; no published fee schedules.", "IEE at 5 MWp, EIA at 10 MWp: not triggered below 3 MWp."]],
  ];
  cards.forEach(([t, items], i) => {
    const x = 54 + i * 396;
    card(s, x, 126, 380, 340, { fill: i === 1 ? C.dark : C.white, line: i !== 1 });
    text(s, t, x + 22, 144, 336, 30, { size: 16, bold: true, color: i === 1 ? C.white : C.dark });
    bullets(s, items, x + 22, 184, 336, 270, { size: 11.5, color: i === 1 ? C.white : C.ink, after: 8 });
  });
  text(s, "Files: five pro forma workbooks (one per case) under rofu_thailand_v2, the satellite roof measurement, the memo of 12 September 2026 (survey-based roof; superseded on the roof only) and its Vietnamese translation, the tariff structure briefing, and the case inputs, solver payloads and raw results for each case.", 54, 490, 1178, 50, { size: 12, color: C.ink });
}

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
