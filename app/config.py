from pydantic import AnyUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: AnyUrl = "redis://localhost:6379/0"
    BASE_URL: str = "http://localhost:8000"
    DEFAULT_CODE_LENGTH: int = 7

    class Config:
        env_file = ".env"

settings = Settings()
