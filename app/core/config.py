from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Env(str, Enum):
    dev = "dev"
    stg = "stg"
    prod = "prod"

class Settings(BaseSettings):
    # Reads .env locally; in prod you can rely on real env vars.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",   # avoids collisions; keys become APP_*
        extra="ignore",
    )

    # General
    PROJECT_NAME: str = "Senecampus Backend"
    ENV: Env = Env.dev
    DEBUG: bool = Field(default=True)  # overridden by APP_DEBUG

    # Database
    DATABASE_URL: str = "sqlite:///./.data/senecampus.db"

    # Vectors & infra
    VECTOR_DIM: int = 128
    
    # Limit for mailbox request length
    MAILBOX_DEFAULT_LIMIT: int = 5
    MAILBOX_MAX_LIMIT: int = 20
    
    MAILBOX_RETENTION_HOURS: int = 18

    # Derived/convenience
    @property
    def LOG_LEVEL(self) -> str:
        return "DEBUG" if self.ENV == Env.dev else "INFO"

settings = Settings()
