# Seven-day GHCP agentic-trace metrics report

Generated 2026-11-04 02:57:14 on Windows-11-10.0.26200-SP0 / Python 3.12.9

> Descriptive statistics of a released sample. No dollar costs. The HYPOTHETICAL section is a what-if in relative units. Anomalies are reported, not removed.

## Ingestion
Checkpointed shards: 606

Totals from checkpoint: `{"sessions": 301026, "turns": 1189581, "llm_calls": 9310255, "prompt_segments": 886856935, "tool_batches": 7849891, "tool_calls": 8681190}`

Summed per-shard ingest seconds: 2,878

- `guard_summary_analyze.json`: `{   "phase": "analyze",   "seconds": 476.1,   "peak_rss_mb": 1175.6,   "min_available_mb": 923.4,   "min_free_gb": 496.68,   "max_data_dir_gb": 5.14,   "max_cpu_pct": 0.0,   "stopped_reason": null }`
- `guard_summary_diag_s6b.json`: `{   "phase": "diag_s6b",   "seconds": 29.9,   "peak_rss_mb": 215.4,   "min_available_mb": 2504.3,   "min_free_gb": 497.1,   "max_data_dir_gb": 5.14,   "max_cpu_pct": 0.0,   "stopped_reason": null }`
- `guard_summary_diag_s7b.json`: `{   "phase": "diag_s7b",   "seconds": 170.5,   "peak_rss_mb": 445.8,   "min_available_mb": 1345.6,   "min_free_gb": 497.1,   "max_data_dir_gb": 5.14,   "max_cpu_pct": 0.0,   "stopped_reason": null }`
- `guard_summary_download.json`: `{   "phase": "download",   "seconds": 1653.8,   "peak_rss_mb": 32.2,   "min_available_mb": 1319.8,   "min_free_gb": 499.16,   "max_data_dir_gb": 2.95,   "max_cpu_pct": 0.0,   "stopped_reason": null }`
- `guard_summary_ingest.json`: `{   "phase": "ingest",   "seconds": 3026.9,   "peak_rss_mb": 1076.6,   "min_available_mb": 1268.0,   "min_free_gb": 497.05,   "max_data_dir_gb": 5.13,   "max_cpu_pct": 0.0,   "stopped_reason": null }`
- `guard_summary_validate.json`: `{   "phase": "validate",   "seconds": 118.3,   "peak_rss_mb": 309.5,   "min_available_mb": 2314.2,   "min_free_gb": 497.1,   "max_data_dir_gb": 5.14,   "max_cpu_pct": 0.0,   "stopped_reason": null }`

## Validation
FAIL count: **3**

