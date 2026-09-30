# Interview Guide: AI Document Q&A Assistant

## 1. The 30-second pitch

> "I built a document Q&A assistant using Retrieval-Augmented Generation. You upload PDFs or Word files, and the backend splits them into overlapping chunks, turns each chunk into an embedding vector, and stores them in ChromaDB. When you ask a question, I embed the question, pull the five most similar chunks by cosine similarity, and send them to the LLM as numbered passages with strict instructions to answer only from them and cite each claim. The answer streams back through a FastAPI endpoint to a React chat UI, and each citation expands to show the exact source text. That's how it reduces hallucinations: the model is grounded in retrieved text, and the user can verify every claim."

## 2. Walk through the code (the order to explain it)

1. **`ingest.py` — indexing.** LangChain loaders (`PyPDFLoader`, `Docx2txtLoader`, `TextLoader`) read the files. `RecursiveCharacterTextSplitter` makes chunks of about 1000 characters with a 200-character overlap. Each chunk keeps metadata (file name, page) for citations.
2. **`vectorstore.py` — embeddings + DB.** The all-MiniLM-L6-v2 model turns text into 384 numbers, and similar meaning gives nearby vectors. ChromaDB stores them on disk with a cosine-distance HNSW index for fast nearest-neighbour search.
3. **`rag.py` — answering.** It embeds the question, runs `similarity_search_with_score` for the top 5 chunks, and builds a prompt with numbered passages. It calls the LLM with a system prompt that forces citations and "I don't know" when the answer isn't there, then streams the tokens.
4. **`main.py` — API.** FastAPI endpoints handle upload, list, delete, search, and chat. Chat returns a `StreamingResponse` of newline-delimited JSON events.
5. **React frontend.** It reads the stream with `fetch` + `ReadableStream` and appends tokens to the last message. It parses `[n]` in the answer and shows only the sources that were actually cited.

## 3. Likely interview questions and good answers

**What is RAG and why use it instead of fine-tuning?**
RAG gives the model relevant text at question time. Fine-tuning changes the model's weights. RAG is cheaper, updates instantly when documents change (just re-index), and gives citations. Fine-tuning is better for teaching a style or format, not for teaching facts.

**What is an embedding?**
A list of numbers that represents meaning. Texts with similar meaning have vectors pointing in similar directions, so "annual leave days" finds "24 days of paid annual leave" even without exact keyword overlap.

**Why a vector database? Why not just search with SQL `LIKE`?**
Keyword search misses synonyms and paraphrases. A vector DB does semantic similarity search. An approximate-nearest-neighbour index (HNSW) keeps that search fast even over millions of chunks.

**What is cosine similarity?**
The cosine of the angle between two vectors: 1 means the same direction (same meaning), 0 means unrelated. It ignores vector length, so a long chunk and a short question can still match well.

**Why chunk at all? How did you pick 1000/200?**
LLM context and embedding models work best on focused passages. Whole documents dilute the meaning, and tiny chunks lose context. 1000 characters is roughly a paragraph or two. The 200-character overlap keeps a sentence that falls on a boundary whole in at least one chunk. I'd tune these on an evaluation set.

**How do you reduce hallucinations?**
(1) The model only sees retrieved passages. (2) The system prompt forbids outside knowledge and requires "I couldn't find that" when the answer is missing. (3) Every claim must cite `[n]`, and the UI shows the source text so users can verify it.

**How are citations implemented?**
Each chunk stores its file name and page as metadata. Retrieved chunks are numbered `[1]…[5]` in the prompt, the model cites those numbers, and the frontend maps the numbers back to the source metadata.

**Why streaming?**
LLM answers take seconds. Streaming shows the first words almost immediately, which feels much faster. I used NDJSON: the first event carries the sources, then token events, then done.

**What if the same file is uploaded twice?**
Chunk IDs are a hash of filename + chunk index, and old chunks for that file are deleted before inserting, so there are no duplicates.

**How would you scale or improve it?**
Hybrid search (BM25 + vector) for exact terms like product codes, a re-ranker model on the top 20 → best 5, query rewriting for follow-ups ("what about the second one?"), a hosted vector DB (pgvector/Pinecone), background ingestion jobs for big files, per-user collections with auth, and caching repeated questions.

**How would you evaluate it?**
Build a set of question/expected-answer pairs from the documents. Measure retrieval hit-rate (was the right chunk in the top 5?) and use RAGAS-style metrics: faithfulness (is the answer supported by the context?) and answer relevance.

**Limitations?**
Scanned PDFs need OCR. Tables and images aren't understood well. Questions that need the whole document ("summarize everything") don't fit a top-5 retrieval. Answer quality is capped by retrieval quality.

## 4. Before you put it on your resume

- Run it yourself, upload your own PDFs, and replace `[N]` on your resume with the real number of documents you indexed.
- Be ready to open the code and explain `rag.py` line by line. It's the heart of the project.
- Try changing `CHUNK_SIZE` and `TOP_K` in `config.py` and notice how the answers change. Interviewers love "I experimented and saw…".

## 5. YouTube learning path (in this order)

**Step 1 — Concepts (about 1 hour)**
- [What is Retrieval-Augmented Generation (RAG)? — IBM Technology](https://www.youtube.com/watch?v=T-D1OfcDW1M) (6 min; the best short intro)
- [But what is a GPT? Visual intro to transformers — 3Blue1Brown](https://www.youtube.com/watch?v=wjZofJX0v4M) (explains embeddings visually)
- [Attention in transformers, visually explained — 3Blue1Brown](https://www.youtube.com/watch?v=eMlx5fFNoYc) (optional, deeper)

**Step 2 — Embeddings and vector databases**
- [ChromaDB Crash Course — Intro to Vector Databases](https://www.youtube.com/watch?v=god8Pox1laE)
- [ChromaDB Explained: Vector Database, Embeddings, Chunking & Semantic Search](https://www.youtube.com/watch?v=_XwIi6jXg_8)

**Step 3 — RAG with LangChain (the core of this project)**
- [RAG From Scratch — official LangChain playlist](https://www.youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x) (short parts; watch 1–5 first)
- [Learn RAG From Scratch — freeCodeCamp (by a LangChain engineer)](https://www.youtube.com/watch?v=sVcwVQRHIc8) (the same material as one long video)
- [Complete RAG Crash Course With LangChain in 2 Hours](https://www.youtube.com/watch?v=o126p1QN_RI)

**Step 4 — FastAPI (backend)**
- [FastAPI Course for Beginners](https://www.youtube.com/watch?v=tLKKmouUams)
- [FastAPI Full Series | Beginner to Advanced (playlist)](https://www.youtube.com/playlist?list=PLll2u-uqtmZMHmxpC46i_7-dWjtZWAoQt)

**Step 5 — React (frontend)**
- [React Tutorial Full Course — Beginner to Pro (React 19)](https://www.youtube.com/watch?v=TtPXvEcE11E)
- [React JS v19 Full Course (playlist)](https://www.youtube.com/playlist?list=PL5dkTTGqCuTM4ZESWF3aTUmG0GUmwSE98)

Tip: after each step, open the matching file in this project (`vectorstore.py` after Step 2, `rag.py` after Step 3, `main.py` after Step 4, `App.jsx` after Step 5) and read it. It will make sense.
