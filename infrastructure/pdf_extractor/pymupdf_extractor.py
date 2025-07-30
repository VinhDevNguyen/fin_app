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

    def extract(self, pdf_bytes: bytes, *, password: str | None = None) -> str:
        """Extract plain text from PDF bytes using PyMuPDF.

        Args:
            pdf_bytes: PDF file content as bytes
            password: Optional password for encrypted PDFs

        Returns:
            Extracted text content
        """
        try:
            text_parts: list[str] = []
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                # Handle password-protected PDFs
                if doc.needs_pass:
                    if password is None:
                        raise ExtractionError(
                            "PDF is password-protected but no password provided"
                        )

                    auth_result = doc.authenticate(password)
                    if not auth_result:
                        raise ExtractionError("Invalid password for encrypted PDF")

                    logger.info("Successfully authenticated password-protected PDF")

                # Extract text from all pages
                for page in doc:
                    text_parts.append(page.get_text("text"))

            return self.joiner.join(text_parts)

        except ExtractionError:
            # Re-raise our custom errors
            raise
        except Exception as exc:
            logger.exception("PDF extraction failed with PyMuPDF")
            raise ExtractionError("Failed to extract text from PDF") from exc
