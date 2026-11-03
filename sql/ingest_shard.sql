-- One shard (~500 sessions) -> six normalised tables. Tokens @...@ are substituted by ingest.py.
-- Nothing is filtered or repaired here: anomalies are preserved on purpose.
-- Table names use a leading underscore; they are TEMP and replaced for every shard.
-- @@ exec load
CREATE OR REPLACE TEMP TABLE _raw AS
SELECT * FROM read_json('@SHARD_PATH@',
  format='newline_delimited', compression='gzip', maximum_object_size=33554432,
  columns={
    'session_id': 'VARCHAR',
    'date': 'VARCHAR',
    'turns': 'STRUCT(
      turn_id VARCHAR,
      llm_calls STRUCT(
        message_id VARCHAR, "timestamp" VARCHAR, duration_ms DOUBLE, initiator_type VARCHAR,
        model VARCHAR, result VARCHAR, status_code VARCHAR,
        tokens STRUCT(total BIGINT, prompt BIGINT, completion BIGINT, cached BIGINT, cached_pct DOUBLE),
        message_metadata STRUCT("type" VARCHAR, role VARCHAR, "sequenceId" BIGINT, token_len BIGINT)[]
      )[],
      tool_batches STRUCT(
        "timestamp" VARCHAR, duration_ms DOUBLE, auto_continue BOOLEAN, result VARCHAR, request_id VARCHAR,
        function_calls STRUCT(name VARCHAR, status BIGINT, duration_ms DOUBLE)[]
      )[]
    )[]'
  });

-- @@ exec turns
CREATE OR REPLACE TEMP TABLE _turns AS
SELECT session_id, unnest(turns) AS trn, generate_subscripts(turns, 1) AS turn_idx FROM _raw;

-- @@ exec calls
CREATE OR REPLACE TEMP TABLE _calls AS
SELECT session_id, turn_idx, trn.turn_id AS turn_id,
       unnest(trn.llm_calls) AS cl, generate_subscripts(trn.llm_calls, 1) AS call_idx
FROM _turns;

-- @@ exec segments
CREATE OR REPLACE TEMP TABLE _segs AS
SELECT session_id, turn_idx, call_idx, cl.message_id AS message_id,
       unnest(cl.message_metadata) AS sg
FROM _calls;

-- @@ exec batches
CREATE OR REPLACE TEMP TABLE _batches AS
SELECT session_id, turn_idx, trn.turn_id AS turn_id,
       unnest(trn.tool_batches) AS tb, generate_subscripts(trn.tool_batches, 1) AS batch_idx
FROM _turns;

-- @@ exec fcalls
CREATE OR REPLACE TEMP TABLE _fcalls AS
SELECT session_id, turn_idx, batch_idx, tb.request_id AS request_id,
       unnest(tb.function_calls) AS fc, generate_subscripts(tb.function_calls, 1) AS call_idx
FROM _batches;

-- @@ exec out_sessions
COPY (
  SELECT session_id, "date" AS session_date, '@SHARD@' AS shard, len(turns) AS n_turns FROM _raw
) TO '@OUT_sessions@' (FORMAT PARQUET, COMPRESSION ZSTD);

-- @@ exec out_turns
COPY (
  SELECT session_id, turn_idx, trn.turn_id AS turn_id,
         len(trn.llm_calls) AS n_llm_calls, len(trn.tool_batches) AS n_tool_batches
  FROM _turns
) TO '@OUT_turns@' (FORMAT PARQUET, COMPRESSION ZSTD);

-- @@ exec out_llm_calls
COPY (
  SELECT session_id, turn_idx, turn_id, call_idx, cl.message_id AS message_id,
         cl."timestamp" AS ts_raw, TRY_CAST(cl."timestamp" AS TIMESTAMPTZ) AS ts,
         cl.duration_ms AS duration_ms, cl.initiator_type AS initiator_type, cl.model AS model,
         cl.result AS result, cl.status_code AS status_code,
         cl.tokens.total AS tokens_total, cl.tokens.prompt AS tokens_prompt,
         cl.tokens.completion AS tokens_completion, cl.tokens.cached AS tokens_cached,
         cl.tokens.cached_pct AS cached_pct, len(cl.message_metadata) AS n_segments
  FROM _calls
) TO '@OUT_llm_calls@' (FORMAT PARQUET, COMPRESSION ZSTD);

-- @@ exec out_prompt_segments
COPY (
  SELECT session_id, turn_idx, call_idx, message_id,
         sg."type" AS seg_type, sg.role AS role, sg."sequenceId" AS sequence_id, sg.token_len AS token_len
  FROM _segs
) TO '@OUT_prompt_segments@' (FORMAT PARQUET, COMPRESSION ZSTD);

-- @@ exec out_tool_batches
COPY (
  SELECT session_id, turn_idx, turn_id, batch_idx, tb.request_id AS request_id,
         tb."timestamp" AS ts_raw, TRY_CAST(tb."timestamp" AS TIMESTAMPTZ) AS ts,
         tb.duration_ms AS duration_ms, tb.auto_continue AS auto_continue, tb.result AS result,
         len(tb.function_calls) AS n_calls
  FROM _batches
) TO '@OUT_tool_batches@' (FORMAT PARQUET, COMPRESSION ZSTD);

-- @@ exec out_tool_calls
COPY (
  SELECT session_id, turn_idx, batch_idx, request_id, call_idx,
         fc.name AS name, fc.status AS status, fc.duration_ms AS duration_ms
  FROM _fcalls
) TO '@OUT_tool_calls@' (FORMAT PARQUET, COMPRESSION ZSTD);
