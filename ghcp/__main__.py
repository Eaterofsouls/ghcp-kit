"""CLI: python -m ghcp <command>.  See README.md and PLAN.md."""
from __future__ import annotations

import argparse
import json
import sys

from .config import Config


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ghcp")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest", help="end-to-end test on a tiny FAKE fixture")
    for name in ("download", "probe", "ingest"):
        s = sub.add_parser(name)
        s.add_argument("--days", nargs="*", help="e.g. 2026-06-06 (default: all 7)")
        if name == "ingest":
            s.add_argument("--limit-shards", type=int, default=None, help="max shards per day this run")
    sub.add_parser("validate")
    a = sub.add_parser("analyze")
    a.add_argument("--only", help="substring of an sql/analysis file name, e.g. 02_cache")
    b = sub.add_parser("benchmark")
    b.add_argument("--repeats", type=int, default=3)
    for name in ("plots", "report", "bundle", "status", "all"):
        sub.add_parser(name)
    args = p.parse_args(argv)

    cfg = Config.from_env()
    cfg.ensure_dirs()
    days = getattr(args, "days", None) or cfg.days

    if args.cmd == "selftest":
        from .selftest import run_selftest
        return run_selftest(cfg)

    from .state import State
    state = State(cfg.state_db)

    if args.cmd == "download":
        from .download import download_day
        from .monitor import Guard
        with Guard(cfg, "download") as g:
            for d in days:
                if g.should_stop:
                    print("SAFE STOP:", g.reason)
                    return 3
                download_day(cfg, d, state)
        return 0
    if args.cmd == "probe":
        from .probe import probe_archive
        r = probe_archive(cfg, days[0])
        print(json.dumps({k: r[k] for k in r if k != "manifest_raw"}, indent=2, default=str))
        print("manifest.json (raw):", r["manifest_raw"])
        return 1 if (r["missing_paths"] or r["extra_paths"] or r["types"]) else 0
    if args.cmd == "ingest":
        from .ingest import run_ingest
        return run_ingest(cfg, state, days, args.limit_shards)
    if args.cmd == "validate":
        from .validate import run_validation
        from .monitor import Guard
        with Guard(cfg, "validate"):
            r = run_validation(cfg, state)
        print(f"FAIL checks: {r['n_fail']}")
        return 1 if r["n_fail"] else 0
    if args.cmd == "analyze":
        from .analyze import run_analysis
        from .monitor import Guard
        with Guard(cfg, "analyze") as g:
            run_analysis(cfg, g, only=args.only)
            if g.should_stop:
                print("SAFE STOP:", g.reason)
                return 3
        return 0
    if args.cmd == "benchmark":
        from .benchmark import run_benchmark
        run_benchmark(cfg, repeats=args.repeats)
        return 0
    if args.cmd == "plots":
        from .plots import make_plots
        make_plots(cfg)
        return 0
    if args.cmd == "report":
        from .report import build_report
        build_report(cfg, state)
        return 0
    if args.cmd == "bundle":
        from .bundle import make_bundle
        make_bundle(cfg)
        return 0
    if args.cmd == "status":
        from .monitor import dir_size_bytes
        print("base:", cfg.base)
        for d in cfg.days:
            print(d, "shards done:", len(state.done_shards(d)))
        print("totals:", state.totals())
        print(f"data dir size: {dir_size_bytes(cfg.base) / 2**30:.2f} GB")
        sr = cfg.logs / "STOP_REASON.txt"
        if sr.exists():
            print("LAST STOP REASON:", sr.read_text().strip())
        return 0
    if args.cmd == "all":
        for c in ("validate", "analyze", "benchmark", "plots", "report", "bundle"):
            rc = main([c])
            if rc not in (0, 1) or (c in ("analyze",) and rc):
                return rc
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
