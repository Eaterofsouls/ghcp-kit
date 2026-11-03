"""TEST FIXTURE GENERATOR - FAKE DATA, used only by `selftest` to prove the pipeline works.

The output imitates the published schema.json structure, including three injected anomalies.
It is never analysed as data and is never written into the real data folders.
"""
from __future__ import annotations

import gzip
import io
import json
import random
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODELS = ["Model A", "Model B", "Model C"]
SEG_TYPES = [("System", "system"), ("Context", "user"), ("UserMessage", "user"), ("Assistant", "assistant")]
TOOLS = ["read_file", "run_in_terminal", "grep_search", "apply_patch"]


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def build_fixture(raw_dir: Path, days=("2026-06-01", "2026-06-02"), shards_per_day=2,
                  sessions_per_shard=5, seed=7) -> dict:
    rng = random.Random(seed)
    raw_dir.mkdir(parents=True, exist_ok=True)
    exp = dict(sessions=0, turns=0, llm_calls=0, prompt_segments=0, tool_batches=0, tool_calls=0,
               negative_llm=0, cross_turn=0, out_of_window=0, prompt_tokens=0, cached_tokens=0)
    models_seen: set = set()
    for di, day in enumerate(days):
        base = datetime.fromisoformat(day).replace(tzinfo=timezone.utc) + timedelta(hours=8)
        shards = []
        for si in range(shards_per_day):
            lines = []
            for k in range(sessions_per_shard):
                sid = f"s{di}{si}{k}"
                n_turns = 2 if (di == 0 and si == 0 and k == 0) else rng.randint(1, 3)
                t = base + timedelta(minutes=rng.randint(0, 600))
                turns, first_msg = [], None
                for ti in range(n_turns):
                    calls, batches = [], []
                    n_calls = rng.randint(2, 4) if (di == 0 and si == 0 and k == 0) else rng.randint(1, 4)
                    for ci in range(n_calls):
                        mid = f"{sid}-t{ti}-m{ci}"
                        first_msg = first_msg or mid
                        prompt = rng.randint(1000, 50000)
                        cached = int(prompt * rng.random())
                        comp = rng.randint(10, 2000)
                        dur = round(rng.uniform(300, 9000), 1)
                        ts = t
                        if di == 1 and si == 0 and k == 0 and ti == 0 and ci == 0:
                            ts = datetime(1970, 1, 1, tzinfo=timezone.utc)   # anomaly: out of window
                            exp["out_of_window"] += 1
                        if di == 0 and si == 0 and k == 0 and ti == 0 and ci == 0:
                            dur = -5.0                                         # anomaly: negative latency
                            exp["negative_llm"] += 1
                        segs = [
                            {"type": ty, "role": ro, "sequenceId": q, "token_len": rng.randint(5, 3000)}
                            for q, (ty, ro) in enumerate(rng.sample(SEG_TYPES, rng.randint(2, 4)))
                        ]
                        model = rng.choice(MODELS)
                        models_seen.add(model)
                        calls.append({
                            "message_id": mid, "timestamp": _ts(ts), "duration_ms": dur,
                            "initiator_type": "user" if ci == 0 else "agent", "model": model,
                            "result": "Success", "status_code": "OK",
                            "tokens": {"total": prompt + comp, "prompt": prompt, "completion": comp,
                                       "cached": cached, "cached_pct": round(100 * cached / prompt, 2)},
                            "message_metadata": segs,
                        })
                        exp["llm_calls"] += 1
                        exp["prompt_segments"] += len(segs)
                        exp["prompt_tokens"] += prompt
                        exp["cached_tokens"] += cached
                        t += timedelta(milliseconds=int(max(dur, 0)) + 200)
                        if ci < n_calls - 1:
                            fcs = [{"name": rng.choice(TOOLS), "status": rng.choice([1, 1, 1, 2]),
                                    "duration_ms": round(rng.uniform(5, 800), 1)}
                                   for _ in range(rng.randint(1, 3))]
                            req = mid
                            if di == 0 and si == 0 and k == 0 and ti == 1 and ci == 0:
                                req = f"{sid}-t0-m0"                             # anomaly: cross-turn ref
                                exp["cross_turn"] += 1
                            batches.append({"timestamp": _ts(t), "duration_ms": round(rng.uniform(5, 900), 1),
                                            "auto_continue": True, "result": "Success",
                                            "request_id": req, "function_calls": fcs})
                            exp["tool_batches"] += 1
                            exp["tool_calls"] += len(fcs)
                            t += timedelta(milliseconds=500)
                    turns.append({"turn_id": f"{sid}-t{ti}", "llm_calls": calls, "tool_batches": batches})
                    exp["turns"] += 1
                    t += timedelta(minutes=rng.randint(1, 20))
                lines.append(json.dumps({"session_id": sid, "date": day, "turns": turns}))
                exp["sessions"] += 1
            shards.append(("\n".join(lines) + "\n").encode())
        archive = raw_dir / f"date.{day}.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            def add(name: str, data: bytes):
                ti_ = tarfile.TarInfo(name)
                ti_.size = len(data)
                tf.addfile(ti_, io.BytesIO(data))
            add(f"date={day}/manifest.json", json.dumps(
                {"date": day, "num_sessions": len(shards) * sessions_per_shard,
                 "num_shards": len(shards)}).encode())
            for i, raw in enumerate(shards):
                add(f"date={day}/shard-{i:04d}.jsonl.gz", gzip.compress(raw))
    exp["distinct_models"] = len(models_seen)
    exp["days"] = list(days)
    return exp