| status | check | observed | expected | note |
|---|---|---|---|---|
| PASS | count:sessions | 301026 | 301026 |  |
| PASS | count:turns | 1189581 | 1189581 |  |
| PASS | count:llm_calls | 9310255 | 9310255 |  |
| FAIL | count:tool_batches | 7849891 | 7767261 |  |
| PASS | count:tool_calls | 8681190 | 8681190 |  |
| FAIL | distinct_models | 38 | 37 |  |
| INFO | count:prompt_segments | 886856935 |  | no published figure |
| PASS | tokens:prompt | 631401670144 | 631400000000.0 | published values are rounded |
| PASS | tokens:completion | 4914633421 | 4910000000.0 | published values are rounded |
| PASS | tokens:cached | 540950119440 | 540950000000.0 | published values are rounded |
| PASS | state_vs_parquet:sessions | 301026 | 301026 |  |
| PASS | state_vs_parquet:turns | 1189581 | 1189581 |  |
| PASS | state_vs_parquet:llm_calls | 9310255 | 9310255 |  |
| PASS | state_vs_parquet:prompt_segments | 886856935 | 886856935 |  |
| PASS | state_vs_parquet:tool_batches | 7849891 | 7849891 |  |
| PASS | state_vs_parquet:tool_calls | 8681190 | 8681190 |  |
| PASS | manifest:2026-06-01:n_sessions | 55870 | 55870 |  |
| PASS | manifest:2026-06-02:n_sessions | 60145 | 60145 |  |
| PASS | manifest:2026-06-03:n_sessions | 60202 | 60202 |  |
| PASS | manifest:2026-06-04:n_sessions | 55143 | 55143 |  |
| PASS | manifest:2026-06-05:n_sessions | 47863 | 47863 |  |
| PASS | manifest:2026-06-06:n_sessions | 10674 | 10674 |  |
| PASS | manifest:2026-06-07:n_sessions | 11129 | 11129 |  |
| PASS | duplicate_session_ids | 0 | 0 |  |
| FAIL | duplicate_message_ids | 8061081 | 0 | within a day |
| INFO | anomaly:negative_llm_duration_ms | 23 |  | team audit reported 4 (unconfirmed by Claude) |
| INFO | anomaly:negative_tool_batch_duration_ms | 2 |  |  |
| INFO | anomaly:negative_tool_call_duration_ms | 0 |  |  |
| INFO | anomaly:null_duration_llm | 0 |  |  |
| INFO | anomaly:unparseable_or_null_llm_ts | 0 |  |  |
| INFO | anomaly:unparseable_or_null_tool_ts | 0 |  |  |
| INFO | anomaly:llm_ts_outside_window | 9581 |  | window 2026-06-01..2026-06-08 UTC |
| INFO | anomaly:tool_ts_outside_window | 7044 |  |  |
| INFO | info:llm_ts_min_max | ["2019-06-02 01:30:30+05:30", "2026-07-07 10:28:17.598+05:30"] |  |  |
| INFO | info:outside_window_by_day_top20 | [["2026-06-01 00:00:00+05:30", 1461], ["2026-05-29 00:00:00+05:30", 1137], ["2026-05-28 00:00:00+05:30", 770], ["2026-04-19 00:00:00+05:30", 663], ["2026-05-31 00:00:00+05:30", 659], ["2026-05-26 00:00:00+05:30", 646], ["2026-04-18 00:00:00+05:30", 527], ["2026-05-20 00:00:00+05:30", 372], ["2026-06-08 00:00:00+05:30", 297], ["2026-05-27 00:00:00+05:30", 273], ["2026-04-24 00:00:00+05:30", 248], ["2026-05-21 00:00:00+05:30", 221], ["2025-09-12 00:00:00+05:30", 195], ["2026-05-30 00:00:00+05:30", 186], ["2026-05-19 00:00:00+05:30", 179], ["2026-04-11 00:00:00+05:30", 178], ["2026-05-25 00:00:00+05:30", 157], ["2026-05-22 00:00:00+05:30", 142], ["2026-07-02 00:00:00+05:30", 132], ["2026-04-20 00:00:00+05:30", 102]] |  |  |
| INFO | anomaly:cached_gt_prompt | 0 |  |  |
| INFO | anomaly:total_ne_prompt_plus_completion | 0 |  |  |
| INFO | info:cached_pct_min_max (scale 0-1 or 0-100?) | [0.0, 100.0] |  |  |
| SUPERSEDED | anomaly:cross_turn_tool_batch_refs | {"cross": 5116, "of_all_batches": 184495105, "pct_of_all": 0.0028, "matched": 184420208, "unmatched": 74897} |  | SUPERSEDED by diag_s6b D2 (earlier validation check suffered fan-out join on non-unique message_id) |
| SUPERSEDED | probe:tool_batch_ts>=its_llm_call_ts | {"share": 0.5025, "pairs": 184420208} |  | SUPERSEDED by diag_s6b D2 (earlier validation check suffered fan-out join on non-unique message_id) |
| SUPERSEDED | probe:tool_batch_ts>=llm_call_end | {"share": 0.4499, "pairs": 184420208} |  | SUPERSEDED by diag_s6b D2 (earlier validation check suffered fan-out join on non-unique message_id) |
| INFO | null:llm_calls.tokens_prompt | 255086 |  |  |
| INFO | null:llm_calls.tokens_total | 255086 |  |  |
| INFO | null:llm_calls.tokens_cached | 255260 |  |  |
| INFO | null:llm_calls.duration_ms | 0 |  |  |
| INFO | null:llm_calls.n_segments | 327170 |  |  |
| INFO | null:tool_batches.duration_ms | 0 |  |  |
| INFO | null:tool_batches.auto_continue | 4371566 |  |  |
| INFO | info:tool_call_status_values | [[1, 7994017], [2, 391817], [0, 295356]] |  |  |
| INFO | info:llm_result_values | [["Success", 9186585], ["UserCancel", 71936], ["Failure", 41997], ["UserFault", 9737]] |  |  |
| INFO | info:null_token_calls_by_result | [["UserCancel", 71936], ["Failure", 41997], ["Success", 131416], ["UserFault", 9737]] |  |  |

## Token concentration - top-x% share of total
| metric | top_pct_of_sessions | share_of_total | n_sessions |
|---|---|---|---|
| cached_tokens | 1 | 0.2156 | 301,026 |
| cached_tokens | 5 | 0.5118 | 301,026 |
| cached_tokens | 10 | 0.6885 | 301,026 |
| cached_tokens | 20 | 0.8588 | 301,026 |
| cached_tokens | 50 | 0.9891 | 301,026 |
| completion_tokens | 1 | 0.1679 | 301,026 |
| completion_tokens | 5 | 0.4116 | 301,026 |
| completion_tokens | 10 | 0.5698 | 301,026 |
| completion_tokens | 20 | 0.7426 | 301,026 |
| completion_tokens | 50 | 0.9334 | 301,026 |
| llm_calls | 1 | 0.1368 | 301,026 |
| llm_calls | 5 | 0.3578 | 301,026 |
| llm_calls | 10 | 0.5152 | 301,026 |
| llm_calls | 20 | 0.7092 | 301,026 |
| llm_calls | 50 | 0.9485 | 301,026 |
| llm_ms | 1 | 0.2748 | 301,026 |
| llm_ms | 5 | 0.4882 | 301,026 |
| llm_ms | 10 | 0.6268 | 301,026 |
| llm_ms | 20 | 0.7805 | 301,026 |
| llm_ms | 50 | 0.948 | 301,026 |
| prompt_tokens | 1 | 0.2062 | 301,026 |
| prompt_tokens | 5 | 0.4951 | 301,026 |
| prompt_tokens | 10 | 0.6708 | 301,026 |
| prompt_tokens | 20 | 0.8432 | 301,026 |
| prompt_tokens | 50 | 0.981 | 301,026 |

