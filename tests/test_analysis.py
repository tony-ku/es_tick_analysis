"""Tests for ES session analysis."""

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from analysis.aggregates import DaySessionAgg, OvernightAgg, vpoc_from_bins
from analysis.pipeline import (
    build_daily_rows,
    classify_gap_size_bucket,
    classify_open_bucket,
    conditional_probabilities,
    gap_fill_probabilities,
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


def test_price_bucket_half_up_not_bankers():
    # Exact half-tick inputs must round away from zero, not to nearest even.
    # Banker's rounding would map 4213.125 → 4213.0 and 4213.375 → 4213.5.
    assert price_bucket(4213.125) == 4213.25
    assert price_bucket(4213.375) == 4213.5


def test_vpoc_tie_midpoint():
    bins = {4000.0: 100.0, 4000.25: 100.0}
    assert vpoc_from_bins(bins) == 4000.125


def test_vpoc_tie_tolerates_float_drift():
    # Sums accumulated in different orders can differ by a few ULPs; the
    # two bins should still be treated as tied. `nextafter` manufactures
    # a single-ULP difference that bare `==` would reject.
    import math as _math
    a = 12345.6789
    b = _math.nextafter(a, a + 1.0)
    assert a != b
    bins = {4000.0: a, 4000.25: b}
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


def test_classify_gap_size_bucket_boundaries():
    assert classify_gap_size_bucket(0.01) == "gap_0_to_0p5_pct"
    assert classify_gap_size_bucket(0.5) == "gap_0_to_0p5_pct"
    assert classify_gap_size_bucket(0.5000001) == "gap_0p5_to_1_pct"
    assert classify_gap_size_bucket(1.0) == "gap_0p5_to_1_pct"
    assert classify_gap_size_bucket(1.0001) == "gap_1_to_2_pct"
    assert classify_gap_size_bucket(2.0) == "gap_1_to_2_pct"
    assert classify_gap_size_bucket(2.0001) == "gap_gt_2_pct"


def test_classify_open_bucket():
    assert classify_open_bucket(100.5, 100.0, 102.0, 99.0) == "HIR"
    assert classify_open_bucket(99.5, 100.0, 102.0, 99.0) == "LIR"
    assert classify_open_bucket(103.0, 100.0, 102.0, 99.0) == "HOR"
    assert classify_open_bucket(98.0, 100.0, 102.0, 99.0) == "LOR"
    # Equality tie-breaks: open == prior_close / prior_high → HIR; open == prior_low → LIR.
    assert classify_open_bucket(100.0, 100.0, 102.0, 99.0) == "HIR"
    assert classify_open_bucket(102.0, 100.0, 102.0, 99.0) == "HIR"
    assert classify_open_bucket(99.0, 100.0, 102.0, 99.0) == "LIR"


def _fake_day(first_price: float, last_price: float, lo: float, hi: float) -> DaySessionAgg:
    """Minimal DaySessionAgg populated directly (bypasses session-bounds gating)."""
    d = DaySessionAgg()
    d.min_p = lo
    d.max_p = hi
    d.first_price = first_price
    d.last_price = last_price
    d.first_ts = datetime(2024, 1, 1, 8, 30, tzinfo=CHICAGO)
    d.last_ts = datetime(2024, 1, 1, 15, 59, tzinfo=CHICAGO)
    return d


def test_prior_trading_day_is_previous_trading_day_not_calendar_day():
    """Monday's prior context must come from Friday (skipping Sat/Sun), not Sunday."""
    from analysis.pipeline import build_daily_rows

    day_aggs = {
        date(2024, 5, 17): _fake_day(4000.0, 4010.0, 3995.0, 4015.0),  # Friday
        date(2024, 5, 20): _fake_day(4012.0, 4020.0, 4008.0, 4025.0),  # Monday
    }
    rows = build_daily_rows({}, day_aggs)
    by_day = {r["trading_day"]: r for r in rows}
    mon = by_day["2024-05-20"]
    assert mon["prior_close"] == 4010.0  # Friday's last_price, not None
    assert mon["prior_day_high"] == 4015.0
    assert mon["prior_day_low"] == 3995.0
    assert mon["open_bucket"] != "incomplete"


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
    assert jan3["open_bucket"] == "LIR"
    assert jan3["hit_onmid"] in (True, False, None)
    assert jan3["hit_onl"] is True
    assert jan3["onl"] == 3985.0
    assert jan3["onh"] == 4015.0
    # Prior day close 4005 (last day-session tick on 2024-01-02); open 4002 → small gap, filled in range.
    assert jan3["prior_close"] == 4005.0
    assert jan3["gap_pct"] is not None and abs(jan3["gap_pct"] - 3.0 / 4005.0 * 100.0) < 1e-9
    assert jan3["gap_size_bucket"] == "gap_0_to_0p5_pct"
    assert jan3["gap_filled"] is True

    prob = conditional_probabilities(rows)
    assert not prob.empty
    assert "pct_of_total_days" in prob.columns
    # Each bucket row's share = days_in_bucket / total_days * 100.
    total = len(rows)
    for _, r in prob.iterrows():
        expected = 100.0 * int(r["days_in_bucket"]) / total
        assert abs(float(r["pct_of_total_days"]) - expected) < 1e-9

    gap_prob = gap_fill_probabilities(rows)
    assert len(gap_prob) == 4
    assert "pct_of_total_days" in gap_prob.columns
    row0 = gap_prob[gap_prob["gap_bucket"] == "gap_0_to_0p5_pct"].iloc[0]
    assert int(row0["days_in_bucket"]) >= 1
    assert int(row0["gap_fill_count"]) >= 1


def test_naive_ts_treated_as_chicago():
    ts = datetime(2024, 5, 15, 9, 0, 0)
    t2 = as_chicago_ts(ts)
    assert t2.tzinfo == CHICAGO


def _fixture_path() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "synthetic_ticks.csv"


def test_run_pipeline_sample_window_fewer_or_equal_rows():
    path = _fixture_path()
    full_daily, _, _, _, _ = run_pipeline(str(path), chunksize=1000)
    win_daily, _, _, _, meta = run_pipeline(str(path), chunksize=1000, max_calendar_days=60)
    assert len(win_daily) <= len(full_daily)
    assert meta.get("anchor_date") == "2024-01-02"
    assert meta.get("max_calendar_days") == 60


def test_run_pipeline_one_calendar_day_excludes_later_days():
    path = _fixture_path()
    daily, _, _, _, meta = run_pipeline(str(path), chunksize=1000, max_calendar_days=1)
    assert meta["anchor_date"] == "2024-01-02"
    assert meta["last_inclusive_date"] == "2024-01-02"
    # First day has no prior context → dropped; window is single-day so no rows.
    assert len(daily) == 0


def test_run_pipeline_two_calendar_days_includes_jan3():
    path = _fixture_path()
    daily, _, _, _, meta = run_pipeline(str(path), chunksize=1000, max_calendar_days=2)
    assert meta["last_inclusive_date"] == "2024-01-03"
    # Jan 2 dropped (first day, no prior); Jan 3 kept.
    days = set(daily["trading_day"].tolist())
    assert days == {"2024-01-03"}
    assert len(daily) == 1


def test_post_ib_exceed_flags_synthetic_jan3():
    """IB 4002–4008 (w=6); post-IB 4000/3980/3998 → exceed IBL and lower 1.5, not IBH/upper 1.5."""
    path = _fixture_path()
    daily, _, _, _, _ = run_pipeline(str(path), chunksize=1000, max_calendar_days=60)
    jan3 = daily[daily["trading_day"] == "2024-01-03"].iloc[0]
    assert jan3["ibh"] == 4008.0
    assert jan3["ibl"] == 4002.0
    assert jan3["post_ib_high"] == 4000.0
    assert jan3["post_ib_low"] == 3980.0
    assert bool(jan3["post_ib_exceed_ibh"]) is False
    assert bool(jan3["post_ib_exceed_ibl"]) is True
    assert bool(jan3["post_ib_exceed_upper_1p5"]) is False
    assert bool(jan3["post_ib_exceed_lower_1p5"]) is True
