from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AZ RAG Backend"

    upload_dir: str = "/app/RAG_Assistant/backend/app/data/uploads"
    seed_dir: str = "/app/RAG_Assistant/backend/app/data/seed_docs"
    history_file: str = "/app/RAG_Assistant/backend/app/data/chat_history.json"
    temp_image_dir: str = "/app/RAG_Assistant/backend/app/data/page_images"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "enterprise_multiformat_docs_v11"

    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "qwen2.5:7b"
    ollama_vision_model: str = "llava:latest"
    ollama_embed_model: str = "nomic-embed-text:latest"

    chunk_size: int = 1000
    chunk_overlap: int = 120

    top_k: int = 5
    retrieval_candidates: int = 120
    embedding_workers: int = 1

    max_source_context_chars: int = 2600
    max_images_to_show: int = 5

    enable_ocr: bool = True
    enable_image_description: bool = True

    # PDF multimodal controls
    enable_pdf_page_ocr: bool = True
    enable_pdf_page_image_summary: bool = False
    enable_table_extraction: bool = True

    min_pdf_text_chars_before_ocr: int = 40
    pdf_render_dpi: int = 150
    max_pdf_pages_for_vision: int = 3

    # LLaVA image compression / payload safety
    llava_max_image_width: int = 1200
    llava_jpeg_quality: int = 70
    llava_max_request_image_bytes: int = 8_000_000

    embedding_timeout: int = 600
    llm_timeout: int = 600

    min_global_relevance_score: float = 18.0
    min_file_relevance_score: float = 8.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()