_(first 25 of 30 rows; full file in outputs/)_


## Gini coefficients
| metric | gini | n_sessions | total |
|---|---|---|---|
| cached_tokens | 0.8179 | 301,026 | 540,950,119,440 |
| completion_tokens | 0.7071 | 301,026 | 4,914,633,421 |
| llm_calls | 0.6907 | 301,026 | 9,310,255 |
| llm_ms | 0.7488 | 301,026 | 1.104e+11 |
| prompt_tokens | 0.8016 | 301,026 | 631,401,670,144 |
| uncached_prompt_tokens | 0.7852 | 301,026 | 90,451,550,704 |


## Per-session distributions
| metric | n | mean | min | p50 | p90 | p99 | p999 | max |
|---|---|---|---|---|---|---|---|---|
| cached_tokens | 301,026 | 1.797e+06 | 0 | 2.008e+05 | 4.672e+06 | 22,725,122 | 6.103e+07 | 288,359,805 |
| completion_tokens | 301,026 | 1.633e+04 | 0 | 5,744 | 40,193 | 1.638e+05 | 4.241e+05 | 2,083,099 |
| llm_calls | 301,026 | 30.93 | 1 | 11 | 80 | 268 | 633 | 3,065 |
| llm_ms | 301,026 | 3.668e+05 | -2.108e+07 | 9.06e+04 | 7.915e+05 | 3.267e+06 | 1.01e+07 | 1.441e+09 |
| prompt_tokens | 301,026 | 2.097e+06 | 0 | 268,712 | 5.475e+06 | 2.566e+07 | 6.847e+07 | 302,473,832 |
| uncached_prompt_tokens | 301,026 | 3.005e+05 | 0 | 6.852e+04 | 6.71e+05 | 3.693e+06 | 1.4e+07 | 165,126,298 |


## Cache - overall
| n_calls | prompt_tokens | cached_tokens | cached_share_token_weighted | mean_call_cached_share | share_calls_zero_cache | n_calls_with_prompt_tokens | n_calls_with_cached_tokens | calls_cached_gt_prompt |
|---|---|---|---|---|---|---|---|---|
| 9,310,255 | 631,401,670,144 | 540,950,119,440 | 0.8567 | 0.859 | 0.06165 | 9,055,169 | 9,054,995 | 0 |


## Cache - by initiator
| initiator_type | n_calls | prompt_tokens | cached_share |
|---|---|---|---|
| agent | 8,163,807 | 559,488,868,942 | 0.9052 |
| user | 1,130,028 | 71,906,734,650 | 0.4801 |
|  | 16,420 | 6,066,552 |  |


## Cache - by call position in turn
| call_position_in_turn | ord | n_calls | prompt_tokens | cached_share |
|---|---|---|---|---|
| 1 | 1 | 1,182,650 | 75,958,605,514 | 0.4624 |
| 2 | 2 | 839,695 | 53,943,907,623 | 0.851 |
| 3 | 3 | 729,995 | 47,976,288,487 | 0.9088 |
| 4-5 | 4 | 1,161,786 | 76,986,694,896 | 0.9172 |
| 6-10 | 6 | 1,857,703 | 122,614,537,244 | 0.9203 |
| 11-20 | 11 | 1,845,290 | 124,913,770,211 | 0.923 |
| 21+ | 21 | 1,693,136 | 129,007,866,169 | 0.9114 |


## Cache - by turn position in session
| turn_position_in_session | ord | n_calls | prompt_tokens | cached_share |
|---|---|---|---|---|
| 1 | 1 | 2,688,816 | 115,702,858,411 | 0.8222 |
| 2 | 2 | 1,316,588 | 75,368,922,568 | 0.8447 |
| 3 | 3 | 917,572 | 60,476,090,624 | 0.8569 |
| 4-5 | 4 | 1,202,839 | 89,752,433,959 | 0.8604 |
| 6-10 | 6 | 1,475,494 | 125,171,233,868 | 0.8671 |
| 11+ | 11 | 1,708,946 | 164,930,130,714 | 0.8766 |


