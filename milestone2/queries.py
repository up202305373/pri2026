import json
import sys
import urllib.parse
import urllib.request

URL = f"http://localhost:8983/solr/games/select"
QUERIES = [
    # ========== SEARCH SCENARIO 1 ==========
    {
    "id": "S1-a",
        "scenario": "technical issues",
        "q": '"game won\'t start" OR "game won\'t launch"'
    },
    {
        "id": "S1-b",
        "scenario": "technical issues",
        "q": '"crashes on loading screens"'
    },

    # ========== SEARCH SCENARIO 2 ==========

    # ========== SEARCH SCENARIO 3 ==========

    # ========== SEARCH SCENARIO 4 ==========
    {
        "id": "S4-a",
        "scenario": "negative reviews on game favored by critics",
        "fq": [
            "recommend:\"Not Recommended\"",
            "{!child of=\"doc_type:game\"}_query_:\"{!parent which='doc_type:game'}metascore:[80 TO 100]\""
        ],
    }
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
    file = open("milestone2/output.txt", "w", encoding="utf-8")
    for query in QUERIES:
        resp = run(query)
        file.write(f"\n== {query.get('id', 'N/A')} [{query.get('scenario', 'N/A')}] q={query.get('q', '*:*')!r} found={resp['numFound']}")
        print(f"\n== {query.get('id', 'N/A')} [{query.get('scenario', 'N/A')}] q={query.get('q', '*:*')!r} found={resp['numFound']}")
        for doc in resp["docs"]:
            full_text = str(doc.get("review", "")).replace("\n", " ")
            text = str(doc.get("review", ""))[:100].replace("\n", " ")
            print(f" {doc['id']:<22} {doc.get('score', 0):.2f} {text}")
            file.write(full_text + "\n")
    file.close()
