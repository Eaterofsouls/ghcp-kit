"""Stream each daily tar.gz, ingest it shard by shard into per-shard Parquet. Resumable."""
from __future__ import annotations

import os
import posixpath
import re
import shutil
import tarfile
import time
from pathlib import Path

from .config import TABLES, q
from .db import load_chunks

SHARD_RE = re.compile(r"shard-(\d+)\.jsonl\.gz$")
SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "ingest_shard.sql"
COUNT_SQL = (
    "SELECT (SELECT count(*) FROM _raw), (SELECT count(*) FROM _turns), (SELECT count(*) FROM _calls), "
    "(SELECT count(*) FROM _segs), (SELECT count(*) FROM _batches), (SELECT count(*) FROM _fcalls)"
)  # same order as config.TABLES


def iter_archive(path: Path):
    """Yield ('manifest'|'shard', shard_id|None, file object). Consume each before advancing."""
    with tarfile.open(path, "r|gz") as tf:
        for m in tf:
            if not m.isfile():
                continue
            name = posixpath.normpath(m.name.replace("\\", "/"))
            if name.startswith("/") or ".." in name.split("/"):
                raise ValueError(f"unsafe tar member refused: {m.name!r}")
            base = posixpath.basename(name)
            if base == "manifest.json":
                yield "manifest", None, tf.extractfile(m)
            else:
                mm = SHARD_RE.search(base)
                if mm:
                    yield "shard", mm.group(1), tf.extractfile(m)


def cleanup_leftovers(cfg) -> None:
    for p in cfg.parquet.rglob("*.tmp"):
        p.unlink(missing_ok=True)
    for p in cfg.staging.glob("*"):
        p.unlink(missing_ok=True)


def ingest_shard(cfg, con, state, day: str, sid: str, fobj, log=print) -> dict:
    t0 = time.time()
    stage = cfg.staging / f"{day}-{sid}.jsonl.gz"
    tmp, final = {}, {}
    for t in TABLES:
        d = cfg.parquet / t / f"archive_date={day}"
        d.mkdir(parents=True, exist_ok=True)
        final[t] = d / f"shard-{sid}.parquet"
        tmp[t] = d / f"shard-{sid}.parquet.tmp"
    try:
        with open(stage, "wb") as out:
            shutil.copyfileobj(fobj, out, 1 << 20)
        for header, sql in load_chunks(SQL_FILE):
            sql = sql.replace("@SHARD_PATH@", q(stage)).replace("@SHARD@", sid)
            for t in TABLES:
                sql = sql.replace(f"@OUT_{t}@", q(tmp[t]))
            con.execute(sql)
        counts = dict(zip(TABLES, con.execute(COUNT_SQL).fetchone()))
        for t in TABLES:  # validate output counts BEFORE publishing the shard
            n = con.execute(f"SELECT count(*) FROM read_parquet('{q(tmp[t])}')").fetchone()[0]
            if n != counts[t]:
                raise RuntimeError(f"{day}/{sid}/{t}: parquet rows {n} != expected {counts[t]}")
        for t in TABLES:
            os.replace(tmp[t], final[t])
        secs = time.time() - t0
        state.mark_done(day, sid, counts, secs)
        return dict(counts, seconds=round(secs, 2))
    except BaseException:
        for p in tmp.values():
            p.unlink(missing_ok=True)
        raise
    finally:
        stage.unlink(missing_ok=True)


def run_ingest(cfg, state, days, limit: int | None = None, log=print) -> int:
    """Ingest the given days under a resource guard. Returns exit code (0 ok, 3 safe-stopped)."""
    from .db import connect
    from .monitor import Guard

    cfg.ensure_dirs()
    cleanup_leftovers(cfg)
    con = connect(cfg)
    with Guard(cfg, "ingest") as g:
        g.register(con)
        try:
            for day in days:
                if ingest_day(cfg, con, state, g, day, limit, log) == "stopped":
                    log(f"SAFE STOP: {g.reason}. Progress is checkpointed; re-run to resume.")
                    return 3
        except Exception:
            if g.should_stop:
                log(f"SAFE STOP (query interrupted): {g.reason}. Re-run to resume.")
                return 3
            raise
    return 0


def ingest_day(cfg, con, state, guard, day: str, limit: int | None = None, log=print) -> str:
    """Returns 'complete' | 'stopped' | 'limit'."""
    archive = cfg.raw / f"date.{day}.tar.gz"
    if not archive.exists():
        raise FileNotFoundError(f"{archive} missing - run `python -m ghcp download` first")
    n_run = 0
    for kind, sid, fobj in iter_archive(archive):
        if kind == "manifest":
            cfg.manifests.mkdir(parents=True, exist_ok=True)
            (cfg.manifests / f"{day}.manifest.json").write_bytes(fobj.read())
            continue
        if state.is_done(day, sid):
            continue
        if guard.should_stop:
            log(f"[{day}] stopping: {guard.reason}")
            return "stopped"
        if limit is not None and n_run >= limit:
            return "limit"
        r = ingest_shard(cfg, con, state, day, sid, fobj, log)
        n_run += 1
        log(f"[{day}] shard {sid}: sessions={r['sessions']} calls={r['llm_calls']} "
            f"segs={r['prompt_segments']} in {r['seconds']}s")
    return "complete"
