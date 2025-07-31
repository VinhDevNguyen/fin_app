from __future__ import annotations

import logging
from io import BytesIO

import fitz
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from services.pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Custom domain error for PDF extraction failures."""

    pass


class DoclingExtractor(PDFExtractor):
    """Docling text extraction using detection and OCR models"""

    def __init__(self):
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = True
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.table_structure_options.do_cell_matching = True
        self.pipeline_options.ocr_options = EasyOcrOptions(force_full_page_ocr=False)

    def extract(self, pdf_bytes: bytes, *, password: str | None = None) -> str:
        """Extract plain text from PDF bytes using Docling.

        Args:
            pdf_bytes: PDF file content as bytes
            password: Optional password for encrypted PDFs

        Returns:
            Extracted text content
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.needs_pass:
                if not doc.authenticate(password):
                    raise ValueError("Wrong password or insufficient privileges")

            # Heuristic check if PDF is scanned
            is_scanned = False
            text_threshold = 50
            full_text = "".join(page.get_text() for page in doc).strip()
            is_scanned = len(full_text) < text_threshold

            logger.info(f"PDF is {'scanned' if is_scanned else 'not scanned'}")

            # Force OCR is scanned
            if is_scanned:
                self.pipeline_options.ocr_options = EasyOcrOptions(
                    force_full_page_ocr=True
                )
            else:
                self.pipeline_options.ocr_options = EasyOcrOptions(
                    force_full_page_ocr=False
                )

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=self.pipeline_options,
                    )
                }
            )

            decrypted = doc.tobytes(encryption=fitz.PDF_ENCRYPT_NONE)
            buf = BytesIO(decrypted)
            stream = DocumentStream(name="file.pdf", stream=buf)
            result = converter.convert(stream).document
            text = result.export_to_markdown()

            return text

        except Exception as exc:
            logger.exception("PDF extraction failed with Docling")
            raise ExtractionError("Failed to extract text from PDF") from exc
