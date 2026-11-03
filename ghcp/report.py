"""Assemble reports/seven_day_metrics.md from outputs. Facts and numbers only; no interpretation."""
from __future__ import annotations

import csv
import json
import platform
import time


def _table(path, max_rows=25):
    if not path.exists():
        return "_(missing)_\n"
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return "_(empty)_\n"
    head, body = rows[0], rows[1:max_rows + 1]

    def fmt(v):
        try:
            x = float(v)
            return f"{x:,.0f}" if abs(x) >= 1000 and x == int(x) else (f"{x:.4g}" if x != int(x) else str(int(x)))
        except ValueError:
            return v.replace("|", "/")

    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in body]
    if len(rows) - 1 > max_rows:
        out.append(f"\n_(first {max_rows} of {len(rows) - 1} rows; full file in outputs/)_")
    return "\n".join(out) + "\n"


SECTIONS = [
    ("Token concentration - top-x% share of total", "concentration_top_shares"),
    ("Gini coefficients", "concentration_gini"),
    ("Per-session distributions", "session_distribution"),
    ("Cache - overall", "cache_overall"),
    ("Cache - by initiator", "cache_by_initiator"),
    ("Cache - by call position in turn", "cache_by_call_position"),
    ("Cache - by turn position in session", "cache_by_turn_position"),
    ("Cache - by model (anonymised labels)", "cache_by_model"),
    ("Cache - by session size", "cache_by_session_size"),
    ("Time decomposition - totals", "time_decomposition_totals"),
    ("Time decomposition - percentiles", "time_decomposition_percentiles"),
    ("Idle gaps between turns", "idle_gap_between_turns"),
    ("Prompt composition by segment type", "prompt_composition_by_type"),
    ("Segment tokens vs reported prompt tokens", "segment_vs_prompt_token_coverage"),
    ("Context growth by call position", "context_growth_by_call_position"),
    ("Tool usage", "tool_usage"),
    ("Tool batches", "tool_batch_summary"),
    ("Top tool transitions", "tool_transitions_top"),
    ("Top tool sequences (first six tools)", "tool_sequences_top"),
    ("Model share", "model_share"),
    ("HYPOTHETICAL cost-index scenarios (relative units, NOT money)", "HYPOTHETICAL_cost_index_scenarios"),
    ("Benchmark: DuckDB vs Polars (single machine; no Spark)", "benchmark"),
    ("Analysis step timings", "analysis_timings"),
]


def build_report(cfg, state, log=print) -> str:
    L = ["# Seven-day GHCP agentic-trace metrics report", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} on {platform.platform()} / Python {platform.python_version()}",
         "", "> Descriptive statistics of a released sample. No dollar costs. The HYPOTHETICAL section is a "
         "what-if in relative units. Anomalies are reported, not removed.", ""]
    L += ["## Ingestion", f"Checkpointed shards: {len(state.done_shards())}", "",
          "Totals from checkpoint: `" + json.dumps(state.totals()) + "`", ""]
    secs = sum(s for *_, s in state.done_shards())
    L += [f"Summed per-shard ingest seconds: {secs:,.0f}", ""]
    for g in sorted(cfg.logs.glob("guard_summary_*.json")):
        L += [f"- `{g.name}`: `{g.read_text().replace(chr(10), ' ')}`"]
    L += ["", "## Validation"]
    vp = cfg.outputs / "validation.json"
    if vp.exists():
        v = json.loads(vp.read_text())
        L += [f"FAIL count: **{v['n_fail']}**", "", "| status | check | observed | expected | note |", "|---|---|---|---|---|"]
        for c in v["checks"]:
            status = c['status']
            note = c['note']
            if c['name'] in ("anomaly:cross_turn_tool_batch_refs", "probe:tool_batch_ts>=its_llm_call_ts", "probe:tool_batch_ts>=llm_call_end"):
                status = "SUPERSEDED"
                note = "SUPERSEDED by diag_s6b D2 (earlier validation check suffered fan-out join on non-unique message_id)"
            L.append(f"| {status} | {c['name']} | {json.dumps(c['observed'], default=str)} | "
                     f"{c['expected'] if c['expected'] is not None else ''} | {note} |")
    else:
        L.append("_validation.json missing - run `python -m ghcp validate`_")
    for title, name in SECTIONS:
        L += ["", f"## {title}", _table(cfg.outputs / f"{name}.csv")]
    L += ["", "## Figures"] + [f"- figures/{p.name}" for p in sorted(cfg.figures.glob("*.png"))]
    L += ["", "## Known limitations (carried from KNOWN_FACTS.md)",
          "- Released sample of non-enterprise sessions, one week; sampling rate not published.",
          "- Model names anonymised; no mapping to prices, so no currency figures exist here.",
          "- Semantics of `tokens.cached` are an assumption (publisher-reported cached prompt tokens).",
          "- LLM-call `timestamp` behaves like a completion (end) time (diag_s6b D3: 0.06% vs 34.4% ordering violations); "
          "tool-batch timestamp semantics are undetermined, so time shares are reported under both assumptions.",
          "- Duration fields contain implausible values (negative, and >1 h); see the outlier-contribution diagnostic. "
          "Tool time may include waiting for user confirmation; that cannot be separated here.",
          "- ~2.7% of LLM calls have null token counts (all non-Success calls, `tool-model`, and some Success calls); "
          "ratios use calls with token counts only, sums skip them.",
          "- `auto_continue` is null for ~56% of tool batches; its share is over the non-null batches only.",
          "- Tool-call status 0 (3.4% of calls) is undocumented and reported as observed.",
          "- Timestamps outside the 2026-06-01..07 window exist (0.1% of calls, down to 2019); kept and flagged.",
          "- No quality, outcome or user-plan fields."]
    text = "\n".join(L) + "\n"
    cfg.reports.mkdir(parents=True, exist_ok=True)
    (cfg.reports / "seven_day_metrics.md").write_text(text, encoding="utf-8")
    log(f"report: {cfg.reports / 'seven_day_metrics.md'}")
    return text
