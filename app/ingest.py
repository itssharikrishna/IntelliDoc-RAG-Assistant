import uuid
from pathlib import Path
from app.utils import extract_text_from_pdf, chunk_text
from app.embedder import Embedder
from app.config import DOCS_DIR

Path(DOCS_DIR).mkdir(parents=True, exist_ok=True)

def ingest_file_local(file_path, source_name=None):
    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)
    metadatas = []
    for i, chunk in enumerate(chunks):
        metadatas.append({
            "id": str(uuid.uuid4()),
            "source": source_name or Path(file_path).name,
            "text": chunk
        })
    emb = Embedder()
    emb.append(chunks, metadatas)
    return len(chunks)
