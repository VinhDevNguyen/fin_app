from __future__ import annotations
import logging
from io import BytesIO
from pdfminer.high_level import extract_text
from services.pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)

class ExtractionError(Exception):
    """Custom domain error for PDF extraction failures."""
    pass

class PDFMinerExtractor(PDFExtractor):
    """Pure Python PDF text extraction using pdfminer.six."""
    
    def extract(self, pdf_bytes: bytes) -> str:
        """Extract plain text from PDF bytes using pdfminer."""
        try:
            return extract_text(BytesIO(pdf_bytes))
        except Exception as exc:
            logger.exception("PDF extraction failed with pdfminer")
            raise ExtractionError("Failed to extract text from PDF") from exc