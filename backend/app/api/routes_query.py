import os
import json
import logging
import traceback
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.schemas import QueryRequest
from app.services.llm_service import answer_question

router = APIRouter()
logger = logging.getLogger("routes_query")


def load_history():
    if not os.path.exists(settings.history_file):
        return []

    try:
        with open(settings.history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history):
    os.makedirs(os.path.dirname(settings.history_file), exist_ok=True)

    with open(settings.history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


@router.post("/query/")
async def query(payload: QueryRequest):
    logger.info(f"Query received: {payload.question}, file_name={payload.file_name}")

    try:
        result = answer_question(payload.question, file_name=payload.file_name)
        logger.info("Query completed successfully")

        history = load_history()
        history.append({
            "question": payload.question,
            "file_name": payload.file_name,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "retrieved_docs": result.get("retrieved_docs", []),
            "image_paths": result.get("image_paths", []),
        })
        save_history(history)

        return result

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))