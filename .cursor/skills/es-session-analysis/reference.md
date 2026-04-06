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

## VPOC algorithm

1. Map each tick with `TICKVOL > 0` to bucket `b = round(price * 4) / 4`.
2. `vol[b] += TICKVOL`.
3. POC = argmax `vol`; if multiple buckets tie, `POC = (min(tied_prices) + max(tied_prices)) / 2`.

If no volume in session, VPOC is undefined (`None`); such days may be excluded from probability denominators for that level or counted as no-hit depending on implementation (see code: undefined VPOC → hit not counted / NaN).

## Reference levels in conditional probabilities

Levels (export `level` column): `ON_VPOC`, `yDay_VPOC`, `ONL`, `ONMID`, `ONH`, `yDay_High`, `yDay_Low`. **ONMID** is the overnight midpoint `(ONH + ONL) / 2`; a hit means today’s day session range brackets that price.

## Conditional probability

For bucket `B` in {`inside_gap_up`, `inside_gap_down`, `above_prior_range`, `below_prior_range`} and level `L`:

```
P(hit L | B) = count(days with bucket B and hit L) / count(days with bucket B)
```

Boundary days (open equals prior close or exactly prior high/low in a way that violates strict buckets) are excluded from the four open-bucket denominators.
