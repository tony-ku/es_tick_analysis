"""Single-pass tick processing and daily metrics / probabilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from .aggregates import DaySessionAgg, OvernightAgg
from .sessions import (
    CHICAGO,
    DAY_CLOSE_S,
    DAY_OPEN_S,
    IB_END_S,
    ON_OPEN_S,
    as_chicago_ts,
    day_trading_day,
    overnight_trading_day,
)


def _is_data_row(sym: Any) -> bool:
    if pd.isna(sym):
        return False
    s = str(sym).strip()
    if not s or s.upper() == "-SYMBOL" or s.upper().startswith("SYMBOL"):
        return False
    return True


# Open vs prior-day session (strict inequalities); order matches stats tables.
OPEN_BUCKET_ORDER = [
    "HIR",
    "LIR",
    "HOR",
    "LOR",
]

OPEN_BUCKET_TITLES = {
    "HIR": "HIR",
    "LIR": "LIR",
    "HOR": "HOR",
    "LOR": "LOR",
}

# Absolute open vs prior close as % of prior close; non-overlapping ranges.
GAP_FILL_BUCKET_ORDER = [
    "gap_0_to_0p5_pct",
    "gap_0p5_to_1_pct",
    "gap_1_to_2_pct",
    "gap_gt_2_pct",
]

GAP_FILL_BUCKET_TITLES = {
    "gap_0_to_0p5_pct": "0% < gap ≤ 0.5%",
    "gap_0p5_to_1_pct": "0.5% < gap ≤ 1%",
    "gap_1_to_2_pct": "1% < gap ≤ 2%",
    "gap_gt_2_pct": "gap > 2%",
}


def classify_gap_size_bucket(gap_pct: float) -> str:
    """Map positive gap size (%) to bucket id; (0,0.5], (0.5,1], (1,2], (2,inf)."""
    if gap_pct <= 0:
        raise ValueError("gap_pct must be positive")
    if gap_pct <= 0.5:
        return "gap_0_to_0p5_pct"
    if gap_pct <= 1.0:
        return "gap_0p5_to_1_pct"
    if gap_pct <= 2.0:
        return "gap_1_to_2_pct"
    return "gap_gt_2_pct"


def classify_open_bucket(
    open_px: float,
    prior_close: float,
    prior_high: float,
    prior_low: float,
) -> str:
    """Map open to bucket id. Equality tie-breaks: == close → HIR, == prior_high → HIR, == prior_low → LIR."""
    if open_px == prior_close:
        return "HIR"
    if open_px == prior_high:
        return "HIR"
    if open_px == prior_low:
        return "LIR"
    if open_px > prior_close and open_px < prior_high:
        return "HIR"
    if open_px < prior_close and open_px > prior_low:
        return "LIR"
    if open_px > prior_close and open_px > prior_high:
        return "HOR"
    if open_px < prior_close and open_px < prior_low:
        return "LOR"
    return "boundary"


def level_hit(day_low: float, day_high: float, level: Optional[float]) -> Optional[bool]:
    if level is None:
        return None
    return day_low <= level <= day_high


def _vector_data_mask_from_cols(df: pd.DataFrame, ts_series: pd.Series) -> np.ndarray:
    """Same rules as `_is_data_row` + valid parsed DATE (vectorized)."""
    sym = df["SYMBOL"]
    na_sym = sym.isna()
    s = sym.astype(str).str.strip()
    bad = (
        na_sym
        | s.eq("")
        | s.eq("nan")
        | s.str.upper().eq("-SYMBOL")
        | s.str.upper().str.startswith("SYMBOL")
    )
    return (~bad & ts_series.notna()).to_numpy(dtype=bool)


def _chunk_tick_arrays(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    One vectorized parse per chunk: DATE, SYMBOL filter, numeric PRICE/TICKVOL.
    Returns (row_indices, ts_vals, price_arr, vol_arr) for rows to process.
    """
    # Investor/RT-style ISO strings; `mixed` avoids per-element fallback when possible
    ts_series = pd.to_datetime(df["DATE"], errors="coerce", format="%Y-%m-%dT%H:%M:%S")
    base = _vector_data_mask_from_cols(df, ts_series)
    prices = pd.to_numeric(df["PRICE"], errors="coerce")
    vols = pd.to_numeric(df["TICKVOL"], errors="coerce")
    good = base & prices.notna().to_numpy() & vols.notna().to_numpy()
    idx = np.flatnonzero(good)
    return (
        idx,
        ts_series.values,
        prices.to_numpy(dtype=np.float64, copy=False),
        vols.to_numpy(dtype=np.float64, copy=False),
    )


