"""
Tool: query_knowledge_base
RAG retrieval from the ChromaDB knowledge base.
"""
from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool

from observability import observe


@tool
@observe(name="tool_query_knowledge_base")
def query_knowledge_base(
    query: Annotated[str, "Natural-language question about impact measurement, digital skills education, satisfaction frameworks, financial models, or feedback practices."],
    k: Annotated[int, "Number of document chunks to retrieve (default 3, max 5)."] = 3,
) -> str:
    """
    Search the knowledge base for best practices, frameworks, and methodologies
    relevant to impact measurement, digital skills workshops, satisfaction analysis,
    reputation management, feedback incorporation, and financial sustainability.

    Use this tool when you need conceptual grounding, interpretation thresholds,
    benchmark values, or methodological guidance.
    """
    from knowledge_base.store import similarity_search

    k = min(k, 5)
    results = similarity_search(query, k=k)

    if not results:
        return json.dumps({"message": "No relevant documents found for the query.", "query": query})

    return json.dumps({
        "query": query,
        "n_results": len(results),
        "results": [
            {
                "rank": idx + 1,
                "source": r["source"],
                "category": r["category"],
                "relevance_score": r["score"],
                "content": r["content"],
            }
            for idx, r in enumerate(results)
        ],
    }, indent=2)
