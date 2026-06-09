from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from app.line.webhook import router as line_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="LINE Bot RAG", lifespan=lifespan)

app.include_router(line_router, prefix="/api/line")

@app.get("/health")
async def health():
    return {"status": "ok"}