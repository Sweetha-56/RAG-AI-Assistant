
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.core.config import settings

logger = logging.getLogger("qdrant_service")

client = QdrantClient(
    url=settings.qdrant_url,
    check_compatibility=False,
    timeout=30,
)


def ensure_collection(vector_size: int):
    """Create the collection if missing; validate its vector size."""
    if vector_size <= 0:
        raise ValueError(f"Invalid embedding vector size: {vector_size}")

    existing = {
        c.name: c
        for c in client.get_collections().collections
    }

    name = settings.qdrant_collection_name

    if name not in existing:
        logger.info(
            "Creating Qdrant collection %s with vector size %s",
            name, vector_size
        )
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Qdrant collection created successfully: %s", name)
        return

    info = client.get_collection(name)
    vectors = info.config.params.vectors

    if not isinstance(vectors, dict):
        actual_size = getattr(vectors, "size", None)
        if actual_size != vector_size:
            raise ValueError(
                f"Collection {name} uses vector size {actual_size}, "
                f"but the embedding model returns {vector_size}. "
                "Do not delete the collection automatically."
            )
    else:
        # Named-vector collections require explicit configuration.
        raise ValueError(
            f"Collection {name} uses named vectors. "
            "Check its vector configuration before proceeding."
        )

    logger.info("Qdrant collection is ready: %s", name)


def upsert_points(points):
    if not points:
        return

    logger.info("Upserting %s points into Qdrant", len(points))
    client.upsert(
        collection_name=settings.qdrant_collection_name,
        points=points,
    )


def _file_filter(file_name: str):
    return Filter(
        must=[
            FieldCondition(
                key="source_file",
                match=MatchValue(value=file_name),
            )
        ]
    )


def search_vectors(query_vector, limit: int, file_name: str = None):
    logger.info(
        "Searching Qdrant: limit=%s, file_name=%s",
        limit, file_name
    )

    result = client.query_points(
        collection_name=settings.qdrant_collection_name,
        query=query_vector,
        limit=limit,
        query_filter=_file_filter(file_name) if file_name else None,
        with_payload=True,
    )
    return result.points


def delete_file_points(file_name: str):
    logger.info("Deleting existing points for file=%s", file_name)
    client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=_file_filter(file_name),
        wait=True,
    )


def get_file_points(file_name: str, limit: int = 1000):
    result = client.scroll(
        collection_name=settings.qdrant_collection_name,
        scroll_filter=_file_filter(file_name),
        with_payload=True,
        limit=limit,
    )
    return result[0] or []


def build_point(point_id, vector, payload):
    return PointStruct(
        id=point_id,
        vector=vector,
        payload=payload,
    )
