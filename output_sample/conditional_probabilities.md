# Conditional hit probabilities P(hit | open bucket)


## Inside gap up (`inside_gap_up`)

| Level     | Days (bucket) | Defined | Hits | % hit  |
|-----------|---------------|---------|------|--------|
| ON_VPOC   | 42            | 42      | 38   | 90.48% |
| yDay_VPOC | 42            | 42      | 33   | 78.57% |
| ONL       | 42            | 42      | 26   | 61.90% |
| ONMID     | 42            | 42      | 31   | 73.81% |
| ONH       | 42            | 42      | 35   | 83.33% |
| yDay_High | 42            | 42      | 25   | 59.52% |
| yDay_Low  | 42            | 42      | 21   | 50.00% |

## Inside gap down (`inside_gap_down`)

| Level     | Days (bucket) | Defined | Hits | % hit  |
|-----------|---------------|---------|------|--------|
| ON_VPOC   | 74            | 74      | 67   | 90.54% |
| yDay_VPOC | 74            | 74      | 56   | 75.68% |
| ONL       | 74            | 74      | 56   | 75.68% |
| ONMID     | 74            | 74      | 59   | 79.73% |
| ONH       | 74            | 74      | 43   | 58.11% |
| yDay_High | 74            | 74      | 29   | 39.19% |
| yDay_Low  | 74            | 74      | 43   | 58.11% |

## Above prior day range (`above_prior_range`)

| Level     | Days (bucket) | Defined | Hits | % hit  |
|-----------|---------------|---------|------|--------|
| ON_VPOC   | 44            | 44      | 34   | 77.27% |
| yDay_VPOC | 44            | 44      | 17   | 38.64% |
| ONL       | 44            | 44      | 15   | 34.09% |
| ONMID     | 44            | 44      | 26   | 59.09% |
| ONH       | 44            | 44      | 34   | 77.27% |
| yDay_High | 44            | 44      | 27   | 61.36% |
| yDay_Low  | 44            | 44      | 5    | 11.36% |

## Below prior day range (`below_prior_range`)

| Level     | Days (bucket) | Defined | Hits | % hit  |
|-----------|---------------|---------|------|--------|
| ON_VPOC   | 41            | 41      | 35   | 85.37% |
| yDay_VPOC | 41            | 41      | 18   | 43.90% |
| ONL       | 41            | 41      | 28   | 68.29% |
| ONMID     | 41            | 41      | 31   | 75.61% |
| ONH       | 41            | 41      | 10   | 24.39% |
| yDay_High | 41            | 41      | 4    | 9.76%  |
| yDay_Low  | 41            | 41      | 27   | 65.85% |

---

# Post-IB session: P(exceed IBH / IBL / 1.5× IB range | open bucket)


After IB ends (09:30 Chicago), we use only **post-IB** prices in **[09:30, 16:00)**. **IBH** / **IBL** come from the first hour **[08:30, 09:30)**. **1.5× IB range** means **1.5 × (IBH − IBL)** added above IBH or subtracted below IBL (not 1.5× price). A day is skipped for a row if IB or post-IB range is missing, or IB width is 0 for the extension rows.


## Inside gap up (`inside_gap_up`)

| Level                              | Days (bucket) | Defined | Hits | % hit  |
|------------------------------------|---------------|---------|------|--------|
| post-IB high > IBH                 | 42            | 42      | 27   | 64.29% |
| post-IB low < IBL                  | 42            | 42      | 24   | 57.14% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 42            | 42      | 7    | 16.67% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 42            | 42      | 11   | 26.19% |

## Inside gap down (`inside_gap_down`)

| Level                              | Days (bucket) | Defined | Hits | % hit  |
|------------------------------------|---------------|---------|------|--------|
| post-IB high > IBH                 | 74            | 74      | 45   | 60.81% |
| post-IB low < IBL                  | 74            | 74      | 47   | 63.51% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 74            | 74      | 8    | 10.81% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 74            | 74      | 6    | 8.11%  |

## Above prior day range (`above_prior_range`)

| Level                              | Days (bucket) | Defined | Hits | % hit  |
|------------------------------------|---------------|---------|------|--------|
| post-IB high > IBH                 | 44            | 44      | 31   | 70.45% |
| post-IB low < IBL                  | 44            | 44      | 24   | 54.55% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 44            | 44      | 3    | 6.82%  |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 44            | 44      | 3    | 6.82%  |

## Below prior day range (`below_prior_range`)

| Level                              | Days (bucket) | Defined | Hits | % hit  |
|------------------------------------|---------------|---------|------|--------|
| post-IB high > IBH                 | 41            | 41      | 27   | 65.85% |
| post-IB low < IBL                  | 41            | 41      | 25   | 60.98% |
| post-IB high > IBH + 1.5*(IBH-IBL) | 41            | 41      | 5    | 12.20% |
| post-IB low < IBL - 1.5*(IBH-IBL)  | 41            | 41      | 3    | 7.32%  |

---

# Gap fill: P(fill | gap size)


**Gap day**: prior day session close is defined, `prior_close > 0`, and day open ≠ prior close. **Gap size** = `|open − prior_close| / prior_close × 100%`. **Filled**: during today’s day session, `day_low ≤ prior_close ≤ day_high` (same inclusive rule as reference hits).


## By gap size bucket **(n<20)**

| Gap size (of prior close)            | Days | Fills | % filled |
|--------------------------------------|------|-------|----------|
| 0% < gap ≤ 0.5% (`gap_0_to_0p5_pct`) | 114  | 87    | 76.32%   |
| 0.5% < gap ≤ 1% (`gap_0p5_to_1_pct`) | 54   | 27    | 50.00%   |
| 1% < gap ≤ 2% (`gap_1_to_2_pct`)     | 28   | 10    | 35.71%   |
| gap > 2% (`gap_gt_2_pct`)            | 5    | 1     | 20.00%   |