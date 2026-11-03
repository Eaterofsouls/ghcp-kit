# PLAN — execute in order; stop at every gate and report using the format in AGENTS.md

Run all commands from the kit root (`D:\ghcp-kit`) in PowerShell with the venv active and
`$env:GHCP_BASE = "D:\ghcp\data"`.

## S0 — Environment and hardware gate
Do:
```powershell
python --version                                   # need >= 3.10
python -m venv D:\ghcp\venv ; D:\ghcp\venv\Scripts\Activate.ps1
$env:PIP_CACHE_DIR = "D:\ghcp\pip-cache" ; $env:GHCP_BASE = "D:\ghcp\data" ; $env:TMP = "D:\ghcp\tmp" ; $env:TEMP = "D:\ghcp\tmp"
mkdir D:\ghcp\tmp -Force ; pip install -r requirements.txt
python -c "import duckdb,polars,psutil,matplotlib;print(duckdb.__version__,polars.__version__)"
python -c "import psutil;v=psutil.virtual_memory();d=psutil.disk_usage('D:\\');print('avail MB',v.available//2**20,'total MB',v.total//2**20,'D: free GB',d.free//2**30)"
```
Done when: imports print versions; D: free ≥ 25 GB. **If available RAM < 1500 MB**, ask the user to close
heavy apps (browsers/IDEs/VMs) and re-check; do not lower guard thresholds.

## S1 — Self-test (fake fixture; proves the code before real data)
`python -m ghcp selftest`
Done when: last line `SELFTEST: N/N passed`. On failure: read the failing check, fix **only** the
failing SQL/Python (surgical), log in CHANGELOG_AGENT.md, re-run. Most likely failure points are DuckDB
SQL dialect details in `sql/ingest_shard.sql` and `sql/analysis/*.sql` (never tested against DuckDB by the author).
If you change any SQL, say which statement and why.

## S2 — Download the smallest day, then probe the real schema
```powershell
python -m ghcp download --days 2026-06-06
python -m ghcp probe --days 2026-06-06
```
Done when: size equals 124,247,983 bytes; probe prints empty `missing_paths`, `extra_paths`, `types`.
Paste: `manifest.json (raw)`, `numeric_ranges` (esp. `cached_pct` — is it 0–1 or 0–100?), `timestamp_samples`,
`max_line_chars` (must be < 134,217,728, the `maximum_object_size` in the ingest SQL).
**GATE:** if the probe disagrees with the schema, STOP and show the user before editing SQL.

## S3 — Pilot ingest of 2026-06-06 and resource projection
```powershell
python -m ghcp ingest --days 2026-06-06
python -m ghcp status
Get-Content D:\ghcp\data\logs\guard_summary_ingest.json
```
Compute and report:
`parquet_ratio = size(parquet\) / 124,247,983`; `projected_total_GB = 3.22 + 3.22*parquet_ratio + 4.0` (raw + parquet + spill cap).
Done when: no FAIL, peak RSS ≤ 1500 MB, projected_total_GB ≤ 15, and seconds-per-MB gives a projected full runtime.
**GATE:** if projected disk > 15 GB or peak RSS > 1500 MB, STOP and report; do not raise limits.
Then test resume: run `python -m ghcp ingest --days 2026-06-06` again — it must finish instantly with zero shards re-ingested.

## S4 — Download remaining archives
`python -m ghcp download` (resumable; re-run after any interruption).
Done when: all 7 files match sizes in `ghcp/config.py` and `state` shows `complete` for each.

## S5 — Full ingest (checkpointed)
`python -m ghcp ingest` — re-run the same command after any stop/crash; it resumes.
Done when: exit code 0 and `python -m ghcp status` shows all days with shard counts equal to the shards in each archive.
If exit code 3: read `logs\STOP_REASON.txt`, report, wait.

## S6 — Validation
`python -m ghcp validate`
Done when: prints `FAIL checks: 0`. Paste the table of every check, **including the anomaly lines**
(negative latencies, cross-turn %, out-of-window timestamps, cached_pct range, timestamp probes) and say
whether each matches the team audit (4 negatives; 0.98% cross-turn). Nothing is removed. Any FAIL → STOP and report.

## S7 — Analytics
`python -m ghcp analyze`
Done when: every chunk logged without error and `analysis_timings.csv` exists. On an SQL error fix only that
statement (surgical), log it, re-run `python -m ghcp analyze --only <file prefix>`.
If memory-stopped, report which step; do not raise limits.

## S8 — Benchmark
`python -m ghcp benchmark`
Done when: `outputs\benchmark.csv` has rows for both engines for q1–q3 × 1/3/7 days, with no `MISMATCH`.
Report the table as measured. Do not editorialise or tune either engine.

## S9 — Figures, report, bundle
```powershell
python -m ghcp plots ; python -m ghcp report ; python -m ghcp bundle
```
Done when: `figures\*.png` (≥6), `reports\seven_day_metrics.md`, `D:\ghcp\data\outputs_bundle.zip` exist.

## S10 — Handoff
Give the user: path of `outputs_bundle.zip` (small; to send to Claude for review), the five numbers they
will want first (corpus counts vs published, peak RSS, peak disk, total ingest time, number of FAIL checks),
the contents of CHANGELOG_AGENT.md, and an explicit list of anything not done or not verified.
