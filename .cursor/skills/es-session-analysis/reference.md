# ES Session Analysis — Reference

## Overnight window math

For trading day `d` (the date of the 08:30 open):

```
ON(d) = [ datetime(d-1, 17:00), datetime(d, 08:30) )
```

Half-open interval: 17:00 inclusive, 08:30 exclusive (08:30 belongs to Day session).

## Day session

```
Day(d) = [ datetime(d, 08:30), datetime(d, 16:00) )
```

## Initial Balance

```
IB(d) = [ datetime(d, 08:30), datetime(d, 09:30) )
```

## Post-IB window (same trading day)

After IB ends, the rest of the day session:

```
PostIB(d) = [ datetime(d, 09:30), datetime(d, 16:00) )
```

Half-open: 09:30 inclusive (first tick at or after IB end), 16:00 exclusive.

## Post-IB exceed levels (conditional stats)

Let `w = IBH − IBL` (IB width). For bucket `B` in the four open buckets:

- **`post-IB high > IBH`**: fraction of days in `B` where **post-IB high** &gt; **IBH** (among days with both IB and post-IB data).
- **`post-IB low < IBL`**: **post-IB low** &lt; **IBL**.
- **`post-IB high > IBH + 1.5*(IBH-IBL)`**: **post-IB high** &gt; `IBH + 1.5 × w` (only if `w > 0`). This is **1.5× the IB range**, not 1.5× the IBH price.
- **`post-IB low < IBL - 1.5*(IBH-IBL)`**: **post-IB low** &lt; `IBL − 1.5 × w` (only if `w > 0`).

Same **`probability_pct`** (0–100) export as reference conditional probabilities; undefined flags excluded from denominators.

## VPOC algorithm

1. Map each tick with `TICKVOL > 0` to bucket `b = round(price * 4) / 4`.
2. `vol[b] += TICKVOL`.
3. POC = argmax `vol`; if multiple buckets tie, `POC = (min(tied_prices) + max(tied_prices)) / 2`.

If no volume in session, VPOC is undefined (`None`); such days may be excluded from probability denominators for that level or counted as no-hit depending on implementation (see code: undefined VPOC → hit not counted / NaN).

## Reference levels in conditional probabilities

Levels (export `level` column): `ONPOC`, `pPOC`, `ONL`, `ONMID`, `ONH`, `pHigh`, `pLow`. **ONMID** is the overnight midpoint `(ONH + ONL) / 2`; a hit means today’s day session range brackets that price.

## Conditional probability

For bucket `B` in {`HIR`, `LIR`, `HOR`, `LOR`} and level `L`:

```
P(hit L | B) = count(days with bucket B and hit L) / count(days with bucket B)
```

Exports use **`probability_pct`**: the same ratio as a percentage in **0–100** (CSV column; Markdown tables show a `% hit` column with a `%` suffix).

Boundary days (open equals prior close or exactly prior high/low in a way that violates strict buckets) are excluded from the four open-bucket denominators.
