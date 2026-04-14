"""America/Chicago session boundaries."""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")

DAY_OPEN = time(8, 30)
DAY_CLOSE = time(16, 0)
ON_OPEN = time(17, 0)
IB_END = time(9, 30)

TICK_SIZE = 0.25


def price_bucket(price: float) -> float:
    """ES tick bucket center (0.25). Half-up rounding (not banker's)."""
    return math.floor(price * 4.0 + 0.5) / 4.0


def combine_chicago(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=CHICAGO)


def day_session_bounds(d: date) -> tuple[datetime, datetime]:
    """Day session [08:30, 16:00) on date d, Chicago."""
    start = combine_chicago(d, DAY_OPEN)
    end = combine_chicago(d, DAY_CLOSE)
    return start, end


def overnight_session_bounds(trading_day: date) -> tuple[datetime, datetime]:
    """Overnight before trading_day: [(d-1) 17:00, d 08:30)."""
    prev = trading_day - timedelta(days=1)
    start = combine_chicago(prev, ON_OPEN)
    end = combine_chicago(trading_day, DAY_OPEN)
    return start, end


def ib_session_bounds(d: date) -> tuple[datetime, datetime]:
    """Initial balance [08:30, 09:30) on date d."""
    start = combine_chicago(d, DAY_OPEN)
    end = combine_chicago(d, IB_END)
    return start, end


def as_chicago_ts(ts: datetime) -> datetime:
    """Attach Chicago if naive; otherwise convert to Chicago."""
    if ts.tzinfo is None:
        return ts.replace(tzinfo=CHICAGO)
    return ts.astimezone(CHICAGO)


def overnight_trading_day(ts: datetime) -> Optional[date]:
    """
    If ts falls in overnight window for some trading day d, return d.
    Otherwise None.
    """
    ts = as_chicago_ts(ts)
    d = ts.date()
    t0 = ts.time()
    if t0 >= ON_OPEN:
        return d + timedelta(days=1)
    if t0 < DAY_OPEN:
        return d
    return None


def day_trading_day(ts: datetime) -> Optional[date]:
    """If ts is in day session on date d, return d; else None."""
    ts = as_chicago_ts(ts)
    d = ts.date()
    t0 = ts.time()
    if DAY_OPEN <= t0 < DAY_CLOSE:
        return d
    return None
