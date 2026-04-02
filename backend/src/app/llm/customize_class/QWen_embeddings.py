from dashscope import MultiModalEmbedding
from langchain_core.embeddings import Embeddings
# 1. 替换导入路径
from app.core.config import settings


class QWenEmbeddings(Embeddings):
    """
    Use qwen2.5-vl-embedding, dimension=1024
    """

    def __init__(self, model: str = "qwen2.5-vl-embedding", dimensions: int = 1024):
        self.model = model
        self.dimensions = dimensions
        # 2. 检查 API Key 是否存在，防止运行时报错
        if not settings.QWEN_EMB_KEY:
            raise ValueError("QWEN_EMB_KEY not found in environment settings")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        input_payload = [{"text": text}]
        # 3. 使用 settings 对象中的配置
        response = MultiModalEmbedding.call(
            model=self.model,
            api_key=settings.QWEN_EMB_KEY,  # 这里改为 settings.xxx
            input=input_payload
        )

        if response.status_code != 200:
            raise Exception(f"Embedding failed: {response.message}")

        return response.output["embeddings"][0]["embedding"]