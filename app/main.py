# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Dict

from app.auth import create_access_token, verify_token
from app.ingest import ingest_file_local
from app.embedder import Embedder
from app.config import DOCS_DIR, TOP_K
from app.model import synthesize_answer
from app.reranker import rerank

app = FastAPI()
Path(DOCS_DIR).mkdir(parents=True, exist_ok=True)

# Serve static files under /static so API routes stay free
app.mount("/static", StaticFiles(directory="web"), name="static")

# Serve index at /
@app.get("/", include_in_schema=False)
def root():
    index_path = Path("web") / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"status": "ok"}


@app.post("/admin/login")
def admin_login(username: str = Form(...), password: str = Form(...)):
    # MVP: hardcoded admin account. Replace with proper OIDC in production.
    if username == "admin" and password == "adminpass":
        token = create_access_token({"sub": "admin"})
        return {"access_token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/admin/upload")
async def upload(file: UploadFile = File(...), token: str = Form(...)):
    """
    Uploads a PDF (multipart/form-data: file + token) and ingests it.
    Returns number of chunks indexed.
    """
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    dest = Path(DOCS_DIR) / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())

    chunks = ingest_file_local(str(dest), file.filename)
    return {"status": "ok", "chunks_indexed": chunks}


@app.post("/query")
async def query(payload: dict):
    """
    Expects JSON body: { "q": "your question" }
    Returns: { "query": ..., "answer": ..., "contexts": [...] }
    """
    q = payload.get("q")
    if not q:
        raise HTTPException(status_code=400, detail="query missing")

    emb = Embedder()
    # Step 1: retrieve a larger candidate pool from FAISS (e.g., 50)
    candidates = emb.search(q, k=50)

    # Step 2: re-rank candidates with cross-encoder and keep top-K
    contexts: List[Dict] = rerank(q, candidates, top_k=TOP_K)

    # Step 3: synthesize final answer using top contexts
    answer = synthesize_answer(q, contexts)

    return {"query": q, "answer": answer, "contexts": contexts}


@app.get("/health")
def health():
    return {"status": "ok"}
