"""DuckDB vs Polars on three queries over 1/3/7 days. Each run is a fresh subprocess; peak RSS sampled.
Spark is intentionally NOT included (see AGENTS.md)."""
from __future__ import annotations

import csv
import json
import os
import statistics
import subprocess
import sys
import time

import psutil

from .bench_worker import QUERIES


def _run(cfg, engine, qname, ndays):
    env = dict(os.environ, GHCP_BASE=str(cfg.base), GHCP_DAYS=",".join(cfg.days))
    p = psutil.Popen([sys.executable, "-m", "ghcp.bench_worker", engine, qname, str(ndays)],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    peak, t0 = 0.0, time.time()
    while p.poll() is None:
        try:
            rss = p.memory_info().rss
            for ch in p.children(recursive=True):
                rss += ch.memory_info().rss
            peak = max(peak, rss / 2**20)
        except psutil.Error:
            pass
        time.sleep(0.05)
    out, err = p.communicate()
    if p.returncode != 0:
        return dict(error=(err or "").strip()[-400:])
    r = json.loads(out.strip().splitlines()[-1])
    r.update(wall_seconds=round(time.time() - t0, 3), peak_rss_mb=round(peak, 1))
    return r


def run_benchmark(cfg, ndays_list=(1, 3, 7), repeats=3, log=print):
    rows, usable = [], [n for n in ndays_list if n <= len(cfg.days)]
    for qname in QUERIES:
        for n in usable:
            checks = {}
            for engine in ("duckdb", "polars"):
                runs = []
                for _ in range(repeats):
                    r = _run(cfg, engine, qname, n)
                    if "error" in r:
                        log(f"  {engine}/{qname}/{n}d ERROR: {r['error']}")
                        runs = []
                        rows.append(dict(query=qname, days=n, engine=engine, error=r["error"]))
                        break
                    runs.append(r)
                if not runs:
                    continue
                checks[engine] = (runs[0]["rows"], runs[0]["checksum"])
                rows.append(dict(
                    query=qname, days=n, engine=engine, files=runs[0]["files"],
                    median_wall_s=round(statistics.median(x["wall_seconds"] for x in runs), 3),
                    min_wall_s=min(x["wall_seconds"] for x in runs),
                    max_peak_rss_mb=max(x["peak_rss_mb"] for x in runs),
                    rows=runs[0]["rows"], checksum=runs[0]["checksum"], error=""))
                log(f"  {qname} {n}d {engine}: median {rows[-1]['median_wall_s']}s, peak {rows[-1]['max_peak_rss_mb']} MB")
            if len(checks) == 2 and checks["duckdb"] != checks["polars"]:
                log(f"  WARNING engines disagree on {qname}/{n}d: {checks}")
                rows.append(dict(query=qname, days=n, engine="MISMATCH", error=str(checks)))
    out = cfg.outputs / "benchmark.csv"
    fields = ["query", "days", "engine", "files", "median_wall_s", "min_wall_s",
              "max_peak_rss_mb", "rows", "checksum", "error"]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    return rows
