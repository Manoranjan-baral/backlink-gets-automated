# RAG recall accuracy test — design spec

**Date:** 2026-07-01
**Status:** approved design → ready for implementation plan
**Area:** `projects/testlify/asset-engine/clubbed/_work/`

## 1. Purpose

Give an **honest, repeatable** answer to one question about the reuse-check RAG:

> For a given content idea, **does the RAG find the existing pages we already own** on that topic?

Output must be both:
- a **recall number** (overall + per stratum), and
- a per-idea **missed-pages list** (real examples to eyeball).

This measures the recall of the production Job-B catalogue (dense top-`RECALL_N` ∪ DF-gated keyword tail), using **Claude as the relevance oracle**.

### Non-goals (v1)
- Not testing the LLM reuse *verdict* (Brand-new / Improve / Reuse) — retrieval only.
- Not a live CI gate yet (design leaves the hook; wiring is later).
- Not full BM25 (YAGNI — add only if pool-completeness spot-check shows leakage).

## 2. Why pooling + Claude judge

No oracle can read all 9,669 pages per idea. Two naive options fail:
- Judge only the RAG's own output → **recall-blind** (can't see what RAG missed). This is the bias that inflated earlier numbers ~+0.15.
- Title-sweep all 9,669 titles → LLM "lost in the middle" + titles lack body context.

**Solution — TREC-style pooling:** build a candidate pool from *several retrievers*, Claude judges the pool, the union of judged-relevant is the ground truth. **Hard rule:** the pool MUST include sources the production RAG does *not* use, or grading is circular.

**Honest limitation (must be stated in the report):** truth is only as complete as the pool; a page no source surfaces stays invisible. Mitigated by diverse sources + an optional title-sweep spot-check to estimate the miss rate.

## 3. Components

### 3.1 Test set — `build_testset.py` → `testset.json`
80 ideas, seeded (reproducible):

| Stratum | Count | Source |
|---|---|---|
| `fixed50` | 50 | existing `bench/benchmark_assets.json` (continuity vs 0.40→0.81) |
| `comparison` | 10 | ideas whose Asset matches /\bvs\.?\b/i, from the remaining 423 |
| `entity` | 10 | entity-heavy ideas (short proper-noun / product-name titles); heuristic + seeded pick |
| `random` | 10 | uniform random from the remaining 423 |

Each entry: `{idx, asset, stratum}`. `idx` = row index in `clubbed-ideas.csv` (aligns with `topic_keywords.json`).

### 3.2 Candidate pool — `build_pool.py` → `pool.jsonl`
Per idea, union (dedup, non-foreign) of 3 sources:
1. **Dense wide** — production blended retrieval, top-100.
2. **Claude query-expansion → dense** — Claude generates 3–5 sub-angle queries from the asset; each dense top-30; union. *Primary independent recall booster.*
3. **Keyword/entity** — `rag.build_keyword_postings` matches (ungated, i.e. all curated phrases incl. generic) + title substring.

Cap pool at `MAX_POOL = 200`/idea (if over, keep all keyword+expansion hits, fill remainder by dense rank). Record per-candidate which source(s) found it (for pool-composition reporting).

Output line: `{idx, candidates: [{url, title, sources:[...]}]}`.

### 3.3 Judging (oracle) — `judge_pool.py` → `judgments.jsonl`
- For each idea, Claude labels each candidate **relevant / not** in batches (~15/call) using a tight rubric: *"a page we would consider we ALREADY OWN on this idea's topic — same subject, would compete for the same intent."* Reuse `label_groundtruth.py` patterns.
- Candidate text shown = title + body snippet (from `content-database.csv` `Full content`, truncated).
- **Cache** keyed by `(idx, url)`; skip already-judged pairs on re-run.
- Invoke Claude via `env -u ANTHROPIC_API_KEY` (nested-Claude "Invalid API key" gotcha).
- Output line: `{idx, relevant: [url, ...]}`.

### 3.4 Scoring — `score_accuracy.py` → `report.json` + `report.md`
- Ground truth per idea = judged-relevant set.
- Grade the **production catalogue** (as `rag.catalogue_for`, dense top-`RECALL_N` ∪ keyword tail) → recall + precision.
- Recall@K curve at K ∈ {50, 75, 100}, **broken down by stratum** (comparison/entity/random/fixed50) so weak spots don't hide in the average.
- Per-idea diff: `RAG found N · missed M → [titles/urls]`.

### 3.5 Report — `report.md` (v1)
Headline recall (overall + per-stratum table), recall@K table, pool-composition stats, and the per-idea missed-pages lists. *(Clickable HTML viewer deferred to v2.)*

## 4. File layout
New dir `projects/testlify/asset-engine/clubbed/_work/accuracy-test/`:
```
build_testset.py     fixed50 + stratified fresh 30 (seeded) -> testset.json
build_pool.py        3-source pooler -> pool.jsonl
judge_pool.py        Claude batched judging, cached -> judgments.jsonl
score_accuracy.py    grade production catalogue -> report.json + report.md
testset.json / pool.jsonl / judgments.jsonl / report.{json,md}   (artifacts)
```
Imports `rag.py` for `load_vecs`, `embed`, `foreign`, `build_keyword_postings`, `catalogue_for`, `load_topic_keywords`. Reuses `bench/` judging/metric patterns.

## 5. Config (tunable constants)
`SEED=1337`, `POOL_DENSE_N=100`, `POOL_EXPAND_Q=5`, `POOL_EXPAND_N=30`, `MAX_POOL=200`, `JUDGE_BATCH=15`, `SCORE_K=[50,75,100]`, `FRESH={comparison:10,entity:10,random:10}`.

## 6. Repeatability / regression use
Judgments cached by `(idx, url)` → re-running after a `rag.py` change re-runs only retrieval + scoring (seconds, ~free). Leaves a clean hook to later become a pass/fail gate (fail if recall drops > threshold vs a stored baseline).

## 7. Cost (first run; cached after)
- Query-expansion: 80 Claude calls.
- Judging: ~80 ideas × ~200 candidates ÷ 15/batch ≈ 800–1,200 Claude calls.
- Voyage embeds: batched, negligible.
Subsequent runs after code changes: ~0 (judgments cached).

## 8. Acceptance criteria
- `score_accuracy.py` prints overall recall + a per-stratum table + recall@K, and writes `report.md` with per-idea missed-pages lists.
- Re-running with unchanged corpus/testset re-uses cached judgments (0 new judge calls).
- The fixed50 recall reproduces the current benchmark (~0.81 @ hybrid K=75) within noise, validating the harness against the known number.
- Report explicitly states the pool-completeness limitation + pool-composition stats.
