# RAG FAQ Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot backend built with **FastAPI**. This system allows you to upload PDF documents, extract and vectorize their contents, and ask questions using a state-of-the-art hybrid search approach paired with Google's Gemini LLM.

## 🚀 Features

- **Hybrid Search**: Combines Dense Vector Search (Sentence Transformers) with Sparse Keyword Search (BM25) to maximize retrieval accuracy.
- **Cross-Encoder Reranking**: Uses `ms-marco-MiniLM-L-6-v2` to intelligently rerank search results before sending them to the LLM.
- **Query Rewriting**: Analyzes and rewrites user queries based on conversation history for better context awareness.
- **Google Gen AI Integration**: Uses Gemini 3.1 (`google-genai`) for generating high-quality, accurate responses.
- **Qdrant Vector Store**: Seamless integration with Qdrant Cloud for storing embeddings and document metadata.
- **PDF Processing & Chunking**: Extracts text from PDFs and chunks it using Langchain text splitters.
- **Session-based Memory**: Maintains conversation history per user session to support follow-up questions.
- **Streaming Support**: API supports real-time text streaming for a better user experience.

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python)
- **LLM**: Google Gemini
- **Vector Database**: Qdrant
- **Embeddings**: `sentence-transformers` (all-MiniLM-L6-v2)
- **Reranker**: HuggingFace Cross-Encoder
- **Keyword Search**: `rank_bm25`
- **PDF Parsing**: `pypdf`

## ⚙️ Installation & Setup

1. **Clone the repository and navigate to the project directory.**

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   ```

## 🚀 Running the Server

Start the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.
- **API Documentation**: `http://127.0.0.1:8000/docs` (Swagger UI)
- **Static UI**: Accessible at the root `http://127.0.0.1:8000/`

## 📡 API Endpoints

### 1. Document Ingestion
- `POST /api/v1/upload` - Upload a PDF document directly. Returns immediately while the ingestion runs as a background task.
- `POST /api/v1/ingest` - Trigger ingestion from a local file path.

### 2. Chat & QA
- `POST /api/v1/ask` - Ask a question. Requires `session_id` and `question`. Returns the answer and sources.
- `POST /api/v1/stream` - Ask a question and get a Server-Sent Events (SSE) streaming response.

### 3. Memory Management
- `GET /api/v1/memory/{session_id}` - Retrieve the conversation history for a specific session.
- `DELETE /api/v1/memory/{session_id}` - Clear the conversation history for a specific session.

### 4. System
- `GET /api/v1/health` - Check if the API is running.

## 🏗️ Project Structure

```text
├── app/
│   ├── api/                 # API routers and endpoints
│   ├── exceptions/          # Custom error handling classes
│   ├── schemas/             # Pydantic models for request/response validation
│   ├── services/            # Core business logic
│   │   ├── bm25_service.py         # Keyword search
│   │   ├── chunk_service.py        # Text splitting
│   │   ├── embedding_service.py    # Vector embeddings
│   │   ├── ingestion_service.py    # PDF to VectorDB pipeline
│   │   ├── llm_service.py          # Gemini API interactions
│   │   ├── memory_service.py       # Conversation history tracking
│   │   ├── pdf_service.py          # PDF text extraction
│   │   ├── query_rewrite_service.py# Contextual query optimization
│   │   ├── rag_service.py          # Orchestrates the entire RAG flow
│   │   ├── reranker_service.py     # Cross-encoder results reranking
│   │   └── vector_store_service.py # Qdrant DB interactions
│   ├── static/              # Frontend UI assets
│   ├── config.py            # Application configuration
│   ├── container.py         # Dependency injection container
│   ├── logger.py            # Custom logging setup
│   └── main.py              # FastAPI application entry point
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables (not checked into source control)
```
