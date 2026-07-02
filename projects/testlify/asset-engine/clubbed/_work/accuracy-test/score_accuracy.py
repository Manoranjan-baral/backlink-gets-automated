#!/usr/bin/env python3
"""Grade the production catalogue (rag.catalogue_for) against Claude-judged truth.

Reports, per stratum + overall:
  - recall_full      : recall vs ALL judged-relevant (harsh; incl. pages only query-
                       expansion surfaced — a CAPABILITY gap production can't rank).
  - recall_reachable : recall vs relevant pages the production methods (dense/keyword)
                       actually surfaced into the pool — isolates the RANKING gap.
  - capability_gap   : fraction of relevant pages ONLY expansion found (headroom that
                       needs a new feature — query expansion — not better ranking).
  - precision        : fraction of the catalogue that is judged-relevant (catches
                       recall gamed by dumping pages).
Outputs report.json + report.md.  SUFFIX env selects the file set (e.g. "_smoke").
"""
import csv, json, os, re, sys
import numpy as np
from collections import defaultdict
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK); import rag
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
IDX = os.path.join(WORK, "content-index")
CONTENT = os.path.join(REPO, "projects/testlify/content-database.csv")
SCORE_K = [50, 75, 100]
SUF = os.environ.get("SUFFIX", "")

_j = [json.loads(l) for l in open(os.path.join(HERE, f"judgments{SUF}.jsonl"))]
gt = {d["idx"]: set(d["relevant"]) for d in _j}
gt_core = {d["idx"]: set(d.get("core", [])) for d in _j}   # empty for pre-tier (smoke) judgments
HAS_CORE = any(gt_core.values())
meta = json.load(open(os.path.join(HERE, f"testset{SUF}.json")))
strat = {t["idx"]: t["stratum"] for t in meta}
assets = {t["idx"]: t["asset"] for t in meta}
pool_src = {}
for l in open(os.path.join(HERE, f"pool{SUF}.jsonl")):
    d = json.loads(l); pool_src[d["idx"]] = {c["url"]: set(c["sources"]) for c in d["candidates"]}

Vt, Mt = rag.load_vecs(os.path.join(IDX, "title")); Vb, Mb = rag.load_vecs(os.path.join(IDX, "body"))
urls = [m["url"] for m in Mt]; uidx = {u: i for i, u in enumerate(urls)}
body_uidx = np.array([uidx[m["url"]] for m in Mb])
tmap = {}
for row in csv.DictReader(open(CONTENT, encoding="utf-8")):
    tmap[(row.get("URL") or "").strip()] = row.get("Title") or ""
postings = rag.build_keyword_postings(urls, tmap)
kwmap = rag.load_topic_keywords(os.path.join(WORK, "topic_keywords.json"))
PROD_SOURCES = {"dense", "keyword"}   # what the production RAG can itself surface


def clean(a):
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", a or "")).strip() or "untitled"


def frac(a, b):
    return round(a / b, 3) if b else None


