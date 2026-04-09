"""CLI: run session analysis on the first N calendar days from the first tick (sample window)."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import probabilities_combined_markdown, run_pipeline


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "ES Overnight/Day session analysis on a calendar-day window from the "
            "first tick (Chicago). Stops reading the file after the window ends."
        )
    )
    p.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to tab-separated tick file (SYMBOL, DATE, PRICE, TICKVOL, BID, ASK).",
    )
    p.add_argument(
        "--output-dir",
        "-o",
        default="output_sample",
        help="Directory for daily_metrics.csv, conditional_probabilities*.csv, conditional_probabilities_gap_fill.csv, conditional_probabilities.md",
    )
    p.add_argument(
        "--days",
        "-d",
        type=int,
        default=60,
        help="Number of calendar days from first valid tick (default 60).",
    )
    p.add_argument(
        "--chunksize",
        type=int,
        default=1_000_000,
        help="Rows per pandas chunk (default 1000000). Larger can be faster if RAM allows.",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print chunk progress and tick-ingest wall time.",
    )
    args = p.parse_args()

    inp = Path(args.input)
    if not inp.is_file():
        raise SystemExit(f"Input not found: {inp}")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    daily_df, prob_df, prob_post_ib_df, prob_gap_fill_df, meta = run_pipeline(
        str(inp),
        chunksize=args.chunksize,
        max_calendar_days=args.days,
        verbose=args.verbose,
    )

    daily_path = out / "daily_metrics.csv"
    prob_path = out / "conditional_probabilities.csv"
    prob_post_path = out / "conditional_probabilities_post_ib.csv"
    prob_gap_path = out / "conditional_probabilities_gap_fill.csv"
    md_path = out / "conditional_probabilities.md"

    daily_df.to_csv(daily_path, index=False)
    prob_df.to_csv(prob_path, index=False)
    prob_post_ib_df.to_csv(prob_post_path, index=False)
    prob_gap_fill_df.to_csv(prob_gap_path, index=False)
    md_path.write_text(
        probabilities_combined_markdown(prob_df, prob_post_ib_df, prob_gap_fill_df),
        encoding="utf-8",
    )

    print(f"Wrote {daily_path} ({len(daily_df)} rows)")
    print(f"Wrote {prob_path}")
    print(f"Wrote {prob_post_path}")
    print(f"Wrote {prob_gap_path}")
    print(f"Wrote {md_path}")
    if meta:
        print(
            f"Sample window: anchor={meta.get('anchor_date')} "
            f"through {meta.get('last_inclusive_date')} "
            f"({meta.get('max_calendar_days')} calendar days from first tick)"
        )


if __name__ == "__main__":
    main()
