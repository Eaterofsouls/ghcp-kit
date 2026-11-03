# KNOWN FACTS — what is verified, what is assumed, what is unknown

**[V]** verified from the original file/repo or an HTTP HEAD request · **[U-R]** reported by the user's own audit,
not seen by the author · **[A]** assumption · **[?]** unknown — to be resolved by the pipeline

## Dataset (source: Azure/AzurePublicDataset)
- [V] Release tag `ghcp-coding-agent-2026`; seven assets `date.2026-06-0N.tar.gz`; sizes in `ghcp/config.py`
  (HEAD, 2026-10-31); total 3,218,886,136 bytes.
- [V] `DATASET_CARD.md` counts: 301,026 sessions; 1,189,581 turns; 9,310,255 LLM calls; 7,767,261 tool batches;
  8,681,190 tool calls; 37 anonymised models; prompt 631.4B / completion 4.91B / cached 540.95B tokens.
- [V] Records are session-level nested JSON (see `SPEC.md` §2; read from `schema.json`). Metadata only: no code,
  prompts, responses, paths, repo names, user ids; model names relabelled "Model A, B…" ranked by usage.
- [V] Repo licence file is CC BY 4.0; the dataset page also says CC-BY and asks to cite arXiv:2608.00101
  (preprint, Liu, Qiu, Goiri, Fonseca, Bianchini, Choukse).
- [V] Sampling: "fixed sampling rate across all dates", non-enterprise users, agentic-mode sessions only.
- [V] The paper analyses a larger corpus (~13M sessions); this release is a 301K-session sample. Do not compare
  absolute counts with the paper.

## Unknown / to be resolved
- [?] Sampling rate. [?] Uncompressed size (expect many GB; do not extract archives).
- [?] Format of `manifest.json` (probe prints it). [?] Whether `cached_pct` is 0–1 or 0–100 (probe prints range).
- [?] Exact meaning of `tokens.cached` (prompt-cache hits vs something else). Treat as "cached prompt tokens as reported".
- [?] Whether `timestamp` is event start or end. [A] start. `validate` probes this.
- [?] Real column types (e.g. `status_code` string vs int). The probe reveals mismatches.
- [?] Number of prompt segments (`prompt_segments` rows). Likely the largest table.

## Reported by the team's audit (not seen by the author) — confirm or contradict
- [U-R] Four negative LLM latencies. [U-R] 0.98% of tool batches reference an LLM call in a different turn.
- [U-R] "Unusual historical timestamps". Treat all three as hypotheses; report observed counts.
- [U-R] Hardware: 12 GB installed RAM, only ~1.79 GB available during the audit; C: has 23.34 GB free; use D:.

## Not available, therefore never claimed
Prices, billing, real model identities, user plan, task success/quality, enterprise sessions, causality.
