# app/llm/guitar_fx_agent/config.py
from app.core.config import settings
from app.llm.llm_factory import LLMFactory, LLMConfig

_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMFactory.create(
            LLMConfig(
                provider="deepseek",
                # model="deepseek-r1-0528"
                model="deepseek-v3",
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                temperature=0.7,
            )
        )
    return _llm_instance