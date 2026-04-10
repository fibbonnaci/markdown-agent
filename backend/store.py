"""
In-memory vector store for document search.

Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings,
chunks documents into ~500 char segments, and searches by cosine similarity.
"""

import re
from typing import Dict, List, Optional

import numpy as np

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class VectorStore:
    def __init__(self):
        self._model = None
        self._chunks: List[dict] = []  # {"doc_name": str, "text": str, "embedding": np.ndarray}
        self._documents: Dict[str, int] = {}  # doc_name -> chunk_count

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def add_document(self, name: str, content: bytes, content_type: str) -> dict:
        """Add a document: extract text, chunk, embed, and store."""
        text = self._extract_text(content, content_type)
        chunks = self._chunk_text(text)

        if not chunks:
            return {"name": name, "chunks": 0}

        model = self._get_model()
        embeddings = model.encode(chunks, show_progress_bar=False)

        for chunk_text, embedding in zip(chunks, embeddings):
            self._chunks.append({
                "doc_name": name,
                "text": chunk_text,
                "embedding": np.array(embedding),
            })

        self._documents[name] = len(chunks)
        return {"name": name, "chunks": len(chunks)}

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        """Search for chunks most similar to the query."""
        if not self._chunks:
            return []

        model = self._get_model()
        query_embedding = model.encode([query], show_progress_bar=False)[0]

        scores = []
        for chunk in self._chunks:
            score = self._cosine_similarity(query_embedding, chunk["embedding"])
            scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scores[:top_k]:
            results.append({
                "doc_name": chunk["doc_name"],
                "text": chunk["text"],
                "score": float(score),
            })
        return results

    def list_documents(self) -> List[dict]:
        """List all uploaded documents."""
        return [{"name": name, "chunks": count} for name, count in self._documents.items()]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def _extract_text(content: bytes, content_type: str) -> str:
        if content_type == "application/pdf":
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        else:
            return content.decode("utf-8", errors="replace")

    @staticmethod
    def _chunk_text(text: str) -> List[str]:
        """Split text into ~CHUNK_SIZE char chunks with CHUNK_OVERLAP overlap."""
        text = text.strip()
        if not text:
            return []

        # Split on paragraph boundaries first
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current) + len(para) + 1 <= CHUNK_SIZE:
                current = (current + "\n\n" + para).strip()
            else:
                if current:
                    chunks.append(current)
                # If paragraph itself is too long, split it
                if len(para) > CHUNK_SIZE:
                    words = para.split()
                    current = ""
                    for word in words:
                        if len(current) + len(word) + 1 <= CHUNK_SIZE:
                            current = (current + " " + word).strip()
                        else:
                            if current:
                                chunks.append(current)
                            current = word
                else:
                    current = para

        if current:
            chunks.append(current)

        # Add overlap between chunks
        if len(chunks) <= 1:
            return chunks

        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-CHUNK_OVERLAP:]
            overlapped.append(prev_tail + " " + chunks[i])
        return overlapped


# Module-level singleton
_store = VectorStore()


def add_document(name: str, content: bytes, content_type: str) -> dict:
    return _store.add_document(name, content, content_type)


def search(query: str, top_k: int = 3) -> List[dict]:
    return _store.search(query, top_k)


def list_documents() -> List[dict]:
    return _store.list_documents()


def reset():
    """Reset the store (used on agent swap)."""
    global _store
    _store = VectorStore()


if __name__ == "__main__":
    result = add_document("test.txt", b"Python is a programming language.\n\nIt is widely used for web development, data science, and automation.\n\nPython was created by Guido van Rossum.", "text/plain")
    print(f"Added: {result}")
    print(f"Documents: {list_documents()}")
    results = search("who created python")
    for r in results:
        print(f"  [{r['doc_name']}] score={r['score']:.3f}: {r['text'][:80]}...")
