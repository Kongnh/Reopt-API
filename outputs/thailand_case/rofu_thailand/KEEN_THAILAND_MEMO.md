# Rofu Thailand: rooftop solar and storage feasibility

Prepared for Keen by Allotrope Partners, 12 September 2026.
Site: Rofu, Phimai, Nakhon Ratchasima. Supply: PEA Schedule 4.2 Large General
Service TOU, 22-33 kV, rate code 4224.

## Where the storage conclusion now stands

Our first memo concluded that battery storage did not pay at this site and
recommended solar alone. We withdrew that conclusion in the second memo, and
this third memo tests it at the most conservative replacement assumption Keen
has asked for. **Storage is still selected. The conclusion has now held at
three price points and we consider it settled.**

The history in one paragraph. The first analysis priced the battery at 300
USD/kW plus 250 USD/kWh, which for a 1.5 hour system is 675 USD/kW installed,
and the optimiser rejected storage. Keen then confirmed 100 USD/kW plus 150
USD/kWh, 325 USD/kW installed, and the optimiser selected storage whether we
ran 475 USD/kWp over 25 years or 500 USD/kWp over 20 years; at that stage the
battery was replaced in year 10 at 70 percent of its install cost. Keen has now
ruled that the replacement is priced at 100 percent of install cost, for the
whole system, storage inverter and pack together. Discounted at 11 percent, a
full-price replacement in year 10 adds about 35 percent of the install cost to
the battery's lifetime cost. The optimiser still builds storage: 367 kWh
alongside the roof-limited array, and 1,881 kWh when the roof constraint is
relaxed. Both are smaller than at 70 percent (429 and 2,378 kWh), which is the
right direction and the right size of response. Neither sits at a modelling
limit, so these are economic choices rather than artefacts of a cap.

## The six cases

All six solved to optimality. Cases 1 to 3 span the plausible roof range, case 4
removes the roof limit to find the economic optimum, and cases 5 and 6 permit
storage at the roof-limited and roof-relaxed sizes. Cases 1 to 4 have no
storage and are unchanged from the previous memo to the cent.

| | PV (kW) | Storage | Capex (USD) | Year 1 savings | Grid offset | tCO2e/yr | Equity IRR | Equity NPV |
|---|---|---|---|---|---|---|---|---|
| 1. Roof, low | 1,685 | none | 842,500 | 272,717 | 30.8% | 1,096 | 66.4% | 1,304,997 |
| 2. Roof, mid | 1,895 | none | 947,500 | 299,784 | 33.8% | 1,205 | 64.5% | 1,415,588 |
| 3. Roof, high | 2,106 | none | 1,053,000 | 324,301 | 36.6% | 1,304 | 62.2% | 1,506,642 |
| 4. No roof limit | 2,549 | none | 1,274,321 | 364,048 | 41.1% | 1,465 | 56.1% | 1,610,103 |
| 5. Roof, low, with storage | 1,685 | 222 kW / 367 kWh | 919,716 | 289,920 | 32.1% | 1,116 | 64.2% | 1,353,566 |
| 6. No roof limit, with storage | 2,847 | 507 kW / 1,881 kWh | 1,756,407 | 460,458 | 50.4% | 1,740 | 49.6% | 1,855,912 |

Financing throughout is 70% debt at 6.5% over 10 years, against a 20 year
project life and an 11% discount rate. Case 1 equity is 252,750 USD against
589,750 USD of debt; case 6 equity is 526,922 USD against 1,229,485 USD.

Equity IRR falls as the system grows because each additional kilowatt is worth
less than the one before it, being pushed further from the load. That is normal
and is not an argument against the larger systems: case 6 produces the largest
NPV, 1.86 million USD, and by far the largest emissions reduction.

## One consequence of the year-10 replacement that Keen should see

The battery is now replaced in year 10, which is also the final year of the
10 year loan. In case 6 the replacement costs 378,411 USD in that year, which
takes cash available for debt service down to 109,516 USD against a debt
payment of 171,027 USD: a debt service coverage of 0.64 in year 10 alone,
against 2.31 on average and above 2.0 in every other year. Case 5 stays above
2.2 throughout because its battery is small.

This is not a reason to drop the battery. It is a structuring point: a lender
will expect the year-10 replacement to be funded from a reserve built up in
years 1 to 9, or the loan tenor to be set so that the replacement falls after
the final payment. We have modelled neither, deliberately, so that the raw
effect is visible. Either fix is routine. What Keen should not do is read the
minimum coverage figure on the case 6 workbook as a sign of a weak project.

## What we recommend Keen do next, in order

**1. Measure the roof.** This is the highest value open item by a wide margin.
The economic optimum with no roof constraint is 2,549 kW without storage and
2,847 kW with it. Our most generous estimate of usable roof is 2,106 kW. The
roof therefore binds across the entire plausible range, which means every
square metre confirmed is a square metre that earns. Our estimate derives from
the site survey as five roofs, 108 m long, recorded at widths between 24 m and
30 m, at 65% usable area and 0.20 kW/m2. The widths are the uncertain term and
the pitch was never recorded.

**2. Get an EPC quote and check it against 500 USD/kWp.** Every return in this
memo scales directly off that figure. See the caveat below.

**3. Decide on grid export.** We have modelled a strict no-export site, which
is what we understood to apply. It is expensive. See below.

