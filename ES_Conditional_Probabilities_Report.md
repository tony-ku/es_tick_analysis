# ES Futures — Conditional Probability Report

**Instrument:** `@ES#` (E-mini S&P 500, continuous front-month)
**Sample:** 5,308 trading days — **2005-09-07 through 2026-04-10**
**Session convention:** America/Chicago. Day session = **08:30–16:00**, Initial Balance (IB) = **08:30–09:30**, Overnight = **prior-day 17:00 – today 08:30**.
**Methodology:** Tick-level pass over Investor/RT data. Tick size 0.25. VPOC computed on `TICKVOL > 0`; highs/lows on all ticks. VPOC ties resolved to the midpoint of the tied range.

---

## How to read this report

- **Open bucket** — where today's day-session open sits relative to the *prior day's* high/low range:
  - **HIR** (Higher Inside Range) — open is inside prior range, in the upper half
  - **LIR** (Lower Inside Range) — open is inside prior range, in the lower half
  - **HOR** (Higher Outside Range) — open is *above* prior day high
  - **LOR** (Lower Outside Range) — open is *below* prior day low
- **Hit** — the reference level was touched during **today's day session** (`day_low ≤ level ≤ day_high`, inclusive).
- **% of total days** — frequency of that open bucket across the 5,308-day sample.
- **Defined** — days in the bucket where the metric could actually be computed (IB / post-IB / prior close present).
- **Sample sizes are large** (≥798 days per bucket); no bucket is flagged small-sample.

Reference levels used throughout:

| Abbreviation | Meaning |
|---|---|
| **ON VPOC** | Overnight session volume point-of-control |
| **ONH / ONL / ONMID** | Overnight high / low / midpoint |
| **yDay VPOC** | Prior day session VPOC |
| **yDay High / yDay Low** | Prior day session high / low |
| **IBH / IBL** | Initial Balance high / low (08:30–09:30) |

---

## 1. Reference-level hit probability — by open bucket

Probability that each reference level is touched during the day session, given today's open bucket.

### HIR — Higher Inside Range  *(32.20% of days · n = 1,709)*

| Reference level | Hits / n | **P(hit)** |
|---|---:|---:|
| ON VPOC    | 1517 / 1709 | **88.77%** |
| ONMID      | 1385 / 1709 | **81.04%** |
| ONH        | 1300 / 1709 | **76.07%** |
| yDay VPOC  | 1190 / 1709 | **69.63%** |
| yDay High  |  974 / 1709 | **56.99%** |
| ONL        |  892 / 1709 | **52.19%** |
| yDay Low   |  619 / 1709 | **36.22%** |

### LIR — Lower Inside Range  *(30.12% of days · n = 1,599)*

| Reference level | Hits / n | **P(hit)** |
|---|---:|---:|
| ON VPOC    | 1418 / 1599 | **88.68%** |
| ONMID      | 1334 / 1599 | **83.43%** |
| ONL        | 1158 / 1599 | **72.42%** |
| yDay VPOC  | 1138 / 1599 | **71.17%** |
| ONH        |  839 / 1599 | **52.47%** |
| yDay Low   |  819 / 1599 | **51.22%** |
| yDay High  |  650 / 1599 | **40.65%** |

### HOR — Higher Outside Range *(open above prior day high · 22.65% of days · n = 1,202)*

| Reference level | Hits / n | **P(hit)** |
|---|---:|---:|
| ON VPOC    | 1000 / 1202 | **83.19%** |
| ONH        |  912 / 1202 | **75.87%** |
| ONMID      |  800 / 1202 | **66.56%** |
| yDay High  |  781 / 1202 | **64.98%** |
| yDay VPOC  |  462 / 1202 | **38.44%** |
| ONL        |  420 / 1202 | **34.94%** |
| yDay Low   |  148 / 1202 | **12.31%** |

### LOR — Lower Outside Range *(open below prior day low · 15.03% of days · n = 798)*

| Reference level | Hits / n | **P(hit)** |
|---|---:|---:|
| ON VPOC    | 697 / 798 | **87.34%** |
| ONL        | 588 / 798 | **73.68%** |
| yDay Low   | 551 / 798 | **69.05%** |
| ONMID      | 550 / 798 | **68.92%** |
| yDay VPOC  | 315 / 798 | **39.47%** |
| ONH        | 307 / 798 | **38.47%** |
| yDay High  | 107 / 798 | **13.41%** |

### Takeaways

- **ON VPOC is the most-touched level in every regime** (83–89%). It is the single strongest magnet intraday regardless of where price opens.
- **Inside-range opens (HIR / LIR) tag the full overnight structure frequently** — ONMID and ON VPOC are both >80%, making overnight midline a high-probability target on balanced opens.
- **Outside-range opens retrace into range strongly**: HOR hits prior day high 65% of the time, LOR hits prior day low 69% of the time — but only 12–13% make it all the way across to the opposite prior-day extreme.
- **yDay Low on HIR / LIR days is rare** (36% / 51%) — a long trade targeting the *prior* day's low from an inside-range open is a low-base-rate setup.

---

## 2. Post-IB session — extension probabilities

Once the first hour closes (IB = 08:30–09:30), these are the probabilities that post-IB price **[09:30–16:00)** breaks IBH / IBL, or extends **1.5 × IB range** beyond those boundaries.

*"1.5× IB range" means `1.5 × (IBH − IBL)` added above IBH or subtracted below IBL — an extension measured in IB width, not in percent of price.*

