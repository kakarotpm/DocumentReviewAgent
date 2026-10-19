"""DocReview API entry point. Run with: uvicorn app.main:app --reload"""

from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="DocReview API")


@app.get("/api/health")
def health():
    """Quick check that the backend is running and the API key is set."""
    return {
        "status": "ok",
        "model": settings.anthropic_model,
        "api_key_configured": bool(settings.anthropic_api_key),
    }
