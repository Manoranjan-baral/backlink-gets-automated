#!/usr/bin/env python3
"""
RAG for the asset-engine reuse check (Stages 1 & 2). Improvements over v1:
  - Option B title weighting: separate TITLE vector + BODY (chunked) vectors per page,
    blended at query time:  score = ALPHA*title_sim + (1-ALPHA)*best_body_chunk_sim
  - Clean query: the Asset TITLE only (the verbose "Distinct angle" is dropped).
  - Reranker: dense gives top-N, then Voyage rerank-2.5 picks the final TOPK.

  index    : python3 rag.py index    <content-database.csv> <index_dir>
  retrieve : python3 rag.py retrieve <clubbed-ideas.csv> <index_dir> <content-database.csv>

Key: VOYAGE_API_KEY env var, else first `pa-...` token in ~/.testlify-access.md (never printed).
"""
import csv, json, os, re, subprocess, sys, time, urllib.request, urllib.error
import numpy as np
from collections import defaultdict
csv.field_size_limit(1 << 24)

EMB_MODEL = "voyage-4-large"     # best general embedding model on the free tier
RERANK_MODEL = "rerank-2.5"      # best reranker on the free tier
ALPHA = 0.5            # title weight in blended score (1-ALPHA = body); tunable
N_RETRIEVE = 40        # dense candidates before reranking (>= TOPK)
TOPK = 15              # RAG candidate LINKS kept per idea — JOB A (precision, for the LLM judge)
RECALL_N = 75          # JOB B (recall, human catalogue): dense top-N shown, NO rerank truncation.
                       # 2026-07 recall study (DE-BIASED labels, ~25 relevant/asset): relevant
                       # pages sit at dense ranks 15-75; the rerank top-15 cut loses them.
                       # dense recall@K: @15≈0.34 @25≈0.47 @40≈0.59 @50≈0.66 @75≈0.78 @100≈0.82.
                       # Set to 75 (hybrid recall ≈0.81) — the free +0.12 over K=50; natural ceiling
                       # ~0.85 beyond which extra pages are off-angle noise. Lever is K (tunable).
                       # Decomposition / query-rewrite tested → no gain over widening K.
# ── HYBRID keyword top-up on Job B (2026-07 follow-up) ────────────────────────
# Dense ranking BURIES exact-entity pages that literal matching catches: e.g. for
# "AI Resume Screening vs Skills Testing", the page /ai-resume-screener/ ("AI resume
# screener") sits at dense rank 63 (just past RECALL_N) because the query's dominant
# angle is "vs skills testing / accuracy". Fix: after the dense top-50, UNION in pages
# matched by the idea's curated topic keywords (topic_keywords.json), but ONLY from
# DF-gated (specific, not generic) phrases so we add an entity tail, not a flood.
MAXDF_KW = 25          # a keyword phrase matching > this many corpus pages is too generic → dropped
                       # (e.g. "skills testing" → 111 pages; "resume screening" → 5, kept)
KW_ADD   = 12          # cap on net-new keyword pages appended to the dense catalogue per idea
# ── QUERY EXPANSION on Job B (2026-07 accuracy-test lever) ────────────────────
# The pooled, Claude-judged accuracy test found 71% of Job-B recall MISSES are pages
# only reachable by expanding the asset into its sub-angle queries — the single
# largest recall lever (smoke: recall_reachable 0.86 while recall_full lagged on
# expansion-only pages). Claude (Haiku) splits each asset into up to EXPAND_Q
# sub-angle search queries; each query's dense top-EXP_DENSE_N is unioned into the
# catalogue as a dense-ranked, capped tail — exactly like the keyword tail. Results
# are cached to disk (query_expansion_cache.json) so re-runs cost ZERO Claude quota
# and production runs are repeatable. Set EXPAND_Q=0 (or make the `claude` CLI absent)
# to disable → catalogue is byte-identical to the pre-expansion behaviour.
EXPAND_Q     = int(os.environ.get("EXPAND_Q", "5"))   # sub-angle queries per asset (0 = off)
EXP_DENSE_N  = 30      # dense depth scanned per expansion query for candidate pages
EXP_ADD      = 20      # cap on net-new expansion pages appended to the catalogue per idea (lever)
EXPAND_MODEL = os.environ.get("EXPAND_MODEL", "claude-haiku-4-5")  # cheap; expansion is simple splitting
EXPAND_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_expansion_cache.json")
CHUNK_CHARS = 4800
OVERLAP = 600
MAX_ITEMS = 64
MAX_CHARS = 90000
RERANK_DOC_CHARS = 4000   # truncate each candidate for the rerank call

