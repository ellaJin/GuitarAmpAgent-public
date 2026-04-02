# app/service/doc_factory.py
import os
from typing import Optional

from app.service.doc_processing.profiles import ChunkProfile
from .processors.pdf_processor import PDFProcessor
from .processors.txt_processor import TextProcessor


class DocProcessorFactory:
    """
    Industrial-safe factory:
    - Do NOT keep processor singletons (avoid shared mutable state across jobs).
    - Always create a new processor instance per call.
    - Profile is passed statelessly to `process_to_chunks(...)`, not stored on the processor.
    """

    # Map file extension -> processor class (not instance)
    _processor_classes = {
        ".pdf": PDFProcessor,
        ".txt": TextProcessor,
        ".md": TextProcessor,
    }

    @classmethod
    def get_processor(cls, file_path: str, profile: Optional[ChunkProfile] = None):
        ext = os.path.splitext(file_path)[1].lower()
        ProcessorCls = cls._processor_classes.get(ext)
        if not ProcessorCls:
            raise ValueError(f"Unsupported format: {ext}")

        # Create a fresh instance each time (no cross-job contamination)
        return ProcessorCls()