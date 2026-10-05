from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="postgresql://postgres:password@localhost:5432/salestorm", alias="DB_DSN")
    REDIS_URL: str = "redis://localhost:6379/0"
    MOCK_PSP_URL: str = Field(default="http://localhost:8001", alias="PSP_URL")
    NAIVE_MODE: bool = False

    class Config:
        env_file = ".env"
        populate_by_name = True

settings = Settings()
