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
cache = {}   # (idx,url) -> tier in {"core","peripheral","no"}
if os.path.exists(cache_p):
    for l in open(cache_p):
        d = json.loads(l)
        # backward-compat: old entries stored {"rel": bool}; map to tier
        tier = d.get("tier") or ("core" if d.get("rel") else "no")
        cache[tuple(d["pair"])] = tier
cache_f = open(cache_p, "a")


def judge_batch(asset, batch):   # batch: list[(url,title)] -> {url: "core"|"peripheral"|"no"}
    listing = "\n".join(f"{i+1}. {t} — {cmap.get(u, '')[:300]}" for i, (u, t) in enumerate(batch))
    prompt = ("For a content idea, classify each EXISTING page we own by how much it overlaps:\n"
              "  CORE = same topic AND same search intent — a page we'd genuinely consider we "
              "already own on this idea (would compete/cannibalize).\n"
              "  PERIPHERAL = related/adjacent, useful context, but not the same intent.\n"
              "  (omit = not relevant)\n"
              'Reply ONLY JSON: {"core":[nums],"peripheral":[nums]}.\n\n'
              f"IDEA: {asset}\n\nPAGES:\n{listing}")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    out = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True,
                         env=env, timeout=180).stdout
    m = re.search(r"\{.*\}", out, re.S)
    core, peri = set(), set()
    try:
        d = json.loads(m.group(0)) if m else {}
        core = {n for n in d.get("core", []) if isinstance(n, int)}
        peri = {n for n in d.get("peripheral", []) if isinstance(n, int)}
    except Exception:
        pass
    res = {}
    for k, (u, t) in enumerate(batch, 1):
        res[u] = "core" if k in core else ("peripheral" if k in peri else "no")
    return res


pool = [json.loads(l) for l in open(os.path.join(HERE, f"pool{SUF}.jsonl"))]
if os.environ.get("SMOKE"):
    pool = pool[:1]
res_f = open(os.path.join(HERE, f"judgments{SUF}.jsonl"), "w")
for row in pool:
    idx = row["idx"]; asset = assets[idx]
    todo = [(c["url"], c["title"]) for c in row["candidates"] if (idx, c["url"]) not in cache]
    for i in range(0, len(todo), JUDGE_BATCH):
        batch = todo[i:i + JUDGE_BATCH]
        tiers = judge_batch(asset, batch)
        for u, t in batch:
            tier = tiers.get(u, "no"); cache[(idx, u)] = tier
            cache_f.write(json.dumps({"pair": [idx, u], "tier": tier}) + "\n"); cache_f.flush()
    core = [c["url"] for c in row["candidates"] if cache.get((idx, c["url"])) == "core"]
    relevant = [c["url"] for c in row["candidates"] if cache.get((idx, c["url"])) in ("core", "peripheral")]
    res_f.write(json.dumps({"idx": idx, "relevant": sorted(set(relevant)), "core": sorted(set(core))}) + "\n")
    res_f.flush()
    print(f"  idx {idx}: {len(set(core))} core / {len(set(relevant))} relevant / "
          f"{len(row['candidates'])} judged ({len(todo)} new)", file=sys.stderr)
res_f.close(); print(f"wrote judgments{SUF}.jsonl", file=sys.stderr)
