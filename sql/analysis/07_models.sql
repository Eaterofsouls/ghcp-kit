-- Model labels are anonymised ("Model A", ...). No mapping to real models or prices exists.
-- @@ csv:model_share
SELECT model, count(*) AS n_calls,
       count(*)::DOUBLE / sum(count(*)) OVER () AS share_of_calls,
       sum(tokens_prompt)::DOUBLE / sum(sum(tokens_prompt)) OVER () AS share_of_prompt_tokens,
       sum(tokens_completion)::DOUBLE / sum(sum(tokens_completion)) OVER () AS share_of_completion_tokens,
       quantile_cont(duration_ms, 0.5) AS p50_duration_ms, quantile_cont(duration_ms, 0.95) AS p95_duration_ms,
       count(*) FILTER (WHERE result <> 'Success')::DOUBLE / count(*) AS non_success_share
FROM llm_calls GROUP BY model ORDER BY n_calls DESC;

-- @@ csv:llm_result_values
SELECT result, status_code, count(*) AS n FROM llm_calls GROUP BY result, status_code ORDER BY n DESC;
