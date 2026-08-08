from sentence_transformers import SentenceTransformer
from app.config import Config
from app.logger import logger
from app.exceptions.embedding_exception import (
    EmbeddingException
)

class EmbeddingService:
    def __init__(self):
        logger.info("Loading Embedding Model")
        self.model = SentenceTransformer(
            Config.EMBEDDING_MODEL
        )
        logger.info("Embedding Model Loaded")

    def get_embedding(self, text: str):
        """
        Single text ki embedding banata hai.
        Retrieval ke time use hoga.
        """
        try:
            embedding= self.model.encode(text)
            return embedding
        except Exception as e:
            raise EmbeddingException(
                str(e)
            )

    def get_embeddings(self, texts: list[str]):
        """
        Multiple texts/chunks ki embeddings banata hai.
        Ingestion ke time use hoga.
        """
        try:
            embedding= self.model.encode(texts)
            return embedding
        except Exception as e:
            raise EmbeddingException(
                str(e)
            )