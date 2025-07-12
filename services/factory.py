from __future__ import annotations
from typing import Literal
from pydantic import BaseModel
from services.pdf_extractor import PDFExtractor
from infrastructure.pdf_extractor.pymupdf_extractor import PyMuPDFExtractor
from infrastructure.pdf_extractor.pdfminer_extractor import PDFMinerExtractor

class Settings(BaseModel):
    """Settings for PDF extraction engine selection."""
    pdf_engine: Literal["pymupdf", "pdfminer"] = "pymupdf"

def make_pdf_extractor(settings: Settings) -> PDFExtractor:
    """Factory function to create PDF extractor based on settings."""
    if settings.pdf_engine == "pymupdf":
        return PyMuPDFExtractor()
    if settings.pdf_engine == "pdfminer":
        return PDFMinerExtractor()
    raise ValueError(f"Unsupported pdf_engine={settings.pdf_engine}")