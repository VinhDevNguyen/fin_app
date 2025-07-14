from __future__ import annotations
from abc import ABC, abstractmethod

class PDFExtractor(ABC):
    """Contract để StatementPipeline không phụ thuộc lib cụ thể."""
    
    @abstractmethod
    def extract(self, pdf_bytes: bytes, *, password: str | None = None) -> str:
        """Extract text content from PDF bytes.
        
        Args:
            pdf_bytes: PDF file content as bytes
            password: Optional password for encrypted PDFs
            
        Returns:
            Extracted text content
        """
        ...