"""Ingestion pipeline: load -> split into chunks -> embed -> store in ChromaDB.

This is the "offline" half of RAG. It runs once per document, not per question.
"""
import hashlib
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CHUNK_OVERLAP, CHUNK_SIZE
from .vectorstore import get_vectorstore

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    # Try to split on paragraphs first, then lines, then sentences, then words.
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_file(path: Path) -> list[Document]:
    """Read a file into LangChain Documents (one per PDF page, one per text file)."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
    elif ext == ".docx":
        loader = Docx2txtLoader(str(path))
    elif ext in {".txt", ".md"}:
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader.load()


def ingest_file(path: Path) -> int:
    """Index one file. Returns the number of chunks stored.

    Re-ingesting the same filename replaces its old chunks, so the index never
    holds stale duplicates.
    """
    pages = load_file(path)
    chunks = _splitter.split_documents(pages)
    chunks = [c for c in chunks if c.page_content.strip()]

    for i, chunk in enumerate(chunks):
        # Metadata is what makes citations possible later: every chunk
        # remembers which file (and PDF page) it came from.
        page = chunk.metadata.get("page")
        chunk.metadata = {
            "source": path.name,
            "page": int(page) + 1 if page is not None else -1,  # 1-indexed for humans
            "chunk": i,
        }

    store = get_vectorstore()
    delete_document(path.name)
    if chunks:
        # Deterministic IDs: same file + same chunk index -> same ID.
        ids = [hashlib.sha1(f"{path.name}:{i}".encode()).hexdigest() for i in range(len(chunks))]
        store.add_documents(chunks, ids=ids)
    return len(chunks)


def delete_document(name: str) -> None:
    get_vectorstore().delete(where={"source": name})


def list_documents() -> dict[str, int]:
    """Map of filename -> number of chunks currently indexed."""
    data = get_vectorstore().get(include=["metadatas"])
    counts: dict[str, int] = {}
    for meta in data["metadatas"]:
        counts[meta["source"]] = counts.get(meta["source"], 0) + 1
    return counts
