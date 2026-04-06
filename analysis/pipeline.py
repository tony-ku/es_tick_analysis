"""Single-pass tick processing and daily metrics / probabilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from .aggregates import DaySessionAgg, OvernightAgg
from .sessions import as_chicago_ts, day_trading_day, overnight_trading_day


def _is_data_row(sym: Any) -> bool:
    if pd.isna(sym):
        return False
    s = str(sym).strip()
    if not s or s.upper() == "-SYMBOL" or s.upper().startswith("SYMBOL"):
        return False
    return True


# Open vs prior-day session (strict inequalities); order matches stats tables.
OPEN_BUCKET_ORDER = [
    "inside_gap_up",
    "inside_gap_down",
    "above_prior_range",
    "below_prior_range",
]

OPEN_BUCKET_TITLES = {
    "inside_gap_up": "Inside gap up",
    "inside_gap_down": "Inside gap down",
    "above_prior_range": "Above prior day range",
    "below_prior_range": "Below prior day range",
}


def classify_open_bucket(
    open_px: float,
    prior_close: float,
    prior_high: float,
    prior_low: float,
) -> str:
    """Map open to bucket id; strict inequalities else boundary."""
    if open_px > prior_close and open_px < prior_high:
        return "inside_gap_up"
    if open_px < prior_close and open_px > prior_low:
        return "inside_gap_down"
    if open_px > prior_close and open_px > prior_high:
        return "above_prior_range"
    if open_px < prior_close and open_px < prior_low:
        return "below_prior_range"
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
    ts_series = pd.to_datetime(df["DATE"], errors="coerce", format="mixed")
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
    for i in idx:
        try:
            raw_t = ts_vals[i]
            if pd.isna(raw_t):
                continue
            ts = as_chicago_ts(pd.Timestamp(raw_t).to_pydatetime())
            _apply_tick(ts, float(p_arr[i]), float(v_arr[i]), on_aggs, day_aggs)
        except (ValueError, TypeError, OverflowError):
            continue


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
    for i in idx:
        try:
            raw_t = ts_vals[i]
            if pd.isna(raw_t):
                continue
            ts = as_chicago_ts(pd.Timestamp(raw_t).to_pydatetime())
            td = ts.date()
            st = window.classify_tick_date(td)
            if st == "stop":
                return True
            if st == "skip":
                continue
            _apply_tick(ts, float(p_arr[i]), float(v_arr[i]), on_aggs, day_aggs)
        except (ValueError, TypeError, OverflowError):
            continue
    return False


def build_daily_rows(
    on_aggs: Dict[date, OvernightAgg],
    day_aggs: Dict[date, DaySessionAgg],
) -> List[Dict[str, Any]]:
    """One row per trading day that has a day session; needs prior calendar day for context."""
    rows: List[Dict[str, Any]] = []
    for d in sorted(day_aggs.keys()):
        day = day_aggs[d]
        if day.min_p == float("inf"):
            continue

        prior = d - timedelta(days=1)
        prior_day = day_aggs.get(prior)

        on = on_aggs.get(d)
        if on is None or on.min_p == float("inf"):
            onh = onl = onmid = on_vpoc = None
        else:
            onh, onl = on.onh(), on.onl()
            onmid = on.onmid()
            on_vpoc = on.on_vpoc()

        if prior_day is None or prior_day.min_p == float("inf"):
            prior_high = prior_low = prior_close = prior_vpoc = None
        else:
            prior_high = prior_day.max_p
            prior_low = prior_day.min_p
            prior_close = prior_day.last_price
            prior_vpoc = prior_day.day_vpoc()

        open_px = day.first_price
        if open_px is None:
            continue

        if (
            prior_close is not None
            and prior_high is not None
            and prior_low is not None
        ):
            bucket = classify_open_bucket(open_px, prior_close, prior_high, prior_low)
        else:
            bucket = "incomplete"

        lo, hi = day.min_p, day.max_p

        row = {
            "trading_day": d.isoformat(),
            "open": open_px,
            "prior_close": prior_close,
            "prior_day_high": prior_high,
            "prior_day_low": prior_low,
            "prior_day_vpoc": prior_vpoc,
            "open_bucket": bucket,
            "onh": onh,
            "onl": onl,
            "onmid": onmid,
            "on_vpoc": on_vpoc,
            "day_high": hi,
            "day_low": lo,
            "day_close": day.last_price,
            "day_vpoc": day.day_vpoc(),
            "ibh": day.ibh(),
            "ibl": day.ibl(),
            "hit_on_vpoc": level_hit(lo, hi, on_vpoc),
            "hit_prior_day_vpoc": level_hit(lo, hi, prior_vpoc),
            "hit_onl": level_hit(lo, hi, onl),
            "hit_onmid": level_hit(lo, hi, onmid),
            "hit_onh": level_hit(lo, hi, onh),
            "hit_prior_day_high": level_hit(lo, hi, prior_high),
            "hit_prior_day_low": level_hit(lo, hi, prior_low),
        }
        rows.append(row)
    return rows


LEVEL_KEYS = [
    "hit_on_vpoc",
    "hit_prior_day_vpoc",
    "hit_onl",
    "hit_onmid",
    "hit_onh",
    "hit_prior_day_high",
    "hit_prior_day_low",
]

LEVEL_LABELS = [
    "ON_VPOC",
    "yDay_VPOC",
    "ONL",
    "ONMID",
    "ONH",
    "yDay_High",
    "yDay_Low",
]


def conditional_probabilities(
    rows: List[Dict[str, Any]],
    buckets: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Rows: bucket; cols: level, count_bucket, hit_count, probability."""
    if buckets is None:
        buckets = list(OPEN_BUCKET_ORDER)
    out_rows = []
    for b in buckets:
        sub = [r for r in rows if r.get("open_bucket") == b]
        n = len(sub)
        for key, label in zip(LEVEL_KEYS, LEVEL_LABELS):
            hits = [r for r in sub if r.get(key) is True]
            miss = [r for r in sub if r.get(key) is False]
            undef = [r for r in sub if r.get(key) is None]
            n_valid = len(hits) + len(miss)
            p = (len(hits) / n_valid) if n_valid > 0 else float("nan")
            out_rows.append(
                {
                    "bucket": b,
                    "level": label,
                    "days_in_bucket": n,
                    "days_level_defined": n_valid,
                    "days_undefined_level": len(undef),
                    "hit_count": len(hits),
                    "probability": p,
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
) -> tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Read tick file in chunks; return (daily_metrics_df, conditional_prob_df, meta).

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
    return daily_df, prob_df, meta


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
    header = ["Level", "Days (bucket)", "Defined", "Hits", "P(hit)"]

    for b in OPEN_BUCKET_ORDER:
        sub = prob_df[prob_df["bucket"] == b]
        if sub.empty:
            continue
        flag = " **(n<20)**" if sub["small_sample"].any() else ""
        title = OPEN_BUCKET_TITLES.get(b, b)
        lines.append(f"\n## {title} (`{b}`){flag}\n")

        body: List[List[str]] = []
        for _, r in sub.iterrows():
            p = r["probability"]
            ps = f"{p:.4f}" if pd.notna(p) else "nan"
            body.append(
                [
                    str(r["level"]),
                    str(int(r["days_in_bucket"])),
                    str(int(r["days_level_defined"])),
                    str(int(r["hit_count"])),
                    ps,
                ]
            )
        lines.extend(_markdown_table(header, body))
    return "\n".join(lines)