def get_key():
    k = os.environ.get("VOYAGE_API_KEY")
    if k:
        return k
    p = os.path.expanduser("~/.testlify-access.md")
    if os.path.exists(p):
        m = re.search(r'pa-[A-Za-z0-9_\-]{20,}', open(p).read())
        if m:
            return m.group(0)
    sys.exit("no VOYAGE_API_KEY (env or ~/.testlify-access.md)")
KEY = get_key()

def _post(url, body):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            w = 2 ** attempt
            if e.code == 429:
                w = max(w, 15)
            print(f"   HTTP {e.code} retry {w}s {e.read()[:120]!r}", file=sys.stderr); time.sleep(w)
        except Exception as ex:
            print(f"   err {ex} retry", file=sys.stderr); time.sleep(2 ** attempt)
    raise RuntimeError("voyage call failed after retries")

def embed(texts, input_type):
    texts = [t if (t and t.strip()) else "untitled" for t in texts]   # Voyage 400s on empty strings
    out, i = [], 0
    while i < len(texts):
        batch, chars = [], 0
        while i < len(texts) and len(batch) < MAX_ITEMS and chars + len(texts[i]) <= MAX_CHARS:
            batch.append(texts[i]); chars += len(texts[i]); i += 1
        if not batch:
            batch = [texts[i][:MAX_CHARS]]; i += 1
        d = _post("https://api.voyageai.com/v1/embeddings",
                  {"input": batch, "model": EMB_MODEL, "input_type": input_type})
        out.extend(e["embedding"] for e in sorted(d["data"], key=lambda x: x["index"]))
        time.sleep(0.2)
    return np.asarray(out, dtype=np.float32)

def rerank(query, docs, top_k):
    d = _post("https://api.voyageai.com/v1/rerank",
              {"query": query, "documents": docs, "model": RERANK_MODEL,
               "top_k": top_k, "return_documents": False})
    return [(r["index"], r["relevance_score"]) for r in d["data"]]

LOCALES = {"ar","pl","it","pt-br","no","ja","da","es","de","el","sv","nl","fr",
           "pt","zh","ko","ru","tr","hi","id","th","vi"}
def foreign(u):
    # translation duplicates: URL's first path segment is an ISO locale code
    m = re.match(r"https?://(?:www\.)?[^/]+/([^/]+)/", u or "")
    return bool(m and m.group(1).lower() in LOCALES)

# ── keyword top-up helpers (Job B hybrid) ────────────────────────────────────
_KW_STOP = {"the","a","an","of","for","and","or","to","in","on","with","how",
            "what","is","are","your","you","vs","that","this"}
def _stem(w):
    for suf in ("ing", "ers", "er", "ed", "es", "s"):   # crude: screening/screener → screen
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w
def _kw_toks(s):
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", (s or "").lower())
            if w not in _KW_STOP and len(w) > 1}

def build_keyword_postings(urls, tmap):
    """Inverted index stemmed-token -> set(url) over title+URL-slug (non-foreign pages)."""
    postings = defaultdict(set)
    for u in urls:
        if foreign(u):
            continue
        slug = re.sub(r"https?://[^/]+", "", u).replace("/", " ").replace("-", " ")
        for t in _kw_toks(tmap.get(u, "")) | _kw_toks(slug):
            postings[t].add(u)
    return postings

def keyword_hits(phrases, postings):
    """Union of pages matching any DF-gated phrase (all of its stemmed tokens present)."""
    hits = set()
    for p in phrases or []:
        toks = _kw_toks(p)
        if not toks:
            continue
        sets = [postings.get(t, set()) for t in toks]
        if not all(sets):                      # a token absent from the corpus → no match
            continue
        m = set.intersection(*sets)
        if 1 <= len(m) <= MAXDF_KW:            # drop generic phrases (too many matches)
            hits |= m
    return hits

