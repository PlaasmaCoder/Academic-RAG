"""Create cloud embeddings for document chunks and student questions."""

from src.errors import GeminiServiceError, gemini_error_message
from src.gemini_client import get_gemini_client

MODEL_NAME = "gemini-embedding-2"


def _embed(content: str) -> list[float]:
    if not content.strip():
        raise ValueError("Cannot create an embedding from empty text.")

    client = get_gemini_client()
    try:
        response = client.models.embed_content(model=MODEL_NAME, contents=content)
    except Exception as error:
        raise GeminiServiceError(gemini_error_message(error)) from error

    if not response.embeddings or not response.embeddings[0].values:
        raise GeminiServiceError("Gemini returned an empty embedding. Please retry.")
    return list(response.embeddings[0].values)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Create one embedding per document chunk, in the same order as input."""
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("Every chunk must contain non-empty text before embedding.")

    return [_embed(f"title: none | text: {text}") for text in texts]


def embed_query(question: str) -> list[float]:
    """Create an embedding for a student's retrieval question."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Enter a question before searching.")
    return _embed(f"task: question answering | query: {question.strip()}")
