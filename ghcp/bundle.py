"""Zip the SMALL result files (csv/json/md/png/logs) so they can be sent back for review.
Never includes raw archives or Parquet."""
from __future__ import annotations

import zipfile
from pathlib import Path


def make_bundle(cfg, log=print) -> Path:
    out = cfg.base / "outputs_bundle.zip"
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for sub, pats in (("outputs", ("*.csv", "*.json")), ("reports", ("*.md",)),
                          ("figures", ("*.png",)), ("logs", ("guard_summary_*.json", "perf.csv", "STOP_REASON.txt")),
                          ("manifests", ("*.json",))):
            for pat in pats:
                for p in sorted((cfg.base / sub).glob(pat)):
                    if p.stat().st_size > 50 * 2**20:
                        continue
                    z.write(p, f"{sub}/{p.name}")
                    n += 1
        if cfg.state_db.exists():
            z.write(cfg.state_db, "state/state.db")
            n += 1
    log(f"bundle: {out} ({n} files, {out.stat().st_size / 2**20:.1f} MB)")
    return out
