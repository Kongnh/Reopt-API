# Thai depreciation, permitting and interconnection: research findings

Date: 2026-09-04
Scope: Task 13. Originally depreciation only; extended by the user to cover
grid-connection and EIA/permitting capex.

## 1. Depreciation

### Finding

Rooftop PV and BESS are depreciated as **machinery and equipment: maximum 20%
per annum, i.e. a 5-year straight line**.

### Basis

Depreciation limits are set by Royal Decree No. 145 issued under the Revenue
Code. Any generally accepted accounting method may be used, but the rate may not
exceed the decree's ceiling for the asset class. The ceilings that matter here:

| Asset class | Maximum rate | Implied life |
|---|---|---|
| Plant, machinery and equipment | 20% pa | 5 years |
| Permanent buildings | 5% pa | 20 years |
| Temporary buildings | 100% | 1 year |

### The classification question, stated honestly

The material uncertainty is not the rate but the **class**: is a roof-mounted PV
array machinery, or an improvement to a permanent building? The two give 5 years
versus 20 years, which is a large difference in the tax shield.

We treat it as machinery. The supporting evidence:

- Thai practice consistently treats factory rooftop PV as removable plant
  serving an energy function rather than as structural building fabric.
- Royal Decree No. 805 (2 March 2026) grants a 150% deduction for **energy-saving
  machinery** carrying a DEDE/EGAT Level 5-star certification, and the measure is
  described as covering solar equipment. That the legislature reaches solar
  through a *machinery* incentive is corroborating evidence for the class.
- BOI treats solar generating equipment as machinery.

**What remains uncertain:** we found no Revenue Department ruling addressing
rooftop PV classification directly. If the Revenue Department were to treat the
array as a building improvement, the life becomes 20 years and the early-year
tax shield shrinks substantially. This should be confirmed with Rofu's Thai tax
advisor before the numbers are relied on. BESS is not exposed to this ambiguity;
a battery container is unambiguously equipment.

### Incentives checked and NOT applied

- **Royal Decree No. 805 solar rooftop deduction (up to THB 200,000):** does NOT
  apply. It is a *personal* income tax deduction, capped at 10 kWp, for
  residential rooftops. Rofu is a corporate taxpayer at roughly 1.7 MW.
- **Royal Decree No. 805 energy-saving machinery 150% deduction:** may apply, but
  only if the equipment carries a DEDE/EGAT Level 5-star certification, and it is
  unavailable for activities already under BOI exemption. Worth asking Keen
  whether the specified equipment is certified, since a 50% bonus deduction is
  material. Not modelled, because eligibility is unverified.
- **BOI promotion:** the project inventory records none for Rofu. Not modelled.

## 2. EIA

**Finding: no EIA, and no IEE. The requirement is threshold-based and this
project is below it.**

The environmental thresholds for solar are 5 MWp for an IEE and 10 MWp for a
full EIA. At roughly 1.7 MWp Rofu is below both.

So `permitting_and_eia_cost` carrying zero EIA cost is **correct**, not a stub.
That is a change in status: it was previously zero because nobody had checked.

## 3. Permitting and interconnection

### What is actually required

1. **PEA grid interconnection approval** (30-60 days), including an anti-islanding
   certificate to UL 1741 or IEEE 1547 per ERC Grid Code B.E. 2559.
2. **Aor.6 building modification permit** (30-45 days) from the local authority,
   with structural drawings by a licensed civil engineer.
3. **ERC generation licence**, triggered at 1 MWp and up. At 1.685 MW Rofu needs
   one. Adds 30-45 days.
4. **COD inspection and permit to operate.**

Note a 2024 change that removes a step people still expect: since 27 December
2024 a factory installing rooftop solar **no longer needs a Ror.Ngor.4 (factory)
licence**, including above 1 MW.

### Costs

Citable figures are small and administrative:

- PEA/MEA grid-connection permit fees and associated engineering: **5,000-15,000
  THB**.
- Connection charge under the Direct PPA rules: **10,000 THB**.
- Residential interconnection inspection fee: 2,000 THB excluding VAT (quoted for
  completeness; not the C&I case).

At 32.5 THB/USD, 10,000 THB is about **USD 308**, roughly 0.03% of a project of
this size. The conclusion worth carrying into the proforma is that **PEA
interconnection is not a material capex line**. Physical scope that could be
material (protection relays, metering, any transformer work) normally sits inside
the EPC contract, not as a separate utility charge, so it should be captured in
`pv_installed_cost_per_kw` rather than here.

### What we could not cite

No public fee schedule exists for the Aor.6 permit or the ERC generation licence,
and engineering/drawing costs are quotation-specific. Per the user's instruction,
these stay at zero rather than being invented, and the report must state that
project capex excludes them.

## 4. Values set

| Key | Value | Status |
|---|---|---|
| `pv_depreciation_years` | 5 | Cited, Royal Decree No. 145. Classification caveat above. |
| `bess_depreciation_years` | 5 | Cited, Royal Decree No. 145. |
| `grid_connection_cost` | 308.0 USD | Cited, 10,000 THB at 32.5. Still placeholder-marked. |
| `permitting_and_eia_cost` | 0.0 | EIA/IEE genuinely not required below 5 MWp. Aor.6 and ERC fees excluded and disclosed. Still placeholder-marked. |

## Sources

- Sherrings, Thailand tax depreciation rates: https://sherrings.com/depreciation-tax-rates-thailand.html
- Thai Revenue Department, Royal Decree: https://www.rd.go.th/english/27736.html
- PwC, Thailand corporate deductions: https://taxsummaries.pwc.com/thailand/corporate/deductions
- Mahanakorn Partners, deductions for investment in machinery: https://mahanakornpartners.com/tax-insights-thailand-corporate-tax-deductions-for-investment-in-machinery/
- Royal Decree No. 805 incentives: https://www.bizwings.co/post/thailand-introduces-tax-incentives-for-solar-rooftop-installation-and-energy-efficient-machinery
- Thailand solar permits and thresholds: https://capsolar.co.th/en/knowledge/solar-permit-approvals-thailand
- Tilleke and Gibbins, factory licence removal: https://www.tilleke.com/insights/thailand-removes-factory-license-requirement-for-solar-rooftop-installations/3/
- Watson Farley and Williams, rooftop regulatory shift: https://www.wfw.com/articles/unlocking-solar-potential-thailands-regulatory-shift-on-rooftop-solar-systems/
