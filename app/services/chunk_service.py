from typing import List, Dict

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from app.config import Config
from app.logger import logger
from app.exceptions.chunk_exception import (
    ChunkException
)


class ChunkService:

    def __init__(
        self,
        chunk_size: int = Config.CHUNK_SIZE,
        chunk_overlap: int = Config.CHUNK_OVERLAP
    ):

        logger.info("Initializing Chunk Service")

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        logger.info("Chunk Service Initialized")

    def create_chunks(
        self,
        text: str
    ) -> List[str]:
        """
        Split plain text into chunks.
        (Backward compatible)
        """

        try:

            logger.info("Creating Chunks")

            chunks = self.splitter.split_text(
                text
            )

            logger.info(
                f"Created {len(chunks)} chunk(s)"
            )

            return chunks

        except Exception as e:

            logger.exception(
                "Failed to create chunks"
            )

            raise ChunkException(
                str(e)
            ) from e

    def create_page_chunks(
        self,
        pages: List[Dict]
    ) -> List[Dict]:
        """
        Split page-wise text while preserving metadata.
        """

        try:

            logger.info(
                "Creating page-wise chunks"
            )

            chunk_id = 1

            chunks = []

            for page in pages:

                if not page.get("text"):
                    continue

                page_chunks = self.splitter.split_text(
                    page["text"]
                )

                for chunk in page_chunks:

                    chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "page": page["page"],
                            "document": chunk
                        }
                    )

                    chunk_id += 1

            logger.info(
                f"Created {len(chunks)} chunk(s)"
            )

            return chunks

        except Exception as e:

            logger.exception(
                "Failed to create page chunks"
            )

            raise ChunkException(
                str(e)
            ) from e