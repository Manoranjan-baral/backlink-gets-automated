#!/usr/bin/env python3
"""Claude judges each pooled candidate relevant/not to the idea. Cached by (idx,url)
in judge_cache.jsonl (shared across smoke/full runs, so smoke work is reused).
SUFFIX env selects testset/pool/judgments file set (e.g. "_smoke").
"""
import csv, json, os, re, subprocess, sys, time
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


def judge_batch(asset, batch, retries=5):   # -> {url: "core"|"peripheral"|"no"}
    """Returns tier dict on success. RAISES on persistent failure so callers never
    cache a failed call as 'no' (that silently poisons the ground truth). Retries
    with backoff to ride out rate limits."""
    listing = "\n".join(f"{i+1}. {t} — {cmap.get(u, '')[:300]}" for i, (u, t) in enumerate(batch))
    prompt = ("For a content idea, classify each EXISTING page we own by how much it overlaps:\n"
              "  CORE = same topic AND same search intent — a page we'd genuinely consider we "
              "already own on this idea (would compete/cannibalize).\n"
              "  PERIPHERAL = related/adjacent, useful context, but not the same intent.\n"
              "  (omit = not relevant)\n"
              'Reply ONLY JSON: {"core":[nums],"peripheral":[nums]}.\n\n'
              f"IDEA: {asset}\n\nPAGES:\n{listing}")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    for attempt in range(retries):
        try:
            p = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True,
                               env=env, timeout=240)
            out = p.stdout or ""
            if p.returncode == 0 and out.strip():
                m = re.search(r"\{.*\}", out, re.S)
                if m:
                    d = json.loads(m.group(0))   # valid JSON (incl. empty arrays) == a real answer
                    core = {n for n in d.get("core", []) if isinstance(n, int)}
                    peri = {n for n in d.get("peripheral", []) if isinstance(n, int)}
                    return {u: ("core" if k in core else "peripheral" if k in peri else "no")
                            for k, (u, t) in enumerate(batch, 1)}
            reason = f"rc={p.returncode} stdout={out[:80]!r} stderr={(p.stderr or '')[:80]!r}"
        except Exception as e:
            reason = f"exc={e}"
        wait = min(60, 5 * (2 ** attempt))
        print(f"      judge retry {attempt+1}/{retries} in {wait}s ({reason})", file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError("judge_batch failed after retries (NOT cached)")


pool = [json.loads(l) for l in open(os.path.join(HERE, f"pool{SUF}.jsonl"))]
if os.environ.get("SMOKE"):
    pool = pool[:1]
res_f = open(os.path.join(HERE, f"judgments{SUF}.jsonl"), "w")
incomplete = []
for row in pool:
    idx = row["idx"]; asset = assets[idx]
    todo = [(c["url"], c["title"]) for c in row["candidates"] if (idx, c["url"]) not in cache]
    failed = False
    for i in range(0, len(todo), JUDGE_BATCH):
        batch = todo[i:i + JUDGE_BATCH]
        try:
            tiers = judge_batch(asset, batch)
        except RuntimeError as e:
            print(f"  idx {idx}: batch FAILED — NOT cached, idea will re-run: {e}", file=sys.stderr)
            failed = True; break
        for u, t in batch:
            tier = tiers.get(u, "no"); cache[(idx, u)] = tier
            cache_f.write(json.dumps({"pair": [idx, u], "tier": tier}) + "\n"); cache_f.flush()
    if failed:
        incomplete.append(idx); continue   # skip writing an incomplete judgments line
    core = [c["url"] for c in row["candidates"] if cache.get((idx, c["url"])) == "core"]
    relevant = [c["url"] for c in row["candidates"] if cache.get((idx, c["url"])) in ("core", "peripheral")]
    res_f.write(json.dumps({"idx": idx, "relevant": sorted(set(relevant)), "core": sorted(set(core))}) + "\n")
    res_f.flush()
    print(f"  idx {idx}: {len(set(core))} core / {len(set(relevant))} relevant / "
          f"{len(row['candidates'])} judged ({len(todo)} new)", file=sys.stderr)
res_f.close()
if incomplete:
    print(f"INCOMPLETE (rerun to finish): {len(incomplete)} ideas: {incomplete}", file=sys.stderr)
print(f"wrote judgments{SUF}.jsonl", file=sys.stderr)
