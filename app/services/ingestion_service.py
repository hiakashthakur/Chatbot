from app.exceptions import chunk_exception
from app.exceptions.pdf_exception import (
    PDFNotFoundException,
    EmptyPDFException
)
from app.exceptions.chunk_exception import ChunkException
from app.exceptions.embedding_exception import EmbeddingException
from app.exceptions.vector_store_exception import VectorStoreException
from app.exceptions.ingestion_exception import IngestionException
from app.logger import logger


class IngestionService:

    def __init__(
        self,
        pdf_service,
        chunk_service,
        embedding_service,
        vector_store_service,
        bm25_service
    ):

        self.pdf_service = pdf_service
        self.chunk_service = chunk_service
        self.embedding_service = embedding_service
        self.vector_store_service = vector_store_service
        self.bm25_service = bm25_service

    def ingest(
        self,
        pdf_path: str
    ) -> None:

        try:

            logger.info(
                f"Starting ingestion for {pdf_path}"
            )

            # -------------------------
            # Load PDF
            # -------------------------

            reader = self.pdf_service.load_pdf(
                pdf_path
            )

            pages = self.pdf_service.extract_pages(
                reader
            )

            source = self.pdf_service.get_filename(
                pdf_path
            )

            # -------------------------
            # Chunking
            # -------------------------

            chunks = self.chunk_service.create_page_chunks(
                pages
            )

            logger.info(
                f"Generated {len(chunks)} chunk(s)"
            )
            for chunk in chunks:
                chunk["source"] = source

            texts = [
                chunk["document"]
                for chunk in chunks
            ]

            # -------------------------
            # Build BM25 Index
            # -------------------------

            self.bm25_service.add_documents(
                chunks
            )
            # -------------------------
            # Embeddings
            # -------------------------

            embeddings = self.embedding_service.get_embeddings(
                texts
            )
            logger.info(
                f"Generated {len(embeddings)} embedding(s)"
            )

            # -------------------------
            # Store in Qdrant
            # -------------------------

            self.vector_store_service.add_documents(
                chunks=chunks,
                embeddings=embeddings,
                source=source
            )

            logger.info(
                f"Successfully ingested {pdf_path}"
            )

        except (
            PDFNotFoundException,
            EmptyPDFException,
            ChunkException,
            EmbeddingException,
            VectorStoreException,
        ):
            raise

        except Exception as e:

            logger.exception(
                "Unexpected ingestion error"
            )

            raise IngestionException(
                str(e)
            ) from e