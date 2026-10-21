"""DocReview API entry point. Run with: uvicorn app.main:app --reload"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import SessionLocal, init_db
from app.routes import dashboard, document_types, documents, reviews
from app.services.llm import ai_available
from app.services.review_engine import mark_interrupted_reviews
from app.services.rulebooks import load_builtin_rulebooks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: create tables, load any new rulebook files, tidy up reviews a restart interrupted.
    init_db()
    with SessionLocal() as session:
        load_builtin_rulebooks(session, settings.rulebooks_dir)
        interrupted = mark_interrupted_reviews(session)
        if interrupted:
            logger.info("Marked %s interrupted review(s) as errors", interrupted)
    if not ai_available():
        logger.warning("No ANTHROPIC_API_KEY set: reviews run in DEMO mode (keyword matching, not AI).")
    yield


app = FastAPI(title="DocReview API", lifespan=lifespan)
app.include_router(document_types.router)
app.include_router(documents.router)
app.include_router(reviews.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    """Quick check that the backend is running and whether the AI is available."""
    return {
        "status": "ok",
        "model": settings.anthropic_model,
        "api_key_configured": ai_available(),
    }
