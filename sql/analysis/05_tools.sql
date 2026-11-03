-- Tool usage and sequences. status: 1 = success, 2 = failure/timeout (schema.json).
-- @@ csv:tool_usage
SELECT name, count(*) AS calls,
       count(*) FILTER (WHERE status = 2)::DOUBLE / count(*) AS fail_rate,
       quantile_cont(duration_ms, 0.5) AS p50_ms, quantile_cont(duration_ms, 0.95) AS p95_ms,
       sum(duration_ms) AS total_ms
FROM tool_calls GROUP BY name ORDER BY calls DESC;

-- @@ csv:tool_status_values
SELECT status, count(*) AS n FROM tool_calls GROUP BY status ORDER BY n DESC;

-- @@ csv:tool_batch_summary
SELECT count(*) AS n_batches, avg(n_calls) AS mean_calls_per_batch,
       quantile_cont(n_calls, 0.99) AS p99_calls_per_batch, max(n_calls) AS max_calls_per_batch,
       avg(auto_continue::INT) AS auto_continue_share,
       quantile_cont(duration_ms, 0.5) AS p50_ms, quantile_cont(duration_ms, 0.95) AS p95_ms
FROM tool_batches;

-- @@ csv:tool_batch_results
SELECT result, count(*) AS n FROM tool_batches GROUP BY result ORDER BY n DESC;

-- @@ csv:turn_tool_call_distribution
SELECT least(n_tool_batches, 50) AS batches_in_turn_capped, count(*) AS n_turns
FROM turns GROUP BY 1 ORDER BY 1;

-- @@ exec tool_seq
CREATE OR REPLACE TEMP TABLE tool_seq AS
SELECT session_id, turn_idx, list(name ORDER BY batch_idx, call_idx) AS seq
FROM tool_calls GROUP BY session_id, turn_idx;

-- @@ csv:tool_transitions_top
WITH p AS (SELECT list_concat(['<START>'], seq, ['<END>']) AS s FROM tool_seq),
e AS (
  SELECT s[i] AS from_tool, s[i + 1] AS to_tool
  FROM (SELECT s, unnest(range(1, len(s))) AS i FROM p)
)
SELECT from_tool, to_tool, count(*) AS n FROM e GROUP BY from_tool, to_tool ORDER BY n DESC LIMIT 60;

-- @@ csv:tool_sequences_top
SELECT array_to_string(list_slice(seq, 1, 6), ' > ') AS first_six_tools, count(*) AS n_turns
FROM tool_seq GROUP BY 1 ORDER BY n_turns DESC LIMIT 30;
