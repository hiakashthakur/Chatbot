from app.schemas import response
import uuid
from typing import List, Dict, Any

from qdrant_client import (
    QdrantClient,
    AsyncQdrantClient
)
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from app.config import Config
from app.logger import logger
from app.exceptions.vector_store_exception import (
    VectorStoreException
)


class VectorStoreService:

    def __init__(self) -> None:
        logger.info("Initializing Vector Store Service (Qdrant)")

        try:

            if Config.QDRANT_URL and Config.QDRANT_API_KEY:
                self.client = QdrantClient(
                    url=Config.QDRANT_URL,
                    api_key=Config.QDRANT_API_KEY
                )

                self.async_client = AsyncQdrantClient(
                    url=Config.QDRANT_URL,
                    api_key=Config.QDRANT_API_KEY
                )
            else:
                self.client = QdrantClient(
                    path=Config.QDRANT_PATH
                )

                self.async_client = AsyncQdrantClient(
                    path=Config.QDRANT_PATH
                )

            self._create_collection()

            logger.info("Vector Store Service Initialized Successfully")

        except Exception as e:

            logger.exception(
                "Failed to initialize Vector Store Service"
            )

            raise VectorStoreException(
                str(e)
            ) from e
    def _vector_params(self) -> VectorParams:
        """
        Return vector configuration.
        """

        return VectorParams(
            size=Config.VECTOR_SIZE,
            distance=Distance.COSINE
        )

    def _create_collection(self) -> None:
        """
        Create collection if it does not exist.
        """

        if not self.client.collection_exists(
            collection_name=Config.COLLECTION_NAME
        ):

            logger.info(
                f"Creating collection: {Config.COLLECTION_NAME}"
            )

            self.client.create_collection(
                collection_name=Config.COLLECTION_NAME,
                vectors_config=self._vector_params()
            )
    def _format_search_result(
        self,
        response
    ) -> Dict[str, Any]:
        """
        Format Qdrant response.
        """

        documents = []
        pages = []
        sources = []
        chunk_ids = []
        scores = []

        for point in response.points:

            payload = point.payload

            documents.append(
                payload.get("document", "")
            )

            pages.append(
                payload.get("page")
            )

            sources.append(
                payload.get("source")
            )

            chunk_ids.append(
                payload.get("chunk_id")
            )

            scores.append(
                point.score
            )

        return {
            "documents": [documents],
            "pages": [pages],
            "sources": [sources],
            "chunk_ids": [chunk_ids],
            "scores": [scores]
        }
        
    def search(
        self,
        embedding,
        top_k: int = Config.TOP_K
    ) -> Dict[str, Any]:
        """
        Search similar documents from Qdrant.
        """

        logger.info(
            f"Searching Top {top_k} documents"
        )

        try:

            response = self.client.query_points(
            collection_name=Config.COLLECTION_NAME,
            query=embedding.tolist(),
            limit=top_k
        )

            logger.info(
                f"Retrieved {len(response.points)} document(s)"
            )
            return self._format_search_result(
                response
            )

        except Exception as e:

            logger.exception(
                "Failed to search documents"
            )

            raise VectorStoreException(
                str(e)
            ) from e

    async def asearch(
        self,
        embedding,
        top_k: int = Config.TOP_K
    ):

        logger.info(
            f"Searching Top {top_k} documents (Async)"
        )

        try:

            response = await self.async_client.query_points(
                collection_name=Config.COLLECTION_NAME,
                query=embedding.tolist(),
                limit=top_k
            )
            return self._format_search_result(
                response
            )
        except Exception as e:

            raise VectorStoreException(
                str(e)
            ) from e

    def _build_points(
        self,
        chunks: List[Dict],
        embeddings,
        source: str
    ) -> List[PointStruct]:
        """
        Build Qdrant PointStruct objects.
        """

        points = []

        for chunk, embedding in zip(
            chunks,
            embeddings.tolist()
        ):

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "document": chunk["document"],
                        "page": chunk["page"],
                        "chunk_id": chunk["chunk_id"],
                        "source": chunk["source"]
                    }
                )
            )

        return points
    
    def add_documents(
        self,
        chunks: List[Dict],
        embeddings,
        source: str
    ) -> None:
        """
        Store documents and metadata in Qdrant.
        """

        logger.info(
            f"Adding {len(chunks)} document(s)"
        )

        try:

            points = self._build_points(
                chunks,
                embeddings,
                source
            )

            batch_size = 200
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=Config.COLLECTION_NAME,
                    points=batch_points
                )
                logger.info(f"Upserted batch {i//batch_size + 1}")

            logger.info(
                "Documents added successfully"
            )

        except Exception as e:

            logger.exception(
                "Failed to add documents"
            )

            raise VectorStoreException(
                str(e)
            ) from e

    async def aadd_documents(
        self,
        chunks,
        embeddings,
        source
    ):
        """
        Store documents and metadata in Qdrant.
        """

        logger.info(
            f"Adding {len(chunks)} document(s)"
        )

        try:

            points = self._build_points(
                chunks,
                embeddings,
                source
            )
            
            batch_size = 200
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i + batch_size]
                await self.async_client.upsert(
                    collection_name=Config.COLLECTION_NAME,
                    points=batch_points
                )
                logger.info(f"Upserted batch {i//batch_size + 1} (async)")

            logger.info(
                "Documents added successfully"
            )

        except Exception as e:

            logger.exception(
                "Failed to add documents"
            )

            raise VectorStoreException(
                str(e)
            ) from e
    

    def count(self) -> int:
        """
        Return total documents stored.
        """

        logger.info(
            "Counting documents in Vector Store"
        )

        try:

            count = self.client.count(
                collection_name=Config.COLLECTION_NAME
            ).count

            logger.info(
                f"Total Documents: {count}"
            )

            return count

        except Exception as e:

            logger.exception(
                "Failed to count documents"
            )

            raise VectorStoreException(
                str(e)
            ) from e

    async def acount(self):

        """
        Return total documents stored.
        """

        logger.info(
            "Counting documents in Vector Store"
        )

        try:

            count = await self.async_client.count(
                collection_name=Config.COLLECTION_NAME
            ).count

            logger.info(
                f"Total Documents: {count}"
            )

            return count

        except Exception as e:

            logger.exception(
                "Failed to count documents"
            )

            raise VectorStoreException(
                str(e)
            ) from e

    def delete(self) -> None:
        """
        Delete all documents from collection.
        """

        logger.warning(
            "Deleting Vector Store Collection"
        )

        try:

            self.client.delete_collection(
                collection_name=Config.COLLECTION_NAME
            )

            self._create_collection()

            logger.info(
                "Collection recreated successfully"
            )

        except Exception as e:

            logger.exception(
                "Failed to delete collection"
            )

            raise VectorStoreException(
                str(e)
            ) from e

    async def adelete(self):
        """
        Delete all documents from collection.
        """

        logger.warning(
            "Deleting Vector Store Collection"
        )

        try:

            await self.async_client.create_collection(
                collection_name=Config.COLLECTION_NAME,
                vectors_config=self._vector_params()
            )
            logger.info(
                "Collection recreated successfully"
            )

        except Exception as e:

            logger.exception(
                "Failed to delete collection"
            )

            raise VectorStoreException(
                str(e)
            ) from e