def _vectorized_session_aggs(
    idx: np.ndarray,
    ts_vals: np.ndarray,
    p_arr: np.ndarray,
    v_arr: np.ndarray,
    on_aggs: Dict[date, OvernightAgg],
    day_aggs: Dict[date, DaySessionAgg],
) -> None:
    """Vectorized session classification and aggregation for one chunk."""
    if len(idx) == 0:
        return

    # Slice to valid rows only
    ts = ts_vals[idx]
    prices = p_arr[idx]
    vols = v_arr[idx]

    # Time decomposition (numpy, no Python loop)
    dates_d64 = ts.astype("datetime64[D]")
    time_of_day_s = (ts - dates_d64).astype("timedelta64[s]").astype(np.int64)

    # Session classification masks
    is_evening = time_of_day_s >= ON_OPEN_S
    is_morning = time_of_day_s < DAY_OPEN_S
    is_overnight = is_evening | is_morning
    is_day = (time_of_day_s >= DAY_OPEN_S) & (time_of_day_s < DAY_CLOSE_S)

    # Overnight trading day: evening -> date+1, morning -> same date
    on_trading_day_d64 = np.where(
        is_evening,
        dates_d64 + np.timedelta64(1, "D"),
        dates_d64,
    )

    # Price bucketing (vectorized)
    bucketed = np.floor(prices * 4.0 + 0.5) / 4.0
    has_vol = vols > 0

    # Overnight aggregation
    if is_overnight.any():
        on_idx = np.flatnonzero(is_overnight)
        on_dates = on_trading_day_d64[on_idx]
        on_prices = prices[on_idx]
        on_vols = vols[on_idx]
        on_bucketed = bucketed[on_idx]
        on_has_vol = has_vol[on_idx]

        unique_on_days, inverse = np.unique(on_dates, return_inverse=True)
        for j, ud64 in enumerate(unique_on_days):
            mask_j = inverse == j
            d = ud64.item()  # numpy datetime64[D] -> Python date
            chunk_min = float(on_prices[mask_j].min())
            chunk_max = float(on_prices[mask_j].max())
            vol_mask = mask_j & on_has_vol
            vol_bins: Dict[float, float] = {}
            if vol_mask.any():
                ub, inv_b = np.unique(on_bucketed[vol_mask], return_inverse=True)
                vol_sums = np.zeros(len(ub), dtype=np.float64)
                np.add.at(vol_sums, inv_b, on_vols[vol_mask])
                vol_bins = dict(zip(ub.tolist(), vol_sums.tolist()))
            on_aggs.setdefault(d, OvernightAgg()).bulk_merge(chunk_min, chunk_max, vol_bins)

    # Day session aggregation
    if is_day.any():
        day_idx = np.flatnonzero(is_day)
        day_dates = dates_d64[day_idx]
        day_ts = ts[day_idx]
        day_prices = prices[day_idx]
        day_vols = vols[day_idx]
        day_bucketed = bucketed[day_idx]
        day_has_vol = has_vol[day_idx]
        day_tod = time_of_day_s[day_idx]

        unique_day_days, inverse = np.unique(day_dates, return_inverse=True)
        for j, ud64 in enumerate(unique_day_days):
            mask_j = inverse == j
            d = ud64.item()

            d_prices = day_prices[mask_j]
            d_ts = day_ts[mask_j]
            chunk_min = float(d_prices.min())
            chunk_max = float(d_prices.max())

            # Volume bins
            vol_mask = mask_j & day_has_vol
            vol_bins_day: Dict[float, float] = {}
            if vol_mask.any():
                ub, inv_b = np.unique(day_bucketed[vol_mask], return_inverse=True)
                vol_sums = np.zeros(len(ub), dtype=np.float64)
                np.add.at(vol_sums, inv_b, day_vols[vol_mask])
                vol_bins_day = dict(zip(ub.tolist(), vol_sums.tolist()))

            # First/last tick by timestamp
            first_idx_local = int(np.argmin(d_ts))
            max_ts_val = d_ts.max()
            last_idx_local = int(np.flatnonzero(d_ts == max_ts_val)[-1])

            first_ts_dt = pd.Timestamp(d_ts[first_idx_local]).to_pydatetime().replace(tzinfo=CHICAGO)
            first_price = float(d_prices[first_idx_local])
            last_ts_dt = pd.Timestamp(d_ts[last_idx_local]).to_pydatetime().replace(tzinfo=CHICAGO)
            last_price = float(d_prices[last_idx_local])

            # IB min/max (08:30 <= tod < 09:30)
            d_tod = day_tod[mask_j]
            ib_mask_local = d_tod < IB_END_S
            ib_min_v = float("inf")
            ib_max_v = float("-inf")
            if ib_mask_local.any():
                ib_min_v = float(d_prices[ib_mask_local].min())
                ib_max_v = float(d_prices[ib_mask_local].max())

            # Post-IB min/max (09:30 <= tod < 16:00)
            pib_mask_local = d_tod >= IB_END_S
            pib_min_v = float("inf")
            pib_max_v = float("-inf")
            if pib_mask_local.any():
                pib_min_v = float(d_prices[pib_mask_local].min())
                pib_max_v = float(d_prices[pib_mask_local].max())

            day_aggs.setdefault(d, DaySessionAgg()).bulk_merge(
                chunk_min, chunk_max, vol_bins_day,
                first_ts_dt, first_price,
                last_ts_dt, last_price,
                ib_min_v, ib_max_v,
                pib_min_v, pib_max_v,
            )


