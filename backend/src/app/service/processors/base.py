# app/service/processors/base.py
from typing import Optional, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.service.doc_processing.profiles import ChunkProfile


class BaseProcessor:
    """
    Base document processor.

    Design goals:
    - Stateless chunking: choose splitter settings per call (per job) using ChunkProfile.
    - Backward compatible defaults if profile is not provided.
    """

    def __init__(self):
        # Default splitter configuration (fallback only).
        # We do NOT instantiate a splitter here to avoid "hard-coded chunking".
        self.default_chunk_size = 1024
        self.default_chunk_overlap = 256

        # Separators are stable and can remain shared.
        self.separators = ["\n\n", "\n", "。", ".", ":", ";", " "]

    def extract_text(self, file_path: str) -> str:
        raise NotImplementedError

    def _build_splitter(self, profile: Optional[ChunkProfile]) -> RecursiveCharacterTextSplitter:
        """
        Build a new splitter instance for this call.
        This avoids shared mutable state across jobs.
        """
        if profile is None:
            chunk_size = self.default_chunk_size
            chunk_overlap = self.default_chunk_overlap
        else:
            # Clamp chunk size into [min_tokens, max_tokens] for safety.
            # NOTE: These are "approximate tokens". RecursiveCharacterTextSplitter
            # uses character length by default unless configured with a token length fn.
            chunk_size = int(max(profile.min_tokens, min(profile.chunk_tokens, profile.max_tokens)))
            chunk_overlap = int(max(0, min(profile.overlap_tokens, chunk_size // 2)))

        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
        )

    def process_to_chunks(self, file_path: str, profile: Optional[ChunkProfile] = None):
        """
        Extract text and split into LangChain Document chunks.

        `profile` controls chunk_size / overlap.
        """
        text = self.extract_text(file_path) or ""
        splitter = self._build_splitter(profile)
        chunks = splitter.create_documents([text])
        return chunks