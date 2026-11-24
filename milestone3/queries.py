import os
import sys
import json
import urllib.parse
import urllib.request
from sentence_transformers import SentenceTransformer
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

SETUPS = {
    "semantics": {"core": "games_semantics", "params": {}},
}

SETUP = sys.argv[1] if len(sys.argv) > 1 else None
if SETUP not in SETUPS:
    sys.exit(f"usage: queries.py {{{', '.join(SETUPS)}}}")
OUT_DIR = f"milestone3/results/{SETUP}"

QUERIES = [
    # ========== SEARCH SCENARIO 1 ==========
    {
        "id": "S1-a",
        "scenario": "technical issues",
        "q": "won't start"
    },
    {
        "id": "S1-b",
        "scenario": "technical issues",
        "q": "crashes boot"
    },
    {
        "id": "S1-c",
        "scenario": "technical issues",
        "q": "stuck loading"
    },

    # ========== SEARCH SCENARIO 2 ==========
    {
    "id": "S2-a",
        "scenario": "aspect-based opinions",
        "q": "great soundtrack"
    },
    {
    "id": "S2-b",
        "scenario": "aspect-based opinions",
        "q": "amazing music"
    },
    {
    "id": "S2-c",
        "scenario": "aspect-based opinions",
        "q": "best sound"
    },

    # ========== SEARCH SCENARIO 3 ==========
    {
        "id": "S3-a",
        "scenario": "game comparison",
        "q": "original better"
    },
    {
        "id": "S3-b",
        "scenario": "game comparison",
        "q": "sequel worse"
    },
    {
        "id": "S3-c",
        "scenario": "game comparison",
        "q": "downgrade original"
    },
]

def embed(text):
    """Unit-normalised query vector, in the [f1,f2,...] form Solr expects."""
    vec = MODEL.encode(text, normalize_embeddings=True)
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"

def run(query, setup):
    cfg = SETUPS[setup]
    vector = embed(query["q"])
    params = {
        "q": f"{{!knn f=review_vector topK={30}}}{vector}",
        "fq": "doc_type:review",
        "rows": 30,
        "fl": "id,name,App_ID,source,review,score",
        "wt": "json",
        **cfg["params"],
    }
    url = f"http://localhost:8983/solr/{cfg['core']}/select?{urllib.parse.urlencode(params, doseq=True)}"
    try:
        with urllib.request.urlopen(url) as r:
            return json.load(r)["response"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Solr said: {e.read().decode()}")

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    dump = open(os.path.join(OUT_DIR, "dump.txt"), "w", encoding="utf-8")
    qrels = open(os.path.join(OUT_DIR, "qrels.txt"), "w", encoding="utf-8")
    results = open(os.path.join(OUT_DIR, "results.txt"), "w", encoding="utf-8")
    dump.write(f"# model={"all-MiniLM-L6-v2"} score=cosine_similarity top_k={30}\n")

    for query in QUERIES:
        resp = run(query, SETUP)
        header = f"\n== {query['id']} [{query['scenario']}] q={query['q']!r} found={resp['numFound']}"
        dump.write(header + "\n")
        print(header)
        for rank, doc in enumerate(resp["docs"], start=1):
            label = doc.get("review") or doc.get("name", "")
            results.write(f"{query['id']} Q0 {doc['id']} {rank} {doc.get("score", 0):.6f} {SETUP}\n")
            qrels.write(f"{query['id']} 0 {doc['id']} 0\n")
            dump.write(f"{rank}\t{doc.get("score", 0):.6f}\t{doc['id']}\t{doc.get('source', '')}\t{doc.get('name', '')}\t{str(label).replace("\n", " ")}\n")
            print(f"{rank:>3}  {doc.get("score", 0):.4f}  {doc['id']:<16} {str(label).replace("\n", " ")[:100]}")

    dump.close()
    qrels.close()
    results.close()