def _row_to_tick(row: Any) -> Optional[tuple]:
    """Parse one data row to (ts_chicago, price, vol) or None (slow path / tests)."""
    if not _is_data_row(row.get("SYMBOL")):
        return None
    try:
        ts = pd.to_datetime(row["DATE"], errors="coerce")
        if pd.isna(ts):
            return None
        if isinstance(ts, pd.Timestamp):
            ts = ts.to_pydatetime()
        ts = as_chicago_ts(ts)
        price = float(row["PRICE"])
        vol = float(row["TICKVOL"])
        return (ts, price, vol)
    except (TypeError, ValueError, KeyError):
        return None


def _apply_tick(
    ts: Any,
    price: float,
    vol: float,
    on_aggs: Dict[date, OvernightAgg],
    day_aggs: Dict[date, DaySessionAgg],
) -> None:
    od = overnight_trading_day(ts)
    if od is not None:
        on_aggs.setdefault(od, OvernightAgg()).add(price, vol)

    dd = day_trading_day(ts)
    if dd is not None:
        day_aggs.setdefault(dd, DaySessionAgg()).add(ts, price, vol)


def process_ticks_frame(df: pd.DataFrame, on_aggs: Dict[date, OvernightAgg], day_aggs: Dict[date, DaySessionAgg]) -> None:
    """Ingest a DataFrame of ticks; mutates on_aggs and day_aggs."""
    idx, ts_vals, p_arr, v_arr = _chunk_tick_arrays(df)
    _vectorized_session_aggs(idx, ts_vals, p_arr, v_arr, on_aggs, day_aggs)


@dataclass
class CalendarWindowState:
    """First-tick anchor and inclusive end date for sample-window runs."""

    max_calendar_days: int
    anchor_date: Optional[date] = None
    last_inclusive: Optional[date] = None

    def classify_tick_date(self, ts_date: date) -> Literal["ok", "skip", "stop"]:
        """After anchor is set: stop if past window; skip if before anchor (out-of-order)."""
        if self.anchor_date is None:
            self.anchor_date = ts_date
            self.last_inclusive = self.anchor_date + timedelta(days=self.max_calendar_days - 1)
        if ts_date > self.last_inclusive:
            return "stop"
        if ts_date < self.anchor_date:
            return "skip"
        return "ok"


