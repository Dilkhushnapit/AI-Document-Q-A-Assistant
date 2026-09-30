"""Embeddings + ChromaDB vector store.

Embeddings turn text into a list of numbers (a vector) so that texts with
similar meaning end up close together. We use the all-MiniLM-L6-v2 model that
ships with ChromaDB (runs locally via ONNX, free, 384 dimensions), wrapped in
LangChain's `Embeddings` interface so LangChain's Chroma integration can use it.
"""
from functools import lru_cache

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from .config import CHROMA_DIR, COLLECTION_NAME


class LocalEmbeddings(Embeddings):
    """LangChain adapter around ChromaDB's built-in MiniLM embedding model."""

    def __init__(self) -> None:
        self._fn = DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(x) for x in vec] for vec in self._fn(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache
def get_vectorstore() -> Chroma:
    """One shared, disk-persisted Chroma collection for the whole app.

    Cosine distance is used so scores are comparable regardless of text length.
    """
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=LocalEmbeddings(),
        persist_directory=str(CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )
