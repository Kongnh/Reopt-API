# Thailand cost and emissions benchmarks: research findings

Date: 2026-09-06
Scope: Task 15. Re-benchmark the eleven Thailand cost/emissions placeholders in
`proforma_thailand/defaults/thailand_defaults.json` against Thailand-applicable,
citable sources. This is research plus a data edit; no code changed.

Site for context: Rofu (Thailand) Ltd., Phimai District, Nakhon Ratchasima.
Roughly 1.7 MWp rooftop PV, behind the meter, zero export, direct ownership,
utility PEA.

Access date for every source below is 2026-09-06 unless stated otherwise.

## Summary table

| Key | Before | After | Status |
|---|---|---|---|
| `pv_installed_cost_per_kw` | 700.0 (placeholder) | 750.0 USD/kWp | Sourced |
| `discount_rate` | 0.08 (placeholder) | 0.115 | Sourced |
| `grid_emission_factor_kg_co2e_per_kwh` | 0.4999 (placeholder) | 0.4750 | Sourced |
| `grid_emission_factor_vintage` | "pending" (placeholder) | "2022-2024 generation data (TGO CFO Scope 2 grid-mix average, effective 1 Jan 2026)" | Sourced |
| `annual_om_per_kw` | 12.0 (placeholder) | 12.0 (unchanged) | Evidence found, not applied - see "Scope conflict" below |
| `debt_interest_rate` | 0.06 (placeholder) | 0.06 (unchanged) | Evidence found, not applied - see "Scope conflict" below |
| `bess_installed_cost_per_kw` | 300.0 (placeholder) | 300.0 (unchanged) | Left as placeholder - no adequate evidence |
| `bess_installed_cost_per_kwh` | 250.0 (placeholder) | 250.0 (unchanged) | Left as placeholder - no adequate evidence |
| `insurance_rate_fraction` | 0.005 (placeholder) | 0.005 (unchanged) | Left as placeholder - no Thailand-applicable source |
| `inverter_replacement_fraction_of_pv_capex` | 0.10 (placeholder) | 0.10 (unchanged) | Left as placeholder - no Thailand-applicable source |
| `bess_om_fraction_of_installed_cost` | 0.01 (placeholder) | 0.01 (unchanged) | Left as placeholder - no Thailand-applicable source |
| `pea_tariff_escalation_rate` | 0.03 (placeholder) | 0.03 (unchanged) | Left as placeholder - recent trend contradicts the assumption but no long-run forecast found |

Four keys were actually re-sourced and had their `value`/`source` fields
replaced: `pv_installed_cost_per_kw`, `discount_rate`,
`grid_emission_factor_kg_co2e_per_kwh`, `grid_emission_factor_vintage`. The
`RESEARCHED` tuple in `test_thailand_defaults.py` lists only the two of those
that live in the `financial` block and are covered by that test
(`pv_installed_cost_per_kw`, `discount_rate`); the grid emission factor has its
own dedicated test. The remaining seven keys keep the exact placeholder marker
string unchanged, per the constraint that a production guard checks for that
string and a workbook with the marker removed everywhere would refuse to
write.

## 1. `pv_installed_cost_per_kw` - SOURCED, 750.0 USD/kWp

**Sources:**
- Krungsri Research, "Rooftop Solar: Suitable Business and Investment Models
  for Thailand" (Feb 2025), krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025.
  Reports a Thai commercial-and-industrial rooftop installed-cost trend of
  THB 20,000-25,000/kWp for 2023-2024, down from THB 27,500/kWp in 2020.
- Farungsang, L., Varquez, A.C.G., Tokimatsu, K., "Geospatial Assessment and
  Economic Analysis of Rooftop Solar Photovoltaic Potential in Thailand,"
  Sustainability (MDPI) 17(15):7052, August 2025, doi.org/10.3390/su17157052.
  Uses USD 276.15 per 360 W panel for commercial and industrial rooftop PV,
  which is USD 767/kWp.

