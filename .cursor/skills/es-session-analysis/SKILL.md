---
name: es-session-analysis
description: >-
  Analyze Investor/RT-style ES (@ES#) tick files for Chicago overnight/day sessions,
  VPOC, Initial Balance, open classification vs prior day, conditional hit
  probabilities, post-IB extension exceed rates vs IBH/IBL, or gap-fill rates by
  gap-size bucket. Use when working with Historical_Data tick exports or session statistics.
---

# ES Overnight / Day Session Analysis

## When to use

- User asks for ONH/ONL/ONMID, overnight VPOC, day VPOC, IBH/IBL, probabilities of hitting those levels conditional on open type, **post-IB** odds of taking out IBH/IBL or 1.5× IB-width extensions, or **gap fill** odds by gap size (% of prior close).
- Data is tab-separated tick text (`SYMBOL`, `DATE`, `PRICE`, `TICKVOL`, `BID`, `ASK`) from Investor/RT or compatible exports.

## Timezone and sessions (America/Chicago)

| Session | Time (Chicago) |
|---------|----------------|
| **Overnight (ON)** | Prior calendar day **17:00** → current day **08:30** (exclusive of 08:30 start of day session) |
| **Day** | **08:30** → **16:00** same calendar day |

**Trading day** is keyed by the **Day session open date** (the date of 08:30). Overnight before that open is attributed to that trading day.

**Yesterday day session** for comparisons is the **previous calendar day’s Day window only** (08:30–16:00), not overnight.

## Assumptions

- Timestamps in the file are **naive** and interpreted as **America/Chicago** (per project convention).
- **ES tick size 0.25** for VPOC binning: `bucket = round(price * 4) / 4`.
- **VPOC**: Sum `TICKVOL` per bucket; only rows with `TICKVOL > 0` contribute volume. **Ties** for max volume: use **midpoint of lowest and highest** tied bucket prices.
- **OHLC** for session high/low use **all** ticks’ `PRICE` (including zero-volume rows).
- **Continuous contract** `@ES#`: contract rolls can distort continuity; stats are as in the file.

## Derived metrics

- **ONH / ONL / ONMID**: Session high / low / midpoint of ON window for that trading day.
- **ON VPOC**: Volume profile POC over ON only.
- **Prior day H / L / Close**: Day session on calendar **yesterday**; close = last tick `PRICE` in that window.
- **Yesterday Day VPOC**: VPOC over yesterday’s Day session only.
- **Open**: First tick at or after 08:30 on the trading day (first `PRICE` in Day session).
- **Open buckets** (stored in `open_bucket`; strict; otherwise **boundary**):
  - **`inside_gap_up`**: `open > prior_close` and `open < prior_high` (gap up, still inside yesterday’s range)
  - **`inside_gap_down`**: `open < prior_close` and `open > prior_low` (gap down, still inside range)
  - **`above_prior_range`**: `open > prior_close` and `open > prior_high` (opens above yesterday’s high)
  - **`below_prior_range`**: `open < prior_close` and `open < prior_low` (opens below yesterday’s low)
- **IB / IBH / IBL**: First hour of Day session **08:30–09:30** Chicago; IBH/IBL = high/low of `PRICE` in that window.
- **Post-IB window**: **09:30–16:00** Chicago (remainder of day session after IB ends). **`post_ib_high` / `post_ib_low`**: max/min `PRICE` in that window only.
- **Post-IB exceed flags** (per day; `None` if IB or post-IB data missing, or IB width is 0 for extension levels):
  - **`post_ib_exceed_ibh`**: `post_ib_high > IBH`
  - **`post_ib_exceed_ibl`**: `post_ib_low < IBL`
  - **`post_ib_exceed_upper_1p5`**: `post_ib_high > IBH + 1.5 × (IBH − IBL)` when IB width &gt; 0
  - **`post_ib_exceed_lower_1p5`**: `post_ib_low < IBL − 1.5 × (IBH − IBL)` when IB width &gt; 0
- **Gap vs prior close** (columns `gap_pct`, `gap_filled`, `gap_size_bucket`; only on **gap days**):
  - **Gap day**: `prior_close` is known, `prior_close > 0`, and **open ≠ prior_close** (flat open excluded).
  - **Gap size %**: `|open − prior_close| / prior_close × 100`.
  - **Gap filled**: during today’s day session, `day_low ≤ prior_close ≤ day_high` (same inclusive rule as reference hits).
  - **Buckets** (stored in `gap_size_bucket`): `(0, 0.5]` → `gap_0_to_0p5_pct`; `(0.5, 1]` → `gap_0p5_to_1_pct`; `(1, 2]` → `gap_1_to_2_pct`; `(2, ∞)` → `gap_gt_2_pct`.

## Hit definition

During **today’s Day session** (08:30–16:00), a level **L** is **hit** if `day_low <= L <= day_high` (range includes the level).

## Seven reference levels (hits evaluated in today’s Day session)

1. ON VPOC (overnight before today)
2. yDay VPOC (`yDay_VPOC`) — yesterday’s day-session VPOC
3. ONL
4. ONMID (`ONMID`) — midpoint of overnight high and low
5. ONH
6. yDay high (`yDay_High`) — yesterday’s day-session high
7. yDay low (`yDay_Low`) — yesterday’s day-session low

## Running the tool

From repo root (after `pip install -r requirements.txt`):

```bash
python -m analysis.run --input Historical_Data/@ES#_Ticks.txt --output-dir output
```

For a **sample** of the first **N** calendar days from the first tick (default 60), use [`es-session-analysis-sample`](../es-session-analysis-sample/SKILL.md) or `python -m analysis.run_sample ...`.

Outputs:

- `daily_metrics.csv` — per trading day metrics, open bucket, IB, `post_ib_high` / `post_ib_low`, post-IB exceed flags, reference hit flags, and gap fields (`gap_pct`, `gap_filled`, `gap_size_bucket`).
- `conditional_probabilities.csv` — P(hit | bucket) per open bucket (`inside_gap_up`, `inside_gap_down`, `above_prior_range`, `below_prior_range`) and each reference level; **`probability_pct`** is 0–100 (same ratio as the formula above).
- `conditional_probabilities_post_ib.csv` — P(exceed | bucket) for four rows per bucket with **`level`** text like `post-IB high > IBH`, `post-IB low < IBL`, `post-IB high > IBH + 1.5*(IBH-IBL)`, `post-IB low < IBL - 1.5*(IBH-IBL)`; same **`probability_pct`** schema.
- `conditional_probabilities_gap_fill.csv` — one row per gap-size bucket: **`gap_bucket`**, **`days_in_bucket`**, **`gap_fill_count`**, **`probability_pct`** (0–100), **`small_sample`** (n &lt; 20 in bucket).
- `conditional_probabilities.md` — reference-level tables, then **---**, then **Post-IB session**, then **---**, then **Gap fill**; **% hit** / **% filled**; flags buckets with **&lt; 20** days where applicable.

## Code location

- Package: [`analysis/`](../../../analysis/) (see `run.py` CLI).
- Optional detail: [`reference.md`](reference.md).
