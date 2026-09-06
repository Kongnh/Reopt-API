# Rofu (Thailand) Rooftop Solar: Sizing, Pricing and Grid Offset

Prepared for Keen Footwear, 2026-09-06. Site: Rofu (Thailand) Ltd., Phimai
District, Nakhon Ratchasima. Basis: six REopt/proforma runs, `case_1` through
`case_6`, under `outputs/thailand_case/rofu_thailand/`, each with its own
workbook (`thailand_report_<run-uuid>.xlsx`).

## 1. Headline

Grid offset runs from 30.7 percent to 37.6 percent without storage, and from
30.7 percent to 37.9 percent with storage added; storage moves the offset by
at most 0.3 percentage points across every case tested (section 4).
Avoided Scope 2 emissions run from 1,054 to 1,303 tonnes CO2e per year across
the same six cases, an Allotrope calculation from avoided grid import, not a
REopt output (section 5).
Two findings should shape how Keen reads the rest of this memo: the roof is
the binding constraint on system value across the whole plausible sizing
range (section 3), and a battery does not pay against PEA's tariff at these
prices (section 4).

## 2. What we modelled

- **Site.** Rofu (Thailand) Ltd., Phimai District, Nakhon Ratchasima.
  Coordinates 15.209427, 102.475687.
- **Tariff.** PEA (Provincial Electricity Authority), Schedule 4.2 Large
  General Service Time-of-Use, 22-33 kV connection, rate code 4224, verified
  line by line against Rofu's own June 2025 invoice.
- **Load.** 35,040 fifteen-minute intervals built from 432 days of Rofu's own
  metered interval data, assembled into a synthetic twelve-month calendar
  (January-June 2026 plus July-December 2025) to give a complete year for the
  model. Annual load 7,235,301 kWh. In the conservative-roof case, monthly
  billed demand runs from about 1,082 kW to about 1,344 kW across the year.
- **Zero export.** PEA pays nothing for surplus energy. Every case curtails
  rather than exports; this is a behind-the-meter, self-consumption analysis
  with no wholesale settlement.
- **Ownership.** Direct ownership only: the factory buys and owns the
  PV/BESS asset outright, keeps the full avoided PEA bill with no ESCO
  discount or revenue split, and finances part of the capex with debt.[^6]
  ESCO and PPA structures for Thailand are out of scope of this analysis.

## 3. Solar sizing

### Roof-area derivation

Source: RTS Data Collection follow-up (Dec 2025), Facility Data sheet. Roof
size is recorded as "24 x 108 m / 30 x 108 m (each building differs)"; Keen's
December follow-up answer is "5 large rooftops of similar size (plus several
smaller)." The smaller roofs are excluded entirely.

Gross area = 5 roofs x 108 m x width. Usable fraction 0.65, the midpoint of
the 60-70 percent planning band for industrial metal roofs after perimeter
setbacks, maintenance walkways, roof penetrations and cable routing. Power
density 0.20 kW per square metre, the installed density of a 21-22 percent
efficient module on a pitched roof after row spacing.

| Roof width | Gross m2 | Usable m2 | PV cap (kWp) | Case |
|---|---|---|---|---|
| 24 m | 12,960 | 8,424 | 1,685 | case_1, case_5 |
| 27 m | 14,580 | 9,477 | 1,895 | case_2 |
| 30 m | 16,200 | 10,530 | 2,106 | case_3 |
| n/a (transformer nameplate, 500+500+1,600+630 kVA) | - | - | 3,230 (ceiling) | case_4, case_6 |

These three widths and the 0.65 / 0.20 factors are provisional pending Ou
confirming the actual roof widths and pitch.[^1] The 3,230 kW case_4/case_6
ceiling is not a roof estimate at all; it is the site's transformer nameplate
rating, used only as a generous upper bound so the optimizer can find where
more PV genuinely stops paying. Behind-the-meter PV with zero export is not
transformer-import-limited, so this ceiling carries no physical roof meaning.

### What each cap returned

| Case | PV cap (kWp) | PV built (kWp) | Grid offset | Reading |
|---|---|---|---|---|
| case_1 | 1,685 | 1,685.0 | 30.7% | Pins at cap: conservative roof |
| case_2 | 1,895 | 1,895.0 | 33.7% | Pins at cap: mid roof |
| case_3 | 2,106 | 2,106.0 | 36.5% | Pins at cap: upper roof |
| case_4 | 3,230 | 2,198.9 | 37.6% | Optimizer stops short of the ceiling |

