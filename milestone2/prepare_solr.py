import os
import glob
import json

import pandas as pd

OUT = "data/solr"
BATCH_SIZE = 50
CHILD_KEY = "_childDocuments_"

def is_missing(v):
    if isinstance(v, str):
        return not v.strip()
    return v is None or pd.isna(v)

def number(value):
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return None
    return int(value) if float(value).is_integer() else float(value)

def game_doc(app_id, info):
    doc = {}
    for key, v in info.items():
        if key == "userscore":
            v = number(v)
        if isinstance(v, dict):
            v = list(v)
        if isinstance(v, list):
            v = [x for x in v if isinstance(x, (str, int, float, bool))]
        if v is None or v == "" or v == []:
            continue
        doc[key] = v
    doc.update(id=f"game_{app_id}", doc_type="game", App_ID=app_id)
    return doc

def review_doc(row, id_, name):
    doc = {k: v for k, v in row.items() if not is_missing(v)}
    doc.update(id=id_, doc_type="review", name=name)
    return doc

def main():
    with open("data/processed/final_games.json", encoding="utf-8") as f:
        games = json.load(f)

    children = {app_id: [] for app_id in games}
    for path in sorted(glob.glob("data/processed/Final_Search_Corpus_part_*.csv.gz")):
        for row in pd.read_csv(path, dtype={"App_ID": str}).to_dict("records"):
            app_id = row["App_ID"]
            if app_id in games:
                kids = children[app_id]
                kids.append(review_doc(row, f"{app_id}_{len(kids) + 1}", games[app_id].get("name")))

    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(f"{OUT}/games_batch_*.json"):
        os.remove(old)

    app_ids = sorted(games)
    for i in range(0, len(app_ids), BATCH_SIZE):
        batch = []
        for app_id in app_ids[i:i + BATCH_SIZE]:
            parent = game_doc(app_id, games[app_id])
            parent[CHILD_KEY] = children[app_id]
            batch.append(parent)
        with open(f"{OUT}/games_batch_{i // BATCH_SIZE + 1:02d}.json", "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False)

if __name__ == "__main__":
    main()