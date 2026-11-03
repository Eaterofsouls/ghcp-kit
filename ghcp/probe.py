"""Schema probe: compare the REAL first shard against the expected schema, in pure Python.

Run this before the first ingest. It never loads more than a few hundred lines.
Any mismatch must be reported to the user and fixed surgically in sql/ingest_shard.sql.
"""
from __future__ import annotations

import gzip
import io
import json

from .ingest import iter_archive

EXPECTED_PATHS = {
    "session_id", "date", "turns", "turns[].turn_id", "turns[].llm_calls", "turns[].tool_batches",
    "turns[].llm_calls[].message_id", "turns[].llm_calls[].timestamp",
    "turns[].llm_calls[].duration_ms", "turns[].llm_calls[].initiator_type",
    "turns[].llm_calls[].model", "turns[].llm_calls[].result", "turns[].llm_calls[].status_code",
    "turns[].llm_calls[].tokens", "turns[].llm_calls[].tokens.total",
    "turns[].llm_calls[].tokens.prompt", "turns[].llm_calls[].tokens.completion",
    "turns[].llm_calls[].tokens.cached", "turns[].llm_calls[].tokens.cached_pct",
    "turns[].llm_calls[].message_metadata", "turns[].llm_calls[].message_metadata[].type",
    "turns[].llm_calls[].message_metadata[].role",
    "turns[].llm_calls[].message_metadata[].sequenceId",
    "turns[].llm_calls[].message_metadata[].token_len",
    "turns[].tool_batches[].timestamp", "turns[].tool_batches[].duration_ms",
    "turns[].tool_batches[].auto_continue", "turns[].tool_batches[].result",
    "turns[].tool_batches[].request_id", "turns[].tool_batches[].function_calls",
    "turns[].tool_batches[].function_calls[].name",
    "turns[].tool_batches[].function_calls[].status",
    "turns[].tool_batches[].function_calls[].duration_ms",
}


def _walk(o, path, seen, ranges):
    t = type(o).__name__
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else k
            seen.setdefault(p, set()).add(type(v).__name__)
            _walk(v, p, seen, ranges)
    elif isinstance(o, list):
        for v in o:
            p = f"{path}[]"
            if isinstance(v, dict):
                _walk(v, p, seen, ranges)
            else:
                seen.setdefault(p, set()).add(type(v).__name__)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        lo, hi = ranges.get(path, (o, o))
        ranges[path] = (min(lo, o), max(hi, o))


def probe_archive(cfg, day: str, n_lines: int = 300) -> dict:
    archive = cfg.raw / f"date.{day}.tar.gz"
    seen: dict = {}
    ranges: dict = {}
    manifest = None
    lines = 0
    max_line = 0
    ts_samples: list = []
    for kind, sid, f in iter_archive(archive):
        if kind == "manifest":
            manifest = f.read().decode("utf-8", "replace")
            continue
        with gzip.open(io.BytesIO(f.read()), "rt", encoding="utf-8") as g:
            for line in g:
                max_line = max(max_line, len(line))
                rec = json.loads(line)
                _walk(rec, "", seen, ranges)
                lines += 1
                for t in rec.get("turns", [])[:1]:
                    for c in t.get("llm_calls", [])[:1]:
                        if len(ts_samples) < 5:
                            ts_samples.append(c.get("timestamp"))
                if lines >= n_lines:
                    break
        if lines >= n_lines:
            break
    norm = {p: sorted(v) for p, v in seen.items()}
    missing = sorted(EXPECTED_PATHS - set(norm))
    extra = sorted(set(norm) - EXPECTED_PATHS)
    result = dict(
        day=day, lines_probed=lines, max_line_chars=max_line, manifest_raw=manifest,
        missing_paths=missing, extra_paths=extra,
        types={p: v for p, v in norm.items() if len(v) > 1 or "NoneType" in v},
        numeric_ranges={p: list(r) for p, r in ranges.items()
                        if p.endswith(("cached_pct", "duration_ms", "status", "token_len", "prompt", "cached"))},
        timestamp_samples=ts_samples,
    )
    out = cfg.outputs / f"probe_{day}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))
    return result
