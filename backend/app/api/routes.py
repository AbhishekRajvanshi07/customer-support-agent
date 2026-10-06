import logging

from fastapi import APIRouter, HTTPException, UploadFile

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentIngestResponse,
    HealthResponse,
    SourceChunk,
)
from app.services.retrieval_tool import KnowledgeBaseRetrievalTool
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)
router = APIRouter()

_retrieval_tool = KnowledgeBaseRetrievalTool()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        vector_store_ready=vector_store_service.is_ready,
        documents_indexed=vector_store_service.document_count(),
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # Imported lazily so the app can boot (and /health can respond) even
    # if GOOGLE_API_KEY isn't set yet during local setup.
    from app.services.agent_service import support_crew

    if not vector_store_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base is empty. Upload at least one document via /documents first.",
        )

    try:
        result = support_crew.handle(request.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent crew failed to handle request")
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc

    raw_hits = vector_store_service.similarity_search(request.message)
    sources = [
        SourceChunk(
            source=doc.metadata.get("source", "unknown"),
            snippet=doc.page_content[:200].strip() + ("…" if len(doc.page_content) > 200 else ""),
            score=round(1.0 / (1.0 + max(distance, 0.0)), 3),
        )
        for doc, distance in raw_hits
    ]

    return ChatResponse(
        session_id=request.session_id,
        answer=result["answer"],
        sources=sources,
        escalate=result["escalate"],
        confidence=result["confidence"],
        latency_ms=result["latency_ms"],
    )


@router.post("/documents", response_model=DocumentIngestResponse)
async def upload_document(file: UploadFile) -> DocumentIngestResponse:
    allowed = (".txt", ".md", ".pdf")
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(status_code=400, detail=f"Only {allowed} files are supported")

    raw_bytes = await file.read()
    try:
        if file.filename.lower().endswith(".pdf"):
            chunks_indexed = _ingest_pdf_bytes(file.filename, raw_bytes)
        else:
            text = raw_bytes.decode("utf-8", errors="ignore")
            chunks_indexed = vector_store_service.add_document(file.filename, text)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to ingest %s", file.filename)
        return DocumentIngestResponse(filename=file.filename, chunks_indexed=0, status="failed")

    return DocumentIngestResponse(filename=file.filename, chunks_indexed=chunks_indexed, status="indexed")


def _ingest_pdf_bytes(filename: str, raw_bytes: bytes) -> int:
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return vector_store_service.add_document(filename, text)
