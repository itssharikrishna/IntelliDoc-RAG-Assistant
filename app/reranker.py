# app/reranker.py
from sentence_transformers import CrossEncoder
import numpy as np
from typing import List, Dict

# model name (small, fast, good quality)
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# lazy singleton
_reranker = None
def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(CROSS_ENCODER_MODEL)
    return _reranker

def rerank(query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    candidates: list of dicts each with at least 'text' key (and metadata).
    Returns top_k candidates re-ordered by cross-encoder score (desc).
    """
    if not candidates:
        return []
    reranker = get_reranker()
    pairs = [[query, c["text"]] for c in candidates]
    scores = reranker.predict(pairs, batch_size=32)
    # attach scores and sort
    for c, s in zip(candidates, scores):
        c["_score"] = float(s)
    candidates.sort(key=lambda x: x["_score"], reverse=True)
    return candidates[:top_k]