def process_ticks_frame_windowed(
    df: pd.DataFrame,
    on_aggs: Dict[date, OvernightAgg],
    day_aggs: Dict[date, DaySessionAgg],
    window: CalendarWindowState,
) -> bool:
    """
    Ingest ticks within [anchor, last_inclusive] (anchor from first valid tick).
    Returns True if the caller should stop reading the file (saw a tick past the window).
    """
    idx, ts_vals, p_arr, v_arr = _chunk_tick_arrays(df)
    if len(idx) == 0:
        return False

    # Extract calendar dates for valid ticks (naive-Chicago datetime64 -> date)
    ts_valid = ts_vals[idx]
    cal_dates = ts_valid.astype("datetime64[D]")

    # Set anchor from first valid tick if needed
    if window.anchor_date is None:
        first_date = cal_dates[0].item()  # numpy datetime64[D] -> Python date
        window.anchor_date = first_date
        window.last_inclusive = first_date + timedelta(days=window.max_calendar_days - 1)

    # Vectorized window check
    anchor_d64 = np.datetime64(window.anchor_date, "D")
    last_d64 = np.datetime64(window.last_inclusive, "D")

    past_window = cal_dates > last_d64
    before_anchor = cal_dates < anchor_d64
    in_window = ~past_window & ~before_anchor

    saw_stop = bool(past_window.any())

    if in_window.any():
        win_orig_idx = idx[np.flatnonzero(in_window)]
        _vectorized_session_aggs(win_orig_idx, ts_vals, p_arr, v_arr, on_aggs, day_aggs)

    return saw_stop


