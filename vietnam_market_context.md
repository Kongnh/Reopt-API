# Vietnam Market Context

> **Last updated:** 2026-03-30
> **Purpose:** Domain knowledge for post-processing layer — tariff math, DPPA mechanics, loss factors

---

## EVN Tariff Structure

### Standard TOU (Industrial/Commercial)

| Period | Hours | Multiplier vs base |
|--------|-------|--------------------|
| Off-peak (thấp điểm) | 22:00–04:00 | ~0.52× |
| Normal (bình thường) | 04:00–09:30, 11:30–17:00, 20:00–22:00 | 1.0× |
| Peak (cao điểm) | 09:30–11:30, 17:00–20:00 | ~1.78× |

**Sunday rule:** No peak period on Sundays (all hours treated as normal).

**Rates by voltage level** (approximate 2025, USD/kWh at 25,000 VND/USD):

| Voltage | Off-peak | Normal | Peak |
|---------|----------|--------|------|
| ≥110kV | ~0.034 | ~0.065 | ~0.116 |
| 22–110kV | ~0.037 | ~0.070 | ~0.126 |
| 6–22kV | ~0.042 | ~0.079 | ~0.141 |
| <6kV | ~0.049 | ~0.092 | ~0.164 |

### 2-Component Pilot Tariff (Giá điện 2 thành phần)

> Source: EVNNPC guidance ref. 7646/BCT-ĐL, 2025-10-09. Status: paper simulation only.

**Formula:** `TC = Cp × P_max + Ca × kWh_consumed`

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

**Eligibility:** Industrial customers ≥200,000 kWh/month average. Opt-in, not mandatory.

---

## DPPA Mechanics

### Physical DPPA (Private Wire)
- Direct connection between RE plant and factory — no EVN grid involvement for contracted energy
- All voltage levels eligible
- Factory pays: `matched_kwh × ppa_price` + residual grid at EVN rate
- Developer earns: `matched_kwh × ppa_price` + `surplus_kwh × surplus_rate`
- No wheeling charges (private wire bypasses EVN grid)

### Virtual DPPA (CfD, Decree 57/2025/NĐ-CP)
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

**Official K_pp values (2025):**

| Voltage | K_pp | Effective loss rate |
|---------|------|---------------------|
| ≥110kV | 1.008525 | 2.790% |
| 22–110kV | 1.027263 | 4.563% |
| 6–22kV | TBD | — (awaiting NLDC/EVN) |
| <6kV | TBD | — (awaiting NLDC/EVN) |

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

**Key economics insight:** Grid fees (service ~0.5¢ + settlement ~0.3¢ = 0.8¢/kWh) consume the entire CfD premium at a 6.5¢ strike price. Virtual DPPA is structurally disadvantaged vs physical. Viable path: strike ≥7.0¢ + USD-denominated loan (~5%).

---

## FMP/CFMP Market Prices (2025)

| Price | VND/kWh | USD/kWh (at 25,000) |
|-------|---------|---------------------|
| FMP (mean 2025) | 1,426.6 | 0.057066 |
| CFMP (mean 2025) | 1,464.8 | 0.058592 |

Hourly 8760 series available in `data/vietnam/fmp_cfmp_vn.json` (on archive branch).

---

## Vietnam Financial Parameters

| Parameter | Default | Source |
|-----------|---------|--------|
| CIT rate | 20% | Standard |
| CIT holiday | 4yr exempt + 9yr 50% reduced | Decree 31/2021 RE projects |
| Depreciation | Straight-line | Circular 45/2013/TT-BTC |
| PV useful life | 10yr | Ministry of Finance |
| BESS useful life | 8yr | Ministry of Finance |
| Debt fraction | 70% | Typical Vietnam RE |
| Loan rate (VND) | 8.5%/yr | Commercial bank |
| Loan rate (USD) | ~5%/yr | International financing |
| Equity IRR target | 12–15% | Developer requirement |
| EVN escalation | 4%/yr | Historical trend 2015–2024 |
| Analysis years | 25 | Standard project life |
| Exchange rate | 25,000 VND/USD | 2025 reference |

---

## BESS Specifics for Vietnam

- SoH replacement threshold: configurable (default 80%, can lower to 70%)
- BESS replaced when SoH < threshold — replacement cost is CIT-adjusted NPV
- Typical Vietnam BESS sizing: 2–4 hours duration (for peak shaving / arbitrage)
- Charge: off-peak (22:00–04:00), discharge: peak (09:30–11:30, 17:00–20:00)

---

## References

- EVN Tariff: Decision 1062/QD-EVN (standard TOU)
- 2-component pilot: EVNNPC ref. 7646/BCT-ĐL, 2025-10-09
- DPPA: Decree 57/2025/NĐ-CP (replaces Decree 80/2024)
- CIT incentives: Vietnam Investment Law, Enterprise Income Tax Law
- K_pp loss factors: NLDC/EVN official 2025 announcement
- FMP/CFMP: Vietnam Wholesale Electricity Market (VWEM) 2025 data
