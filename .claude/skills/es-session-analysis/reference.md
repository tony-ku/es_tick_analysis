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

```
PostIB(d) = [ datetime(d, 09:30), datetime(d, 16:00) )
```

Half-open: 09:30 inclusive (first tick at or after IB end), 16:00 exclusive.

## Post-IB exceed levels (conditional stats)

Let `w = IBH − IBL` (IB width). For bucket `B` in the four open buckets:

- **`post-IB high > IBH`**: fraction of days in `B` where **post-IB high** > **IBH** (among days with both IB and post-IB data).
- **`post-IB low < IBL`**: **post-IB low** < **IBL**.
- **`post-IB high > IBH + 1.5*(IBH-IBL)`**: **post-IB high** > `IBH + 1.5 × w` (only if `w > 0`). This is **1.5× the IB range**, not 1.5× the IBH price.
- **`post-IB low < IBL - 1.5*(IBH-IBL)`**: **post-IB low** < `IBL − 1.5 × w` (only if `w > 0`).

Same **`probability_pct`** (0–100) export as reference conditional probabilities; undefined flags excluded from denominators.

## VPOC algorithm

1. Map each tick with `TICKVOL > 0` to bucket `b = round(price * 4) / 4`.
2. `vol[b] += TICKVOL`.
3. POC = argmax `vol`; if multiple buckets tie, `POC = (min(tied_prices) + max(tied_prices)) / 2`.

If no volume in session, VPOC is undefined (`None`); such days may be excluded from probability denominators for that level or counted as no-hit depending on implementation (see code: undefined VPOC → hit not counted / NaN).

## Value Area algorithm (Steidlmayer 70%)

Starting from the volume profile `vol[b]` and total day volume `V`:

1. **Seed** VA at the POC bucket. If multiple buckets tie for POC, choose the **upper** tied bucket as the seed.
2. Let `va_hi` and `va_lo` be the current top and bottom buckets in the VA; initially both equal the seed.
3. Compute:
   - `up_sum = vol[va_hi + 0.25] + vol[va_hi + 0.50]`
   - `dn_sum = vol[va_lo − 0.25] + vol[va_lo − 0.50]`
4. Extend:
   - If `up_sum >= dn_sum`: `va_hi += 0.50`, add `up_sum` to VA volume. **Upper wins on tie.**
   - Else: `va_lo -= 0.50`, add `dn_sum` to VA volume.
   - If one side has no remaining volume buckets, extend the other.
5. Stop when VA volume ≥ `0.70 × V`. Then **VAH = va_hi**, **VAL = va_lo**.

Prior day VAH/VAL (`pVAH`, `pVAL`) are this algorithm applied to the **previous trading day's Day session** volume profile.

## Reference levels in conditional probabilities

Levels (export `level` column): `ON_VPOC`, `yDay_VPOC`, `ONL`, `ONMID`, `ONH`, `ONH_or_ONL`, `yDay_High`, `yDay_Low`, `pVAH`, `pVAL`.

- **ONMID** is the overnight midpoint `(ONH + ONL) / 2`; a hit means today's day session range brackets that price.
- **ONH_or_ONL** is a composite: hit if either ONH or ONL is hit today.
- **pVAH / pVAL** are prior day's 70% VA bounds.

## Conditional probability

For bucket `B` in {`HIR`, `LIR`, `HOR`, `LOR`} and level `L`:

```
P(hit L | B) = count(days with bucket B and hit L) / count(days with bucket B and level L defined)
```

Exports use **`probability_pct`**: 0–100. Boundary days (open exactly on prior close / prior high / prior low in a way that violates strict buckets) are excluded from the four open-bucket denominators.
