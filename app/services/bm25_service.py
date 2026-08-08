from typing import List, Dict, Any

from rank_bm25 import BM25Okapi

from app.logger import logger


class BM25Service:
    """
    BM25 lexical search service.
    """

    def __init__(self):

        logger.info("Initializing BM25 Service")

        # Stores complete metadata for every chunk
        self.documents: List[Dict] = []

        # BM25 index
        self.bm25 = None

        logger.info("BM25 Service Initialized")

    def _rebuild_index(self) -> None:
        """
        Rebuild BM25 index from all documents.
        """

        tokenized_documents = [
            item["document"].lower().split()
            for item in self.documents
        ]

        if tokenized_documents:

            self.bm25 = BM25Okapi(
                tokenized_documents
            )

        else:

            self.bm25 = None

    def add_documents(
        self,
        documents: List[Dict]
    ) -> None:
        """
        Add new documents without removing old ones.
        """

        logger.info(
            f"Adding {len(documents)} documents to BM25"
        )

        existing_ids = {
            item["chunk_id"]
            for item in self.documents
        }

        new_documents = [
            item
            for item in documents
            if item["chunk_id"] not in existing_ids
        ]

        self.documents.extend(
            new_documents
        )

        self._rebuild_index()

        logger.info(
            f"BM25 now contains {len(self.documents)} chunks"
        )

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents using BM25.

        Returns documents along with BM25 score
        and rank for hybrid retrieval.
        """

        if self.bm25 is None:
            return []

        logger.info(
            f"BM25 searching Top {top_k} documents"
        )

        query_tokens = query.lower().split()

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked = sorted(
            zip(scores, self.documents),
            key=lambda x: x[0],
            reverse=True
        )

        results = []

        for rank, (score, document) in enumerate(
            ranked[:top_k],
            start=1
        ):

            result = document.copy()

            result["bm25_score"] = float(score)
            result["bm25_rank"] = rank

            results.append(
                result
            )

        logger.info(
            f"BM25 retrieved {len(results)} document(s)"
        )

        return results

    def count(self) -> int:
        """
        Total indexed chunks.
        """

        return len(
            self.documents
        )

    def clear(self) -> None:
        """
        Remove all indexed documents.
        """

        self.documents.clear()

        self.bm25 = None

        logger.info(
            "BM25 index cleared"
        )