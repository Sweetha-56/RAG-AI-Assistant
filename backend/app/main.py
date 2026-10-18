import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes_upload import router as upload_router
from app.api.routes_ingest import router as ingest_router
from app.api.routes_query import router as query_router
from app.api.routes_files import router as files_router
from app.api.routes_history import router as history_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("rag_backend")
logger.info("Starting backend application...")


def ensure_directories():
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.seed_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.history_file), exist_ok=True)

    if hasattr(settings, "temp_image_dir") and settings.temp_image_dir:
        os.makedirs(settings.temp_image_dir, exist_ok=True)


ensure_directories()

app = FastAPI(
    title=settings.app_name,
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": f"{settings.app_name} backend is running",
        "health_check": "/health",
        "docs": "/docs",
        "api_base": "/api"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(ingest_router, prefix="/api", tags=["Ingest"])
app.include_router(query_router, prefix="/api", tags=["Query"])
app.include_router(files_router, prefix="/api", tags=["Files"])
app.include_router(history_router, prefix="/api", tags=["History"])

logger.info("Routers registered successfully")
logger.info(f"Qdrant collection in use: {settings.qdrant_collection_name}")
logger.info(f"Upload dir: {settings.upload_dir}")
logger.info(f"Seed dir: {settings.seed_dir}")
logger.info(f"History file: {settings.history_file}")