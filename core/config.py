from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    POOL_THRESHOLD: int = 5
    POOL_TARGET: int = 10
    RATE_LIMIT_PER_MINUTE: int = 30
    GEMINI_API_KEY: str
    MODEL_NAME: str = "gemini-3.8-flash"
    POOL_INTERVAL_SECONDS: int = 60
    WORKER_ENABLED: bool = True
    DB_SSL: bool = False
    GROQ_API_KEY: str | None = None
    LLM_MODEL: str = "openai/gpt-oss-120b"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_quiz_app_test"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

settings = Settings()