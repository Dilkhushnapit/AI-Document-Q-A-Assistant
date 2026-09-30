# AI Document Q&A Assistant (RAG)

Upload PDFs, Word files, or text/Markdown notes, then ask questions about them in a chat UI. Answers come **only** from your documents, and every claim cites the passage it came from, like `[2]`. You can click a citation to see the exact source text.

**Stack:** Python · FastAPI · LangChain · ChromaDB · Claude API (Anthropic) · React (Vite)

```
                    ┌──────────── INDEXING (once per document) ────────────┐
 PDF/DOCX/TXT ──►  Load  ──►  Split into chunks  ──►  Embed (MiniLM)  ──►  ChromaDB
                    (LangChain loaders)  (1000 chars, 200 overlap)   (384-dim vectors)   (on disk)
                    └──────────────────────────────────────────────────────┘

                    ┌──────────── QUERYING (every question) ───────────────┐
 Question ──► Embed ──► Top-5 similar chunks (cosine) ──► Prompt = rules + numbered chunks + question
                                                                   │
 React UI  ◄── streamed tokens + sources ◄── FastAPI ◄── Claude writes answer citing [n]
                    └──────────────────────────────────────────────────────┘
```

## Project structure

```
backend/
  app/config.py        settings (chunk size, top-k, model)
  app/vectorstore.py   embedding model + ChromaDB connection
  app/ingest.py        load → chunk → embed → store; list/delete documents
  app/rag.py           retrieve → build grounded prompt → stream the LLM answer
  app/main.py          FastAPI endpoints
  ingest_folder.py     bulk-index a folder from the command line
  sample_docs/         3 demo documents
frontend/
  src/App.jsx          chat state + streaming
  src/api.js           fetch helpers, NDJSON stream reader
  src/components/      Sidebar (upload/list/delete), Message (answer + citations)
```

## Run it

You need Python 3.10+, Node 20+, and an Anthropic API key from https://console.anthropic.com.

**1. Backend** (terminal 1)
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your key into .env
python ingest_folder.py sample_docs   # optional: index the demo docs
uvicorn app.main:app --reload --port 8000
```
The first run downloads the embedding model (~80 MB) automatically. Interactive API docs are at http://localhost:8000/docs.

**2. Frontend** (terminal 2)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

> **Note:** Some college and office networks block `huggingface.co`, `*.amazonaws.com`, or `api.anthropic.com`. If you see "Could not reach the LLM API" or the model download times out, switch to a mobile hotspot.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/documents` | List indexed files and their chunk counts |
| POST | `/api/documents` | Upload and index one or more files (multipart) |
| DELETE | `/api/documents/{name}` | Remove a file and its vectors |
| POST | `/api/search` | Retrieval only (no LLM), for debugging |
| POST | `/api/chat` | `{question, history}` → streamed NDJSON: `sources`, `token`…, `done` |

## Design decisions

- **Local embeddings (all-MiniLM-L6-v2 via ONNX):** free, fast, and private. The only paid call is the final answer.
- **Chunk metadata (file, page, chunk #):** this is what makes citations possible.
- **Deterministic chunk IDs + delete-before-insert:** re-uploading a file replaces it instead of creating duplicates.
- **Numbered passages + strict system prompt:** the model must cite `[n]` and must say "I couldn't find that" instead of guessing. This is how it reduces hallucination.
- **Streaming (NDJSON):** sources arrive first, then the answer appears token by token, so the UI feels instant.
- **Short chat history (last 6 turns)** is sent so follow-up questions work. Only the current question triggers retrieval.

## Ideas to extend

Hybrid search (BM25 + vectors), a cross-encoder re-ranker, query rewriting for follow-up questions, an evaluation set scored with RAGAS (faithfulness, answer relevance), per-user collections with auth, and Docker Compose deployment.
