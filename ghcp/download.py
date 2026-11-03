"""Resumable, size-verified download of the daily archives. Archives are never modified."""
from __future__ import annotations

import hashlib
import shutil
import time
import urllib.error
import urllib.request

from .config import ARCHIVE_BYTES, RELEASE_BASE

CHUNK = 1 << 20


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def download_day(cfg, day: str, state, log=print):
    expected = ARCHIVE_BYTES[day]
    dest = cfg.raw / f"date.{day}.tar.gz"
    part = cfg.raw / f"date.{day}.tar.gz.part"
    url = f"{RELEASE_BASE}/date.{day}.tar.gz"
    cfg.raw.mkdir(parents=True, exist_ok=True)

    if dest.exists() and dest.stat().st_size == expected:
        if not state.get_archive(day):
            state.set_archive(day, expected, sha256_file(dest), "complete")
        log(f"[{day}] already complete ({expected:,} bytes)")
        return dest

    have0 = part.stat().st_size if part.exists() else 0
    free_gb = shutil.disk_usage(cfg.raw).free / 2**30
    need_gb = (expected - have0) / 2**30
    if free_gb - need_gb < cfg.min_free_gb:
        raise RuntimeError(
            f"[{day}] not enough disk: free {free_gb:.1f} GB, need {need_gb:.1f} GB "
            f"plus {cfg.min_free_gb} GB reserve"
        )

    for attempt in range(1, 7):
        have = part.stat().st_size if part.exists() else 0
        if have == expected:
            break
        if have > expected:
            part.unlink()
            have = 0
        headers = {"User-Agent": "ghcp-kit/1.0"}
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            log(f"[{day}] attempt {attempt}: resuming at {have:,}/{expected:,}")
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                mode = "ab" if (have and r.status == 206) else "wb"
                with open(part, mode) as f:
                    shutil.copyfileobj(r, f, CHUNK)
        except urllib.error.HTTPError as e:
            log(f"[{day}] HTTP {e.code}: {e.reason}")
            if e.code == 416 and part.exists():
                part.unlink()
            time.sleep(min(30, 2 ** attempt))
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            log(f"[{day}] network error: {e!r}")
            time.sleep(min(30, 2 ** attempt))

    size = part.stat().st_size if part.exists() else 0
    if size != expected:
        raise RuntimeError(f"[{day}] size mismatch after retries: {size:,} != {expected:,}")
    part.replace(dest)
    sha = sha256_file(dest)
    state.set_archive(day, expected, sha, "complete")
    log(f"[{day}] complete, sha256={sha[:16]}...")
    return dest
