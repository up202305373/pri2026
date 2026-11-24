import os
import glob
import json

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

OUT = "data/solr_semantics"
BATCH_SIZE = 50
CHILD_KEY = "_childDocuments_"

MODEL_NAME = "all-MiniLM-L6-v2"
MAX_TOKENS = 32  # default: 256
VECTOR_CACHE = "data/solr_semantics/review_vectors.npy"
VECTOR_IDS = "data/solr_semantics/review_vector_ids.json"
VECTOR_CONFIG = "data/solr_semantics/review_vector_config.json"
ENCODE_BATCH = 128
ENCODE_CONFIG = {"model": MODEL_NAME, "max_tokens": MAX_TOKENS}

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

def attach_vectors(children):
    """Add review_vector to every child document, reusing the cache when the IDs match."""
    flat = [d for app_id in children for d in children[app_id]]
    ids = [d["id"] for d in flat]

    vecs = None
    if all(os.path.exists(p) for p in (VECTOR_CACHE, VECTOR_IDS, VECTOR_CONFIG)):
        with open(VECTOR_IDS, encoding="utf-8") as f:
            ids_match = json.load(f) == ids
        with open(VECTOR_CONFIG, encoding="utf-8") as f:
            config_match = json.load(f) == ENCODE_CONFIG
        if ids_match and config_match:
            vecs = np.load(VECTOR_CACHE)

    if vecs is None:
        model = SentenceTransformer(MODEL_NAME)
        texts = [str(d.get("review", "")) for d in flat]
        vecs = model.encode(
            texts,
            batch_size=ENCODE_BATCH,
            normalize_embeddings=True,
            show_progress_bar=True,
            processing_kwargs={"text": {"max_length": MAX_TOKENS, "truncation": True}},
        )
        os.makedirs(OUT, exist_ok=True)
        np.save(VECTOR_CACHE, vecs)
        with open(VECTOR_IDS, "w", encoding="utf-8") as f:
            json.dump(ids, f)
        with open(VECTOR_CONFIG, "w", encoding="utf-8") as f:
            json.dump(ENCODE_CONFIG, f)

    for d, v in zip(flat, vecs):
        d["review_vector"] = [round(float(x), 5) for x in v]

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

    attach_vectors(children)

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
            json.dump(batch, f, ensure_ascii=False, separators=(",", ":"))

if __name__ == "__main__":
    main()