// Rofu Thailand rooftop solar and storage: feasibility results deck.
// Style follows outputs/thailand_case/rofu_thailand/Rofu_Thailand_Tariff_Structure_Internal.pptx
// (pale green ground, teal title band, Allotrope logo, condensed layouts); content
// from KEEN_THAILAND_MEMO.md and the six case records on master (deck_data.json).
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const ROOT = "C:/Users/kongn/Pictures/CodeProject/Reopt API/REopt_API";
const HERE = path.join(ROOT, "tmp/presentations/rofu_feasibility");
const OUT = path.join(ROOT, "outputs/thailand_case/rofu_thailand/Rofu_Thailand_Solar_Storage_Feasibility.pptx");
const D = JSON.parse(fs.readFileSync(path.join(HERE, "deck_data.json"), "utf8"));

const C = {
  bg: "EAF5F2", header: "24857B", dark: "17685F", ink: "143B37", muted: "4D6D68",
  pale: "CFE7E2", pale2: "B7D9D2", green: "70AD52", green2: "3F8E73", yellow: "F7D98B",
  orange: "E98A55", red: "D77C7F", white: "FFFFFF", line: "8AB8B0", gray: "E5E9E8",
};
const FONT = "Arial";
const FOOT = "Rofu Thailand feasibility  |  Allotrope Partners  |  September 2026";
const px = (v) => v / 96; // 1280 x 720 px design grid on a 13.333 x 7.5 in canvas

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Allotrope Partners";
pres.title = "Rofu Thailand rooftop solar and storage feasibility";

const logo = "image/png;base64," + fs.readFileSync(path.join(ROOT, "tmp/keen_design/allotrope-logo-1.png")).toString("base64");
const cover = "image/png;base64," + fs.readFileSync(path.join(ROOT, "tmp/keen_design/cover-03.png")).toString("base64");

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
const cases = D.cases;
const c1 = cases[0], c4 = cases[3], c5 = cases[4], c6 = cases[5];
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
  text(s, "Feasibility results: six configurations on the PEA time-of-use tariff, sized by optimisation and tested on a 20 year pro forma", 92, 350, 350, 130, { size: 17, color: C.white });
  text(s, "Prepared by Allotrope Partners\nSeptember 2026", 92, 560, 340, 60, { size: 14, color: C.pale });
  s.addNotes("Deck built from KEEN_THAILAND_MEMO.md (12 September 2026) and the six case records under outputs/thailand_case/rofu_thailand on master. Visual style follows the Rofu tariff structure briefing (Allotrope KEEN reference deck). All money in USD at 32.5 THB per USD unless marked THB.");
}

// ---------------------------------------------------------------- 2 summary
{
  const s = standard("Summary: solar pays at every roof size; storage is selected", "Headline numbers are the memo's six-case table. Storage was selected at both the roof-limited size (367 kWh) and the unconstrained size (1,881 kWh) once the battery was priced at 100 USD/kW plus 150 USD/kWh with a full-price replacement in year 10; it had been rejected at the earlier 675 USD/kW installed price. The roof binds across the plausible range, so the roof measurement is the highest-value open item.");
  const stats = [
    ["1,685-2,106 kWp", "usable roof range from the site survey; the economic optimum is larger (2,549 kWp without storage, 2,847 with)"],
    ["367-1,881 kWh", "storage selected at both ends of the range (222 kW at the roof-limited size, 507 kW unconstrained)"],
    [`${fmt0(c1.year1_savings_usd / 1000)}k-${fmt0(c6.year1_savings_usd / 1000)}k USD`, "year-1 bill savings against a business-as-usual bill of 843,443 USD"],
    [`${M(c1.npv_usd)}-${M(c6.npv_usd)} M USD`, "equity NPV at 11 percent over 20 years; equity IRR 50 to 66 percent on 70 percent debt"],
  ];
  stats.forEach(([v, l], i) => stat(s, 54 + i * 296, 126, 276, 168, v, l, { valueSize: 21, labelSize: 11.5 }));
  text(s, "What the analysis found", 54, 318, 600, 30, { size: 18, bold: true, color: C.dark });
  bullets(s, [
    "Every roof case is strongly positive: equity IRR above 60 percent and simple equity payback under two years, driven by a 500 USD/kWp installed cost that sits below published Thai benchmarks.",
    "The roof, not the economics, sets the size. Each square metre confirmed adds value up to about 2.5 to 2.8 MWp.",
    "The site cannot export, so 9 to 19 percent of production is curtailed depending on size; storage recovers part of it and clips the on-peak demand charge.",
    "The battery is replaced in full in year 10, the final loan year. Case 6 shows a one-year coverage dip that a reserve or a longer tenor removes.",
  ], 54, 356, 720, 300, { size: 14, after: 8 });
  card(s, 812, 318, 420, 332, { fill: C.dark, line: false });
  text(s, "Recommended path", 840, 340, 370, 30, { size: 18, bold: true, color: C.white });
  bullets(s, [
    "Base case: the roof-limited array with storage (case 5): 1,685 kWp, 222 kW / 367 kWh, 919,716 USD capex, NPV 1.35 M USD.",
    "Upside: the unconstrained array with storage (case 6) if the measured roof allows it: 2,847 kWp, NPV 1.86 M USD.",
    "Next: measure the roof, obtain an EPC quotation against 500 USD/kWp, decide on grid export, supply monthly kVAR data.",
  ], 840, 380, 370, 260, { size: 13, color: C.white, after: 8 });
}

