"""DocReview API entry point. Run with: uvicorn app.main:app --reload"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import SessionLocal, init_db
from app.routes import dashboard, document_types, documents, reviews, usage
from app.services.llm import PROVIDERS, ai_available, ai_provider, key_setting, model_name, provider_name
from app.services.review_engine import mark_interrupted_reviews
from app.services.rulebooks import load_builtin_rulebooks
from app.services.usage import seed_default_prices

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: create tables, load any new rulebook files, tidy up reviews a restart interrupted.
    init_db()
    with SessionLocal() as session:
        load_builtin_rulebooks(session, settings.rulebooks_dir)
        seed_default_prices(session)
        interrupted = mark_interrupted_reviews(session)
        if interrupted:
            logger.info("Marked %s interrupted review(s) as errors", interrupted)
    if ai_provider() not in PROVIDERS:
        logger.warning("AI_PROVIDER '%s' isn't recognised. Use anthropic or openai.", settings.ai_provider)
    if ai_available() and not model_name():
        logger.warning("OPENAI_MODEL isn't set in .env: AI reviews will fail until you add the model name.")
    elif ai_available():
        logger.info("Reviews use %s, model %s.", provider_name(), model_name())
    else:
        logger.warning("No %s set: reviews run in DEMO mode (keyword matching, not AI).", key_setting())
    yield


app = FastAPI(title="DocReview API", lifespan=lifespan)
app.include_router(document_types.router)
app.include_router(documents.router)
app.include_router(reviews.router)
app.include_router(dashboard.router)
app.include_router(usage.router)


@app.get("/api/health")
def health():
    """Quick check that the backend is running and whether the AI is available."""
    return {
        "status": "ok",
        "provider": provider_name(),
        "model": model_name(),
        "api_key_configured": ai_available(),
    }
