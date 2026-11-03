"""Central configuration. Every limit lives here so nothing is hidden elsewhere."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

RELEASE_BASE = (
    "https://github.com/Azure/AzurePublicDataset/releases/download/ghcp-coding-agent-2026"
)
DAYS = [f"2026-06-0{i}" for i in range(1, 8)]

# Content-Length from HTTP HEAD on 2026-10-31 [VERIFIED]
ARCHIVE_BYTES = {
    "2026-06-01": 594_479_134,
    "2026-06-02": 621_345_734,
    "2026-06-03": 618_403_924,
    "2026-06-04": 572_771_629,
    "2026-06-05": 548_375_182,
    "2026-06-06": 124_247_983,
    "2026-06-07": 139_262_550,
}

# analysis/GitHubCopilotCodingAgents/DATASET_CARD.md [VERIFIED]
PUBLISHED = dict(
    sessions=301_026,
    turns=1_189_581,
    llm_calls=9_310_255,
    tool_batches=7_767_261,
    tool_calls=8_681_190,
    distinct_models=37,
)
# Rounded by the publisher (e.g. "631.4B"), so compared with a tolerance.
PUBLISHED_TOKENS = dict(prompt=631.4e9, completion=4.91e9, cached=540.95e9)

# Findings reported by the team's own hardware/feasibility audit. NOT confirmed by Claude.
USER_REPORTED = dict(negative_llm_latencies=4, cross_turn_tool_batch_pct=0.98)

WINDOW_START = "2026-06-01"
WINDOW_END_EXCL = "2026-06-08"

# Order matters: ingest.py maps the count query onto this order.
TABLES = [
    "sessions",
    "turns",
    "llm_calls",
    "prompt_segments",
    "tool_batches",
    "tool_calls",
]


def _check_drive(base: Path) -> None:
    if sys.platform != "win32" or os.environ.get("GHCP_ALLOW_ANY_DRIVE"):
        return
    drive = base.resolve().drive.upper()
    if drive != "D:":
        raise SystemExit(
            f"Refusing to use {base}: all data must live on D:\\ (drive is '{drive}'). "
            "Set GHCP_BASE to a folder on D:\\ (or GHCP_ALLOW_ANY_DRIVE=1 to override)."
        )


@dataclass
class Config:
    base: Path
    days: list = field(default_factory=lambda: list(DAYS))
    published: dict | None = field(default_factory=lambda: dict(PUBLISHED))
    published_tokens: dict | None = field(default_factory=lambda: dict(PUBLISHED_TOKENS))
    user_reported: dict | None = field(default_factory=lambda: dict(USER_REPORTED))
    window_start: str = WINDOW_START
    window_end_excl: str = WINDOW_END_EXCL
    # Resource limits (hardware audit: 12 GB installed, ~1.79 GB available)
    memory_limit_mb: int = 1000      # DuckDB memory_limit
    threads: int = 2
    temp_cap_gb: int = 4             # DuckDB spill cap
    rss_soft_mb: int = 1500          # stop if this process exceeds this
    min_avail_mb: int = 250          # stop if system available RAM drops below this
    min_free_gb: float = 10.0        # stop if free space on the data drive drops below this
    max_used_gb: float = 15.0        # stop if everything under base exceeds this

    @classmethod
    def from_env(cls) -> "Config":
        default = "D:/ghcp/data" if sys.platform == "win32" else "./ghcp_data"
        base = Path(os.environ.get("GHCP_BASE") or default)
        _check_drive(base)
        cfg = cls(base=base)
        if os.environ.get("GHCP_DAYS"):
            cfg.days = [d for d in os.environ["GHCP_DAYS"].split(",") if d]
        for name, cast in [
            ("memory_limit_mb", int), ("threads", int), ("temp_cap_gb", int),
            ("rss_soft_mb", int), ("min_avail_mb", int),
            ("min_free_gb", float), ("max_used_gb", float),
        ]:
            v = os.environ.get("GHCP_" + name.upper())
            if v:
                setattr(cfg, name, cast(v))
        return cfg

    # --- derived paths -------------------------------------------------
    @property
    def raw(self) -> Path: return self.base / "raw"
    @property
    def staging(self) -> Path: return self.base / "staging"
    @property
    def parquet(self) -> Path: return self.base / "parquet"
    @property
    def duckdb_tmp(self) -> Path: return self.base / "duckdb_tmp"
    @property
    def state_db(self) -> Path: return self.base / "state" / "state.db"
    @property
    def manifests(self) -> Path: return self.base / "manifests"
    @property
    def logs(self) -> Path: return self.base / "logs"
    @property
    def outputs(self) -> Path: return self.base / "outputs"
    @property
    def reports(self) -> Path: return self.base / "reports"
    @property
    def figures(self) -> Path: return self.base / "figures"

    def ensure_dirs(self) -> None:
        for p in (self.raw, self.staging, self.parquet, self.duckdb_tmp, self.state_db.parent,
                  self.manifests, self.logs, self.outputs, self.reports, self.figures):
            p.mkdir(parents=True, exist_ok=True)


def q(path) -> str:
    """Path -> SQL-safe string literal body (forward slashes, quotes doubled)."""
    return Path(path).as_posix().replace("'", "''")
