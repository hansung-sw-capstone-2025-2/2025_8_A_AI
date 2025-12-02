from typing import List
from langchain_upstage import UpstageEmbeddings

from src.core.config import settings


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        if not settings.upstage_api_key:
            raise ValueError("UPSTAGE_API_KEY is not set")

        self.embedder = UpstageEmbeddings(
            api_key=settings.upstage_api_key,
            model=settings.embedding_model
        )
        self._initialized = True

    def embed_text(self, text: str) -> List[float]:
        return self.embedder.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(texts)

    @property
    def dimension(self) -> int:
        return settings.embedding_dimension
