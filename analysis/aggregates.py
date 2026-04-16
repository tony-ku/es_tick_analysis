"""Session aggregates and VPOC."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple

from .sessions import as_chicago_ts, ib_session_bounds, price_bucket

ES_TICK = 0.25


def vpoc_from_bins(vol_bins: Dict[float, float]) -> Optional[float]:
    """POC price; ties → midpoint of min and max tied bucket prices.

    Tolerance-based tie detection: float sums accumulated in different
    orders can differ by a few ULPs, so exact `==` would silently break
    true ties. 1e-9 relative tolerance is far below any meaningful
    volume difference.
    """
    if not vol_bins:
        return None
    mx = max(vol_bins.values())
    if mx <= 0:
        return None
    tied = [p for p, v in vol_bins.items() if math.isclose(v, mx, rel_tol=1e-9, abs_tol=0.0)]
    if len(tied) == 1:
        return tied[0]
    return (min(tied) + max(tied)) / 2.0


def value_area_from_bins(
    vol_bins: Dict[float, float],
    target_pct: float = 0.70,
) -> Tuple[Optional[float], Optional[float]]:
    """Steidlmayer 70% value area over 0.25 price buckets.

    Seed at POC (upper bucket on POC tie). Each step, compare volume of the
    two buckets immediately above the developing VA to the two immediately
    below; add the larger pair. Tie → extend upward. When one side has no
    buckets left with volume, extend the other. Stop when VA volume ≥ 70%
    of day total. Returns (VAH, VAL).
    """
    if not vol_bins:
        return (None, None)
    total = sum(vol_bins.values())
    if total <= 0:
        return (None, None)
    target = total * target_pct

    mx = max(vol_bins.values())
    tied = sorted(
        p for p, v in vol_bins.items()
        if math.isclose(v, mx, rel_tol=1e-9, abs_tol=0.0)
    )
    poc = tied[-1]  # upper bucket on POC tie

    hi_px = max(vol_bins.keys())
    lo_px = min(vol_bins.keys())
    va_hi = va_lo = poc
    va_vol = vol_bins[poc]

    def vol_at(p: float) -> float:
        return vol_bins.get(price_bucket(p), 0.0)

    while va_vol < target:
        up_exhausted = va_hi >= hi_px
        dn_exhausted = va_lo <= lo_px
        if up_exhausted and dn_exhausted:
            break

        up_sum = vol_at(va_hi + ES_TICK) + vol_at(va_hi + 2 * ES_TICK)
        dn_sum = vol_at(va_lo - ES_TICK) + vol_at(va_lo - 2 * ES_TICK)

        if up_exhausted:
            va_lo -= 2 * ES_TICK
            va_vol += dn_sum
        elif dn_exhausted:
            va_hi += 2 * ES_TICK
            va_vol += up_sum
        elif up_sum >= dn_sum:  # upper on tie
            va_hi += 2 * ES_TICK
            va_vol += up_sum
        else:
            va_lo -= 2 * ES_TICK
            va_vol += dn_sum

    return (va_hi, va_lo)


@dataclass
class OvernightAgg:
    min_p: float = float("inf")
    max_p: float = float("-inf")
    vol_bins: Dict[float, float] = field(default_factory=lambda: defaultdict(float))

    def add(self, price: float, tickvol: float) -> None:
        self.min_p = min(self.min_p, price)
        self.max_p = max(self.max_p, price)
        if tickvol > 0:
            b = price_bucket(price)
            self.vol_bins[b] += tickvol

    def bulk_merge(self, min_p: float, max_p: float, vol_bins_chunk: Dict[float, float]) -> None:
        """Merge vectorized chunk results into this aggregate."""
        self.min_p = min(self.min_p, min_p)
        self.max_p = max(self.max_p, max_p)
        for bucket, vol in vol_bins_chunk.items():
            self.vol_bins[bucket] += vol

    def onh(self) -> Optional[float]:
        return None if self.min_p == float("inf") else self.max_p

    def onl(self) -> Optional[float]:
        return None if self.min_p == float("inf") else self.min_p

    def onmid(self) -> Optional[float]:
        h, lo = self.onh(), self.onl()
        if h is None or lo is None:
            return None
        return (h + lo) / 2.0

    def on_vpoc(self) -> Optional[float]:
        return vpoc_from_bins(dict(self.vol_bins))


@dataclass
class DaySessionAgg:
    min_p: float = float("inf")
    max_p: float = float("-inf")
    vol_bins: Dict[float, float] = field(default_factory=lambda: defaultdict(float))
    first_ts: Optional[datetime] = None
    first_price: Optional[float] = None
    last_ts: Optional[datetime] = None
    last_price: Optional[float] = None
    ib_min: float = float("inf")
    ib_max: float = float("-inf")
    post_ib_min: float = float("inf")
    post_ib_max: float = float("-inf")

    def add(self, ts: datetime, price: float, tickvol: float) -> None:
        ts = as_chicago_ts(ts)
        self.min_p = min(self.min_p, price)
        self.max_p = max(self.max_p, price)
        if tickvol > 0:
            b = price_bucket(price)
            self.vol_bins[b] += tickvol

        if self.first_ts is None or ts < self.first_ts:
            self.first_ts = ts
            self.first_price = price

        if self.last_ts is None or ts >= self.last_ts:
            self.last_ts = ts
            self.last_price = price

        d = ts.date()
        ib_lo, ib_hi = ib_session_bounds(d)
        if ib_lo <= ts < ib_hi:
            self.ib_min = min(self.ib_min, price)
            self.ib_max = max(self.ib_max, price)
        if ts >= ib_hi:
            self.post_ib_min = min(self.post_ib_min, price)
            self.post_ib_max = max(self.post_ib_max, price)

    def bulk_merge(
        self,
        min_p: float,
        max_p: float,
        vol_bins_chunk: Dict[float, float],
        first_ts: datetime,
        first_price: float,
        last_ts: datetime,
        last_price: float,
        ib_min: float,
        ib_max: float,
        post_ib_min: float,
        post_ib_max: float,
    ) -> None:
        """Merge vectorized chunk results into this aggregate."""
        self.min_p = min(self.min_p, min_p)
        self.max_p = max(self.max_p, max_p)
        for bucket, vol in vol_bins_chunk.items():
            self.vol_bins[bucket] += vol
        if self.first_ts is None or first_ts < self.first_ts:
            self.first_ts = first_ts
            self.first_price = first_price
        if self.last_ts is None or last_ts >= self.last_ts:
            self.last_ts = last_ts
            self.last_price = last_price
        self.ib_min = min(self.ib_min, ib_min)
        self.ib_max = max(self.ib_max, ib_max)
        self.post_ib_min = min(self.post_ib_min, post_ib_min)
        self.post_ib_max = max(self.post_ib_max, post_ib_max)

    def day_vpoc(self) -> Optional[float]:
        return vpoc_from_bins(dict(self.vol_bins))

    def day_value_area(self) -> Tuple[Optional[float], Optional[float]]:
        return value_area_from_bins(dict(self.vol_bins))

    def ibh(self) -> Optional[float]:
        if self.ib_min == float("inf"):
            return None
        return self.ib_max

    def ibl(self) -> Optional[float]:
        if self.ib_min == float("inf"):
            return None
        return self.ib_min

    def post_ib_high(self) -> Optional[float]:
        if self.post_ib_max == float("-inf"):
            return None
        return self.post_ib_max

    def post_ib_low(self) -> Optional[float]:
        if self.post_ib_min == float("inf"):
            return None
        return self.post_ib_min

