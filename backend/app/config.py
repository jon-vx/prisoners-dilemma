import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    frontend_origins: tuple[str, ...]


def get_settings() -> Settings:
    configured_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173")
    origins = tuple(
        origin.strip() for origin in configured_origins.split(",") if origin.strip()
    )
    return Settings(frontend_origins=origins)
