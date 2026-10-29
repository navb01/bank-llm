"""
RAG Engine for Bank LLM System (Optimized for Low Latency)
"""

import time
import logging
from typing import Optional
from langchain_ollama import OllamaLLM

from document_processor import get_collection, get_embeddings
from config import (
    LLM_MODEL,
    OLLAMA_BASE_URL,
    CHROMA_COLLECTION_INTERNAL,
    TOP_K_RESULTS,
    MIN_SIMILARITY_SCORE,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

# ─── LLM Singleton Setup ──────────────────────────────────────────────────────
_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = OllamaLLM(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            top_p=0.9,
            repeat_penalty=1.1,
            num_ctx=4096,       # Keeps memory footprint tight and fast on CPU
            num_predict=512,    # Cap answer length so it doesn't spin for minutes
            keep_alive=-1,      # CRITICAL: Prevents Ollama from unloading model from RAM
        )
    return _llm_instance


# ─── Retrieval ────────────────────────────────────────────────────────────────

def retrieve_context(query: str, collection_names: list = None) -> list[dict]:
    t0 = time.time()
    if collection_names is None:
        collection_names = [CHROMA_COLLECTION_INTERNAL, "regulatory_docs"]

    embedder = get_embeddings()
    query_embedding = embedder.embed_query(query)
    logger.info(f"  [Timing] Query embedding took: {time.time() - t0:.2f}s")

    all_results = []
    t_db = time.time()

    for col_name in collection_names:
        try:
            collection = get_collection(col_name)
            if collection.count() == 0:
                continue

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(TOP_K_RESULTS, collection.count()),
                include=["documents", "metadatas", "distances"]
            )

            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                similarity = 1 - (distance / 2)

                if similarity >= MIN_SIMILARITY_SCORE:
                    meta = results["metadatas"][0][i]
                    all_results.append({
                        "text": doc,
                        "similarity": similarity,
                        "filename": meta.get("filename", "Unknown"),
                        "ref_no": meta.get("ref_no", "N/A"),
                        "date": meta.get("date", "N/A"),
                        "authority": meta.get("authority", "N/A"),
                        "collection": col_name,
                    })
        except Exception as e:
            logger.warning(f"Error querying collection {col_name}: {e}")
            continue

    logger.info(f"  [Timing] Vector DB search took: {time.time() - t_db:.2f}s")

    all_results.sort(key=lambda x: x["similarity"], reverse=True)

    seen_texts = set()
    unique_results = []
    for r in all_results:
        text_key = r["text"][:100]
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_results.append(r)

    return unique_results[:TOP_K_RESULTS]


# ─── Context Formatter ────────────────────────────────────────────────────────

def format_context(retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return "No relevant documents found in the knowledge base."

    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        source_info = (
            f"[Doc {i} | File: {chunk['filename']} | "
            f"Ref: {chunk['ref_no']} | Date: {chunk['date']} | "
            f"Authority: {chunk['authority']}]"
        )
        context_parts.append(f"{source_info}\n{chunk['text']}")

    return "\n\n---\n\n".join(context_parts)


# ─── Answer Generation ────────────────────────────────────────────────────────

def generate_answer(query: str, context: str) -> str:
    t0 = time.time()
    llm = get_llm()
    prompt = SYSTEM_PROMPT.format(context=context) + f"\n\nUser Query: {query}\n\nAnswer:"

    try:
        response = llm.invoke(prompt)
        logger.info(f"  [Timing] LLM Generation took: {time.time() - t0:.2f}s")
        return response.strip()
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return f"Error generating response: {str(e)}. Please check if Ollama is running."


# ─── Main RAG Pipeline ────────────────────────────────────────────────────────

def ask(query: str) -> dict:
    logger.info(f"Query: {query}")
    total_start = time.time()

    retrieved = retrieve_context(query)
    if not retrieved:
        return {
            "answer": "I don't have information about this topic in the available circulars and documents.",
            "sources": [],
            "chunks_found": 0,
        }

    context = format_context(retrieved)
    answer = generate_answer(query, context)

    sources = []
    seen_files = set()
    for chunk in retrieved:
        fname = chunk["filename"]
        if fname not in seen_files:
            seen_files.add(fname)
            sources.append({
                "filename": fname,
                "ref_no": chunk["ref_no"],
                "date": chunk["date"],
                "authority": chunk["authority"],
                "relevance": round(chunk["similarity"] * 100, 1),
                "collection": chunk["collection"],
            })

    logger.info(f"  [Timing] Total ask() pipeline took: {time.time() - total_start:.2f}s")
    return {
        "answer": answer,
        "sources": sources,
        "chunks_found": len(retrieved),
    }
