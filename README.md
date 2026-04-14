# ES Futures — session analysis

Python tools for analyzing Investor/RT-style ES (`@ES#`) tick files: Chicago overnight (17:00–08:30) and day (08:30–16:00) sessions, ONH/ONL/ONMID, overnight and day VPOC, Initial Balance (08:30–09:30), open classification vs prior day, and conditional hit probabilities.

## Published report

A formatted, human-readable summary of the latest full-history run is checked into the repo root:

- **[ES_Conditional_Probabilities_Report.md](ES_Conditional_Probabilities_Report.md)** — reference-level hit probabilities by open bucket (HIR / LIR / HOR / LOR), post-IB extension probabilities, and gap-fill probabilities by gap size, over **5,308 trading days (2005-09-07 → 2026-04-10)**.

This report is provided **with no warranties of any kind**. See the disclaimer at the bottom of this README and inside the report itself.

## Data layout

**You are responsible for placing your tick export on disk.** The examples below assume a folder named `Historical_Data` at the repo root and a file such as `@ES#_Ticks.txt`. Create `Historical_Data` if it does not exist and copy your tab-separated tick file there (or pass any other path to `--input` / `-i`).

Expected columns: `SYMBOL`, `DATE`, `PRICE`, `TICKVOL`, `BID`, `ASK`.

## Setup

```bash
pip install -r requirements.txt
```

## Scripts

| Module | Purpose |
|--------|---------|
| `python -m analysis.run` | Process the **entire** tick file (full history). |
| `python -m analysis.run_sample` | Process only the **first N calendar days** from the first valid tick, then stop (faster for large files). |

### `analysis.run` (full file)

| Option | Default | Description |
|--------|---------|-------------|
| `--input` / `-i` | (required) | Path to the tick file. |
| `--output-dir` / `-o` | `output` | Directory for CSV and Markdown outputs. |
| `--chunksize` | `1000000` | Rows per read chunk; increase if you have RAM and want less overhead. |
| `--verbose` / `-v` | off | Print progress every 20 chunks and total tick-ingest time. |

Example (paths under `Historical_Data`):

```bash
python -m analysis.run --input Historical_Data/@ES#_Ticks.txt --output-dir output
python -m analysis.run -i Historical_Data/@ES#_Ticks.txt -o output -v
```

**Outputs** (under the chosen output directory):

- `daily_metrics.csv`
- `conditional_probabilities.csv`
- `conditional_probabilities_post_ib.csv`
- `conditional_probabilities_gap_fill.csv`
- `conditional_probabilities.md`

### `analysis.run_sample` (first N calendar days)

| Option | Default | Description |
|--------|---------|-------------|
| `--input` / `-i` | (required) | Path to the tick file. |
| `--output-dir` / `-o` | `output_sample` | Directory for outputs. |
| `--days` / `-d` | `60` | Number of calendar days from the **first valid tick** (inclusive window). |
| `--chunksize` | `1000000` | Rows per read chunk. |
| `--verbose` / `-v` | off | Print chunk progress and ingest time. |

Example:

```bash
python -m analysis.run_sample --input Historical_Data/@ES#_Ticks.txt --output-dir output_sample --days 360
```

On completion, the sample run also prints the resolved anchor and last-inclusive dates. Same output filenames as the full run.

## Cursor skills

- Full definitions: [`.cursor/skills/es-session-analysis/SKILL.md`](.cursor/skills/es-session-analysis/SKILL.md)
- Sample window: [`.cursor/skills/es-session-analysis-sample/SKILL.md`](.cursor/skills/es-session-analysis-sample/SKILL.md)

## Tests

```bash
python -m pytest tests/ -v
```

## ⚠ Disclaimer

**The code, data, and reports in this repository — including [ES_Conditional_Probabilities_Report.md](ES_Conditional_Probabilities_Report.md) — are provided for educational and informational purposes only. They are not investment advice, a solicitation, or a recommendation to buy, sell, or hold any security, futures contract, or other financial instrument.**

- Past statistical behavior does **not** predict future results. Probabilities reported here are historical frequencies observed in a specific dataset over a specific window; market structure, liquidity, session hours, and contract specifications can and do change.
- Futures trading involves **substantial risk of loss** and is not suitable for all investors. You can lose more than your initial deposit.
- Outputs are derived from a single tick source (`@ES#` continuous contract) and have **not been independently audited**. Data errors, missed ticks, session-boundary edge cases, contract rolls, and holiday/half-session handling may materially affect the numbers.
- No backtest, commission, slippage, margin, or execution-cost model is applied. Live trading results will differ from any naive strategy implied by these probabilities.
- The author makes **no representation or warranty**, express or implied, regarding the accuracy, completeness, or fitness for any particular purpose of this software or its outputs. Use at your own risk.

**Consult a licensed financial professional before making any trading decision.**

## License

MIT License

Copyright (c) 2026 Tony Ku

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
