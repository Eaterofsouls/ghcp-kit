-- Prompt composition from message_metadata segments, plus context growth.
-- @@ csv:prompt_composition_by_type
SELECT seg_type, role, count(*) AS n_segments, sum(token_len) AS tokens,
       sum(token_len)::DOUBLE / sum(sum(token_len)) OVER () AS share_of_segment_tokens
FROM prompt_segments GROUP BY seg_type, role ORDER BY tokens DESC;

-- @@ csv:prompt_composition_by_call_position
WITH s AS (
  SELECT CASE WHEN call_idx = 1 THEN 1 WHEN call_idx <= 5 THEN 2 WHEN call_idx <= 20 THEN 3 ELSE 4 END AS ord,
         seg_type, token_len
  FROM prompt_segments)
SELECT CASE ord WHEN 1 THEN '1' WHEN 2 THEN '2-5' WHEN 3 THEN '6-20' ELSE '21+' END AS call_position_in_turn,
       ord, seg_type, sum(token_len) AS tokens,
       sum(token_len)::DOUBLE / sum(sum(token_len)) OVER (PARTITION BY ord) AS share_within_position
FROM s GROUP BY ord, seg_type ORDER BY ord, tokens DESC;

-- @@ csv:segment_vs_prompt_token_coverage
SELECT (SELECT sum(token_len) FROM prompt_segments) AS segment_tokens,
       (SELECT sum(tokens_prompt) FROM llm_calls) AS prompt_tokens,
       (SELECT sum(token_len) FROM prompt_segments)::DOUBLE /
       nullif((SELECT sum(tokens_prompt) FROM llm_calls), 0) AS segment_to_prompt_ratio;

-- @@ csv:context_growth_by_call_position
SELECT least(call_idx, 30) AS call_idx_capped, count(*) AS n_calls,
       avg(tokens_prompt) AS mean_prompt_tokens, quantile_cont(tokens_prompt, 0.5) AS p50_prompt_tokens,
       avg(tokens_completion) AS mean_completion_tokens
FROM llm_calls GROUP BY 1 ORDER BY 1;

-- @@ csv:context_growth_by_turn_position
SELECT least(turn_idx, 20) AS turn_idx_capped, count(*) AS n_calls,
       avg(tokens_prompt) AS mean_prompt_tokens, quantile_cont(tokens_prompt, 0.5) AS p50_prompt_tokens
FROM llm_calls GROUP BY 1 ORDER BY 1;
