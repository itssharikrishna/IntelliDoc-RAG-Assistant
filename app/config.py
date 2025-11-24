from pathlib import Path

DATA_DIR = Path("data")
DOCS_DIR = DATA_DIR / "docs"
FAISS_DIR = DATA_DIR / "faiss_index"
METADATA_DB = DATA_DIR / "metadata.db"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_GEN_MODEL = "google/flan-t5-small"

SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_THIS"  # change later; don't commit
ALGORITHM = "HS256"
TOP_K = 5
