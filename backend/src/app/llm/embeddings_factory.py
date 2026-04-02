# app/llm/embeddings_factory.py
from dataclasses import dataclass
from typing import Literal

from app.llm.customize_class.QWen_embeddings import QWenEmbeddings

EmbProvider = Literal["qwen"]


@dataclass
class EmbeddingsConfig:
    provider: EmbProvider = "qwen"
    model: str = "qwen2.5-vl-embedding"
    dimensions: int = 1024


class EmbeddingsFactory:
    """
    Embeddings 工厂
    - 只负责创建「向量模型」
    - 统一 provider/model/dim 的入口
    """

    @staticmethod
    def create(cfg: EmbeddingsConfig):
        if isinstance(cfg, str):
            cfg = EmbeddingsConfig(provider=cfg)

        if cfg.provider == "qwen":
            # QWenEmbeddings 内部已经会从 settings 读 QWEN_EMB_KEY
            return QWenEmbeddings(model=cfg.model, dimensions=cfg.dimensions)

        raise ValueError(f"Unsupported embeddings provider: {cfg.provider}")
