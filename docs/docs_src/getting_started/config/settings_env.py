import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    url: str
    queue: str = "test-queue"


settings = Settings(_env_file=os.getenv("ENV", ".env"))
