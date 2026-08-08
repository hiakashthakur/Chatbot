from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import os
import shutil

from app.container import container
from app.schemas.request import AskRequest,IngestRequest
from app.schemas.response import AskResponse,IngestResponse,HealthResponse

from app.exceptions.embedding_exception import EmbeddingException
from app.exceptions.vector_store_exception import VectorStoreException
from app.exceptions.llm_exception import LLMException
from fastapi import BackgroundTasks
from app.logger import logger

router = APIRouter()
router = APIRouter(
    prefix="/api/v1",
    tags=["RAG APIs"]
)


@router.get("/health")
def health():

    return HealthResponse(
        status="healthy"
    )


@router.post("/ingest")
async def ingest(
    request: IngestRequest,
    background_tasks: BackgroundTasks
):

    background_tasks.add_task(
        container.ingestion_service.ingest,
        request.pdf_path
    )

    return {
        "status":"accepted",
        "message":"PDF ingestion started."
    }

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    try:
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, file.filename)
        
        # Read the file contents asynchronously
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        background_tasks.add_task(
            container.ingestion_service.ingest,
            file_path
        )
        
        return {
            "status": "accepted",
            "message": f"File {file.filename} uploaded and ingestion started."
        }
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/ask",
    response_model=AskResponse
)
async def ask(
    request: AskRequest
):

    result = await container.rag_service.ask(
        session_id=request.session_id,
        question=request.question
    )

    return AskResponse(
        answer=result["answer"],
        sources=result["sources"]
    )


@router.post("/stream")
async def stream(
    request: AskRequest
):

    generator = container.rag_service.stream(
        session_id=request.session_id,
        question=request.question
    )

    return StreamingResponse(
        generator,
        media_type="text/plain"
    )

@router.delete("/memory/{session_id}")
def clear_memory(session_id: str):

    container.memory_service.clear_history(
        session_id
    )

    return {
        "message": "Conversation history cleared successfully."
    }

@router.get("/memory/{session_id}")
def get_memory(session_id: str):

    return {
        "history": container.memory_service.get_history(
            session_id
        )
    }