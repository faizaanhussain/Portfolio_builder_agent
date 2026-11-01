"""
Vercel Serverless Function entry point for Portfolio AI Agent Studio.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from portfolio_agent.config import get_config
from portfolio_agent.sandbox.workspace import Workspace
from portfolio_agent.web.runner import get_default_job_manager
from portfolio_agent.web.server import StudioRequestHandler

# Initialize workspace inside /tmp on serverless environments
config = get_config()
workspace = Workspace(config.workspace_dir)
job_manager = get_default_job_manager()

# Seed sample_portfolio into serverless workspace if available
repo_root = Path(__file__).resolve().parent.parent
sample_src = repo_root / "generated_sites" / "sample_portfolio"
sample_dst = workspace.website_workspace / "sample_portfolio"

if sample_src.exists() and not sample_dst.exists():
    try:
        shutil.copytree(sample_src, sample_dst)
    except Exception:
        pass


class handler(StudioRequestHandler):
    """Vercel HTTP request handler inheriting all Studio functionality."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            workspace=workspace,
            job_manager=job_manager,
            config=config,
            **kwargs,
        )


app = handler
