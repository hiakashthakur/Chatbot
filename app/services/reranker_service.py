from typing import List, Dict

from sentence_transformers import CrossEncoder

from app.config import Config
from app.logger import logger
from app.exceptions.reranker_exception import (
    RerankerException
)


class RerankerService:
    """
    Cross Encoder based reranking service.
    """

    def __init__(self):

        logger.info(
            "Initializing Reranker Service"
        )

        try:

            self.model = CrossEncoder(
                Config.RERANKER_MODEL
            )

            logger.info(
                "Reranker Service Initialized"
            )

        except Exception as e:

            logger.exception(
                "Failed to initialize Reranker"
            )

            raise RerankerException(
                str(e)
            ) from e

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = Config.RERANK_TOP_K
    ) -> List[Dict]:
        """
        Re-rank retrieved documents.
        """

        try:

            if not documents:
                return []

            logger.info(
                f"Reranking {len(documents)} documents"
            )

            pairs = [
                (
                    query,
                    document["document"]
                )
                for document in documents
            ]

            scores = self.model.predict(
                pairs
            )

            ranked_documents = sorted(
                zip(scores, documents),
                key=lambda x: x[0],
                reverse=True
            )

            top_documents = [
                document
                for _, document in ranked_documents[:top_k]
            ]

            logger.info(
                f"Selected Top {len(top_documents)} documents"
            )

            return top_documents

        except Exception as e:

            logger.exception(
                "Reranking failed"
            )

            raise RerankerException(
                str(e)
            ) from e