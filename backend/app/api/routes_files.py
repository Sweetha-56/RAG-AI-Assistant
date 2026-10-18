import os
import logging
import traceback
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.qdrant_service import get_file_points, delete_file_points

router = APIRouter()
logger = logging.getLogger("routes_files")


@router.get("/files/")
async def list_files():
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)

        files = []
        for name in os.listdir(settings.upload_dir):
            full_path = os.path.join(settings.upload_dir, name)
            if os.path.isfile(full_path):
                ext = os.path.splitext(name)[1].lower()
                files.append({
                    "name": name,
                    "path": full_path,
                    "type": ext,
                    "size_bytes": os.path.getsize(full_path)
                })

        files.sort(key=lambda x: x["name"].lower())
        return files

    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_name}")
async def get_file_details(file_name: str):
    try:
        file_path = os.path.join(settings.upload_dir, file_name)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        points = get_file_points(file_name)

        pages = sorted(
            {
                p.payload.get("page_number")
                for p in points
                if getattr(p, "payload", None) and p.payload.get("page_number") not in [None, "", "-"]
            }
        )

        entry_types = sorted(
            {
                p.payload.get("entry_type", "unknown")
                for p in points
                if getattr(p, "payload", None)
            }
        )

        content_types = sorted(
            {
                p.payload.get("content_type", "unknown")
                for p in points
                if getattr(p, "payload", None)
            }
        )

        source_modalities = sorted(
            {
                p.payload.get("source_modality", "unknown")
                for p in points
                if getattr(p, "payload", None)
            }
        )

        preview_chunks = []
        for p in points[:12]:
            payload = p.payload or {}
            preview_chunks.append({
                "page_number": payload.get("page_number", "-"),
                "entry_type": payload.get("entry_type", "unknown"),
                "content_type": payload.get("content_type", "unknown"),
                "source_modality": payload.get("source_modality", "unknown"),
                "sheet_name": payload.get("sheet_name", "-"),
                "text_preview": (payload.get("text", "") or "")[:350]
            })

        return {
            "name": file_name,
            "path": file_path,
            "type": os.path.splitext(file_name)[1].lower(),
            "size_bytes": os.path.getsize(file_path),
            "chunk_count": len(points),
            "pages": pages,
            "entry_types": entry_types,
            "content_types": content_types,
            "source_modalities": source_modalities,
            "preview_chunks": preview_chunks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file details for {file_name}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{file_name}")
async def delete_file(file_name: str):
    try:
        file_path = os.path.join(settings.upload_dir, file_name)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        try:
            os.remove(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

        try:
            delete_file_points(file_name)
        except Exception as e:
            logger.error(f"Failed deleting Qdrant points for {file_name}: {e}")

        return {"message": f"{file_name} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file {file_name}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/")
async def delete_all_files():
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)

        deleted_files = []

        for name in os.listdir(settings.upload_dir):
            full_path = os.path.join(settings.upload_dir, name)
            if not os.path.isfile(full_path):
                continue

            try:
                os.remove(full_path)
                deleted_files.append(name)
            except Exception as e:
                logger.warning(f"Failed to delete file {name}: {e}")

            try:
                delete_file_points(name)
            except Exception as e:
                logger.warning(f"Failed to delete Qdrant points for {name}: {e}")

        return {
            "message": "All uploaded files processed for deletion",
            "deleted_files": deleted_files
        }

    except Exception as e:
        logger.error(f"Failed to delete all files: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))