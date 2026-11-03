-- Time decomposition per turn, v2 (replaces the v1 start-timestamp assumption).
-- EVIDENCE (diag_s6b D3): for consecutive llm_calls in a turn, "next call starts after previous call ends"
-- fails for 34.4% of pairs if timestamp = START, but only 0.06% if timestamp = END. So LLM-call timestamp
-- behaves like a COMPLETION time: interval = [ts - duration, ts].
-- Tool-batch timestamp semantics are NOT established (D4 had only 8,333 unambiguous pairs). Primary outputs
-- assume tool batch ts = END too (same logger convention, ASSUMPTION [A]); the *_toolstart outputs assume START.
-- Negative durations: kept in the llm_ms/tool_ms sums, clamped to 0 only when building intervals.
-- has_far_oow flags turns containing a timestamp >1 day outside 2026-06-01..07 UTC; flagged, never removed.
-- @@ exec turn_events
CREATE OR REPLACE TEMP VIEW turn_events AS
SELECT session_id, turn_idx, 'llm' AS kind, ts, duration_ms,
       greatest(coalesce(duration_ms, 0), 0) AS d FROM llm_calls WHERE ts IS NOT NULL
UNION ALL
SELECT session_id, turn_idx, 'tool' AS kind, ts, duration_ms,
       greatest(coalesce(duration_ms, 0), 0) AS d FROM tool_batches WHERE ts IS NOT NULL;

-- @@ exec turn_time
CREATE OR REPLACE TABLE turn_time AS
SELECT session_id, turn_idx,
       min(ts - to_milliseconds(CAST(d AS BIGINT))) AS t_start,
       max(ts) AS t_end,
       coalesce(sum(duration_ms) FILTER (WHERE kind = 'llm'), 0) AS llm_ms,
       coalesce(sum(duration_ms) FILTER (WHERE kind = 'tool'), 0) AS tool_ms,
       count(*) AS n_events,
       coalesce(bool_or(ts < TIMESTAMPTZ '2026-05-31 00:00:00+00'
                        OR ts >= TIMESTAMPTZ '2026-06-09 00:00:00+00'), false) AS has_far_oow
FROM turn_events GROUP BY session_id, turn_idx;

-- @@ exec turn_time2
CREATE OR REPLACE TABLE turn_time2 AS
SELECT *, date_diff('millisecond', t_start, t_end) AS span_ms,
       date_diff('millisecond', t_start, t_end) - llm_ms - tool_ms AS residual_ms,
       date_diff('millisecond', t_end,
                 lead(t_start) OVER (PARTITION BY session_id ORDER BY turn_idx)) AS idle_gap_ms,
       lead(has_far_oow) OVER (PARTITION BY session_id ORDER BY turn_idx) AS next_far_oow
FROM turn_time;

-- @@ exec turn_time_s
CREATE OR REPLACE TABLE turn_time_s AS
SELECT session_id, turn_idx,
       min(CASE kind WHEN 'llm' THEN ts - to_milliseconds(CAST(d AS BIGINT)) ELSE ts END) AS t_start,
       max(CASE kind WHEN 'llm' THEN ts ELSE ts + to_milliseconds(CAST(d AS BIGINT)) END) AS t_end,
       coalesce(sum(duration_ms) FILTER (WHERE kind = 'llm'), 0) AS llm_ms,
       coalesce(sum(duration_ms) FILTER (WHERE kind = 'tool'), 0) AS tool_ms,
       coalesce(bool_or(ts < TIMESTAMPTZ '2026-05-31 00:00:00+00'
                        OR ts >= TIMESTAMPTZ '2026-06-09 00:00:00+00'), false) AS has_far_oow
FROM turn_events GROUP BY session_id, turn_idx;

-- @@ exec turn_time_s2
CREATE OR REPLACE TABLE turn_time_s2 AS
SELECT *, date_diff('millisecond', t_start, t_end) AS span_ms,
       date_diff('millisecond', t_start, t_end) - llm_ms - tool_ms AS residual_ms
FROM turn_time_s;

