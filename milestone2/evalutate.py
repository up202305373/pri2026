import os
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def load_trec_format(qrels_path, results_path):
    qrels = defaultdict(dict)
    with open(qrels_path, 'r') as f:
        for line in f:
            qid, _, docid, rel = line.strip().split()
            qrels[qid][docid] = int(rel)
            
    results = defaultdict(list)
    with open(results_path, 'r') as f:
        for line in f:
            qid, _, docid, rank, score, _ = line.strip().split()
            results[qid].append((docid, float(score)))
            
    # Sort results by score descending
    for qid in results:
        results[qid].sort(key=lambda x: x[1], reverse=True)
        
    return qrels, results

def calculate_metrics(qrels, results, k=10):
    average_precisions = []
    precisions_at_k = []
    
    # For 11-point Precision-Recall curve
    recall_levels = [x / 10.0 for x in range(11)]
    interpolated_precisions = {lvl: [] for lvl in recall_levels}

    for qid, docs in results.items():
        if qid not in qrels:
            continue
            
        relevant_docs = {docid for docid, rel in qrels[qid].items() if rel > 0}
        total_rel = len(relevant_docs)
        if total_rel == 0:
            continue

        hits = 0
        ap_sum = 0.0
        precisions = []
        recalls = []

        for i, (docid, _) in enumerate(docs):
            if docid in relevant_docs:
                hits += 1
                ap_sum += hits / (i + 1)
            
            precisions.append(hits / (i + 1))
            recalls.append(hits / total_rel)
            
            if i + 1 == k:
                precisions_at_k.append(hits / k)

        average_precisions.append(ap_sum / total_rel)

        # Calculate 11-point interpolated precision for this query
        for lvl in recall_levels:
            # Find max precision for any recall >= lvl
            valid_precs = [p for p, r in zip(precisions, recalls) if r >= lvl]
            max_p = max(valid_precs) if valid_precs else 0.0
            interpolated_precisions[lvl].append(max_p)

    map_score = sum(average_precisions) / len(average_precisions) if average_precisions else 0
    p_at_k_score = sum(precisions_at_k) / len(precisions_at_k) if precisions_at_k else 0
    
    avg_interpolated_precisions = [
        sum(interpolated_precisions[lvl]) / len(interpolated_precisions[lvl]) 
        if len(interpolated_precisions[lvl]) > 0 else 0.0
        for lvl in recall_levels
    ]

    return map_score, p_at_k_score, recall_levels, avg_interpolated_precisions

def plot_pr_curve(recall_levels, basic_precs, improved_precs, output_dir):
    plt.figure(figsize=(8, 6))
    plt.plot(recall_levels, basic_precs, label='Basic Setup', marker='o')
    plt.plot(recall_levels, improved_precs, label='Improved Setup', marker='s')
    
    plt.title('11-Point Interpolated Precision-Recall Curve')
    plt.xlabel('Recall')
    plt.ylabel('Interpolated Precision')
    plt.legend()
    plt.grid(True)
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    
    plt.savefig(os.path.join(output_dir, 'pr_curve.png'))
    print(f"Saved PR curve to {output_dir}/pr_curve.png")

if __name__ == "__main__":
    basic_qrels, basic_res = load_trec_format("milestone2/results/basic/judgements.txt", "milestone2/results/basic/results.txt")
    imp_qrels, imp_res = load_trec_format("milestone2/results/improved/judgements.txt", "milestone2/results/improved/results.txt")

    b_map, b_p10, b_recs, b_precs = calculate_metrics(basic_qrels, basic_res, k=10)
    i_map, i_p10, i_recs, i_precs = calculate_metrics(imp_qrels, imp_res, k=10)

    print(f"=== Basic Setup ===")
    print(f"MAP: {b_map:.4f}")
    print(f"P@10: {b_p10:.4f}")
    
    print(f"\n=== Improved Setup ===")
    print(f"MAP: {i_map:.4f}")
    print(f"P@10: {i_p10:.4f}")

    plot_pr_curve(b_recs, b_precs, i_precs, "milestone2/")