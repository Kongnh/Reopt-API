# Vietnam Market Context

> **Last updated:** 2026-07-05
> **Purpose:** Domain knowledge for post-processing layer — tariff math, DPPA mechanics, loss factors
> **2026-07-05 revision:** Decree 243/2026 amendments, two-component tariff rollout status,
> CIT Law 67/2025, FX, and solar ceiling frame verified against primary sources (see References).

---

## Regulatory Update — Decree 243/2026/NĐ-CP (issued & effective 2026-06-26)

Amends Decree 57/2025/NĐ-CP (DPPA) and Decree 58/2025/NĐ-CP (RE self-consumption).

### Rooftop surplus sales (amends ND58)
- Surplus sale cap raised **20% → 50%** of rooftop-solar output.
- From 2026-06-26 to **2030-12-31**, parties may agree to sell **above 50%** where the
  grid can safely absorb it (grid-capacity conditions apply).
- No cap for off-grid remote areas (mountain/border/island) until grid-connected.
- **Surplus purchase price** = previous year's **average electricity market price**
  (published by the market operator), **capped at the ground-mounted-solar
  (no storage) ceiling** of the generation price frame, excl. VAT.
  - 2025 average market price ≈ 1,426.6 VND/kWh (our FMP series mean) → the
    **regional ceiling binds** everywhere in 2026 (see ceiling frame below).
- Rooftop systems serving large customers no longer need development-registration
  procedures; provincial People's Committees get expanded approval authority.

### DPPA changes (amends ND57)
- **Private-wire (physical) DPPA: price ceiling removed** — parties negotiate the
  directly-traded price freely. Only surplus sold to EVN/utilities remains capped by
  the source-type ceiling.
- Participants expanded: **data centers, EV charging stations, EV battery-swap
  stations, urban zones/clusters, retail electricity units in zones & clusters**.
  Trilateral models allowed (RE genco → retail unit → large consumer).
- Both EVN-affiliated units and private enterprises may purchase surplus.
- No changes found to virtual-DPPA settlement math, K_pp, or fee structure
  (2025 values remain in force; 2026 CDPPAdv pending retail-price approval).

### Solar generation price frame (Decision 988/QĐ-BCT, 2025-04-10) — ceilings, excl. VAT

| Type | North | Central | South |
|------|-------|---------|-------|
| Ground-mounted, no storage | 1,382.7 | 1,107.1 | 1,012.0 |
| Ground-mounted, with storage* | 1,571.98 | 1,257.05 | 1,149.86 |

*Storage qualification: ≥10% of plant capacity, ≥2h discharge, ≤5% of plant output used for charging.
The no-storage ground-mounted ceiling is the cap for Decree 243 surplus purchases.

---

## EVN Tariff Structure

### Standard TOU (Industrial/Commercial)

Basis: **Decision 1279/QĐ-BCT (2025-05-09)**, average retail price 2,204.0655 VND/kWh
excl. VAT (+4.8% vs Decision 2699/QĐ-BCT of Oct 2024). **Still in force as of
2026-07** — no further average-price adjustment through May 2026; Decision
14/2025/QĐ-TTg (residential tier restructure 6→5) does not affect manufacturing TOU.

| Period | Hours | Multiplier vs base |
|--------|-------|--------------------|
| Off-peak (thấp điểm) | 22:00–04:00 | ~0.52× |
| Normal (bình thường) | 04:00–09:30, 11:30–17:00, 20:00–22:00 | 1.0× |
| Peak (cao điểm) | 09:30–11:30, 17:00–20:00 | ~1.78× |

**Sunday rule:** No peak period on Sundays (all hours treated as normal).

**Rates by voltage level** (2025 decision, USD/kWh at 25,000 VND/USD):

| Voltage | Off-peak | Normal | Peak |
|---------|----------|--------|------|
| ≥110kV | ~0.034 | ~0.065 | ~0.116 |
| 22–110kV | ~0.037 | ~0.070 | ~0.126 |
| 6–22kV | ~0.042 | ~0.079 | ~0.141 |
| <6kV | ~0.049 | ~0.092 | ~0.164 |

### 2-Component Tariff (Giá điện 2 thành phần) — rollout status 2026-07

> Phased MOIT rollout (draft decision, four phases). **Not yet universal.**
> - Oct–Dec 2025: parallel reference invoices (pilot group).
> - Jan–Jun 2026: communication + paper testing, parallel invoices, all participants.
> - **Jul 2026 – Jul 2027: official testing with ACTUAL PAYMENT for selected
>   production customers ≥200,000 kWh/month connected at ≥22kV** (the DPPA-eligible segment).
> - From Aug 2027: comprehensive evaluation before full rollout.
> Modeling stance: keep two-component as an explicit scenario toggle; it is the
> realistic BAU only for large customers selected into the Jul-2026 phase.

