from dataclasses import dataclass
from typing import Optional, Literal

from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek


# 支持的 LLM 提供方
Provider = Literal["openai", "deepseek", "qwen", "local"]


@dataclass
class LLMConfig:
    """
    统一的 Chat LLM 配置
    """
    provider: Provider
    model: str

    api_key: Optional[str] = None
    base_url: Optional[str] = None

    temperature: float = 0.7
    max_tokens: int = 1024
    timeout_s: int = 60
    max_retries: int = 2


class LLMFactory:
    """
    Chat LLM 工厂
    - 只负责创建「对话模型」
    - 屏蔽不同 provider 的参数差异
    """

    @staticmethod
    def create(cfg: LLMConfig):
        if cfg.provider == "openai":
            return ChatOpenAI(
                model=cfg.model,
                api_key=cfg.api_key,
                base_url=cfg.base_url,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                timeout=cfg.timeout_s,
                max_retries=cfg.max_retries,
            )

        if cfg.provider == "deepseek":
            # ⚠️ DeepSeek wrapper 使用的是 model_name / api_base
            # ⚠️ 很多版本不支持 max_tokens / timeout / max_retries
            return ChatDeepSeek(
                model_name=cfg.model,
                api_key=cfg.api_key,
                api_base=cfg.base_url,
                temperature=cfg.temperature,
            )

        # 预留扩展位（你后面会加）
        # if cfg.provider == "qwen":
        #     ...
        #
        # if cfg.provider == "local":
        #     ...

        raise ValueError(f"Unsupported provider: {cfg.provider}")