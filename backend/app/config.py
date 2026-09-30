"""Central settings. Everything tunable about the RAG pipeline lives here."""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"        # raw files users upload
CHROMA_DIR = BASE_DIR / "chroma_db"      # persisted vector database
UPLOAD_DIR.mkdir(exist_ok=True)

COLLECTION_NAME = "documents"
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

# Chunking: ~1000 characters per chunk with 200 overlap so a sentence cut at a
# boundary still appears whole in one of the two neighbouring chunks.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval: how many chunks to pull from the vector DB per question.
TOP_K = 5

# LLM
LLM_MODEL = "claude-opus-5-5"
MAX_TOKENS = 4096