def load_topic_keywords(path):
    if not path or not os.path.exists(path):
        return {}
    return {k["i"]: k.get("keywords", []) for k in json.load(open(path, encoding="utf-8"))}

# ── query-expansion helpers (Job B lever) ────────────────────────────────────
_expand_cache = None
def _load_expand_cache():
    global _expand_cache
    if _expand_cache is None:
        try:
            _expand_cache = json.load(open(EXPAND_CACHE, encoding="utf-8")) if os.path.exists(EXPAND_CACHE) else {}
        except Exception:
            _expand_cache = {}
    return _expand_cache

def expand_queries(asset, n=EXPAND_Q):
    """Claude (Haiku) → up to n sub-angle search queries for `asset`, cached to disk.
    Returns [] (→ no expansion, identical to pre-expansion catalogue) when disabled or
    the CLI call fails, so the retrieval path degrades gracefully with zero cost."""
    key = (asset or "").strip()
    if not key or n <= 0:
        return []
    cache = _load_expand_cache()
    if key in cache:
        return cache[key][:n]
    prompt = ("Given this content asset idea, output ONLY a JSON array of up to %d short "
              "search queries capturing its distinct sub-angles (for retrieving existing "
              "articles on each angle). No prose.\n\nASSET: %s" % (n, key))
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        out = subprocess.run(["claude", "-p", "--model", EXPAND_MODEL, prompt],
                             capture_output=True, text=True, env=env, timeout=120).stdout
        m = re.search(r"\[.*\]", out, re.S)
        qs = json.loads(m.group(0)) if m else []
        qs = [q for q in qs if isinstance(q, str) and q.strip()][:n]
    except Exception as e:
        print("   expand fallback:", str(e)[:60], file=sys.stderr)
        return []
    cache[key] = qs
    try:
        json.dump(cache, open(EXPAND_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass
    return qs

def _dense_order(qvec, Vt, Vb, urls, body_uidx):
    """Blended title+body dense ranking of non-foreign pages for a single query vector."""
    bb = np.full(len(urls), -1.0, dtype=np.float32)
    np.maximum.at(bb, body_uidx, Vb @ qvec)
    blended = ALPHA * (Vt @ qvec) + (1 - ALPHA) * bb
    return [urls[k] for k in np.argsort(blended)[::-1] if not foreign(urls[k])]

def catalogue_for(dense_order, idx, kwmap, postings, recall_n=RECALL_N, kw_add=KW_ADD,
                  exp_orders=None, exp_dense_n=EXP_DENSE_N, exp_add=EXP_ADD):
    """Job B catalogue = dense top-recall_n  ∪  DF-gated keyword tail  ∪  query-expansion
    tail. Each tail is dense-ranked and capped. exp_orders is a list of dense orders, one
    per Claude sub-angle query; when None/empty the result is identical to dense∪keyword."""
    recall = dense_order[:recall_n]
    seen = set(recall)
    rank = {u: i for i, u in enumerate(dense_order)}
    khits = keyword_hits(kwmap.get(idx, []), postings)
    ktail = [u for u in sorted(khits, key=lambda u: rank.get(u, 1 << 30)) if u not in seen][:kw_add]
    seen.update(ktail)
    etail = []
    if exp_orders:
        best = {}   # page -> best (smallest) rank across any expansion query's top-exp_dense_n
        for order in exp_orders:
            for pos, u in enumerate(order[:exp_dense_n]):
                if u not in seen and (u not in best or pos < best[u]):
                    best[u] = pos
        etail = sorted(best, key=lambda u: best[u])[:exp_add]
    return recall + ktail + etail

def chunks(text):
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= CHUNK_CHARS:
        return [text]
    out, s = [], 0
    while s < len(text):
        out.append(text[s:s + CHUNK_CHARS]); s += CHUNK_CHARS - OVERLAP
    return out

# ---------------- INDEX ----------------
def load_pages(content_csv):
    pages = []
    with open(content_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = (row.get("URL") or "").strip()
            title = (row.get("Title") or "").strip()
            fc = (row.get("Full content") or "").strip()
            if url and fc:                       # only pages with real content can be reuse candidates
                pages.append((url, title, fc))
    return pages

def do_index(content_csv, idx_dir):
    pages = load_pages(content_csv)
    print(f"index: {len(pages)} pages with content", file=sys.stderr)

    # --- TITLE index: one vector per page (cheap, one shot) ---
    tdir = os.path.join(idx_dir, "title")
    if os.path.exists(os.path.join(tdir, "vectors.npy")):
        print("title index already present, skipping", file=sys.stderr)
    else:
        os.makedirs(tdir, exist_ok=True)
        tvecs = embed([t if t else u for u, t, fc in pages], "document")
        np.save(os.path.join(tdir, "vectors.npy"), tvecs)
        with open(os.path.join(tdir, "meta.jsonl"), "w", encoding="utf-8") as f:
            for u, t, fc in pages:
                f.write(json.dumps({"url": u, "title": t}) + "\n")
        print("title index done", file=sys.stderr)

    # --- BODY index: chunked, resumable ---
    bdir = os.path.join(idx_dir, "body")
    os.makedirs(os.path.join(bdir, "parts"), exist_ok=True)
    state_p = os.path.join(bdir, "state.json")
    meta_p = os.path.join(bdir, "meta.jsonl")
    state = json.load(open(state_p)) if os.path.exists(state_p) else {"done": [], "part": 0}
    done = set(state["done"])
    todo = [(u, t, fc) for u, t, fc in pages if u not in done]
    print(f"body index: {len(todo)} pages to embed ({len(done)} done)", file=sys.stderr)
    meta_f = open(meta_p, "a", encoding="utf-8")
    buf, buf_chunks = [], 0

    def flush():
        nonlocal buf, buf_chunks
        if not buf:
            return
        texts, metas = [], []
        for u, t, fc in buf:
            for ci, ch in enumerate(chunks(fc)):
                texts.append(ch); metas.append({"url": u, "title": t, "chunk": ci})
        vecs = embed(texts, "document")
        np.save(os.path.join(bdir, "parts", f"part_{state['part']:05d}.npy"), vecs)
        for m in metas:
            meta_f.write(json.dumps(m) + "\n")
        meta_f.flush()
        state["part"] += 1
        state["done"].extend(u for u, _, _ in buf)
        json.dump(state, open(state_p, "w"))
        print(f"   flushed {len(buf)} pages / {len(texts)} chunks (done {len(state['done'])})", file=sys.stderr)
        buf, buf_chunks = [], 0

    for p in todo:
        buf.append(p); buf_chunks += len(chunks(p[2]))
        if buf_chunks >= MAX_ITEMS:
            flush()
    flush()
    meta_f.close()
    print("body index done", file=sys.stderr)

# ---------------- RETRIEVE ----------------
def load_vecs(subdir):
    vp = os.path.join(subdir, "vectors.npy")
    if os.path.exists(vp):
        V = np.load(vp)
    else:
        parts = sorted(os.listdir(os.path.join(subdir, "parts")))
        V = np.concatenate([np.load(os.path.join(subdir, "parts", p)) for p in parts], axis=0)
    M = [json.loads(l) for l in open(os.path.join(subdir, "meta.jsonl"), encoding="utf-8")]
    assert len(M) == len(V), f"{subdir}: meta {len(M)} != vecs {len(V)}"
    V = V.astype(np.float32)
    V /= (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    return V, M

def do_retrieve(clubbed_csv, idx_dir, content_csv):
    Vt, Mt = load_vecs(os.path.join(idx_dir, "title"))
    Vb, Mb = load_vecs(os.path.join(idx_dir, "body"))
    urls = [m["url"] for m in Mt]                       # title order == page order
    uidx = {u: i for i, u in enumerate(urls)}
    body_uidx = np.array([uidx[m["url"]] for m in Mb])  # url-index per body chunk
    print(f"retrieve: {len(urls)} pages | {len(Vb)} body chunks", file=sys.stderr)

    cmap, tmap = {}, {}
    for row in csv.DictReader(open(content_csv, encoding="utf-8")):
        u = (row.get("URL") or "").strip()
        cmap[u] = (row.get("Full content") or ""); tmap[u] = (row.get("Title") or "")

    # hybrid keyword top-up (Job B): curated per-idea phrases + corpus inverted index
    postings = build_keyword_postings(urls, tmap)
    kwmap = load_topic_keywords(os.path.join(os.path.dirname(os.path.abspath(__file__)), "topic_keywords.json"))
    print(f"retrieve: keyword index {len(postings)} tokens | {len(kwmap)} keyworded ideas", file=sys.stderr)

    with open(clubbed_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; rows = list(reader)

    # CLEAN query = Asset title, with parenthetical feature/qualifier detail stripped
    # (e.g. "... Benchmark Report (Adoption, Completion, AI Cheating)" -> "... Benchmark Report").
    # The parenthetical is mini-angle noise that drags retrieval off-topic.
    def query_text(r):
        a = re.sub(r"\([^)]*\)", " ", (r.get("Asset") or ""))
        a = re.sub(r"\s+", " ", a).strip()
        return a or (r.get("Asset") or "").strip() or (r.get("Distinct angle") or "").strip() or "untitled"
    queries = [query_text(r) for r in rows]
    Q = embed(queries, "query"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)

    # ── QUERY EXPANSION (Job B recall lever) — build sub-angle queries per idea (cached,
    # Haiku), embed them once in bulk, and slice back per idea. Zero cost on a warm cache.
    exp_qs = [expand_queries(r.get("Asset") or "") for r in rows]
    exp_slices, off = [], 0
    for qs in exp_qs:
        exp_slices.append((off, off + len(qs))); off += len(qs)
    flat = [q for qs in exp_qs for q in qs]
    EQ = embed(flat, "query") if flat else Q[:0]
    if len(EQ):
        EQ /= (np.linalg.norm(EQ, axis=1, keepdims=True) + 1e-9)
    print(f"retrieve: query-expansion {len(flat)} sub-queries over "
          f"{sum(1 for qs in exp_qs if qs)}/{len(rows)} ideas "
          f"(model {EXPAND_MODEL}; EXPAND_Q={EXPAND_Q})", file=sys.stderr)

    for n, r in enumerate(rows):
        q = Q[n]
        tsim = Vt @ q                                   # per page
        bsim = Vb @ q                                   # per body chunk
        bestbody = np.full(len(urls), -1.0, dtype=np.float32)
        np.maximum.at(bestbody, body_uidx, bsim)        # best chunk per page
        blended = ALPHA * tsim + (1 - ALPHA) * bestbody
        dense_order = [urls[k] for k in np.argsort(blended)[::-1] if not foreign(urls[k])]

        # ── JOB A — precision (for the LLM judge): rerank dense top-N, keep TOPK ──
        cand = dense_order[:N_RETRIEVE]
        docs = [((tmap[u][:200] + "\n" + cmap[u])[:RERANK_DOC_CHARS]).replace("\x00", " ").strip() or "(no content)"
                for u in cand]
        order = rerank(queries[n] or r.get("Asset", ""), docs, min(TOPK, len(cand)))
        top = [(cand[i], sc) for i, sc in order]

        # ── JOB B — recall (human catalogue): dense top-RECALL_N ∪ DF-gated keyword tail ──
        # (2026-07 de-biased study: widening K 15→50 lifts recall ~0.34→0.66 (~0.79 @75);
        #  rerank truncation to 15 is what loses on-topic siblings. The keyword tail then
        #  recovers exact-entity pages dense buries past K — e.g. /ai-resume-screener/ @63.)
        #  Query-expansion tail adds pages only the asset's sub-angle queries reach (71% of misses).
        a, b = exp_slices[n]
        exp_orders = [_dense_order(EQ[j], Vt, Vb, urls, body_uidx) for j in range(a, b)]
        catalogue = catalogue_for(dense_order, n, kwmap, postings, exp_orders=exp_orders)

        # LINKS ONLY — store links, not content. Any step needing page text fetches on
        # demand from content-database.csv (holds Full content) or the live page.
        r["RAG candidates"] = "; ".join(f"{tmap[u]} — {u} ({sc:.2f})" for u, sc in top)
        r["Topic pages we own"] = "; ".join(f"{tmap[u]} — {u}" for u in catalogue)
        r["Reference links"] = "; ".join(dict.fromkeys([u for u, _ in top] + catalogue))
        if (n + 1) % 50 == 0:
            print(f"   retrieved {n+1}/{len(rows)}", file=sys.stderr)

    with open(clubbed_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"retrieve: wrote candidates for {len(rows)} ideas", file=sys.stderr)

def do_catalogue(clubbed_csv, idx_dir, content_csv):
    """Cheap Job-B-only refresh: recompute 'Topic pages we own' + 'Reference links'
    (dense top-50 ∪ keyword tail) WITHOUT re-running the reranker. Reuses the existing
    'RAG candidates' cell (Job A) for the reference union. No rerank calls."""
    Vt, Mt = load_vecs(os.path.join(idx_dir, "title"))
    Vb, Mb = load_vecs(os.path.join(idx_dir, "body"))
    urls = [m["url"] for m in Mt]
    uidx = {u: i for i, u in enumerate(urls)}
    body_uidx = np.array([uidx[m["url"]] for m in Mb])
    tmap = {}
    for row in csv.DictReader(open(content_csv, encoding="utf-8")):
        u = (row.get("URL") or "").strip(); tmap[u] = (row.get("Title") or "")
    postings = build_keyword_postings(urls, tmap)
    kwmap = load_topic_keywords(os.path.join(os.path.dirname(os.path.abspath(__file__)), "topic_keywords.json"))
    print(f"catalogue: {len(urls)} pages | {len(postings)} tokens | {len(kwmap)} keyworded ideas", file=sys.stderr)

    with open(clubbed_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; rows = list(reader)

    def query_text(r):
        a = re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", (r.get("Asset") or ""))).strip()
        return a or (r.get("Asset") or "").strip() or (r.get("Distinct angle") or "").strip() or "untitled"
    Q = embed([query_text(r) for r in rows], "query"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)

    # Query-expansion tail (Job B lever). On a warm query_expansion_cache.json this is free;
    # a cold cache incurs Haiku calls (or set EXPAND_Q=0 to skip and match dense∪keyword).
    exp_qs = [expand_queries(r.get("Asset") or "") for r in rows]
    exp_slices, off = [], 0
    for qs in exp_qs:
        exp_slices.append((off, off + len(qs))); off += len(qs)
    flat = [q for qs in exp_qs for q in qs]
    EQ = embed(flat, "query") if flat else Q[:0]
    if len(EQ):
        EQ /= (np.linalg.norm(EQ, axis=1, keepdims=True) + 1e-9)

    for n, r in enumerate(rows):
        q = Q[n]
        bestbody = np.full(len(urls), -1.0, dtype=np.float32)
        np.maximum.at(bestbody, body_uidx, Vb @ q)
        blended = ALPHA * (Vt @ q) + (1 - ALPHA) * bestbody
        dense_order = [urls[k] for k in np.argsort(blended)[::-1] if not foreign(urls[k])]
        a, b = exp_slices[n]
        exp_orders = [_dense_order(EQ[j], Vt, Vb, urls, body_uidx) for j in range(a, b)]
        catalogue = catalogue_for(dense_order, n, kwmap, postings, exp_orders=exp_orders)
        rag_urls = re.findall(r"(https?://\S+?)(?:\s*\([\-\d.]+\))?(?:;|$)", r.get("RAG candidates", ""))
        r["Topic pages we own"] = "; ".join(f"{tmap[u]} — {u}" for u in catalogue)
        r["Reference links"] = "; ".join(dict.fromkeys(rag_urls + catalogue))
        if (n + 1) % 50 == 0:
            print(f"   catalogue {n+1}/{len(rows)}", file=sys.stderr)

    with open(clubbed_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"catalogue: refreshed Job-B catalogue for {len(rows)} ideas", file=sys.stderr)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "index":
        do_index(sys.argv[2], sys.argv[3])
    elif cmd == "retrieve":
        do_retrieve(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "catalogue":
        do_catalogue(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit("unknown command")
