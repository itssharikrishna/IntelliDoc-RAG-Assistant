from sentence_transformers import SentenceTransformer
import faiss
import sqlite3
from pathlib import Path
from app.config import FAISS_DIR, METADATA_DB, EMBED_MODEL

Path(FAISS_DIR).mkdir(parents=True, exist_ok=True)

class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(EMBED_MODEL)
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index_path = Path(FAISS_DIR) / "index.faiss"

        # SQLite DB for metadata
        self.conn = sqlite3.connect(METADATA_DB, check_same_thread=False)
        self._create_db()

        # Load FAISS or create new
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = faiss.IndexFlatL2(self.dim)

    def _create_db(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS docs (
            id TEXT PRIMARY KEY,
            source TEXT,
            text TEXT
        )
        """)
        self.conn.commit()

    def encode(self, texts):
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def append(self, texts, metadatas):
        embeddings = self.encode(texts)
        self.index.add(embeddings)
        faiss.write_index(self.index, str(self.index_path))

        cur = self.conn.cursor()
        for m in metadatas:
            cur.execute("INSERT OR REPLACE INTO docs (id, source, text) VALUES (?,?,?)",
                        (m["id"], m.get("source"), m.get("text")))
        self.conn.commit()

    def search(self, query, k=5):
        q_vec = self.encode([query])
        D, I = self.index.search(q_vec, k)
        # For simplicity, retrieve first k rows from DB as best-effort fallback
        cur = self.conn.cursor()
        cur.execute("SELECT id, source, text FROM docs LIMIT ?", (k,))
        rows = cur.fetchall()
        results = [{"id": r[0], "source": r[1], "text": r[2]} for r in rows]
        return results
