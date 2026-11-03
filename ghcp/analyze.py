"""Run sql/analysis/*.sql in order; each `-- @@ csv:name` chunk becomes outputs/name.csv."""
from __future__ import annotations

import csv
import time
from pathlib import Path

from .config import q
from .db import connect, create_views, load_chunks

SQL_DIR = Path(__file__).resolve().parent.parent / "sql" / "analysis"


def run_analysis(cfg, guard=None, only: str | None = None, log=print) -> list[dict]:
    con = connect(cfg)
    if guard:
        guard.register(con)
    create_views(con, cfg)
    cfg.outputs.mkdir(parents=True, exist_ok=True)
    timings = []
    for path in sorted(SQL_DIR.glob("*.sql")):
        if only and only not in path.name:
            continue
        for header, sql in load_chunks(path):
            if guard and guard.should_stop:
                log(f"stopping before {path.name}: {guard.reason}")
                return timings
            t0 = time.time()
            body = sql.rstrip().rstrip(";")
            if header.startswith("csv:"):
                name = header[4:].strip()
                out = cfg.outputs / f"{name}.csv"
                con.execute(f"COPY ({body}) TO '{q(out)}' (HEADER, DELIMITER ',')")
            else:
                name = header.replace("exec", "").strip() or path.stem
                con.execute(body)
            dt = round(time.time() - t0, 2)
            peak = round(guard.peak_rss_mb, 1) if guard else None
            timings.append(dict(file=path.name, step=name, seconds=dt, peak_rss_mb_so_far=peak))
            log(f"  {path.name} :: {name} ({dt}s)")
    with open(cfg.outputs / "analysis_timings.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "step", "seconds", "peak_rss_mb_so_far"])
        w.writeheader()
        w.writerows(timings)
    con.close()
    return timings
