"""Tests for ES session analysis."""

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from analysis.aggregates import OvernightAgg, vpoc_from_bins
from analysis.pipeline import (
    build_daily_rows,
    classify_open_bucket,
    conditional_probabilities,
    level_hit,
    process_ticks_frame,
    run_pipeline,
)
from analysis.sessions import (
    CHICAGO,
    as_chicago_ts,
    day_trading_day,
    overnight_session_bounds,
    overnight_trading_day,
    price_bucket,
)


def test_price_bucket():
    assert price_bucket(4213.25) == 4213.25
    assert price_bucket(4213.22) == 4213.25


def test_vpoc_tie_midpoint():
    bins = {4000.0: 100.0, 4000.25: 100.0}
    assert vpoc_from_bins(bins) == 4000.125


def test_overnight_trading_day():
    d = date(2024, 5, 15)
    assert overnight_trading_day(datetime(2024, 5, 14, 18, 0, tzinfo=CHICAGO)) == d
    assert overnight_trading_day(datetime(2024, 5, 15, 7, 0, 0, tzinfo=CHICAGO)) == d
    assert overnight_trading_day(datetime(2024, 5, 15, 8, 29, 0, tzinfo=CHICAGO)) == d
    assert overnight_trading_day(datetime(2024, 5, 15, 8, 30, 0, tzinfo=CHICAGO)) is None


def test_day_trading_day():
    d = date(2024, 5, 15)
    assert day_trading_day(datetime(2024, 5, 15, 8, 30, 0, tzinfo=CHICAGO)) == d
    assert day_trading_day(datetime(2024, 5, 15, 15, 59, 0, tzinfo=CHICAGO)) == d
    assert day_trading_day(datetime(2024, 5, 15, 16, 0, 0, tzinfo=CHICAGO)) is None


def test_overnight_bounds():
    d = date(2024, 5, 15)
    lo, hi = overnight_session_bounds(d)
    assert lo == datetime(2024, 5, 14, 17, 0, tzinfo=CHICAGO)
    assert hi == datetime(2024, 5, 15, 8, 30, tzinfo=CHICAGO)


def test_classify_open_bucket():
    assert classify_open_bucket(100.5, 100.0, 102.0, 99.0) == "inside_gap_up"
    assert classify_open_bucket(99.5, 100.0, 102.0, 99.0) == "inside_gap_down"
    assert classify_open_bucket(103.0, 100.0, 102.0, 99.0) == "above_prior_range"
    assert classify_open_bucket(98.0, 100.0, 102.0, 99.0) == "below_prior_range"
    assert classify_open_bucket(100.0, 100.0, 102.0, 99.0) == "boundary"


def test_level_hit():
    assert level_hit(3998.0, 4010.0, 4005.0) is True
    assert level_hit(3998.0, 4010.0, 3990.0) is False
    assert level_hit(3998.0, 4010.0, None) is None


def test_synthetic_fixture_pipeline():
    path = __file__.replace("test_analysis.py", "fixtures/synthetic_ticks.csv")
    df = pd.read_csv(path, sep="\t", names=["SYMBOL", "DATE", "PRICE", "TICKVOL", "BID", "ASK"])
    on_aggs = {}
    day_aggs = {}
    process_ticks_frame(df, on_aggs, day_aggs)

    assert date(2024, 1, 2) in day_aggs
    assert date(2024, 1, 3) in day_aggs
    assert date(2024, 1, 3) in on_aggs

    rows = build_daily_rows(on_aggs, day_aggs)
    by_day = {r["trading_day"]: r for r in rows}
    jan3 = by_day["2024-01-03"]
    assert jan3["open_bucket"] == "inside_gap_down"
    assert jan3["hit_onmid"] in (True, False, None)
    assert jan3["hit_onl"] is True
    assert jan3["onl"] == 3985.0
    assert jan3["onh"] == 4015.0

    prob = conditional_probabilities(rows)
    assert not prob.empty


def test_naive_ts_treated_as_chicago():
    ts = datetime(2024, 5, 15, 9, 0, 0)
    t2 = as_chicago_ts(ts)
    assert t2.tzinfo == CHICAGO


def _fixture_path() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "synthetic_ticks.csv"


def test_run_pipeline_sample_window_fewer_or_equal_rows():
    path = _fixture_path()
    full_daily, _, _, _ = run_pipeline(str(path), chunksize=1000)
    win_daily, _, _, meta = run_pipeline(str(path), chunksize=1000, max_calendar_days=60)
    assert len(win_daily) <= len(full_daily)
    assert meta.get("anchor_date") == "2024-01-02"
    assert meta.get("max_calendar_days") == 60


def test_run_pipeline_one_calendar_day_excludes_later_days():
    path = _fixture_path()
    daily, _, _, meta = run_pipeline(str(path), chunksize=1000, max_calendar_days=1)
    assert meta["anchor_date"] == "2024-01-02"
    assert meta["last_inclusive_date"] == "2024-01-02"
    days = set(daily["trading_day"].tolist())
    assert days == {"2024-01-02"}
    assert len(daily) == 1


def test_run_pipeline_two_calendar_days_includes_jan3():
    path = _fixture_path()
    daily, _, _, meta = run_pipeline(str(path), chunksize=1000, max_calendar_days=2)
    assert meta["last_inclusive_date"] == "2024-01-03"
    assert len(daily) == 2


def test_post_ib_exceed_flags_synthetic_jan3():
    """IB 4002–4008 (w=6); post-IB 4000/3980/3998 → exceed IBL and lower 1.5, not IBH/upper 1.5."""
    path = _fixture_path()
    daily, _, _, _ = run_pipeline(str(path), chunksize=1000, max_calendar_days=60)
    jan3 = daily[daily["trading_day"] == "2024-01-03"].iloc[0]
    assert jan3["ibh"] == 4008.0
    assert jan3["ibl"] == 4002.0
    assert jan3["post_ib_high"] == 4000.0
    assert jan3["post_ib_low"] == 3980.0
    assert jan3["post_ib_exceed_ibh"] is False
    assert jan3["post_ib_exceed_ibl"] is True
    assert jan3["post_ib_exceed_upper_1p5"] is False
    assert jan3["post_ib_exceed_lower_1p5"] is True
