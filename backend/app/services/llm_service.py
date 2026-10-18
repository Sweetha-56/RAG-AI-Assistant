import re
import logging
import traceback
import requests

from app.core.config import settings
from app.services.embedding_service import get_embedding
from app.services.qdrant_service import search_vectors

logger = logging.getLogger("llm_service")

NOT_FOUND_MESSAGE = "The information is not present in the provided documents."


def normalize_text(text):
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def tokenize(text):
    return set(re.findall(r"[a-zA-Z0-9$%._'-]+", normalize_text(text)))


def split_meta_pipe_field(value):
    if not value:
        return []
    return [v.strip().lower() for v in str(value).split("|") if v.strip()]


def keyword_overlap_score(question, doc):
    q = tokenize(question)
    d = tokenize(doc)
    if not q or not d:
        return 0
    return len(q.intersection(d))


def phrase_match_score(question, doc):
    q = normalize_text(question)
    d = normalize_text(doc)

    score = 0

    if q and q in d:
        score += 20

    for word in q.split():
        if len(word) >= 3 and word in d:
            score += 3

    return score


def detect_question_type(question: str) -> str:
    q = normalize_text(question)

    chart_terms = [
        "chart", "graph", "bar chart", "line chart", "plot", "trend",
        "axis", "axes", "visual", "curve", "distribution"
    ]
    image_terms = [
        "image", "picture", "diagram", "figure", "illustration", "photo"
    ]
    table_terms = [
        "table", "row", "column", "sheet", "excel", "spreadsheet",
        "revenue", "sales", "medicine", "product", "region", "section", "heading"
    ]
    numeric_terms = [
        "highest", "lowest", "average", "mean", "sum", "total", "count",
        "percentage", "percent", "value", "statistic", "max", "min",
        "how many", "number of", "revenue", "sales", "actual", "cer"
    ]

    if any(t in q for t in chart_terms):
        return "chart"
    if any(t in q for t in image_terms):
        return "image"
    if any(t in q for t in table_terms) and any(t in q for t in numeric_terms):
        return "table_numeric"
    if any(t in q for t in table_terms):
        return "table"
    if any(t in q for t in numeric_terms):
        return "numeric"
    return "text"


def subject_term_boost(question, doc):
    q = normalize_text(question)
    d = normalize_text(doc)
    score = 0

    subject_map = {
        "jvm": [
            "jvm", "class loader", "heap", "stack",
            "execution engine", "native method", "method area"
        ],
        "transformer": [
            "transformer", "self-attention", "multi-head attention",
            "positional encoding", "feed-forward", "embeddings", "encoder-decoder"
        ],
        "rag": [
            "rag", "retrieve", "retrieving", "augment",
            "generate", "context-aware", "retrieval", "response generation"
        ],
        "docker": [
            "docker", "container", "containers", "dockerfile", "docker daemon"
        ],
        "excel": [
            "sheet", "row", "column", "table", "total", "amount",
            "revenue", "sales", "employee", "department", "salary"
        ],
    }

    for subject, terms in subject_map.items():
        if subject in q:
            for term in terms:
                if term in d:
                    score += 8

    return score


def medicine_name_boost(question, doc):
    q = normalize_text(question)
    d = normalize_text(doc)

    medicine_names = [
        "tagrisso", "imfinzi", "calquence", "lynparza", "enhertu",
        "zoladex", "truqap", "imjudo", "datroway", "farxiga",
        "crestor", "brilinta", "seloken", "lokelma", "roxadustat",
        "wainua", "symbicort", "fasenra", "breztri", "tezspire",
        "beyfortus", "synagis", "flumist", "ultomiris", "soliris",
        "strensiq", "koselugo", "nexium", "saphnelo", "airsupra",
        "pulmicort", "wainzua", "beyonttra", "voydeya",
        "camizestrant", "eneboparatide", "orpathys"
    ]

    score = 0
    for med in medicine_names:
        if med in q and med in d:
            score += 35

    return score


def exact_row_pattern_boost(question, doc, meta):
    q = normalize_text(question)
    d = normalize_text(doc)
    score = 0

    region_terms = [
        "us", "europe", "emerging markets", "established row",
        "established row", "china", "emerging markets ex. china", "total"
    ]

    for region in region_terms:
        if region in q and region in d:
            score += 15

    medicine_name = normalize_text(meta.get("medicine_name", ""))
    if medicine_name and medicine_name in q:
        score += 25

    if "q1 2025" in q and "q1 2025" in d:
        score += 8

    if "h1 2025" in q and "h1 2025" in d:
        score += 8

    return score


