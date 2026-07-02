#!/usr/bin/env python3
"""Build a multi-source candidate pool per idea:
   dense-wide  ∪  Claude-query-expansion→dense  ∪  keyword (ungated).

The pool deliberately includes sources the PRODUCTION rag does not use (Claude
query-expansion), so grading the production catalogue against it is not circular.
SMOKE=1 limits to the first 2 ideas for a cheap dry run.
"""
import csv, json, os, re, subprocess, sys
import numpy as np
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK); import rag
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
IDX = os.path.join(WORK, "content-index")
CONTENT = os.path.join(REPO, "projects/testlify/content-database.csv")
POOL_DENSE_N = 100; POOL_EXPAND_Q = 5; POOL_EXPAND_N = 30; MAX_POOL = 200
SUF = os.environ.get("SUFFIX", "")   # e.g. "_smoke" -> testset_smoke.json / pool_smoke.jsonl


def expand_queries(asset, n=POOL_EXPAND_Q):
    """Claude splits the asset into up to n sub-angle search queries (JSON array)."""
    prompt = ("Given this content asset idea, output ONLY a JSON array of up to %d short "
              "search queries capturing its distinct sub-angles (for retrieving existing "
              "articles on each angle). No prose.\n\nASSET: %s" % (n, asset))
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        out = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True,
                             env=env, timeout=120).stdout
        m = re.search(r"\[.*\]", out, re.S)
        qs = json.loads(m.group(0)) if m else []
        return [q for q in qs if isinstance(q, str) and q.strip()][:n]
    except Exception as e:
        print("   expand fallback:", str(e)[:60], file=sys.stderr); return []


Vt, Mt = rag.load_vecs(os.path.join(IDX, "title")); Vb, Mb = rag.load_vecs(os.path.join(IDX, "body"))
urls = [m["url"] for m in Mt]; uidx = {u: i for i, u in enumerate(urls)}
body_uidx = np.array([uidx[m["url"]] for m in Mb])
tmap = {}
for row in csv.DictReader(open(CONTENT, encoding="utf-8")):
    tmap[(row.get("URL") or "").strip()] = row.get("Title") or ""
postings = rag.build_keyword_postings(urls, tmap)
kwmap = rag.load_topic_keywords(os.path.join(WORK, "topic_keywords.json"))
print(f"pool: {len(urls)} pages | {len(postings)} tokens | {len(kwmap)} keyworded ideas", file=sys.stderr)


def dense_order(qtext):
    Q = rag.embed([qtext], "query"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9); q = Q[0]
    bb = np.full(len(urls), -1.0, np.float32); np.maximum.at(bb, body_uidx, Vb @ q)
    blended = rag.ALPHA * (Vt @ q) + (1 - rag.ALPHA) * bb
    return [urls[k] for k in np.argsort(blended)[::-1] if not rag.foreign(urls[k])]


def clean(a):
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", a or "")).strip() or "untitled"


def ungated_keyword_hits(idx):
    hits = set()
    for p in kwmap.get(idx, []):
        toks = rag._kw_toks(p)
        if not toks:
            continue
        sets = [postings.get(x, set()) for x in toks]
        if all(sets):
            hits |= set.intersection(*sets)
    return hits


testset = json.load(open(os.path.join(HERE, f"testset{SUF}.json")))
if os.environ.get("SMOKE"):
    testset = testset[:2]
out = open(os.path.join(HERE, f"pool{SUF}.jsonl"), "w")
for t in testset:
    idx, asset = t["idx"], t["asset"]
    src = {}   # url -> set(sources)
    for u in dense_order(clean(asset))[:POOL_DENSE_N]:
        src.setdefault(u, set()).add("dense")
    for sq in expand_queries(asset):
        for u in dense_order(sq)[:POOL_EXPAND_N]:
            src.setdefault(u, set()).add("expand")
    for u in ungated_keyword_hits(idx):
        src.setdefault(u, set()).add("keyword")
    cands = [{"url": u, "title": tmap.get(u, ""), "sources": sorted(s)} for u, s in src.items()]
    if len(cands) > MAX_POOL:   # keep expand+keyword; fill remainder by dense presence
        pri = [c for c in cands if set(c["sources"]) & {"expand", "keyword"}]
        pri_urls = {c["url"] for c in pri}
        fill = [c for c in cands if c["url"] not in pri_urls][: MAX_POOL - len(pri)]
        cands = (pri + fill)[:MAX_POOL]
    out.write(json.dumps({"idx": idx, "candidates": cands}) + "\n"); out.flush()
    print(f"  idx {idx}: pool {len(cands)}", file=sys.stderr)
out.close(); print(f"wrote pool{SUF}.jsonl", file=sys.stderr)