-- @@ csv:time_decomposition_totals
SELECT count(*) AS n_turns, sum(span_ms) AS span_ms_total, sum(llm_ms) AS llm_ms_total,
       sum(tool_ms) AS tool_ms_total, sum(greatest(residual_ms, 0)) AS positive_residual_ms_total,
       sum(llm_ms)::DOUBLE / nullif(sum(span_ms), 0) AS llm_share_of_span,
       sum(tool_ms)::DOUBLE / nullif(sum(span_ms), 0) AS tool_share_of_span,
       sum(greatest(residual_ms, 0))::DOUBLE / nullif(sum(span_ms), 0) AS positive_residual_share,
       count(*) FILTER (WHERE residual_ms < 0) AS turns_negative_residual,
       count(*) FILTER (WHERE span_ms <= 0) AS turns_nonpositive_span,
       count(*) FILTER (WHERE llm_ms > span_ms) AS turns_llm_ms_exceeds_span
FROM turn_time2;

-- @@ csv:time_decomposition_percentiles
SELECT 'turn_span_s' AS quantity, quantile_cont(span_ms / 1000.0, 0.5) AS p50,
       quantile_cont(span_ms / 1000.0, 0.9) AS p90, quantile_cont(span_ms / 1000.0, 0.99) AS p99
FROM turn_time2 WHERE span_ms > 0
UNION ALL
SELECT 'llm_share_of_turn', quantile_cont(llm_ms::DOUBLE / span_ms, 0.5),
       quantile_cont(llm_ms::DOUBLE / span_ms, 0.9), quantile_cont(llm_ms::DOUBLE / span_ms, 0.99)
FROM turn_time2 WHERE span_ms > 0
UNION ALL
SELECT 'tool_share_of_turn', quantile_cont(tool_ms::DOUBLE / span_ms, 0.5),
       quantile_cont(tool_ms::DOUBLE / span_ms, 0.9), quantile_cont(tool_ms::DOUBLE / span_ms, 0.99)
FROM turn_time2 WHERE span_ms > 0;

-- @@ csv:idle_gap_between_turns
SELECT count(*) AS n_gaps, quantile_cont(idle_gap_ms / 1000.0, 0.5) AS p50_s,
       quantile_cont(idle_gap_ms / 1000.0, 0.9) AS p90_s, quantile_cont(idle_gap_ms / 1000.0, 0.99) AS p99_s,
       count(*) FILTER (WHERE idle_gap_ms < 0) AS negative_gaps,
       count(*) FILTER (WHERE idle_gap_ms > 60000) AS gaps_over_1min,
       count(*) FILTER (WHERE idle_gap_ms > 300000) AS gaps_over_5min,
       count(*) FILTER (WHERE idle_gap_ms > 1800000) AS gaps_over_30min,
       sum(idle_gap_ms) / 1000.0 AS idle_total_s
FROM turn_time2 WHERE idle_gap_ms IS NOT NULL;

-- @@ csv:time_decomposition_totals_excl_far_oow
SELECT count(*) AS n_turns, sum(span_ms) AS span_ms_total, sum(llm_ms) AS llm_ms_total,
       sum(tool_ms) AS tool_ms_total, sum(greatest(residual_ms, 0)) AS positive_residual_ms_total,
       sum(llm_ms)::DOUBLE / nullif(sum(span_ms), 0) AS llm_share_of_span,
       sum(tool_ms)::DOUBLE / nullif(sum(span_ms), 0) AS tool_share_of_span,
       sum(greatest(residual_ms, 0))::DOUBLE / nullif(sum(span_ms), 0) AS positive_residual_share,
       count(*) FILTER (WHERE residual_ms < 0) AS turns_negative_residual,
       count(*) FILTER (WHERE span_ms <= 0) AS turns_nonpositive_span,
       count(*) FILTER (WHERE llm_ms > span_ms) AS turns_llm_ms_exceeds_span
FROM turn_time2 WHERE NOT has_far_oow;