### HIR  *(n = 1,709)*

| Event | Hits / n | **P** |
|---|---:|---:|
| post-IB high > IBH                  | 1150 / 1709 | **67.29%** |
| post-IB low  < IBL                  | 1027 / 1709 | **60.09%** |
| post-IB high > IBH + 1.5·(IBH−IBL)  |  152 / 1709 | **8.89%**  |
| post-IB low  < IBL − 1.5·(IBH−IBL)  |  220 / 1709 | **12.87%** |

### LIR  *(n = 1,599)*

| Event | Hits / n | **P** |
|---|---:|---:|
| post-IB high > IBH                  | 1084 / 1599 | **67.79%** |
| post-IB low  < IBL                  | 1008 / 1599 | **63.04%** |
| post-IB high > IBH + 1.5·(IBH−IBL)  |  143 / 1599 | **8.94%**  |
| post-IB low  < IBL − 1.5·(IBH−IBL)  |  184 / 1599 | **11.51%** |

### HOR  *(n = 1,201)*

| Event | Hits / n | **P** |
|---|---:|---:|
| post-IB high > IBH                  | 770 / 1201 | **64.11%** |
| post-IB low  < IBL                  | 688 / 1201 | **57.29%** |
| post-IB high > IBH + 1.5·(IBH−IBL)  | 105 / 1201 | **8.74%**  |
| post-IB low  < IBL − 1.5·(IBH−IBL)  | 133 / 1201 | **11.07%** |

### LOR  *(n = 798)*

| Event | Hits / n | **P** |
|---|---:|---:|
| post-IB high > IBH                  | 537 / 798 | **67.29%** |
| post-IB low  < IBL                  | 475 / 798 | **59.52%** |
| post-IB high > IBH + 1.5·(IBH−IBL)  |  63 / 798 | **7.89%**  |
| post-IB low  < IBL − 1.5·(IBH−IBL)  |  80 / 798 | **10.03%** |

### Takeaways

- **Breakout of IBH or IBL is nearly a coin flip — toward 2/3.** Across every open bucket, post-IB price breaks IBH 64–68% of the time and IBL 57–63% of the time. One-sided IB days are the minority.
- **IB-range extensions (1.5×) are rare** — roughly **9% upside, 11–13% downside** across all regimes. The asymmetry is persistent: downside extensions outrun upside extensions in every bucket.
- Open bucket has **surprisingly little effect** on post-IB extension rates — the IB itself, not the open location, appears to dominate the day's extension distribution.

---

## 3. Gap-fill probability — by gap size

A **gap day** requires a defined prior session close (`prior_close > 0`) and `open ≠ prior_close`. **Gap size** = `|open − prior_close| / prior_close × 100%`. **Filled** = prior close was touched during today's day session.

| Gap size | Days | % of sample | Fills | **P(fill)** |
|---|---:|---:|---:|---:|
| 0%  < gap ≤ 0.5%   | 4,187 | 78.88% | 2,980 | **71.17%** |
| 0.5% < gap ≤ 1.0%  |   751 | 14.15% |   262 | **34.89%** |
| 1.0% < gap ≤ 2.0%  |   257 |  4.84% |    70 | **27.24%** |
| gap > 2.0%         |    50 |  0.94% |    11 | **22.00%** |

### Takeaways

- **Small gaps (≤0.5%) fill ~71% of the time** — the baseline "gap-fill trade" edge lives almost entirely in this bucket, which is also the vast majority of all sessions (79%).
- **Fill rate collapses fast as gap size grows.** A gap over 0.5% cuts fill probability by more than half (~35%), and anything above 1% falls into the 22–27% range.
- **Gaps >2% are tail events** (≈1% of days) and fill barely 1 in 5 times — these are trend-continuation signals more than mean-reversion setups.

---

## Notes on methodology

- Timestamps in the source file are **naive** and interpreted as **America/Chicago** (no conversion). `@ES#` is a **continuous** contract — roll discontinuities are **not** adjusted, so levels crossing a roll date can be distorted. This is most relevant for single-day reference levels (prior day high/low/VPOC) on the day immediately after a roll.
- The first day of the sample is dropped (no prior-day context).
- VPOC ties are resolved to the **midpoint** of the lowest and highest tied 0.25 buckets.
- All percentages above are on a **0–100 scale**.

---

## ⚠ Disclaimer

**This report is for educational and informational purposes only. It is not investment advice, a solicitation, or a recommendation to buy, sell, or hold any security, futures contract, or other financial instrument.**

- Past statistical behavior does **not** predict future results. Probabilities shown are historical frequencies observed in a specific dataset over a specific window; the underlying market structure, liquidity, session hours, and contract specifications can and do change.
- Futures trading involves **substantial risk of loss** and is not suitable for all investors. You can lose more than your initial deposit.
- The data is derived from a single tick source (`@ES#` continuous contract) and has **not been independently audited**. Data errors, missed ticks, session-boundary edge cases, contract rolls, and holiday/half-session handling may materially affect the numbers.
- No backtest, commission, slippage, margin, or execution-cost model is applied. Live trading results will differ from any naive strategy implied by these probabilities.
- The author makes **no representation or warranty**, express or implied, regarding the accuracy, completeness, or fitness for any particular purpose of this analysis. Use at your own risk.

**Consult a licensed financial professional before making any trading decision.**
