-- Cache utilisation. `tokens_cached` semantics are NOT defined in schema.json: treat as "cached prompt
-- tokens as reported by the publisher". Shares are computed from token counts, not from cached_pct.
-- @@ csv:cache_overall
SELECT count(*) AS n_calls, sum(tokens_prompt) AS prompt_tokens, sum(tokens_cached) AS cached_tokens,
       sum(tokens_cached)::DOUBLE / nullif(sum(tokens_prompt), 0) AS cached_share_token_weighted,
       avg(CASE WHEN tokens_prompt > 0 THEN tokens_cached::DOUBLE / tokens_prompt END) AS mean_call_cached_share,
       count(*) FILTER (WHERE tokens_cached = 0)::DOUBLE / nullif(count(tokens_cached), 0) AS share_calls_zero_cache,
       count(tokens_prompt) AS n_calls_with_prompt_tokens, count(tokens_cached) AS n_calls_with_cached_tokens,
       count(*) FILTER (WHERE tokens_cached > tokens_prompt) AS calls_cached_gt_prompt
FROM llm_calls;

-- @@ csv:cache_by_initiator
SELECT initiator_type, count(*) AS n_calls, sum(tokens_prompt) AS prompt_tokens,
       sum(tokens_cached)::DOUBLE / nullif(sum(tokens_prompt), 0) AS cached_share
FROM llm_calls GROUP BY initiator_type ORDER BY n_calls DESC;

-- @@ csv:cache_by_call_position
SELECT CASE WHEN call_idx = 1 THEN '1' WHEN call_idx = 2 THEN '2' WHEN call_idx = 3 THEN '3'
            WHEN call_idx <= 5 THEN '4-5' WHEN call_idx <= 10 THEN '6-10'
            WHEN call_idx <= 20 THEN '11-20' ELSE '21+' END AS call_position_in_turn,
       min(call_idx) AS ord, count(*) AS n_calls, sum(tokens_prompt) AS prompt_tokens,
       sum(tokens_cached)::DOUBLE / nullif(sum(tokens_prompt), 0) AS cached_share
FROM llm_calls GROUP BY 1 ORDER BY ord;

-- @@ csv:cache_by_turn_position
SELECT CASE WHEN turn_idx = 1 THEN '1' WHEN turn_idx = 2 THEN '2' WHEN turn_idx = 3 THEN '3'
            WHEN turn_idx <= 5 THEN '4-5' WHEN turn_idx <= 10 THEN '6-10' ELSE '11+' END AS turn_position_in_session,
       min(turn_idx) AS ord, count(*) AS n_calls, sum(tokens_prompt) AS prompt_tokens,
       sum(tokens_cached)::DOUBLE / nullif(sum(tokens_prompt), 0) AS cached_share
FROM llm_calls GROUP BY 1 ORDER BY ord;

-- @@ csv:cache_by_model
SELECT model, count(*) AS n_calls, sum(tokens_prompt) AS prompt_tokens, sum(tokens_completion) AS completion_tokens,
       sum(tokens_cached)::DOUBLE / nullif(sum(tokens_prompt), 0) AS cached_share,
       avg(duration_ms) AS mean_duration_ms
FROM llm_calls GROUP BY model ORDER BY prompt_tokens DESC;

-- @@ csv:cache_by_session_size
SELECT CASE WHEN m.n_calls <= 10 THEN 'a: 1-10 calls' WHEN m.n_calls <= 50 THEN 'b: 11-50'
            WHEN m.n_calls <= 200 THEN 'c: 51-200' WHEN m.n_calls <= 1000 THEN 'd: 201-1000'
            ELSE 'e: >1000' END AS session_size_bucket,
       count(DISTINCT m.session_id) AS n_sessions, count(*) AS n_calls, sum(l.tokens_prompt) AS prompt_tokens,
       sum(l.tokens_cached)::DOUBLE / nullif(sum(l.tokens_prompt), 0) AS cached_share
FROM llm_calls l JOIN session_metrics m USING (session_id)
GROUP BY 1 ORDER BY 1;

-- @@ csv:cache_share_histogram
SELECT least(floor(10 * tokens_cached::DOUBLE / tokens_prompt), 9)::INT AS decile_of_cached_share,
       count(*) AS n_calls, sum(tokens_prompt) AS prompt_tokens
FROM llm_calls WHERE tokens_prompt > 0 AND tokens_cached >= 0 AND tokens_cached <= tokens_prompt
GROUP BY 1 ORDER BY 1;
