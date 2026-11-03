"""SQLite checkpoint: which archives/shards are done, with row counts."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


class State:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS shards("
            "day TEXT, shard TEXT, status TEXT, counts TEXT, seconds REAL, finished TEXT, "
            "PRIMARY KEY(day, shard))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS archives("
            "day TEXT PRIMARY KEY, bytes INTEGER, sha256 TEXT, status TEXT)"
        )
        self.db.commit()

    # shards ------------------------------------------------------------
    def is_done(self, day: str, shard: str) -> bool:
        r = self.db.execute(
            "SELECT status FROM shards WHERE day=? AND shard=?", (day, shard)
        ).fetchone()
        return bool(r and r[0] == "done")

    def mark_done(self, day: str, shard: str, counts: dict, seconds: float) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO shards VALUES(?,?,?,?,?,?)",
            (day, shard, "done", json.dumps(counts), seconds, time.strftime("%Y-%m-%dT%H:%M:%S")),
        )
        self.db.commit()

    def done_shards(self, day: str | None = None) -> list[tuple[str, str, dict, float]]:
        q = "SELECT day, shard, counts, seconds FROM shards WHERE status='done'"
        args: tuple = ()
        if day:
            q += " AND day=?"
            args = (day,)
        rows = self.db.execute(q + " ORDER BY day, shard", args).fetchall()
        return [(d, s, json.loads(c), sec) for d, s, c, sec in rows]

    def totals(self) -> dict:
        tot: dict = {}
        for _, _, c, _ in self.done_shards():
            for k, v in c.items():
                tot[k] = tot.get(k, 0) + v
        return tot

    # archives ----------------------------------------------------------
    def set_archive(self, day: str, nbytes: int, sha: str, status: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO archives VALUES(?,?,?,?)", (day, nbytes, sha, status)
        )
        self.db.commit()

    def get_archive(self, day: str):
        return self.db.execute(
            "SELECT day, bytes, sha256, status FROM archives WHERE day=?", (day,)
        ).fetchone()

    def close(self) -> None:
        self.db.close()
