from __future__ import annotations
import logging
import fitz  # PyMuPDF
from services.pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)

class ExtractionError(Exception):
    """Custom domain error for PDF extraction failures."""
    pass

class PyMuPDFExtractor(PDFExtractor):
    """Fast PDF text extraction using PyMuPDF (fitz)."""
    
    def __init__(self, *, joiner: str = "\n"):
        self.joiner = joiner

    def extract(self, pdf_bytes: bytes) -> str:
        """Extract plain text from PDF bytes using PyMuPDF."""
        try:
            text_parts: list[str] = []
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    text_parts.append(page.get_text("text"))
            return self.joiner.join(text_parts)
        except Exception as exc:
            logger.exception("PDF extraction failed with PyMuPDF")
            raise ExtractionError("Failed to extract text from PDF") from exc