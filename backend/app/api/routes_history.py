import os
import json
import logging
import traceback
from fastapi import APIRouter, HTTPException

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger("routes_history")


def load_history():
    if not os.path.exists(settings.history_file):
        return []

    try:
        with open(settings.history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Failed to load history: {e}")
        return []


def save_history(history):
    try:
        os.makedirs(os.path.dirname(settings.history_file), exist_ok=True)
        with open(settings.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")
        raise


@router.get("/history/")
async def get_history():
    try:
        return load_history()
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/")
async def clear_history():
    try:
        save_history([])
        return {"message": "History cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{index}")
async def delete_history_item(index: int):
    try:
        history = load_history()

        if index < 0 or index >= len(history):
            raise HTTPException(status_code=404, detail="History item not found")

        deleted_item = history.pop(index)
        save_history(history)

        return {
            "message": "History item deleted successfully",
            "deleted_item": deleted_item
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete history item at index {index}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))