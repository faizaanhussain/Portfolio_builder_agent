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

# Automatically load .env file if present
load_dotenv()


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
            os.getenv("WORKSPACE_DIR", "./generated_sites")
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
