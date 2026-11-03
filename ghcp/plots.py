"""Aggregate-only static figures from outputs/*.csv. No dashboard (out of scope)."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _rows(cfg, name):
    p = cfg.outputs / f"{name}.csv"
    if not p.exists():
        return []
    with open(p, newline="") as fh:
        return list(csv.DictReader(fh))


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def make_plots(cfg, log=print) -> list[str]:
    cfg.figures.mkdir(parents=True, exist_ok=True)
    made = []

    def save(fig, name):
        path = cfg.figures / name
        fig.tight_layout()
        fig.savefig(path, dpi=140)
        plt.close(fig)
        made.append(name)

    lor = _rows(cfg, "concentration_lorenz")
    if lor:
        fig, ax = plt.subplots(figsize=(5.5, 5))
        for m in sorted({r["metric"] for r in lor}):
            pts = [(_f(r["session_percentile"]), _f(r["cum_share"])) for r in lor if r["metric"] == m]
            ax.plot([0] + [p[0] for p in pts], [0] + [p[1] for p in pts], label=m)
        ax.plot([0, 100], [0, 1], "k:", lw=1)
        ax.set(xlabel="session percentile (ascending)", ylabel="cumulative share", title="Lorenz curves")
        ax.legend(fontsize=7)
        save(fig, "lorenz.png")

    cc = _rows(cfg, "cache_by_call_position")
    if cc:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar([r["call_position_in_turn"] for r in cc], [_f(r["cached_share"]) for r in cc])
        ax.set(xlabel="LLM call position within turn", ylabel="cached share of prompt tokens",
               title="Cache share by call position", ylim=(0, 1))
        save(fig, "cache_by_call_position.png")

    td = _rows(cfg, "time_decomposition_totals")
    if td:
        r = td[0]
        parts = [("LLM", _f(r["llm_share_of_span"])), ("tools", _f(r["tool_share_of_span"])),
                 ("other/residual", _f(r["positive_residual_share"]))]
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar([p[0] for p in parts], [p[1] for p in parts])
        ax.set(ylabel="share of summed turn span", title="Where turn time goes (totals)")
        save(fig, "time_decomposition.png")

    pc = _rows(cfg, "prompt_composition_by_type")[:12]
    if pc:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh([f"{r['seg_type']}/{r['role']}" for r in pc][::-1],
                [_f(r["share_of_segment_tokens"]) for r in pc][::-1])
        ax.set(xlabel="share of segment tokens", title="Prompt composition")
        save(fig, "prompt_composition.png")

    tt = _rows(cfg, "tool_transitions_top")[:20]
    if tt:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.barh([f"{r['from_tool']} > {r['to_tool']}" for r in tt][::-1], [_f(r["n"]) for r in tt][::-1])
        ax.set(xlabel="count", title="Top tool transitions")
        ax.tick_params(axis="y", labelsize=6)
        save(fig, "tool_transitions.png")

    hs = _rows(cfg, "HYPOTHETICAL_cost_index_scenarios")
    if hs:
        ks = sorted({_f(r["assumed_completion_price_multiple"]) for r in hs})
        rs = sorted({_f(r["assumed_cached_price_ratio"]) for r in hs})
        grid = [[next(_f(r["hypothetical_caching_saving_fraction"]) for r in hs
                      if _f(r["assumed_completion_price_multiple"]) == k and _f(r["assumed_cached_price_ratio"]) == rr)
                 for rr in rs] for k in ks]
        fig, ax = plt.subplots(figsize=(5.5, 4))
        im = ax.imshow(grid, aspect="auto")
        ax.set_xticks(range(len(rs)), [str(x) for x in rs])
        ax.set_yticks(range(len(ks)), [str(int(x)) for x in ks])
        ax.set(xlabel="assumed cached/uncached price ratio r", ylabel="assumed completion multiple k",
               title="HYPOTHETICAL caching saving fraction (relative units, not money)")
        ax.title.set_fontsize(8)
        fig.colorbar(im)
        save(fig, "HYPOTHETICAL_sensitivity.png")

    bm = [r for r in _rows(cfg, "benchmark") if r.get("engine") in ("duckdb", "polars") and not r.get("error")]
    if bm:
        fig, axes = plt.subplots(1, 2, figsize=(9, 4))
        for ax, key, title in ((axes[0], "median_wall_s", "median wall seconds"),
                               (axes[1], "max_peak_rss_mb", "peak RSS MB")):
            for eng in ("duckdb", "polars"):
                for q in sorted({r["query"] for r in bm}):
                    pts = sorted((int(r["days"]), _f(r[key])) for r in bm if r["engine"] == eng and r["query"] == q)
                    ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=f"{eng}:{q[:2]}")
            ax.set(xlabel="days of data", title=title)
        axes[0].legend(fontsize=6)
        save(fig, "benchmark.png")
    log(f"figures: {made}")
    return made