**Range spanned:** USD 615-769/kWp (Krungsri's THB 20,000-25,000/kWp converted
at the model's own 32.5 THB/USD rate) versus a single MDPI point estimate of
USD 767/kWp. The two sources converge tightly at the upper end of the Krungsri
band.

**Why 750:** Set near the top of the confirmed range rather than the midpoint.
Two independent reasons: no site-specific EPC quote exists yet for Rofu, and
understating capex would inflate the IRR/NPV the client memo quotes, which is
the wrong direction to err in when a client is about to compare these numbers
against contractor bids. Rofu's 1.7 MWp scale is also larger than the small
commercial examples (30-100 kW) that anchor the low end of some Thai retail
pricing surveys, so there is no strong reason to expect below-band pricing
either.

## 2. `bess_installed_cost_per_kw` and `bess_installed_cost_per_kwh` - LEFT AS PLACEHOLDER

The brief explicitly allows a Thailand-or-Southeast-Asia figure for these two
keys (unlike the stricter Thailand-only bar for the rest of the table). Even
with that relaxed bar, nothing adequate turned up.

**What was checked:**
- BloombergNEF's 2025 lithium-ion pack price survey (via pv-magazine,
  energy-storage.news, ess-news.com secondary reporting): global average
  turnkey BESS price of USD 117/kWh in 2025, stationary-storage pack price of
  USD 70/kWh. Global, not Southeast Asia, and predominantly utility-scale.
- Wood Mackenzie's APAC grid-scale energy storage pricing 2024 report: EPC
  cost of USD 59-117/kWh across APAC. The countries the report actually
  covers (per its own summary) are China, Australia, South Korea and Japan;
  Thailand and the rest of Southeast Asia are not in scope, and the figure is
  grid-scale, not commercial-and-industrial rooftop-scale.
- Vendor-blog aggregates (gsl-energy.com, bslbatt.com, highjoule.com) citing
  "commercial lithium BESS, USD 280-580/kWh installed" and "outside China and
  the US, USD 125/kWh all-in" for 4-hour utility-scale systems. These are SEO
  content from battery vendors, not a reputable market tracker's own report,
  and the "outside China/US" figure is again utility-scale, not C&I.

**Why left provisional:** Every candidate is either a different market
segment (utility-scale grid storage, materially cheaper per kWh than a small
C&I rooftop-attached system) or lacks a real Southeast Asia tie, and one
tier is a vendor marketing blog rather than a market tracker. Applying any of
these would understate the BESS cost line, which is the wrong direction to
err in for a client investment decision. The placeholder marker stays.

## 3. `annual_om_per_kw` - EVIDENCE FOUND, NOT APPLIED (scope conflict)

**Source:** Farungsang, Varquez & Tokimatsu (MDPI Sustainability 17(15):7052,
Aug 2025, same paper as above) assumes O&M costs at 1 percent of installed
CAPEX per year for its Thai rooftop PV economic analysis. Applied to the
750 USD/kWp capex chosen above, that is approximately USD 7.5/kWp/yr, versus
the current placeholder of USD 12.0/kWp/yr.

**Why not applied:** `proforma_thailand/tests/test_case_builder.py::PayloadDefaultInheritanceTests::test_pv_om_cost_comes_from_the_thailand_defaults`
hardcodes `self.assertEqual(pv["om_cost_per_kw"], 12.0)`, reading the value
live from `annual_om_per_kw`. Changing the default breaks that test. This
task's declared scope is `thailand_defaults.json`, `test_thailand_defaults.py`
and this note; touching `test_case_builder.py` is out of scope. Rather than
either silently break an existing test or quietly expand scope, the value is
left at 12.0 and the marker stays in place. This is flagged as a follow-up:
a future task should decide whether to adopt the 1-percent-of-capex figure
and update the coupled test at the same time.

## 4. `insurance_rate_fraction` - LEFT AS PLACEHOLDER

