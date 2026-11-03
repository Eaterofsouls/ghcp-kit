# SPEC — Full-corpus analysis of the GitHub Copilot agentic-session trace (7 days)

## 1. Goal
Run the pre-defined analytics on the **full seven-day** released sample using a bounded-memory
DuckDB pipeline, validate it against the publisher's counts, and produce a metrics report, validated
Parquet tables, reproducible scripts, benchmark results and aggregate figures.

**Research question:** In the released June 2026 GitHub Copilot agentic-session sample, how concentrated
is token consumption, how does prompt-cache reuse vary within and across turns, and what share of
session time is spent on LLM calls, tool execution and idle gaps?

## 2. Input (read-only)
Seven archives from `https://github.com/Azure/AzurePublicDataset/releases/download/ghcp-coding-agent-2026/date.<YYYY-MM-DD>.tar.gz`,
each containing `date=<day>/manifest.json` and numbered `shard-NNNN.jsonl.gz` (≈500 sessions each).
Sizes are in `ghcp/config.py` (total 3,218,886,136 bytes). One JSON object per line = one session:

```
session_id, date, turns[ { turn_id,
   llm_calls[ { message_id, timestamp, duration_ms, initiator_type ('user'|'agent'), model, result, status_code,
                tokens{total,prompt,completion,cached,cached_pct},
                message_metadata[ {type, role, sequenceId, token_len} ] } ],
   tool_batches[ { timestamp, duration_ms, auto_continue, result, request_id (= an llm_calls.message_id),
                   function_calls[ {name, status (1 ok, 2 fail/timeout), duration_ms} ] } ] } ]
```

## 3. Output tables (Parquet, ZSTD, one file per shard, hive-partitioned `archive_date=<day>`)
| table | grain | key columns |
|---|---|---|
| sessions | session | session_id, session_date, shard, n_turns |
| turns | turn | session_id, turn_idx, turn_id, n_llm_calls, n_tool_batches |
| llm_calls | LLM call | session_id, turn_idx, call_idx, message_id, ts_raw, ts, duration_ms, initiator_type, model, result, status_code, tokens_total/prompt/completion/cached, cached_pct, n_segments |
| prompt_segments | prompt segment | session_id, turn_idx, call_idx, message_id, seg_type, role, sequence_id, token_len |
| tool_batches | tool batch | session_id, turn_idx, batch_idx, request_id, ts_raw, ts, duration_ms, auto_continue, result, n_calls |
| tool_calls | tool call | session_id, turn_idx, batch_idx, request_id, call_idx, name, status, duration_ms |

`turn_idx`, `call_idx`, `batch_idx` are 1-based list positions. `ts_raw` keeps the original string; `ts`
is `TRY_CAST` to TIMESTAMPTZ (NULL if unparseable — counted by validation, never dropped).

## 4. Validation (must be run; see `ghcp/validate.py`)
Reconcile with `DATASET_CARD.md`: sessions 301,026 · turns 1,189,581 · LLM calls 9,310,255 ·
tool batches 7,767,261 · tool calls 8,681,190 · 37 distinct models · prompt ≈631.4B / completion ≈4.91B /
cached ≈540.95B tokens (rounded by publisher → 0.15% tolerance). Also: checkpoint state = Parquet counts,
no duplicate ids, per-day manifest counts (format unknown: inspect).
**Report, don't remove:** negative durations, cross-turn tool-batch references, timestamps outside
2026-06-01..07 UTC, cached>prompt, total≠prompt+completion, cached_pct scale.
The team's own audit reported 4 negative LLM latencies and 0.98% cross-turn references: **confirm or
contradict with the full-data counts**; do not assume.

## 5. Analyses (all in `sql/analysis/`, one CSV per `-- @@ csv:name` chunk in `outputs\`)
1. **Concentration** — per-session prompt/uncached/cached/completion tokens, calls, LLM ms: top 1/5/10/20/50% share, Gini = 2Σ(i·xᵢ)/(nΣx) − (n+1)/n (ascending rank i), 100-point Lorenz.
2. **Cache** — Σcached/Σprompt overall, by initiator_type, call position in turn, turn position in session, model, session size; zero-cache share; decile histogram.
3. **Time** — per turn: span = min(ts) → max(ts+duration); LLM ms, tool ms, residual = span − LLM − tool; idle gap = next turn start − this turn end. Assumption [A]: `timestamp` is event start (validation probes it).
4. **Prompt composition** — segment tokens by (type, role) and by call position; segment-token / prompt-token coverage; context growth by call/turn position.
5. **Tools** — usage, failure rate (status=2), p50/p95 duration; batch parallelism; auto_continue share; top 60 transitions incl. `<START>/<END>`; top 30 first-six-tool sequences.
6. **Hypothetical sensitivity** — relative index `(prompt−cached) + r·cached + k·completion`, r∈{0,.1,.25,.5,1}, k∈{1,3,5,8}. Unitless. No currency.
7. **Benchmark** — DuckDB vs Polars on 3 queries × {1,3,7} days × 3 repeats; wall time and peak RSS per run; result checksums must agree.

## 6. Success criteria (all must be evidenced)
- S1 self-test: all checks PASS on the fake fixture.
- S2 schema probe on the real 2026-06-06 archive: `missing_paths`, `extra_paths`, `types` all empty (else fix `sql/ingest_shard.sql` surgically and re-probe).
- S3 pilot (2026-06-06): peak RSS ≤ 1500 MB, projected total disk ≤ 15 GB (formula in PLAN.md).
- S4 full ingest: 7 days checkpointed, zero FAIL in validation for published counts.
- S5 every CSV in §5 exists; `analysis_timings.csv` shows no failed step.
- S6 `reports\seven_day_metrics.md`, `figures\*.png`, `outputs_bundle.zip` exist.
- Resource log (`logs\perf.csv`) shows no breach of the limits in `ghcp/config.py`.

## 7. Non-goals
Spark, dashboards/web apps, ML models, dollar costs, quality/productivity claims, enterprise-user
claims, any other dataset, restructuring the research question.
