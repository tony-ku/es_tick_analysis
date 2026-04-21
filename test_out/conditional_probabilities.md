# Conditional hit probabilities P(hit | open bucket)


## HIR (`HIR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit |
|------------|---------------|-----------------|---------|------|-------|
| ONPOC      | 0             | 0.00%           | 0       | 0    | nan   |
| pPOC       | 0             | 0.00%           | 0       | 0    | nan   |
| ONL        | 0             | 0.00%           | 0       | 0    | nan   |
| ONMID      | 0             | 0.00%           | 0       | 0    | nan   |
| ONH        | 0             | 0.00%           | 0       | 0    | nan   |
| ONH_or_ONL | 0             | 0.00%           | 0       | 0    | nan   |
| pHigh      | 0             | 0.00%           | 0       | 0    | nan   |
| pLow       | 0             | 0.00%           | 0       | 0    | nan   |
| pVAH       | 0             | 0.00%           | 0       | 0    | nan   |
| pVAL       | 0             | 0.00%           | 0       | 0    | nan   |

## LIR (`LIR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit   |
|------------|---------------|-----------------|---------|------|---------|
| ONPOC      | 1             | 100.00%         | 1       | 1    | 100.00% |
| ONL        | 1             | 100.00%         | 1       | 1    | 100.00% |
| pVAL       | 1             | 100.00%         | 1       | 1    | 100.00% |
| ONMID      | 1             | 100.00%         | 1       | 1    | 100.00% |
| ONH_or_ONL | 1             | 100.00%         | 1       | 1    | 100.00% |
| pLow       | 1             | 100.00%         | 1       | 1    | 100.00% |
| pPOC       | 1             | 100.00%         | 1       | 0    | 0.00%   |
| ONH        | 1             | 100.00%         | 1       | 0    | 0.00%   |
| pHigh      | 1             | 100.00%         | 1       | 0    | 0.00%   |
| pVAH       | 1             | 100.00%         | 1       | 0    | 0.00%   |

## HOR (`HOR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit |
|------------|---------------|-----------------|---------|------|-------|
| ONPOC      | 0             | 0.00%           | 0       | 0    | nan   |
| pPOC       | 0             | 0.00%           | 0       | 0    | nan   |
| ONL        | 0             | 0.00%           | 0       | 0    | nan   |
| ONMID      | 0             | 0.00%           | 0       | 0    | nan   |
| ONH        | 0             | 0.00%           | 0       | 0    | nan   |
| ONH_or_ONL | 0             | 0.00%           | 0       | 0    | nan   |
| pHigh      | 0             | 0.00%           | 0       | 0    | nan   |
| pLow       | 0             | 0.00%           | 0       | 0    | nan   |
| pVAH       | 0             | 0.00%           | 0       | 0    | nan   |
| pVAL       | 0             | 0.00%           | 0       | 0    | nan   |

## LOR (`LOR`) **(n<20)**

| Level      | Days (bucket) | % of total days | Defined | Hits | % hit |
|------------|---------------|-----------------|---------|------|-------|
| ONPOC      | 0             | 0.00%           | 0       | 0    | nan   |
| pPOC       | 0             | 0.00%           | 0       | 0    | nan   |
| ONL        | 0             | 0.00%           | 0       | 0    | nan   |
| ONMID      | 0             | 0.00%           | 0       | 0    | nan   |
| ONH        | 0             | 0.00%           | 0       | 0    | nan   |
| ONH_or_ONL | 0             | 0.00%           | 0       | 0    | nan   |
| pHigh      | 0             | 0.00%           | 0       | 0    | nan   |
| pLow       | 0             | 0.00%           | 0       | 0    | nan   |
| pVAH       | 0             | 0.00%           | 0       | 0    | nan   |
| pVAL       | 0             | 0.00%           | 0       | 0    | nan   |

---

# Post-IB session: P(exceed IBH / IBL / 1.5× IB range | open bucket)


After IB ends (09:30 Chicago), we use only **post-IB** prices in **[09:30, 16:00)**. **IBH** / **IBL** come from the first hour **[08:30, 09:30)**. **1.5× IB range** means **1.5 × (IBH − IBL)** added above IBH or subtracted below IBL (not 1.5× price). A day is skipped for a row if IB or post-IB range is missing, or IB width is 0 for the extension rows.


## HIR (`HIR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit |
|------------------------------------|---------------|-----------------|---------|------|-------|
| post-IB high > IBH                 | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB low < IBL                  | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB high > IBH + 1.5*(IBH-IBL) | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 0             | 0.00%           | 0       | 0    | nan   |

## LIR (`LIR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit   |
|------------------------------------|---------------|-----------------|---------|------|---------|
| post-IB low < IBL                  | 1             | 100.00%         | 1       | 1    | 100.00% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 1             | 100.00%         | 1       | 1    | 100.00% |
| post-IB high > IBH                 | 1             | 100.00%         | 1       | 0    | 0.00%   |
| post-IB high > IBH + 1.5*(IBH-IBL) | 1             | 100.00%         | 1       | 0    | 0.00%   |

## HOR (`HOR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit |
|------------------------------------|---------------|-----------------|---------|------|-------|
| post-IB high > IBH                 | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB low < IBL                  | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB high > IBH + 1.5*(IBH-IBL) | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 0             | 0.00%           | 0       | 0    | nan   |

## LOR (`LOR`) **(n<20)**

| Level                              | Days (bucket) | % of total days | Defined | Hits | % hit |
|------------------------------------|---------------|-----------------|---------|------|-------|
| post-IB high > IBH                 | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB low < IBL                  | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB high > IBH + 1.5*(IBH-IBL) | 0             | 0.00%           | 0       | 0    | nan   |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 0             | 0.00%           | 0       | 0    | nan   |

---

# Gap fill: P(fill | gap size)


**Gap day**: prior day session close is defined, `prior_close > 0`, and day open ≠ prior close. **Gap size** = `|open − prior_close| / prior_close × 100%`. **Filled**: during today’s day session, `day_low ≤ prior_close ≤ day_high` (same inclusive rule as reference hits).


## By gap size bucket **(n<20)**

| Gap size (of prior close)            | Days | % of total days | Fills | % filled |
|--------------------------------------|------|-----------------|-------|----------|
| 0% < gap ≤ 0.5% (`gap_0_to_0p5_pct`) | 1    | 100.00%         | 1     | 100.00%  |
| 0.5% < gap ≤ 1% (`gap_0p5_to_1_pct`) | 0    | 0.00%           | 0     | nan      |
| 1% < gap ≤ 2% (`gap_1_to_2_pct`)     | 0    | 0.00%           | 0     | nan      |
| gap > 2% (`gap_gt_2_pct`)            | 0    | 0.00%           | 0     | nan      |