# Jinu CA2: NHS A&E live waiting-times collector

Part of B9AI001 Programming for Data Analysis CA2 (DBS, MSc AI).

**Question:** two hours from now, will this emergency department's wait be over 240 minutes?

## What is collected
- `collectors/nhs_collect.py`: one snapshot of the live A&E feed (`https://live.checkwaitingtimes.co.uk/ae.json`) per run. Each site becomes one row in `data/nhs/readings_csv/YYYY-MM-DD.csv` (UTC date). Duplicate readings (same site and `source_as_of`) are skipped. Every run is logged in `logs/nhs_collection_log.csv`.
- `collectors/nhs_history.py`: saves the site's rolling ~30-day hourly history for each source to `data/nhs/history_raw/{source}/YYYY-MM-DD.json`.

## Schedule
- **Collect NHS A&E** (`.github/workflows/collect_nhs.yml`): every 15 minutes.
- **Weekly NHS history** (`.github/workflows/nhs_history.yml`): Sundays 03:00 UTC.

GitHub's built-in cron is often delayed or skipped, so an external scheduler (cron-job.org) also triggers the collector every 15 minutes through the GitHub API `workflow_dispatch` endpoint.

## Run manually
- On GitHub: Actions, then the workflow, then **Run workflow**.
- On Windows: double-click `bats/run_nhs.bat` (needs Python and `pip install -r requirements-collect.txt`).

## Storage
Raw CSV/JSON files are committed here; the analysis notebook rebuilds a SQLite database from them (no `.db` files are committed).

## Data source
Live and historical A&E waiting times from [checkwaitingtimes.co.uk](https://checkwaitingtimes.co.uk), which aggregates published NHS trust feeds. Used for non-commercial student research.