**What was checked:** Thai insurers (SCB, Chubb, MSIG, Sompo, Lockton
Wattana, TTIB) all publish "Industrial All Risks" property insurance product
pages for the Thai market, but none discloses a premium rate as a percentage
of sum insured; Thai insurance premiums for this class follow Office of
Insurance Commission tariff rates that are risk-rated per policy and are not
published. The only numeric benchmark found (roughly 0.5-1.0 percent of
capex for a 1 MW solar plant) came from an Indian-market example, with no
Thailand tie.

**Why left provisional:** No Thailand-applicable figure exists in the public
domain. A global rule-of-thumb dressed up as a Thai number would be exactly
the kind of unsupported guess this task is meant to avoid.

## 5. `inverter_replacement_fraction_of_pv_capex` - LEFT AS PLACEHOLDER

**What was checked:** General solar-cost commentary confirms module and
inverter costs together drove roughly 55 percent of the 2010-2024 decline in
system costs, and NREL's Annual Technology Baseline models a DC:AC ratio for
commercial PV, but no source (Thai or otherwise) gives an inverter cost as a
clean percentage of total system capex. NREL ATB is a US national-lab figure
in any case, with no Thailand applicability even if a number had been found.

**Why left provisional:** No citable, Thailand-applicable percentage exists.
The existing note that this figure came from the ENS SolarStorage vendor
comparator (a Vietnam-configured workbook, explicitly a comparator and never
a Thailand source per the brief) is retained as-is; the marker stays.

## 6. `bess_om_fraction_of_installed_cost` - LEFT AS PLACEHOLDER

Same conclusion and reasoning as `bess_installed_cost_per_kw` above: nothing
Thailand- or Southeast-Asia-specific was found for BESS O&M as a fraction of
capex. Global benchmarks exist (NREL ATB, roughly 2.5 percent for the US) but
carry no Thailand or Southeast Asia tie and are left out.

## 7. `pea_tariff_escalation_rate` - LEFT AS PLACEHOLDER

**What was checked:** PEA's Ft (fuel-adjustment) charge fell from 93.43
satang/kWh (Jan-Apr 2023) to 9.72 satang/kWh (Jan-Apr 2026), a roughly
ten-fold drop, and the ERC's blended system-wide rate is described as
"historically low" through 2026. Industrial electricity prices in 2024
"returned to 2022 levels" after several years near USD 0.10/kWh since 2019.

**Why left provisional, not lowered:** The actual multi-year trend has been
flat-to-declining, which if anything argues the current 3 percent/year
placeholder is too high, not that it should be confirmed as-is. But Ft is a
short-cycle fuel pass-through subject to active government intervention
(price caps, subsidies), not a stable trend that safely extrapolates across a
25-year analysis horizon. No EPPO or ERC long-run tariff forecast (e.g. from
the Power Development Plan) was found to responsibly anchor a replacement
number. Rather than invent a downward-revised figure from a few years of
politically-managed data, the placeholder is left in place and this finding
is recorded so a future task can pick it up if an authoritative long-run
forecast becomes available.

## 8. `discount_rate` - SOURCED, 0.115 (11.5 percent)

**Sources:**
- Saelim, S. (Agora Energiewende, on behalf of CASE for Southeast Asia,
  implemented with the Thailand Development Research Institute, TDRI),
  "Policy instruments for facilitating rooftop solar PV investments: Thailand
  and international cases," 16 Aug 2024 (GIZ/IKI-funded). Its risk waterfall
  for Thai rooftop PV investment gives a cost of equity of 11.5 percent under
  business-as-usual (current) risk conditions, versus a 7.3 percent
  "best case" if every identified policy and financial risk were mitigated.
- Farungsang, Varquez & Tokimatsu (MDPI, Aug 2025, cited above) used a
  discount rate of 6.3145 percent, stated as reflecting the 2022 Bank of
  Thailand policy rate.

**Range spanned:** 6.31 percent (BOT policy-rate proxy) to 11.5 percent
(TDRI/Agora cost of equity, BAU), a gap well beyond a narrow band.

