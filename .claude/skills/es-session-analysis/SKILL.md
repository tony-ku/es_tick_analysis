---
name: es-session-analysis
description: >-
  Analyze Investor/RT-style ES (@ES#) tick files for Chicago overnight/day sessions,
  VPOC, Value Area (Steidlmayer 70%), Initial Balance, open classification vs prior day,
  conditional hit probabilities (incl. pVAH/pVAL/ONH-or-ONL), post-IB extension exceed
  rates vs IBH/IBL, or gap-fill rates by gap-size bucket. Use when working with
  Historical_Data tick exports or session statistics.
---

# ES Overnight / Day Session Analysis

## When to use

- User asks for ONH/ONL/ONMID, overnight VPOC, day VPOC, prior day Value Area (pVAH/pVAL), IBH/IBL, probabilities of hitting those levels conditional on open type, **post-IB** odds of taking out IBH/IBL or 1.5× IB-width extensions, or **gap fill** odds by gap size (% of prior close).
- Data is tab-separated tick text (`SYMBOL`, `DATE`, `PRICE`, `TICKVOL`, `BID`, `ASK`) from Investor/RT or compatible exports.

## Timezone and sessions (America/Chicago)

| Session | Time (Chicago) |
|---------|----------------|
| **Overnight (ON)** | Prior calendar day **17:00** → current day **08:30** (exclusive of 08:30 start of day session) |
| **Day** | **08:30** → **16:00** same calendar day |

**Trading day** is keyed by the **Day session open date** (the date of 08:30). Overnight before that open is attributed to that trading day.

**Yesterday day session** for comparisons is the **previous calendar day's Day window only** (08:30–16:00), not overnight.

## Assumptions

- Timestamps in the file are **naive** and interpreted as **America/Chicago** (per project convention).
- **ES tick size 0.25** for VPOC binning: `bucket = round(price * 4) / 4`.
- **VPOC**: Sum `TICKVOL` per bucket; only rows with `TICKVOL > 0` contribute volume. **Ties** for max volume: use **midpoint of lowest and highest** tied bucket prices.
- **OHLC** for session high/low use **all** ticks' `PRICE` (including zero-volume rows).
- **Continuous contract** `@ES#`: contract rolls can distort continuity; stats are as in the file.

## Derived metrics

- **ONH / ONL / ONMID**: Session high / low / midpoint of ON window for that trading day.
- **ON VPOC**: Volume profile POC over ON only.
- **Prior day H / L / Close**: Day session on the **previous trading day**; close = last tick `PRICE` in that window.
- **Prior day VPOC** (`yDay_VPOC`): VPOC over the prior trading day's Day session only.
- **Prior day Value Area** (`pVAH`, `pVAL`): Steidlmayer 70% value area over the prior trading day's Day session volume profile (see VA algorithm below).
- **Open**: First tick at or after 08:30 on the trading day (first `PRICE` in Day session).
- **Open buckets** (stored in `open_bucket`; strict; otherwise **boundary**):
  - **`HIR`** (Higher Inside Range): `open > prior_close` and `open < prior_high` (gap up, still inside yesterday's range)
  - **`LIR`** (Lower Inside Range): `open < prior_close` and `open > prior_low` (gap down, still inside range)
  - **`HOR`** (Higher Outside Range): `open > prior_close` and `open > prior_high` (opens above yesterday's high)
  - **`LOR`** (Lower Outside Range): `open < prior_close` and `open < prior_low` (opens below yesterday's low)
- **IB / IBH / IBL**: First hour of Day session **08:30–09:30** Chicago; IBH/IBL = high/low of `PRICE` in that window.
- **Post-IB window**: **09:30–16:00** Chicago (remainder of day session after IB ends). **`post_ib_high` / `post_ib_low`**: max/min `PRICE` in that window only.
- **Post-IB exceed flags** (per day; `None` if IB or post-IB data missing, or IB width is 0 for extension levels):
  - **`post_ib_exceed_ibh`**: `post_ib_high > IBH`
  - **`post_ib_exceed_ibl`**: `post_ib_low < IBL`
  - **`post_ib_exceed_upper_1p5`**: `post_ib_high > IBH + 1.5 × (IBH − IBL)` when IB width > 0
  - **`post_ib_exceed_lower_1p5`**: `post_ib_low < IBL − 1.5 × (IBH − IBL)` when IB width > 0
- **Gap vs prior close** (columns `gap_pct`, `gap_filled`, `gap_size_bucket`; only on **gap days**):
  - **Gap day**: `prior_close` is known, `prior_close > 0`, and **open ≠ prior_close** (flat open excluded).
  - **Gap size %**: `|open − prior_close| / prior_close × 100`.
  - **Gap filled**: during today's day session, `day_low ≤ prior_close ≤ day_high` (same inclusive rule as reference hits).
  - **Buckets** (stored in `gap_size_bucket`): `(0, 0.5]` → `gap_0_to_0p5_pct`; `(0.5, 1]` → `gap_0p5_to_1_pct`; `(1, 2]` → `gap_1_to_2_pct`; `(2, ∞)` → `gap_gt_2_pct`.

## Hit definition

During **today's Day session** (08:30–16:00), a level **L** is **hit** if `day_low <= L <= day_high` (range includes the level). **ONH_or_ONL** is hit if *either* ONH or ONL is hit.

## Ten reference levels (hits evaluated in today's Day session)

1. `ON_VPOC` — overnight VPOC before today
2. `yDay_VPOC` — prior trading day's day-session VPOC
3. `ONL`
4. `ONMID` — `(ONH + ONL) / 2`
5. `ONH`
6. `ONH_or_ONL` — touched either overnight extreme
7. `yDay_High` — prior trading day's day-session high
8. `yDay_Low` — prior trading day's day-session low
9. `pVAH` — prior day Value Area High (Steidlmayer 70%)
10. `pVAL` — prior day Value Area Low (Steidlmayer 70%)

## Value Area algorithm (Steidlmayer 70%)

1. Seed VA at the POC bucket (upper bucket on POC tie).
2. Each step, compare the summed volume of the **two buckets immediately above** the developing VA to the **two immediately below**.
3. Add the larger pair (both buckets) to the VA. **Upper wins on tie.**
4. If one side is exhausted at the profile edge, extend the other.
5. Stop once VA cumulative volume ≥ **70%** of day total. VAH = top bucket, VAL = bottom bucket.

## Running the tool

From repo root (after `pip install -r requirements.txt`):

```bash
python -m analysis.run --input Historical_Data/@ES#_Ticks.txt --output-dir output
```

For a **sample** of the first **N** calendar days from the first tick (default 60), use [`es-session-analysis-sample`](../es-session-analysis-sample/SKILL.md) or `python -m analysis.run_sample ...`.

Outputs:

- `daily_metrics.csv` — per trading day metrics, open bucket, IB, `post_ib_high` / `post_ib_low`, post-IB exceed flags, reference hit flags (incl. `hit_onh_or_onl`, `hit_prior_day_vah`, `hit_prior_day_val`), and gap fields.
- `conditional_probabilities.csv` — P(hit | bucket) per open bucket (`HIR`, `LIR`, `HOR`, `LOR`) × 10 reference levels; **`probability_pct`** is 0–100.
- `conditional_probabilities_post_ib.csv` — P(exceed | bucket), four rows per bucket with explicit `level` text; same schema.
- `conditional_probabilities_gap_fill.csv` — one row per gap-size bucket: **`gap_bucket`**, **`days_in_bucket`**, **`gap_fill_count`**, **`probability_pct`**, **`small_sample`** (n < 20).
- `conditional_probabilities.md` — reference-level tables, then **---**, then **Post-IB session**, then **---**, then **Gap fill**; flags buckets with **< 20** days.

## Code location

- Package: [`analysis/`](../../../analysis/) (see `run.py` CLI).
- Optional detail: [`reference.md`](reference.md).
