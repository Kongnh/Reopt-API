# Fade-aware battery sizing: REopt degradation (A) against a fixed-size grid (D)

Research line (`battery-soh-fade`, worktree `REopt_API-soh`), 2026-09-12
night. Ruling: A + D, run on the worktree, full delegation. Nothing on
`master` was changed; the findings that belong on `master` are listed at the
end for the user to rule on.

## Question

Once the year-10 replacement left the objective (2026-09-12 morning), REopt
sized batteries with nothing in the objective that ages them, and the pro
forma derated the savings afterwards. Which sizing method puts the battery at
the top of the number the workbook reports (the fade-derated equity NPV), and
how far off is today's size?

## Method

`proforma_vietnam/tools/fade_sizing_probe.py` re-solves a kept case straight
against a Julia server and scores every candidate with the same pro forma
call the workbooks use (`calculate_esco_pro_forma_from_reopt_results` with
the case's own assumptions, SOH derate on):

- `blind`: REopt as run today, sizes free, no ageing in the objective.
- `deg` (method A): `ElectricStorage.model_degradation = true`, augmentation
  strategy (linear, no binaries). REopt's SOH recurrence carries an
  hours-per-step factor `h`, so the coefficients are passed as `k / h`
  (Vietnam hourly: unchanged; Thailand 15 minute: times 4) and the optimiser
  then ages the battery exactly as `battery_soh` does at h = 1. `k_cyc` =
  0.2 / 8,000 EFC = 2.5e-5 from the cycle-life ruling; calendar coefficients
  NREL's; augmentation priced at the case's `installed_cost_per_kwh` declining
  3 percent a year (REopt's default is 5).
- `grid` (method D): REopt without ageing at pinned energy capacities (0,
  0.25 ... 1.25 of the blind size, power and PV free), plus the `deg` size
  pinned the same way so it sits on the same curve, plus one refinement
  round around the best point. Every grid point is also re-solved with
  degradation on (`grid_deg`) to separate the sizing effect from the
  dispatch effect.

Two pieces of infrastructure were needed and are kept on the research line:

1. Django's V3 models do not accept `model_degradation`, so the probe posts
   to Julia directly, and REopt.jl 0.57 types the vector-valued degradation
   inputs as `Vector{<:Real}` while `JSON.parse` yields `Vector{Any}`
   (`dictkeys_tosymbols` does not convert those keys), so
   `cycle_fade_coefficient` could not be set over HTTP at all. The
   worktree's `julia_src/http.jl` coerces them. The research line runs its
   own Julia container for that file: `julia_api_soh` (image
   `reopt_api-julia:soh`, committed from the running shared container so
   the compiled cache came along), port 8082, mounting the worktree's
   `julia_src`. `docker start julia_api_soh` brings it back. The shared
   8081 server and Django on 8000 serve `master`.
2. The kept run's echoed inputs are self-contained (load, production factor
   and tariff series inline), so a solve needs nothing from Django; each
   solve is saved Django-shaped (`inputs` + `outputs`) so the pro forma reads
   it unchanged. The BAU solve is kept because the pro forma reads the BAU
   bill. Per-solve files are gitignored (4 MB each); `summary.json` and
   `summary.md` per case are committed under `outputs/research/fade_sizing/`.

Wrapper check: Thailand case_6 re-solved on 8082 with unchanged inputs lands
on the kept sizes and NPV to the dollar (815 kW / 4,047 kWh, 2,161,251), so
the direct path is faithful to the Django path.

## Finding 1: the Vietnam objective carries US tax incentives (both lines)

The Vietnam builder sends `Financial: {analysis_years, owner_discount_rate}`
and PV / storage blocks without incentive fields, so Django fills REopt's US
defaults and echoes them into the solve:

| field | sent by the Vietnam builder | what REopt optimised with | pro forma uses |
|---|---|---|---|
| PV `federal_itc_fraction` | (absent) | 0.30 | none |
| PV / storage `macrs_option_years`, `macrs_bonus_fraction` | (absent) | 5 years, 100 percent bonus | straight-line 20 / 8 years |
| storage `total_itc_fraction` | (absent) | 0.30 | none |
| `offtaker_discount_rate_fraction` | (absent) | 0.0624, and because `third_party_ownership` is false REopt overrides the owner rate with it, so the sent 0.10 was discarded | 0.10 |
| `owner_tax_rate_fraction`, `offtaker_tax_rate_fraction` | (absent) | 0.26 | 0.20 CIT |
| `elec_cost_escalation_rate_fraction` | (absent) | 0.0166 | 0.04 EVN |
| `om_cost_escalation_rate_fraction` | (absent) | 0.025 | 0.03 |

REopt's own echo shows it: Vietnam case_1 `initial_capital_costs` 4,218,573
against `initial_capital_costs_after_incentives` 2,149,789. The optimiser has
been buying PV and batteries at 51 percent of their price and discounting at
6.24 percent. Thailand's builder zeroes all of this explicitly
(`proforma_thailand/case_builder.py`, the "C2 critical" of the 2026-09-05
plan); the Vietnam builder never got the same fix, and `MODEL_AUDIT.md` does
not know about it. This is older than the SOH work and sits on `master` too.

Effect when the objective is aligned (incentives off, 10 percent discount,
20 percent CIT, 4 percent EVN escalation, 3 percent O&M escalation):

| case | PV kW | BESS kW / kWh | derated NPV USD | equity IRR | min DSCR |
|---|---|---|---|---|---|
| Vietnam case_1, as kept | 5,701 | 1,896 / 11,087 | 585,319 | 13.3% | 1.02 |
| Vietnam case_1, aligned | 3,520 | 1,031 / 4,079 | 1,111,148 | 22.2% | 1.37 |
| Vietnam case_3, as kept | 6,071 | 2,220 / 14,337 | -470,729 | - | 0.78 |
| Vietnam case_3, aligned | 2,188 | 579 / 3,088 | 389,852 | 16.2% | 1.12 |

The kept Vietnam systems are roughly 1.6 times too much PV and 2.7 to 4.6
times too much battery for the economics the pro forma books, and the ESCO
NPV is understated by half (case_1) or has the wrong sign (case_3). The
aligned REopt objective lands within about 1 percent of the pro forma NPV
(case_1: REopt 1,097,499 against pro forma 1,111,148), which is the
consistency the sizing needs.

## Results

All rows scored by the fade-derated pro forma with the case's own assumptions; deg rows carry the kWh O&M restored (see below). "Fade loss PV" is the present worth of the savings the derate removes; "augmentation PV" the present worth of topping the capacity up daily at the installed USD/kWh declining 3 percent a year, both at the owner discount rate.

### Vietnam case_1 (ESCO, PV + BESS, hourly)

| sizing | PV kW | BESS kW | BESS kWh | capex USD | pro forma NPV USD | equity IRR | min DSCR | SOH y20 | EFC y1 | fade loss PV | augmentation PV | REopt degr cost PV | solve s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kept (Django run, as today) | 5,701 | 1,896 | 11,087 | 4,218,573 | 585,319 | 13.3% | 1.02 | 85.9% | 215 | 172,869 | 78,188 | - | - |
| blind, incentives off + aligned Financial | 3,520 | 1,031 | 4,079 | 2,261,868 | 1,111,148 | 22.2% | 1.37 | 84.1% | 264 | 104,835 | 31,373 | - | 24.4 |
| deg (fade-aware objective, sizes free) | 3,539 | 1,067 | 4,222 | 2,290,614 | 1,116,497 | 22.1% | 1.37 | 84.8% | 262 | 100,701 | 30,291 | 29,386 | 189.1 |
| grid point at the deg size (blind dispatch) | 3,545 | 1,067 | 4,222 | 2,293,867 | 1,111,349 | 22.0% | 1.37 | 84.1% | 262 | 107,300 | 32,329 | - | 9.0 |
| grid point at the ESCO-share size (rates x 0.9 / 0.8 when sizing) | 3,149 | 612 | 2,423 | 1,851,449 | 1,080,697 | 24.6% | 1.46 | 83.0% | 284 | 70,837 | 19,680 | - | 19.5 |
| grid best (blind dispatch, argmax derated NPV) | 3,545 | 1,067 | 4,222 | 2,293,867 | 1,111,349 | 22.0% | 1.37 | 84.1% | 262 | 107,300 | 32,329 | - | 9.0 |

Derated NPV against battery energy capacity (power free, PV free, blind dispatch; the fade-aware dispatch column re-solves the same size with `model_degradation` on):

| fraction of blind kWh | BESS kWh | BESS kW | PV kW | NPV blind dispatch | NPV fade-aware dispatch | dispatch gain | SOH y20 blind | SOH y20 fade-aware |
|---|---|---|---|---|---|---|---|---|
| 0.000 | 0 | 0 | 2,656 | 919,745 | - | - | - | - |
| 0.250 | 1,020 | 341 | 2,859 | 1,016,671 | 1,018,569 | 1,898 | 80.7% | 81.6% |
| 0.500 | 2,040 | 516 | 3,061 | 1,067,642 | 1,070,371 | 2,729 | 82.7% | 83.4% |
| 0.594 | 2,423 | 612 | 3,149 | 1,080,697 | 1,083,837 | 3,139 | 83.0% | 83.7% |
| 0.750 | 3,060 | 773 | 3,297 | 1,097,603 | 1,101,431 | 3,828 | 83.5% | 84.2% |
| 1.000 | 4,079 | 1,031 | 3,520 | 1,111,148 | 1,116,160 | 5,012 | 84.1% | 84.7% |
| 1.017 | 4,151 | 1,049 | 3,527 | 1,111,258 | 1,116,386 | 5,129 | 84.1% | 84.8% |
| 1.035 (deg size) | 4,222 | 1,067 | 3,545 | 1,111,349 | 1,116,498 | 5,149 | 84.1% | 84.8% |
| 1.052 | 4,293 | 1,085 | 3,555 | 1,111,248 | 1,116,487 | 5,239 | 84.2% | 84.9% |
| 1.250 | 5,099 | 1,309 | 3,694 | 1,099,807 | 1,106,113 | 6,305 | 84.7% | 85.4% |

REopt SOH (coefficients / h) against the pro forma replica on the deg dispatch: max abs diff 0.0005; REopt end SOH 0.853, replica 0.848. REopt's degradation cost 29,386 USD PV against the offline augmentation 30,291 USD PV and the derate's lost value 100,701 USD PV.

Fields changed for the aligned objective: Financial.owner_discount_rate_fraction 0.0624 to 0.1, Financial.offtaker_discount_rate_fraction 0.0624 to 0.1, Financial.owner_tax_rate_fraction 0.26 to 0.2, Financial.offtaker_tax_rate_fraction 0.26 to 0.2, Financial.elec_cost_escalation_rate_fraction 0.0166 to 0.04, Financial.om_cost_escalation_rate_fraction 0.025 to 0.03, PV.federal_itc_fraction 0.3 to 0, PV.macrs_option_years 5 to 0, PV.macrs_bonus_fraction 1.0 to 0, ElectricStorage.total_itc_fraction 0.3 to 0, ElectricStorage.macrs_option_years 5 to 0, ElectricStorage.macrs_bonus_fraction 1.0 to 0.

### Vietnam case_3 (ESCO, demand-charge tariff, hourly)

| sizing | PV kW | BESS kW | BESS kWh | capex USD | pro forma NPV USD | equity IRR | min DSCR | SOH y20 | EFC y1 | fade loss PV | augmentation PV | REopt degr cost PV | solve s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kept (Django run, as today) | 6,071 | 2,220 | 14,337 | 4,812,252 | -470,729 | 7.7% | 0.78 | 85.6% | 224 | 262,774 | 102,496 | - | - |
| blind, incentives off + aligned Financial | 2,188 | 579 | 3,088 | 1,467,206 | 389,852 | 16.2% | 1.12 | 84.5% | 245 | 95,288 | 23,506 | - | 24.4 |
| deg (fade-aware objective, sizes free) | 2,222 | 597 | 3,273 | 1,507,051 | 395,079 | 16.1% | 1.12 | 85.4% | 245 | 91,396 | 22,876 | 22,220 | 40.0 |
| grid point at the deg size (blind dispatch) | 2,229 | 597 | 3,273 | 1,510,313 | 389,309 | 16.1% | 1.12 | 84.5% | 245 | 99,093 | 24,861 | - | 15.3 |
| grid point at the ESCO-share size (rates x 0.9 / 0.8 when sizing) | 1,758 | 392 | 1,299 | 1,030,815 | 341,180 | 17.9% | 1.20 | 84.0% | 253 | 54,501 | 10,253 | - | 12.7 |
| grid best (blind dispatch, argmax derated NPV) | 2,181 | 571 | 2,995 | 1,451,877 | 390,068 | 16.3% | 1.13 | 84.5% | 245 | 93,440 | 22,838 | - | 13.3 |

Derated NPV against battery energy capacity (power free, PV free, blind dispatch; the fade-aware dispatch column re-solves the same size with `model_degradation` on):

| fraction of blind kWh | BESS kWh | BESS kW | PV kW | NPV blind dispatch | NPV fade-aware dispatch | dispatch gain | SOH y20 blind | SOH y20 fade-aware |
|---|---|---|---|---|---|---|---|---|
| 0.000 | 0 | 0 | 1,209 | 132,470 | - | - | - | - |
| 0.250 | 772 | 318 | 1,549 | 312,537 | 316,346 | 3,810 | 83.7% | 85.3% |
| 0.421 | 1,299 | 392 | 1,758 | 341,180 | 345,586 | 4,406 | 84.0% | 85.3% |
| 0.500 | 1,544 | 423 | 1,839 | 350,328 | 355,058 | 4,731 | 84.0% | 85.3% |
| 0.750 | 2,316 | 504 | 2,016 | 375,871 | 381,337 | 5,466 | 84.3% | 85.4% |
| 0.970 | 2,995 | 571 | 2,181 | 390,068 | 395,472 | 5,404 | 84.5% | 85.4% |
| 1.000 | 3,088 | 579 | 2,188 | 389,852 | 395,653 | 5,801 | 84.5% | 85.4% |
| 1.030 | 3,180 | 589 | 2,224 | 389,840 | 395,353 | 5,513 | 84.5% | 85.4% |
| 1.060 (deg size) | 3,273 | 597 | 2,229 | 389,309 | 395,079 | 5,770 | 84.5% | 85.4% |
| 1.250 | 3,860 | 654 | 2,335 | 382,763 | 388,522 | 5,760 | 84.6% | 85.4% |

REopt SOH (coefficients / h) against the pro forma replica on the deg dispatch: max abs diff 0.0005; REopt end SOH 0.859, replica 0.854. REopt's degradation cost 22,220 USD PV against the offline augmentation 22,876 USD PV and the derate's lost value 91,396 USD PV.

Fields changed for the aligned objective: Financial.owner_discount_rate_fraction 0.0624 to 0.1, Financial.offtaker_discount_rate_fraction 0.0624 to 0.1, Financial.owner_tax_rate_fraction 0.26 to 0.2, Financial.offtaker_tax_rate_fraction 0.26 to 0.2, Financial.elec_cost_escalation_rate_fraction 0.0166 to 0.04, Financial.om_cost_escalation_rate_fraction 0.025 to 0.03, PV.federal_itc_fraction 0.3 to 0, PV.macrs_option_years 5 to 0, PV.macrs_bonus_fraction 1.0 to 0, ElectricStorage.total_itc_fraction 0.3 to 0, ElectricStorage.macrs_option_years 5 to 0, ElectricStorage.macrs_bonus_fraction 1.0 to 0.

### Thailand case_6 (direct ownership, PV + BESS, 15 min)

| sizing | PV kW | BESS kW | BESS kWh | capex USD | pro forma NPV USD | equity IRR | min DSCR | SOH y20 | EFC y1 | fade loss PV | augmentation PV | REopt degr cost PV | solve s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kept (Django run, as today) | 3,230 | 815 | 4,047 | 2,303,614 | 2,161,251 | 44.2% | 2.10 | 83.7% | 261 | 106,538 | 40,194 | - | - |
| blind, re-solved on 8082 (wrapper check) | 3,230 | 815 | 4,047 | 2,303,614 | 2,161,251 | 44.2% | 2.10 | 83.7% | 261 | 106,538 | 40,194 | - | 268.4 |
| deg (fade-aware objective, sizes free) | 3,230 | 831 | 4,203 | 2,328,617 | 2,172,154 | 44.0% | 2.09 | 84.7% | 259 | 103,858 | 38,347 | 35,542 | 397.7 |
| grid point at the deg size (blind dispatch) | 3,230 | 832 | 4,203 | 2,328,650 | 2,167,247 | 44.0% | 2.09 | 83.8% | 259 | 108,591 | 41,539 | - | 164.0 |
| grid best (blind dispatch, argmax derated NPV) | 3,230 | 998 | 5,565 | 2,549,497 | 2,191,768 | 41.3% | 2.00 | 84.5% | 244 | 123,337 | 52,831 | - | 131.6 |

Derated NPV against battery energy capacity (power free, PV free, blind dispatch; the fade-aware dispatch column re-solves the same size with `model_degradation` on):

| fraction of blind kWh | BESS kWh | BESS kW | PV kW | NPV blind dispatch | NPV fade-aware dispatch | dispatch gain | SOH y20 blind | SOH y20 fade-aware |
|---|---|---|---|---|---|---|---|---|
| 0.000 | 0 | 0 | 2,549 | 1,659,545 | - | - | - | - |
| 0.250 | 1,012 | 381 | 2,663 | 1,870,236 | 1,873,459 | 3,223 | 81.2% | 82.8% |
| 0.500 | 2,024 | 532 | 2,874 | 1,993,125 | 1,996,963 | 3,838 | 82.7% | 83.9% |
| 0.750 | 3,035 | 675 | 3,103 | 2,090,732 | 2,094,702 | 3,969 | 83.3% | 84.3% |
| 1.000 | 4,047 | 815 | 3,230 | 2,161,254 | 2,166,453 | 5,198 | 83.7% | 84.6% |
| 1.039 (deg size) | 4,203 | 832 | 3,230 | 2,167,247 | 2,172,527 | 5,280 | 83.8% | 84.7% |
| 1.125 | 4,553 | 895 | 3,230 | 2,178,658 | 2,183,994 | 5,336 | 84.0% | 84.9% |
| 1.250 | 5,059 | 957 | 3,230 | 2,189,179 | 2,194,523 | 5,345 | 84.2% | 85.1% |
| 1.375 | 5,565 | 998 | 3,230 | 2,191,768 | 2,197,273 | 5,506 | 84.5% | 85.4% |
| 1.500 | 6,071 | 1,031 | 3,230 | 2,186,720 | 2,192,487 | 5,767 | 84.9% | 85.8% |
| 1.750 | 7,082 | 1,078 | 3,230 | 2,154,204 | 2,160,407 | 6,203 | 85.9% | 86.7% |

REopt SOH (coefficients / h) against the pro forma replica on the deg dispatch: max abs diff 0.0005; REopt end SOH 0.851, replica 0.847. REopt's degradation cost 35,542 USD PV against the offline augmentation 38,347 USD PV and the derate's lost value 103,858 USD PV.

### Vietnam bess_arbitrage_5mw (grid arbitrage, 5 MW power pinned, hourly)

| sizing | PV kW | BESS kW | BESS kWh | capex USD | pro forma NPV USD | equity IRR | min DSCR | SOH y20 | EFC y1 | fade loss PV | augmentation PV | REopt degr cost PV | solve s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kept (Django run, as today) | 0 | 5,000 | 25,000 | 3,400,000 | 4,092,688 | 53.9% | 2.40 | 81.9% | 297 | 830,414 | 219,011 | - | - |
| blind, incentives off + aligned Financial | 0 | 5,000 | 25,000 | 3,400,000 | 4,092,688 | 53.9% | 2.40 | 81.9% | 297 | 830,414 | 219,011 | - | 5.5 |
| deg (fade-aware objective, sizes free) | 0 | 5,000 | 25,000 | 3,400,000 | 4,100,100 | 53.9% | 2.40 | 82.1% | 297 | 819,727 | 216,116 | 216,118 | 6.1 |
| grid point at the deg size (blind dispatch) | 0 | 5,000 | 25,000 | 3,400,000 | 4,092,688 | 53.9% | 2.40 | 81.9% | 297 | 830,414 | 219,011 | - | 5.2 |
| grid best (blind dispatch, argmax derated NPV) | 0 | 5,000 | 28,125 | 3,775,000 | 4,307,126 | 51.4% | 2.33 | 81.9% | 297 | 895,892 | 246,416 | - | 4.7 |

Derated NPV against battery energy capacity (power free, PV free, blind dispatch; the fade-aware dispatch column re-solves the same size with `model_degradation` on):

| fraction of blind kWh | BESS kWh | BESS kW | PV kW | NPV blind dispatch | NPV fade-aware dispatch | dispatch gain | SOH y20 blind | SOH y20 fade-aware |
|---|---|---|---|---|---|---|---|---|
| 0.250 | 6,250 | 5,000 | 0 | 714,861 | 731,262 | 16,402 | 81.2% | 82.7% |
| 0.500 | 12,500 | 5,000 | 0 | 1,835,885 | 1,859,126 | 23,241 | 81.5% | 82.5% |
| 0.750 | 18,750 | 5,000 | 0 | 2,961,685 | 2,982,215 | 20,530 | 81.7% | 82.3% |
| 0.875 | 21,875 | 5,000 | 0 | 3,526,573 | 3,541,771 | 15,198 | 81.8% | 82.2% |
| 1.000 | 25,000 | 5,000 | 0 | 4,092,688 | 4,100,100 | 7,412 | 81.9% | 82.1% |
| 1.000 (deg size) | 25,000 | 5,000 | 0 | 4,092,688 | 4,100,100 | 7,412 | 81.9% | 82.1% |
| 1.125 | 28,125 | 5,000 | 0 | 4,307,126 | 4,319,062 | 11,936 | 81.9% | 82.1% |
| 1.250 | 31,250 | 5,000 | 0 | 3,992,207 | 4,026,155 | 33,948 | 83.1% | 83.8% |

REopt SOH (coefficients / h) against the pro forma replica on the deg dispatch: max abs diff 0.0005; REopt end SOH 0.821, replica 0.821. REopt's degradation cost 216,118 USD PV against the offline augmentation 216,116 USD PV and the derate's lost value 819,727 USD PV.

Fields changed for the aligned objective: Financial.owner_discount_rate_fraction 0.0624 to 0.1, Financial.offtaker_discount_rate_fraction 0.0624 to 0.1, Financial.owner_tax_rate_fraction 0.26 to 0.2, Financial.offtaker_tax_rate_fraction 0.26 to 0.2, Financial.elec_cost_escalation_rate_fraction 0.0166 to 0.04, Financial.om_cost_escalation_rate_fraction 0.025 to 0.03, PV.federal_itc_fraction 0.3 to 0, PV.macrs_option_years 5 to 0, PV.macrs_bonus_fraction 1.0 to 0, ElectricStorage.total_itc_fraction 0.3 to 0, ElectricStorage.macrs_option_years 5 to 0, ElectricStorage.macrs_bonus_fraction 1.0 to 0.


## Reading the numbers

- **Sizing.** With the objective aligned, the ageing-blind size already
  sits on the flat top of the derated-NPV curve: Vietnam case_1 is within
  200 USD of the best grid point anywhere between 4,079 and 4,293 kWh,
  case_3 within 200 USD between 2,995 and 3,180 kWh. Method A moves the
  size by +3.5 percent (case_1) and +6 percent (case_3) and lands within 500
  USD of the blind size on the same blind-dispatch curve, inside the solver
  noise. The reason is arithmetic: on these duty cycles (245 to 265 EFC a
  year) the fade cost REopt prices is about 7 USD per kWh of capacity
  present worth, 6 percent of the 120 USD/kWh capex, so it barely bends a
  curve whose curvature comes from the tariff. Thailand
  case_6 is the exception, and not because of fade: its derated equity NPV
  keeps rising past the blind size and tops out between 1.25 and 1.5 times
  it (5,000 to 6,000 kWh; best grid point 5,565 kWh at 2,191,768 against
  2,161,254, +1.4 percent) with the roof-capped PV unchanged. The Thailand
  pro forma carries 70 percent debt at 6.5 percent against an 11 percent
  discount rate and 5-year depreciation, so every unit of capex earns a
  levered, tax-shielded gain that REopt's unlevered objective never sees;
  method A (4,203 kWh) does not find it either. The financing view of the
  objective, not ageing, is what moves the Thailand size.
- **Where the size was wrong.** The kept Vietnam sizes were not wrong
  because of ageing; they were wrong because the objective was buying at
  half price with a 6.24 percent discount rate. Aligning the objective takes
  case_1 from 11,087 to 4,079 kWh and case_3 from 14,337 to 3,088 kWh and
  roughly halves the PV. Thailand had no such leak.
- **Method A's small upward bias is REopt's O&M convention, not fade.** With
  `model_degradation` on, REopt drops the kWh share of storage O&M from the
  objective and from `year_one_om_costs_before_tax` (deemed covered by
  augmentation): about 10 USD/kWh present worth in Vietnam against a fade
  cost of 7 USD/kWh, so the kWh looks 3 USD cheaper than in the blind
  objective and A sizes a few percent larger. The pro forma reads that same
  O&M output, so the first pass scored every deg solve with 1 percent of the
  kWh capex a year missing (4,900 USD a year on case_1) and showed a false
  4.6 to 8.5 percent "dispatch gain". `fade_sizing_probe.restore_kwh_om`
  puts the O&M back before scoring; all numbers here carry it.
- **Dispatch.** Re-solving the *same* size with degradation on raises the
  derated NPV by 0.5 percent (case_1, +5,012) and 1.5 percent (case_3,
  +5,801) and 0.2 percent (Thailand, +5,199). Discharged energy, EFC and year-1 revenue are
  identical to the blind solve; the whole gain is resting state of charge.
  The blind dispatch fills the battery as soon as PV allows and lets it sit
  full (REopt's `add_soc_incentive` rewards a high SOC to break ties), so
  the day-average SOC is 54 percent (case_1) and 64 percent (case_3); the
  fade-aware dispatch charges as late as the evening discharge allows and
  rests at 41 and 46 percent, which cuts the calendar term of the fade by a
  quarter (case_1 20-year calendar fade 2.8 to 2.1 percent of capacity,
  cycle fade unchanged at 12.7 percent). That is an EMS rule, not a sizing
  result: charge late, do not park the battery full.
- **ESCO share in the objective: tested, not adopted.** Sizing with the
  rates scaled by the contract shares (energy 0.90, demand 0.80) gives a
  smaller system (case_1 2,423 kWh, case_3 1,299 kWh) whose derated equity
  NPV on the true-rate curve is *lower* (1,080,697 against 1,111,148;
  341,180 against 389,852). The equity NPV is levered (70 percent debt at
  8.5 percent against a 10 percent discount rate), so every unit of capex
  also carries a financing gain the optimiser does not see; on these two
  cases that pulls the optimum up by about as much as the share pulls it
  down, and the full-rate objective is the better proxy. Keep the full
  rates.
- **Augmentation against derate.** On the aligned sizes the present worth of
  the derate (savings lost to fade) is 25 to 31 USD per kWh of capacity;
  topping the capacity up daily at the installed price declining 3 percent a
  year costs 7.6 USD per kWh in Vietnam (120 USD/kWh) and 9.9 in Thailand
  (150 USD/kWh); REopt's own degradation cost agrees within 3 to 8 percent,
  the difference being its day-count discounting. Keeping the
  capacity is about a quarter of the cost of losing it, so if a
  capacity-maintenance contract exists at anything near the installed
  USD/kWh, the pro forma should book that instead of derating, and the
  reported NPV rises by roughly the difference (about 70,000 USD on either
  Vietnam case). Both treatments should stay available; this is a booking
  question, not a sizing one.
- **Grid arbitrage (bess_arbitrage_5mw, power pinned at 5 MW).** The
  hard-cycled case (297 EFC a year, SOH 81.9 percent at year 20) behaves
  the same way: the derated NPV rises to 1.125 times the design energy
  (28,125 kWh, +214,000 USD or 5 percent) and falls at 1.25 because a 6.25
  hour battery can no longer be cycled fully inside the price windows (EFC
  drops to 270); fade-aware dispatch adds 0.2 percent at the design size;
  augmentation (216,000 USD PV) is 26 percent of the derate (820,000). The
  5 MW / 25 MWh design is a sound point on its own curve; the sizing
  question there is duration, not ageing. (Its kept REopt NPV of 6.7M was
  also inflated by the US defaults; aligned 4.8M against the pro forma's
  4.1M.)
- **Consistency check.** REopt's `state_of_health` on the deg dispatch
  matches the pro forma replica to 5e-4 in every case (four cases, Thailand at 15 minutes included), so
  the 1/h scaling is right and the optimiser and the workbook age the
  battery identically. The aligned REopt NPV lands within about 1 percent of
  the pro forma NPV (case_1 1,097,499 against 1,111,148; case_3 389,877
  against 389,852), which it never did with the US defaults in the
  objective (case_1 2,573,174 against 585,319).

## Recommendation

1. **Port the objective alignment to `master`** (user's ruling; it changes
   every Vietnam deliverable). The Vietnam builder should send what the
   Thailand builder already sends: PV `federal_itc_fraction 0`,
   `macrs_option_years 0`, `macrs_bonus_fraction 0`; storage
   `total_itc_fraction 0`, `macrs_option_years 0`, `macrs_bonus_fraction 0`;
   `Financial.offtaker_discount_rate_fraction` equal to the owner rate,
   `owner_tax_rate_fraction` and `offtaker_tax_rate_fraction` at the CIT
   rate, `elec_cost_escalation_rate_fraction` at the EVN escalation and
   `om_cost_escalation_rate_fraction` at the O&M escalation from the case.
   Then re-solve the Vietnam cases. This is the single largest accuracy
   improvement available to the battery optimiser, and it is not an ageing
   question. `MODEL_AUDIT.md` needs the item.
2. **Keep the ageing-blind (aligned) solve as the sizing standard.** On the
   derated NPV its size is the optimum to within the solver gap on all three
   cases; method A adds nothing to the *size* and carries the O&M bias.
   Use `model_degradation` for two things only: the consistency proof (the
   optimiser's SOH equals the workbook's) and the resting-SOC dispatch, which
   is better delivered as an EMS specification than as a sizing input.
3. **Add `battery_ageing_treatment: derate | augment` to the pro forma.**
   `augment` books the yearly augmentation cost (replica delta-SOH times the
   declining USD/kWh) as an O&M line and does not derate; `derate` stays as
   today. Default `derate` until a vendor capacity-maintenance price is in
   hand; the Battery SOH sheet shows both numbers either way.
4. **Keep `fade_sizing_probe` as the sizing check** for new projects (30
   minutes for a Vietnam case, about 2 hours for a Thailand 15 minute case
   with the fade-aware grid, 40 minutes without) and read the size off the
   flat top of the curve rather than the optimiser's decimal. Any objective
   change (shares, financing, tariffs) is tested the same way: size with the
   changed objective, score on the true-rate curve.
5. Remaining accuracy levers, in order: `soc_min_fraction` 0.10 for the
   grid-arbitrage cases so the 8,000 EFC datasheet life holds; calendar-fade
   calibration to LFP at 30 degrees; a dispatch-realism haircut on
   grid-arbitrage revenue (perfect foresight); 15 minute resolution for the
   demand-charge Vietnam cases; the levered equity NPV as the objective if a
   sizing ever needs to be exact (a bespoke outer loop, D already does it).

## Caveats

- The derate assumes the battery's delivered energy scales with SOH (capacity
  bound every day); it is the upper bound of the loss. The augmentation figure
  assumes a capacity-maintenance contract is available at the installed
  USD/kWh declining 3 percent a year; cell-only augmentation would be cheaper,
  a contract with mobilisation costs dearer.
- With `model_degradation` on, REopt drops the kWh share of storage O&M from
  its objective and its O&M outputs. The probe restores it before scoring;
  the sizing bias inside REopt's own objective remains (about 3 USD/kWh in
  the battery's favour) and cannot be corrected over HTTP without also
  changing the capex REopt reports. D is the arbiter.
- HiGHS runs at a 0.1 percent optimality gap; the top of the NPV curve is
  flat to within about 1,000 USD, so "best grid point" is a range, not a
  point. PV re-optimises at every grid point (as a real sizing would).
- Fade-aware dispatch is a policy the EMS must actually run (skip cycles whose
  margin is below the fade cost, hold a lower resting SOC); the gain is an
  upper bound with REopt's perfect foresight.
- Coefficients: cycle life 8,000 EFC to 80 percent (LFP datasheet), NREL
  calendar fade at laboratory conditions; no 30 degree calibration yet.

## Implementation status (2026-09-13, user ruling: all four)

1. Objective alignment: `proforma_vietnam/case_builder.py` on `master`
   (9329e147), cherry-picked here (5efc04cf); the eight Vietnam cases
   re-solved on both lines. This line's reconcile (old = 2026-09-12 solves):

| case | PV kW old / new | BESS kW / kWh old / new | capex USD old / new | equity NPV old / new | equity IRR old / new | min DSCR old / new |
|---|---|---|---|---|---|---|
| factory_a/case_1 | 5,701 / 3,520 | 1,896 / 11,087 to 1,031 / 4,079 | 4,218,573 / 2,261,868 | 585,319 / 1,111,148 | 13.3% / 22.2% | 1.02 / 1.37 |
| factory_a/case_2 | 5,996 / 3,968 | 2,011 / 12,331 to 1,180 / 7,311 | 4,518,797 / 2,876,230 | 405,302 / 765,929 | 12.1% / 16.4% | 0.97 / 1.15 |
| factory_a/case_3 | 6,071 / 2,188 | 2,220 / 14,337 to 579 / 3,088 | 4,812,252 / 1,467,206 | -470,729 / 389,852 | 7.7% / 16.2% | 0.78 / 1.12 |
| factory_a/case_4 | 3,243 / 2,436 | 0 / 0 to 0 / 0 | 1,556,758 / 1,169,156 | 440,925 / 529,270 | 16.8% / 21.1% | 1.17 / 1.33 |
| factory_a/case_5 | 5,996 / 3,968 | 2,011 / 12,331 to 1,180 / 7,311 | 4,518,797 / 2,876,230 | 986,353 / 920,389 | 15.1% / 17.5% | 1.07 / 1.16 |
| factory_a/case_6 | 5,914 / 5,914 | 592 / 1,184 to 592 / 1,184 | 3,028,160 / 3,028,160 | 1,982,816 / 1,982,822 | 26.0% / 26.0% | 1.48 / 1.48 |
| bess_arbitrage_5mw | 0 / 0 | 5,000 / 25,000 to 5,000 / 25,000 | 3,400,000 / 3,400,000 | 4,092,688 / 4,092,688 | 53.9% / 53.9% | 2.40 / 2.40 |
| bess_arbitrage_5mw_mfg | 0 / 0 | 5,000 / 25,000 to 5,000 / 25,000 | 3,400,000 / 3,400,000 | 1,455,082 / 1,455,082 | 24.7% / 24.7% | 1.51 / 1.51 |

   case_5 (grid-CfD DPPA) is the one ESCO case whose NPV falls: the
   optimiser still sizes on the retail bill while the pro forma settles at
   the CfD strike and FMP, so a smaller retail-optimal system earns less on
   the CfD; the grid check (recommendation 4) is the tool for that case.
2. Sizing standard documented (input guide, contract model design); the
   resting-SOC rule recorded as an EMS specification.
3. `technologies.storage.ageing_treatment: derate | augment` implemented
   (53e7fc66): cash flow, audit sheet (unit SOH factor plus an augmentation
   row inside EBITDA under augment), Battery SOH sheet with both figures,
   query plumbing, docs. Demonstration: `outputs/research/augment/vn_case_1`
   (aligned case_1 re-read with augment; Excel tie-out ALL CHECKS PASS):
   NPV 1,111,148 (derate) to 1,164,799 (augment), equity IRR 22.2 to 22.4
   percent, minimum DSCR 1.37 to 1.35 (the top-up is a cost from year 1
   while the derate's loss starts small), augmentation 59,724 USD nominal
   over the horizon against 370,995 USD of derate-basis loss.
4. `fade_sizing_probe` kept as the sizing check, unit tests on its pure
   pieces (`test_fade_sizing_probe.py`), runbook in the input guide.
