"""
LexOrch-KG — Application Configuration
Uses Pydantic Settings for type-safe environment variable loading.
"""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyHttpUrl


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "LexOrch-KG"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = Field(
        default="change-me-in-production-minimum-32-characters",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = (
        "sqlite+aiosqlite:///./lexorch.db"
    )

    # ── Neo4j ─────────────────────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "lexorch_neo4j"

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    chromadb_collection_name: str = "legal_documents"

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: Literal["groq", "openai", "ollama"] = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-specdec"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dimension: int = 768

    # ── File Upload ───────────────────────────────────────────────────────────
    upload_dir: str = "uploads"
    max_file_size_mb: int = 50
    allowed_extensions: str = "pdf,docx,txt"

    # ── Reports ───────────────────────────────────────────────────────────────
    reports_dir: str = "reports"

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Admin Bootstrap ──────────────────────────────────────────────────────
    admin_email: str = "admin@lexorch.ai"
    admin_password: str = "AdminLex@2024"
    admin_first_name: str = "System"
    admin_last_name: str = "Admin"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance (singleton)."""
    return Settings()


# Global settings instance for convenience imports
settings = get_settings()
