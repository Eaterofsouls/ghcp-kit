"""End-to-end self-test on a tiny FAKE fixture. Must pass before touching real data."""
from __future__ import annotations

import csv
import dataclasses
import json
import os
import shutil
import time

from .config import Config


def run_selftest(real_cfg, log=print) -> int:
    from .analyze import run_analysis
    from .benchmark import run_benchmark
    from .bundle import make_bundle
    from .db import connect, create_views
    from .fixture import build_fixture
    from .ingest import run_ingest
    from .monitor import Guard
    from .plots import make_plots
    from .probe import probe_archive
    from .report import build_report
    from .state import State
    from .validate import run_validation

    base = real_cfg.base / "_selftest"
    shutil.rmtree(base, ignore_errors=True)
    days = ["2026-06-01", "2026-06-02"]
    cfg = dataclasses.replace(real_cfg, base=base, days=days, published=None, published_tokens=None,
                              user_reported=None)
    cfg.ensure_dirs()
    os.environ["GHCP_BASE"] = str(base)
    os.environ["GHCP_DAYS"] = ",".join(days)
    results: list[tuple[str, bool, str]] = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), str(detail)))
        log(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")

    exp = build_fixture(cfg.raw, days=tuple(days))
    cfg.published = {k: exp[k] for k in ("sessions", "turns", "llm_calls", "tool_batches", "tool_calls",
                                         "distinct_models")}
    check("fixture built", exp["sessions"] == 20, exp)

    pr = probe_archive(cfg, days[0])
    check("probe: schema matches", not pr["missing_paths"] and not pr["extra_paths"],
          dict(missing=pr["missing_paths"], extra=pr["extra_paths"]))

    state = State(cfg.state_db)
    rc = run_ingest(cfg, state, days, limit=1, log=log)          # partial run = simulated interruption
    first = sorted(cfg.parquet.rglob("shard-0000.parquet"))
    mt = {p: p.stat().st_mtime_ns for p in first}
    check("partial ingest checkpointed", rc == 0 and len(state.done_shards()) == 2, len(state.done_shards()))
    time.sleep(0.05)
    rc = run_ingest(cfg, state, days, log=log)                    # resume
    check("resume completes all shards", rc == 0 and len(state.done_shards()) == 4, len(state.done_shards()))
    check("resume did not redo finished shards", all(p.stat().st_mtime_ns == mt[p] for p in first))
    check("no leftover .tmp / staging", not list(cfg.parquet.rglob("*.tmp")) and not list(cfg.staging.glob("*")))

    v = run_validation(cfg, state, log=log)
    check("validation has zero FAIL", v["n_fail"] == 0, [c for c in v["checks"] if c["status"] == "FAIL"])
    byname = {c["name"]: c for c in v["checks"]}
    check("anomaly: negative LLM duration detected", byname["anomaly:negative_llm_duration_ms"]["observed"] == exp["negative_llm"],
          byname["anomaly:negative_llm_duration_ms"]["observed"])
    check("anomaly: cross-turn ref detected", byname["anomaly:cross_turn_tool_batch_refs"]["observed"]["cross"] == exp["cross_turn"],
          byname["anomaly:cross_turn_tool_batch_refs"]["observed"])
    check("anomaly: out-of-window ts detected", byname["anomaly:llm_ts_outside_window"]["observed"] == exp["out_of_window"],
          byname["anomaly:llm_ts_outside_window"]["observed"])
    check("anomalies preserved (rows not dropped)", v["counts"]["llm_calls"] == exp["llm_calls"], v["counts"])

    with Guard(cfg, "analyze") as g:
        timings = run_analysis(cfg, g, log=log)
    check("all analysis SQL ran", len(timings) >= 30, len(timings))
    with open(cfg.outputs / "cache_overall.csv", newline="") as fh:
        row = next(csv.DictReader(fh))
    check("analysis totals match fixture",
          int(row["n_calls"]) == exp["llm_calls"] and int(row["prompt_tokens"]) == exp["prompt_tokens"]
          and int(row["cached_tokens"]) == exp["cached_tokens"], row)
    check("hypothetical output present", (cfg.outputs / "HYPOTHETICAL_cost_index_scenarios.csv").exists())

    bm = run_benchmark(cfg, ndays_list=(1, 2), repeats=1, log=log)
    ok_rows = [r for r in bm if r.get("engine") in ("duckdb", "polars") and not r.get("error")]
    check("benchmark ran for both engines, no mismatch",
          {r["engine"] for r in ok_rows} == {"duckdb", "polars"} and not any(r.get("engine") == "MISMATCH" for r in bm),
          [r for r in bm if r.get("error")])

    figs = make_plots(cfg, log=log)
    check("figures written", len(figs) >= 5, figs)
    build_report(cfg, state, log=log)
    check("report written", (cfg.reports / "seven_day_metrics.md").stat().st_size > 1000)
    make_bundle(cfg, log=log)
    check("bundle written", (cfg.base / "outputs_bundle.zip").exists())

    tiny = dataclasses.replace(cfg, rss_soft_mb=1)
    with Guard(tiny, "guardtest", interval=0.2) as g2:
        time.sleep(0.8)
        tripped = g2.should_stop
    check("guard trips on breach", tripped, g2.reason)

    state.close()
    failed = [r for r in results if not r[1]]
    log(f"\nSELFTEST: {len(results) - len(failed)}/{len(results)} passed")
    if not failed:
        shutil.rmtree(base, ignore_errors=True)
        return 0
    log(f"Failures kept for inspection in {base}")
    return 1
