# app/service/effects/strategies/base.py
"""
Abstract base for brand-specific effect extraction strategies.

Each brand subclass is responsible for:
  1. match()              - Does this document belong to me?
  2. should_process_page() - Lightweight gate: skip pages with no effect listings.
  3. build_page_prompt()   - Brand-tailored LLM prompt.
  4. post_process()        - Normalize raw_type, deduplicate, enrich metadata.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BrandMatchResult:
    """Returned by the router after brand matching."""
    brand_key: str          # e.g. "line6", "mooer"
    confidence: float       # 0.0 ~ 1.0
    device_family: str      # e.g. "Helix LT", "GE150 Pro"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BrandExtractStrategy(ABC):

    # ---- Identity ----

    @abstractmethod
    def brand_key(self) -> str:
        """Unique identifier, e.g. 'line6_helix'."""
        ...

    # ---- Matching ----

    @abstractmethod
    def match(
        self,
        device_name: str,
        brand_hint: str = "",
        sample_text: str = "",
    ) -> Optional[BrandMatchResult]:
        """
        Check whether this strategy matches the given document.

        Args:
            device_name:  user-provided device name or doc-metadata name.
            brand_hint:   brand field from upstream ctx (set by admin at upload).
            sample_text:  sampled text from first few chunks (fallback signal).
        Returns:
            BrandMatchResult if matched, else None.
        """
        ...

    # ---- Page gate ----

    def should_process_page(self, page_chunks: List[Dict[str, Any]]) -> bool:
        """
        Lightweight pre-filter run BEFORE the LLM call.
        Return False to skip this page entirely (saves tokens + reduces noise).

        Default: process everything.  Override per brand for efficiency.
        """
        return True

    # ---- Prompt ----

    @abstractmethod
    def build_page_prompt(
        self,
        device_name: str,
        page_chunks_json: str,
        page_number: Optional[int] = None,
        allowed_indices: list[int] | None = None,
    ) -> str:
        """Build a brand-specific page-level extraction prompt."""
        ...

    # ---- Post-processing ----

    @abstractmethod
    def post_process(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Brand-specific normalization, dedup, metadata enrichment."""
        ...

    # ---- MIDI extraction (optional; off by default) ----

    def supports_midi(self) -> bool:
        """
        Return True if this strategy can extract MIDI mappings from the manual.
        Default: False. Override per brand when MIDI content is present.
        """
        return False

    def should_process_midi_page(self, page_chunks: List[Dict[str, Any]]) -> bool:
        """
        Lightweight pre-filter run BEFORE the LLM call for MIDI extraction.
        Return False to skip this page (saves tokens + reduces noise).
        Default: False (skip everything). Override per brand.
        """
        return False

    def build_midi_page_prompt(
        self,
        device_name: str,
        page_chunks_json: str,
        page_number: Optional[int] = None,
        allowed_indices: list[int] | None = None,
    ) -> str:
        """
        Build a brand-specific page-level MIDI extraction prompt.
        Only called when supports_midi() is True.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build_midi_page_prompt() "
            "when supports_midi() returns True."
        )

    def post_process_midi(
        self, entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Brand-specific normalization / dedup for raw MIDI entries.
        Default: identity pass-through.
        """
        return entries

    # ---- Helpers (available to all subclasses) ----

    @staticmethod
    def _combine_chunk_text(
        page_chunks: List[Dict[str, Any]],
        max_chars_per_chunk: int = 300,
    ) -> str:
        """Join the first N chars of each chunk into one lowercase string."""
        return " ".join(
            (c.get("content") or "")[:max_chars_per_chunk].lower()
            for c in page_chunks
        )

    @staticmethod
    def _check_section_metadata(
        page_chunks: List[Dict[str, Any]],
        keywords: tuple[str, ...],
    ) -> bool:
        """Return True if any chunk's 'section' field contains one of the keywords."""
        for c in page_chunks:
            section = (c.get("section") or "").lower()
            if any(kw in section for kw in keywords):
                return True
        return False
