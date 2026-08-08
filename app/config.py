import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Config:

    # Models
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    LLM_MODEL = "gemini-3.1-flash-lite"

    # QdrantDB
    QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_db")
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    COLLECTION_NAME = "collection_test"
    VECTOR_SIZE = 384
    # Chunking
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100

    # Retrieval
    TOP_K = 5

    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    RERANKER_MODEL="cross-encoder/ms-marco-MiniLM-L-6-v2"

    RERANK_TOP_K=3