"""
NetElixIQ AI — Configuration
Uses pydantic-settings for environment-based configuration.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "NetElixIQ AI"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    demo_mode: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./netelixiq.db"

    # Gemini AI
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"

    # ML
    default_forecast_horizon: int = 30
    monte_carlo_simulations: int = 2000
    max_upload_size_mb: int = 50

    # Cache
    cache_dir: str = ".cache"
    cache_ttl_seconds: int = 1800

    # Data
    demo_data_dir: str = "data/sample"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
