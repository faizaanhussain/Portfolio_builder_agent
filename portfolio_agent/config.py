"""
Configuration settings for Portfolio Agent.
Loads configuration from environment variables and .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Automatically load .env file if present, overriding any pre-existing environment variables
load_dotenv(override=True)


@dataclass
class Config:
    """Application configuration."""

    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    base_url: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL") or None
    )
    model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )
    workspace_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("WORKSPACE_DIR")
            or ("/tmp/generated_sites" if os.getenv("VERCEL") else "./generated_sites")
        ).resolve()
    )
    max_turns: int = field(
        default_factory=lambda: int(os.getenv("AGENT_MAX_TURNS", "25"))
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    )
    preview_host: str = field(
        default_factory=lambda: os.getenv("PREVIEW_HOST", "127.0.0.1")
    )
    preview_port: int = field(
        default_factory=lambda: int(os.getenv("PREVIEW_PORT", "8000"))
    )

    def __post_init__(self) -> None:
        """Auto-configure known provider endpoints based on key signatures."""
        if self.api_key and self.api_key.startswith("gsk_"):
            if not self.base_url or "api.openai.com" in self.base_url:
                self.base_url = "https://api.groq.com/openai/v1"
            if not self.model or self.model.startswith("gpt-"):
                self.model = "llama-3.3-70b-versatile"
        elif self.api_key and self.api_key.startswith("sk-or-"):
            if not self.base_url or "api.openai.com" in self.base_url:
                self.base_url = "https://openrouter.ai/api/v1"

    def validate(self) -> None:
        """Validate configuration values."""
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please provide it in your .env file or environment."
            )
        if self.max_turns <= 0:
            raise ValueError("max_turns must be a positive integer.")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0.")


_global_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get the active configuration instance."""
    global _global_config
    if _global_config is None or reload:
        _global_config = Config()
    return _global_config
