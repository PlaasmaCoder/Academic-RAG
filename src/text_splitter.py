"""Split extracted PDF pages into overlapping chunks."""


def split_pages(pages, chunk_size=800, overlap=150):
    """Create text chunks while preserving source filename and page number."""
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if not isinstance(overlap, int) or overlap < 0:
        raise ValueError("overlap must be a non-negative integer.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    chunks = []
    step = chunk_size - overlap

    for page in pages:
        if not isinstance(page, dict) or not {"text", "source", "page"}.issubset(page):
            raise ValueError("Each page must include text, source, and page fields.")
        text = page["text"]
        if not isinstance(text, str):
            raise ValueError("Page text must be a string.")

        for start in range(0, len(text), step):
            chunk_text = text[start : start + chunk_size].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "source": str(page["source"]),
                    "page": int(page["page"]),
                })

    return chunks
