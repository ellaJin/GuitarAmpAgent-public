# app/service/effects/extract_router.py
"""
Effect Extraction Router.

Selects the best brand-specific strategy based on:
  1. brand_hint  - from upstream ctx (admin-set at upload, most reliable)
  2. device_name - user-provided or from document metadata
  3. sample_text - sampled from first few chunks (fallback)

Usage:
    router = EffectExtractRouter()
    strategy, match = router.route(brand_hint="boss", device_name="GT-1")
    if strategy.should_process_page(page_chunks):
        prompt = strategy.build_page_prompt(...)
        ...
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from app.service.effects.strategies import (
    BrandExtractStrategy,
    BrandMatchResult,
    MooerGEStrategy,
    Line6HelixStrategy,
    BossGTStrategy,
    GenericFallbackStrategy,
)


class EffectExtractRouter:

    def __init__(self):
        self._strategies: List[BrandExtractStrategy] = []
        self._fallback: Optional[BrandExtractStrategy] = None

        # Register all known brand strategies
        self.register(MooerGEStrategy())
        self.register(Line6HelixStrategy())
        self.register(BossGTStrategy())
        # Add new brands here:
        # self.register(ZoomStrategy())
        # self.register(HeadRushStrategy())

        # Default fallback
        self.set_fallback(GenericFallbackStrategy())

    def register(self, strategy: BrandExtractStrategy) -> None:
        self._strategies.append(strategy)

    def set_fallback(self, strategy: BrandExtractStrategy) -> None:
        self._fallback = strategy

    def route(
        self,
        device_name: str = "",
        brand_hint: str = "",
        sample_text: str = "",
    ) -> Tuple[BrandExtractStrategy, BrandMatchResult]:
        """
        Try each registered strategy.  Pick the one with highest confidence.
        Falls back to GenericFallbackStrategy if nothing matches.
        """
        best_strategy: Optional[BrandExtractStrategy] = None
        best_match: Optional[BrandMatchResult] = None

        # Log all candidates for debugging
        print(f"[router] routing: brand_hint='{brand_hint}', "
              f"device_name='{device_name}', "
              f"sample_text_len={len(sample_text)}")

        for strategy in self._strategies:
            result = strategy.match(device_name, brand_hint=brand_hint, sample_text=sample_text)

            if result is None:
                print(f"[router]   {strategy.brand_key():20s} -> no match")
                continue

            print(f"[router]   {strategy.brand_key():20s} -> "
                  f"conf={result.confidence:.2f}, family={result.device_family}")

            if best_match is None or result.confidence > best_match.confidence:
                best_strategy = strategy
                best_match = result

        if best_strategy and best_match:
            print(f"[router] SELECTED: {best_match.brand_key} "
                  f"(conf={best_match.confidence:.2f}, family={best_match.device_family})")
            return best_strategy, best_match

        # No match - use fallback
        assert self._fallback is not None, "No fallback strategy set"
        fallback_result = BrandMatchResult(
            brand_key="generic",
            confidence=0.3,
            device_family=device_name or "Unknown",
        )
        print(f"[router] NO MATCH - falling back to generic "
              f"(device_name='{device_name}')")
        return self._fallback, fallback_result

    def list_brands(self) -> List[str]:
        return [s.brand_key() for s in self._strategies]
