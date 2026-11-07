import os
import sys
import json
import urllib.parse
import urllib.request

REVIEW_SETUPS = {
    "basic": {"core": "games_basic", "params": {}},
    "improved": {"core": "games_improved", "params": {"defType": "edismax", "qf": "review", "mm": "100%"}},
}

GAME_SETUPS = {
    "basic": {"core": "games_basic", "params": {}},
    "improved": {"core": "games_improved", "params": {"defType": "edismax", "qf": "review", "mm": "20%"}},
}

NAMES = {k: v.get("name", "") for k, v in json.load(open("data/processed/final_games.json", encoding="utf-8")).items()}
SETUP = sys.argv[1] if len(sys.argv) > 1 else None
if SETUP not in REVIEW_SETUPS:
    sys.exit(f"usage: queries.py {{{', '.join(REVIEW_SETUPS)}}}")
OUT_DIR = f"milestone2/results/{SETUP}"

TEXT_QUERIES = [
    {"id": "S1-a", "scenario": "technical issues", "q": "won't start"},
    {"id": "S1-b", "scenario": "technical issues", "q": "crashes boot"},
    {"id": "S1-c", "scenario": "technical issues", "q": "stuck loading"},
    {"id": "S2-a", "scenario": "aspect-based opinions", "q": "great soundtrack"},
    {"id": "S2-b", "scenario": "aspect-based opinions", "q": "amazing music"},
    {"id": "S2-c", "scenario": "aspect-based opinions", "q": "best sound"},
    {"id": "S3-a", "scenario": "game comparison", "q": "original better"},
    {"id": "S3-b", "scenario": "game comparison", "q": "sequel worse"},
    {"id": "S3-c", "scenario": "game comparison", "q": "downgrade original"},
]

GAME_QUERIES = [
    {"id": "S4-a", "scenario": "critic and player disagreement", "critic_q": "loved amazing masterpiece", "player_q": "hated bad awful terrible boring", "threshold": 0.5},
]

def run_review_query(query, setup):
    cfg = REVIEW_SETUPS[setup]
    params = {
        "q": query["q"],
        "df": "review",
        "fq": "doc_type:review",
        "rows": 10,
        "fl": "id,name,App_ID,source,recommend,review,score",
        "wt": "json",
        **cfg["params"],
    }
    url = f"http://localhost:8983/solr/{cfg['core']}/select?{urllib.parse.urlencode(params, doseq=True)}"
    with urllib.request.urlopen(url) as r:
        return json.load(r)["response"]

def count_by_game(setup, q, fq):
    """Number of matching reviews per App_ID, from a facet on the same query."""
    cfg = GAME_SETUPS[setup]
    params = {
        **cfg["params"],
        "q": q,
        "df": "review",
        "fq": fq,
        "rows": 0,
        "wt": "json",
        "facet": "true",
        "facet.field": "App_ID",
        "facet.limit": -1,
        "facet.mincount": 1,
    }
    url = f"http://localhost:8983/solr/{cfg['core']}/select?{urllib.parse.urlencode(params, doseq=True)}"
    with urllib.request.urlopen(url) as r:
        flat = json.load(r)["facet_counts"]["facet_fields"]["App_ID"]
    return dict(zip(flat[::2], flat[1::2]))

def run_game_query(spec, setup):
    critic = count_by_game(setup, spec["critic_q"], "doc_type:review AND source:Metacritic")
    hits = count_by_game(setup, spec["player_q"], "doc_type:review AND source:Steam")
    total = count_by_game(setup, "*:*", "doc_type:review AND source:Steam")

    rows = []
    for app_id in critic:
        n = total.get(app_id, 0)
        if n == 0:
            continue
        share = hits.get(app_id, 0) / n
        if share >= spec["threshold"]:
            rows.append((app_id, NAMES.get(app_id, ""), share, hits.get(app_id, 0), n))
    rows.sort(key=lambda r: (-r[2], r[0]))
    return rows

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    dump = open(os.path.join(OUT_DIR, "dump.txt"), "w", encoding="utf-8")
    qrels = open(os.path.join(OUT_DIR, "qrels.txt"), "w", encoding="utf-8")
    results = open(os.path.join(OUT_DIR, "results.txt"), "w", encoding="utf-8")

    for query in TEXT_QUERIES:
        resp = run_review_query(query, SETUP)
        header = f"\n== {query['id']} [{query['scenario']}] q={query.get('q', '')!r} found={resp['numFound']}"
        dump.write(header + "\n")
        print(header)
        for rank, doc in enumerate(resp["docs"], start=1):
            label = doc.get("review") or doc.get("name", "")
            results.write(f"{query['id']} Q0 {doc['id']} {rank} {doc.get('score', 0):.6f} {SETUP}\n")
            qrels.write(f"{query['id']} 0 {doc['id']} 0\n")
            dump.write(str(label).replace("\n", " ") + "\n")
            print(f"{doc['id']:<16}{doc.get('score',0):.2f}    {str(label).replace("\n", " ")[:100]}")

    for spec in GAME_QUERIES:
        rows = run_game_query(spec, SETUP)
        header = (f"\n== {spec['id']} [{spec['scenario']}] critic_q={spec['critic_q']!r} "f"player_q={spec['player_q']!r} threshold={spec['threshold']} found={len(rows)}")
        dump.write(header + "\n")
        print(header)
        for rank, (app_id, name, share, hit_n, total_n) in enumerate(rows[:10], start=1):
            game_id = f"game_{app_id}"
            results.write(f"{spec['id']} Q0 {game_id} {rank} {share:.6f} {SETUP}\n")
            qrels.write(f"{spec['id']} 0 {game_id} 0\n")
            line = f"(App_ID {app_id}) {name}: {hit_n}/{total_n} Steam reviews match player_q (share {share:.2f})"
            dump.write(line + "\n")
            print(f"  {game_id:<16} {name:<48} {share:.2f}    {hit_n}/{total_n} Steam reviews match")

    dump.close()
    qrels.close()
    results.close()