**Formula:** `TC = Cp × P_max + Ca × kWh_consumed`

Published pilot unit prices (EVNNPC guidance ref. 7646/BCT-ĐL, 2025-10-09 — still
the operative published table; official 2026 pilot-phase rates pending):

| Voltage | Cp (VND/kW/month) | Ca Normal (VND/kWh) | Ca Peak (VND/kWh) | Ca Off-peak (VND/kWh) |
|---------|-------------------|---------------------|-------------------|-----------------------|
| ≥110kV | 209,459 | 1,253 | 2,162 | 843 |
| 22–110kV | 235,414 | 1,275 | 2,182 | 859 |
| 6–22kV | 240,050 | 1,280 | 2,189 | 871 |
| <6kV | 286,153 | 1,332 | 2,251 | 904 |

**P_max** = peak 30-min average demand in billing month (kW).

**REopt mapping:**
- Ca rates → `tou_energy_rates_per_kwh` (8760 absolute values, not multipliers)
- Cp → `monthly_demand_rates` (12-element vector, same value each month)

**Eligibility:** Industrial customers ≥200,000 kWh/month average, ≥22kV. Opt-in in the model.

---

## DPPA Mechanics

### Physical DPPA (Private Wire)
- Direct connection between RE plant and factory — no EVN grid involvement for contracted energy
- All voltage levels eligible
- **Price freely negotiated (Decree 243 removed the ceiling for directly-traded volume)**
- Factory pays: `matched_kwh × ppa_price` + residual grid at EVN rate
- Developer earns: `matched_kwh × ppa_price` + `surplus_kwh × surplus_rate`
  (surplus to EVN capped at the source-type ceiling price)
- No wheeling charges (private wire bypasses EVN grid)

### Virtual DPPA (CfD, Decree 57/2025/NĐ-CP as amended by 243/2026)
- Financial settlement through EVN grid
- Eligible voltage levels: **≥110kV and 22–110kV only** (ND57 Art. 16)
- 6–22kV and <6kV cannot use virtual DPPA — physical only

**Settlement quantity formula:**
```
Q_m(h) = Q_mq(h) / (k × K_pp) × δ
```
- `Q_mq(h)` = measured generation at RE plant meter (developer POC)
- `k` = 1.02 (transmission loss factor, fixed by VWEM)
- `K_pp` = distribution loss factor (voltage-dependent)
- `δ` = energy allocation fraction (default 1.0 for single buyer)
- `Q_m(h)` = delivered RE energy at factory POC (settlement basis)

**Official K_pp values (2025, confirmed still current 2026-07; 2026 update pending):**

| Voltage | K_pp | Effective loss rate |
|---------|------|---------------------|
| ≥110kV | 1.008525 | 2.790% |
| 22–110kV | 1.027263 | 4.563% |
| 6–22kV | TBD | — (awaiting NLDC/EVN) |
| <6kV | TBD | — (awaiting NLDC/EVN) |

**Official 2025 fee values (EVN notice 08/05/2025; 2026 values pending retail-price approval):**
- `CDPPAdv` (system service fee): **360.14 VND/kWh** provisional 2025 (model default 360.0).
- `PCL` (settlement adder): **163.2–163.3 VND/kWh** — secondary sources disagree on the
  last digit; the NSMO CD7 worked example uses 163.3, which the model reproduces exactly.
  Verify against EVN letter "Giao các TCTĐL thông báo các chi phí… 080525.pdf" (in
  `DPPA DOC/`) before changing. Keeping 163.3 pending that check.

**Developer revenue (virtual):**
```
R_spot(h) = Q_mq(h) × FMP(h)              # wholesale at developer POC
R_CfD(h) = Q_Khc(h) × (Strike - FMP(h))   # CfD settlement (can be negative)
Q_Khc(h) = min(load(h), Q_m(h))            # matched at factory POC
```

**Factory cost (virtual):**
```
CDN(h) = Q_Khc(h) × CFMP(h) × K_pp       # RE energy charge (reference price × K_pp)
CCL(h) = Q_Khc(h) × PCL                   # balancing cost adder
C_DPPA(h) = Q_Khc(h) × CDPPAdv           # DPPA service charge
C_BL(h) = (load(h) - Q_Khc(h)) × EVN_rate(h)  # residual retail
Total_factory_cost = Σ(CDN + CCL + C_DPPA + C_BL) + capacity_charge
```

