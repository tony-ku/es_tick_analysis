"""CLI for ES session analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import probabilities_to_markdown, run_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="ES Overnight/Day session analysis (Chicago).")
    p.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to tab-separated tick file (SYMBOL, DATE, PRICE, TICKVOL, BID, ASK).",
    )
    p.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Directory for daily_metrics.csv, conditional_probabilities.csv, .md",
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

    daily_df, prob_df, _meta = run_pipeline(
        str(inp),
        chunksize=args.chunksize,
        verbose=args.verbose,
    )

    daily_path = out / "daily_metrics.csv"
    prob_path = out / "conditional_probabilities.csv"
    md_path = out / "conditional_probabilities.md"

    daily_df.to_csv(daily_path, index=False)
    prob_df.to_csv(prob_path, index=False)
    md_path.write_text(probabilities_to_markdown(prob_df), encoding="utf-8")

    print(f"Wrote {daily_path} ({len(daily_df)} rows)")
    print(f"Wrote {prob_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
