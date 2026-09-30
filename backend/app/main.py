"""FastAPI server exposing the RAG pipeline to the React frontend."""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import ingest
from .config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from .rag import answer_stream, retrieve

app = FastAPI(title="AI Document Q&A Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    history: list[Turn] = []


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/documents")
def documents():
    return [{"name": n, "chunks": c} for n, c in sorted(ingest.list_documents().items())]


@app.post("/api/documents")
async def upload(files: list[UploadFile]):
    results = []
    for f in files:
        name = Path(f.filename or "").name  # strip any directory parts
        if Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"{name}: only {', '.join(sorted(ALLOWED_EXTENSIONS))} files are supported")
        dest = UPLOAD_DIR / name
        dest.write_bytes(await f.read())
        try:
            chunks = ingest.ingest_file(dest)
        except Exception as e:  # corrupt PDF, bad encoding, ...
            dest.unlink(missing_ok=True)
            raise HTTPException(422, f"{name}: could not be processed ({e})")
        results.append({"name": name, "chunks": chunks})
    return results


@app.delete("/api/documents/{name}")
def delete(name: str):
    name = Path(name).name
    ingest.delete_document(name)
    (UPLOAD_DIR / name).unlink(missing_ok=True)
    return {"deleted": name}


@app.post("/api/search")
def search(req: ChatRequest):
    """Retrieval only, no LLM. Handy for debugging what the retriever finds."""
    return retrieve(req.question)


@app.post("/api/chat")
def chat(req: ChatRequest):
    history = [t.model_dump() for t in req.history]
    return StreamingResponse(answer_stream(req.question, history), media_type="application/x-ndjson")