## Cache - by model (anonymised labels)
| model | n_calls | prompt_tokens | completion_tokens | cached_share | mean_duration_ms |
|---|---|---|---|---|---|
| Model A | 2,398,528 | 164,877,301,650 | 1,381,058,464 | 0.8647 | 1.311e+04 |
| Model B | 1,315,292 | 73,888,860,700 | 545,801,948 | 0.8628 | 8898 |
| Model C | 975,680 | 72,961,481,687 | 383,779,570 | 0.8076 | 1.098e+04 |
| Model D | 763,028 | 58,406,883,730 | 275,540,228 | 0.895 | 1.117e+04 |
| Model E | 767,234 | 42,063,082,533 | 340,762,621 | 0.8721 | 6091 |
| Model H | 434,139 | 41,398,476,918 | 484,481,994 | 0.8831 | 1.745e+04 |
| Model G | 387,557 | 37,599,249,461 | 322,660,053 | 0.8106 | 1.336e+04 |
| Model F | 849,483 | 36,381,052,159 | 462,724,679 | 0.849 | 1.095e+04 |
| Model I | 400,350 | 36,266,976,514 | 171,109,371 | 0.8904 | 1.718e+04 |
| Model J | 178,663 | 15,759,986,661 | 56,865,210 | 0.9012 | 2.262e+04 |
| Model K | 200,581 | 15,592,859,356 | 276,219,164 | 0.7722 | 1.922e+04 |
| Model P | 46,842 | 9,010,536,340 | 35,422,537 | 0.8939 | 1.043e+04 |
| Model L | 113,306 | 7,799,640,079 | 44,731,224 | 0.8426 | 7680 |
| Model O | 42,084 | 3,520,909,850 | 36,152,147 | 0.8325 | 1.096e+04 |
| Model M | 65,631 | 3,174,203,174 | 10,323,183 | 0.7155 | 9882 |
| Model N | 41,435 | 2,511,769,438 | 12,694,506 | 0.8867 | 2.081e+04 |
| Model T | 25,302 | 2,166,166,749 | 19,575,203 | 0.8607 | 1.016e+04 |
| Model Q | 32,430 | 1,824,681,926 | 6,217,190 | 0.8617 | 4611 |
| Model R | 23,498 | 1,487,662,641 | 8,634,964 | 0.8423 | 1.343e+04 |
| Model S | 19,206 | 1,216,090,234 | 3,381,985 | 0.797 | 1.047e+04 |
| Model W | 14,234 | 608,620,444 | 7,713,903 | 0.9457 | 1.666e+04 |
| Model V | 15,158 | 579,500,630 | 3,013,783 | 0.9497 | 4617 |
| Model Other | 32,564 | 567,127,633 | 828,451 | 0.1779 | 7680 |
| Model U | 20,417 | 521,771,315 | 14,241,459 | 0.7125 | 6189 |
| Model X | 9,069 | 353,590,060 | 4,445,272 | 0.6288 | 1.449e+04 |

_(first 25 of 38 rows; full file in outputs/)_


## Cache - by session size
| session_size_bucket | n_sessions | n_calls | prompt_tokens | cached_share |
|---|---|---|---|---|
| a: 1-10 calls | 147,061 | 441,744 | 16,214,895,054 | 0.5208 |
| b: 11-50 | 100,155 | 2,571,996 | 121,380,300,343 | 0.8112 |
| c: 51-200 | 48,093 | 4,401,753 | 321,377,810,482 | 0.8646 |
| d: 201-1000 | 5,652 | 1,805,630 | 164,801,176,020 | 0.9041 |
| e: >1000 | 65 | 89,132 | 7,627,488,245 | 0.9418 |


## Time decomposition - totals
| n_turns | span_ms_total | llm_ms_total | tool_ms_total | positive_residual_ms_total | llm_share_of_span | tool_share_of_span | positive_residual_share | turns_negative_residual | turns_nonpositive_span | turns_llm_ms_exceeds_span |
|---|---|---|---|---|---|---|---|---|---|---|
| 1,189,581 | 279,017,583,580 | 1.104e+11 | 1.122e+11 | 5.727e+10 | 0.3957 | 0.402 | 0.2052 | 193,310 | 6 | 168,183 |


## Time decomposition - percentiles
| quantity | p50 | p90 | p99 |
|---|---|---|---|
| turn_span_s | 49.79 | 337.9 | 1883 |
| llm_share_of_turn | 0.9083 | 1 | 1 |
| tool_share_of_turn | 0.024 | 0.4239 | 0.9265 |


## Idle gaps between turns
| n_gaps | p50_s | p90_s | p99_s | negative_gaps | gaps_over_1min | gaps_over_5min | gaps_over_30min | idle_total_s |
|---|---|---|---|---|---|---|---|---|
| 888,555 | 152.4 | 1844 | 1.632e+04 | 679 | 645,533 | 305,113 | 90,444 | 9.32e+08 |


## Prompt composition by segment type
| seg_type | role | n_segments | tokens | share_of_segment_tokens |
|---|---|---|---|---|
| History | tool | 262,745,641 | 178,305,179,169 | 0.3009 |
| FunctionCalls | tool | 107,339,450 | 107,969,282,683 | 0.1822 |
| History | user | 105,713,781 | 97,034,301,379 | 0.1637 |
| History | assistant | 274,563,330 | 88,208,722,880 | 0.1488 |
| System | system | 8,896,842 | 43,788,789,849 | 0.07389 |
| FunctionCalls | assistant | 95,595,935 | 28,412,385,230 | 0.04794 |
| Context | user | 12,441,044 | 25,387,779,485 | 0.04284 |
| RepositoryWideCustomInstructions | system | 3,761,904 | 13,492,615,716 | 0.02277 |
| UserMessage | user | 8,896,842 | 4,215,037,477 | 0.007112 |
| IdeState | user | 5,905,910 | 2,322,020,047 | 0.003918 |
| AgentSkillsInstructions | system | 779,908 | 1,828,535,643 | 0.003085 |
| FunctionCalls | user | 88,192 | 865,403,899 | 0.00146 |
| PathSpecificCustomInstructions | system | 126,990 | 825,746,857 | 0.001393 |
| McpInstructions | system | 1,157 | 654,835 | 1.105e-06 |
| ResponseInstructions | user | 9 | 381 | 6.429e-10 |


## Segment tokens vs reported prompt tokens
| segment_tokens | prompt_tokens | segment_to_prompt_ratio |
|---|---|---|
| 592,656,455,530 | 631,401,670,144 | 0.9386 |


