---
name: es-session-analysis-sample
description: >-
  Run ES session analysis on the first N calendar days from the first tick in a
  large Investor/RT tick file (default 60 days). Use for quick validation without
  scanning the full history. Full definitions match es-session-analysis.
---

# ES Session Analysis — Sample window (first N calendar days)

## When to use

- The tick file is very large and you want a **fast** run for testing or spot checks.
- You need the same metrics as [es-session-analysis](../es-session-analysis/SKILL.md) but only over an **initial calendar window** from the **first valid tick** in file order.

## Window semantics

- **Anchor date**: Chicago calendar date of the **first valid data row** (header lines are skipped).
- **Inclusive range**: `anchor_date` through `anchor_date + (N - 1)` calendar days — so **`--days 60`** is exactly **60** calendar days.
- **Early exit**: After the last tick on the last included day, the reader **stops** as soon as it sees a tick on a **later** date, so the rest of the file is not read.

Timestamps are still interpreted as **America/Chicago** (see main skill).

## Command

From repo root (after `pip install -r requirements.txt`):

```bash
python -m analysis.run_sample --input Historical_Data/@ES#_Ticks.txt --output-dir output_sample --days 60
```

Defaults: `--output-dir output_sample`, `--days 60`.

Outputs (same names as full run):

- `daily_metrics.csv` — includes **`post_ib_high`**, **`post_ib_low`**, **`post_ib_exceed_*`**, **`gap_pct`**, **`gap_filled`**, **`gap_size_bucket`**
- `conditional_probabilities.csv` — reference levels; **`probability_pct`** (0–100) per bucket/level
- `conditional_probabilities_post_ib.csv` — post-IB exceed levels (explicit **IBH** / **IBL** / **1.5×(IBH−IBL)** range in the `level` column)
- `conditional_probabilities_gap_fill.csv` — P(gap filled | gap size bucket); **`probability_pct`** (0–100)
- `conditional_probabilities.md` — reference tables, **Post-IB session**, and **Gap fill** sections

The CLI prints the resolved **anchor** and **last inclusive** dates.

## Full-file run

For the complete history:

```bash
python -m analysis.run --input Historical_Data/@ES#_Ticks.txt --output-dir output
```

## Code

- [`analysis/run_sample.py`](../../../analysis/run_sample.py) — CLI
- [`analysis/pipeline.py`](../../../analysis/pipeline.py) — `run_pipeline(..., max_calendar_days=N)`
