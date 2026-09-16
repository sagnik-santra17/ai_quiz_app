from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "AI QUIZ APP"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    POOL_THRESHOLD: int = 5
    POOL_TARGET: int = 10
    CACHE_TTL_SECONDS: int = 3600
    RATE_LIMIT_PER_MINUTE: int = 30
    GEMINI_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()