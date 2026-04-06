"""Session aggregates and VPOC."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from .sessions import as_chicago_ts, ib_session_bounds, price_bucket


def vpoc_from_bins(vol_bins: Dict[float, float]) -> Optional[float]:
    """POC price; ties → midpoint of min and max tied bucket prices."""
    if not vol_bins:
        return None
    mx = max(vol_bins.values())
    if mx <= 0:
        return None
    tied = [p for p, v in vol_bins.items() if v == mx]
    if len(tied) == 1:
        return tied[0]
    return (min(tied) + max(tied)) / 2.0


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

    def day_vpoc(self) -> Optional[float]:
        return vpoc_from_bins(dict(self.vol_bins))

    def ibh(self) -> Optional[float]:
        if self.ib_min == float("inf"):
            return None
        return self.ib_max

    def ibl(self) -> Optional[float]:
        if self.ib_min == float("inf"):
            return None
        return self.ib_min

