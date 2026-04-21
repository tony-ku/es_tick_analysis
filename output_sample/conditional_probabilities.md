# Conditional hit probabilities P(hit | open bucket)


## HIR (`HIR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit   |
|------------|---------------|-----------------|---------|------|---------|
| ONH_or_ONL | 12            | 29.27%          | 12      | 12   | 100.00% |
| ONPOC      | 12            | 29.27%          | 12      | 11   | 91.67%  |
| pVAH       | 12            | 29.27%          | 12      | 10   | 83.33%  |
| ONH        | 12            | 29.27%          | 12      | 10   | 83.33%  |
| ONMID      | 12            | 29.27%          | 12      | 9    | 75.00%  |
| pPOC       | 12            | 29.27%          | 12      | 8    | 66.67%  |
| pVAL       | 12            | 29.27%          | 12      | 8    | 66.67%  |
| pHigh      | 12            | 29.27%          | 12      | 8    | 66.67%  |
| ONL        | 12            | 29.27%          | 12      | 7    | 58.33%  |
| pLow       | 12            | 29.27%          | 12      | 5    | 41.67%  |

## LIR (`LIR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit  |
|------------|---------------|-----------------|---------|------|--------|
| ONH_or_ONL | 10            | 24.39%          | 10      | 9    | 90.00% |
| ONPOC      | 10            | 24.39%          | 10      | 8    | 80.00% |
| ONMID      | 10            | 24.39%          | 10      | 8    | 80.00% |
| ONL        | 10            | 24.39%          | 10      | 7    | 70.00% |
| pPOC       | 10            | 24.39%          | 10      | 6    | 60.00% |
| ONH        | 10            | 24.39%          | 10      | 6    | 60.00% |
| pVAL       | 10            | 24.39%          | 10      | 6    | 60.00% |
| pHigh      | 10            | 24.39%          | 10      | 5    | 50.00% |
| pVAH       | 10            | 24.39%          | 10      | 5    | 50.00% |
| pLow       | 10            | 24.39%          | 10      | 3    | 30.00% |

## HOR (`HOR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit  |
|------------|---------------|-----------------|---------|------|--------|
| ONH_or_ONL | 9             | 21.95%          | 9       | 8    | 88.89% |
| ONH        | 9             | 21.95%          | 9       | 7    | 77.78% |
| pHigh      | 9             | 21.95%          | 9       | 6    | 66.67% |
| ONPOC      | 9             | 21.95%          | 9       | 5    | 55.56% |
| ONMID      | 9             | 21.95%          | 9       | 5    | 55.56% |
| pVAH       | 9             | 21.95%          | 9       | 4    | 44.44% |
| pPOC       | 9             | 21.95%          | 9       | 2    | 22.22% |
| ONL        | 9             | 21.95%          | 9       | 1    | 11.11% |
| pLow       | 9             | 21.95%          | 9       | 0    | 0.00%  |
| pVAL       | 9             | 21.95%          | 9       | 0    | 0.00%  |

## LOR (`LOR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit   |
|------------|---------------|-----------------|---------|------|---------|
| ONH_or_ONL | 10            | 24.39%          | 10      | 10   | 100.00% |
| ONPOC      | 10            | 24.39%          | 10      | 8    | 80.00%  |
| pVAL       | 10            | 24.39%          | 10      | 7    | 70.00%  |
| ONL        | 10            | 24.39%          | 10      | 7    | 70.00%  |
| ONMID      | 10            | 24.39%          | 10      | 7    | 70.00%  |
| pLow       | 10            | 24.39%          | 10      | 7    | 70.00%  |
| pPOC       | 10            | 24.39%          | 10      | 6    | 60.00%  |
| ONH        | 10            | 24.39%          | 10      | 3    | 30.00%  |
| pVAH       | 10            | 24.39%          | 10      | 3    | 30.00%  |
| pHigh      | 10            | 24.39%          | 10      | 2    | 20.00%  |

---

# Post-IB session: P(exceed IBH / IBL / 1.5× IB range | open bucket)


After IB ends (09:30 Chicago), we use only **post-IB** prices in **[09:30, 16:00)**. **IBH** / **IBL** come from the first hour **[08:30, 09:30)**. **1.5× IB range** means **1.5 × (IBH − IBL)** added above IBH or subtracted below IBL (not 1.5× price). A day is skipped for a row if IB or post-IB range is missing, or IB width is 0 for the extension rows.


## HIR (`HIR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit  |
|------------------------------------|---------------|-----------------|---------|------|--------|
| post-IB high > IBH                 | 12            | 29.27%          | 12      | 7    | 58.33% |
| post-IB low < IBL                  | 12            | 29.27%          | 12      | 7    | 58.33% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 12            | 29.27%          | 12      | 3    | 25.00% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 12            | 29.27%          | 12      | 2    | 16.67% |

## LIR (`LIR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit  |
|------------------------------------|---------------|-----------------|---------|------|--------|
| post-IB low < IBL                  | 10            | 24.39%          | 10      | 6    | 60.00% |
| post-IB high > IBH                 | 10            | 24.39%          | 10      | 5    | 50.00% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 10            | 24.39%          | 10      | 1    | 10.00% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 10            | 24.39%          | 10      | 1    | 10.00% |

## HOR (`HOR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit  |
|------------------------------------|---------------|-----------------|---------|------|--------|
| post-IB high > IBH                 | 9             | 21.95%          | 9       | 7    | 77.78% |
| post-IB low < IBL                  | 9             | 21.95%          | 9       | 4    | 44.44% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 9             | 21.95%          | 9       | 1    | 11.11% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 9             | 21.95%          | 9       | 0    | 0.00%  |

## LOR (`LOR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit  |
|------------------------------------|---------------|-----------------|---------|------|--------|
| post-IB high > IBH                 | 10            | 24.39%          | 10      | 6    | 60.00% |
| post-IB low < IBL                  | 10            | 24.39%          | 10      | 4    | 40.00% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 10            | 24.39%          | 10      | 1    | 10.00% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 10            | 24.39%          | 10      | 1    | 10.00% |

---

# Gap fill: P(fill | gap size)


**Gap day**: prior day session close is defined, `prior_close > 0`, and day open ≠ prior close. **Gap size** = `|open − prior_close| / prior_close × 100%`. **Filled**: during today’s day session, `day_low ≤ prior_close ≤ day_high` (same inclusive rule as reference hits).


## By gap size bucket **(n<20)**

| Gap size (of prior close)            | Days | % of total days | Fills | % filled |
|--------------------------------------|------|-----------------|-------|----------|
| 0% < gap ≤ 0.5% (`gap_0_to_0p5_pct`) | 17   | 41.46%          | 13    | 76.47%   |
| 0.5% < gap ≤ 1% (`gap_0p5_to_1_pct`) | 12   | 29.27%          | 8     | 66.67%   |
| 1% < gap ≤ 2% (`gap_1_to_2_pct`)     | 9    | 21.95%          | 1     | 11.11%   |
| gap > 2% (`gap_gt_2_pct`)            | 2    | 4.88%           | 0     | 0.00%    |