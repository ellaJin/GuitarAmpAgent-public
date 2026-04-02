# app/service/processors/pdf_processor.py
import fitz
from typing import Optional, List
from langchain_core.documents import Document
from .base import BaseProcessor
from app.service.doc_processing.profiles import ChunkProfile


class PDFProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()

    def extract_text(self, file_path: str) -> str:
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)

    def extract_pages(self, file_path: str) -> List[dict]:
        """Extract text per page with page number."""
        pages = []
        with fitz.open(file_path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text().strip()
                if text:
                    pages.append({"page": i + 1, "text": text})
        return pages

    def process_to_chunks(self, file_path: str, profile: Optional[ChunkProfile] = None):
        """Split per page, preserve page number in metadata."""
        pages = self.extract_pages(file_path)
        splitter = self._build_splitter(profile)

        all_chunks = []
        for p in pages:
            docs = splitter.create_documents([p["text"]])
            for doc in docs:
                doc.metadata["page"] = p["page"]
                all_chunks.append(doc)

        return all_chunks