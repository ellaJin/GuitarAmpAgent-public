# app/service/effects/extractor_factory.py
from app.service.effects.llm_effect_extractor import LLMEffectExtractor
from app.llm.guitar_fx_agent.config import get_llm


class EffectExtractorFactory:
    @staticmethod
    def create(kind: str = "llm", **kwargs):
        if kind == "llm":
            llm = get_llm()  # ✅ 复用你统一配置
            return LLMEffectExtractor(llm=llm, **kwargs)
        raise ValueError(f"Unknown extractor kind: {kind}")
