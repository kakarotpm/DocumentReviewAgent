"""DocReview API entry point. Run with: uvicorn app.main:app --reload"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import SessionLocal, init_db
from app.routes import document_types
from app.services.rulebooks import load_builtin_rulebooks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: create tables and load any rulebook files not yet in the database.
    init_db()
    with SessionLocal() as session:
        load_builtin_rulebooks(session, settings.rulebooks_dir)
    yield


app = FastAPI(title="DocReview API", lifespan=lifespan)
app.include_router(document_types.router)


@app.get("/api/health")
def health():
    """Quick check that the backend is running and the API key is set."""
    return {
        "status": "ok",
        "model": settings.anthropic_model,
        "api_key_configured": bool(settings.anthropic_api_key),
    }
