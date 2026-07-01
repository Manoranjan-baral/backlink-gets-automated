# RAG Recall Accuracy Test — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pooled, Claude-judged test that measures whether the reuse-check RAG finds the existing pages we own — outputting recall per stratum + a per-idea missed-pages list.

**Architecture:** Four standalone scripts under `_work/accuracy-test/`, chained by JSONL artifacts: build the test set → build a multi-source candidate pool → judge the pool with Claude (cached) → score the production catalogue against the judged truth. Reuses `rag.py` (retrieval, keyword index, `catalogue_for`) and `bench/` judging patterns.

**Tech Stack:** Python 3.9 (repo `.venv`), numpy, Voyage embeddings (via `rag.py`), Claude CLI (`env -u ANTHROPIC_API_KEY claude -p`) for judging.

## Global Constraints
- Run everything from repo root `/Users/devanshmehta/Desktop/SUTRA/backlink-gets-automated` with `.venv/bin/python`.
- `csv.field_size_limit(1 << 24)` in every script that reads `clubbed-ideas.csv` / `content-database.csv`.
- Exclude foreign-locale pages via `rag.foreign`.
- Claude calls MUST use `env -u ANTHROPIC_API_KEY` (nested-Claude "Invalid API key" gotcha).
- Artifacts + scripts live in `projects/testlify/asset-engine/clubbed/_work/accuracy-test/`.
- `SEED = 1337`. All sampling seeded and reproducible.
- Config constants (copy verbatim): `POOL_DENSE_N=100`, `POOL_EXPAND_Q=5`, `POOL_EXPAND_N=30`, `MAX_POOL=200`, `JUDGE_BATCH=15`, `SCORE_K=[50,75,100]`, `FRESH={"comparison":10,"entity":10,"random":10}`.
- Paths: `AT` = `projects/testlify/asset-engine/clubbed/_work/accuracy-test`; `WORK` = its parent (`_work`); `IDX` = `WORK/content-index`; `CLUBBED` = `projects/testlify/asset-engine/clubbed/clubbed-ideas.csv`; `CONTENT` = `projects/testlify/content-database.csv`; `BENCH` = `WORK/bench`.

---

### Task 1: `build_testset.py` — assemble the 80-idea test set

**Files:**
- Create: `projects/testlify/asset-engine/clubbed/_work/accuracy-test/build_testset.py`
- Reads: `bench/benchmark_assets.json` (fixed50), `clubbed-ideas.csv` (all 473 for fresh strata)
- Produces: `accuracy-test/testset.json`

