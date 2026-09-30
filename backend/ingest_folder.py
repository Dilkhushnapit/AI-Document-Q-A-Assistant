"""Bulk-index every supported file in a folder.

Usage:  python ingest_folder.py sample_docs
"""
import shutil
import sys
from pathlib import Path

from app.config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from app.ingest import ingest_file, list_documents

folder = Path(sys.argv[1] if len(sys.argv) > 1 else "sample_docs")
files = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in ALLOWED_EXTENSIONS]
for path in files:
    dest = UPLOAD_DIR / path.name
    if path.resolve() != dest.resolve():
        shutil.copy(path, dest)
    print(f"{path.name}: {ingest_file(dest)} chunks")

docs = list_documents()
print(f"\nIndex now holds {len(docs)} documents, {sum(docs.values())} chunks.")