def heading_match_boost(question, meta, doc):
    q = normalize_text(question)
    score = 0

    section_headings = split_meta_pipe_field(meta.get("section_headings", ""))
    table_titles = split_meta_pipe_field(meta.get("table_titles", ""))
    table_title = normalize_text(meta.get("table_title", ""))

    for heading in section_headings:
        if heading and heading in q:
            score += 25

    for title in table_titles:
        if title and title in q:
            score += 28

    if table_title and table_title in q:
        score += 30

    if "table " in q and (table_title or table_titles):
        score += 10

    return score


def excel_question_boost(question, doc, meta):
    q = normalize_text(question)
    d = normalize_text(doc)

    score = 0

    excel_terms = [
        "excel", "sheet", "row", "column", "table",
        "value", "record", "sales", "revenue", "employee",
        "department", "salary", "amount", "total", "sum"
    ]

    if any(term in q for term in excel_terms):
        if meta.get("entry_type") == "xlsx_sheet":
            score += 15

        if meta.get("sheet_name"):
            score += 5

        if "sheet name:" in d:
            score += 6

        if "columns:" in d:
            score += 6

        if "row " in d:
            score += 6

    return score


def question_type_boost(question, doc, meta):
    question_type = detect_question_type(question)
    score = 0

    entry_type = meta.get("entry_type", "")
    content_type = meta.get("content_type", "")
    source_modality = meta.get("source_modality", "")

    if question_type == "chart":
        if content_type in {"chart_or_visual", "page_summary", "image"}:
            score += 25
        if source_modality in {"vision_summary", "hybrid_page_summary", "image_ocr_vision"}:
            score += 18
        if meta.get("image_description"):
            score += 10
        if meta.get("contains_chart_terms"):
            score += 12
        if entry_type in {"pdf_visual_summary", "pdf_page_summary", "image_content"}:
            score += 8

    elif question_type == "image":
        if content_type in {"image", "chart_or_visual", "page_summary"}:
            score += 20
        if meta.get("image_description"):
            score += 12
        if meta.get("image_paths"):
            score += 8
        if source_modality in {"vision_summary", "hybrid_page_summary", "image_ocr_vision"}:
            score += 10

    elif question_type == "table":
        if content_type == "table":
            score += 25
        if entry_type in {"xlsx_sheet", "pdf_table", "docx_table", "pdf_medicine_block"}:
            score += 18

    elif question_type == "table_numeric":
        if content_type == "table":
            score += 30
        if meta.get("contains_numbers"):
            score += 14
        if entry_type in {"xlsx_sheet", "pdf_table", "docx_table", "pdf_medicine_block"}:
            score += 24

    elif question_type == "numeric":
        if meta.get("contains_numbers"):
            score += 14
        if content_type in {"table", "chart_or_visual", "page_summary", "summary"}:
            score += 12

    return score


def metadata_boost(meta, question, doc, file_name=None):
    score = 0
    entry_type = meta.get("entry_type", "")
    content_type = meta.get("content_type", "")
    question_lower = normalize_text(question)
    medicine_name = normalize_text(meta.get("medicine_name", ""))

    section_headings = split_meta_pipe_field(meta.get("section_headings", ""))
    table_titles = split_meta_pipe_field(meta.get("table_titles", ""))
    table_title = normalize_text(meta.get("table_title", ""))

    if content_type == "table":
        score += 8
    if content_type == "summary":
        score += 8
    if content_type == "page_summary":
        score += 6
    if content_type == "chart_or_visual":
        score += 8
    if meta.get("ocr_text"):
        score += 4
    if meta.get("image_description"):
        score += 6
    if entry_type == "xlsx_sheet":
        score += 10
    if entry_type == "pdf_medicine_block":
        score += 28
    if entry_type == "pdf_medicine_summary":
        score += 22

    if medicine_name and medicine_name in question_lower:
        score += 35

    for heading in section_headings:
        if heading and heading in question_lower:
            score += 18

    for title in table_titles:
        if title and title in question_lower:
            score += 20

    if table_title and table_title in question_lower:
        score += 22

    if meta.get("sheet_name") not in [None, "", "-"]:
        score += 5
    if meta.get("page_number") not in [None, "", "-"]:
        score += 2
    if meta.get("slide_number") not in [None, "", "-"]:
        score += 1

    if file_name and meta.get("source_file") == file_name:
        score += 20

    return score