## Context growth by call position
| call_idx_capped | n_calls | mean_prompt_tokens | p50_prompt_tokens | mean_completion_tokens |
|---|---|---|---|---|
| 1 | 1,182,650 | 6.861e+04 | 53,331 | 943.3 |
| 2 | 839,695 | 6.647e+04 | 51,509 | 471.7 |
| 3 | 729,995 | 6.751e+04 | 52,952 | 449.8 |
| 4 | 625,487 | 6.781e+04 | 5.35e+04 | 451.7 |
| 5 | 536,299 | 6.776e+04 | 53,567 | 461.9 |
| 6 | 465,980 | 6.747e+04 | 53,363 | 467.6 |
| 7 | 410,229 | 6.741e+04 | 53,282 | 479.6 |
| 8 | 363,899 | 6.728e+04 | 5.316e+04 | 482.5 |
| 9 | 325,486 | 6.737e+04 | 5.335e+04 | 490 |
| 10 | 292,109 | 6.752e+04 | 5.362e+04 | 495.4 |
| 11 | 264,665 | 6.778e+04 | 53,939 | 504.4 |
| 12 | 240,728 | 6.801e+04 | 54,258 | 505.2 |
| 13 | 219,857 | 6.838e+04 | 54,673 | 508.2 |
| 14 | 201,307 | 6.864e+04 | 55,136 | 513.6 |
| 15 | 184,955 | 6.905e+04 | 55,680 | 512.5 |
| 16 | 170,347 | 6.939e+04 | 56,097 | 516.6 |
| 17 | 157,305 | 6.986e+04 | 56,713 | 519.7 |
| 18 | 145,592 | 7.02e+04 | 57,113 | 517.6 |
| 19 | 134,979 | 7.061e+04 | 57,646 | 516.2 |
| 20 | 125,555 | 7.097e+04 | 58,080 | 519.6 |
| 21 | 116,786 | 7.147e+04 | 58,737 | 513.5 |
| 22 | 108,806 | 7.19e+04 | 59,217 | 511.2 |
| 23 | 101,518 | 7.235e+04 | 59,838 | 518.9 |
| 24 | 94,827 | 7.28e+04 | 60,425 | 521.3 |
| 25 | 88,821 | 7.337e+04 | 61,109 | 509 |

_(first 25 of 30 rows; full file in outputs/)_


## Tool usage
| name | calls | fail_rate | p50_ms | p95_ms | total_ms |
|---|---|---|---|---|---|
| get_file | 3,085,349 | 0.02436 | 68.97 | 996.6 | 2.882e+09 |
| run_command_in_terminal | 1,385,182 | 0.1135 | 430 | 6.023e+04 | 7e+10 |
| replace_string_in_file | 825,832 | 0.008429 | 259 | 1969 | 2.511e+09 |
| code_search | 706,910 | 0.006342 | 1740 | 9661 | 2.495e+09 |
| run_build | 421,942 | 0.2155 | 5053 | 9.339e+04 | 3.17e+10 |
| file_search | 409,945 | 0.0223 | 59.27 | 300 | 1.207e+08 |
| apply_patch | 321,350 | 0.02349 | 293.2 | 1.15e+04 | 1.218e+09 |
| create_file | 253,625 | 0.05175 | 586 | 5318 | 1.035e+09 |
| update_plan_progress | 219,061 | 0.001096 | 16.91 | 286.2 | 1.962e+07 |
| multi_replace_string_in_file | 171,108 | 0.01951 | 358.6 | 2927 | 4.233e+08 |
| get_errors | 170,525 | 0.01422 | 63.91 | 416.4 | 2.946e+07 |
| edit_file | 95,338 | 0.1225 | 4884 | 4.575e+04 | 1.448e+09 |
| get_files_in_project | 76,418 | 0.00195 | 66.06 | 417 | 1.39e+07 |
| find_symbol | 70,279 | 0.0037 | 217.3 | 2601 | 4.863e+08 |
| get_projects_in_solution | 70,047 | 0.001399 | 95.27 | 458.3 | 1.313e+07 |
| get_symbols_by_name | 59,654 | 0.002347 | 96.83 | 794.4 | 1.643e+09 |
| run_tests | 48,756 | 0.02041 | 7683 | 1.005e+05 | 1.688e+09 |
| remove_file | 41,482 | 0.03659 | 726.6 | 6423 | 7.928e+07 |
| plan | 37,881 | 0.000528 | 265.2 | 1182 | 1.586e+07 |
| finish_plan | 33,111 | 3.02e-05 | 12.81 | 235.4 | 2.103e+06 |
| record_observation | 18,245 | 0.0001644 | 29.89 | 354.9 | 1.827e+06 |
| get_background_terminal_output | 16,861 | 0.02432 | 8093 | 1.436e+05 | 5.921e+08 |
| get_currentfile | 16,390 | 0.003539 | 64.85 | 289.2 | 1.852e+06 |
| get_output_window_logs | 15,277 | 0.1004 | 94.37 | 6.281e+04 | 1.326e+09 |
| detect_memories | 13,843 | 0.005418 | 47.33 | 219.4 | 1.449e+06 |

_(first 25 of 2496 rows; full file in outputs/)_


