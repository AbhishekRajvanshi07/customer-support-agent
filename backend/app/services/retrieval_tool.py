"""
A CrewAI-compatible tool that exposes the FAISS vector store to
the Knowledge Retriever agent. Keeping this separate from
vector_store.py keeps "storage" and "agent-facing interface"
concerns apart.
"""
import math

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.vector_store import vector_store_service


class RetrievalInput(BaseModel):
    query: str = Field(..., description="The customer's question, or a focused restatement of it")


class KnowledgeBaseRetrievalTool(BaseTool):
    name: str = "knowledge_base_search"
    description: str = (
        "Searches the enterprise knowledge base (product docs, policies, FAQs) "
        "for passages relevant to a customer support query. Returns the top "
        "matching passages with their source document and a relevance score."
    )
    args_schema: type[BaseModel] = RetrievalInput

    def _run(self, query: str) -> str:
        results = vector_store_service.similarity_search(query)
        if not results:
            return "NO_RESULTS: the knowledge base returned nothing relevant to this query."

        formatted = []
        for doc, distance in results:
            # L2 distance -> a rough 0..1 relevance score (closer to 1 is better).
            relevance = 1.0 / (1.0 + max(distance, 0.0))
            formatted.append(
                f"[source: {doc.metadata.get('source', 'unknown')} | "
                f"relevance: {relevance:.2f}]\n{doc.page_content.strip()}"
            )
        return "\n\n---\n\n".join(formatted)


def best_match_confidence(query: str) -> float:
    """Used by the API layer (outside the LLM call) to decide whether
    to flag a response for human escalation, independent of what the
    agent says about itself."""
    results = vector_store_service.similarity_search(query)
    if not results:
        return 0.0
    _, distance = results[0]
    return 1.0 / (1.0 + max(distance, 0.0))
