import os
import shutil
import logging
import traceback
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger("routes_upload")

ALLOWED_EXTENSIONS = {
    ".txt", ".pdf", ".docx", ".xlsx", ".pptx",
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"
}


def validate_extension(file_name: str):
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)

        validate_extension(file.filename)

        file_path = os.path.join(settings.upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "message": "File uploaded successfully",
            "file_name": file.filename,
            "path": file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/multiple/")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)

        uploaded = []
        failed = []

        for file in files:
            try:
                validate_extension(file.filename)

                file_path = os.path.join(settings.upload_dir, file.filename)

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                uploaded.append({
                    "file_name": file.filename,
                    "path": file_path,
                    "status": "uploaded"
                })

            except HTTPException as e:
                failed.append({
                    "file_name": file.filename,
                    "status": "failed",
                    "error": e.detail
                })
            except Exception as e:
                failed.append({
                    "file_name": file.filename,
                    "status": "failed",
                    "error": str(e)
                })

        return {
            "message": "Multiple file upload completed",
            "uploaded": uploaded,
            "failed": failed
        }

    except Exception as e:
        logger.error(f"Multi-upload failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))