"""Resource sampler + safety guard. Logs RSS, CPU, free RAM, disk; stops work on breach."""
from __future__ import annotations

import csv
import json
import os
import threading
import time
from pathlib import Path

import psutil


def dir_size_bytes(path: Path) -> int:
    total, stack = 0, [str(path)]
    while stack:
        p = stack.pop()
        try:
            with os.scandir(p) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        elif e.is_file(follow_symlinks=False):
                            total += e.stat(follow_symlinks=False).st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total


class Guard:
    """Use as a context manager. Call `should_stop` between units of work."""

    def __init__(self, cfg, phase: str, interval: float = 5.0, size_every: float = 30.0):
        self.cfg, self.phase = cfg, phase
        self.interval, self.size_every = interval, size_every
        self.reason: str | None = None
        self._halt = threading.Event()
        self._thread: threading.Thread | None = None
        self._cons: list = []
        self.peak_rss_mb = 0.0
        self.min_avail_mb = float("inf")
        self.max_used_gb = 0.0
        self.min_free_gb = float("inf")
        self.max_cpu = 0.0
        self.t0 = time.time()
        self._used_gb = 0.0

    @property
    def should_stop(self) -> bool:
        return self.reason is not None

    def register(self, con) -> None:
        self._cons.append(con)

    def sample(self) -> dict:
        """One synchronous sample (also used by tests)."""
        proc = psutil.Process()
        rss = proc.memory_info().rss / 2**20
        avail = psutil.virtual_memory().available / 2**20
        cpu = proc.cpu_percent(None)
        free = psutil.disk_usage(str(self.cfg.base)).free / 2**30
        self.peak_rss_mb = max(self.peak_rss_mb, rss)
        self.min_avail_mb = min(self.min_avail_mb, avail)
        self.min_free_gb = min(self.min_free_gb, free)
        self.max_cpu = max(self.max_cpu, cpu)
        return dict(rss_mb=rss, avail_mb=avail, cpu_pct=cpu, free_gb=free)

    def _trip(self, why: str) -> None:
        if self.reason is None:
            self.reason = why
            try:
                (self.cfg.logs / "STOP_REASON.txt").write_text(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} phase={self.phase}: {why}\n"
                )
            except OSError:
                pass
            for c in self._cons:
                try:
                    c.interrupt()
                except Exception:
                    pass

    def _loop(self) -> None:
        log_path = self.cfg.logs / "perf.csv"
        new = not log_path.exists()
        last_size = 0.0
        with open(log_path, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["time", "phase", "rss_mb", "avail_mb", "cpu_pct", "free_gb", "used_gb"])
            while not self._halt.wait(self.interval):
                s = self.sample()
                now = time.time()
                if now - last_size >= self.size_every:
                    self._used_gb = dir_size_bytes(self.cfg.base) / 2**30
                    self.max_used_gb = max(self.max_used_gb, self._used_gb)
                    last_size = now
                w.writerow([time.strftime("%H:%M:%S"), self.phase, round(s["rss_mb"], 1),
                            round(s["avail_mb"], 1), s["cpu_pct"], round(s["free_gb"], 2),
                            round(self._used_gb, 2)])
                fh.flush()
                c = self.cfg
                if s["rss_mb"] > c.rss_soft_mb:
                    self._trip(f"process RSS {s['rss_mb']:.0f} MB > {c.rss_soft_mb} MB")
                elif s["avail_mb"] < c.min_avail_mb:
                    self._trip(f"system available RAM {s['avail_mb']:.0f} MB < {c.min_avail_mb} MB")
                elif s["free_gb"] < c.min_free_gb:
                    self._trip(f"free disk {s['free_gb']:.1f} GB < {c.min_free_gb} GB")
                elif self._used_gb > c.max_used_gb:
                    self._trip(f"data dir {self._used_gb:.1f} GB > {c.max_used_gb} GB")

    def summary(self) -> dict:
        return dict(
            phase=self.phase,
            seconds=round(time.time() - self.t0, 1),
            peak_rss_mb=round(self.peak_rss_mb, 1),
            min_available_mb=None if self.min_avail_mb == float("inf") else round(self.min_avail_mb, 1),
            min_free_gb=None if self.min_free_gb == float("inf") else round(self.min_free_gb, 2),
            max_data_dir_gb=round(self.max_used_gb, 2),
            max_cpu_pct=self.max_cpu,
            stopped_reason=self.reason,
        )

    def __enter__(self) -> "Guard":
        self.cfg.logs.mkdir(parents=True, exist_ok=True)
        self.sample()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._halt.set()
        if self._thread:
            self._thread.join(timeout=10)
        self.sample()
        out = self.cfg.logs / f"guard_summary_{self.phase}.json"
        try:
            out.write_text(json.dumps(self.summary(), indent=2))
        except OSError:
            pass
