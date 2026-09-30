"""Query pipeline: retrieve relevant chunks -> build a grounded prompt -> ask the LLM.

This is the "online" half of RAG. It runs on every question.
"""
import json
from collections.abc import Iterator

import anthropic

from .config import LLM_MODEL, MAX_TOKENS, TOP_K
from .vectorstore import get_vectorstore

_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

SYSTEM_PROMPT = """You are a document Q&A assistant. Answer the user's question using ONLY the numbered context passages provided in their message.

Rules:
- Cite every factual claim with the passage number in square brackets, e.g. [1] or [2][4].
- If the passages do not contain the answer, say "I couldn't find that in the uploaded documents." and do not guess.
- Keep answers concise and use Markdown formatting where it helps readability."""


def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    """Semantic search: embed the question and return the k closest chunks."""
    results = get_vectorstore().similarity_search_with_score(question, k=k)
    sources = []
    for i, (doc, distance) in enumerate(results, start=1):
        sources.append({
            "id": i,
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page", -1),
            "text": doc.page_content,
            # Chroma returns cosine *distance*; 1 - distance = cosine similarity.
            "score": round(1 - distance, 3),
        })
    return sources


def build_user_message(question: str, sources: list[dict]) -> str:
    """Put the retrieved passages in the prompt, each tagged with a number to cite."""
    blocks = []
    for s in sources:
        where = s["source"] + (f", page {s['page']}" if s["page"] > 0 else "")
        blocks.append(f"[{s['id']}] ({where})\n{s['text']}")
    context = "\n\n---\n\n".join(blocks)
    return f"<context>\n{context}\n</context>\n\nQuestion: {question}"


def _event(obj: dict) -> str:
    """One newline-delimited JSON event for the streaming response."""
    return json.dumps(obj) + "\n"


def answer_stream(question: str, history: list[dict]) -> Iterator[str]:
    """Stream the answer as NDJSON events: sources first, then tokens, then done."""
    sources = retrieve(question)
    yield _event({"type": "sources", "sources": sources})

    if not sources:
        yield _event({"type": "token", "text": "No documents are indexed yet. Upload a file first."})
        yield _event({"type": "done"})
        return

    # Earlier turns are sent as plain text so follow-up questions ("what about
    # the second one?") make sense. Only the latest turn carries retrieved context.
    messages = [{"role": m["role"], "content": m["content"]} for m in history[-6:]]
    messages.append({"role": "user", "content": build_user_message(question, sources)})

    try:
        with _client.beta.messages.stream(
            model=LLM_MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
            output_config={"effort": "low"},  # Q&A over given context needs little deliberation
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # if the model declines, the API retries on a fallback model
        ) as stream:
            for text in stream.text_stream:
                yield _event({"type": "token", "text": text})
            final = stream.get_final_message()
        if final.stop_reason == "refusal":
            yield _event({"type": "error", "message": "The model declined to answer this question."})
    except anthropic.AuthenticationError:
        yield _event({"type": "error", "message": "Invalid or missing ANTHROPIC_API_KEY on the server."})
    except anthropic.RateLimitError:
        yield _event({"type": "error", "message": "Rate limited by the LLM API. Try again shortly."})
    except anthropic.APIStatusError as e:
        yield _event({"type": "error", "message": f"LLM API error ({e.status_code})."})
    except anthropic.APIConnectionError:
        yield _event({"type": "error", "message": "Could not reach the LLM API."})

    yield _event({"type": "done"})
