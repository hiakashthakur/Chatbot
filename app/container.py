from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.chunk_service import ChunkService
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService
from app.services.memory_service import MemoryService
from app.services.bm25_service import BM25Service
from app.services.reranker_service import RerankerService
from app.services.query_rewrite_service import QueryRewriteService


class Container:
    """
    Dependency Injection Container.

    Responsible for initializing and managing all
    application services.
    """

    def __init__(self):

        # -------------------------
        # Core Services
        # -------------------------

        self.embedding_service = EmbeddingService()

        self.vector_store_service = VectorStoreService()

        self.llm_service = LLMService()

        self.pdf_service = PDFService()

        self.chunk_service = ChunkService()

        self.memory_service = MemoryService()

        self.bm25_service = BM25Service()
        
        self.reranker_service = RerankerService()

        self.query_rewrite_service=QueryRewriteService(
            llm_service=self.llm_service
        )

        # -------------------------
        # Business Services
        # -------------------------

        self.ingestion_service = IngestionService(
            pdf_service=self.pdf_service,
            chunk_service=self.chunk_service,
            embedding_service=self.embedding_service,
            vector_store_service=self.vector_store_service,
            bm25_service=self.bm25_service
        )

        self.rag_service = RAGService(
            embedding_service=self.embedding_service,
            vector_service=self.vector_store_service,
            bm25_service=self.bm25_service,
            reranker_service=self.reranker_service,
            query_rewrite_service=self.query_rewrite_service,
            llm_service=self.llm_service,
            memory_service=self.memory_service
        )


container = Container()