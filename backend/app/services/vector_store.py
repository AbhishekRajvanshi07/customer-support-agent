"""
Vector store service.

Wraps a FAISS index built from enterprise documents so both the
CrewAI retrieval tool and the plain REST ingestion endpoint share
one source of truth. The index is persisted to disk so the app
doesn't have to re-embed every document on every restart.
"""
import logging
import os
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreService:
    """Singleton-style holder for the FAISS index and its embedding model."""

    def __init__(self) -> None:
        self._embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        self._store: FAISS | None = None
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def load_or_build(self) -> None:
        """Load a persisted index if present, otherwise build one from
        whatever is in the documents directory (may be empty at first
        boot — that's fine, documents can be uploaded later)."""
        index_path = Path(settings.faiss_index_dir)
        if (index_path / "index.faiss").exists():
            logger.info("Loading existing FAISS index from %s", index_path)
            self._store = FAISS.load_local(
                str(index_path), self._embeddings, allow_dangerous_deserialization=True
            )
            return

        docs_dir = Path(settings.documents_dir)
        docs_dir.mkdir(parents=True, exist_ok=True)
        documents = self._load_documents(docs_dir)
        if documents:
            self._build_index(documents)
        else:
            logger.warning("No seed documents found — vector store starts empty.")

    def _load_documents(self, docs_dir: Path) -> list[Document]:
        documents: list[Document] = []
        for path in docs_dir.glob("**/*"):
            if path.is_dir():
                continue
            try:
                if path.suffix.lower() == ".pdf":
                    documents.extend(PyPDFLoader(str(path)).load())
                elif path.suffix.lower() in {".txt", ".md"}:
                    documents.extend(TextLoader(str(path), encoding="utf-8").load())
            except Exception:  # noqa: BLE001 - one bad file shouldn't kill startup
                logger.exception("Failed to load document: %s", path)
        return documents

    def _build_index(self, documents: list[Document]) -> None:
        chunks = self._splitter.split_documents(documents)
        self._store = FAISS.from_documents(chunks, self._embeddings)
        self._persist()
        logger.info("Built FAISS index with %d chunks from %d documents", len(chunks), len(documents))

    def _persist(self) -> None:
        if self._store is None:
            return
        index_path = Path(settings.faiss_index_dir)
        index_path.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(index_path))

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    @property
    def is_ready(self) -> bool:
        return self._store is not None

    def document_count(self) -> int:
        if self._store is None:
            return 0
        return self._store.index.ntotal

    def add_document(self, filename: str, raw_text: str) -> int:
        """Chunk, embed, and index a single document's raw text.
        Returns the number of chunks indexed."""
        doc = Document(page_content=raw_text, metadata={"source": filename})
        chunks = self._splitter.split_documents([doc])
        if self._store is None:
            self._store = FAISS.from_documents(chunks, self._embeddings)
        else:
            self._store.add_documents(chunks)
        self._persist()
        return len(chunks)

    def similarity_search(self, query: str, k: int | None = None) -> list[tuple[Document, float]]:
        if self._store is None:
            return []
        k = k or settings.retriever_top_k
        # FAISS returns L2 distance; smaller is better. We convert to a
        # 0-1 "confidence-ish" score downstream in the agent service.
        return self._store.similarity_search_with_score(query, k=k)


vector_store_service = VectorStoreService()