def score_document(question, doc, meta, file_name=None):
    semantic = float(meta.get("_vector_score", 0)) * 100
    overlap = keyword_overlap_score(question, doc) * 8
    phrase = phrase_match_score(question, doc)
    subject = subject_term_boost(question, doc)
    med_score = medicine_name_boost(question, doc)
    row_score = exact_row_pattern_boost(question, doc, meta)
    heading_score = heading_match_boost(question, meta, doc)
    excel_score = excel_question_boost(question, doc, meta)
    qtype_score = question_type_boost(question, doc, meta)
    meta_score = metadata_boost(meta, question, doc, file_name=file_name)

    return (
        semantic
        + overlap
        + phrase
        + subject
        + med_score
        + row_score
        + heading_score
        + excel_score
        + qtype_score
        + meta_score
    )


def rerank_results(question, docs, metas, file_name=None):
    ranked = []

    for doc, meta in zip(docs, metas):
        if not doc or not str(doc).strip():
            continue

        score = score_document(question, doc, meta, file_name=file_name)
        ranked.append((score, doc, meta))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked


def extract_best_image_paths(ranked_results):
    scored_images = []

    for score, _, meta in ranked_results:
        raw = meta.get("image_paths", "")
        if raw:
            for path in [p for p in raw.split("|") if p.strip()]:
                scored_images.append((score, path))

    seen = set()
    unique_images = []

    for score, path in scored_images:
        if path not in seen:
            seen.add(path)
            unique_images.append((score, path))

    unique_images.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in unique_images[:settings.max_images_to_show]]


def required_term_presence(question, ranked_results):
    candidates = re.findall(r"[A-Za-z0-9&+/\-]{3,}", question)

    stop_terms = {
        "what", "was", "were", "the", "this", "that", "from", "with", "and",
        "for", "did", "does", "how", "much", "many", "show", "section", "table",
        "heading", "summarize", "compare", "q1", "h1", "2025", "revenue",
        "which", "who", "why", "when", "where", "only", "using", "answer",
        "according", "under", "within", "about", "tell", "give", "provide"
    }

    important_terms = []
    for term in candidates:
        t = term.lower()
        if t not in stop_terms:
            important_terms.append(t)

    if not important_terms:
        return True

    combined_docs = " ".join(normalize_text(doc) for _, doc, _ in ranked_results[:5])

    matched = sum(1 for term in important_terms if term in combined_docs)
    return matched >= max(1, min(2, len(important_terms)))


def build_prompt(question, ranked_results, file_name=None):
    best_results = ranked_results[:settings.top_k]
    context_parts = []

    for i, (score, doc, meta) in enumerate(best_results, start=1):
        context_parts.append(
            f"Context {i}\n"
            f"Source File: {meta.get('source_file', 'Unknown')}\n"
            f"Entry Type: {meta.get('entry_type', 'unknown')}\n"
            f"Content Type: {meta.get('content_type', 'unknown')}\n"
            f"Source Modality: {meta.get('source_modality', 'unknown')}\n"
            f"Medicine Name: {meta.get('medicine_name', '-')}\n"
            f"Section Headings: {meta.get('section_headings', '-')}\n"
            f"Table Title: {meta.get('table_title', '-')}\n"
            f"Table Titles: {meta.get('table_titles', '-')}\n"
            f"Page Number: {meta.get('page_number', '-')}\n"
            f"Slide Number: {meta.get('slide_number', '-')}\n"
            f"Sheet Name: {meta.get('sheet_name', '-')}\n"
            f"Relevance Score: {score}\n"
            f"Content:\n{str(doc)[:settings.max_source_context_chars]}"
        )

    context = "\n\n".join(context_parts)

    scope_line = (
        f"The user selected this file only: {file_name}"
        if file_name else
        "The user searched across all uploaded files. If any retrieved context contains the answer, answer from it."
    )

    qtype = detect_question_type(question)

    special_instruction = ""
    if qtype in {"numeric", "table_numeric"}:
        special_instruction = (
            "This is a numeric or statistical question. Prefer exact values from the retrieved context. "
            "If the question names a product, medicine, region, table, heading, or row, find that exact row or exact relevant chunk and return its exact value only. "
            "Do not mix values from nearby rows, nearby medicines, or nearby sections. "
            "If the answer is a Total row, return the Total row value. "
            "If exact values are not clearly visible, say the information is not present in the provided documents."
        )
    elif qtype == "chart":
        special_instruction = (
            "This is a chart or graph question. Use only retrieved chart summaries, OCR text, and page summaries. "
            "Do not infer unsupported values."
        )
    elif qtype == "table":
        special_instruction = (
            "This is a table or section-heading question. Use rows, columns, headers, section headings, and table titles carefully. "
            "If the question names a specific section, table, medicine, region, or row, focus only on chunks matching that heading or label."
        )
    elif qtype == "image":
        special_instruction = (
            "This is an image or figure question. Use image descriptions, OCR text, and page summaries only if relevant."
        )
    else:
        special_instruction = (
            "Answer using the most relevant retrieved context only."
        )

    return f"""
You are a strict document-grounded assistant.

Use ONLY the retrieved context below.

Instructions:
- Answer ONLY if the answer is explicitly supported by the retrieved context.
- Prefer the most relevant chunk or chunks only.
- If the question mentions a section heading, table heading, table number, medicine name, row, or region, focus only on chunks matching that heading or label.
- Do not drift into nearby sections.
- Do not use general document knowledge if the relevant heading or table is not present in the retrieved context.
- If the requested heading, table, medicine, or exact information is not present in the retrieved context, reply exactly:
{NOT_FOUND_MESSAGE}
- Do not invent facts.
- For numeric questions, return the exact value from the relevant row or relevant chunk only.
- If the retrieved context is related but does not contain the requested answer, reply exactly:
{NOT_FOUND_MESSAGE}
- When possible, mention the page number or table title.
- {special_instruction}

{scope_line}

Question:
{question}

Retrieved Context:
{context}

Answer:
"""


