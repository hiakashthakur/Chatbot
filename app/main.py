from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import router


app = FastAPI(
    title="Production RAG API",
    version="1.0.0"
)

app.include_router(router)

# Mount static files for UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")