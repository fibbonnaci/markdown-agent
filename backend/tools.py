"""
Agent tools — the developer-facing file.

Add a @tool decorator to any function to make it available as an agent capability.
The decorator automatically generates a Claude-compatible tool schema from the
function signature and docstring. No additional configuration needed.
"""

from backend.decorator import tool
from backend import store


@tool
def search_docs(query: str, top_k: int = 3):
    """Search uploaded documents for relevant passages.

    Args:
        query: The search query string.
        top_k: Number of top results to return.
    """
    results = store.search(query, top_k)
    if not results:
        return "No relevant documents found. The user may need to upload documents first."
    formatted = []
    for r in results:
        formatted.append(f"[{r['doc_name']}] (score: {r['score']:.2f})\n{r['text']}")
    return "\n\n---\n\n".join(formatted)


@tool
def list_docs():
    """List all uploaded documents and their chunk counts."""
    docs = store.list_documents()
    if not docs:
        return "No documents uploaded yet."
    return "\n".join(f"- {d['name']} ({d['chunks']} chunks)" for d in docs)
