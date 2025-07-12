from __future__ import annotations
from abc import ABC, abstractmethod

class PDFExtractor(ABC):
    """Contract để StatementPipeline không phụ thuộc lib cụ thể."""
    
    @abstractmethod
    def extract(self, pdf_bytes: bytes) -> str:
        """Extract text content from PDF bytes."""
        ...