from pypdf import PdfReader
import re

def extract_text_from_pdf(path):
    text = ""
    reader = PdfReader(path)
    for p in reader.pages:
        page_text = p.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def clean_text(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def chunk_text(text, chunk_chars=1200, overlap_chars=200):
    text = clean_text(text)
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = start + chunk_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = max(end - overlap_chars, end)
    return chunks
