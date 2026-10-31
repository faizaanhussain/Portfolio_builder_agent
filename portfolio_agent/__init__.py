"""
Portfolio Agent Package.
Autonomous AI agent that creates modern, responsive portfolio websites inside a secure sandbox.
"""

from portfolio_agent.agent import PortfolioAgent
from portfolio_agent.config import Config, get_config
from portfolio_agent.prompts import WEBSITE_SYSTEM_PROMPT
from portfolio_agent.sandbox.workspace import Workspace

__version__ = "1.0.0"
__all__ = [
    "PortfolioAgent",
    "Config",
    "get_config",
    "WEBSITE_SYSTEM_PROMPT",
    "Workspace",
]
