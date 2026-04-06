# ES Futures — session analysis

Python tools for analyzing Investor/RT-style ES (`@ES#`) tick files: Chicago overnight (17:00–08:30) and day (08:30–16:00) sessions, ONH/ONL/ONMID, overnight and day VPOC, Initial Balance (08:30–09:30), open classification vs prior day, and conditional hit probabilities.

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

On completion, the sample run also prints the resolved anchor and last-inclusive dates. Same three output filenames as the full run.

## Cursor skills

- Full definitions: [`.cursor/skills/es-session-analysis/SKILL.md`](.cursor/skills/es-session-analysis/SKILL.md)
- Sample window: [`.cursor/skills/es-session-analysis-sample/SKILL.md`](.cursor/skills/es-session-analysis-sample/SKILL.md)

## Tests

```bash
python -m pytest tests/ -v
```
