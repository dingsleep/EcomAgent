"""向量化封装：支持 OpenAI API 和本地 sentence-transformers 两种后端。

- openai：text-embedding-3-small 等云端模型
- local：BAAI/bge-small-zh-v1.5 等本地模型（免费，无需 API Key）
- 统一接口 encode(texts) → list[list[float]]
"""

from typing import Iterable

from openai import OpenAI


class Embedder:
    """OpenAI Embeddings 同步封装。"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "text-embedding-3-small",
        batch_size: int = 64,
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._batch_size = batch_size

    @property
    def model(self) -> str:
        return self._model

    def encode(self, texts: Iterable[str]) -> list[list[float]]:
        """批量编码，自动按 batch_size 分批请求。"""
        texts = list(texts)
        if not texts:
            return []
        out: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            resp = self._client.embeddings.create(model=self._model, input=batch)
            out.extend(item.embedding for item in resp.data)
        return out

    def encode_one(self, text: str) -> list[float]:
        return self.encode([text])[0]


class LocalEmbedder:
    """本地 sentence-transformers 封装（免费，无需 API Key）。

    默认 BAAI/bge-small-zh-v1.5：中文优化，512 维，约 100MB 首次自动下载。
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", batch_size: int = 64):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        self._batch_size = batch_size

    @property
    def model(self) -> str:
        return self._model_name

    def encode(self, texts: Iterable[str]) -> list[list[float]]:
        texts = list(texts)
        if not texts:
            return []
        out: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            embeddings = self._model.encode(batch, normalize_embeddings=True)
            out.extend(embeddings.tolist())
        return out

    def encode_one(self, text: str) -> list[float]:
        return self.encode([text])[0]
