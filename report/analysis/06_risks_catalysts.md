# Phase 6: Risks, catalysts and what would make me wrong

Method: each risk is run through the full Excel model (`src/risks.py` rebuilds and recalculates it in LibreOffice)
with one driver shocked and everything else at Base. Base: FY2028E EPS JPY 327.8, 12-month TP JPY 5,850, HOLD.
Results: `data/clean/risk_sensitivities.csv`.

## Top risks, quantified
| # | Risk | Shock | FY2028E OP | FY2028E EPS | TP (JPY) | Rating |
|---|---|---|---|---|---|---|
| 1 | Yen strength (BoJ hikes narrow rate gaps) | Yen +10% vs USD and EUR | -7.6% | **-6.9%** | 5,650 (-200) | HOLD |
| 1b | Yen weakness (upside risk) | Yen -10% | +8.3% | +7.6% | 6,050 (+200) | BUY |
| 2 | Margin pressure: price competition from TTI and DeWalt, or another inventory clearance | Gross margin -200bp, all years | -14.8% | **-14.5%** | 5,200 (-650) | HOLD |
| 3 | Construction downturn in Europe and Japan | Local-currency growth -3pp in FY2027-28 | -5.8% | -5.4% | 5,700 (-150) | HOLD |
| 4 | Cost creep: sales headcount build under Vision FY2030 without revenue | SG&A +100bp of revenue | -7.4% | -7.2% | 5,550 (-300) | HOLD |
| 5 | Inventory rebuild (the FY2022 pattern) | +30 inventory days | 0% | -0.7% | 5,700 (-150) | HOLD |
| 6 | US tariffs on China-made goods | 25% tariff, 50% passed on | -3.2% | -3.1% | n/a (outside model) | n/a |
| - | Valuation input | Terminal growth -0.5pp | - | - | 5,800 (-50) | HOLD |

Reading the table:
- **Margins matter most.** 200bp of gross margin is worth more than twice a 10% yen move. Makita's gross margin
  fell 620bp in FY2023 alone (30.9% to 24.7%) and 1,220bp from FY2018, so this is not a tail scenario.
- **FX is modelled as translation with constant margins.** The real effect is probably larger. Yen-denominated costs
  (Japan HQ, R&D, 7.5% domestic production) do not move with the yen, so a stronger yen would compress margins too.
  The -6.9% is a floor, not a ceiling.
- **Inventory hurts value, not EPS.** 30 extra days barely touches earnings but ties up about JPY 40bn of cash, which
  is the FY2022 lesson: profits looked fine until the clearance.
- **Terminal growth matters less than usual.** With the value-driver formula, lower growth also means less
  reinvestment, and RONIC (12%) is only modestly above WACC (8.8%).
- **Tariff estimate assumptions** (not disclosed by Makita): North America FY2028E revenue x cost-of-sales ratio x
  China share of group units (51.5%, Makita Report 2026) x 25% x (1 - 50% pass-through). The Feb 2026 Supreme Court
  ruling removed the IEEPA tariffs, but Section 301 tariffs on China remain, so this is a live risk.

## Catalysts (approximate dates)
| When | Event | What to watch |
|---|---|---|
| **Late Oct / early Nov 2026** (2Q FY2026 was released 31 Oct 2025) | 2Q FY3/2027 results | Local-currency growth in Europe; gross margin ex the tariff refund; inventory days; any guidance change from JPY 820bn revenue / 110bn OP |
| Dec 2026 | Payment of the JPY 79 interim dividend | Confirms the step-up under the 50% payout policy |
| Early Feb 2027 (approx.) | 3Q FY3/2027 results | Inventory trend into the spring season |
| BoJ meetings through 2026-27 | JPY rate path | Yen strength is the largest macro risk (risk 1) |
| Late Apr 2027 (FY2026 results came 28 Apr 2026) | FY3/2027 results and FY3/2028 guidance | First guidance year after the tariff refund; progress toward the 15% OP margin target; buyback |
| Jun 2027 | AGM and Makita Report 2027 | Vision FY2030 progress (40Vmax mix, OPE, cordless motor units) |

## What would make me wrong
The rating is HOLD with +11% upside. BUY needs a TP above JPY 6,041 (+15%); SELL needs one below JPY 4,728 (-10%).

| Flip | Condition | Evidence from the model |
|---|---|---|
| **HOLD to BUY** | Operating margin heads to the 15% Vision FY2030 target without giving up growth | Sensitivity 3: a steady 15.5% margin gives about JPY 5,980 fair value, so a TP of about JPY 6,350 (+21%) |
| **HOLD to BUY** | Sustained yen weakness of about 10% against USD and EUR | TP JPY 6,050 (+15.2%), only just over the line |
| **HOLD to BUY** | Bull case: European recovery, 40Vmax mix lifts gross margin to 38% | Bull TP JPY 7,600 (+45%) |
| **HOLD to SELL** | A second inventory and margin cycle: gross margin back to 34-35%, growth flat, yen +10% | Bear TP JPY 4,400 (-16%) |
| **Thesis break** | Inventory days back above 300 at 2Q or 3Q, or Europe local-currency decline beyond -3% | Either would point to the Bear path |
