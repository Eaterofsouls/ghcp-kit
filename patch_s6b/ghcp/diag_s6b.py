"""S6b: READ-ONLY diagnostics on the ingested Parquet. Nothing is modified or removed.

Run:  python -m ghcp.diag_s6b
Writes: <outputs>/diag_s6b.json and prints the same JSON.
Why: validate.py joined tool_batches to llm_calls on (session_id, message_id) and message_id is NOT unique
per call, so its cross-turn count and timestamp probes were computed on a fanned-out join. These
diagnostics (1) establish what message_id is, (2) recount cross-turn references per BATCH,
(3) probe timestamp semantics without an ambiguous join, (4) list every negative duration,
(5) list all models, (6) split out-of-window timestamps (UTC).
Per-day loops keep memory bounded.
"""
from __future__ import annotations

import json

from .config import Config
from .db import connect, create_views
from .monitor import Guard

W0, W1 = "2026-06-01", "2026-06-08"          # window, UTC, end exclusive
NEAR0, NEAR1 = "2026-05-31", "2026-06-09"    # 'far' = more than 1 day outside the window


def main() -> int:
    cfg = Config.from_env()
    cfg.ensure_dirs()
    out: dict = {}
    with Guard(cfg, "diag_s6b") as g:
        con = connect(cfg)
        g.register(con)
        create_views(con, cfg)
        con.execute("SET TimeZone='UTC'")  # redundant with db.connect, kept so this file is self-contained

        # D1 - what is message_id? (per day)
        d1 = []
        for day in cfg.days:
            w = f"CAST(archive_date AS VARCHAR) = '{day}'"
            r = con.execute(f"""
              SELECT count(*),
                     count(*) FILTER (WHERE message_id IS NULL),
                     count(DISTINCT message_id),
                     (SELECT count(*) FROM (SELECT DISTINCT session_id, message_id FROM llm_calls WHERE {w})),
                     (SELECT count(*) FROM (SELECT DISTINCT session_id, turn_idx, message_id FROM llm_calls WHERE {w})),
                     (SELECT count(*) FROM (SELECT DISTINCT session_id, turn_idx FROM llm_calls WHERE {w})),
                     count(*) FILTER (WHERE message_id = turn_id),
                     (SELECT quantile_cont(n, 0.5) FROM (SELECT count(*) n FROM llm_calls WHERE {w}
                                                         GROUP BY session_id, turn_idx, message_id)),
                     (SELECT max(n) FROM (SELECT count(*) n FROM llm_calls WHERE {w}
                                          GROUP BY session_id, turn_idx, message_id))
              FROM llm_calls WHERE {w}""").fetchone()
            d1.append(dict(day=day, n_calls=r[0], null_message_id=r[1], distinct_message_id=r[2],
                           distinct_session_message_id=r[3], distinct_session_turn_message_id=r[4],
                           distinct_session_turn=r[5], message_id_equals_turn_id=r[6],
                           median_calls_per_turn_message_id=r[7], max_calls_per_turn_message_id=r[8]))
        out["D1_message_id_structure"] = d1

        # D2 - cross-turn references counted per BATCH (message_id collapsed to distinct session/message/turn)
        d2 = []
        for day in cfg.days:
            w = f"CAST(archive_date AS VARCHAR) = '{day}'"
            r = con.execute(f"""
              WITH b AS (SELECT session_id, turn_idx, batch_idx, request_id, n_calls FROM tool_batches WHERE {w}),
                   m AS (SELECT DISTINCT session_id, message_id, turn_idx FROM llm_calls
                         WHERE {w} AND message_id IS NOT NULL),
                   j AS (SELECT b.session_id, b.turn_idx, b.batch_idx, any_value(b.n_calls) AS n_calls,
                                coalesce(bool_or(m.turn_idx = b.turn_idx), false) AS same_turn,
                                coalesce(bool_or(m.turn_idx <> b.turn_idx), false) AS other_turn
                         FROM b LEFT JOIN m ON b.session_id = m.session_id AND b.request_id = m.message_id
                         GROUP BY b.session_id, b.turn_idx, b.batch_idx)
              SELECT count(*),
                     count(*) FILTER (WHERE same_turn AND NOT other_turn),
                     count(*) FILTER (WHERE other_turn AND NOT same_turn),
                     count(*) FILTER (WHERE same_turn AND other_turn),
                     count(*) FILTER (WHERE NOT same_turn AND NOT other_turn),
                     count(*) FILTER (WHERE n_calls > 0),
                     count(*) FILTER (WHERE n_calls > 0 AND other_turn AND NOT same_turn),
                     count(*) FILTER (WHERE n_calls > 0 AND other_turn)
              FROM j""").fetchone()
            d2.append(dict(day=day, batches=r[0], same_turn_only=r[1], other_turn_only=r[2], both=r[3],
                           unmatched=r[4], nonempty_batches=r[5], nonempty_other_turn_only=r[6],
                           nonempty_any_other_turn=r[7]))
        tot = {k: sum(x[k] for x in d2) for k in d2[0] if k != "day"}
        tot["pct_other_turn_only_of_batches"] = round(100.0 * tot["other_turn_only"] / tot["batches"], 4)
        tot["pct_any_other_turn_of_batches"] = round(100.0 * (tot["other_turn_only"] + tot["both"]) / tot["batches"], 4)
        tot["pct_nonempty_any_other_turn_of_nonempty"] = round(
            100.0 * tot["nonempty_any_other_turn"] / tot["nonempty_batches"], 4)
        out["D2_cross_turn_per_batch"] = dict(per_day=d2, total=tot)

        # D3 - timestamp semantics from consecutive llm_calls in a turn (no message_id join)
        d3 = []
        for day in cfg.days:
            w = f"CAST(archive_date AS VARCHAR) = '{day}'"
            r = con.execute(f"""
              WITH x AS (
                SELECT ts, greatest(coalesce(duration_ms, 0), 0) AS d,
                       lag(ts) OVER (PARTITION BY session_id, turn_idx ORDER BY call_idx) AS p_ts,
                       lag(greatest(coalesce(duration_ms, 0), 0))
                           OVER (PARTITION BY session_id, turn_idx ORDER BY call_idx) AS p_d
                FROM llm_calls WHERE {w} AND ts IS NOT NULL),
              y AS (SELECT date_diff('millisecond', p_ts, ts) AS gap, d, p_d FROM x WHERE p_ts IS NOT NULL)
              SELECT count(*),
                     count(*) FILTER (WHERE gap < 0),
                     count(*) FILTER (WHERE gap - p_d < 0),
                     count(*) FILTER (WHERE gap - d < 0)
              FROM y""").fetchone()
            d3.append(dict(day=day, pairs=r[0], ts_goes_backwards=r[1],
                           violates_if_ts_is_start=r[2], violates_if_ts_is_end=r[3]))
        t = {k: sum(x[k] for x in d3) for k in d3[0] if k != "day"}
        t["share_violates_if_ts_is_start"] = round(t["violates_if_ts_is_start"] / t["pairs"], 5) if t["pairs"] else None
        t["share_violates_if_ts_is_end"] = round(t["violates_if_ts_is_end"] / t["pairs"], 5) if t["pairs"] else None
        out["D3_timestamp_semantics_consecutive_calls"] = dict(per_day=d3, total=t,
            reading="start: next call should begin after prev ts+dur (gap>=prev dur). end: next call's ts-dur should be after prev ts (gap>=own dur). The semantics with the clearly lower violation share is better supported; similar shares = undetermined.")

        # D4 - batch vs call timestamp, only unambiguous pairs (message_id has exactly 1 call in that turn)
        d4 = []
        for day in cfg.days:
            w = f"CAST(archive_date AS VARCHAR) = '{day}'"
            wb = f"CAST(b.archive_date AS VARCHAR) = '{day}'"
            r = con.execute(f"""
              WITH c AS (SELECT session_id, turn_idx, message_id, any_value(ts) AS ts,
                                any_value(greatest(coalesce(duration_ms, 0), 0)) AS d
                         FROM llm_calls WHERE {w} AND message_id IS NOT NULL AND ts IS NOT NULL
                         GROUP BY session_id, turn_idx, message_id HAVING count(*) = 1)
              SELECT count(*),
                     count(*) FILTER (WHERE b.ts >= c.ts),
                     count(*) FILTER (WHERE b.ts >= c.ts + to_milliseconds(CAST(c.d AS BIGINT)))
              FROM tool_batches b JOIN c ON b.session_id = c.session_id AND b.turn_idx = c.turn_idx
                                         AND b.request_id = c.message_id
              WHERE {wb} AND b.ts IS NOT NULL""").fetchone()
            d4.append(dict(day=day, unambiguous_pairs=r[0], batch_ts_ge_call_ts=r[1], batch_ts_ge_call_ts_plus_dur=r[2]))
        out["D4_batch_vs_call_timestamp_unambiguous_pairs"] = dict(
            per_day=d4, total={k: sum(x[k] for x in d4) for k in d4[0] if k != "day"})

        # D5 - every model value
        out["D5_models"] = [dict(model=r[0], calls=r[1], null_token_calls=r[2], prompt_tokens=r[3])
                            for r in con.execute(
            "SELECT model, count(*), count(*) FILTER (WHERE tokens_prompt IS NULL), sum(tokens_prompt) "
            "FROM llm_calls GROUP BY model ORDER BY 2 DESC").fetchall()]

        # D6 - every negative duration, and duration extremes
        out["D6_negative_llm_calls"] = [list(map(str, r)) for r in con.execute(
            "SELECT archive_date, model, result, duration_ms, ts, tokens_prompt FROM llm_calls "
            "WHERE duration_ms < 0 ORDER BY duration_ms").fetchall()]
        out["D6_negative_tool_batches"] = [list(map(str, r)) for r in con.execute(
            "SELECT archive_date, turn_idx, batch_idx, duration_ms, ts, n_calls FROM tool_batches "
            "WHERE duration_ms < 0 ORDER BY duration_ms").fetchall()]
        out["D6_duration_extremes"] = dict(
            llm=con.execute("SELECT max(duration_ms), count(*) FILTER (WHERE duration_ms > 3600000), "
                            "quantile_cont(duration_ms, 0.99) FROM llm_calls").fetchone(),
            tool_batch=con.execute("SELECT max(duration_ms), count(*) FILTER (WHERE duration_ms > 3600000), "
                                   "quantile_cont(duration_ms, 0.99) FROM tool_batches").fetchone(),
            keys=["max_ms", "n_over_1h", "p99_ms"])

        # D7 - out-of-window timestamps in UTC: by month, near vs far
        far = f"(ts < TIMESTAMPTZ '{NEAR0} 00:00:00+00' OR ts >= TIMESTAMPTZ '{NEAR1} 00:00:00+00')"
        oow = f"(ts < TIMESTAMPTZ '{W0} 00:00:00+00' OR ts >= TIMESTAMPTZ '{W1} 00:00:00+00')"
        out["D7_oow_llm_by_utc_month"] = [list(map(str, r)) for r in con.execute(
            f"SELECT date_trunc('month', ts), count(*), count(DISTINCT session_id) FROM llm_calls "
            f"WHERE {oow} GROUP BY 1 ORDER BY 1").fetchall()]
        r = con.execute(f"SELECT count(*) FILTER (WHERE {oow} AND NOT {far}), count(*) FILTER (WHERE {far}), "
                        f"count(DISTINCT (session_id, turn_idx)) FILTER (WHERE {far}), "
                        f"count(DISTINCT session_id) FILTER (WHERE {far}) FROM llm_calls").fetchone()
        out["D7_oow_llm_near_vs_far"] = dict(near_within_1_day=r[0], far_more_than_1_day=r[1],
                                              far_distinct_turns=r[2], far_distinct_sessions=r[3])
        r = con.execute(f"SELECT count(*) FILTER (WHERE {oow} AND NOT {far}), count(*) FILTER (WHERE {far}) "
                        f"FROM tool_batches").fetchone()
        out["D7_oow_tool_batches_near_vs_far"] = dict(near_within_1_day=r[0], far_more_than_1_day=r[1])
        con.close()

    cfg.outputs.mkdir(parents=True, exist_ok=True)
    (cfg.outputs / "diag_s6b.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