**Key economics insight:** Grid fees (service ~0.5¢ + settlement ~0.3¢ = 0.8¢/kWh) consume the entire CfD premium at a 6.5¢ strike price. Virtual DPPA is structurally disadvantaged vs physical. Viable path: strike ≥7.0¢ + USD-denominated loan (~5%). **Decree 243 strengthens the physical-DPPA case further (free price negotiation).**

---

## FMP/CFMP Market Prices (2025)

| Price | VND/kWh | USD/kWh (at 25,000) |
|-------|---------|---------------------|
| FMP (mean 2025) | 1,426.6 | 0.057066 |
| CFMP (mean 2025) | 1,464.8 | 0.058592 |

Hourly 8760 series in `DPPA DOC/fmp_cfmp_vn.json`. **2026 series not yet published
in usable form — 2025 series remains the modeling basis (logged simplification).**

---

## Vietnam Financial Parameters

| Parameter | Default | Source |
|-----------|---------|--------|
| CIT standard rate | 20% | Law 67/2025/QH15 |
| CIT preferential (RE producer) | **10% for 15 years** from first revenue year | Law 67/2025/QH15 (effective 2025-10-01, from tax year 2025) + Decree 320/2025/NĐ-CP |
| CIT holiday | 4yr exempt + 9yr **50% of applicable rate** | Law 67/2025; clock starts first profit year, latest year 4 |
| RE-producer effective schedule | 0% (y1–4), 5% (y5–13), 10% (y14–15), 20% (y16+) | 50% of 10% preferential during reduction years |
| ESCO (service co.) schedule | 0% (y1–4), 10% (y5–13), 20% (y14+) | Conservative: RE-producer status for a service ESCO is a legal question; grandfather clause preserves old-law incentives |
| Industrial-zone location incentive | **Removed** for new projects | Law 67/2025 |
| Loss carryforward | 5 years, FIFO | unchanged |
| Depreciation | Straight-line | Circular 45/2013/TT-BTC |
| PV useful life | 7–20yr band, default 20yr | Circular 45/2013 |
| BESS useful life | 8yr | Circular 45/2013 |
| Debt fraction | 70% | Typical Vietnam RE |
| Loan rate (VND) | 8.5%/yr | Commercial bank |
| Loan rate (USD) | ~5%/yr | International financing |
| Equity IRR target | 12–15% | Developer requirement |
| EVN escalation | 4%/yr | Historical trend 2015–2024 |
| Analysis years | 25 | Standard project life |
| Exchange rate | **26,300 VND/USD** (2026-06; 2026 avg ≈ 26,244; was 25,000 in 2025) | Market data; VND depreciated ~1.4% y/y |

---

## BESS Specifics for Vietnam

- SoH replacement threshold: configurable (default 80%, can lower to 70%)
- BESS replaced when SoH < threshold — replacement cost is CIT-adjusted NPV
- Typical Vietnam BESS sizing: 2–4 hours duration (for peak shaving / arbitrage)
- Charge: off-peak (22:00–04:00), discharge: peak (09:30–11:30, 17:00–20:00)

---

## References

- EVN retail tariff: Decision 1279/QĐ-BCT (2025-05-09), avg 2,204.0655 VND/kWh excl. VAT
- Retail tariff structure: Decision 14/2025/QĐ-TTg (residential tiers 6→5)
- 2-component pilot rates: EVNNPC ref. 7646/BCT-ĐL, 2025-10-09; phased MOIT rollout
  (actual payment for selected ≥200MWh/mo ≥22kV customers from Jul 2026)
- DPPA: Decree 57/2025/NĐ-CP, **amended by Decree 243/2026/NĐ-CP (2026-06-26)**
- RE self-consumption: Decree 58/2025/NĐ-CP, **amended by Decree 243/2026/NĐ-CP**
- Solar generation price frame (surplus ceiling): Decision 988/QĐ-BCT (2025-04-10)
- CIT: **Law 67/2025/QH15** (2025-06-14, effective 2025-10-01) + **Decree 320/2025/NĐ-CP**
  (2025-12-15); supersedes Circular 78/2014 framework for new projects
- K_pp loss factors & DPPA fees: NLDC/EVN 2025 announcements (CDPPAdv 360.14 provisional;
  PCL 163.2/163.3 — see DPPA DOC PDF); 2026 values pending
- FMP/CFMP: VWEM 2025 data (`DPPA DOC/fmp_cfmp_vn.json`)
- FX: USD/VND ≈ 26,300 (Jun 2026), 2026 avg ≈ 26,244
