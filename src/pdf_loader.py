"""Read text from PDF files while preserving page-level source metadata."""

from pathlib import Path

from pypdf import PdfReader

from src.errors import DocumentProcessingError

MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 1000


def load_pdf(pdf_path: str | Path) -> list[dict[str, str | int]]:
    """Return page text, filename, and 1-based page number for a text PDF."""
    path = Path(pdf_path)
    if not path.is_file():
        raise DocumentProcessingError(f"PDF not found: {path.name}")

    if path.stat().st_size == 0:
        raise DocumentProcessingError(f"{path.name} is empty.")
    if path.stat().st_size > MAX_PDF_SIZE_BYTES:
        raise DocumentProcessingError(f"{path.name} is larger than the 25 MB limit.")

    try:
        with path.open("rb") as pdf_file:
            if pdf_file.read(5) != b"%PDF-":
                raise DocumentProcessingError(f"{path.name} is not a valid PDF file.")

        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")
            except Exception as error:
                raise DocumentProcessingError(
                    f"{path.name} is password-protected. Remove its password and upload it again."
                ) from error
            if not decrypted:
                raise DocumentProcessingError(
                    f"{path.name} is password-protected. Remove its password and upload it again."
                )

        if not reader.pages:
            raise DocumentProcessingError(f"{path.name} contains no pages.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise DocumentProcessingError(f"{path.name} has more than the 1000-page limit.")

        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as error:
                raise DocumentProcessingError(
                    f"Could not extract text from page {page_number} of {path.name}."
                ) from error
            pages.append({"text": text, "source": path.name, "page": page_number})

    except DocumentProcessingError:
        raise
    except Exception as error:
        raise DocumentProcessingError(
            f"Could not read {path.name}. The PDF may be damaged or use an unsupported format."
        ) from error

    if not any(page["text"].strip() for page in pages):
        raise DocumentProcessingError(
            f"No selectable text was found in {path.name}. It may be a scanned PDF; OCR is not enabled yet."
        )
    return pages