def build_daily_rows(
    on_aggs: Dict[date, OvernightAgg],
    day_aggs: Dict[date, DaySessionAgg],
) -> List[Dict[str, Any]]:
    """One row per trading day that has a day session; prior context is the most recent prior trading day with data (Friday for Monday, last pre-holiday day post-holiday)."""
    rows: List[Dict[str, Any]] = []
    prev_valid: Optional[DaySessionAgg] = None
    for d in sorted(day_aggs.keys()):
        day = day_aggs[d]
        if day.min_p == float("inf"):
            continue

        prior_day = prev_valid
        prev_valid = day

        on = on_aggs.get(d)
        if on is None or on.min_p == float("inf"):
            onh = onl = onmid = on_vpoc = None
        else:
            onh, onl = on.onh(), on.onl()
            onmid = on.onmid()
            on_vpoc = on.on_vpoc()

        if prior_day is None or prior_day.min_p == float("inf"):
            prior_high = prior_low = prior_close = prior_vpoc = None
            prior_vah = prior_val = None
        else:
            prior_high = prior_day.max_p
            prior_low = prior_day.min_p
            prior_close = prior_day.last_price
            prior_vpoc = prior_day.day_vpoc()
            prior_vah, prior_val = prior_day.day_value_area()

        open_px = day.first_price
        if open_px is None:
            continue

        if prior_close is None or prior_high is None or prior_low is None:
            continue
        bucket = classify_open_bucket(open_px, prior_close, prior_high, prior_low)

        lo, hi = day.min_p, day.max_p

        ibh_v = day.ibh()
        ibl_v = day.ibl()
        post_hi = day.post_ib_high()
        post_lo = day.post_ib_low()
        ib_width = (ibh_v - ibl_v) if ibh_v is not None and ibl_v is not None else None

        post_ib_exceed_ibh: Optional[bool] = None
        if ibh_v is not None and post_hi is not None:
            post_ib_exceed_ibh = post_hi > ibh_v

        post_ib_exceed_ibl: Optional[bool] = None
        if ibl_v is not None and post_lo is not None:
            post_ib_exceed_ibl = post_lo < ibl_v

        post_ib_exceed_upper_1p5: Optional[bool] = None
        post_ib_exceed_lower_1p5: Optional[bool] = None
        if (
            ibh_v is not None
            and ibl_v is not None
            and post_hi is not None
            and post_lo is not None
            and ib_width is not None
            and ib_width > 0
        ):
            upper_1p5 = ibh_v + 1.5 * ib_width
            lower_1p5 = ibl_v - 1.5 * ib_width
            post_ib_exceed_upper_1p5 = post_hi > upper_1p5
            post_ib_exceed_lower_1p5 = post_lo < lower_1p5

        gap_pct: Optional[float] = None
        gap_filled: Optional[bool] = None
        gap_size_bucket: Optional[str] = None
        if prior_close is not None and prior_close > 0 and open_px != prior_close:
            gap_pct = abs(open_px - prior_close) / prior_close * 100.0
            gap_filled = level_hit(lo, hi, prior_close)
            gap_size_bucket = classify_gap_size_bucket(gap_pct)

        row = {
            "trading_day": d.isoformat(),
            "open": open_px,
            "prior_close": prior_close,
            "prior_day_high": prior_high,
            "prior_day_low": prior_low,
            "prior_day_vpoc": prior_vpoc,
            "prior_day_vah": prior_vah,
            "prior_day_val": prior_val,
            "open_bucket": bucket,
            "onh": onh,
            "onl": onl,
            "onmid": onmid,
            "on_vpoc": on_vpoc,
            "day_high": hi,
            "day_low": lo,
            "day_close": day.last_price,
            "day_vpoc": day.day_vpoc(),
            "ibh": ibh_v,
            "ibl": ibl_v,
            "post_ib_high": post_hi,
            "post_ib_low": post_lo,
            "hit_on_vpoc": level_hit(lo, hi, on_vpoc),
            "hit_prior_day_vpoc": level_hit(lo, hi, prior_vpoc),
            "hit_onl": level_hit(lo, hi, onl),
            "hit_onmid": level_hit(lo, hi, onmid),
            "hit_onh": level_hit(lo, hi, onh),
            "hit_onh_or_onl": (
                None if (onh is None or onl is None)
                else (level_hit(lo, hi, onh) or level_hit(lo, hi, onl))
            ),
            "hit_prior_day_high": level_hit(lo, hi, prior_high),
            "hit_prior_day_low": level_hit(lo, hi, prior_low),
            "hit_prior_day_vah": level_hit(lo, hi, prior_vah),
            "hit_prior_day_val": level_hit(lo, hi, prior_val),
            "post_ib_exceed_ibh": post_ib_exceed_ibh,
            "post_ib_exceed_ibl": post_ib_exceed_ibl,
            "post_ib_exceed_upper_1p5": post_ib_exceed_upper_1p5,
            "post_ib_exceed_lower_1p5": post_ib_exceed_lower_1p5,
            "gap_pct": gap_pct,
            "gap_filled": gap_filled,
            "gap_size_bucket": gap_size_bucket,
        }
        rows.append(row)
    return rows


LEVEL_KEYS = [
    "hit_on_vpoc",
    "hit_prior_day_vpoc",
    "hit_onl",
    "hit_onmid",
    "hit_onh",
    "hit_onh_or_onl",
    "hit_prior_day_high",
    "hit_prior_day_low",
    "hit_prior_day_vah",
    "hit_prior_day_val",
]

LEVEL_LABELS = [
    "ONPOC",
    "pPOC",
    "ONL",
    "ONMID",
    "ONH",
    "ONH_or_ONL",
    "pHigh",
    "pLow",
    "pVAH",
    "pVAL",
]

POST_IB_LEVEL_KEYS = [
    "post_ib_exceed_ibh",
    "post_ib_exceed_ibl",
    "post_ib_exceed_upper_1p5",
    "post_ib_exceed_lower_1p5",
]

POST_IB_LEVEL_LABELS = [
    "post-IB high > IBH",
    "post-IB low < IBL",
    "post-IB high > IBH + 1.5*(IBH-IBL)",
    "post-IB low < IBL - 1.5*(IBH-IBL)",
]