## Tool batches
| n_batches | mean_calls_per_batch | p99_calls_per_batch | max_calls_per_batch | auto_continue_share | p50_ms | p95_ms |
|---|---|---|---|---|---|---|
| 7,849,891 | 1.106 | 3 | 139 | 0.9182 | 174.6 | 1.445e+04 |


## Top tool transitions
| from_tool | to_tool | n |
|---|---|---|
| get_file | get_file | 1,493,215 |
| run_command_in_terminal | run_command_in_terminal | 791,521 |
| get_file | replace_string_in_file | 361,309 |
| code_search | get_file | 321,326 |
| get_file | code_search | 316,956 |
| <START> | get_file | 302,839 |
| run_command_in_terminal | get_file | 259,461 |
| replace_string_in_file | replace_string_in_file | 249,925 |
| run_build | <END> | 224,411 |
| file_search | get_file | 219,271 |
| get_file | run_command_in_terminal | 206,880 |
| replace_string_in_file | run_build | 148,947 |
| replace_string_in_file | get_file | 142,514 |
| get_file | <END> | 139,996 |
| code_search | code_search | 139,921 |
| get_file | file_search | 134,562 |
| run_command_in_terminal | <END> | 123,887 |
| get_file | apply_patch | 112,185 |
| create_file | create_file | 106,959 |
| code_search | file_search | 102,166 |
| apply_patch | apply_patch | 101,796 |
| get_file | multi_replace_string_in_file | 98,701 |
| <START> | code_search | 95,525 |
| <START> | run_command_in_terminal | 93,546 |
| replace_string_in_file | <END> | 75,260 |

_(first 25 of 60 rows; full file in outputs/)_


## Top tool sequences (first six tools)
| first_six_tools | n_turns |
|---|---|
| get_file | 20,275 |
| replace_string_in_file | 18,763 |
| run_command_in_terminal | 14,577 |
| run_command_in_terminal > run_command_in_terminal > run_command_in_terminal > run_command_in_terminal > run_command_in_terminal > run_command_in_terminal | 13,029 |
| get_file > get_file > get_file > get_file > get_file > get_file | 12,561 |
| get_file > replace_string_in_file | 12,031 |
| apply_patch | 9,127 |
| apply_patch > run_build | 9,018 |
| get_file > get_file | 8,245 |
| get_file > replace_string_in_file > run_build | 7,892 |
| replace_string_in_file > run_build | 7,608 |
| run_command_in_terminal > run_command_in_terminal | 6,874 |
| run_command_in_terminal > run_command_in_terminal > run_command_in_terminal | 4,343 |
| create_file | 4,143 |
| multi_replace_string_in_file | 3,867 |
| code_search | 3,822 |
| get_file > apply_patch | 3,762 |
| apply_patch > get_errors | 3,761 |
| get_file > get_file > get_file | 3,745 |
| get_projects_in_solution > get_files_in_project > get_file > get_file > get_file > get_file | 3,722 |
| get_file > apply_patch > run_build | 3,611 |
| detect_memories | 3,373 |
| edit_file | 3,213 |
| file_search > get_file > get_file > get_file > get_file > get_file | 2,978 |
| run_command_in_terminal > run_command_in_terminal > run_command_in_terminal > run_command_in_terminal | 2,818 |

_(first 25 of 30 rows; full file in outputs/)_


## Model share
| model | n_calls | share_of_calls | share_of_prompt_tokens | share_of_completion_tokens | p50_duration_ms | p95_duration_ms | non_success_share |
|---|---|---|---|---|---|---|---|
| Model A | 2,398,528 | 0.2576 | 0.2611 | 0.281 | 5329 | 3.583e+04 | 0.0102 |
| Model B | 1,315,292 | 0.1413 | 0.117 | 0.1111 | 5154 | 2.405e+04 | 0.01334 |
| Model C | 975,680 | 0.1048 | 0.1156 | 0.07809 | 5344 | 2.519e+04 | 0.00877 |
| Model F | 849,483 | 0.09124 | 0.05762 | 0.09415 | 4830 | 2.517e+04 | 0.01908 |
| Model E | 767,234 | 0.08241 | 0.06662 | 0.06934 | 3742 | 1.582e+04 | 0.01137 |
| Model D | 763,028 | 0.08196 | 0.0925 | 0.05607 | 5870 | 2.557e+04 | 0.01105 |
| Model H | 434,139 | 0.04663 | 0.06557 | 0.09858 | 7351 | 6.135e+04 | 0.01038 |
| Model I | 400,350 | 0.043 | 0.05744 | 0.03482 | 7128 | 3.362e+04 | 0.008847 |
| Model G | 387,557 | 0.04163 | 0.05955 | 0.06565 | 6198 | 3.844e+04 | 0.01031 |
| Model K | 200,581 | 0.02154 | 0.0247 | 0.0562 | 7448 | 5.355e+04 | 0.07864 |
| Model J | 178,663 | 0.01919 | 0.02496 | 0.01157 | 6425 | 2.692e+04 | 0.009067 |
| Model L | 113,306 | 0.01217 | 0.01235 | 0.009102 | 4722 | 2.03e+04 | 0.01233 |
| tool-model | 111,315 | 0.01196 |  |  | 4176 | 3.581e+04 | 0.01828 |
| Model M | 65,631 | 0.007049 | 0.005027 | 0.0021 | 4407 | 1.908e+04 | 0.01909 |
| Model P | 46,842 | 0.005031 | 0.01427 | 0.007208 | 5786 | 3.096e+04 | 0.008305 |
| Model O | 42,084 | 0.00452 | 0.005576 | 0.007356 | 5369 | 3.626e+04 | 0.008127 |
| Model N | 41,435 | 0.00445 | 0.003978 | 0.002583 | 4225 | 2.076e+04 | 0.01861 |
| Model Other | 32,564 | 0.003498 | 0.0008982 | 0.0001686 | 3325 | 2.208e+04 | 0.04959 |
| Model Q | 32,430 | 0.003483 | 0.00289 | 0.001265 | 2693 | 1.336e+04 | 0.009282 |
| Model T | 25,302 | 0.002718 | 0.003431 | 0.003983 | 5707 | 3.197e+04 | 0.007628 |
| Model R | 23,498 | 0.002524 | 0.002356 | 0.001757 | 6444 | 3.868e+04 | 0.02345 |
| Model U | 20,417 | 0.002193 | 0.0008264 | 0.002898 | 2898 | 2.406e+04 | 0.01092 |
| Model S | 19,206 | 0.002063 | 0.001926 | 0.0006881 | 2903 | 1.308e+04 | 0.008175 |
| Model V | 15,158 | 0.001628 | 0.0009178 | 0.0006132 | 3319 | 1.099e+04 | 0.001451 |
| Model W | 14,234 | 0.001529 | 0.0009639 | 0.00157 | 7266 | 6.775e+04 | 0.02346 |

