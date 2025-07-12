from __future__ import annotations
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from infrastructure.pdf_extractor.pymupdf_extractor import PyMuPDFExtractor, ExtractionError
from infrastructure.pdf_extractor.pdfminer_extractor import PDFMinerExtractor
from services.factory import Settings, make_pdf_extractor

def load_sample_bytes(name: str) -> bytes:
    """Load test PDF files from fixtures directory."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return (fixtures_dir / name).read_bytes()

def test_pymupdf_extractor_with_sample():
    """Test PyMuPDF extractor with real PDF file."""
    pdf_bytes = load_sample_bytes("sample.pdf")
    extractor = PyMuPDFExtractor()
    text = extractor.extract(pdf_bytes)
    
    assert isinstance(text, str)
    assert len(text) > 0
    # Basic check for Vietnamese bank statement content
    assert any(keyword in text.lower() for keyword in ["bank", "statement", "account", "số dư", "giao dịch"])

def test_pdfminer_extractor_with_sample():
    """Test PDFMiner extractor with real PDF file."""
    pdf_bytes = load_sample_bytes("sample.pdf")
    extractor = PDFMinerExtractor()
    text = extractor.extract(pdf_bytes)
    
    assert isinstance(text, str)
    assert len(text) > 0

def test_factory_pymupdf():
    """Test factory creates PyMuPDF extractor by default."""
    settings = Settings()
    extractor = make_pdf_extractor(settings)
    assert isinstance(extractor, PyMuPDFExtractor)

def test_factory_pdfminer():
    """Test factory creates PDFMiner extractor when specified."""
    settings = Settings(pdf_engine="pdfminer")
    extractor = make_pdf_extractor(settings)
    assert isinstance(extractor, PDFMinerExtractor)

def test_factory_invalid_engine():
    """Test factory raises error for invalid engine."""
    settings = Settings(pdf_engine="invalid")
    with pytest.raises(ValueError, match="Unsupported pdf_engine"):
        make_pdf_extractor(settings)

def test_extraction_error_handling():
    """Test that extraction errors are properly wrapped."""
    extractor = PyMuPDFExtractor()
    # Pass invalid PDF bytes
    with pytest.raises(ExtractionError):
        extractor.extract(b"not a pdf")

class DummyExtractor:
    """Dummy extractor for testing pipeline without real PDF processing."""
    
    def extract(self, pdf_bytes: bytes) -> str:
        return "dummy text for testing"

def test_dummy_extractor():
    """Test dummy extractor for pipeline testing."""
    extractor = DummyExtractor()
    result = extractor.extract(b"any bytes")
    assert result == "dummy text for testing"