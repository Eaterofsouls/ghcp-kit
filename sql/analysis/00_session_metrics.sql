-- Per-session rollup used by concentration, cache-by-session-size and sensitivity analyses.
-- Views available: sessions, turns, llm_calls, prompt_segments, tool_batches, tool_calls
-- (hive column archive_date = day). Nothing is filtered: negative values etc. are kept.
-- @@ exec session_metrics
CREATE OR REPLACE TABLE session_metrics AS
WITH c AS (
  SELECT session_id, count(*) AS n_calls,
         sum(tokens_prompt) AS prompt_tokens, sum(tokens_completion) AS completion_tokens,
         sum(tokens_cached) AS cached_tokens, sum(duration_ms) AS llm_ms
  FROM llm_calls GROUP BY session_id),
b AS (
  SELECT session_id, count(*) AS n_tool_batches, sum(duration_ms) AS tool_ms, sum(n_calls) AS n_tool_calls
  FROM tool_batches GROUP BY session_id),
f AS (
  SELECT session_id, count(*) FILTER (WHERE status = 2) AS n_tool_fail
  FROM tool_calls GROUP BY session_id)
SELECT s.session_id, s.n_turns,
       coalesce(c.n_calls, 0) AS n_calls,
       coalesce(c.prompt_tokens, 0) AS prompt_tokens,
       coalesce(c.completion_tokens, 0) AS completion_tokens,
       coalesce(c.cached_tokens, 0) AS cached_tokens,
       coalesce(c.llm_ms, 0) AS llm_ms,
       coalesce(b.n_tool_batches, 0) AS n_tool_batches,
       coalesce(b.tool_ms, 0) AS tool_ms,
       coalesce(b.n_tool_calls, 0) AS n_tool_calls,
       coalesce(f.n_tool_fail, 0) AS n_tool_fail
FROM sessions s
LEFT JOIN c USING (session_id)
LEFT JOIN b USING (session_id)
LEFT JOIN f USING (session_id);
