"""S7b: READ-ONLY diagnostics #2 (nothing modified or removed).
Run: python -m ghcp.diag_s7b      Writes <outputs>/diag_s7b.json and prints it.
A outliers   : how much summed time comes from implausible durations (>1h, >24h, negative)
B null tokens: which model/result the 255,086 null-token calls belong to
C unmatched  : tool batches whose request_id matches no llm_call in the session (0.95%): what are they?
D seg types  : why 'Context'/'user' appears twice in prompt_composition_by_type
E status 0   : which tools carry the undocumented tool-call status 0
"""
from __future__ import annotations

import json

from .config import Config
from .db import connect, create_views
from .monitor import Guard


def main() -> int:
    cfg = Config.from_env()
    cfg.ensure_dirs()
    out: dict = {}
    with Guard(cfg, "diag_s7b") as g:
        con = connect(cfg)
        g.register(con)
        create_views(con, cfg)

        rows = []
        for src in ("llm_calls", "tool_batches", "tool_calls"):
            r = con.execute(f"""
              SELECT count(*), sum(duration_ms),
                     count(*) FILTER (WHERE duration_ms > 3600000),  sum(duration_ms) FILTER (WHERE duration_ms > 3600000),
                     count(*) FILTER (WHERE duration_ms > 86400000), sum(duration_ms) FILTER (WHERE duration_ms > 86400000),
                     count(*) FILTER (WHERE duration_ms < 0),        sum(duration_ms) FILTER (WHERE duration_ms < 0)
              FROM {src}""").fetchone()
            tot = r[1] or 0
            rows.append(dict(table=src, n=r[0], sum_ms=tot,
                             n_gt_1h=r[2], sum_gt_1h_ms=r[3], share_gt_1h=(r[3] or 0) / tot if tot else None,
                             n_gt_24h=r[4], sum_gt_24h_ms=r[5], share_gt_24h=(r[5] or 0) / tot if tot else None,
                             n_negative=r[6], sum_negative_ms=r[7]))
        out["A_duration_outlier_contribution"] = rows

        out["B_null_token_calls_by_model_kind_and_result"] = [
            dict(is_tool_model=r[0], result=r[1], n=r[2]) for r in con.execute(
                "SELECT model = 'tool-model', result, count(*) FROM llm_calls "
                "WHERE tokens_prompt IS NULL GROUP BY 1, 2 ORDER BY 3 DESC").fetchall()]

        c = {}
        for day in cfg.days:
            w = f"CAST(archive_date AS VARCHAR) = '{day}'"
            for r in con.execute(f"""
              WITH b AS (SELECT session_id, turn_idx, batch_idx, request_id, n_calls, result
                         FROM tool_batches WHERE {w}),
                   m AS (SELECT DISTINCT session_id, message_id FROM llm_calls WHERE {w} AND message_id IS NOT NULL),
                   j AS (SELECT b.session_id, b.turn_idx, b.batch_idx, any_value(b.n_calls) AS n_calls,
                                any_value(b.result) AS result, count(m.message_id) AS n_match
                         FROM b LEFT JOIN m ON b.session_id = m.session_id AND b.request_id = m.message_id
                         GROUP BY b.session_id, b.turn_idx, b.batch_idx)
              SELECT n_calls = 0 AS empty_batch, result, turn_idx = 1 AS first_turn, count(*)
              FROM j WHERE n_match = 0 GROUP BY 1, 2, 3""").fetchall():
                key = (r[0], r[1], r[2])
                c[key] = c.get(key, 0) + r[3]
        out["C_unmatched_batches_by_empty_result_firstturn"] = [
            dict(empty_batch=k[0], result=k[1], first_turn=k[2], n=v)
            for k, v in sorted(c.items(), key=lambda kv: -kv[1])]

        out["D_prompt_segment_types"] = [
            dict(seg_type=r[0], role=r[1], len=r[2], hex=r[3], n=r[4], tokens=r[5]) for r in con.execute(
                "SELECT seg_type, role, length(seg_type), hex(seg_type), count(*), sum(token_len) "
                "FROM prompt_segments GROUP BY 1, 2, 3, 4 ORDER BY 5 DESC").fetchall()]

        out["E_status0_by_tool"] = [dict(name=r[0], status0=r[1], calls=r[2]) for r in con.execute(
            "SELECT name, count(*) FILTER (WHERE status = 0), count(*) FROM tool_calls "
            "GROUP BY name HAVING count(*) FILTER (WHERE status = 0) > 0 ORDER BY 2 DESC LIMIT 15").fetchall()]
        con.close()

    cfg.outputs.mkdir(parents=True, exist_ok=True)
    (cfg.outputs / "diag_s7b.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