**Why 11.5 not 6.3:** A central-bank policy rate is close to a risk-free rate
and does not carry the equity risk premium a private investor requires to
bear rooftop-solar project risk in Thailand; the TDRI/Agora figure is
purpose-built to measure exactly that premium for this asset class. The
higher, more conservative figure is carried, consistent with the instruction
to pick the conservative side of a disagreement and say so. This is also
methodologically the better match for the brief's ask for "Thai corporate
WACC or hurdle rate": it is Thailand-specific and rooftop-solar-specific,
which a generic corporate WACC benchmark (only found as an unsourced global
10-14 percent manufacturing range, no Thailand tie) is not.

## 9. `debt_interest_rate` - EVIDENCE FOUND, NOT APPLIED (scope conflict)

**Sources:**
- Siam Commercial Bank (SCB) Minimum Loan Rate (MLR): cut from 6.500 percent
  to 6.400 percent, effective 23 Dec 2025.
- Bangkok Bank MLR: cut from 6.50 percent to 6.45 percent, effective 22 Dec
  2025.
- KBank MLR: cut from 6.72 percent to 6.62 percent, effective 22 Dec 2025.
- Cross-check: the same TDRI/Agora CASE study above gives a cost of debt for
  Thai rooftop PV of 5.3 percent under business-as-usual conditions (Aug
  2024), versus 2.4 percent "best case."

**Range spanned:** 5.3 percent (project-specific, Aug 2024) to 6.62 percent
(KBank MLR, Dec 2025). The bank MLR figures, being the most current and the
most directly "commercial lending rate," would be carried at roughly 6.5
percent, the conservative (higher) end.

**Why not applied:** `proforma_thailand/tests/test_case_builder.py::ThailandCaseBuilderTests::test_assumptions_list_the_active_placeholders`
asserts `self.assertIn("debt_interest_rate", assumptions["placeholder_keys"])`,
reading live from the same `placeholder_keys()` function this task's default
change would affect. Sourcing this key removes it from that set and breaks
the test. As with `annual_om_per_kw`, the fix belongs in `test_case_builder.py`,
which is outside this task's declared scope, so the value and marker are left
unchanged and this is flagged as a follow-up alongside the O&M finding.

## 10. `grid_emission_factor_kg_co2e_per_kwh` - SOURCED, 0.4750 kgCO2e/kWh

**Primary source:** Thailand Greenhouse Gas Management Organization (TGO),
official emission-factor table for Carbon Footprint for Organization (CFO)
Scope 2 reporting, published at thaicarbonlabel.tgo.or.th, document dated
"UPDATE: February 2569" (February 2026, Buddhist Era). The table's
"Electricity, grid mix" section lists, among other rows:

| Vintage | Use | kgCO2e/kWh |
|---|---|---|
| 2016-2018 | CFO Scope 2 (usable through 31 Mar 2026) | 0.4999 |
| 2016-2018 | Scope 3 (fuel extraction/transport) | 0.0987 |
| 2016-2018 | Carbon Footprint of Product (CFP) | 0.5986 |
| 2022-2024 | CFO Scope 2 (effective 1 Jan 2026) | **0.4750** |
| 2022-2024 | Scope 3 | 0.0812 |
| 2022-2024 | CFP | 0.5562 |

The 0.4999 row is exactly the figure the placeholder previously carried,
confirming it was a real (if stale) TGO number, just not the currently
effective one. Methodology: "Thai National LCI Database, TIISMTEC-NSTDA, AR5
(with TGO electricity generation data for the stated years)," i.e. this is a
**grid-mix (average) factor**, not an operating-margin, build-margin or
combined-margin figure. This distinction matters because
`proforma_thailand/emissions.py` computes avoided Scope 2 emissions (its own
docstring says so), and the grid-mix Scope 2 factor is the methodologically
correct match; a T-VER/CDM-style combined-margin factor serves a different
purpose (carbon-credit MRV baselines) and would not be the right substitute
even though a combined-margin number is sometimes what "TGO grid factor"
colloquially refers to.

