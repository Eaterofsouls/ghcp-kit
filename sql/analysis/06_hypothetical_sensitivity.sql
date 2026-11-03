-- HYPOTHETICAL. RELATIVE UNITS ONLY. NOT MONEY.
-- We have no model identities and no billing data. Every number here is a what-if:
--   index = (prompt - cached) * 1.0  +  cached * r  +  completion * k
-- r = assumed price of a cached prompt token relative to an uncached one (1.0 = no discount)
-- k = assumed price of a completion token relative to an uncached prompt token
-- The same r and k are applied to all models (explicit simplifying assumption).
-- @@ csv:HYPOTHETICAL_cost_index_scenarios
WITH g AS (
  SELECT a.r AS r, b.k AS k
  FROM (VALUES (0.0), (0.1), (0.25), (0.5), (1.0)) a(r), (VALUES (1), (3), (5), (8)) b(k)),
x AS (
  SELECT g.r AS r, g.k AS k, s.session_id AS session_id,
         (s.prompt_tokens - s.cached_tokens) + g.r * s.cached_tokens + g.k * s.completion_tokens AS idx,
         s.prompt_tokens + g.k * s.completion_tokens AS no_cache_idx
  FROM session_metrics s CROSS JOIN g),
d AS (
  SELECT r, k, idx, ntile(10) OVER (PARTITION BY r, k ORDER BY idx DESC) AS decile FROM x),
tot AS (
  SELECT r, k, sum(idx) AS idx_total, sum(no_cache_idx) AS no_cache_total FROM x GROUP BY r, k),
top AS (
  SELECT r, k, sum(idx) AS top_idx FROM d WHERE decile = 1 GROUP BY r, k)
SELECT tot.r AS assumed_cached_price_ratio, tot.k AS assumed_completion_price_multiple,
       tot.idx_total AS hypothetical_index_total,
       tot.no_cache_total AS hypothetical_no_cache_index_total,
       1 - tot.idx_total / tot.no_cache_total AS hypothetical_caching_saving_fraction,
       top.top_idx / tot.idx_total AS hypothetical_top10pct_sessions_share
FROM tot JOIN top ON tot.r = top.r AND tot.k = top.k
ORDER BY tot.k, tot.r;
