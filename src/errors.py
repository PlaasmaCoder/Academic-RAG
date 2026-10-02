"""Safe, user-facing errors for expected Academic-RAG failures."""


class AcademicRAGError(Exception):
    """Base class for errors that the app can explain to a user."""


class ConfigurationError(AcademicRAGError):
    """A required setting or API key is missing or invalid."""


class DocumentProcessingError(AcademicRAGError):
    """A document could not be read or did not contain extractable text."""


class GeminiServiceError(AcademicRAGError):
    """A Gemini request failed or the service could not be reached."""


class VectorStoreError(AcademicRAGError):
    """The local Chroma database operation failed."""


def gemini_error_message(error: Exception) -> str:
    """Translate common API failures into safe, actionable messages."""
    status = getattr(error, "code", None) or getattr(error, "status_code", None)
    normalized = str(status).upper()

    if normalized in {"400", "INVALID_ARGUMENT"}:
        return "Gemini rejected the request. Check that the document or question is valid."
    if normalized in {"401", "403", "UNAUTHENTICATED", "PERMISSION_DENIED"}:
        return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file or Streamlit Cloud app secrets."
    if normalized in {"429", "RESOURCE_EXHAUSTED"}:
        return "Gemini's free-tier quota or rate limit was reached. Wait and try again later."
    if normalized in {"500", "502", "503", "504", "INTERNAL", "UNAVAILABLE"}:
        return "Gemini is temporarily unavailable. Wait a little and retry."
    if isinstance(error, (TimeoutError, ConnectionError)):
        return "Could not connect to Gemini. Check your internet connection and retry."
    return "The Gemini request failed. Check your API settings and try again."
