"""Application configuration module.

Defines strongly-typed configuration settings using Pydantic Settings,
supporting loading from environment variables, .env files, and runtime overrides.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Global application settings and security thresholds."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = Field(default="AI ISO 27001 Compliance Assistant", description="Application display name")
    debug: bool = Field(default=False, description="Enable debug mode and verbose logging")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")

    # Storage & Persistence (SQLite initial database)
    database_url: str = Field(
        default=f"sqlite:///{BASE_DIR}/data/app.db",
        description="SQLAlchemy database connection URI (SQLite default)",
    )
    upload_dir: Path = Field(
        default=BASE_DIR / "data" / "uploads",
        description="Local directory for temporary or persistent storage of uploaded files",
    )
    standards_dir: Path = Field(
        default=BASE_DIR / "data" / "standards",
        description="Directory containing non-copyrighted structural standard references",
    )

    # File Upload Security Settings
    max_file_size_bytes: int = Field(
        default=25 * 1024 * 1024,  # 25 MB
        description="Maximum allowed upload file size in bytes",
    )
    allowed_extensions: tuple[str, ...] = Field(
        default=(".pdf", ".docx", ".xlsx"),
        description="Permitted document file extensions",
    )
    allowed_mime_types: tuple[str, ...] = Field(
        default=(
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        description="Permitted MIME types verified against file headers",
    )

    # AI / LLM Configuration (Optional & Configurable)
    llm_provider: Literal["mock", "openai", "gemini", "anthropic", "ollama", "azure"] = Field(
        default="mock",
        description="Active AI provider backend. Defaults to 'mock' for offline operation without API keys",
    )
    llm_model: str = Field(default="mock-audit-v1", description="Model identifier to invoke")
    llm_temperature: float = Field(default=0.1, description="Sampling temperature for deterministic audit output")
    llm_request_timeout: int = Field(default=60, description="HTTP timeout in seconds for LLM calls")

    # Provider Credentials (Optional)
    openai_api_key: str | None = Field(default=None, description="OpenAI API Key")
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API Key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API Key")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    azure_openai_endpoint: str | None = Field(default=None, description="Azure OpenAI Endpoint")
    azure_openai_api_key: str | None = Field(default=None, description="Azure OpenAI Key")


settings = Settings()

