from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    app_name: str = "AI Byggesøknad API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://byggesoknad:byggesoknad_dev@localhost:5432/byggesoknad"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_strong_model: str = "gpt-4.1"

    # External APIs
    kartverket_api_base: str = "https://api.kartverket.no"
    geonorge_api_base: str = "https://wfs.geonorge.no"
    nve_api_base: str = "https://gis3.nve.no"

    # Storage
    storage_type: str = "local"
    storage_local_path: str = "./uploads"

    # Feature flags
    feature_pdf_generation: bool = True
    feature_ai_classification: bool = True
    feature_hazard_data: bool = True
    feature_plan_data: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
