"""Reconcile the corpus against published counts and REPORT (never remove) anomalies."""
from __future__ import annotations

import json
import re

from .config import TABLES
from .db import connect, create_views


def _one(con, sql):
    return con.execute(sql).fetchone()[0]


def run_validation(cfg, state, log=print) -> dict:
    con = connect(cfg)
    create_views(con, cfg)
    checks: list[dict] = []

    def add(name, ok, observed, expected=None, note=""):
        status = "INFO" if ok is None else ("PASS" if ok else "FAIL")
        checks.append(dict(name=name, status=status, observed=observed, expected=expected, note=note))
        log(f"  [{status}] {name}: observed={observed} expected={expected} {note}")

    counts = {t: _one(con, f"SELECT count(*) FROM {t}") for t in TABLES}

    # V1 totals vs the publisher's dataset card
    if cfg.published:
        for k in ("sessions", "turns", "llm_calls", "tool_batches", "tool_calls"):
            if k in cfg.published:
                add(f"count:{k}", counts[k] == cfg.published[k], counts[k], cfg.published[k])
        if "distinct_models" in cfg.published:
            n = _one(con, "SELECT count(DISTINCT model) FROM llm_calls")
            add("distinct_models", n == cfg.published["distinct_models"], n, cfg.published["distinct_models"])
    add("count:prompt_segments", None, counts["prompt_segments"], note="no published figure")

    # V2 token sums vs rounded published sums (0.15% tolerance)
    tok = con.execute(
        "SELECT sum(tokens_prompt), sum(tokens_completion), sum(tokens_cached) FROM llm_calls"
    ).fetchone()
    if cfg.published_tokens:
        for name, val in zip(("prompt", "completion", "cached"), tok):
            exp = cfg.published_tokens[name]
            ok = abs(val - exp) / exp <= 0.0015
            add(f"tokens:{name}", ok, int(val), exp, "published values are rounded")
    else:
        add("tokens:sums", None, [int(x or 0) for x in tok])

    # V3 checkpoint state vs parquet
    st = state.totals()
    for t in TABLES:
        add(f"state_vs_parquet:{t}", st.get(t, 0) == counts[t], st.get(t, 0), counts[t])

    # V4 manifests (format unknown: report what we can find)
    for day in cfg.days:
        mp = cfg.manifests / f"{day}.manifest.json"
        got = _one(con, f"SELECT count(*) FROM sessions WHERE CAST(archive_date AS VARCHAR) = '{day}'")
        if not mp.exists():
            add(f"manifest:{day}", None, got, note="manifest not saved")
            continue
        try:
            man = json.loads(mp.read_text())
        except ValueError:
            add(f"manifest:{day}", None, got, note="manifest not JSON")
            continue
        cand = {k: v for k, v in _flatten(man).items()
                if re.search(r"session", k, re.I) and isinstance(v, int)}
        if cand:
            k, v = next(iter(cand.items()))
            add(f"manifest:{day}:{k}", v == got, got, v)
        else:
            add(f"manifest:{day}", None, got, note="no session-count key found; inspect manifests/")

    # V5 duplicates, per day to bound memory
    dup_s = dup_c = 0
    for day in cfg.days:
        dup_s += _one(con, f"SELECT count(*) - count(DISTINCT session_id) FROM sessions "
                           f"WHERE CAST(archive_date AS VARCHAR) = '{day}'")
        dup_c += _one(con, f"SELECT count(*) - count(DISTINCT message_id) FROM llm_calls "
                           f"WHERE CAST(archive_date AS VARCHAR) = '{day}'")
    add("duplicate_session_ids", dup_s == 0, dup_s, 0)
    add("duplicate_message_ids", dup_c == 0, dup_c, 0, "within a day")

    # ---- anomalies: reported, never removed ---------------------------------
    neg = _one(con, "SELECT count(*) FROM llm_calls WHERE duration_ms < 0")
    ur = cfg.user_reported or {}
    note = ""
    if "negative_llm_latencies" in ur:
        note = f"team audit reported {ur['negative_llm_latencies']} (unconfirmed by Claude)"
    add("anomaly:negative_llm_duration_ms", None, neg, note=note)
    add("anomaly:negative_tool_batch_duration_ms", None, _one(con, "SELECT count(*) FROM tool_batches WHERE duration_ms < 0"))
    add("anomaly:negative_tool_call_duration_ms", None, _one(con, "SELECT count(*) FROM tool_calls WHERE duration_ms < 0"))
    add("anomaly:null_duration_llm", None, _one(con, "SELECT count(*) FROM llm_calls WHERE duration_ms IS NULL"))
    add("anomaly:unparseable_or_null_llm_ts", None,
        _one(con, "SELECT count(*) FROM llm_calls WHERE ts IS NULL"))
    add("anomaly:unparseable_or_null_tool_ts", None,
        _one(con, "SELECT count(*) FROM tool_batches WHERE ts IS NULL"))
    w0, w1 = cfg.window_start, cfg.window_end_excl
    oow = _one(con, f"SELECT count(*) FROM llm_calls WHERE ts < TIMESTAMPTZ '{w0} 00:00:00+00' "
                    f"OR ts >= TIMESTAMPTZ '{w1} 00:00:00+00'")
    add("anomaly:llm_ts_outside_window", None, oow, note=f"window {w0}..{w1} UTC")
    add("anomaly:tool_ts_outside_window", None,
        _one(con, f"SELECT count(*) FROM tool_batches WHERE ts < TIMESTAMPTZ '{w0} 00:00:00+00' "
                  f"OR ts >= TIMESTAMPTZ '{w1} 00:00:00+00'"))
    mm = con.execute("SELECT min(ts)::VARCHAR, max(ts)::VARCHAR FROM llm_calls").fetchone()
    add("info:llm_ts_min_max", None, list(mm))
    oow_days = con.execute(
        f"SELECT date_trunc('day', ts)::VARCHAR AS d, count(*) FROM llm_calls "
        f"WHERE ts < TIMESTAMPTZ '{w0} 00:00:00+00' OR ts >= TIMESTAMPTZ '{w1} 00:00:00+00' "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 20").fetchall()
    add("info:outside_window_by_day_top20", None, oow_days)

    add("anomaly:cached_gt_prompt", None, _one(con, "SELECT count(*) FROM llm_calls WHERE tokens_cached > tokens_prompt"))
    add("anomaly:total_ne_prompt_plus_completion", None,
        _one(con, "SELECT count(*) FROM llm_calls WHERE tokens_total <> tokens_prompt + tokens_completion"))
    r = con.execute("SELECT min(cached_pct), max(cached_pct) FROM llm_calls").fetchone()
    add("info:cached_pct_min_max (scale 0-1 or 0-100?)", None, list(r))

    # Cross-turn tool-batch references + timestamp semantics, per day (bounded memory)
    total_b = matched = cross = unmatched = 0
    ge_start = ge_end = n_pairs = 0
    for day in cfg.days:
        r = con.execute(f"""
          SELECT count(*),
                 count(*) FILTER (WHERE c.turn_idx IS NOT NULL),
                 count(*) FILTER (WHERE c.turn_idx IS NOT NULL AND c.turn_idx <> b.turn_idx),
                 count(*) FILTER (WHERE c.turn_idx IS NULL),
                 count(*) FILTER (WHERE c.ts IS NOT NULL AND b.ts >= c.ts),
                 count(*) FILTER (WHERE c.ts IS NOT NULL AND b.ts >= c.ts
                                  + to_milliseconds(CAST(greatest(coalesce(c.duration_ms,0),0) AS BIGINT)))
          FROM (SELECT * FROM tool_batches WHERE CAST(archive_date AS VARCHAR) = '{day}') b
          LEFT JOIN (SELECT * FROM llm_calls WHERE CAST(archive_date AS VARCHAR) = '{day}') c
            ON b.session_id = c.session_id AND b.request_id = c.message_id
        """).fetchone()
        total_b += r[0]; matched += r[1]; cross += r[2]; unmatched += r[3]; ge_start += r[4]; ge_end += r[5]
    n_pairs = matched
    pct_all = 100.0 * cross / total_b if total_b else 0.0
    note = ""
    if "cross_turn_tool_batch_pct" in ur:
        note = f"team audit reported {ur['cross_turn_tool_batch_pct']}% (unconfirmed by Claude)"
    add("anomaly:cross_turn_tool_batch_refs", None, dict(cross=cross, of_all_batches=total_b,
        pct_of_all=round(pct_all, 4), matched=matched, unmatched=unmatched), note=note)
    add("probe:tool_batch_ts>=its_llm_call_ts", None,
        dict(share=round(ge_start / n_pairs, 4) if n_pairs else None, pairs=n_pairs),
        note="supports 'timestamp = start' if ~1.0")
    add("probe:tool_batch_ts>=llm_call_end", None,
        dict(share=round(ge_end / n_pairs, 4) if n_pairs else None, pairs=n_pairs),
        note="tells whether batch starts after the call ends")

    for tbl, col in [("llm_calls","tokens_prompt"),("llm_calls","tokens_total"),("llm_calls","tokens_cached"),
                     ("llm_calls","duration_ms"),("llm_calls","n_segments"),("tool_batches","duration_ms"),
                     ("tool_batches","auto_continue")]:
        add(f"null:{tbl}.{col}", None, _one(con, f"SELECT count(*) FROM {tbl} WHERE {col} IS NULL"))
    add("info:tool_call_status_values", None, con.execute("SELECT status, count(*) FROM tool_calls GROUP BY 1 ORDER BY 2 DESC").fetchall())
    add("info:llm_result_values", None, con.execute("SELECT result, count(*) FROM llm_calls GROUP BY 1 ORDER BY 2 DESC").fetchall())
    add("info:null_token_calls_by_result", None, con.execute("SELECT result, count(*) FROM llm_calls WHERE tokens_prompt IS NULL GROUP BY 1").fetchall())

    fails = [c for c in checks if c["status"] == "FAIL"]
    result = dict(counts=counts, checks=checks, n_fail=len(fails))
    cfg.outputs.mkdir(parents=True, exist_ok=True)
    (cfg.outputs / "validation.json").write_text(json.dumps(result, indent=2, default=str))
    con.close()
    return result


def _flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flatten(v, f"{prefix}{k}."))
    elif isinstance(d, list):
        out[prefix.rstrip(".")] = len(d)
    else:
        out[prefix.rstrip(".")] = d
    return out
