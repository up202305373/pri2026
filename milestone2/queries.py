import os
import sys
import json
import urllib.parse
import urllib.request

URL = "http://localhost:8983/solr/games/select"
SETUPS = ["basic", "improved"]
SETUP = sys.argv[1] if len(sys.argv) > 1 else None
if SETUP not in SETUPS:
    sys.exit(f"usage: queries.py {{{', '.join(SETUPS)}}}")
OUT_DIR = f"milestone2/results/{SETUP}"

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
        "q": '"great soundtrack"'
    },
    {
    "id": "S2-b",
        "scenario": "aspect-based opinions",
        "q": '"amazing music"'
    },
    {
    "id": "S2-c",
        "scenario": "aspect-based opinions",
        "q": '"best sound"'
    },

    # ========== SEARCH SCENARIO 3 ==========
    {
        "id": "S3-a",
        "scenario": "game comparison",
        "q": '"original better"'
    },
    {
        "id": "S3-b",
        "scenario": "game comparison",
        "q": '"sequel worse"'
    },
    {
        "id": "S3-c",
        "scenario": "game comparison",
        "q": '"downgrade original"'
    },

    # ========== SEARCH SCENARIO 4 ==========
    {
        "id": "S4-a",
        "scenario": "negative reviews on game favored by critics",
        "fq": [
            "recommend:\"Not Recommended\"",
            "{!child of=\"doc_type:game\"}_query_:\"{!parent which='doc_type:game'}metascore:[80 TO 100]\""
        ],
    },
    {
        "id": "S4-b",
        "scenario": "critic and player disagreement",
        "q": '{!parent which="doc_type:game"}(source:Metacritic AND metascore:[75 TO 100])',
        "fq": [
            "doc_type:game",
            "{!frange l=0.5}div(negative,sum(positive,negative))",
        ],
    },
]

def run(query):
    params = {
        "q": query.get("q", "*:*"),
        "df": query.get("df", "review"),
        "fq": query.get("fq", "doc_type:review"),
        "rows": query.get("rows", 10),
        "fl": query.get("fl", "id,name,App_ID,source,recommend,review,score"),
        "wt": "json",
    }
    url = f"{URL}?{urllib.parse.urlencode(params, doseq=True)}"
    with urllib.request.urlopen(url) as r:
        return json.load(r)["response"]

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    dump = open(os.path.join(OUT_DIR, "dump.txt"), "w", encoding="utf-8")
    qrels = open(os.path.join(OUT_DIR, "qrels.txt"), "w", encoding="utf-8")
    results = open(os.path.join(OUT_DIR, "results.txt"), "w", encoding="utf-8")

    for query in QUERIES:
        resp = run(query)
        dump.write(f"\n== {query['id']} [{query['scenario']}] q={query.get("q", "")!r} fq={query.get("fq", "")!r} found={resp['numFound']}\n")
        print(f"\n== {query['id']} [{query['scenario']}] q={query.get("q", "")!r} fq={query.get("fq", "")!r} found={resp['numFound']}")
        for rank, doc in enumerate(resp["docs"], start=1):
            results.write(f"{query['id']} Q0 {doc['id']} {rank} {doc.get('score', 0):.6f} {SETUP}\n")
            qrels.write(f"{query['id']} 0 {doc['id']} 0\n")
            dump.write(str(doc.get("review", "")).replace("\n", " ") + "\n")
            print(f"{doc['id']:<22}{doc.get('score',0):.2f}{str(doc.get("review","")).replace('\n',' ')[:100]}")

    dump.close()
    qrels.close()
    results.close()