**Cases 1 through 3 pin exactly at their roof cap.** In every one of those
three cases the optimizer would build more solar if it were allowed to; the
roof estimate, not the economics, decides the answer. Case 4 removes the roof
limit and raises the ceiling to the transformer nameplate; the optimizer
still chose about 2,199 kW, which is **above even the most generous roof
estimate above (case_3's 2,106 kWp)**. In other words, at every roof size
this memo can currently justify, the economics want more solar than the roof
can plausibly hold: there is no "too much solar" risk anywhere in this range.

**Confirming the actual usable roof area is therefore the single
highest-value open item on this project.** Moving from the 24 m to the 30 m
width alone is worth about +25 percent of system size, and every case above
shows that the added PV keeps paying for itself at every width tested.

## 4. Storage

| Case | PV (kWp) | Battery power (kW) | Battery energy (kWh) | Grid offset |
|---|---|---|---|---|
| case_5 (conservative roof) | 1,685.0 | 0.0 | 0.0 | 30.7% |
| case_6 (roof-unconstrained) | 2,210.3 | 38.83 | 58.24 | 37.9% |

Both storage cases gave the optimizer complete freedom to size a battery up
to 4,000 kW / 16,000 kWh, about four times the site's own peak demand, so
neither result below is a bound artifact; it is what the optimizer actually
wanted.[^3]

**At the conservative roof cap, the optimizer built no battery at all.** At
the roof-unconstrained cap, it built 38.83 kW / 58.24 kWh, about 1 percent of
the kW ceiling and 0.4 percent of the kWh ceiling it was allowed to use.

Say this plainly: **a battery does not pay against PEA's tariff at these
prices**, at any PV size tested. PEA's on-peak window runs 09:00 to 22:00;
PV alone cannot serve the 18:00-22:00 evening tail, which is the one place a
battery could add value by shifting midday surplus into the evening peak.
Even there, the economics do not support anything beyond a token system. Any
contractor proposal that includes a battery should be read against this
result: it should be justified by demand-charge or load-shifting value in
that evening window, not by a general energy-arbitrage story, and it should
be compared against a $0 storage baseline, not assumed to be additive value.

This deliverable reports what a battery is worth on PEA's tariff; it does not
price a specific vendor-scale battery. If a contractor quotes one, comparing
it against these results needs a further, forced-size run.

## 5. Emissions

REopt's own built-in emissions module is not usable for a Thailand site: the
grid datasets it relies on are US-specific with no Thailand coverage, so its
emissions outputs are always zero here. They are excluded from this memo and
from every workbook. The figures below are an **Allotrope calculation**,
computed from avoided grid import, not a REopt output.

| Case | Annual avoided (tCO2e) | Lifetime avoided, 25 yr (tCO2e) |
|---|---|---|
| case_1 | 1,054 | 24,820 |
| case_2 | 1,159 | 27,292 |
| case_3 | 1,254 | 29,539 |
| case_4 | 1,292 | 30,430 |
| case_5 | 1,054 | 24,820 |
| case_6 | 1,303 | 30,689 |

**Method.** Annual avoided tCO2e = (annual load kWh minus annual grid-
supplied kWh) x grid emission factor, divided by 1,000. The bracket is energy
actually served by PV (net of curtailment and net of any battery
grid-charging), the same quantity already reported as the grid offset above,
so the two figures cannot drift apart. Curtailed energy displaces no grid
import and is not claimed. The lifetime figure applies each year's PV
degradation rather than multiplying year one by 25.

**Emission factor: 0.4750 kg CO2e/kWh.** Source: Thailand Greenhouse Gas
Management Organization (TGO), official Carbon Footprint for Organization
(CFO) Scope 2 emission-factor table. Vintage: 2022-2024 generation data,
effective 1 January 2026. This is TGO's grid-mix (average) factor, not an
operating-margin, build-margin or combined-margin figure; the grid-mix
average is the methodologically correct match for a Scope 2 avoided-import
calculation like this one.

**Constant-factor assumption.** The factor above is held flat across the
full 25-year analysis period. This is the optimistic end of the range:
Thailand's grid is expected to decarbonise over time under the government's
power development planning, which would lower the true avoided-emissions
figure in later years relative to what is shown here.

**Market-based claim.** A market-based Scope 2 reduction claim depends on
Keen retaining and retiring the environmental attributes generated by this
system. Thailand has a live I-REC (International REC) registry. If the
I-RECs from this system are sold to a third party, the emissions reduction
above is not Keen's to claim under a market-based accounting approach. This
is stated as a fact for Keen's own accounting decision, not as advice on
which way to go.

## 6. Financials

| Case | Total investment (USD) | Equity IRR | Project IRR | NPV (USD) | Simple payback (yrs) |
|---|---|---|---|---|---|
| case_1 | 1,263,750 | 36.62% | 19.98% | 1,006,077 | 2.75 |
| case_2 | 1,421,250 | 35.37% | 19.55% | 1,079,560 | 2.85 |
| case_3 | 1,579,500 | 33.94% | 19.04% | 1,133,681 | 2.97 |
| case_4 | 1,649,166 | 33.23% | 18.79% | 1,149,208 | 3.03 |
| case_5 | 1,263,750 | 36.62% | 19.98% | 1,006,077 | 2.75 |
| case_6 | 1,683,898 | 32.94% | 18.68% | 1,158,344 | 3.06 |

case_5's row is identical to case_1's because the optimizer built zero
battery at the conservative roof cap; there is no separate "with storage"
price at that roof size. IRR and NPV are computed at an owner discount rate
of 11.5 percent.[^2]

**Cost basis.** Of the cost and technical inputs behind these figures, five
carry Thailand-specific citations:

- PV installed cost, USD 750/kWp: Krungsri Research (Feb 2025), Thai
  commercial-and-industrial rooftop trend of THB 20,000-25,000/kWp, cross-
  checked against Farungsang, Varquez and Tokimatsu (MDPI Sustainability, Aug
  2025), USD 767/kWp. Set near the top of the cited range because no
  site-specific EPC quote exists yet.
- PV O&M, USD 7.5/kWp/yr: the same MDPI paper's assumption of 1 percent of
  installed capex per year.
- Debt interest rate, 6.5 percent: Thai commercial bank Minimum Loan Rates as
  of December 2025 (Siam Commercial Bank, Bangkok Bank, KBank), taken at the
  conservative (higher) end of the 6.40-6.62 percent band.
- The grid emission factor and its vintage (section 5).

**Nineteen inputs remain provisional**, pending Keen's confirmation, carrying
the exact marker "PLACEHOLDER - pending Keen confirmation" on the Assumptions
sheet of every workbook. The ones with the largest bearing on this memo's
numbers are the roof-area and PV-cap inputs,[^1] the owner discount
rate,[^2] BESS pricing,[^3] and debt structure, insurance and connection
costs.[^6] The full list and its sourcing history are in
`docs/superpowers/notes/2026-09-05-thailand-cost-benchmarks.md`.

**Power factor is not computed in any case.**[^4] **The ERC generation
licence and the Aor.6 building-modification permit are required but excluded
from capex.**[^5] By contrast, an Environmental Impact Assessment (EIA) and
an Initial Environmental Examination (IEE) are **genuinely not required**:
Thailand's thresholds are 5 MWp for an IEE and 10 MWp for a full EIA, and
every case here sits at roughly 1.7 to 2.2 MWp. The zero cost carried for
environmental permitting in every case is a finding, not a gap.

## Footnotes

[^1]: Usable roof area and the resulting PV capacity cap (`usable_roof_area_m2`, `pv_max_kw`) are provisional, derived from Keen's written description of roof dimensions rather than a structural survey. Status: PLACEHOLDER, pending Keen confirmation.

[^2]: The owner discount rate of 11.5 percent (`discount_rate`) used for NPV is provisional. The sourced figure (Saelim/Agora Energiewende/TDRI, CASE for Southeast Asia, 16 Aug 2024) is a **third-party rooftop-solar developer's** cost of equity under business-as-usual risk, not Rofu's own hurdle rate as a factory self-investing in its own roof. Rofu's real cost of capital is unknown and is plausibly lower, so 11.5 percent is a conservative figure, not a confirmed one. Status: PLACEHOLDER, pending Keen confirmation.

[^3]: BESS installed cost (USD 300/kW, USD 250/kWh), replacement cost, minimum duration and O&M fraction are all provisional. No adequate Thailand- or Southeast-Asia-specific benchmark was found for these; every candidate source found in research was either a different market segment (utility-scale grid storage) or lacked a genuine regional tie. Status: PLACEHOLDER, pending Keen confirmation.

[^4]: Power factor is not computed. PEA's power-factor charge and allowance calculation needs the site's monthly kVAR maximum, which has not been supplied. Every case therefore reports 0 kVAR compensation and 0 mitigation cost; that is "not computed," not a confirmed absence of a power-factor charge. Status: not computed, pending the site's monthly kVAR maximum from Ou.

[^5]: The ERC generation licence (triggered at 1 MWp; every case here is above that) and the Aor.6 building-modification permit are required for this project but excluded from capex in every case, because neither has a public fee schedule; engineering and drawing costs are quotation-specific. Status: PLACEHOLDER, pending an EPC or permitting-agent quote.

[^6]: Debt fraction (70 percent of capex), debt term (10 years), insurance rate (0.5 percent of capex per year), the PEA grid-connection charge, and inverter-replacement timing and cost are also provisional. Status: PLACEHOLDER, pending Keen confirmation. The full list of provisional inputs, and the five that are sourced, are documented in `docs/superpowers/notes/2026-09-05-thailand-cost-benchmarks.md`.

## 7. Information requests

For Ou:

1. **Confirmed roof widths and pitch** for the five large rooftops. This is
   the single highest-value open item in this analysis: it can move system
   size, and savings, by up to about 25 percent from the cases modelled here,
   and every case in this memo shows the economics want at least as much
   solar as the roof can plausibly hold.
2. **The site's monthly kVAR maximum.** Without it, power factor is not
   modelled anywhere in this memo or its workbooks; any PEA power-factor
   charge or credit is currently unknown.
3. **Any EPC quotes already in hand**, for PV, for BESS, or for both, so the
   benchmark pricing in this memo (USD 750/kWp for PV; provisional pricing
   for BESS) can be checked against real vendor numbers before Keen evaluates
   contractor proposals.