_(first 25 of 38 rows; full file in outputs/)_


## HYPOTHETICAL cost-index scenarios (relative units, NOT money)
| assumed_cached_price_ratio | assumed_completion_price_multiple | hypothetical_index_total | hypothetical_no_cache_index_total | hypothetical_caching_saving_fraction | hypothetical_top10pct_sessions_share |
|---|---|---|---|---|---|
| 0 | 1 | 95,366,184,125 | 636,316,303,565 | 0.8501 | 0.6614 |
| 0.1 | 1 | 149,461,196,069 | 636,316,303,565 | 0.7651 | 0.65 |
| 0.25 | 1 | 230,603,713,985 | 636,316,303,565 | 0.6376 | 0.6537 |
| 0.5 | 1 | 365,841,243,845 | 636,316,303,565 | 0.4251 | 0.6611 |
| 1 | 1 | 636,316,303,565 | 636,316,303,565 | 0 | 0.6695 |
| 0 | 3 | 105,195,450,967 | 646,145,570,407 | 0.8372 | 0.6441 |
| 0.1 | 3 | 159,290,462,911 | 646,145,570,407 | 0.7535 | 0.6403 |
| 0.25 | 3 | 240,432,980,827 | 646,145,570,407 | 0.6279 | 0.6473 |
| 0.5 | 3 | 375,670,510,687 | 646,145,570,407 | 0.4186 | 0.6568 |
| 1 | 3 | 646,145,570,407 | 646,145,570,407 | 0 | 0.6669 |
| 0 | 5 | 115,024,717,809 | 655,974,837,249 | 0.8247 | 0.6311 |
| 0.1 | 5 | 169,119,729,753 | 655,974,837,249 | 0.7422 | 0.6322 |
| 0.25 | 5 | 250,262,247,669 | 655,974,837,249 | 0.6185 | 0.6416 |
| 0.5 | 5 | 385,499,777,529 | 655,974,837,249 | 0.4123 | 0.6529 |
| 1 | 5 | 655,974,837,249 | 655,974,837,249 | 0 | 0.6644 |
| 0 | 8 | 129,768,618,072 | 670,718,737,512 | 0.8065 | 0.6169 |
| 0.1 | 8 | 183,863,630,016 | 670,718,737,512 | 0.7259 | 0.6225 |
| 0.25 | 8 | 265,006,147,932 | 670,718,737,512 | 0.6049 | 0.6342 |
| 0.5 | 8 | 400,243,677,792 | 670,718,737,512 | 0.4033 | 0.6474 |
| 1 | 8 | 670,718,737,512 | 670,718,737,512 | 0 | 0.6608 |


