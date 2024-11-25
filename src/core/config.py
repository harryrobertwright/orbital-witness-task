from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    COPILOT_API_BASE_URL: str = "https://owpublic.blob.core.windows.net/tech-task"

    class Config:  # noqa: D106
        env_file = ".env"
        case_sensitive = True


settings = Settings()