**4. Supply the monthly kVAR maximum** if power factor is to be assessed. Keen
has directed that power factor mitigation be excluded from capital cost, so we
have excluded it, and no kVAR data was requested. This is a scoping decision
rather than a finding that no mitigation is needed.

## The capital cost is the assumption that matters most

The 500 USD/kWp used here was supplied by Keen. It sits below every published
Thai benchmark we were able to locate. Krungsri Research puts commercial and
industrial rooftop at THB 20,000 to 25,000 per kWp, which is 615 to 769 USD at
32.5 THB per USD. Farungsang, Varquez and Tokimatsu (MDPI Sustainability 17(15):
7052, August 2025) assume 767 USD/kWp. Keen's figure is roughly 19% below the
bottom of that range.

We have used it as given, and we are not disputing it: a current quotation from
a contractor is better evidence than a published average. But the reader should
understand that the returns in this memo are unusually strong precisely because
the capital cost is unusually low. Case 1 shows a simple equity payback of 1.5
years. That is a consequence of the input, not a discovery about the site, and a
quote at 650 USD/kWp would change the picture materially. Confirming the price is
therefore worth more than refining anything else in this analysis.

## Curtailment: the site is throwing away energy it cannot sell

The site is modelled with no export to PEA, so any solar the factory cannot use
at the moment it is generated is simply lost. The cost of that rises sharply
with system size.

| Case | PV (kW) | Production curtailed |
|---|---|---|
| 1 | 1,685 | 8.6% |
| 2 | 1,895 | 10.7% |
| 3 | 2,106 | 13.0% |
| 4 | 2,549 | 19.2% |
| 5 | 1,685 with storage | 6.5% |
| 6 | 2,847 with storage | 12.7% |

At the unconstrained optimum, nearly one fifth of everything the array generates
is discarded. Two things follow.

First, if export at any reasonable price can be negotiated, the economics of the
larger systems improve considerably and the optimal size rises again. We have
not modelled that because we have no price to model it at, and we would rather
leave the question open than invent one.

Second, **part of what the battery is buying is recovered curtailment.** Compare
cases 1 and 5, which have identical arrays: adding storage takes curtailment
from 8.6% down to 6.5%. The battery is not only arbitraging the tariff, it is
catching energy that would otherwise be thrown away. That is a more durable
argument for storage than the tariff spread alone, because it does not depend on
the peak and off peak differential staying where it is.

## Technical basis

Specific yield is 1,498 kWh/kWp in year one against plane of array irradiation
of 2,049 kWh/m2, a performance ratio of 0.731. Annual site load is 7,235,301 kWh
and the business as usual electricity bill is 843,443 USD per year.

**Equipment replacement.** The battery system, storage inverter and pack
together, is replaced once, in year 10, at 100 percent of its install cost.
That is Keen's ruling and it is the conservative choice: the optimiser's own
storage operating cost is plain maintenance with no allowance for capacity
fade, so this single event stands in for all battery ageing in the model. The
PV inverter is replaced in year 11 at 10 percent of PV capital cost, an
Allotrope convention still awaiting Keen's confirmation. Both replacements are
capitalised and depreciated over the five year machinery life. The same rule
now governs Allotrope's Vietnam work, so the two countries' models can be read
side by side.

We checked the year-10 assumption against the optimiser's own battery
degradation model, which tracks state of health day by day from calendar age
and cycling. Under that model and this site's dispatch the case 6 battery is
still at 96 percent of its capacity after 20 years and never reaches the 80
percent point at which a replacement is normally triggered; the cost of topping
up lost cells would be about 3 percent of what the year-10 replacement costs.
The year-10 whole-system replacement is therefore conservative by a wide
margin. We have not relied on the degradation model in the figures above
because its coefficients are laboratory defaults with no calibration to the
chemistry or the 30 degree ambient here; the vendor's warranty, not the model,
is what will decide when the system is actually replaced.

Emissions are an Allotrope calculation, not a model output: avoided grid import
multiplied by the Thailand Greenhouse Gas Management Organization grid mix
factor of 0.4750 kg CO2e per kWh, the 2022 to 2024 vintage effective 1 January
2026. The optimiser's own emissions outputs are built on United States datasets
with no Thailand coverage and are all zero here; we do not use them and neither
should any reader of the underlying model files.

Environmental permitting is genuinely not required at this scale. An initial
environmental examination is triggered at 5 MWp and a full assessment at 10 MWp,
against a project under 3 MWp. An ERC generation licence and an Aor.6 building
modification permit are both required, but neither has a published fee schedule,
so both are excluded from the capital costs above and must be added when quoted.

## What remains provisional

Fourteen inputs are still Allotrope estimates rather than confirmed figures, and
each is marked as such on the Assumptions sheet of the accompanying workbooks.
The ones that would move the answer are the roof area, the debt terms, and the
insurance rate. The PV inverter replacement year and fraction are two of the
fourteen. The rest are immaterial at this scale.

Two disclosures on the mechanics. The model applies PV operating cost at 8.00
USD/kWp per year rather than the 7.50 supplied, because the optimiser rounds
cost parameters to whole dollars; the workbooks show all three figures so the
rounding is visible. And grid connection cost is excluded from capital cost at
Keen's direction, alongside power factor mitigation.

## Files

Six workbooks, one per case, each carrying the full cash flow, the assumptions
with their sources, and the dispatch profile. Case inputs, the solver payload,
and the raw results accompany each one.