**Interfaces:**
- Produces `testset.json`: `[{"idx": int, "asset": str, "stratum": "fixed50"|"comparison"|"entity"|"random"}]`

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Assemble 80-idea test set: fixed 50 (bench) + stratified fresh 30 (seeded)."""
import csv, json, os, random, re
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
CLUBBED = os.path.join(REPO, "projects/testlify/asset-engine/clubbed/clubbed-ideas.csv")
BENCH = os.path.join(WORK, "bench", "benchmark_assets.json")
SEED = 1337; FRESH = {"comparison": 10, "entity": 10, "random": 10}

rows = list(csv.DictReader(open(CLUBBED, encoding="utf-8")))
fixed = json.load(open(BENCH))
fixed_idx = {a["idx"] for a in fixed}
testset = [{"idx": a["idx"], "asset": a["asset"], "stratum": "fixed50"} for a in fixed]

pool = [(i, (r.get("Asset") or "").strip()) for i, r in enumerate(rows)
        if i not in fixed_idx and (r.get("Asset") or "").strip()]
def is_comp(a): return bool(re.search(r"\bvs\.?\b", a, re.I))
def is_entity(a):
    # entity-heavy heuristic: a short-ish title with a capitalized product/proper-noun run,
    # not a comparison. Refine if judging shows noise.
    head = a.split(":")[0]
    caps = re.findall(r"\b[A-Z][a-zA-Z0-9]+\b", head)
    return (not is_comp(a)) and len(head.split()) <= 8 and len(caps) >= 2

rnd = random.Random(SEED)
comp = [p for p in pool if is_comp(p[1])]
ent = [p for p in pool if is_entity(p[1])]
rnd.shuffle(comp); rnd.shuffle(ent)
picked = set()
def take(cands, n, stratum):
    out = []
    for i, a in cands:
        if len(out) >= n: break
        if i in picked: continue
        picked.add(i); out.append({"idx": i, "asset": a, "stratum": stratum})
    return out
testset += take(comp, FRESH["comparison"], "comparison")
testset += take(ent, FRESH["entity"], "entity")
rest = [p for p in pool if p[0] not in picked]; rnd.shuffle(rest)
testset += take(rest, FRESH["random"], "random")

json.dump(testset, open(os.path.join(HERE, "testset.json"), "w"), indent=0)
from collections import Counter
print("testset:", len(testset), dict(Counter(t["stratum"] for t in testset)))
```

- [ ] **Step 2: Run it**

Run: `cd <repo> && .venv/bin/python projects/testlify/asset-engine/clubbed/_work/accuracy-test/build_testset.py`
Expected: `testset: 80 {'fixed50': 50, 'comparison': 10, 'entity': 10, 'random': 10}` (comparison/entity may be < 10 if the corpus lacks enough — if so, the shortfall is topped up from random; note it in output).

- [ ] **Step 3: Verify shape**

Run: `.venv/bin/python -c "import json;d=json.load(open('projects/testlify/asset-engine/clubbed/_work/accuracy-test/testset.json'));assert len(d)==80;assert len({x['idx'] for x in d})==80;print('ok, unique idx:',len(d))"`
Expected: `ok, unique idx: 80`

- [ ] **Step 4: Commit**

```bash
git add projects/testlify/asset-engine/clubbed/_work/accuracy-test/build_testset.py projects/testlify/asset-engine/clubbed/_work/accuracy-test/testset.json
git commit -m "accuracy-test: build 80-idea test set (fixed50 + stratified fresh 30)"
```

---

### Task 2: `build_pool.py` — multi-source candidate pool

**Files:**
- Create: `accuracy-test/build_pool.py`
- Reads: `testset.json`, `content-index/`, `content-database.csv`, `topic_keywords.json`
- Produces: `accuracy-test/pool.jsonl`

**Interfaces:**
- Consumes `testset.json` (Task 1).
- Consumes from `rag.py`: `load_vecs`, `embed`, `foreign`, `build_keyword_postings`, `load_topic_keywords`, `ALPHA`.
- Consumes from Task 2a helper `expand_queries(asset) -> list[str]` (below).
- Produces `pool.jsonl`: one line per idea `{"idx": int, "candidates": [{"url": str, "title": str, "sources": ["dense"|"expand"|"keyword"]}]}`.

- [ ] **Step 1: Write `expand_queries` (Claude sub-angle query generation) as a helper in the same file**

```python
def expand_queries(asset, n=5):
    """Claude splits the asset into up to n sub-angle search queries (JSON list)."""
    import subprocess, json as _j
    prompt = ("Given this content asset idea, output ONLY a JSON array of up to %d short "
              "search queries capturing its distinct sub-angles (for retrieving existing "
              "articles on each angle). No prose.\n\nASSET: %s" % (n, asset))
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        out = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True,
                             env=env, timeout=120).stdout
        m = re.search(r"\[.*\]", out, re.S)
        qs = _j.loads(m.group(0)) if m else []
        return [q for q in qs if isinstance(q, str) and q.strip()][:n]
    except Exception as e:
        print("   expand fallback:", str(e)[:60]); return []
```

- [ ] **Step 2: Write the pooler body**

```python
#!/usr/bin/env python3
"""Build a multi-source candidate pool per idea: dense-wide ∪ Claude-expansion-dense ∪ keyword."""
import csv, json, os, re, sys
import numpy as np
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK); import rag
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
IDX = os.path.join(WORK, "content-index")
CONTENT = os.path.join(REPO, "projects/testlify/content-database.csv")
POOL_DENSE_N = 100; POOL_EXPAND_Q = 5; POOL_EXPAND_N = 30; MAX_POOL = 200
# (paste expand_queries here)

Vt, Mt = rag.load_vecs(os.path.join(IDX, "title")); Vb, Mb = rag.load_vecs(os.path.join(IDX, "body"))
urls = [m["url"] for m in Mt]; uidx = {u: i for i, u in enumerate(urls)}
body_uidx = np.array([uidx[m["url"]] for m in Mb])
tmap = {}
for row in csv.DictReader(open(CONTENT, encoding="utf-8")):
    tmap[(row.get("URL") or "").strip()] = row.get("Title") or ""
postings = rag.build_keyword_postings(urls, tmap)
kwmap = rag.load_topic_keywords(os.path.join(WORK, "topic_keywords.json"))

def dense_order(qtext):
    Q = rag.embed([qtext], "query"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9); q = Q[0]
    bb = np.full(len(urls), -1.0, np.float32); np.maximum.at(bb, body_uidx, Vb @ q)
    blended = rag.ALPHA * (Vt @ q) + (1 - rag.ALPHA) * bb
    return [urls[k] for k in np.argsort(blended)[::-1] if not rag.foreign(urls[k])]

def clean(a): return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", a or "")).strip() or "untitled"

testset = json.load(open(os.path.join(HERE, "testset.json")))
out = open(os.path.join(HERE, "pool.jsonl"), "w")
for t in testset:
    idx, asset = t["idx"], t["asset"]
    src = {}   # url -> set(sources)
    for u in dense_order(clean(asset))[:POOL_DENSE_N]: src.setdefault(u, set()).add("dense")
    for sq in expand_queries(asset, POOL_EXPAND_Q):
        for u in dense_order(sq)[:POOL_EXPAND_N]: src.setdefault(u, set()).add("expand")
    for u in rag.keyword_hits(kwmap.get(idx, []), _AllPost := postings) if False else []:  # see note
        pass
    # keyword source: ungated (all curated phrases) — use a local ungated matcher:
    for p in kwmap.get(idx, []):
        toks = rag._kw_toks(p)
        if not toks: continue
        sets = [postings.get(x, set()) for x in toks]
        if all(sets):
            for u in set.intersection(*sets): src.setdefault(u, set()).add("keyword")
    cands = [{"url": u, "title": tmap.get(u, ""), "sources": sorted(s)} for u, s in src.items()]
    if len(cands) > MAX_POOL:   # keep expand+keyword, fill rest by dense presence
        pri = [c for c in cands if set(c["sources"]) & {"expand", "keyword"}]
        fill = [c for c in cands if c not in pri][: MAX_POOL - len(pri)]
        cands = (pri + fill)[:MAX_POOL]
    out.write(json.dumps({"idx": idx, "candidates": cands}) + "\n")
    print(f"  idx {idx}: pool {len(cands)}", file=sys.stderr)
out.close(); print("wrote pool.jsonl")
```

> Note: the `keyword_hits`/`_AllPost` dead branch above is illustrative — implement the ungated keyword loop shown (do NOT DF-gate here; the pool wants max completeness). Remove the `if False` line.

- [ ] **Step 3: Smoke run on 2 ideas**

Run: `.venv/bin/python -c "import json;d=json.load(open('.../testset.json'))[:2];json.dump(d,open('.../testset.json','w'))"` is destructive — instead smoke by temporarily slicing: add `testset = testset[:2]` guarded by `if os.environ.get('SMOKE'):`. Then:
`SMOKE=1 .venv/bin/python .../build_pool.py`
Expected: 2 `idx ...: pool N` lines with `20 <= N <= 200`.

- [ ] **Step 4: Full run**

Run: `.venv/bin/python projects/testlify/asset-engine/clubbed/_work/accuracy-test/build_pool.py 2> pool.log`
Expected: 80 pool lines; `wc -l pool.jsonl` == 80.

- [ ] **Step 5: Verify pool composition**

Run: `.venv/bin/python -c "import json;L=[json.loads(l) for l in open('.../pool.jsonl')];import statistics as s;sz=[len(x['candidates']) for x in L];print('ideas',len(L),'median pool',s.median(sz),'max',max(sz))"`
Expected: 80 ideas, median pool 80–200.

- [ ] **Step 6: Commit**

```bash
git add projects/testlify/asset-engine/clubbed/_work/accuracy-test/build_pool.py projects/testlify/asset-engine/clubbed/_work/accuracy-test/pool.jsonl
git commit -m "accuracy-test: multi-source candidate pooler (dense ∪ expand ∪ keyword)"
```

---

### Task 3: `judge_pool.py` — Claude relevance judging (cached)

**Files:**
- Create: `accuracy-test/judge_pool.py`
- Reads: `pool.jsonl`, `content-database.csv` (body snippets), existing `judgments.jsonl` (cache)
- Produces / appends: `accuracy-test/judgments.jsonl`

**Interfaces:**
- Consumes `pool.jsonl` (Task 2), `testset.json` (for asset text).
- Produces `judgments.jsonl`: one line per idea `{"idx": int, "relevant": [url, ...]}`; plus a cache line format `{"pair": [idx, url], "rel": bool}` in `judge_cache.jsonl`.

- [ ] **Step 1: Write the judge**

```python
#!/usr/bin/env python3
"""Claude judges each pooled candidate relevant/not to the idea. Cached by (idx,url)."""
import csv, json, os, re, subprocess, sys
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
CONTENT = os.path.join(REPO, "projects/testlify/content-database.csv")
JUDGE_BATCH = 15
cmap = {}
for row in csv.DictReader(open(CONTENT, encoding="utf-8")):
    cmap[(row.get("URL") or "").strip()] = (row.get("Full content") or "")[:600]
assets = {t["idx"]: t["asset"] for t in json.load(open(os.path.join(HERE, "testset.json")))}
cache_p = os.path.join(HERE, "judge_cache.jsonl")
cache = {}
if os.path.exists(cache_p):
    for l in open(cache_p):
        d = json.loads(l); cache[tuple(d["pair"])] = d["rel"]
cache_f = open(cache_p, "a")

def judge_batch(asset, batch):   # batch: list[(url,title)]
    listing = "\n".join(f"{i+1}. {t} — {cmap.get(u,'')[:300]}" for i, (u, t) in enumerate(batch))
    prompt = ("You decide which EXISTING pages we already own are relevant to a content idea "
              "(same topic; a page that would compete for the same search intent). "
              "Reply ONLY a JSON array of the numbers that are relevant.\n\n"
              f"IDEA: {asset}\n\nPAGES:\n{listing}")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    out = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, env=env, timeout=180).stdout
    m = re.search(r"\[.*\]", out, re.S)
    nums = set(json.loads(m.group(0))) if m else set()
    return [batch[i-1][0] for i in nums if 1 <= i <= len(batch)]

pool = [json.loads(l) for l in open(os.path.join(HERE, "pool.jsonl"))]
res_f = open(os.path.join(HERE, "judgments.jsonl"), "w")
for row in pool:
    idx = row["idx"]; asset = assets[idx]; relevant = []
    todo = [(c["url"], c["title"]) for c in row["candidates"] if (idx, c["url"]) not in cache]
    for u, t in [(c["url"], c["title"]) for c in row["candidates"] if (idx, c["url"]) in cache]:
        if cache[(idx, u)]: relevant.append(u)
    for i in range(0, len(todo), JUDGE_BATCH):
        batch = todo[i:i+JUDGE_BATCH]
        rel = set(judge_batch(asset, batch))
        for u, t in batch:
            r = u in rel; cache[(idx, u)] = r
            cache_f.write(json.dumps({"pair": [idx, u], "rel": r}) + "\n"); cache_f.flush()
            if r: relevant.append(u)
    res_f.write(json.dumps({"idx": idx, "relevant": sorted(set(relevant))}) + "\n")
    print(f"  idx {idx}: {len(relevant)} relevant / {len(row['candidates'])} judged", file=sys.stderr)
res_f.close(); print("wrote judgments.jsonl")
```

- [ ] **Step 2: Smoke run on first idea only**

Add `pool = pool[:1]` under `if os.environ.get("SMOKE"):`. Run `SMOKE=1 .venv/bin/python .../judge_pool.py`.
Expected: one `idx N: M relevant / P judged` line, `0 < M <= P`. Confirms Claude CLI works (no "Invalid API key").

- [ ] **Step 3: Full run**

Run: `.venv/bin/python projects/testlify/asset-engine/clubbed/_work/accuracy-test/judge_pool.py 2> judge.log`
Expected: 80 lines in `judgments.jsonl`. (Long — 800–1,200 Claude calls. Run in background.)

- [ ] **Step 4: Verify cache re-use**

Re-run the full command. Expected: same 80 lines, but `judge.log` shows work is instant (all pairs cached, 0 new `claude` calls). Confirm by timing (< 30s second run).

- [ ] **Step 5: Commit** (cache + judgments are the expensive asset — commit them)

```bash
git add projects/testlify/asset-engine/clubbed/_work/accuracy-test/judge_pool.py \
        projects/testlify/asset-engine/clubbed/_work/accuracy-test/judgments.jsonl \
        projects/testlify/asset-engine/clubbed/_work/accuracy-test/judge_cache.jsonl
git commit -m "accuracy-test: Claude relevance judging (cached by idx,url)"
```

---

### Task 4: `score_accuracy.py` — grade production catalogue, write report

**Files:**
- Create: `accuracy-test/score_accuracy.py`
- Reads: `testset.json`, `judgments.jsonl`, `pool.jsonl`, index, `content-database.csv`, `topic_keywords.json`
- Produces: `accuracy-test/report.json`, `accuracy-test/report.md`

**Interfaces:**
- Consumes `judgments.jsonl` (Task 3), `testset.json`, `pool.jsonl`.
- Consumes from `rag.py`: `load_vecs`, `embed`, `foreign`, `build_keyword_postings`, `load_topic_keywords`, `catalogue_for`, `ALPHA`, `RECALL_N`.

- [ ] **Step 1: Write the scorer**

```python
#!/usr/bin/env python3
"""Grade the production catalogue (rag.catalogue_for) against Claude-judged truth."""
import csv, json, os, re, sys
import numpy as np
from collections import defaultdict
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK); import rag
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
IDX = os.path.join(WORK, "content-index"); CONTENT = os.path.join(REPO, "projects/testlify/content-database.csv")
SCORE_K = [50, 75, 100]
gt = {d["idx"]: set(d["relevant"]) for d in (json.loads(l) for l in open(os.path.join(HERE, "judgments.jsonl")))}
strat = {t["idx"]: t["stratum"] for t in json.load(open(os.path.join(HERE, "testset.json")))}
assets = {t["idx"]: t["asset"] for t in json.load(open(os.path.join(HERE, "testset.json")))}
pool_src = {}
for l in open(os.path.join(HERE, "pool.jsonl")):
    d = json.loads(l); pool_src[d["idx"]] = {c["url"]: c["sources"] for c in d["candidates"]}

Vt, Mt = rag.load_vecs(os.path.join(IDX, "title")); Vb, Mb = rag.load_vecs(os.path.join(IDX, "body"))
urls = [m["url"] for m in Mt]; uidx = {u: i for i, u in enumerate(urls)}
body_uidx = np.array([uidx[m["url"]] for m in Mb])
tmap = {}
for row in csv.DictReader(open(CONTENT, encoding="utf-8")):
    tmap[(row.get("URL") or "").strip()] = row.get("Title") or ""
postings = rag.build_keyword_postings(urls, tmap); kwmap = rag.load_topic_keywords(os.path.join(WORK, "topic_keywords.json"))
def clean(a): return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", a or "")).strip() or "untitled"
def rec(pred, rel): return len(set(pred) & rel) / len(rel) if rel else None

idxs = sorted(gt)
Q = rag.embed([clean(assets[i]) for i in idxs], "query"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
per_idea = []; by_strat = defaultdict(lambda: {"cat": [], **{f"r{k}": [] for k in SCORE_K}})
for j, i in enumerate(idxs):
    q = Q[j]; bb = np.full(len(urls), -1.0, np.float32); np.maximum.at(bb, body_uidx, Vb @ q)
    dorder = [urls[k] for k in np.argsort(rag.ALPHA * (Vt @ q) + (1 - rag.ALPHA) * bb)[::-1] if not rag.foreign(urls[k])]
    rel = gt[i]
    cat = rag.catalogue_for(dorder, i, kwmap, postings)   # production catalogue (RECALL_N + kw tail)
    r_cat = rec(cat, rel)
    missed = [u for u in rel if u not in set(cat)]
    per_idea.append({"idx": i, "stratum": strat[i], "asset": assets[i], "n_relevant": len(rel),
                     "recall_catalogue": r_cat, "missed": [{"url": u, "title": tmap.get(u, ""),
                     "pool_sources": pool_src.get(i, {}).get(u, [])} for u in missed]})
    s = by_strat[strat[i]]
    if r_cat is not None: s["cat"].append(r_cat)
    for k in SCORE_K:
        rk = rec(dorder[:k], rel)
        if rk is not None: s[f"r{k}"].append(rk)
def mean(x): return round(sum(x) / len(x), 3) if x else None
report = {"n": len(idxs),
          "overall": {"recall_catalogue": mean([p["recall_catalogue"] for p in per_idea if p["recall_catalogue"] is not None]),
                      **{f"dense@{k}": mean(sum([by_strat[s][f"r{k}"] for s in by_strat], [])) for k in SCORE_K}},
          "by_stratum": {s: {"n": len(v["cat"]), "recall_catalogue": mean(v["cat"]),
                             **{f"dense@{k}": mean(v[f"r{k}"]) for k in SCORE_K}} for s, v in by_strat.items()},
          "per_idea": per_idea}
json.dump(report, open(os.path.join(HERE, "report.json"), "w"), indent=1)

# markdown
L = ["# RAG recall accuracy report", "",
     f"Test set: {report['n']} ideas (Claude-judged pooled ground truth).", "",
     f"**Overall catalogue recall: {report['overall']['recall_catalogue']}**", "",
     "## By stratum", "", "| stratum | n | catalogue | dense@50 | dense@75 | dense@100 |",
     "|---|---|---|---|---|---|"]
for s, v in report["by_stratum"].items():
    L.append(f"| {s} | {v['n']} | {v['recall_catalogue']} | {v['dense@50']} | {v['dense@75']} | {v['dense@100']} |")
L += ["", "## Biggest misses (per idea)", ""]
for p in sorted(per_idea, key=lambda x: (x["recall_catalogue"] if x["recall_catalogue"] is not None else 1)):
    if not p["missed"]: continue
    L.append(f"- **[{p['stratum']}] {p['asset'][:70]}** — recall {p['recall_catalogue']}, missed {len(p['missed'])}:")
    for m in p["missed"][:8]:
        L.append(f"    - {m['title'][:60]} ({m['url'].replace('https://testlify.com','')}) — found by pool via {m['pool_sources']}")
L += ["", "> Limitation: ground truth is only as complete as the pool (dense ∪ Claude-expansion ∪ keyword);",
      "> a page no source surfaced is invisible. Pool sizes in pool.jsonl."]
open(os.path.join(HERE, "report.md"), "w").write("\n".join(L))
print("overall catalogue recall:", report["overall"]["recall_catalogue"])
print("by stratum:", {s: v["recall_catalogue"] for s, v in report["by_stratum"].items()})
```

- [ ] **Step 2: Run it**

Run: `.venv/bin/python projects/testlify/asset-engine/clubbed/_work/accuracy-test/score_accuracy.py 2>/dev/null`
Expected: prints `overall catalogue recall: <float>` and a per-stratum dict; writes `report.json` + `report.md`.

- [ ] **Step 3: Validate against known number (acceptance criterion)**

The `fixed50` stratum recall should land near the known hybrid@75 ≈ 0.81 (within ~±0.05 — judging differs slightly from the frozen `groundtruth.jsonl`, so exact match isn't expected).
Run: `.venv/bin/python -c "import json;r=json.load(open('.../report.json'));print('fixed50 catalogue recall:',r['by_stratum']['fixed50']['recall_catalogue'])"`
Expected: ~0.75–0.86. If wildly off, stop and inspect judging quality before trusting fresh strata.

- [ ] **Step 4: Eyeball report.md**

Run: `sed -n '1,40p' projects/testlify/asset-engine/clubbed/_work/accuracy-test/report.md`
Expected: readable headline + per-stratum table + missed-pages lists with pool-source annotations.

- [ ] **Step 5: Commit**

```bash
git add projects/testlify/asset-engine/clubbed/_work/accuracy-test/score_accuracy.py \
        projects/testlify/asset-engine/clubbed/_work/accuracy-test/report.json \
        projects/testlify/asset-engine/clubbed/_work/accuracy-test/report.md
git commit -m "accuracy-test: score production catalogue vs judged truth + report"
```

---

### Task 5: End-to-end doc + README

**Files:**
- Create: `accuracy-test/README.md`

- [ ] **Step 1: Write a short run-order README**

```markdown
# RAG recall accuracy test
Run order (from repo root, with .venv):
1. build_testset.py   -> testset.json     (fixed50 + stratified fresh 30)
2. build_pool.py      -> pool.jsonl        (dense ∪ Claude-expansion ∪ keyword)
3. judge_pool.py      -> judgments.jsonl   (Claude, cached by idx,url; long first run)
4. score_accuracy.py  -> report.md/json    (recall per stratum + missed-pages)
Re-running after a rag.py change: rerun step 4 only (judgments cached).
Ground truth = only as complete as the pool (stated limitation).
```

- [ ] **Step 2: Commit**

```bash
git add projects/testlify/asset-engine/clubbed/_work/accuracy-test/README.md
git commit -m "accuracy-test: run-order README"
```

---

## Self-Review

**Spec coverage:** test set (T1) ✓, 3-source pool incl. anti-bias expansion source (T2) ✓, cached Claude judging (T3) ✓, per-stratum scoring + missed-pages diff + limitation note (T4) ✓, repeatability via cache (T3 step 4, T4) ✓, acceptance criterion "fixed50 reproduces ~0.81" (T4 step 3) ✓. BM25 correctly omitted (spec: deferred). HTML viewer omitted (spec: v2).

**Placeholder scan:** the `if False`/`_AllPost` line in T2 is explicitly flagged as illustrative with the real loop shown beneath — implementer removes it. No other TODOs.

**Type consistency:** `testset.json` {idx,asset,stratum}, `pool.jsonl` {idx,candidates[{url,title,sources}]}, `judgments.jsonl` {idx,relevant[]} — consumed consistently across T2/T3/T4. `rag.catalogue_for(dense_order, idx, kwmap, postings)` signature matches `rag.py`.