**Cross-checks:**
- Thailand's Energy Policy and Planning Office (EPPO, Ministry of Energy)
  reports a generation-only CO2 intensity of 0.400 kg/kWh for 2023 and 0.399
  kg/kWh for 2024 (a record low, per CEIC's reporting of EPPO data). This is
  CO2-only (excludes CH4 and N2O) and generation-side only (excludes
  transmission-and-distribution losses that TGO's LCA-style figure folds in),
  so a lower number than TGO's is expected and is not itself evidence of
  disagreement between authorities, just of different scope.
- An attempt to cross-check against the IGES/IFI harmonised grid-factor list
  (iges.or.jp/en/pub/list-grid-emission-factor/en) was blocked by the site
  (HTTP 403) and could not be verified directly; this is disclosed rather
  than papered over with an invented combined-margin number.

**Why 0.4750 and not 0.4999:** The 0.4999 figure the placeholder carried is
TGO's own prior vintage, and the same TGO document states it is usable only
through 31 March 2026. Given today's date (2026-09-06), that window has
already closed and 0.4750 is the currently effective, officially designated
TGO figure. It is also the lower of the two TGO vintages, so adopting it is
not a case of picking the more "generous" number: it happens to be both the
current and the more conservative of the two TGO options.

## 11. `grid_emission_factor_vintage` - SOURCED

Set to `"2022-2024 generation data (TGO CFO Scope 2 grid-mix average,
effective 1 Jan 2026)"`, recording the vintage year, the fact that it is a
grid-mix/average factor rather than an operating-margin, build-margin or
combined-margin figure, and the effective date, so a brand's auditor asking
"which TGO factor was this" has the answer without needing to re-derive it.

## Sources consulted (full list)

- Krungsri Research, "Rooftop Solar: Suitable Business and Investment Models
  for Thailand," Feb 2025:
  krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025
- Farungsang, Varquez and Tokimatsu, "Geospatial Assessment and Economic
  Analysis of Rooftop Solar Photovoltaic Potential in Thailand," Sustainability
  17(15):7052, MDPI, Aug 2025: doi.org/10.3390/su17157052
- Saelim, S. (Agora Energiewende / CASE for Southeast Asia / TDRI), "Policy
  instruments for facilitating rooftop solar PV investments: Thailand and
  international cases," 16 Aug 2024: caseforsea.org
- Thailand Greenhouse Gas Management Organization (TGO), CFO emission-factor
  table: thaicarbonlabel.tgo.or.th
- Thailand Energy Policy and Planning Office (EPPO) generation CO2 intensity,
  as reported by CEIC Data: ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics
- Siam Commercial Bank, "SCB to Cut Lending Rates," Dec 2025: scb.co.th
- Nation Thailand, Thai bank MLR cuts following the December 2025 MPC
  decision: nationthailand.com/business/banking-finance/40060060
- Nation Thailand, "TGO sets new emission factors for electricity generation
  and transmission": nationthailand.com/news/policy/40059019
- IGES, "List of Grid Emission Factors" (attempted, blocked, HTTP 403):
  iges.or.jp/en/pub/list-grid-emission-factor/en
- Wood Mackenzie, "APAC utility-scale energy storage pricing report 2025"
  (summary only): woodmac.com/press-releases/apac-utility-scale-energy-storage-pricing-report-2025
- BloombergNEF 2025 lithium-ion battery pack price survey, as reported by
  pv-magazine, energy-storage.news and ess-news.com

## Note on the ENS SolarStorage vendor form

The ENS SolarStorage calculation form in the client's `05_Vendor_Market/`
folder was not used as a source for any figure in this note. It is
configured for a Vietnam site at latitude 11.09 with EVN tariffs, THB/VND and
a 10 percent VAT rate, none of which apply to the Rofu site in Nakhon
Ratchasima. Two existing entries in `thailand_defaults.json`
(`inverter_replacement_year` and the pre-Task-15 `inverter_replacement_fraction_of_pv_capex`
note) already disclose that they originated from that form as a comparator;
this task did not add any new citation to it.