def conditional_probabilities(
    rows: List[Dict[str, Any]],
    buckets: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Rows: bucket; cols: level, counts, probability_pct (0–100), pct_of_total_days (bucket share of all daily rows)."""
    if buckets is None:
        buckets = list(OPEN_BUCKET_ORDER)
    total_days = len(rows)
    out_rows = []
    for b in buckets:
        sub = [r for r in rows if r.get("open_bucket") == b]
        n = len(sub)
        share = (100.0 * n / total_days) if total_days > 0 else float("nan")
        for key, label in zip(LEVEL_KEYS, LEVEL_LABELS):
            hits = [r for r in sub if r.get(key) is True]
            miss = [r for r in sub if r.get(key) is False]
            undef = [r for r in sub if r.get(key) is None]
            n_valid = len(hits) + len(miss)
            p = (len(hits) / n_valid) if n_valid > 0 else float("nan")
            pct = (100.0 * p) if pd.notna(p) else float("nan")
            out_rows.append(
                {
                    "bucket": b,
                    "level": label,
                    "days_in_bucket": n,
                    "pct_of_total_days": share,
                    "days_level_defined": n_valid,
                    "days_undefined_level": len(undef),
                    "hit_count": len(hits),
                    "probability_pct": pct,
                    "small_sample": n < 20,
                }
            )
    return pd.DataFrame(out_rows)


def conditional_probabilities_post_ib(
    rows: List[Dict[str, Any]],
    buckets: Optional[List[str]] = None,
) -> pd.DataFrame:
    """P(exceed level in post-IB window | open bucket); same schema as conditional_probabilities."""
    if buckets is None:
        buckets = list(OPEN_BUCKET_ORDER)
    total_days = len(rows)
    out_rows = []
    for b in buckets:
        sub = [r for r in rows if r.get("open_bucket") == b]
        n = len(sub)
        share = (100.0 * n / total_days) if total_days > 0 else float("nan")
        for key, label in zip(POST_IB_LEVEL_KEYS, POST_IB_LEVEL_LABELS):
            hits = [r for r in sub if r.get(key) is True]
            miss = [r for r in sub if r.get(key) is False]
            undef = [r for r in sub if r.get(key) is None]
            n_valid = len(hits) + len(miss)
            p = (len(hits) / n_valid) if n_valid > 0 else float("nan")
            pct = (100.0 * p) if pd.notna(p) else float("nan")
            out_rows.append(
                {
                    "bucket": b,
                    "level": label,
                    "days_in_bucket": n,
                    "pct_of_total_days": share,
                    "days_level_defined": n_valid,
                    "days_undefined_level": len(undef),
                    "hit_count": len(hits),
                    "probability_pct": pct,
                    "small_sample": n < 20,
                }
            )
    return pd.DataFrame(out_rows)


def gap_fill_probabilities(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """P(gap filled | gap size bucket); gap days only (open != prior_close, prior_close > 0). pct_of_total_days is share of all daily rows, not gap-days only."""
    total_days = len(rows)
    out_rows = []
    for b in GAP_FILL_BUCKET_ORDER:
        sub = [r for r in rows if r.get("gap_size_bucket") == b]
        n = len(sub)
        share = (100.0 * n / total_days) if total_days > 0 else float("nan")
        fills = [r for r in sub if r.get("gap_filled") is True]
        misses = [r for r in sub if r.get("gap_filled") is False]
        n_valid = len(fills) + len(misses)
        p = (len(fills) / n_valid) if n_valid > 0 else float("nan")
        pct = (100.0 * p) if pd.notna(p) else float("nan")
        out_rows.append(
            {
                "gap_bucket": b,
                "days_in_bucket": n,
                "pct_of_total_days": share,
                "gap_fill_count": len(fills),
                "probability_pct": pct,
                "small_sample": n < 20,
            }
        )
    return pd.DataFrame(out_rows)


def _read_csv_chunks(
    input_path: str,
    chunksize: int,
):
    cols = ["SYMBOL", "DATE", "PRICE", "TICKVOL", "BID", "ASK"]
    common = dict(
        sep="\t",
        names=cols,
        chunksize=chunksize,
        dtype={"SYMBOL": str},
        low_memory=False,
    )
    try:
        return pd.read_csv(input_path, **common, on_bad_lines="skip")
    except TypeError:
        return pd.read_csv(input_path, **common, error_bad_lines=False)


def run_pipeline(
    input_path: str,
    chunksize: int = 1_000_000,
    max_calendar_days: Optional[int] = None,
    verbose: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Read tick file in chunks; return (daily_metrics_df, conditional_prob_df,
    conditional_prob_post_ib_df, gap_fill_prob_df, meta).

    When max_calendar_days is set, only ticks with Chicago date in
    [anchor_date, anchor_date + max_calendar_days - 1] are processed (anchor = date
    of first valid tick). Reading stops once a tick after the window is seen.
    """
    on_aggs: Dict[date, OvernightAgg] = {}
    day_aggs: Dict[date, DaySessionAgg] = {}
    meta: Dict[str, Any] = {}

    reader = _read_csv_chunks(input_path, chunksize)

    t0 = time.perf_counter()
    n_chunks = 0
    if max_calendar_days is not None:
        if max_calendar_days < 1:
            raise ValueError("max_calendar_days must be >= 1")
        window = CalendarWindowState(max_calendar_days=max_calendar_days)
        for chunk in reader:
            n_chunks += 1
            stop = process_ticks_frame_windowed(chunk, on_aggs, day_aggs, window)
            if verbose and n_chunks % 20 == 0:
                print(
                    f"  chunks={n_chunks} elapsed={time.perf_counter() - t0:.1f}s",
                    flush=True,
                )
            if stop:
                break
        if window.anchor_date is not None:
            meta["anchor_date"] = window.anchor_date.isoformat()
            meta["last_inclusive_date"] = window.last_inclusive.isoformat() if window.last_inclusive else ""
            meta["max_calendar_days"] = max_calendar_days
    else:
        for chunk in reader:
            n_chunks += 1
            process_ticks_frame(chunk, on_aggs, day_aggs)
            if verbose and n_chunks % 20 == 0:
                print(
                    f"  chunks={n_chunks} elapsed={time.perf_counter() - t0:.1f}s",
                    flush=True,
                )
    if verbose:
        print(
            f"Tick ingest: {n_chunks} chunk(s) in {time.perf_counter() - t0:.1f}s",
            flush=True,
        )

    rows = build_daily_rows(on_aggs, day_aggs)
    daily_df = pd.DataFrame(rows)
    prob_df = conditional_probabilities(rows)
    prob_post_ib_df = conditional_probabilities_post_ib(rows)
    prob_gap_fill_df = gap_fill_probabilities(rows)
    return daily_df, prob_df, prob_post_ib_df, prob_gap_fill_df, meta


def _markdown_table(header: List[str], body: List[List[str]]) -> List[str]:
    """Aligned pipe table: column widths from header and body."""
    n = len(header)
    widths = [len(header[i]) for i in range(n)]
    for row in body:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: List[str]) -> str:
        return "| " + " | ".join(cells[i].ljust(widths[i]) for i in range(n)) + " |"

    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    out = [fmt_row(header), sep]
    out.extend(fmt_row(row) for row in body)
    return out


