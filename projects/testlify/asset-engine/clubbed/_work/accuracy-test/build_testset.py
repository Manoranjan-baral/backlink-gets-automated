#!/usr/bin/env python3
"""Assemble 80-idea test set: fixed 50 (bench) + stratified fresh 30 (seeded).

Strata: fixed50 (continuity), comparison ("X vs Y"), entity (product/proper-noun
heavy), random. Shortfalls in comparison/entity are topped up from random so the
total is always 80. Reproducible via SEED.
"""
import csv, json, os, random, re
from collections import Counter
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
CLUBBED = os.path.join(REPO, "projects/testlify/asset-engine/clubbed/clubbed-ideas.csv")
BENCH = os.path.join(WORK, "bench", "benchmark_assets.json")
SEED = 1337
FRESH = {"comparison": 10, "entity": 10, "random": 10}
TARGET = 50 + sum(FRESH.values())

rows = list(csv.DictReader(open(CLUBBED, encoding="utf-8")))
fixed = json.load(open(BENCH))
fixed_idx = {a["idx"] for a in fixed}
testset = [{"idx": a["idx"], "asset": a["asset"], "stratum": "fixed50"} for a in fixed]

pool = [(i, (r.get("Asset") or "").strip()) for i, r in enumerate(rows)
        if i not in fixed_idx and (r.get("Asset") or "").strip()]

def is_comp(a):
    return bool(re.search(r"\bvs\.?\b", a, re.I))

def is_entity(a):
    # entity-heavy: short-ish head with >=2 capitalized product/proper-noun tokens, not a comparison
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
        if len(out) >= n:
            break
        if i in picked:
            continue
        picked.add(i); out.append({"idx": i, "asset": a, "stratum": stratum})
    return out

testset += take(comp, FRESH["comparison"], "comparison")
testset += take(ent, FRESH["entity"], "entity")
rest = [p for p in pool if p[0] not in picked]; rnd.shuffle(rest)
# random stratum + top up any shortfall from comparison/entity so total == TARGET
need_random = FRESH["random"] + (TARGET - len(testset) - FRESH["random"])
testset += take(rest, need_random, "random")

json.dump(testset, open(os.path.join(HERE, "testset.json"), "w"), indent=0)
print("testset:", len(testset), dict(Counter(t["stratum"] for t in testset)))