-- @@ csv:time_decomposition_percentiles_excl_far_oow
SELECT 'turn_span_s' AS quantity, quantile_cont(span_ms / 1000.0, 0.5) AS p50,
       quantile_cont(span_ms / 1000.0, 0.9) AS p90, quantile_cont(span_ms / 1000.0, 0.99) AS p99
FROM turn_time2 WHERE span_ms > 0 AND NOT has_far_oow
UNION ALL
SELECT 'llm_share_of_turn', quantile_cont(llm_ms::DOUBLE / span_ms, 0.5),
       quantile_cont(llm_ms::DOUBLE / span_ms, 0.9), quantile_cont(llm_ms::DOUBLE / span_ms, 0.99)
FROM turn_time2 WHERE span_ms > 0 AND NOT has_far_oow
UNION ALL
SELECT 'tool_share_of_turn', quantile_cont(tool_ms::DOUBLE / span_ms, 0.5),
       quantile_cont(tool_ms::DOUBLE / span_ms, 0.9), quantile_cont(tool_ms::DOUBLE / span_ms, 0.99)
FROM turn_time2 WHERE span_ms > 0 AND NOT has_far_oow;

-- @@ csv:idle_gap_between_turns_excl_far_oow
SELECT count(*) AS n_gaps, quantile_cont(idle_gap_ms / 1000.0, 0.5) AS p50_s,
       quantile_cont(idle_gap_ms / 1000.0, 0.9) AS p90_s, quantile_cont(idle_gap_ms / 1000.0, 0.99) AS p99_s,
       count(*) FILTER (WHERE idle_gap_ms < 0) AS negative_gaps,
       count(*) FILTER (WHERE idle_gap_ms > 60000) AS gaps_over_1min,
       count(*) FILTER (WHERE idle_gap_ms > 300000) AS gaps_over_5min,
       count(*) FILTER (WHERE idle_gap_ms > 1800000) AS gaps_over_30min,
       sum(idle_gap_ms) / 1000.0 AS idle_total_s
FROM turn_time2
WHERE idle_gap_ms IS NOT NULL AND NOT has_far_oow AND NOT coalesce(next_far_oow, false);

-- @@ csv:time_decomposition_totals_toolstart
SELECT count(*) AS n_turns, sum(span_ms) AS span_ms_total, sum(llm_ms) AS llm_ms_total,
       sum(tool_ms) AS tool_ms_total, sum(greatest(residual_ms, 0)) AS positive_residual_ms_total,
       sum(llm_ms)::DOUBLE / nullif(sum(span_ms), 0) AS llm_share_of_span,
       sum(tool_ms)::DOUBLE / nullif(sum(span_ms), 0) AS tool_share_of_span,
       sum(greatest(residual_ms, 0))::DOUBLE / nullif(sum(span_ms), 0) AS positive_residual_share,
       count(*) FILTER (WHERE residual_ms < 0) AS turns_negative_residual,
       count(*) FILTER (WHERE span_ms <= 0) AS turns_nonpositive_span,
       count(*) FILTER (WHERE llm_ms > span_ms) AS turns_llm_ms_exceeds_span
FROM turn_time_s2;

-- @@ csv:time_decomposition_totals_toolstart_excl_far_oow
SELECT count(*) AS n_turns, sum(span_ms) AS span_ms_total, sum(llm_ms) AS llm_ms_total,
       sum(tool_ms) AS tool_ms_total, sum(greatest(residual_ms, 0)) AS positive_residual_ms_total,
       sum(llm_ms)::DOUBLE / nullif(sum(span_ms), 0) AS llm_share_of_span,
       sum(tool_ms)::DOUBLE / nullif(sum(span_ms), 0) AS tool_share_of_span,
       sum(greatest(residual_ms, 0))::DOUBLE / nullif(sum(span_ms), 0) AS positive_residual_share,
       count(*) FILTER (WHERE residual_ms < 0) AS turns_negative_residual,
       count(*) FILTER (WHERE span_ms <= 0) AS turns_nonpositive_span,
       count(*) FILTER (WHERE llm_ms > span_ms) AS turns_llm_ms_exceeds_span
FROM turn_time_s2 WHERE NOT has_far_oow;