def probabilities_to_markdown(prob_df: pd.DataFrame) -> str:
    """Pivot-style markdown table for readability (aligned columns)."""
    lines: List[str] = ["# Conditional hit probabilities P(hit | open bucket)\n"]
    header = ["Level", "Days (bucket)", "% of total days", "Defined", "Hits", "% hit"]

    for b in OPEN_BUCKET_ORDER:
        sub = prob_df[prob_df["bucket"] == b]
        if sub.empty:
            continue
        flag = " **(n<20)**" if sub["small_sample"].any() else ""
        title = OPEN_BUCKET_TITLES.get(b, b)
        lines.append(f"\n## {title} (`{b}`){flag}\n")

        sub_sorted = sub.sort_values("probability_pct", ascending=False, na_position="last")
        body: List[List[str]] = []
        for _, r in sub_sorted.iterrows():
            p = r["probability_pct"]
            ps = f"{p:.2f}%" if pd.notna(p) else "nan"
            share = r["pct_of_total_days"]
            ss = f"{share:.2f}%" if pd.notna(share) else "nan"
            body.append(
                [
                    str(r["level"]),
                    str(int(r["days_in_bucket"])),
                    ss,
                    str(int(r["days_level_defined"])),
                    str(int(r["hit_count"])),
                    ps,
                ]
            )
        lines.extend(_markdown_table(header, body))
    return "\n".join(lines)


