import os
import logging
import traceback
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.ingestion_service import ingest_single_file

router = APIRouter()
logger = logging.getLogger("routes_ingest")


def supported_file(path: str) -> bool:
    allowed = {".txt", ".pdf", ".docx", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    return os.path.splitext(path)[1].lower() in allowed


@router.post("/ingest/file/{file_name}")
async def ingest_file(file_name: str):
    try:
        file_path = os.path.join(settings.upload_dir, file_name)
        logger.info(f"Requested ingestion for file: {file_path}")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_name}")

        count = ingest_single_file(file_path)

        logger.info(f"Ingestion complete for {file_name}. Points upserted: {count}")

        return {
            "message": f"Ingested file: {file_name}",
            "points_upserted": count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest file failed for {file_name}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/uploads")
async def ingest_all_uploads():
    try:
        if not os.path.exists(settings.upload_dir):
            return {"message": "Upload directory does not exist", "files": []}

        results = []

        for name in os.listdir(settings.upload_dir):
            path = os.path.join(settings.upload_dir, name)

            if not os.path.isfile(path):
                continue
            if not supported_file(path):
                continue

            logger.info(f"Starting ingestion for uploaded file: {name}")
            count = ingest_single_file(path)
            logger.info(f"Finished ingestion for uploaded file: {name}, points: {count}")

            results.append({
                "file_name": name,
                "points_upserted": count
            })

        return {
            "message": "All uploaded files ingested",
            "files": results
        }

    except Exception as e:
        logger.error(f"Ingest uploads failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/seed")
async def ingest_seed_docs():
    try:
        if not os.path.exists(settings.seed_dir):
            return {"message": "Seed directory does not exist", "files": []}

        results = []

        for name in os.listdir(settings.seed_dir):
            path = os.path.join(settings.seed_dir, name)

            if not os.path.isfile(path):
                continue
            if not supported_file(path):
                continue

            logger.info(f"Starting ingestion for seed file: {name}")
            count = ingest_single_file(path)
            logger.info(f"Finished ingestion for seed file: {name}, points: {count}")

            results.append({
                "file_name": name,
                "points_upserted": count
            })

        return {
            "message": "All seed docs ingested",
            "files": results
        }

    except Exception as e:
        logger.error(f"Ingest seed failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))