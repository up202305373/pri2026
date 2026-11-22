"""Rerank the lexical candidate pool with a cross-encoder."""
# pip install onnxruntime transformers

import ast
import os
import re

import onnxruntime as ort
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

MODEL_ID = "Xenova/ms-marco-MiniLM-L-6-v2"
ONNX_FILE = "onnx/model.onnx"
MAX_LENGTH = 512
BATCH_SIZE = 32
TOP_K = 30

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE, "results", "rerank")
HEADER_RE = re.compile(r"^== (\S+) \[(.*?)\] q=(.*?) found=(\d+)\s*$")

def load_model():
    model_path = hf_hub_download(MODEL_ID, ONNX_FILE)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    input_names = [inp.name for inp in session.get_inputs()]
    return tokenizer, session, input_names

def load_candidates(path):
    groups = []
    current = None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip():
                continue

            header = HEADER_RE.match(line)
            if header:
                current = {
                    "qid": header.group(1),
                    "query": ast.literal_eval(header.group(3)),
                    "docs": [],
                }
                groups.append(current)
                continue

            if current is None:
                continue
            rank, score, docid, source, name, review = line.split("\t", 5)
            current["docs"].append({
                "id": docid,
                "source": source,
                "name": name,
                "review": review,
                "lexical_score": float(score),
            })
    return groups

def score_pairs(groups, tokenizer, session, input_names):
    for group in groups:
        pairs = [(group["query"], doc["review"]) for doc in group["docs"]]
        scores = []
        for start in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[start:start + BATCH_SIZE]
            encoded = tokenizer(
                [query for query, _ in batch],
                [review for _, review in batch],
                truncation=True,
                max_length=MAX_LENGTH,
                padding=True,
                return_tensors="np",
            )
            feed = {name: encoded[name] for name in input_names if name in encoded}
            logits = session.run(None, feed)[0].reshape(-1)
            scores.extend(float(value) for value in logits)

        for doc, score in zip(group["docs"], scores):
            doc["ce_score"] = score

def write_outputs(groups):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "results.txt"), "w", encoding="utf-8") as results, \
         open(os.path.join(RESULTS_DIR, "qrels.txt"), "w", encoding="utf-8") as qrels, \
         open(os.path.join(RESULTS_DIR, "ranked.txt"), "w", encoding="utf-8") as ranked:
        for group in groups:
            ordered = sorted(group["docs"], key=lambda doc: doc["ce_score"], reverse=True)[:TOP_K]
            print(f"\n== {group['qid']} q={group['query']!r} candidates={len(group['docs'])}")
            for rank, doc in enumerate(ordered, start=1):
                results.write(f"{group['qid']} Q0 {doc['id']} {rank} {doc['ce_score']:.6f} rerank\n")
                qrels.write(f"{group['qid']} 0 {doc['id']} 0\n")
                ranked.write(
                    f"{rank}\t{doc['ce_score']:.6f}\t{doc['id']}\t{doc['source']}\t"
                    f"{doc['name']}\t{doc['review'].replace(chr(10), ' ')}\n"
                )
                if rank <= 3:
                    print(f"{rank}\t{doc['ce_score']:.4f}\t{doc['id']}\t{doc['name']}")

def main():
    candidates = os.path.join(RESULTS_DIR, "dump.txt")
    if not os.path.exists(candidates):
        raise SystemExit(
            "Missing candidate pool. Run first:\n"
            "    python3 milestone3/queries.py rerank"
        )

    groups = load_candidates(candidates)
    if not groups:
        raise SystemExit(f"No queries found in {candidates}")

    print(f"Loading cross-encoder {MODEL_ID}")
    tokenizer, session, input_names = load_model()
    score_pairs(groups, tokenizer, session, input_names)
    write_outputs(groups)
    print(f"\nWrote top {TOP_K} per query to {RESULTS_DIR}/")

if __name__ == "__main__":
    main()