def probabilities_post_ib_to_markdown(prob_df: pd.DataFrame) -> str:
    """Markdown tables for post-IB exceed rates (aligned columns)."""
    lines: List[str] = [
        "# Post-IB session: P(exceed IBH / IBL / 1.5× IB range | open bucket)\n",
        "\nAfter IB ends (09:30 Chicago), we use only **post-IB** prices in **[09:30, 16:00)**. "
        "**IBH** / **IBL** come from the first hour **[08:30, 09:30)**. "
        "**1.5× IB range** means **1.5 × (IBH − IBL)** added above IBH or subtracted below IBL (not 1.5× price). "
        "A day is skipped for a row if IB or post-IB range is missing, or IB width is 0 for the extension rows.\n",
    ]
    header = ["Level", "Days (bucket)", "% of total days", "Defined", "Hits", "% hit"]

    for b in OPEN_BUCKET_ORDER:
        sub = prob_df[prob_df["bucket"] == b]
        if sub.empty:
            continue
        flag = " **(n<20)**" if sub["small_sample"].any() else ""
        title = OPEN_BUCKET_TITLES.get(b, b)
        lines.append(f"\n## {title} (`{b}`){flag}\n")

        sub_sorted = sub.sort_values("probability_pct", ascending=False, na_position="last")
        body: List[List[str]] = []
        for _, r in sub_sorted.iterrows():
            p = r["probability_pct"]
            ps = f"{p:.2f}%" if pd.notna(p) else "nan"
            share = r["pct_of_total_days"]
            ss = f"{share:.2f}%" if pd.notna(share) else "nan"
            body.append(
                [
                    str(r["level"]),
                    str(int(r["days_in_bucket"])),
                    ss,
                    str(int(r["days_level_defined"])),
                    str(int(r["hit_count"])),
                    ps,
                ]
            )
        lines.extend(_markdown_table(header, body))
    return "\n".join(lines)


def probabilities_gap_fill_to_markdown(prob_gap_df: pd.DataFrame) -> str:
    """P(prior close touched in day session | gap size % of prior close)."""
    lines: List[str] = [
        "# Gap fill: P(fill | gap size)\n",
        "\n**Gap day**: prior day session close is defined, `prior_close > 0`, and day open ≠ prior close. "
        "**Gap size** = `|open − prior_close| / prior_close × 100%`. "
        "**Filled**: during today’s day session, `day_low ≤ prior_close ≤ day_high` (same inclusive rule as reference hits).\n",
    ]
    header = ["Gap size (of prior close)", "Days", "% of total days", "Fills", "% filled"]
    body: List[List[str]] = []
    flag = " **(n<20)**" if not prob_gap_df.empty and prob_gap_df["small_sample"].any() else ""
    lines.append(f"\n## By gap size bucket{flag}\n")

    for _, r in prob_gap_df.iterrows():
        p = r["probability_pct"]
        ps = f"{p:.2f}%" if pd.notna(p) else "nan"
        share = r["pct_of_total_days"]
        ss = f"{share:.2f}%" if pd.notna(share) else "nan"
        bid = str(r["gap_bucket"])
        title = GAP_FILL_BUCKET_TITLES.get(bid, bid)
        body.append(
            [
                f"{title} (`{bid}`)",
                str(int(r["days_in_bucket"])),
                ss,
                str(int(r["gap_fill_count"])),
                ps,
            ]
        )
    lines.extend(_markdown_table(header, body))
    return "\n".join(lines)


def probabilities_combined_markdown(
    prob_df: pd.DataFrame,
    prob_post_ib_df: pd.DataFrame,
    prob_gap_fill_df: Optional[pd.DataFrame] = None,
) -> str:
    """Reference-level conditional hits, post-IB exceed tables, optional gap fill."""
    out = (
        probabilities_to_markdown(prob_df)
        + "\n\n---\n\n"
        + probabilities_post_ib_to_markdown(prob_post_ib_df)
    )
    if prob_gap_fill_df is not None:
        out += "\n\n---\n\n" + probabilities_gap_fill_to_markdown(prob_gap_fill_df)
    return out
