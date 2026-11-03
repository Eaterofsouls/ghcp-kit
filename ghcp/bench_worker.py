"""Subprocess worker for benchmark.py: one engine x one query x N days. Prints one JSON line."""
from __future__ import annotations

import json
import sys
import time

from .config import Config

QUERIES = {
    # name: (table, duckdb sql over {F}, polars builder name)
    "q1_session_token_rollup": ("llm_calls",
        "SELECT session_id, count(*) AS n, sum(tokens_prompt) AS p, sum(tokens_cached) AS c "
        "FROM read_parquet({F}) GROUP BY session_id"),
    "q2_cache_by_call_position": ("llm_calls",
        "SELECT least(call_idx, 21) AS pos, count(*) AS n, sum(tokens_cached)::DOUBLE / sum(tokens_prompt) AS s "
        "FROM read_parquet({F}) GROUP BY 1"),
    "q3_tool_usage": ("tool_calls",
        "SELECT name, count(*) AS n, count(*) FILTER (WHERE status = 2) AS f, median(duration_ms) AS m "
        "FROM read_parquet({F}) GROUP BY name"),
}


def main() -> None:
    engine, qname, ndays = sys.argv[1], sys.argv[2], int(sys.argv[3])
    cfg = Config.from_env()
    table = QUERIES[qname][0]
    days = cfg.days[:ndays]
    files = [str(p) for d in days
             for p in sorted((cfg.parquet / table / f"archive_date={d}").glob("shard-*.parquet"))]
    t0 = time.time()
    if engine == "duckdb":
        from .db import connect
        con = connect(cfg)
        flist = "[" + ",".join("'" + f.replace("\\", "/").replace("'", "''") + "'" for f in files) + "]"
        rows = con.execute(QUERIES[qname][1].replace("{F}", flist)).fetchall()
        n_rows, checksum = len(rows), int(sum(r[1] for r in rows))
    elif engine == "polars":
        import polars as pl
        lf = pl.scan_parquet(files)
        if qname == "q1_session_token_rollup":
            lf = lf.group_by("session_id").agg(pl.len().alias("n"), pl.col("tokens_prompt").sum(),
                                               pl.col("tokens_cached").sum())
        elif qname == "q2_cache_by_call_position":
            lf = (lf.with_columns(pos=pl.min_horizontal("call_idx", pl.lit(21)))
                    .group_by("pos").agg(pl.len().alias("n"), pl.col("tokens_cached").sum(),
                                         pl.col("tokens_prompt").sum()))
        else:
            lf = lf.group_by("name").agg(pl.len().alias("n"), (pl.col("status") == 2).sum().alias("f"),
                                         pl.col("duration_ms").median())
        try:
            df = lf.collect(engine="streaming")
        except TypeError:
            df = lf.collect(streaming=True)
        n_rows, checksum = df.height, int(df["n"].sum())
    else:
        raise SystemExit("engine must be duckdb|polars")
    print(json.dumps(dict(engine=engine, query=qname, days=ndays, files=len(files),
                          seconds=round(time.time() - t0, 3), rows=n_rows, checksum=checksum)))


if __name__ == "__main__":
    main()
