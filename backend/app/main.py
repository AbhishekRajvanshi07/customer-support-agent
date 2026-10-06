import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.services.vector_store import vector_store_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.api_title, version=settings.api_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Loading/building vector store...")
    vector_store_service.load_or_build()
    logger.info(
        "Startup complete. Vector store ready=%s, chunks=%d",
        vector_store_service.is_ready,
        vector_store_service.document_count(),
    )


@app.get("/")
def root() -> dict:
    return {"service": settings.api_title, "version": settings.api_version, "docs": "/docs"}
