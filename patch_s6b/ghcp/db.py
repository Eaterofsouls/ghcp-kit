"""DuckDB connection with hard memory/thread/spill limits, plus Parquet views."""
from __future__ import annotations

from pathlib import Path

from .config import TABLES, q


def connect(cfg):
    import duckdb  # lazy: lets non-DuckDB modules import without it

    cfg.duckdb_tmp.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()  # in-memory; nothing persisted except what we COPY out
    con.execute(f"SET memory_limit='{cfg.memory_limit_mb}MB'")
    con.execute(f"SET threads={cfg.threads}")
    con.execute("SET TimeZone='UTC'")  # day/hour bucketing and display must not depend on the OS time zone
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"SET temp_directory='{q(cfg.duckdb_tmp)}'")
    con.execute(f"SET max_temp_directory_size='{cfg.temp_cap_gb}GB'")
    return con


def create_views(con, cfg) -> None:
    """One view per table over all shard files; hive column `archive_date` is the day."""
    for t in TABLES:
        glob = f"{q(cfg.parquet)}/{t}/*/*.parquet"
        con.execute(
            f"CREATE OR REPLACE VIEW {t} AS "
            f"SELECT * FROM read_parquet('{glob}', hive_partitioning=true)"
        )


def load_chunks(path: Path) -> list[tuple[str, str]]:
    """Split a SQL file on lines starting with `-- @@`. Header is e.g. `exec` or `csv:name`."""
    chunks: list[tuple[str, str]] = []
    header, buf = None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- @@"):
            if header is not None and "".join(buf).strip():
                chunks.append((header, "\n".join(buf).strip()))
            header, buf = line[5:].strip(), []
        else:
            buf.append(line)
    if header is not None and "".join(buf).strip():
        chunks.append((header, "\n".join(buf).strip()))
    return chunks
