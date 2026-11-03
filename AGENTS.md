# AGENT RULES — read fully before doing anything

You are executing a pre-specified data pipeline on the user's Windows machine. The spec is
already decided. Your job is to **run it, verify it, and report evidence** — not to redesign it.

## Working principles (Karpathy-style, applied to this repo)

1. **Think before coding.** State your assumptions and what you are about to do. If something is
   ambiguous or a result surprises you, say so and stop; do not guess silently.
2. **Simplicity first.** Write the minimum that satisfies the spec. No new abstractions, no
   frameworks, no "while I'm here" features.
3. **Surgical changes.** If code or SQL fails, fix only the failing statement. Do not refactor.
   Log every change you make to code/SQL in `CHANGELOG_AGENT.md` (file, line/statement, why,
   the error text that triggered it).
4. **Goal-driven execution.** Every stage in `PLAN.md` has a "Done when" check. A stage is not
   done until you have run the check and pasted the actual command output. Never write
   "should work" or "completed" without evidence.

## Hard constraints (violating any of these = stop and report)

- **Storage:** everything under `D:\` (`GHCP_BASE=D:\ghcp\data`). Never write datasets, extracted
  files, Parquet, DuckDB temp files, pip cache or venv to `C:`. Never extract a full archive.
- **Memory:** machine has ~1.79 GB RAM available. DuckDB `memory_limit` is 1000 MB, 2 threads.
  Never load a whole table into pandas/Polars eager frames. If the guard stops a run, **do not raise
  the limits**; report `logs\STOP_REASON.txt` and wait for the user.
- **Engine:** DuckDB is primary. Polars only inside `benchmark`. **Do not install Spark/Java/Hadoop.**
- **No dashboard** and no web app. Static figures and a Markdown report only.
- **Do not delete or "fix" anomalies.** Negative latencies, cross-turn tool-batch references,
  odd timestamps are data. Count them, report them, keep them.
- **Money:** there are no prices, no real model names, no billing data. Never output a currency
  figure. The only cost-like numbers are the relative-unit scenarios in
  `sql/analysis/06_hypothetical_sensitivity.sql`, always labelled HYPOTHETICAL.
- **Network:** only the seven GitHub release URLs in `ghcp/config.py` and `pip install -r requirements.txt`.
- **Archives are read-only.** Never modify, move or delete files in `raw\`.
- **Don't change the research scope** (see `SPEC.md`). If you think it should change, say why and stop.
- **Don't claim results you did not observe.** If a command was not run, say it was not run.

## Reporting format after every stage

```
STAGE: <id and name>
COMMAND(S): <exact commands run>
OUTPUT: <the real, trimmed output>
DONE-WHEN CHECK: PASS | FAIL — <which condition, with numbers>
CHANGES MADE: <none | list, also in CHANGELOG_AGENT.md>
RESOURCES: <peak RSS MB, data dir GB, free D: GB — from logs\guard_summary_*.json>
NEXT: <next stage, or STOP + reason>
```

## When blocked

Stop. Write what you tried, the exact error, and one or two options. Do not work around a block by
loosening a limit, switching engine, sampling instead of using the full data, or skipping validation.

*(If Antigravity does not auto-load this file as workspace rules, paste it into the agent's rules
or at the start of the conversation. A copy named GEMINI.md is included.)*
