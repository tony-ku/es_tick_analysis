# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Setup:
```bash
pip install -r requirements.txt
```

Run full-history analysis (reads the entire tick file):
```bash
python -m analysis.run -i Historical_Data/@ES#_Ticks.txt -o output
```

Run sample-window analysis (first N calendar days from the first valid tick; stops reading once window ends):
```bash
python -m analysis.run_sample -i Historical_Data/@ES#_Ticks.txt -o output_sample -d 60
```

Common flags on both CLIs: `--chunksize` (rows per pandas chunk, default 1,000,000), `--verbose`/`-v` (progress + ingest time).

Tests:
```bash
python -m pytest tests/ -v
python -m pytest tests/test_analysis.py::test_vpoc_tie_midpoint -v   # single test
```

## Architecture

Single-pass streaming pipeline over tab-separated Investor/RT tick files (`SYMBOL, DATE, PRICE, TICKVOL, BID, ASK`). Ticks are read in chunks via `pandas.read_csv`, vectorized-filtered for data rows and valid timestamps, then folded into per-trading-day aggregates. No intermediate DataFrame of all ticks is ever materialized.

Key modules in [analysis/](analysis/):

- [sessions.py](analysis/sessions.py) — America/Chicago session boundaries and ES tick math. `overnight_trading_day(ts)` / `day_trading_day(ts)` map a Chicago timestamp to the **trading day** it belongs to (keyed by the date of 08:30 day-session open). Overnight is `[prev 17:00, today 08:30)`; Day is `[08:30, 16:00)`; IB is `[08:30, 09:30)`. `price_bucket` enforces ES tick size 0.25.
- [aggregates.py](analysis/aggregates.py) — `OvernightAgg` and `DaySessionAgg` dataclasses. Each holds min/max price, a `defaultdict` volume-by-bucket, plus (on the day side) first/last tick, IB min/max, and post-IB min/max. All updated in O(1) per tick via `.add()`. `vpoc_from_bins` resolves ties by returning the **midpoint** of the lowest and highest tied buckets.
- [pipeline.py](analysis/pipeline.py) — orchestration. `_chunk_tick_arrays` does one vectorized parse per chunk; `process_ticks_frame` / `process_ticks_frame_windowed` iterate valid indices and call `_apply_tick` which dispatches to the right aggregate(s). `build_daily_rows` turns the two dicts of aggregates into one row per trading day with all derived metrics (open bucket, IB, post-IB exceed flags, gap fields, reference-level hit flags). `conditional_probabilities`, `conditional_probabilities_post_ib`, and `gap_fill_probabilities` roll those rows up. `run_pipeline` is the single entry point used by both CLIs.
- [run.py](analysis/run.py) / [run_sample.py](analysis/run_sample.py) — thin argparse wrappers around `run_pipeline`; `run_sample` passes `max_calendar_days`, which activates `CalendarWindowState` (anchor = first valid tick's date; stops reading once a tick's date exceeds `anchor + days - 1`).

Derived-metric semantics that multiple files depend on:

- **Open buckets** (strict inequalities, else `boundary`): `HIR` (Higher Inside Range), `LIR` (Lower Inside Range), `HOR` (Higher Outside Range), `LOR` (Lower Outside Range). Defined in `classify_open_bucket`.
- **Gap-size buckets** (positive gap %, non-overlapping): `(0, 0.5]`, `(0.5, 1]`, `(1, 2]`, `(2, ∞)`. Defined in `classify_gap_size_bucket`.
- **Hit** for a reference level `L` = `day_low <= L <= day_high` (inclusive, over the day session only). Seven reference levels: ON VPOC, yDay VPOC, ONL, ONMID, ONH, yDay High, yDay Low.
- **Post-IB exceed** flags compare `post_ib_high`/`post_ib_low` (09:30–16:00) against IBH/IBL and ±1.5×(IBH−IBL) extensions; `None` when IB or post-IB data is missing (or IB width is 0 for extension rows).
- **Gap fill** only computed on gap days: `prior_close > 0` and `open != prior_close`; filled = `day_low <= prior_close <= day_high`.
- `probability_pct` in all CSVs is **0–100**, not 0–1. `small_sample` flags buckets with `n < 20`.

Outputs (written to `--output-dir`): `daily_metrics.csv`, `conditional_probabilities.csv`, `conditional_probabilities_post_ib.csv`, `conditional_probabilities_gap_fill.csv`, and a combined `conditional_probabilities.md` (reference-level tables, then post-IB, then gap fill, separated by `---`).

## Data convention

Tick file timestamps are **naive** and interpreted as **America/Chicago** — `as_chicago_ts` attaches the zone without converting. `@ES#` is a continuous contract; roll discontinuities are not adjusted. Only rows with `TICKVOL > 0` contribute to VPOC; high/low use all ticks.

## Skills

Canonical session/metric conventions live in the skill files — consult them when definitions above feel ambiguous:

- Claude Code: [.claude/skills/es-session-analysis/SKILL.md](.claude/skills/es-session-analysis/SKILL.md), [.claude/skills/es-session-analysis/reference.md](.claude/skills/es-session-analysis/reference.md), [.claude/skills/es-session-analysis-sample/SKILL.md](.claude/skills/es-session-analysis-sample/SKILL.md)
- Cursor: [.cursor/skills/es-session-analysis/SKILL.md](.cursor/skills/es-session-analysis/SKILL.md), [.cursor/skills/es-session-analysis-sample/SKILL.md](.cursor/skills/es-session-analysis-sample/SKILL.md)
