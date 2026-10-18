import re


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_paragraphs(text: str):
    text = normalize_whitespace(text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    if not paragraphs:
        compact = " ".join(text.split())
        return [compact] if compact else []

    cleaned = []
    for p in paragraphs:
        if len(p) < 60 and cleaned:
            cleaned[-1] = f"{cleaned[-1]}\n{p}"
        else:
            cleaned.append(p)

    return cleaned


def chunk_long_text(text: str, chunk_size: int, overlap: int):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start += max(1, chunk_size - overlap)

    return chunks


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 120):
    paragraphs = split_into_paragraphs(text)
    if not paragraphs:
        return []

    chunks = []
    current = ""

    for para in paragraphs:
        candidate = para if not current else f"{current}\n\n{para}"

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())

            if len(para) <= chunk_size:
                current = para
            else:
                long_chunks = chunk_long_text(para, chunk_size, overlap)
                chunks.extend(long_chunks)
                current = ""

    if current.strip():
        chunks.append(current.strip())

    return chunks