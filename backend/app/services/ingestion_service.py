import os
import math
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.config import settings
from app.services.file_parser import parse_file
from app.services.embedding_service import get_embedding
from app.services.chunk_service import chunk_text
from app.services.qdrant_service import ensure_collection, upsert_points, delete_file_points, build_point

logger = logging.getLogger("ingestion_service")

SUPPORTED_EXTENSIONS = {
    ".txt", ".pdf", ".docx", ".xlsx", ".pptx",
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"
}

MAX_EMBED_CHARS = 12000


def sanitize_metadata_value(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and math.isnan(value):
            return ""
        return value
    return str(value)


def sanitize_metadata(metadata):
    return {k: sanitize_metadata_value(v) for k, v in metadata.items()}


def infer_source_modality(entry):
    entry_type = entry.get("type", "")
    if entry_type in {"pdf_ocr"}:
        return "ocr"
    if entry_type in {"pdf_visual_summary"}:
        return "vision_summary"
    if entry_type in {"pdf_page_summary"}:
        return "hybrid_page_summary"
    if entry_type in {"pdf_table", "docx_table", "xlsx_sheet", "pdf_medicine_block"}:
        return "table_parse"
    if entry_type in {"image_content"}:
        return "image_ocr_vision"
    return "native_text"


def embed_chunk_task(task):
    index, chunk = task
    embedding = get_embedding(chunk)
    return index, embedding


def enforce_chunk_limit(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    if len(text) <= MAX_EMBED_CHARS:
        return [text]

    return chunk_text(text, chunk_size=4000, overlap=300)


def ingest_single_file(file_path: str):
    logger.info(f"Starting ingestion for file: {file_path}")

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    parsed_entries = parse_file(file_path)
    logger.info(f"Parsed entries count for {filename}: {len(parsed_entries)}")

    prepared_records = []

    for entry_idx, entry in enumerate(parsed_entries):
        entry_text = (entry.get("text") or "").strip()
        if not entry_text:
            continue

        content_type = entry.get("content_type", "text")
        source_modality = infer_source_modality(entry)

        if content_type in {"table", "page_summary", "chart_or_visual", "summary"}:
            chunks = chunk_text(
                entry_text,
                chunk_size=max(settings.chunk_size, 1400),
                overlap=settings.chunk_overlap
            )
        else:
            chunks = chunk_text(
                entry_text,
                settings.chunk_size,
                settings.chunk_overlap
            )

        safe_chunks = []
        for chunk in chunks:
            safe_chunks.extend(enforce_chunk_limit(chunk))

        logger.info(
            f"Entry {entry_idx} generated {len(safe_chunks)} safe chunks "
            f"(type={entry.get('type')}, page={entry.get('page_number')}, medicine={entry.get('medicine_name', '')})"
        )

        for chunk_index, chunk in enumerate(safe_chunks):
            raw_metadata = {
                "source_file": filename,
                "file_type": ext,
                "entry_type": entry.get("type", "unknown"),
                "content_type": content_type,
                "source_modality": source_modality,
                "chunk_index": chunk_index,
                "entry_index": entry_idx,
                "page_number": entry.get("page_number"),
                "sheet_name": entry.get("sheet_name"),
                "slide_number": entry.get("slide_number"),
                "table_number": entry.get("table_number"),
                "table_title": entry.get("table_title", ""),
                "table_titles": "|".join(entry.get("table_titles", [])) if entry.get("table_titles") else "",
                "section_headings": "|".join(entry.get("section_headings", [])) if entry.get("section_headings") else "",
                "medicine_name": entry.get("medicine_name", ""),
                "image_paths": "|".join(entry.get("image_paths", [])) if entry.get("image_paths") else "",
                "ocr_text": entry.get("ocr_text", ""),
                "image_description": entry.get("image_description", ""),
                "document_page_key": f"{filename}#page_{entry.get('page_number')}" if entry.get("page_number") else "",
                "contains_numbers": any(ch.isdigit() for ch in chunk),
                "contains_chart_terms": any(
                    term in chunk.lower()
                    for term in ["chart", "graph", "bar", "line", "axis", "trend", "plot", "table", "%", "increase", "decrease"]
                )
            }

            prepared_records.append({
                "id": str(uuid.uuid4()),
                "chunk": chunk,
                "metadata": sanitize_metadata(raw_metadata)
            })

    logger.info(f"Prepared records count for {filename}: {len(prepared_records)}")

    if not prepared_records:
        logger.warning(f"No prepared records for file: {filename}")
        return 0

    embeddings_result = [None] * len(prepared_records)
    tasks = [(i, record["chunk"]) for i, record in enumerate(prepared_records)]

    with ThreadPoolExecutor(max_workers=settings.embedding_workers) as executor:
        future_to_index = {
            executor.submit(embed_chunk_task, task): task[0]
            for task in tasks
        }

        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            result_index, embedding = future.result()
            embeddings_result[result_index] = embedding

    first_embedding = next((e for e in embeddings_result if e is not None), None)
    if first_embedding is None:
        raise ValueError("No embeddings were generated for any chunk")

    ensure_collection(len(first_embedding))
    delete_file_points(filename)

    points = []
    for i, record in enumerate(prepared_records):
        if embeddings_result[i] is None:
            continue

        payload = dict(record["metadata"])
        payload["text"] = record["chunk"]

        points.append(
            build_point(
                point_id=record["id"],
                vector=embeddings_result[i],
                payload=payload
            )
        )

    upsert_points(points)
    logger.info(f"Upserted {len(points)} points into Qdrant for file {filename}")

    return len(points)