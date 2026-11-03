# GHCP trace pipeline — Antigravity kickstart kit

A bounded-memory DuckDB pipeline for the 7-day GitHub Copilot agentic-session trace
(3.22 GB compressed; 301,026 sessions; 9.3M LLM calls). Everything on `D:\`.

## Dataset & Attribution
- **Dataset**: GitHub Copilot agentic-session trace (June 1–7, 2026; 301,026 sessions; 1,189,581 turns; 9,310,255 LLM calls; 8,681,190 tool calls).
- **Source**: Azure Public Dataset `ghcp-coding-agent-2026`.
- **License**: Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
- **Attribution**: GitHub Copilot Trace Team / Microsoft Azure Public Datasets.
- **Cost Disclaimer**: Every cost figure in this pipeline is strictly **hypothetical** and represents parameterized sensitivity scenarios in relative units. **This is not money or billing data**. Model identities are anonymized and no actual prices exist in the corpus.

## How to Reproduce
Make the base storage path configurable via `GHCP_BASE` (default `D:\ghcp\data`), run `setup.ps1`, then execute the pipeline:
```powershell
$env:GHCP_BASE = "D:\ghcp\data"  # or your preferred storage drive/path
powershell -File setup.ps1
python -m ghcp selftest ; python -m ghcp download ; python -m ghcp ingest ; python -m ghcp validate ; python -m ghcp analyze ; python -m ghcp benchmark ; python -m ghcp plots ; python -m ghcp report ; python -m ghcp bundle
```

## Presentation & Demo
- **Demo Video**: [Google Drive / YouTube Link Placeholder]
- **Slide Deck**: Presentation deck PDF export and slides available in the repository.

## Start in 5 steps
1. Unzip to `D:\ghcp-kit`.
2. Open that folder as the workspace in Antigravity.
3. Open `START_PROMPT.md`, paste its contents as your first message to the agent.
4. Reply "go" after it restates the goal and constraints.
5. At each GATE the agent stops. Read its evidence; reply "continue" or give direction.

If Antigravity does not pick up `AGENTS.md` automatically, paste it into the agent's rules (`GEMINI.md`
is an identical copy). I have not verified Antigravity's rule-file conventions.

## What is in the kit
| file | purpose |
|---|---|
| `AGENTS.md` / `GEMINI.md` | binding rules + working principles |
| `SPEC.md` | goal, schema, tables, analyses, success criteria |
| `PLAN.md` | stages S0–S10, each with a "Done when" check and gates |
| `KNOWN_FACTS.md` | verified facts vs assumptions vs unknowns |
| `ghcp/` | Python package (`python -m ghcp <command>`) |
| `sql/ingest_shard.sql`, `sql/analysis/*.sql` | all SQL, one CSV per `-- @@ csv:` chunk |
| `setup.ps1` | creates venv/pip cache/temp on D: |

## Commands
`selftest · download · probe · ingest · validate · analyze · benchmark · plots · report · bundle · status`

## Safety design
- Archives are streamed shard-by-shard (no full extraction); one ~500-session shard is staged at a time.
- DuckDB: 1000 MB memory limit, 2 threads, 4 GB spill cap, spill dir on D:.
- A background guard logs RSS/CPU/RAM/disk to `logs\perf.csv` every 5 s and **stops safely** if RSS > 1500 MB,
  system RAM available < 250 MB, free D: < 10 GB, or data dir > 15 GB (exit code 3, progress kept).
- Ingestion is resumable: `state\state.db` records each finished shard; output counts are verified per shard
  before it is published (write to `.tmp`, then atomic rename).

## Honest status
- Tested by the author: fixture generation, tar streaming, schema probe, checkpoint DB, resource guard, SQL file parsing.
- **Not tested by the author:** anything that runs DuckDB or Polars, and anything on the real data
  (DuckDB could not be installed in the authoring environment). Stage S1 (`selftest`) is the first proof;
  expect to fix a few SQL dialect details surgically.
- Numbers from the team's audit (4 negative latencies, 0.98% cross-turn references) are treated as unconfirmed.

## Send back for review
After S9, send `D:\ghcp\data\outputs_bundle.zip` (small CSV/JSON/PNG/MD only).
