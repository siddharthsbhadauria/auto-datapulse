# auto-datapulse

[![CI](https://github.com/siddharthsbhadauria/auto-datapulse/actions/workflows/ci.yml/badge.svg)](https://github.com/siddharthsbhadauria/auto-datapulse/actions/workflows/ci.yml)

Telemetry collection for my home NAS (UGREEN DXP4800, 32 GB). Every 15 minutes it reads the host's CPU, memory, disk usage and disk I/O, checks the reading against a data contract and appends it to DuckDB. Once a day it commits a short Markdown report to `REPORTS/`.

[homelab-mlops](https://github.com/siddharthsbhadauria/homelab-mlops) reads the same DuckDB file to train anomaly detection models.

## How it works

```
psutil reading every 15 min              src/collector.py
  -> data contract                       src/quality_contracts.py
  -> DuckDB table telemetry_snapshots    main.py  (data/telemetry.duckdb, plus a JSONL backup)
  -> daily report via the GitHub API     src/git_publisher.py
  -> dbt models                          dbt_telemetry/
```

- **Data contract:** plain Python. A reading is rejected if the system block is missing or CPU, memory or disk usage falls outside 0 to 100%. Rejected readings are never stored.
- **No placeholder data:** if psutil can't read the host, the collector raises an error instead of writing made-up numbers.
- **dbt models:** `stg_telemetry` (typed view over the raw table) and `fct_daily_disk_wear` (daily averages and peaks with a simple health tier), with not-null and uniqueness tests. CI builds them on every change against a fresh snapshot. They aren't scheduled on the NAS yet; run `dbt build` by hand to refresh them.

## Deploy on the NAS (Portainer)

1. In Portainer, go to **Stacks** > **Add stack** and choose **Repository**.
2. Repository URL `https://github.com/siddharthsbhadauria/auto-datapulse.git`, reference `refs/heads/main`, compose path `docker-compose.yml`.
3. Add environment variables:
   - `GITHUB_TOKEN`: a token with contents write access to this repo, for the daily report
   - `DATA_PATH`: for example `/volume2/docker/auto-datapulse/data`
   - `REPORTS_PATH`: for example `/volume2/docker/auto-datapulse/REPORTS`
4. Deploy. The container runs the 15-minute loop until stopped.

Or over SSH:

```bash
git clone https://github.com/siddharthsbhadauria/auto-datapulse.git
cd auto-datapulse
printf "GITHUB_TOKEN=...\nDATA_PATH=/volume2/docker/auto-datapulse/data\nREPORTS_PATH=/volume2/docker/auto-datapulse/REPORTS\n" > .env
docker compose up -d --build
```

## Develop

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
pytest -q
GITHUB_TOKEN= python main.py --once      # one reading, no report push
cd dbt_telemetry && dbt build --profiles-dir .
```

Unset `GITHUB_TOKEN` when running locally, or `main.py` will push your machine's metrics as today's report.

## License

MIT
