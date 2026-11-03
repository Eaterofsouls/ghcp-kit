-- Token / call / time concentration across sessions: top-x% shares, Gini, Lorenz curve.
-- @@ exec conc_base
CREATE OR REPLACE TEMP TABLE conc_base AS
          SELECT 'prompt_tokens' AS metric, session_id, prompt_tokens::DOUBLE AS v FROM session_metrics
UNION ALL SELECT 'uncached_prompt_tokens', session_id, (prompt_tokens - cached_tokens)::DOUBLE FROM session_metrics
UNION ALL SELECT 'cached_tokens', session_id, cached_tokens::DOUBLE FROM session_metrics
UNION ALL SELECT 'completion_tokens', session_id, completion_tokens::DOUBLE FROM session_metrics
UNION ALL SELECT 'llm_calls', session_id, n_calls::DOUBLE FROM session_metrics
UNION ALL SELECT 'llm_ms', session_id, llm_ms::DOUBLE FROM session_metrics;

-- @@ exec conc_ranked
CREATE OR REPLACE TEMP TABLE conc_ranked AS
SELECT metric, v,
       row_number() OVER (PARTITION BY metric ORDER BY v DESC) AS rk_desc,
       count(*) OVER (PARTITION BY metric) AS n,
       sum(v) OVER (PARTITION BY metric) AS tot
FROM conc_base;

-- @@ csv:concentration_top_shares
SELECT metric, p.pct AS top_pct_of_sessions, sum(v) / any_value(tot) AS share_of_total,
       any_value(n) AS n_sessions
FROM conc_ranked
JOIN (VALUES (1), (5), (10), (20), (50)) p(pct) ON rk_desc <= ceil(n * p.pct / 100.0)
GROUP BY metric, p.pct
ORDER BY metric, p.pct;

-- @@ csv:concentration_gini
SELECT metric,
       (2.0 * sum((n - rk_desc + 1) * v) / (any_value(n) * any_value(tot)))
         - (any_value(n) + 1.0) / any_value(n) AS gini,
       any_value(n) AS n_sessions, any_value(tot) AS total
FROM conc_ranked GROUP BY metric ORDER BY metric;

-- @@ csv:concentration_lorenz
WITH b AS (
  SELECT metric, v, ntile(100) OVER (PARTITION BY metric ORDER BY v) AS pctile FROM conc_base),
a AS (SELECT metric, pctile, sum(v) AS s FROM b GROUP BY metric, pctile)
SELECT metric, pctile AS session_percentile,
       sum(s) OVER (PARTITION BY metric ORDER BY pctile) / sum(s) OVER (PARTITION BY metric) AS cum_share
FROM a ORDER BY metric, pctile;

-- @@ csv:session_distribution
SELECT metric, count(*) AS n, avg(v) AS mean, min(v) AS min,
       quantile_cont(v, 0.5) AS p50, quantile_cont(v, 0.9) AS p90,
       quantile_cont(v, 0.99) AS p99, quantile_cont(v, 0.999) AS p999, max(v) AS max
FROM conc_base GROUP BY metric ORDER BY metric;
