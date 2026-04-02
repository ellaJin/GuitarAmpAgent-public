# app/service/effects/strategies/__init__.py
from app.service.effects.strategies.base import BrandExtractStrategy, BrandMatchResult
from app.service.effects.strategies.mooer_ge import MooerGEStrategy
from app.service.effects.strategies.line6_helix import Line6HelixStrategy
from app.service.effects.strategies.boss_gt import BossGTStrategy
from app.service.effects.strategies.generic import GenericFallbackStrategy

__all__ = [
    "BrandExtractStrategy",
    "BrandMatchResult",
    "MooerGEStrategy",
    "Line6HelixStrategy",
    "BossGTStrategy",
    "GenericFallbackStrategy",
]
