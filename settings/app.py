from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class AppSettings(BaseSettings):
    CORS_ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:4200",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    ALLOWED_HOSTS: Annotated[list[str], NoDecode] = [
        "localhost",
        "127.0.0.1",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True
        extra = "ignore"

    @field_validator("CORS_ALLOWED_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_csv_list(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