def ask_llm(prompt):
    logger.info(f"Calling Ollama LLM model: {settings.ollama_llm_model}")

    response = requests.post(
        f"{settings.ollama_base_url}/api/generate",
        json={
            "model": settings.ollama_llm_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=settings.llm_timeout
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def clean_answer(answer):
    if not answer:
        return NOT_FOUND_MESSAGE

    answer = answer.strip()
    answer = re.sub(r"\n{3,}", "\n\n", answer).strip()

    lower = normalize_text(answer)
    refusal_like = [
        "not enough information",
        "insufficient information",
        "cannot determine",
        "can't determine",
        "cannot be determined",
        "not explicitly stated",
        "not clearly stated"
    ]
    if any(p in lower for p in refusal_like):
        return NOT_FOUND_MESSAGE

    return answer if answer else NOT_FOUND_MESSAGE


def answer_question(question: str, file_name: str = None):
    logger.info(f"Answering question: {question}, file_name={file_name}")

    try:
        query_vector = get_embedding(question)

        results = search_vectors(
            query_vector=query_vector,
            limit=settings.retrieval_candidates,
            file_name=file_name
        )

        docs = []
        metas = []

        for r in results:
            payload = dict(r.payload or {})
            payload["_vector_score"] = getattr(r, "score", 0.0)

            text = payload.get("text", "")
            if not text or not str(text).strip():
                continue

            docs.append(text)
            metas.append(payload)

        if not docs:
            return {
                "answer": NOT_FOUND_MESSAGE,
                "sources": [],
                "retrieved_docs": [],
                "image_paths": []
            }

        ranked_results = rerank_results(question, docs, metas, file_name=file_name)

        if not ranked_results:
            return {
                "answer": NOT_FOUND_MESSAGE,
                "sources": [],
                "retrieved_docs": [],
                "image_paths": []
            }

        best_score = ranked_results[0][0]
        threshold = settings.min_file_relevance_score if file_name else settings.min_global_relevance_score

        if best_score < threshold:
            return {
                "answer": NOT_FOUND_MESSAGE,
                "sources": [meta for _, _, meta in ranked_results[:settings.top_k]],
                "retrieved_docs": [doc for _, doc, _ in ranked_results[:settings.top_k]],
                "image_paths": extract_best_image_paths(ranked_results)
            }

        if not required_term_presence(question, ranked_results):
            return {
                "answer": NOT_FOUND_MESSAGE,
                "sources": [meta for _, _, meta in ranked_results[:settings.top_k]],
                "retrieved_docs": [doc for _, doc, _ in ranked_results[:settings.top_k]],
                "image_paths": extract_best_image_paths(ranked_results)
            }

        prompt = build_prompt(question, ranked_results, file_name=file_name)
        raw_answer = ask_llm(prompt)
        answer = clean_answer(raw_answer)

        return {
            "answer": answer,
            "sources": [meta for _, _, meta in ranked_results[:settings.top_k]],
            "retrieved_docs": [doc for _, doc, _ in ranked_results[:settings.top_k]],
            "image_paths": extract_best_image_paths(ranked_results)
        }

    except Exception as e:
        logger.error(str(e))
        logger.error(traceback.format_exc())
        raise