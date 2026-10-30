import json
import sys
import urllib.parse
import urllib.request

URL = f"http://localhost:8983/solr/games/select"
QUERIES = [ {"id": "S1-a", "scenario": "technical issues", "q": "game won't start"} ]

def run(query):
    params = {
        "q": query["q"],
        "df": "review",
        "fq": "doc_type:review",
        "rows": 10,
        "fl": "id,name,App_ID,source,recommend,review,score",
        "wt": "json",
    }
    url = f"{URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as r:
        return json.load(r)["response"]

if __name__ == "__main__":
    for query in QUERIES:
        resp = run(query)
        print(f"\n== {query['id']} [{query['scenario']}] q={query['q']!r} found={resp['numFound']}")
        for doc in resp["docs"]:
            text = str(doc.get("review", ""))[:100].replace("\n", " ")
            print(f"  {doc['id']:<22} {doc.get('score', 0):.2f}  {text}")