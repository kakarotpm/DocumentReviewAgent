"""App settings, read from the .env file in the project root."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    # Which AI reviews documents: "anthropic" (Claude) or "openai" (GPT). Without that provider's key, demo mode.
    ai_provider: str = "anthropic"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    # How hard the model thinks: low / medium / high. Medium balances quality and speed.
    anthropic_effort: str = "medium"

    openai_api_key: str = ""
    openai_model: str = ""  # the model name your key can use, as shown on the OpenAI dashboard
    # Reasoning models only: low / medium / high. Leave blank for models that don't support it.
    openai_reasoning_effort: str = ""
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'backend' / 'docreview.db'}"
    rulebooks_dir: Path = PROJECT_ROOT / "rulebooks"


settings = Settings()
