import json
import sys
import urllib.parse
import urllib.request

URL = f"http://localhost:8983/solr/games/select"
QUERIES = [ {"id": "S1-a", "scenario": "technical issues", "q": '"game won\'t start"' }, 
            {"id": "S1-b", "scenario": "technical issues", "q": '"crashes on loading screens"' },
           ]

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
    file = open("milestone2/output.txt", "w")
    for query in QUERIES:
        resp = run(query)
        file.write(f"\n== {query['id']} [{query['scenario']}] q={query['q']!r} found={resp['numFound']}\n")
        print(f"\n== {query['id']} [{query['scenario']}] q={query['q']!r} found={resp['numFound']}")
        for doc in resp["docs"]:
            full_text = str(doc.get("review", "")).replace("\n", " ")
            text = str(doc.get("review", ""))[:100].replace("\n", " ")
            print(f" {doc['id']:<22} {doc.get('score', 0):.2f} {text}")
            file.write(full_text + "\n")
    file.close()
