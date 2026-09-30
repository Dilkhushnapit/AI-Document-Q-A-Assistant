# Retrieval-Augmented Generation (RAG) - Short Notes

Large language models (LLMs) only know what was in their training data, and they can confidently invent facts, which is called hallucination. Retrieval-Augmented Generation reduces this by looking up relevant text from a trusted knowledge base at question time and giving it to the model as context.

A RAG system has two phases. In the indexing phase, documents are loaded, split into overlapping chunks, converted to embedding vectors, and stored in a vector database. In the query phase, the user's question is embedded with the same model, the vector database returns the most similar chunks (for example using cosine similarity), and those chunks are inserted into the prompt so the LLM answers from them.

Chunk size is a trade-off: small chunks give precise retrieval but may lose context, while large chunks keep context but add noise and cost more tokens. Overlap between chunks prevents an important sentence from being cut in half at a boundary.

Common improvements include hybrid search (combining keyword BM25 search with vector search), re-ranking retrieved chunks with a cross-encoder, query rewriting, and evaluating the system with metrics such as faithfulness and answer relevance.
