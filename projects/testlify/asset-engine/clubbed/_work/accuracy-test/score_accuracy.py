#!/usr/bin/env python3
"""Grade the production catalogue (rag.catalogue_for) against Claude-judged truth.
Outputs report.json + report.md (per-stratum recall + per-idea missed-pages).
SUFFIX env selects the file set (e.g. "_smoke").
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

gt = {d["idx"]: set(d["relevant"]) for d in (json.loads(l) for l in open(os.path.join(HERE, f"judgments{SUF}.jsonl")))}
meta = json.load(open(os.path.join(HERE, f"testset{SUF}.json")))
strat = {t["idx"]: t["stratum"] for t in meta}
assets = {t["idx"]: t["asset"] for t in meta}
pool_src = {}
for l in open(os.path.join(HERE, f"pool{SUF}.jsonl")):
    d = json.loads(l); pool_src[d["idx"]] = {c["url"]: c["sources"] for c in d["candidates"]}

Vt, Mt = rag.load_vecs(os.path.join(IDX, "title")); Vb, Mb = rag.load_vecs(os.path.join(IDX, "body"))
urls = [m["url"] for m in Mt]; uidx = {u: i for i, u in enumerate(urls)}
body_uidx = np.array([uidx[m["url"]] for m in Mb])
tmap = {}
for row in csv.DictReader(open(CONTENT, encoding="utf-8")):
    tmap[(row.get("URL") or "").strip()] = row.get("Title") or ""
postings = rag.build_keyword_postings(urls, tmap)
kwmap = rag.load_topic_keywords(os.path.join(WORK, "topic_keywords.json"))


def clean(a):
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", a or "")).strip() or "untitled"


def rec(pred, rel):
    return len(set(pred) & rel) / len(rel) if rel else None


idxs = sorted(gt)
Q = rag.embed([clean(assets[i]) for i in idxs], "query"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
per_idea = []
by_strat = defaultdict(lambda: {"cat": [], **{f"r{k}": [] for k in SCORE_K}})
for j, i in enumerate(idxs):
    q = Q[j]; bb = np.full(len(urls), -1.0, np.float32); np.maximum.at(bb, body_uidx, Vb @ q)
    blended = rag.ALPHA * (Vt @ q) + (1 - rag.ALPHA) * bb
    dorder = [urls[k] for k in np.argsort(blended)[::-1] if not rag.foreign(urls[k])]
    rel = gt[i]
    cat = rag.catalogue_for(dorder, i, kwmap, postings)   # production catalogue (RECALL_N + kw tail)
    r_cat = rec(cat, rel)
    missed = [u for u in rel if u not in set(cat)]
    per_idea.append({"idx": i, "stratum": strat[i], "asset": assets[i], "n_relevant": len(rel),
                     "recall_catalogue": r_cat,
                     "missed": [{"url": u, "title": tmap.get(u, ""),
                                 "pool_sources": pool_src.get(i, {}).get(u, [])} for u in missed]})
    s = by_strat[strat[i]]
    if r_cat is not None:
        s["cat"].append(r_cat)
    for k in SCORE_K:
        rk = rec(dorder[:k], rel)
        if rk is not None:
            s[f"r{k}"].append(rk)


def mean(x):
    return round(sum(x) / len(x), 3) if x else None


report = {"n": len(idxs), "suffix": SUF,
          "overall": {"recall_catalogue": mean([p["recall_catalogue"] for p in per_idea if p["recall_catalogue"] is not None]),
                      **{f"dense@{k}": mean(sum([by_strat[s][f"r{k}"] for s in by_strat], [])) for k in SCORE_K}},
          "by_stratum": {s: {"n": len(v["cat"]), "recall_catalogue": mean(v["cat"]),
                             **{f"dense@{k}": mean(v[f"r{k}"]) for k in SCORE_K}} for s, v in by_strat.items()},
          "per_idea": per_idea}
json.dump(report, open(os.path.join(HERE, f"report{SUF}.json"), "w"), indent=1)

L = ["# RAG recall accuracy report" + (f" ({SUF})" if SUF else ""), "",
     f"Test set: {report['n']} ideas · Claude-judged pooled ground truth "
     "(pool = dense ∪ Claude-expansion ∪ keyword).", "",
     f"**Overall catalogue recall: {report['overall']['recall_catalogue']}**", "",
     "## By stratum", "",
     "| stratum | n | catalogue recall | dense@50 | dense@75 | dense@100 |",
     "|---|---|---|---|---|---|"]
for s, v in report["by_stratum"].items():
    L.append(f"| {s} | {v['n']} | {v['recall_catalogue']} | {v['dense@50']} | {v['dense@75']} | {v['dense@100']} |")
L += ["", "## Biggest misses (lowest recall first)", ""]
for p in sorted(per_idea, key=lambda x: (x["recall_catalogue"] if x["recall_catalogue"] is not None else 1)):
    if not p["missed"]:
        continue
    L.append(f"- **[{p['stratum']}] {p['asset'][:70]}** — recall {p['recall_catalogue']}, "
             f"missed {len(p['missed'])} of {p['n_relevant']}:")
    for m in p["missed"][:8]:
        L.append(f"    - {m['title'][:58]} ({m['url'].replace('https://testlify.com', '')}) "
                 f"— pool via {m['pool_sources']}")
L += ["", "> Limitation: ground truth is only as complete as the pool; a page no source",
      "> surfaced is invisible. See pool.jsonl for pool sizes/composition."]
open(os.path.join(HERE, f"report{SUF}.md"), "w").write("\n".join(L))
print("overall catalogue recall:", report["overall"]["recall_catalogue"])
print("by stratum:", {s: v["recall_catalogue"] for s, v in report["by_stratum"].items()})
