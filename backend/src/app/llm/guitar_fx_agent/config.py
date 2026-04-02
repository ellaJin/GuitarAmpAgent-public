# app/llm/guitar_fx_agent/config.py
from app.core.config import settings
from app.llm.llm_factory import LLMFactory, LLMConfig

def get_llm():
    llm = LLMFactory.create(
        LLMConfig(
            provider="deepseek",
            model="deepseek-r1-0528",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=1.3,
        )
    )
    return llm