// ---------------------------------------------------------------- 3 scope and method
{
  const s = standard("Scope and method", "The optimiser is REopt (NREL) at 15 minute resolution with the HiGHS solver: it chooses PV and battery sizes and the hourly dispatch that minimise the 20 year cost of electricity for the site under the PEA tariff, with no export allowed. The pro forma (proforma_vietnam engine, Thailand profile) then builds the 20 year cash flow for direct ownership: capex, financing, O&M, insurance, replacements, depreciation and CIT. Three iterations of the battery price: 300 + 250 (rejected), 100 + 150 with a 70 percent year-10 replacement (selected), and 100 + 150 with a 100 percent year-10 replacement (selected, smaller).");
  text(s, "Question", 54, 128, 380, 30, { size: 18, bold: true, color: C.dark });
  text(s, "How much rooftop solar, with or without battery storage, should Rofu Thailand install under its current PEA tariff, and what does the investment return over 20 years?", 54, 162, 380, 120, { size: 14 });
  text(s, "Method", 54, 300, 380, 30, { size: 18, bold: true, color: C.dark });
  bullets(s, [
    "Dispatch and sizing: REopt optimisation at 15 minute resolution, one full year of metered load, PVWatts irradiance for Phimai, no grid export.",
    "Economics: 20 year pro forma, direct ownership by the factory, 70 percent debt, Thai CIT and depreciation.",
    "Six cases: three roof sizes, one unconstrained size, and the two storage variants.",
  ], 54, 336, 380, 300, { size: 13, after: 8 });

  text(s, "How the battery conclusion was tested", 490, 128, 740, 30, { size: 18, bold: true, color: C.dark });
  const steps = [
    ["1", "Initial price", "300 USD/kW + 250 USD/kWh (675 USD/kW installed for 1.5 h)", "Storage rejected by the optimiser", C.pale2, C.ink],
    ["2", "Keen quotation", "100 USD/kW + 150 USD/kWh (325 USD/kW installed); year-10 replacement at 70 percent of install", "Storage selected: 429 kWh roof-limited, 2,378 kWh unconstrained", C.green2, C.white],
    ["3", "Conservative replacement", "Same prices; the whole battery system replaced in year 10 at 100 percent of install cost", "Storage still selected: 367 kWh and 1,881 kWh. The conclusion has held at three price points", C.dark, C.white],
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
  const s = standard("The facility: Rofu Thailand, Phimai", "Sources: PEA invoice June 2025; RTS data collection workbook; KTH2 electricity use; 15 minute interval data for 2025 supplied by PEA. Monthly energy from the metered series used by the optimiser (7,235,301 kWh in the year). Roof estimate: five roofs 108 m long, widths recorded at 24 to 30 m, 65 percent usable, 0.20 kW per m2; the widths are the uncertain term and the pitch was never recorded.");
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
    { t: "Survey basis: ", b: true }, { t: "five roofs, 108 m long, widths between 24 m and 30 m; pitch not recorded", br: true, after: 6 },
    { t: "Usable estimate: ", b: true }, { t: "65 percent of area at 0.20 kW per m2 gives 1,685 to 2,106 kWp", br: true, after: 6 },
    { t: "Status: ", b: true }, { t: "the widths are the uncertain term; the roof has not been measured for this study" },
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

// ---------------------------------------------------------------- 5 load profile and tariff clock
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

// ---------------------------------------------------------------- 6 tariff
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

// ---------------------------------------------------------------- 7 assumptions technical and cost
{
  const s = standard("Assumptions (1): technical and cost inputs", "Cost inputs from Keen's quotation: 500 USD/kWp installed for PV (the top of the confirmed C&I rooftop range), 100 USD/kW plus 150 USD/kWh for the battery. O&M was supplied at 1.5 percent of PV capex (7.50 USD/kWp per year); the optimiser rounds cost parameters to whole dollars and applied 8.00, which the workbooks disclose. Battery O&M 1 percent of its install cost a year. The year-10 whole-system replacement at 100 percent of install cost is the conservative case; the PV inverter replacement at 10 percent of PV capex in year 11 is an Allotrope convention awaiting confirmation.");
  const rows = [
    [{ text: "Item", options: { bold: true, color: C.white, fill: { color: C.header } } }, { text: "Value", options: { bold: true, color: C.white, fill: { color: C.header } } }, { text: "Basis", options: { bold: true, color: C.white, fill: { color: C.header } } }],
    ["PV installed cost", "500 USD/kWp", "Keen quotation; below published Thai benchmarks (see slide 14)"],
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
    x: px(54), y: px(126), w: px(1178), colW: [px(300), px(300), px(578)], fontFace: FONT, fontSize: 11.5, color: C.ink, border: { type: "solid", pt: 0.5, color: C.line }, fill: { color: C.white }, rowH: px(38), valign: "middle", margin: [2, 6, 2, 6], autoPage: false,
  });
}

// ---------------------------------------------------------------- 8 assumptions financial and scope
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
    "Fifteen inputs are provisional and marked as such in the workbooks; the ones that move the answer are the roof area, the debt terms and the insurance rate (Appendix A).",
  ], 710, 398, 500, 190, { size: 11.5, after: 6 });
  text(s, "All results are before grid connection, permitting and power-factor costs; add them when quoted.", 54, 616, 1178, 26, { size: 12, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 9 the six cases
{
  const s = standard("Six configurations were optimised", "Cases 1 to 3 cap the array at the three roof-width readings from the survey (24, 27 and 30 m; five roofs 108 m long; 65 percent usable; 0.20 kW per m2). Case 4 removes the cap so the optimiser finds the economic optimum. Cases 5 and 6 allow storage at the roof-limited and unconstrained sizes; the optimiser chose the battery size in both. All six solved to optimality; cases 1 to 4 carry no storage and are unchanged from the earlier memo.");
  const defs = [
    ["1", "Roof, low", "PV capped at 1,685 kWp (24 m roof width)", "no storage", C.pale2, C.ink],
    ["2", "Roof, mid", "PV capped at 1,895 kWp (27 m)", "no storage", C.pale2, C.ink],
    ["3", "Roof, high", "PV capped at 2,106 kWp (30 m)", "no storage", C.pale2, C.ink],
    ["4", "No roof limit", "PV free up to the 3,230 kVA connection", "no storage: the economic optimum", C.green2, C.white],
    ["5", "Roof, low, with storage", "PV capped at 1,685 kWp", "storage sized by the optimiser", C.dark, C.white],
    ["6", "No roof limit, with storage", "PV free", "storage sized by the optimiser", C.dark, C.white],
  ];
  defs.forEach(([n, t, pv, st, fill, col], i) => {
    const x = 54 + (i % 3) * 396, y = 130 + Math.floor(i / 3) * 150;
    box(s, x, y, 380, 132, fill, { radius: 18 });
    text(s, n, x + 20, y + 16, 44, 48, { size: 30, bold: true, color: col });
    text(s, t, x + 76, y + 18, 290, 30, { size: 16, bold: true, color: col });
    text(s, pv, x + 76, y + 54, 290, 36, { size: 12, color: col });
    text(s, st, x + 76, y + 92, 290, 30, { size: 12, bold: true, color: col });
  });
  card(s, 54, 440, 1178, 200);
  text(s, "How the roof estimate is built", 78, 458, 500, 28, { size: 16, bold: true, color: C.dark });
  const chain = ["5 roofs", "x 108 m", "x 24 to 30 m", "x 65% usable", "x 0.20 kW/m2", "= 1,685 to 2,106 kWp"];
  chain.forEach((t, i) => {
    const x = 78 + i * 188;
    box(s, x, 498, 172, 52, i === chain.length - 1 ? C.dark : C.pale, { radius: 12 });
    text(s, t, x + 8, 498, 156, 52, { size: 13, bold: true, color: i === chain.length - 1 ? C.white : C.ink, align: "center", valign: "middle" });
  });
  text(s, "The widths are the uncertain term and the pitch was not recorded. The optimiser wants 2,549 kWp without storage and 2,847 kWp with it, so the roof binds across the whole plausible range.", 78, 566, 1130, 56, { size: 12.5, color: C.ink });
}

// ---------------------------------------------------------------- 10 results table
{
  const s = standard("Results: the six cases side by side", "Figures from the six pro forma workbooks (12 September 2026). Financing throughout is 70 percent debt at 6.5 percent over 10 years, 20 year life, 11 percent discount rate. Case 1 equity 252,750 USD against 589,750 USD of debt; case 6 equity 526,922 USD against 1,229,485 USD. Equity IRR falls as the system grows because each additional kilowatt is pushed further from the load and is worth less than the one before; case 6 still produces the largest NPV and by far the largest emissions reduction.");
  const memoOffset = { 1: 0.308, 2: 0.338, 3: 0.366, 4: 0.411, 5: 0.321, 6: 0.504 };
  const H = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.header }, align: "center" } });
  const rows = [[H("Case"), H("PV (kWp)"), H("Storage"), H("Capex (USD)"), H("Year-1 savings (USD)"), H("Grid offset"), H("tCO2e / yr"), H("Equity IRR"), H("Equity NPV (USD)")]];
  cases.forEach((c) => {
    const bold = c.n === 5 || c.n === 6;
    const opt = { bold, fill: { color: bold ? C.pale : C.white } };
    rows.push([
      { text: `${c.n}. ${c.label}`, options: { ...opt, align: "left" } },
      { text: fmt0(c.pv_kw), options: { ...opt, align: "right" } },
      { text: c.bess_kwh ? `${fmt0(c.bess_kw)} kW / ${fmt0(c.bess_kwh)} kWh` : "none", options: { ...opt, align: "center" } },
      { text: fmt0(c.capex_usd), options: { ...opt, align: "right" } },
      { text: fmt0(c.year1_savings_usd), options: { ...opt, align: "right" } },
      { text: pct1(memoOffset[c.n]), options: { ...opt, align: "right" } },
      { text: fmt0(c.tco2e), options: { ...opt, align: "right" } },
      { text: pct1(c.equity_irr), options: { ...opt, align: "right" } },
      { text: fmt0(c.npv_usd), options: { ...opt, align: "right" } },
    ]);
  });
  s.addTable(rows, {
    x: px(54), y: px(130), w: px(1178), colW: [px(220), px(90), px(190), px(120), px(140), px(90), px(90), px(80), px(158)], fontFace: FONT, fontSize: 11.5, color: C.ink, border: { type: "solid", pt: 0.5, color: C.line }, rowH: px(38), valign: "middle", margin: [2, 6, 2, 6],
  });
  text(s, "Reading the table", 54, 462, 400, 28, { size: 16, bold: true, color: C.dark });
  bullets(s, [
    "Every case returns its equity in under two years at the 500 USD/kWp price; the differences between cases are in scale, not in whether the investment works.",
    "Storage adds 77,000 USD of capex at the roof-limited size and 17,000 USD of year-1 savings, lifting NPV by 49,000 USD; unconstrained, it adds 1.9 MWh and lifts NPV by 246,000 USD.",
    "Equity IRR falls with size because each added kilowatt is used less on site; NPV, not IRR, is the figure to size on.",
  ], 54, 496, 1178, 170, { size: 13, after: 8 });
}

