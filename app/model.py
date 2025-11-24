# app/model.py
from transformers import pipeline
from app.config import HF_GEN_MODEL

# Lazy-initialize pipeline so server startup is fast; first request will load model.
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        # text2text-generation works well for flan models like google/flan-t5-small
        _generator = pipeline("text2text-generation", model=HF_GEN_MODEL, device=-1)  # CPU device=-1
    return _generator

def synthesize_answer(query, contexts, max_length=200):
    """
    contexts: list of dicts with 'text' and optionally 'source'
    Returns a synthesized string answer that cites sources.
    """
    prompt = "Use the context below to answer the question. If the answer is not in the context, say 'I don't know'.\n\nContext:\n"
    for i, c in enumerate(contexts):
        text = c.get("text", "")
        source = c.get("source", "unknown")
        prompt += f"[{i+1}] Source: {source}\n{text}\n\n"
    prompt += f"Question: {query}\nAnswer:"
    gen = get_generator()
    out = gen(prompt, max_length=max_length, do_sample=False)
    if isinstance(out, list) and len(out) > 0:
        return out[0].get("generated_text", "").strip()
    return ""
