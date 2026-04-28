"""
ChromaDB vector store with local HuggingFace embeddings.

No OpenAI key needed for embeddings — uses sentence-transformers locally.
The store is persisted to disk so it survives restarts.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import config
from knowledge_base.loader import KNOWLEDGE_DOCUMENTS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_vectorstore():
    """
    Build (or reload) the ChromaDB vector store.
    Cached: successive calls return the same instance.
    """
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    persist_dir = config.CHROMA_PERSIST_DIR
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    logger.info("Loading embedding model: %s", config.EMBEDDING_MODEL)
    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # If the store already has documents, reuse it
    chroma = Chroma(
        collection_name="workshop_knowledge",
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )

    existing = chroma.get()
    if not existing["ids"]:
        logger.info("Populating knowledge base with %d documents…", len(KNOWLEDGE_DOCUMENTS))
        chroma.add_documents(KNOWLEDGE_DOCUMENTS)
    else:
        logger.info("Reusing existing knowledge base (%d chunks).", len(existing["ids"]))

    return chroma


def similarity_search(query: str, k: int = 3) -> list[dict]:
    """
    Return the top-k most relevant document chunks for *query*.
    Each result: {"content": str, "source": str, "category": str, "score": float}
    """
    store = get_vectorstore()
    results = store.similarity_search_with_relevance_scores(query, k=k)
    return [
        {
            "content": doc.page_content.strip(),
            "source": doc.metadata.get("source", "unknown"),
            "category": doc.metadata.get("category", "general"),
            "score": round(float(score), 3),
        }
        for doc, score in results
    ]
