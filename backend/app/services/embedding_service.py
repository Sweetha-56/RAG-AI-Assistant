import logging
import requests

from app.core.config import settings

logger = logging.getLogger("embedding_service")


def get_embedding(text: str):
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Cannot create embedding for empty text")

    logger.info(f"Requesting embedding from Ollama model: {settings.ollama_embed_model}")

    response = requests.post(
        f"{settings.ollama_base_url}/api/embeddings",
        json={
            "model": settings.ollama_embed_model,
            "prompt": cleaned
        },
        timeout=settings.embedding_timeout
    )
    response.raise_for_status()
    data = response.json()

    if "embedding" not in data:
        raise ValueError(f"Embedding response missing 'embedding': {data}")

    embedding = data["embedding"]
    if not embedding:
        raise ValueError("Received empty embedding from Ollama")

    return embedding