## Benchmark: DuckDB vs Polars (single machine; no Spark)
| query | days | engine | files | median_wall_s | min_wall_s | max_peak_rss_mb | rows | checksum | error |
|---|---|---|---|---|---|---|---|---|---|
| q1_session_token_rollup | 1 | duckdb | 112 | 1.888 | 1.831 | 70.9 | 55,870 | 1,748,037 |  |
| q1_session_token_rollup | 1 | polars | 112 | 1.691 | 1.674 | 127.7 | 55,870 | 1,748,037 |  |
| q1_session_token_rollup | 3 | duckdb | 354 | 3.248 | 3.032 | 94.4 | 176,217 | 5,391,816 |  |
| q1_session_token_rollup | 3 | polars | 354 | 1.865 | 1.841 | 188.3 | 176,217 | 5,391,816 |  |
| q1_session_token_rollup | 7 | duckdb | 606 | 5.667 | 5.156 | 123.5 | 301,026 | 9,310,255 |  |
| q1_session_token_rollup | 7 | polars | 606 | 1.99 | 1.684 | 236.2 | 301,026 | 9,310,255 |  |
| q2_cache_by_call_position | 1 | duckdb | 112 | 0.993 | 0.829 | 66.4 | 21 | 1,748,037 |  |
| q2_cache_by_call_position | 1 | polars | 112 | 1.336 | 1.313 | 104.8 | 21 | 1,748,037 |  |
| q2_cache_by_call_position | 3 | duckdb | 354 | 1.335 | 1.091 | 70.3 | 21 | 5,391,816 |  |
| q2_cache_by_call_position | 3 | polars | 354 | 1.763 | 1.736 | 118.4 | 21 | 5,391,816 |  |
| q2_cache_by_call_position | 7 | duckdb | 606 | 1.487 | 1.415 | 68.5 | 21 | 9,310,255 |  |
| q2_cache_by_call_position | 7 | polars | 606 | 1.578 | 1.518 | 155.4 | 21 | 9,310,255 |  |
| q3_tool_usage | 1 | duckdb | 112 | 0.944 | 0.931 | 73.8 | 855 | 1,635,686 |  |
| q3_tool_usage | 1 | polars | 112 | 2.132 | 1.454 | 236.1 | 855 | 1,635,686 |  |
| q3_tool_usage | 3 | duckdb | 354 | 1.335 | 1.113 | 122.3 | 1,759 | 4,991,052 |  |
| q3_tool_usage | 3 | polars | 354 | 1.769 | 1.702 | 542.9 | 1,759 | 4,991,052 |  |
| q3_tool_usage | 7 | duckdb | 606 | 1.515 | 1.438 | 169.1 | 2,496 | 8,681,190 |  |
| q3_tool_usage | 7 | polars | 606 | 2.209 | 2.077 | 920 | 2,496 | 8,681,190 |  |


## Analysis step timings
| file | step | seconds | peak_rss_mb_so_far |
|---|---|---|---|
| 00_session_metrics.sql | session_metrics | 51.61 | 206.5 |
| 01_concentration.sql | conc_base | 0.4 | 206.5 |
| 01_concentration.sql | conc_ranked | 1.7 | 206.5 |
| 01_concentration.sql | concentration_top_shares | 0.37 | 206.5 |
| 01_concentration.sql | concentration_gini | 0.09 | 206.5 |
| 01_concentration.sql | concentration_lorenz | 1.45 | 458.8 |
| 01_concentration.sql | session_distribution | 0.38 | 458.8 |
| 02_cache.sql | cache_overall | 0.8 | 458.8 |
| 02_cache.sql | cache_by_initiator | 2.32 | 458.8 |
| 02_cache.sql | cache_by_call_position | 6.03 | 458.8 |
| 02_cache.sql | cache_by_turn_position | 4.34 | 458.8 |
| 02_cache.sql | cache_by_model | 2.91 | 458.8 |
| 02_cache.sql | cache_by_session_size | 2.07 | 458.8 |
| 02_cache.sql | cache_share_histogram | 1.01 | 458.8 |
| 03_time.sql | turn_events | 0.03 | 458.8 |
| 03_time.sql | turn_time | 14.88 | 682.9 |
| 03_time.sql | turn_time2 | 1.79 | 682.9 |
| 03_time.sql | turn_time_s | 5.13 | 768.7 |
| 03_time.sql | turn_time_s2 | 0.87 | 768.7 |
| 03_time.sql | time_decomposition_totals | 0.15 | 768.7 |
| 03_time.sql | time_decomposition_percentiles | 0.78 | 768.7 |
| 03_time.sql | idle_gap_between_turns | 0.22 | 768.7 |
| 03_time.sql | time_decomposition_totals_excl_far_oow | 0.14 | 768.7 |
| 03_time.sql | time_decomposition_percentiles_excl_far_oow | 0.41 | 768.7 |
| 03_time.sql | idle_gap_between_turns_excl_far_oow | 0.21 | 787.4 |

_(first 25 of 43 rows; full file in outputs/)_


## Figures
- figures/benchmark.png
- figures/cache_by_call_position.png
- figures/HYPOTHETICAL_sensitivity.png
- figures/lorenz.png
- figures/prompt_composition.png
- figures/time_decomposition.png
- figures/tool_transitions.png

## Known limitations (carried from KNOWN_FACTS.md)
- Released sample of non-enterprise sessions, one week; sampling rate not published.
- Model names anonymised; no mapping to prices, so no currency figures exist here.
- Semantics of `tokens.cached` are an assumption (publisher-reported cached prompt tokens).
- LLM-call `timestamp` behaves like a completion (end) time (diag_s6b D3: 0.06% vs 34.4% ordering violations); tool-batch timestamp semantics are undetermined, so time shares are reported under both assumptions.
- Duration fields contain implausible values (negative, and >1 h); see the outlier-contribution diagnostic. Tool time may include waiting for user confirmation; that cannot be separated here.
- ~2.7% of LLM calls have null token counts (all non-Success calls, `tool-model`, and some Success calls); ratios use calls with token counts only, sums skip them.
- `auto_continue` is null for ~56% of tool batches; its share is over the non-null batches only.
- Tool-call status 0 (3.4% of calls) is undocumented and reported as observed.
- Timestamps outside the 2026-06-01..07 window exist (0.1% of calls, down to 2019); kept and flagged.
- No quality, outcome or user-plan fields.