// ---------------------------------------------------------------- 11 NPV and IRR chart
{
  const s = standard("Bigger systems return more in total, less per dollar", "Equity NPV at 11 percent and equity IRR from the six workbooks. NPV rises monotonically with size; IRR falls from 66 percent to 50 percent. The storage cases sit on the same curve: case 5 above case 1, case 6 above case 4.");
  text(s, "Equity NPV (USD, 20 years at 11 percent)", 54, 124, 600, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "Equity NPV", labels: cases.map((c) => `${c.n}. ${c.label}`), values: cases.map((c) => Math.round(c.npv_usd)) }], {
    ...chartBase, x: px(54), y: px(154), w: px(620), h: px(420), barDir: "bar", catAxisOrientation: "maxMin", chartColors: [C.green2], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, dataLabelFormatCode: "#,##0", valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 2300000, catAxisLabelFontSize: 10,
  });
  text(s, "Equity IRR", 720, 124, 500, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "Equity IRR", labels: cases.map((c) => `${c.n}`), values: cases.map((c) => Math.round(1000 * c.equity_irr) / 10) }], {
    ...chartBase, x: px(720), y: px(154), w: px(512), h: px(230), barDir: "col", chartColors: [C.orange], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, dataLabelFormatCode: "0.0\"%\"", valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 80,
  });
  card(s, 720, 404, 512, 170, { fill: C.dark, line: false });
  text(s, "Capex and equity by case (USD)", 744, 420, 470, 26, { size: 13, bold: true, color: C.white });
  rich(s, cases.flatMap((c, i) => [{ t: `${c.n}: `, b: true, c: C.white }, { t: `capex ${fmt0(c.capex_usd)}, equity ${fmt0(c.equity_usd)}, debt ${fmt0(c.debt_usd)}`, c: C.white, br: i < cases.length - 1 }]), 744, 450, 470, 120, { size: 11.5 });
  text(s, "Simple equity payback runs from 1.5 years (case 1) to 2.0 years (case 6). These are consequences of the 500 USD/kWp input; see slide 14.", 54, 590, 1178, 40, { size: 12, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 12 what storage does
{
  const s = standard("What storage buys: recovered curtailment and a lower monthly peak", "Case 6 average day across 2025 from the optimiser's dispatch: PV serves the daytime load, charges the battery late morning when the array would otherwise be curtailed, and the battery discharges into the evening on-peak hours (18:00 to 22:00) and covers the morning ramp. Year 1 case 6: storage to load 529 MWh, PV to storage 472 MWh, grid to storage 113 MWh, PV curtailed 542 MWh (12.7 percent), demand charge savings 32,470 USD. Comparing cases 1 and 5 (identical arrays): curtailment falls from 8.6 to 6.5 percent when storage is added.");
  text(s, "Case 6, average day: who serves the load (kW by hour)", 54, 124, 700, 26, { size: 15, bold: true, color: C.dark });
  const d6 = D.case6_dispatch;
  const hours = Array.from({ length: 24 }, (_, h) => String(h).padStart(2, "0"));
  s.addChart(pres.ChartType.bar, [
    { name: "PV to load", labels: hours, values: d6.pv_to_load.map((v) => Math.round(v)) },
    { name: "Battery to load", labels: hours, values: d6.storage_to_load.map((v) => Math.round(v)) },
    { name: "Grid to load", labels: hours, values: d6.grid_to_load.map((v) => Math.round(v)) },
  ], {
    ...chartBase, x: px(54), y: px(154), w: px(760), h: px(330), barDir: "col", barGrouping: "stacked", barGapWidthPct: 40, chartColors: [C.yellow, C.green2, C.pale2], showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: C.ink, catAxisLabelFontSize: 9, valAxisMinVal: 0, valAxisMaxVal: 1300,
  });
  text(s, "Late morning the array also charges the battery (up to 340 kW) and still curtails up to 400 kW; the battery gives it back from 18:00 to 22:00, inside the peak window.", 54, 494, 760, 44, { size: 11.5, color: C.muted, italic: true });
  const stats = [
    ["529 MWh / yr", "delivered by the case 6 battery to the load, mostly in the evening peak hours", C.dark, C.white],
    ["8.6% to 6.5%", "curtailment at the roof-limited array without and with storage (cases 1 and 5): energy that would otherwise be lost", C.green2, C.white],
    ["32,470 USD / yr", "case 6 demand charge savings; the battery covers the interval that would set the monthly peak", C.white, C.dark],
  ];
  stats.forEach(([v, l, fill, col], i) => {
    const y = 124 + i * 150;
    card(s, 850, y, 382, 134, { fill, line: fill === C.white });
    text(s, v, 874, y + 14, 340, 44, { size: 24, bold: true, color: col === C.white ? C.white : C.dark, valign: "middle" });
    text(s, l, 874, y + 62, 340, 66, { size: 11.5, color: col === C.white ? C.white : C.muted });
  });
  text(s, "The conclusion held at three battery price points, so it rests on the tariff shape and the no-export rule, not on one quotation.", 54, 560, 1178, 40, { size: 12.5, color: C.ink, bold: true });
}

// ---------------------------------------------------------------- 13 year-10 replacement and DSCR
{
  const s = standard("The year-10 battery replacement meets the final loan year", "Debt service coverage by year from the case 5 and case 6 workbooks. The whole battery system is replaced in year 10 at 100 percent of install cost, the same year as the last of ten level debt payments. In case 6 the replacement takes cash available for debt service to 109,516 USD against a payment of 171,027 USD: coverage 0.64 in that one year against 2.31 on average and above 2.0 in every other year. Case 5 stays above 2.2 throughout because its battery is small. Neither a reserve nor a longer tenor has been modelled, deliberately, so the raw effect is visible.");
  text(s, "Debt service coverage ratio, years 1 to 10", 54, 124, 700, 26, { size: 15, bold: true, color: C.dark });
  const years = Array.from({ length: 10 }, (_, i) => `Y${i + 1}`);
  s.addChart(pres.ChartType.line, [
    { name: "Case 5: roof, low, with storage", labels: years, values: c5.dscr_by_year.slice(0, 10).map((v) => Math.round(v * 100) / 100) },
    { name: "Case 6: no roof limit, with storage", labels: years, values: c6.dscr_by_year.slice(0, 10).map((v) => Math.round(v * 100) / 100) },
  ], {
    ...chartBase, x: px(54), y: px(154), w: px(760), h: px(360), chartColors: [C.green2, C.orange], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 6, showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: C.ink, valAxisMinVal: 0, valAxisMaxVal: 3.5, showValue: true, dataLabelFontSize: 9, dataLabelColor: C.ink, dataLabelPosition: "t", dataLabelFormatCode: "0.00",
  });
  card(s, 850, 124, 382, 390, { fill: C.dark, line: false });
  text(s, "A structuring point", 874, 146, 340, 30, { size: 17, bold: true, color: C.white });
  bullets(s, [
    "Case 6, year 10: cash available for debt service 109,516 USD against 171,027 USD of debt service after a 332,891 USD battery replacement.",
    "A lender will expect the replacement funded from a reserve built in years 1 to 9, or a tenor set so the replacement falls after the final payment. Either fix is routine.",
    "The minimum coverage figure on the case 6 workbook should be read with this in mind.",
    "The optimiser's own degradation model puts the case 6 battery at 96 percent capacity after 20 years; the year-10 full replacement is conservative by a wide margin.",
  ], 874, 188, 336, 320, { size: 12, color: C.white, after: 8 });
  text(s, "Average coverage over the loan: case 5 2.89, case 6 2.31. PV inverter replacement (10 percent of PV capex) follows in year 11, after the loan.", 54, 530, 760, 44, { size: 11.5, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 14 capex and export
{
  const s = standard("Two inputs move the answer: capital cost and export", "Benchmarks: Krungsri Research puts Thai C&I rooftop at THB 20,000 to 25,000 per kWp (615 to 769 USD at 32.5); Farungsang, Varquez and Tokimatsu (MDPI Sustainability 17(15):7052, August 2025) assume 767 USD/kWp. The 500 USD/kWp used here is Keen's quotation, about 19 percent below the bottom of that range; a current quotation is better evidence than a published average, but every return in the deck scales off it. Curtailment: the site is modelled with no export, so surplus generation is lost; if export at any reasonable price can be negotiated, the larger systems improve and the optimal size rises. No price was assumed because none is known.");
  text(s, "Installed PV cost, USD per kWp", 54, 124, 560, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "USD/kWp", labels: ["This study (Keen quotation)", "Krungsri low", "Krungsri high", "MDPI 2025"], values: [500, 615, 769, 767] }], {
    ...chartBase, x: px(54), y: px(154), w: px(560), h: px(300), barDir: "col", chartColors: [C.dark, C.pale2, C.pale2, C.pale2], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 900, catAxisLabelFontSize: 10,
  });
  text(s, "The 500 USD/kWp price is used as given. It is why simple equity payback is 1.5 years; a quotation at 650 USD/kWp would change the picture materially. Confirming the price is worth more than refining anything else in the analysis.", 54, 464, 560, 90, { size: 12.5, color: C.ink });
  text(s, "Share of production curtailed (no export)", 670, 124, 560, 26, { size: 15, bold: true, color: C.dark });
  s.addChart(pres.ChartType.bar, [{ name: "Curtailed", labels: cases.map((c) => `${c.n}`), values: cases.map((c) => Math.round(1000 * c.curtailed_fraction) / 10) }], {
    ...chartBase, x: px(670), y: px(154), w: px(560), h: px(300), barDir: "col", chartColors: [C.orange], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: C.ink, dataLabelFormatCode: "0.0\"%\"", valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 24, catAxisLabelFontSize: 10,
  });
  text(s, "At the unconstrained optimum nearly one fifth of generation is discarded. An export price, if PEA or a third party offers one, would raise both the value of the larger systems and the optimal size; the question is left open rather than priced by assumption.", 670, 464, 560, 90, { size: 12.5, color: C.ink });
  text(s, "Cases: 1 roof low, 2 roof mid, 3 roof high, 4 no roof limit, 5 roof low with storage, 6 no roof limit with storage.", 54, 580, 1178, 24, { size: 11, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 15 recommendation
{
  const s = standard("Recommendation: build to the roof, with storage", "The storage conclusion has held at three price points and is treated as settled. The size is set by the roof, which has not been measured; the roof-limited storage case (5) is the base case and the unconstrained storage case (6) the upside if the measured roof allows it. Next steps in order of value: measure the roof; obtain an EPC quotation and check it against 500 USD/kWp; decide on grid export; supply monthly kVAR maxima if power factor is to be assessed. Permits: an ERC generation licence and an Aor.6 building modification permit are required; no environmental assessment below 5 MWp.");
  card(s, 54, 126, 580, 250, { fill: C.dark, line: false });
  text(s, "Base case: case 5", 78, 144, 520, 30, { size: 18, bold: true, color: C.white });
  rich(s, [
    { t: "1,685 kWp PV with 222 kW / 367 kWh storage", b: true, c: C.white, br: true, after: 6 },
    { t: `Capex ${fmt0(c5.capex_usd)} USD, equity ${fmt0(c5.equity_usd)} USD`, c: C.white, br: true, after: 4 },
    { t: `Year-1 savings ${fmt0(c5.year1_savings_usd)} USD; grid offset 32 percent; ${fmt0(c5.tco2e)} tCO2e a year avoided`, c: C.white, br: true, after: 4 },
    { t: `Equity NPV ${fmt0(c5.npv_usd)} USD; IRR ${pct1(c5.equity_irr)}; coverage above 2.2 in every year`, c: C.white, br: true, after: 4 },
    { t: "Fits the smallest roof reading; every metre of roof confirmed beyond it adds value.", c: C.pale },
  ], 78, 182, 530, 180, { size: 12.5 });
  card(s, 652, 126, 580, 250);
  text(s, "Upside: case 6, if the roof allows", 676, 144, 520, 30, { size: 18, bold: true, color: C.dark });
  rich(s, [
    { t: "2,847 kWp PV with 507 kW / 1,881 kWh storage", b: true, br: true, after: 6 },
    { t: `Capex ${fmt0(c6.capex_usd)} USD, equity ${fmt0(c6.equity_usd)} USD`, br: true, after: 4 },
    { t: `Year-1 savings ${fmt0(c6.year1_savings_usd)} USD; grid offset 50 percent; ${fmt0(c6.tco2e)} tCO2e a year avoided`, br: true, after: 4 },
    { t: `Equity NPV ${fmt0(c6.npv_usd)} USD; IRR ${pct1(c6.equity_irr)}; year-10 replacement needs a reserve or a longer tenor`, br: true, after: 4 },
    { t: "Needs about 35 percent more roof than the most generous survey reading.", c: C.muted },
  ], 676, 182, 530, 180, { size: 12.5 });
  text(s, "Next steps, in order of value", 54, 400, 600, 30, { size: 18, bold: true, color: C.dark });
  const steps = [
    ["1", "Measure the roof", "Widths and pitch of the five roofs. The optimum is 2.5 to 2.8 MWp; every confirmed square metre earns."],
    ["2", "Obtain an EPC quotation", "Check it against the 500 USD/kWp used here. Every return in this deck scales off that figure."],
    ["3", "Decide on grid export", "A price for surplus generation would raise the optimal size; none is assumed today."],
    ["4", "Supply monthly kVAR maxima", "Needed to assess power factor; mitigation is currently outside the capital cost."],
  ];
  steps.forEach(([n, t, sub], i) => {
    const x = 54 + i * 296;
    box(s, x, 438, 276, 176, i === 0 ? C.green2 : C.white, { radius: 18, line: i === 0 ? undefined : C.line });
    const col = i === 0 ? C.white : C.ink;
    text(s, n, x + 20, 452, 40, 44, { size: 28, bold: true, color: i === 0 ? C.white : C.dark });
    text(s, t, x + 66, 456, 200, 40, { size: 14, bold: true, color: col, valign: "middle" });
    text(s, sub, x + 20, 504, 240, 100, { size: 11.5, color: i === 0 ? C.white : C.muted });
  });
  text(s, "Then: ERC generation licence and Aor.6 building modification permit (no published fee schedule); no environmental assessment below 5 MWp.", 54, 628, 1178, 30, { size: 11.5, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 16 appendix A provisional inputs
{
  const s = standard("Appendix A: provisional inputs", "Fifteen inputs are Allotrope estimates rather than confirmed figures and are marked 'PLACEHOLDER - pending Keen confirmation' on the Assumptions sheet of each workbook. The ones that move the answer are the roof area (and the PV cap derived from it), the debt fraction and tenor, and the insurance rate. The rest are immaterial at this scale.");
  const H = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.header } } });
  const rows = [[H("Input"), H("Value used"), H("Effect if changed")],
    ["Usable roof area and PV cap", "8,424 m2, 1,685 kWp (low reading); mid 1,895, high 2,106", "Sets the size of every roof case; the highest-value open item"],
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
    x: px(54), y: px(126), w: px(1178), colW: [px(300), px(400), px(478)], fontFace: FONT, fontSize: 11, color: C.ink, border: { type: "solid", pt: 0.5, color: C.line }, fill: { color: C.white }, rowH: px(35), valign: "middle", margin: [2, 6, 2, 6],
  });
  text(s, "Counted as fifteen items on the workbook because the roof area and the PV cap are listed separately, as are the PV inverter year and share.", 54, 616, 1178, 24, { size: 10.5, color: C.muted, italic: true });
}

// ---------------------------------------------------------------- 17 appendix B technical basis
{
  const s = standard("Appendix B: technical basis, permitting and files", "REopt (NREL) v0.57 via the Allotrope REopt API fork, HiGHS solver, 15 minute resolution, one metered year (2025). PVWatts irradiance and production factor for the site coordinates. Emissions from the TGO grid factor, not the optimiser. Permitting thresholds: initial environmental examination at 5 MWp, full assessment at 10 MWp; this project is under 3 MWp. Six workbooks accompany the memo, one per case, each with the full cash flow, the assumptions with sources, and the dispatch profile; case inputs, solver payload and raw results sit beside each.");
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
  text(s, "Files: six pro forma workbooks (one per case), the memo of 12 September 2026 and its Vietnamese translation, the tariff structure briefing, and the case inputs, solver payloads and raw results for each case.", 54, 490, 1178, 50, { size: 12, color: C.ink });
}

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
