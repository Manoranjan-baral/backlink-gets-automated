#!/usr/bin/env python3
"""Claude judges each pooled candidate relevant/not to the idea. Cached by (idx,url)
in judge_cache.jsonl (shared across smoke/full runs, so smoke work is reused).
SUFFIX env selects testset/pool/judgments file set (e.g. "_smoke").
"""
import csv, json, os, re, subprocess, sys
csv.field_size_limit(1 << 24)
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(WORK, "..", "..", "..", "..", ".."))
CONTENT = os.path.join(REPO, "projects/testlify/content-database.csv")
JUDGE_BATCH = 15
SUF = os.environ.get("SUFFIX", "")

cmap = {}
for row in csv.DictReader(open(CONTENT, encoding="utf-8")):
    cmap[(row.get("URL") or "").strip()] = (row.get("Full content") or "")[:600]
assets = {t["idx"]: t["asset"] for t in json.load(open(os.path.join(HERE, f"testset{SUF}.json")))}

cache_p = os.path.join(HERE, "judge_cache.jsonl")   # shared cache (not suffixed)
cache = {}
if os.path.exists(cache_p):
    for l in open(cache_p):
        d = json.loads(l); cache[tuple(d["pair"])] = d["rel"]
cache_f = open(cache_p, "a")


def judge_batch(asset, batch):   # batch: list[(url,title)]
    listing = "\n".join(f"{i+1}. {t} — {cmap.get(u, '')[:300]}" for i, (u, t) in enumerate(batch))
    prompt = ("You decide which EXISTING pages we already own are relevant to a content idea "
              "(same topic; a page that would compete for the same search intent as the idea). "
              "Reply ONLY a JSON array of the numbers that are relevant (e.g. [1,4,5]).\n\n"
              f"IDEA: {asset}\n\nPAGES:\n{listing}")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    out = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True,
                         env=env, timeout=180).stdout
    m = re.search(r"\[.*\]", out, re.S)
    try:
        nums = set(json.loads(m.group(0))) if m else set()
    except Exception:
        nums = set()
    return [batch[i - 1][0] for i in nums if isinstance(i, int) and 1 <= i <= len(batch)]


pool = [json.loads(l) for l in open(os.path.join(HERE, f"pool{SUF}.jsonl"))]
if os.environ.get("SMOKE"):
    pool = pool[:1]
res_f = open(os.path.join(HERE, f"judgments{SUF}.jsonl"), "w")
for row in pool:
    idx = row["idx"]; asset = assets[idx]; relevant = []
    todo = [(c["url"], c["title"]) for c in row["candidates"] if (idx, c["url"]) not in cache]
    for c in row["candidates"]:
        if (idx, c["url"]) in cache and cache[(idx, c["url"])]:
            relevant.append(c["url"])
    for i in range(0, len(todo), JUDGE_BATCH):
        batch = todo[i:i + JUDGE_BATCH]
        rel = set(judge_batch(asset, batch))
        for u, t in batch:
            r = u in rel; cache[(idx, u)] = r
            cache_f.write(json.dumps({"pair": [idx, u], "rel": r}) + "\n"); cache_f.flush()
            if r:
                relevant.append(u)
    res_f.write(json.dumps({"idx": idx, "relevant": sorted(set(relevant))}) + "\n"); res_f.flush()
    print(f"  idx {idx}: {len(set(relevant))} relevant / {len(row['candidates'])} judged "
          f"({len(todo)} new)", file=sys.stderr)
res_f.close(); print(f"wrote judgments{SUF}.jsonl", file=sys.stderr)