idxs = sorted(gt)
Q = rag.embed([clean(assets[i]) for i in idxs], "query"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
per_idea = []
agg = defaultdict(lambda: {"rfull": [], "rreach": [], "rcore": [], "prec": [], "preccore": [],
                           "capgap": [], **{f"r{k}": [] for k in SCORE_K}})
for j, i in enumerate(idxs):
    q = Q[j]; bb = np.full(len(urls), -1.0, np.float32); np.maximum.at(bb, body_uidx, Vb @ q)
    blended = rag.ALPHA * (Vt @ q) + (1 - rag.ALPHA) * bb
    dorder = [urls[k] for k in np.argsort(blended)[::-1] if not rag.foreign(urls[k])]
    rel = gt[i]
    if not rel:
        per_idea.append({"idx": i, "stratum": strat[i], "asset": assets[i], "n_relevant": 0,
                         "note": "no owned pages (nothing to recall — likely a novel topic)"})
        continue
    cat = rag.catalogue_for(dorder, i, kwmap, postings)   # production catalogue (RECALL_N + kw tail)
    catset = set(cat)
    rel_reach = {u for u in rel if pool_src.get(i, {}).get(u, set()) & PROD_SOURCES}
    r_full = frac(len(catset & rel), len(rel))
    r_reach = frac(len(catset & rel_reach), len(rel_reach))
    prec = frac(len(catset & rel), len(cat))
    cap_gap = frac(len(rel) - len(rel_reach), len(rel))
    core = gt_core.get(i, set())
    r_core = frac(len(catset & core), len(core)) if core else None      # recall on CORE pages
    prec_core = frac(len(catset & core), len(cat)) if HAS_CORE else None  # catalogue that is CORE
    missed = [u for u in rel if u not in catset]
    per_idea.append({"idx": i, "stratum": strat[i], "asset": assets[i], "n_relevant": len(rel),
                     "n_core": len(core), "catalogue_len": len(cat), "recall_full": r_full,
                     "recall_reachable": r_reach, "recall_core": r_core, "precision": prec,
                     "precision_core": prec_core, "capability_gap": cap_gap,
                     "missed": [{"url": u, "title": tmap.get(u, ""), "core": u in core,
                                 "pool_sources": sorted(pool_src.get(i, {}).get(u, []))} for u in missed]})
    s = agg[strat[i]]
    s["rfull"].append(r_full); s["prec"].append(prec)
    if r_reach is not None: s["rreach"].append(r_reach)
    if cap_gap is not None: s["capgap"].append(cap_gap)
    if r_core is not None: s["rcore"].append(r_core)
    if prec_core is not None: s["preccore"].append(prec_core)
    for k in SCORE_K:
        rk = frac(len(set(dorder[:k]) & rel), len(rel))
        if rk is not None: s[f"r{k}"].append(rk)


def mean(x):
    return round(sum(x) / len(x), 3) if x else None


def strat_row(v):
    return {"n": len(v["rfull"]), "recall_full": mean(v["rfull"]), "recall_reachable": mean(v["rreach"]),
            "recall_core": mean(v["rcore"]), "precision": mean(v["prec"]), "precision_core": mean(v["preccore"]),
            "capability_gap": mean(v["capgap"]), **{f"dense@{k}": mean(v[f"r{k}"]) for k in SCORE_K}}


scored = [p for p in per_idea if p.get("n_relevant", 0) > 0]
n_zero = sum(1 for p in per_idea if p.get("n_relevant", 0) == 0)
report = {"n_total": len(per_idea), "n_scored": len(scored), "n_zero_owned": n_zero, "suffix": SUF,
          "has_core_tiers": HAS_CORE,
          "overall": {"recall_full": mean([p["recall_full"] for p in scored]),
                      "recall_reachable": mean([p["recall_reachable"] for p in scored if p["recall_reachable"] is not None]),
                      "recall_core": mean([p["recall_core"] for p in scored if p["recall_core"] is not None]),
                      "precision": mean([p["precision"] for p in scored]),
                      "precision_core": mean([p["precision_core"] for p in scored if p["precision_core"] is not None]),
                      "capability_gap": mean([p["capability_gap"] for p in scored if p["capability_gap"] is not None])},
          "by_stratum": {s: strat_row(v) for s, v in agg.items()},
          "per_idea": per_idea}
json.dump(report, open(os.path.join(HERE, f"report{SUF}.json"), "w"), indent=1)

o = report["overall"]
core_hdr = " recall_core | precision_core |" if HAS_CORE else ""
core_sep = "---|---|" if HAS_CORE else ""
L = ["# RAG recall accuracy report" + (f" ({SUF})" if SUF else ""), "",
     f"Test set: {report['n_scored']} scored ideas (+{n_zero} with no owned pages) · Claude-judged pooled truth."
     + ("" if HAS_CORE else "  \n_(pre-tier judgments: core/peripheral not available — re-run judge_pool.py for tiers.)_"), "",
     f"**recall (full): {o['recall_full']}** · recall (reachable): {o['recall_reachable']}"
     + (f" · recall (core): {o['recall_core']}" if HAS_CORE else "")
     + f" · precision: {o['precision']}"
     + (f" · precision (core): {o['precision_core']}" if HAS_CORE else "")
     + f" · capability gap: {o['capability_gap']}", "",
     "- **recall_full** — vs all relevant, incl. pages only query-expansion found (harsh).",
     "- **recall_reachable** — vs pages production's own methods surfaced (the *ranking* gap).",
     "- **capability_gap** — share of relevant reachable ONLY via query expansion (a *feature* gap).",
     "- **precision** — share of the catalogue that is relevant (guards against dumping)."]
if HAS_CORE:
    L += ["- **recall_core / precision_core** — restricted to CORE pages (same intent), the headline that ignores peripheral noise."]
L += ["", "## By stratum", "",
      f"| stratum | n | recall_full | recall_reachable |{core_hdr} precision | capability_gap | dense@75 |",
      f"|---|---|---|---|{core_sep}---|---|---|"]
for s, v in report["by_stratum"].items():
    core_cells = f" {v['recall_core']} | {v['precision_core']} |" if HAS_CORE else ""
    L.append(f"| {s} | {v['n']} | {v['recall_full']} | {v['recall_reachable']} |{core_cells} "
             f"{v['precision']} | {v['capability_gap']} | {v['dense@75']} |")
L += ["", "## Biggest misses (lowest recall_full first)", ""]
for p in sorted(scored, key=lambda x: x["recall_full"]):
    if not p["missed"]:
        continue
    L.append(f"- **[{p['stratum']}] {p['asset'][:70]}** — recall_full {p['recall_full']}, "
             f"reachable {p['recall_reachable']}, missed {len(p['missed'])}/{p['n_relevant']}:")
    for m in p["missed"][:8]:
        L.append(f"    - {m['title'][:56]} ({m['url'].replace('https://testlify.com', '')}) "
                 f"— pool via {m['pool_sources']}")
L += ["", "> Limitation: ground truth = only as complete as the pool (dense ∪ Claude-expansion ∪ keyword).",
      "> recall_full includes expansion-only pages the production RAG cannot rank; recall_reachable is the",
      "> fair ranking number. The gap between them is the query-expansion opportunity."]
open(os.path.join(HERE, f"report{SUF}.md"), "w").write("\n".join(L))
print("overall:", report["overall"])
print("by stratum recall_full/reachable:",
      {s: (v["recall_full"], v["recall_reachable"]) for s, v in report["by_stratum"].items()})
