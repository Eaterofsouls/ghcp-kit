# CHANGELOG_AGENT.md

The executing agent must log every edit to code or SQL here (one entry per change).

| time | file | statement/line | error text that triggered it | change | re-test result |
|---|---|---|---|---|---|
| 2026-10-31 17:24 | ghcp/validate.py | lines 150-157 | User request: Addition B | Added INFO checks for null columns, tool_call status values, llm result values, and null token calls by result | Passed (19/19 passed in selftest) |
| 2026-10-31 17:28 | sql/ingest_shard.sql | line 7 (`maximum_object_size=134217728`) | `_duckdb.OutOfMemoryException: Out of Memory Error: failed to allocate data of size 16.0 MiB (940.0 MiB/953.6 MiB used)` during chunk `exec load` on shard 0008 | Changed `maximum_object_size=134217728` to `33554432` (32 MB, > 5.58 MB max_line_chars) to prevent DuckDB JSON reader buffer over-allocation | Passed (all 22 shards of 2026-06-06 ingested cleanly with exit code 0) |
| 2026-11-02 00:12 | ghcp/diag_s6b.py | new file | Author patch_s6b | Added new read-only diagnostic module for message_id structure, per-batch cross-turn refs, and timestamp semantics | Ready for diag_s6b run |
| 2026-11-02 00:12 | ghcp/db.py | line 16 | Author patch_s6b | Added `SET TimeZone='UTC'` so day/hour bucketing does not depend on OS time zone | Applied |
| 2026-11-02 00:12 | sql/analysis/03_time.sql | multiple chunks | Author patch_s6b | Added `has_far_oow` and `next_far_oow` columns and 3 new CSV outputs `*_excl_far_oow` while keeping original 3 unchanged | Ready for analysis run |
| 2026-11-02 00:14 | ghcp/diag_s6b.py | lines 142, 145, 158 | `_duckdb.InvalidInputException: Required module 'pytz' failed to import` when fetching raw TIMESTAMPTZ | Cast `ts::VARCHAR` in D6 and `date_trunc('month', ts)::VARCHAR` in D7 to return ISO strings without requiring pytz | Passed (diag_s6b succeeded with code 0) |
| 2026-11-02 00:16 | sql/analysis/03_time.sql | lines 66-69 | `_duckdb.ParserException: Parser Error: syntax error at or near ";"` on `idle_gap_between_turns` due to comment trailing the semicolon before next chunk header | Moved comment lines after `-- @@ csv:time_decomposition_totals_excl_far_oow` so trailing semicolon is stripped properly by analyze.py | Passed (all 39 analysis steps completed with exit code 0) |
| 2026-11-02 20:53 | ghcp/diag_s7b.py | new file | Author patch_s7b | Added new read-only diagnostic module #2 for duration outliers, null token calls, unmatched batches, segment types, and status 0 | Ready for diag_s7b run |
| 2026-11-02 20:53 | sql/analysis/03_time.sql | entire file | Author patch_s7b | Replaced with v2 time decomposition adopting completion-time interval [ts-dur, ts], toolstart sensitivity, and llm_ms_exceeds_span tracking | Ready for analyze run |
| 2026-11-02 20:53 | ghcp/report.py | lines 87-96 | Author patch_s7b | Updated "Known limitations" section with empirical findings from diag_s6b and diag_s7b | Ready for report run |
| 2026-11-02 20:54 | sql/analysis/02_cache.sql | line 7 (`cache_overall`) | User request: patch_s7b item 1d | Replaced denominator with `nullif(count(tokens_cached), 0)` for `share_calls_zero_cache` and added `n_calls_with_prompt_tokens`, `n_calls_with_cached_tokens` | Ready for analyze run |
| 2026-11-04 02:57 | ghcp/report.py | lines 76-80 | User request: Fix 1 | Marked cross-turn and timestamp-probe validation lines as SUPERSEDED by diag_s6b D2 due to fan-out join on non-unique message_id | Passed (seven_day_metrics.md updated) |

## Validation Failures Assessment (S6)

In Stage S6, three checks failed against initial expectations:

1. `count:tool_batches` (Observed: 7,849,891 vs Expected: 7,767,261):
   - **Reconciled**: The published figure (7,767,261) counted non-empty batches with `n_calls > 0`. The dataset contains exactly 82,630 empty batches (`n_calls = 0`), totaling 7,849,891.
2. `distinct_models` (Observed: 38 vs Expected: 37):
   - **Undetermined**: The dataset contains 36 lettered models + `Model Other` + `tool-model` (211,048 calls). Upstream documentation does not specify whether `tool-model` or another model was excluded in the published count of 37.
3. `duplicate_message_ids` (Observed: 8,061,081 non-unique calls vs Expected: 0):
   - **Undetermined (Wrong Initial Assumption)**: The check assumed `message_id` is unique across calls within a day. In Copilot traces, `message_id` is reused across multiple calls and turns within a session. This invalidates validation queries that join on `message_id` without qualifying `session_id`/`turn_idx` (superseded by `diag_s6b`).
